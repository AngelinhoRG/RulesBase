# RulesBase
Want to know something specific about a rulebook? You've come to the right place! Ask our bot a question in plain english, and receive the information you're looking for straight from the rulebook without having to search for the answer yourself!

## Getting Started

The project is currently at an early, backend-only stage: a command-line pipeline that ingests rulebooks and answers questions grounded in them. There's no FastAPI server, React frontend, or Docker setup yet (see [Tech Stack](#tech-stack) below for what's built vs. planned).

**Prerequisites**
- Python 3.12+
- A [Gemini API key](https://aistudio.google.com/apikey) (free tier is fine to start)

**Setup**

1. Create and activate a virtual environment, then install dependencies:
   ```
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Set up your environment file at the **project root** (not inside `backend/`):
   ```
   cp .env.example .env
   ```
   Then open `.env` and set `GEMINI_API_KEY=your-actual-key`.
3. Add rulebook files (`.md` or `.txt`) to `documents/rulebooks/`. Two placeholder sample rulebooks (Soccer, Uno) are already there so you can try things out immediately — swap in real official rulebook text whenever you're ready.
4. From `backend/`, with the venv active, ingest the rulebooks into the local vector store:
   ```
   python -m ingest.ingest
   ```
   Re-run this any time you add or edit a rulebook file.
5. Ask questions interactively:
   ```
   python dev_repl.py
   ```

## The Problem We're Solving
Google searches and LLM queries don't always give you the correct rule for a game. For example, stacking +4's in Uno is a popular house rule, but it's not in the official rulebook — and you might be told otherwise. We eliminate that hallucination risk by showing you the rulebook's exact wording, so you know exactly what's official.

## Tech Stack

**Built:**
- **Python** — chunking, ingestion, and retrieval logic
- **ChromaDB** — vector store for rulebook chunks (running locally via a persistent client for now)
- **Google Gemini API** — embeds rulebook chunks/questions and generates answers constrained to the retrieved rulebook text

**Planned:**
- **FastAPI** — HTTP API wrapping the ingestion/retrieval logic (`/ask`, `/games` endpoints)
- **React + Vite** — chat UI, including a source panel showing the exact matched rulebook passage alongside each generated answer
- **Docker / docker-compose** — containerized services for Chroma, the backend, and the frontend, so the whole stack runs with one command