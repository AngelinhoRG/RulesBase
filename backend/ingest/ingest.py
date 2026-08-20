import argparse
import os

from app import gemini_client
from app.chroma_client import get_collection
from app.config import RULEBOOKS_DIR
from ingest.chunking import chunk_markdown, game_name_from_filename

SUPPORTED_EXTENSIONS = (".md", ".txt")


def discover_paths(rulebooks_dir):
    """documents/rulebooks/<category>/<game>.md -- each immediate subfolder
    of rulebooks_dir is a category; files directly under rulebooks_dir
    (no category folder) are not supported."""
    paths = []
    for category in sorted(os.listdir(rulebooks_dir)):
        category_dir = os.path.join(rulebooks_dir, category)
        if not os.path.isdir(category_dir):
            continue
        for filename in sorted(os.listdir(category_dir)):
            if filename.endswith(SUPPORTED_EXTENSIONS):
                paths.append(os.path.join(category_dir, filename))
    return paths


def ingest_file(path, collection):
    filename = os.path.basename(path)
    category = os.path.basename(os.path.dirname(path))
    game_name = game_name_from_filename(filename)

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_markdown(text, filename, category, game_name)
    if not chunks:
        print(f"  {category}/{filename}: no chunks produced, skipping")
        return 0

    embeddings = gemini_client.embed_texts(
        [c["text"] for c in chunks], task_type="RETRIEVAL_DOCUMENT"
    )

    collection.delete(where={"source_file": filename})
    collection.add(
        ids=[f"{category}::{filename}::{c['chunk_index']}" for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "source_file": c["source_file"],
                "category": c["category"],
                "game_name": c["game_name"],
                "section_path": c["section_path"],
                "chunk_index": c["chunk_index"],
            }
            for c in chunks
        ],
    )
    print(f"  {category}/{filename}: {len(chunks)} chunks ingested (game={game_name!r})")
    return len(chunks)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file", help="Only re-ingest this single file, given as '<category>/<filename>'"
    )
    args = parser.parse_args()

    collection = get_collection()

    if args.file:
        paths = [os.path.join(RULEBOOKS_DIR, args.file)]
    else:
        paths = discover_paths(RULEBOOKS_DIR)

    print(f"Ingesting {len(paths)} file(s) from {RULEBOOKS_DIR}")
    total = 0
    for path in paths:
        total += ingest_file(path, collection)

    print(f"Done. {total} chunks in collection (count={collection.count()}).")


if __name__ == "__main__":
    main()
