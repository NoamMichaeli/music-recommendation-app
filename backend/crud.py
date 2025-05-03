from .database import get_db
from typing import Dict


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
                SELECT id as user_id, username as user_name, is_admin, hashed_password FROM users WHERE username = %s;
            """, (username,))
            user = cur.fetchone()
            return user


def user_exists(user_id: int, user_name: str) -> Dict[str, bool]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, is_admin FROM users WHERE id = %s;", (user_id,))
            user = cur.fetchone()
            return {"is_user_exists": user and user['username'] == user_name, "is_admin": user['is_admin']}


def get_likes(user_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT t.track_id, t.track_name, t.artist_name, year
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


def add_like(user_id: int, track_id: str) -> tuple[bool, str, int]:
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
            # stats_crud.user_liked_recommended_track_report(user_id, track_id)
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
