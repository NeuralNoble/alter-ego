# tiny_retriever.py
import re, json, functools

# ---- load once at startup -------------------------------------------
with open("data/chunks.json", encoding="utf-8") as f:
    CHUNKS = json.load(f)

# pre-group by section for O(1) fetch
BY_SECTION = functools.reduce(
    lambda d,c: d.setdefault(c["section"], []).append(c["text"]) or d, CHUNKS, {}
)

# ---- regex intent router --------------------------------------------
INTENT_RE = {
    r"\b(project|github|built)\b"           : "project",
    r"\b(experience|job|work(ed)?)\b"       : "experience",
    r"\b(skill|stack|tool|tech)\b"          : "skills",
    r"\b(educat|degree|study|college)\b"    : "education",
    r"\b(contact|email|phone|linked[in]?)\b": "contact",
    r"\b(summary|about|intro)\b"            : "summary",
}

def route(query: str) -> str | None:
    q = query.lower()
    for pat, sec in INTENT_RE.items():
        if re.search(pat, q):
            return sec
    return None     # fallback: whole résumé

def build_context(user_query: str) -> str:
    sec = route(user_query)
    if sec:
        parts = BY_SECTION[sec]
    else:
        # include everything, but keep order for readability
        parts = [c["text"] for c in CHUNKS]
    return "\n\n".join(parts)
