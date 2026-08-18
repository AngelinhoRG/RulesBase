import os
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Copy .env.example to .env at the project "
        "root and fill in your key."
    )

GEMINI_EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
GEMINI_GENERATION_MODEL = os.environ.get("GEMINI_GENERATION_MODEL", "gemini-3.6-flash")

COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "rulebooks")

# Set once we move to a Chroma server container (M3) via CHROMA_HOST/CHROMA_PORT.
CHROMA_HOST = os.environ.get("CHROMA_HOST")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
CHROMA_PERSIST_DIR = os.environ.get(
    "CHROMA_PERSIST_DIR", str(_PROJECT_ROOT / "backend" / "chroma_dev_data")
)

RULEBOOKS_DIR = os.environ.get("RULEBOOKS_DIR", str(_PROJECT_ROOT / "documents" / "rulebooks"))

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
