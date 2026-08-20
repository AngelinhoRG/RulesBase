from app.chroma_client import get_collection


def list_categories():
    result = get_collection().get(include=["metadatas"])
    return sorted({m["category"] for m in result["metadatas"]})


def list_games(category=None):
    where = {"category": category} if category else None
    result = get_collection().get(where=where, include=["metadatas"])
    return sorted({m["game_name"] for m in result["metadatas"]})
