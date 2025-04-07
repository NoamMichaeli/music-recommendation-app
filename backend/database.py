from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL=os.environ.get("DATABASE_URL")

@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    except Exception as e:
        print(e)
    finally:
        conn.close()