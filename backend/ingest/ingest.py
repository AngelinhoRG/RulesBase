import argparse
import os

from app import gemini_client
from app.chroma_client import get_collection
from app.config import RULEBOOKS_DIR
from ingest.chunking import chunk_markdown

SUPPORTED_EXTENSIONS = (".md", ".txt")


def ingest_file(path, collection):
    filename = os.path.basename(path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_markdown(text, filename)
    if not chunks:
        print(f"  {filename}: no chunks produced, skipping")
        return 0

    embeddings = gemini_client.embed_texts(
        [c["text"] for c in chunks], task_type="RETRIEVAL_DOCUMENT"
    )

    collection.delete(where={"source_file": filename})
    collection.add(
        ids=[f"{filename}::{c['chunk_index']}" for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "source_file": c["source_file"],
                "game_name": c["game_name"],
                "section_path": c["section_path"],
                "chunk_index": c["chunk_index"],
            }
            for c in chunks
        ],
    )
    print(f"  {filename}: {len(chunks)} chunks ingested")
    return len(chunks)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Only re-ingest this single filename")
    args = parser.parse_args()

    collection = get_collection()

    if args.file:
        paths = [os.path.join(RULEBOOKS_DIR, args.file)]
    else:
        paths = [
            os.path.join(RULEBOOKS_DIR, f)
            for f in sorted(os.listdir(RULEBOOKS_DIR))
            if f.endswith(SUPPORTED_EXTENSIONS)
        ]

    print(f"Ingesting {len(paths)} file(s) from {RULEBOOKS_DIR}")
    total = 0
    for path in paths:
        total += ingest_file(path, collection)

    print(f"Done. {total} chunks in collection (count={collection.count()}).")


if __name__ == "__main__":
    main()
