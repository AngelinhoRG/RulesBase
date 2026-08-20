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
3. Add rulebook files (`.md` or `.txt`) under `documents/rulebooks/<category>/<game>.md` — the immediate subfolder is the category (e.g. `sports`, `board-games`) and the filename becomes the game's name (e.g. `soccer.md` → "Soccer"). Two placeholder samples are already there (`sports/soccer.md`, `board-games/uno.md`) so you can try things out immediately — swap in real official rulebook text whenever you're ready. See [Design Decisions](#design-decisions-and-why) for why category/game name come from file structure rather than document content.
4. From `backend/`, with the venv active, ingest the rulebooks into the local vector store:
   ```
   python -m ingest.ingest
   ```
   Re-run this any time you add or edit a rulebook file, or pass `--file <category>/<filename>` to re-ingest just one file.
5. Ask questions interactively:
   ```
   python dev_repl.py
   ```
   You'll be asked which category to search (defaults to `sports`); within a session you can switch with `/category <name>` or narrow to one game with `/game <name>`.

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

## Design Decisions (and Why)

Keeping a record of the more opinionated calls I've made here, so it's clear these weren't arbitrary — and so anyone reading the code understands the reasoning behind the structure before they hit it.

### Category-based retrieval, not "search everything" or "pick one exact game"

I considered two extremes: let a question search across every ingested rulebook with no filtering at all, or force the user to pick one specific game before they can ask anything. Neither sat right with me.

No filtering means an unrelated rulebook's chunk can get pulled into a question's context purely because of an embedding-similarity fluke — I actually saw this happen during early testing, where a soccer question about red cards pulled back a low-relevance Uno chunk as a "source." Forcing one exact game up front solves that, but it breaks a different kind of question I want this to handle well — something like "what game allows players to draw cards?" is a legitimate question about a whole category, not about one game I'd have to already know the answer to before I could even ask.

So the middle ground I landed on is a **category** level (`sports`, `board-games` for now, more later) that a user picks — or that defaults to one category rather than an ambiguous blank state — with retrieval filtered to that category instead of to one exact game. This keeps genuinely unrelated domains from polluting each other's results while still supporting "which game in this category does X" questions.

### Category and game name come from folder/file structure, not from document content

Rulebooks are organized as `documents/rulebooks/<category>/<game>.md` — e.g. `documents/rulebooks/sports/soccer.md`. The category is the subfolder name; the game's name is its filename. I chose this over inferring names from the document's own text (e.g. reading an `# Soccer` heading out of the file) because relying on document content caused a real, reproducible bug early on: the same rulebook's inferred name came out differently depending on whether it happened to have a top-level heading, which made a chunk's own metadata inconsistent with itself between runs. Tying both category and game name to where the file physically lives is deterministic — there's exactly one place either value can come from, and dropping a new rulebook into the right folder *is* the entire "categorize this game" step, nothing else to remember to update.

### Sports is the default category

The app starts in the `sports` category rather than presenting a blank or "pick one" first screen, with board games (and future categories) as an explicit switch. This is just an opinionated default, not a technical requirement — an opinionated starting point beats making someone choose before they've asked anything.

### Known limitation I'm choosing to accept for now: enumeration questions

A question like "does soccer require a ball?" names a specific game and is well-supported by category-filtered retrieval today. A question like "what sports don't use a ball?" asks the system to enumerate across *every* game in a category — and plain top-k-by-similarity search isn't guaranteed to surface at least one chunk from every game in that category. It could easily answer confidently based on only the 2-3 games whose rulebook phrasing happened to embed closest to the question, silently leaving the rest out — not quite a hallucination, but a coverage gap that would look like one. Category filtering alone doesn't fix this; it would need retrieval that deliberately spreads across distinct games (e.g. top-N *per game*, not top-N overall). I'm noting it here as a real, known gap rather than fixing it now, since it's a separate problem from what category filtering was meant to solve.