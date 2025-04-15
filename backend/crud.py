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