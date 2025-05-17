from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from pinecone import Pinecone

DATABASE_URL=os.environ.get("POSTGRES_URL")
PINECONE_API_KEY=os.environ.get("PINECONE_API_KEY")

@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    except Exception as e:
        print(e)
    finally:
        conn.close()


@contextmanager
def get_pinecone_conn(index_name):
    # Initialize Pinecone connection
    pc = Pinecone(api_key=PINECONE_API_KEY)
    conn = pc.Index(index_name)
    try:
        yield conn
    except Exception as e:
        print(e)
    finally:
        # Explicitly delete the connection object
        del conn