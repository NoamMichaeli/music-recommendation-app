import pandas as pd
from backend.pinecone_crud import query_pinecone_by_ids, upsert_pinecone, delete_ids_pinecone
from backend.postgres_crud import get_likes


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
    liked_tracks_vectors = query_pinecone_by_ids("tracks", user_liked_track_ids).get("vectors")

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

