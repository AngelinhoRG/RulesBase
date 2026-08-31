import time

from google import genai
from google.genai import errors, types

from app import config

_client = None

# The API rejects batches over 100 requests (BatchEmbedContentsRequest).
_EMBED_BATCH_SIZE = 100

# Free-tier embedding quota is ~100 requests/minute; back off and retry
# rather than failing the whole ingestion run on a 429.
_MAX_RETRIES = 5
_INITIAL_BACKOFF_SECONDS = 20

SYSTEM_PROMPT = """You are a rules-lookup assistant. Answer ONLY using the RULEBOOK EXCERPTS
provided in the user message. Do not use any outside knowledge of this game, even if you
believe you know the answer, and even if the excerpts seem incomplete.

If the excerpts do not contain enough information to answer, respond with exactly this
sentence and nothing else: "I couldn't find that in the rulebook."

Do not guess, infer common house rules, or fill gaps with general knowledge of how the
game is usually played. Quote or closely paraphrase only what appears in the excerpts.
Be concise."""


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def embed_texts(texts, task_type):
    embeddings = []
    for i in range(0, len(texts), _EMBED_BATCH_SIZE):
        embeddings.extend(_embed_batch(texts[i : i + _EMBED_BATCH_SIZE], task_type))
    return embeddings


def _embed_batch(texts, task_type):
    # A flat list[str] is treated by the SDK as multiple *parts* of one Content
    # (and returns a single embedding). Wrapping each string in its own Content
    # is what actually batches them into separate embeddings.
    contents = [types.Content(parts=[types.Part(text=t)]) for t in texts]

    backoff = _INITIAL_BACKOFF_SECONDS
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = _get_client().models.embed_content(
                model=config.GEMINI_EMBEDDING_MODEL,
                contents=contents,
                config=types.EmbedContentConfig(task_type=task_type),
            )
            return [e.values for e in response.embeddings]
        except errors.ClientError as e:
            if e.code != 429 or attempt == _MAX_RETRIES:
                raise
            print(f"    Rate limited, waiting {backoff}s before retry ({attempt + 1}/{_MAX_RETRIES})...")
            time.sleep(backoff)
            backoff *= 2


def generate_answer(question, context_block):
    prompt = (
        f"RULEBOOK EXCERPTS:\n\n{context_block}\n\n"
        f"QUESTION: {question}\n\n"
        "Answer using only the excerpts above."
    )
    response = _get_client().models.generate_content(
        model=config.GEMINI_GENERATION_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            # gemini-3.6-flash is a reasoning model -- its internal "thinking"
            # tokens are drawn from this same budget before any visible answer
            # text, so a low limit here silently truncates the answer (hits
            # MAX_TOKENS) long before it looks like it should have run out.
            max_output_tokens=2048,
        ),
    )
    return response.text
