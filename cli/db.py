import os

from langchain_core import embeddings
from langchain_huggingface import HuggingFaceEmbeddings

import psycopg


db_connection = psycopg.connect(os.getenv("POSTGRES_SERVICE_URI"))

embeddings = HuggingFaceEmbeddings()


def embed_query(query: str):
    """generate embedding from the search query"""
    return embeddings.embed_query(query)


def similarity_search(query: str):
    """Search for similar content based on vector embeddings"""

    embedding = embed_query(query)
    embedding_str = str(embedding)

    sql = """
    SELECT title, content_snippet, hybrid_score FROM hybrid_search(
        %s,
        %s::vector,  -- Your query embedding
        0.6,  -- Content weight
        0.4,   -- Vector weight
        20     -- Max results
    );"""

    with db_connection.cursor() as cur:
        result = cur.execute(sql, (query, embedding_str))
        rows = result.fetchall()
        return rows
