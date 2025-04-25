from typing import List
from sqlalchemy.orm import Session
from models.user import User
from core.config import logger
from sqlalchemy import text


def search_users_by_embedding(db: Session, query_embedding: List[float], top_n: int = 5) -> List[User]:
    """
    Efficient search for users by embedding similarity using PostgreSQL pgvector extension.
    Uses cosine similarity operator directly in SQL.

    Returns top_n users sorted by similarity descending.
    """
    # Pgvector cosine distance operator: <=>  (lower means more similar)
    # We order by ascending distance

    # Convert input embedding list to string format compatible with SQL array input
    embedding_str = ','.join(str(x) for x in query_embedding)

    sql = text(f"""
    SELECT * FROM users
    WHERE bio_embedding IS NOT NULL AND profession_embedding IS NOT NULL
    ORDER BY LEAST(
        bio_embedding <=> cube(array[{embedding_str}]),
        profession_embedding <=> cube(array[{embedding_str}])
    )
    LIMIT :top_n
    """)

    result = db.execute(sql, {'top_n': top_n})
    users = result.fetchall()

    # Convert result back to User objects
    user_list = [db.merge(user) for user in users]

    logger.info(f"User similarity search top {top_n}: {[ (u.email) for u in user_list]}")

    return user_list


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    # We can optionally keep this for non-DB purposes
    from numpy import dot
    from numpy.linalg import norm
    if not vec1 or not vec2:
        return 0.0
    v1 = vec1
    v2 = vec2
    denom = (norm(v1) * norm(v2))
    if denom == 0.0:
        return 0.0
    return float(dot(v1, v2) / denom)
