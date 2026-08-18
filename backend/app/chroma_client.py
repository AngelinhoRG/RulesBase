import chromadb

from app import config

_collection = None


def get_collection():
    global _collection
    if _collection is not None:
        return _collection

    if config.CHROMA_HOST:
        client = chromadb.HttpClient(host=config.CHROMA_HOST, port=config.CHROMA_PORT)
    else:
        client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)

    _collection = client.get_or_create_collection(
        config.COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )
    return _collection
