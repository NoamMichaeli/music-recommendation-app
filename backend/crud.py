from .database import get_db

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