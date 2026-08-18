import re

MAX_CHUNK_CHARS = 1100
MIN_CHUNK_CHARS = 100

_HEADER_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_NUMBERED_LINE_RE = re.compile(r"^\s*\d+(?:\.\d+)*[.)]?\s+", re.MULTILINE)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def chunk_markdown(text, source_file):
    text = _HTML_COMMENT_RE.sub("", text) # strips html comments.
    blocks = _parse_blocks(text) # splits doc into sections by md headers.
    game_name = _derive_game_name(blocks, source_file) # finds game name from top level header or falls back to filename.
    blocks = _merge_tiny_blocks(blocks) # Merges header sections that are too short to be useful on their own.

    chunks = []
    for block in blocks:
        body = block["body"].strip()
        if not body:
            continue
        for piece in _split_oversized(body, MAX_CHUNK_CHARS):
            chunks.append(
                {
                    "text": piece,
                    "source_file": source_file,
                    "game_name": game_name,
                    "section_path": block["breadcrumb"],
                }
            )

    for i, chunk in enumerate(chunks):
        chunk["chunk_index"] = i

    return chunks


def _derive_game_name(blocks, source_file):
    for block in blocks:
        if block["level"] == 1 and block["title"]:
            return block["title"]
    stem = source_file.rsplit(".", 1)[0]
    return stem.replace("_", " ").replace("-", " ").title()


def _parse_blocks(text):
    """Split into (header, body-until-next-header) blocks, tracking a
    breadcrumb per block from the header hierarchy (e.g. 'Soccer > Fouls > Red Card')."""
    headers = list(_HEADER_RE.finditer(text))
    blocks = []
    stack = []  # list of (level, title)

    if not headers:
        return [{"level": 0, "title": "", "breadcrumb": "", "body": text}]

    if headers[0].start() > 0:
        blocks.append({"level": 0, "title": "", "breadcrumb": "", "body": text[: headers[0].start()]})

    for i, match in enumerate(headers):
        level = len(match.group(1))
        title = match.group(2).strip()
        body_start = match.end()
        body_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[body_start:body_end]

        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))
        breadcrumb = " > ".join(t for _, t in stack)

        blocks.append({"level": level, "title": title, "breadcrumb": breadcrumb, "body": body})

    return blocks


def _merge_tiny_blocks(blocks):
    """A header followed by only a short one-liner gets folded into the
    next sibling block rather than emitted as a context-free micro-chunk."""
    merged = []
    carry = ""
    for block in blocks:
        body = carry + block["body"] if carry else block["body"]
        carry = ""
        if len(body.strip()) < MIN_CHUNK_CHARS and block is not blocks[-1]:
            carry = body + "\n\n"
            continue
        merged.append({**block, "body": body})

    if carry and merged:
        merged[-1]["body"] += carry

    return merged


def _split_oversized(body, max_chars):
    if len(body) <= max_chars:
        return [body]

    numbered = _split_keep_delim(body, _NUMBERED_LINE_RE)
    if len(numbered) > 1:
        return _pack(numbered, max_chars, _split_paragraphs)

    paragraphs = _split_paragraphs(body)
    if len(paragraphs) > 1:
        return _pack(paragraphs, max_chars, _split_sentences)

    sentences = _split_sentences(body)
    if len(sentences) > 1:
        return _pack(sentences, max_chars, None)

    return [body]


def _split_keep_delim(text, pattern):
    matches = list(pattern.finditer(text))
    if not matches:
        return [text]
    segments = []
    start = 0
    for m in matches[1:]:
        segments.append(text[start : m.start()])
        start = m.start()
    segments.append(text[start:])
    segments = [s for s in segments if s.strip()]
    return segments if len(segments) > 1 else [text]


def _split_paragraphs(text):
    parts = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    return parts if len(parts) > 1 else [text]


def _split_sentences(text):
    parts = [p for p in _SENTENCE_SPLIT_RE.split(text) if p.strip()]
    return parts if len(parts) > 1 else [text]


def _pack(segments, max_chars, next_splitter):
    """Greedily reassemble segments into chunks up to max_chars, recursively
    re-splitting any segment that's still oversized with next_splitter."""
    expanded = []
    for seg in segments:
        if len(seg) > max_chars and next_splitter:
            expanded.extend(next_splitter(seg))
        else:
            expanded.append(seg)

    chunks = []
    current = ""
    for seg in expanded:
        candidate = f"{current}\n\n{seg}" if current else seg
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            chunks.append(current.strip())
            current = seg
    if current:
        chunks.append(current.strip())
    return chunks
