from typing import List
from sqlalchemy.orm import Session
from models.user import User
from core.config import logger
import numpy as np


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    if not vec1 or not vec2:
        return 0.0
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    denom = (np.linalg.norm(v1) * np.linalg.norm(v2))
    if denom == 0.0:
        return 0.0
    return float(np.dot(v1, v2) / denom)


def search_users_by_embedding(db: Session, query_embedding: list[float], top_n: int = 5) -> List[User]:
    """
    Search users by embedding similarity (bio and profession embeddings combined).
    Returns top_n users sorted by similarity descending.
    """
    users = db.query(User).filter(User.bio_embedding != None, User.profession_embedding != None).all()

    results = []
    for user in users:
        if not user.bio_embedding or not user.profession_embedding:
            continue
        sim_bio = cosine_similarity(query_embedding, user.bio_embedding)
        sim_prof = cosine_similarity(query_embedding, user.profession_embedding)
        sim = max(sim_bio, sim_prof)  # Use max similarity as score
        results.append((user, sim))

    # Sort by similarity descending
    results.sort(key=lambda x: x[1], reverse=True)

    # Log top results
    logger.info(f"User similarity search top {top_n}: {[ (u.email, s) for u,s in results[:top_n]]}")

    return [u for u, _ in results[:top_n]]
