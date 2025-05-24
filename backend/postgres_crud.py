from .database import get_db
from typing import List, Dict, Tuple


# function related to the basic webapp
def get_track():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT track_id, track_name, artist_name, year
                FROM tracks
                ORDER BY RANDOM()
                LIMIT 1;
            """)
            track = cur.fetchall()
    return track


def get_random_10_tracks():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT track_id, track_name, artist_name, year
                FROM tracks
                ORDER BY RANDOM()
                LIMIT 10;
            """)
            track = cur.fetchall()
    return track


def create_user(username: str, hashed_password: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, hashed_password) VALUES (%s, %s)
                ON CONFLICT (username) DO NOTHING
                RETURNING id as user_id, username as user_name;
            """, (username, hashed_password))
            user = cur.fetchone()
            conn.commit()
            return user


def authenticate_user(username: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id as user_id, username as user_name, hashed_password FROM users WHERE username = %s;
            """, (username,))
            user = cur.fetchone()
            return user


def user_exists(user_id: int, user_name: str) -> Dict[str, bool]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username FROM users WHERE id = %s;", (user_id,))
            user = cur.fetchone()
            if user:
                return {"is_user_exists": user and user['username'] == user_name}
            else:
                return {"is_user_exists": False}


def get_likes(user_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.track_id, t.track_name, t.artist_name, year, update_timestamp
                FROM likes l
                JOIN tracks t ON l.track_id = t.track_id
                WHERE l.user_id = %s
                ORDER BY l.update_timestamp ASC;
            """, (user_id,))
            tracks = cur.fetchall()
            return tracks


def get_dislikes(user_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.track_id, t.track_name, t.artist_name, year
                FROM dislikes d
                JOIN users u ON d.user_id = u.id
                JOIN tracks t ON d.track_id = t.track_id
                WHERE u.id = %s
                ORDER BY d.update_timestamp ASC;
            """, (user_id,))
            tracks = cur.fetchall()
            return tracks


def add_like(user_id: int, track_id: str) -> Tuple[bool, str, int]:
    with get_db() as conn:
        with conn.cursor() as cur:
            # Check if the track_id exists in the dislikes table for the user
            cur.execute("""
                SELECT 1 FROM dislikes WHERE user_id = %s AND track_id = %s;
            """, (user_id, track_id))
            disliked = cur.fetchone()
            if disliked:
                return False, "Track is in dislikes, cannot add to likes.", 0

            # Check if the track_id exists in the tracks table
            cur.execute("""
                SELECT 1 FROM tracks WHERE track_id = %s;
            """, (track_id,))
            is_track_exists = cur.fetchone()
            if not is_track_exists:
                return False, "The requested track is not exists in our limited 1M dataset.", 0

            # Insert into likes
            cur.execute("""
                INSERT INTO likes (user_id, track_id) 
                VALUES (%s, %s)
                ON CONFLICT (user_id, track_id) DO NOTHING;
            """, (user_id, track_id))
            conn.commit()
            affected_rows = cur.rowcount
            if affected_rows > 0:
                return True, "Track added to likes.", 1
            else:
                return False, "Track already in likes.", 0


def upload_csv(user_id: int, track_ids: list):
    affected_rows = 0
    for track_id in track_ids:
        if add_like(user_id, track_id)[0]:
            affected_rows += 1
    return affected_rows


def add_dislike(user_id: int, track_id: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO dislikes (user_id, track_id) 
                VALUES (%s, %s)
                ON CONFLICT (user_id, track_id) DO NOTHING;
            """, (user_id, track_id))
            conn.commit()


def remove_like(user_id: int, track_id: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""DELETE FROM likes WHERE user_id = %s AND track_id = %s;""", (user_id, track_id))
            conn.commit()


def remove_dislike(user_id: int, track_id: str):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""DELETE FROM dislikes WHERE user_id = %s AND track_id = %s;""", (user_id, track_id))
            conn.commit()


def get_recommended_tracks_by_filtering_out_the_user_listening_history(top_tracks: List[tuple], user_id: int):
    values_clause = ", ".join([f"('{track_id}', {relevance_percentage})" for track_id, relevance_percentage in top_tracks])
    query = f"""
        WITH
        current_user_likes_dislikes AS (
            SELECT likes.track_id
            FROM likes
            WHERE user_id = {user_id}
            UNION
            SELECT dislikes.track_id
            FROM dislikes
            WHERE user_id = {user_id}
        ),
        top_tracks AS (
            SELECT track_id_col, ROUND(100 * relevance_percentage, 2) as relevance_percentage
            FROM (
                VALUES {values_clause}
            ) AS derived_table(track_id_col, relevance_percentage)
        )
        SELECT tracks.track_id, track_name, artist_name, relevance_percentage, year, 'user_history' as recommendation_type
        FROM top_tracks
        JOIN tracks ON top_tracks.track_id_col = tracks.track_id
        LEFT OUTER JOIN current_user_likes_dislikes ON top_tracks.track_id_col = current_user_likes_dislikes.track_id
        WHERE current_user_likes_dislikes.track_id IS NULL;
    """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            tracks = cur.fetchall()
            return tracks


def get_recommended_tracks_by_top_similar_users(top_users, user_id):
    values_clause = ", ".join([f"(CAST('{user_id}' AS INT), {relevance_percentage})" for user_id, relevance_percentage in top_users])
    query = f"""
        WITH
        current_user_likes_dislikes AS (
            SELECT likes.track_id, likes.user_id
            FROM likes
            WHERE user_id = {user_id}
            UNION
            SELECT dislikes.track_id, dislikes.user_id
            FROM dislikes
            WHERE user_id = {user_id}
        ),
        top_users AS (
            SELECT user_id_col, ROUND(100 * relevance_percentage, 2) as relevance_percentage
            FROM (
                VALUES {values_clause}
            ) AS derived_table(user_id_col, relevance_percentage)
        )
        SELECT tracks.track_id, track_name, artist_name, top_users.relevance_percentage, year, 'similar_users' as recommendation_type
        FROM top_users
        JOIN likes ON top_users.user_id_col = likes.user_id
        JOIN tracks ON likes.track_id = tracks.track_id
        LEFT OUTER JOIN current_user_likes_dislikes ON tracks.track_id = current_user_likes_dislikes.track_id
        WHERE current_user_likes_dislikes.track_id IS NULL;
        """

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            tracks = cur.fetchall()
            return tracks


def get_trending_tracks():
    query = f"""
        SELECT tracks.track_id, track_name, artist_name, year, '' as recommendation_type, 0 as relevance_percentage
        FROM likes
        JOIN tracks on likes.track_id = tracks.track_id
        ORDER BY likes.update_timestamp DESC;
        """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            tracks = cur.fetchall()
            return tracks


