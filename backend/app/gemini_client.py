from google import genai
from google.genai import types

from app import config

_client = None

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
    # A flat list[str] is treated by the SDK as multiple *parts* of one Content
    # (and returns a single embedding). Wrapping each string in its own Content
    # is what actually batches them into separate embeddings.
    contents = [types.Content(parts=[types.Part(text=t)]) for t in texts]
    response = _get_client().models.embed_content(
        model=config.GEMINI_EMBEDDING_MODEL,
        contents=contents,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [e.values for e in response.embeddings]


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
            max_output_tokens=512,
        ),
    )
    return response.text
