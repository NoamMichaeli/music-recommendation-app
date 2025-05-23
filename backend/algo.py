from typing import Dict

import pandas as pd
from backend.pinecone_crud import query_pinecone_by_ids, upsert_pinecone, delete_ids_pinecone, query_pinecone_by_vector
from backend.postgres_crud import get_likes, get_recommended_tracks_by_filtering_out_the_user_listening_history, get_recommended_tracks_by_top_similar_users, get_trending_tracks
import random

VECTOR_DIMENSIONS = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'mode',
                       'popularity', 'speechiness', 'tempo', 'valence', 'year_2000_2004', 'year_2005_2009',
                       'year_2010_2014', 'year_2015_2019', 'year_2020_2024']


def build_vector_df_with_timestamps(vectors: dict, user_liked_tracks: list) -> pd.DataFrame:
    """
    Convert Pinecone vector dict to DataFrame and add timestamp column.
    """
    # Extract mapping from track_id to timestamp
    tracks_to_timestamp = {
        row["track_id"]: row["update_timestamp"]
        for row in user_liked_tracks
    }

    # Build list of dicts with track_id and vector values
    records = []
    for item in vectors.values():
        record = {"track_id": item["id"]}
        for name, value in zip(VECTOR_DIMENSIONS, item["values"]):
            record[name] = value
        records.append(record)

    # Build DataFrame
    df = pd.DataFrame(records)

    # Add timestamp column
    df["update_timestamp"] = df["track_id"].map(tracks_to_timestamp)
    return df


def weighted_mean(df, col="update_timestamp"):
    date_col = df[col]

    min_date = date_col.min()
    max_date = date_col.max()

    bucket_time_period = (max_date - min_date) / 4

    # first_quarter = min_date
    second_quarter = min_date + bucket_time_period
    third_quarter = min_date + bucket_time_period * 2
    fourth_quarter = min_date + bucket_time_period * 3

    if (max_date - min_date).days < 7:
        mean_df = df.mean().drop(col)

    else:
        # calculate each quarter mean and multiply by matching weight
        # the later the records, the bigger the weight
        first_quarter_df = df[df[col] <= second_quarter].mean().drop(col).mul(1)
        second_quarter_df = df[(df[col] > second_quarter) & (df[col] <= third_quarter)].mean().drop(col).mul(2)
        third_quarter_df = df[(df[col] > third_quarter) & (df[col] <= fourth_quarter)].mean().drop(col).mul(3)
        fourth_quarter_df = df[df[col] > fourth_quarter].mean().drop(col).mul(4)

        all_quarter_df = pd.DataFrame({
            'first': first_quarter_df,
            'second': second_quarter_df,
            'third': third_quarter_df,
            'fourth': fourth_quarter_df})

        mean_df = all_quarter_df.mean(axis=1)

    return mean_df


def update_user_mean_vector(user_id: int):
    user_liked_tracks = get_likes(user_id)
    if not user_liked_tracks:
        print(f"delete user vector: {user_id}")
        delete_ids_pinecone('users', [str(user_id)])
        return

    user_liked_track_ids = [row["track_id"] for row in user_liked_tracks]
    liked_tracks_vectors = query_pinecone_by_ids("tracks", user_liked_track_ids).vectors

    df_with_timestamps = build_vector_df_with_timestamps(liked_tracks_vectors, user_liked_tracks)
    df_with_timestamps = df_with_timestamps.drop("track_id", axis=1)

    # Calc mean vector
    user_mean_vector_df = weighted_mean(df_with_timestamps)
    # print(user_mean_vector_df)

    user_vector_to_update = [
        {
            "id": str(user_id),
            "metadata": {
                "num_tracks": len(user_liked_tracks)
            },
            "values": [
                round(float(user_mean_vector_df["acousticness"]), 3),
                round(float(user_mean_vector_df["danceability"]), 3),
                round(float(user_mean_vector_df["energy"]), 3),
                round(float(user_mean_vector_df["instrumentalness"]), 3),
                round(float(user_mean_vector_df["liveness"]), 3),
                round(float(user_mean_vector_df["loudness"]), 3),
                round(float(user_mean_vector_df["mode"]), 3),
                round(float(user_mean_vector_df["popularity"]), 3),
                round(float(user_mean_vector_df["speechiness"]), 3),
                round(float(user_mean_vector_df["tempo"]), 3),
                round(float(user_mean_vector_df["valence"]), 3),
                round(float(user_mean_vector_df["year_2000_2004"]), 3),
                round(float(user_mean_vector_df["year_2005_2009"]), 3),
                round(float(user_mean_vector_df["year_2010_2014"]), 3),
                round(float(user_mean_vector_df["year_2015_2019"]), 3),
                round(float(user_mean_vector_df["year_2020_2024"]), 3)
            ]
        }
    ]
    # print(user_vector_to_update)

    num_user_vectors_affected = upsert_pinecone('users', user_vector_to_update)
    if len(user_vector_to_update) == num_user_vectors_affected:
        # print(f"Updated user_id={user_id} vector={user_vector_to_update}")
        return True
    return


def get_recommendations_by_user_listening_history(user_id: int):
    retrieve_user_results = query_pinecone_by_ids('users', [str(user_id)])
    user_record = retrieve_user_results.vectors.get(str(user_id))

    if not user_record:
        return []  # user has no likes or dislikes, can't recommend

    top_k_recommendations = 2 * user_record.metadata.get('num_tracks')
    top_k_recommendations = 50 if top_k_recommendations < 50 else top_k_recommendations

    # Query Pinecone 'tracks' index, using 'cosine' metric, to find the top most similar vectors
    query_result = query_pinecone_by_vector('tracks', user_record.values, top_k_recommendations)
    top_ids_scores = [(match['id'], match['score']) for match in query_result.matches]

    # Get tracks information by 'track_id', and add the similarity 'score' pinecone calculated
    if len(top_ids_scores) > 0:
        result = get_recommended_tracks_by_filtering_out_the_user_listening_history(top_ids_scores, user_id)
        return result
    return []


def get_recommendations_by_similar_users(user_id: int):
    retrieve_user_results = query_pinecone_by_ids('users', [str(user_id)])
    user_record = retrieve_user_results.vectors.get(str(user_id))

    if not user_record:
        return []  # user has no likes or dislikes, can't recommend

    # get similar user from pinecone, take top k user_id
    # Query Pinecone 'users' index, using 'cosine' metric, to find the top most similar vectors
    top_k_users = 20
    query_user_results = query_pinecone_by_vector('users', user_record.values, top_k=top_k_users)
    top_ids_scores = [(match.get('id'), match.get('score')) for match in query_user_results.get('matches')]

    if not len(top_ids_scores):
        return []

    result = get_recommended_tracks_by_top_similar_users(top_ids_scores, user_id)
    return result

def remove_duplicate_tracks_from_recommendation_list(combined_list):
    frozensets = [frozenset(d.items()) for d in combined_list]
    unique_frozensets = set(frozensets)
    combined_dedup = [dict(fs) for fs in unique_frozensets]
    return combined_dedup


def get_combined_recommendation(user_id: int):
    user_history = get_recommendations_by_user_listening_history(user_id)
    similar_users = get_recommendations_by_similar_users(user_id)
    combined = user_history + similar_users

    # remove duplicates
    combined_dedup = remove_duplicate_tracks_from_recommendation_list(combined)

    if not combined_dedup:
        trending = get_trending_tracks()
        suggest_num = len(trending)
        suggest_num = 50 if suggest_num > 50 else suggest_num
        return random.sample(trending, suggest_num)

    sample_size = int(max(len(user_history), len(similar_users))/4)
    shuffled_list = random.sample(combined_dedup, sample_size)
    shuffled_list = sorted(shuffled_list, key=lambda rec: rec["relevance_percentage"], reverse=True)

    return shuffled_list