from typing import List

from .database import get_pinecone_conn

def query_pinecone_by_ids(index_name: str, id_list: List[str]):
    with get_pinecone_conn(index_name) as index:
        fetch_results = index.fetch(ids=id_list)
        return fetch_results


def upsert_pinecone(index_name: str, vectors: List[dict]):
    with get_pinecone_conn(index_name) as index:
        response = index.upsert(vectors=vectors)
        if response:
            return response.get('upsertedCount')
        return 0


def delete_ids_pinecone(index_name: str, ids: List[str]):
    with get_pinecone_conn(index_name) as index:
        response = index.delete(ids=ids)
        # index.delete returns empty list if delete operation was successful
        if not response:
            return True
        else:
            return False

def query_pinecone_by_vector(index_name: str, column_averages: list[float], top_k: int):
    with get_pinecone_conn(index_name) as index:
        query_result = index.query(vector=column_averages, top_k=top_k)
        return query_result

