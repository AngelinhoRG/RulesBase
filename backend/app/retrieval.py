from app import gemini_client
from app.chroma_client import get_collection
from app.config import DEFAULT_CATEGORY

NO_ANSWER_MESSAGE = "I couldn't find that in the rulebook."


def ask(question, category=DEFAULT_CATEGORY, game=None, top_k=5):
    collection = get_collection()

    [query_embedding] = gemini_client.embed_texts([question], task_type="RETRIEVAL_QUERY")

    conditions = []
    if category:
        conditions.append({"category": category})
    if game:
        conditions.append({"game_name": game})

    if len(conditions) > 1:
        where = {"$and": conditions}
    elif conditions:
        where = conditions[0]
    else:
        where = None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    if not documents:
        return {"answer": NO_ANSWER_MESSAGE, "sources": []}

    context_block = "\n\n".join(
        f"[{i + 1}] (Source: {meta['source_file']} > {meta['section_path']})\n{doc}"
        for i, (doc, meta) in enumerate(zip(documents, metadatas))
    )

    answer = gemini_client.generate_answer(question, context_block)

    sources = [
        {
            "text": doc,
            "source_file": meta["source_file"],
            "section": meta["section_path"],
            "score": round(1 - dist, 4),
        }
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]

    return {"answer": answer, "sources": sources}
