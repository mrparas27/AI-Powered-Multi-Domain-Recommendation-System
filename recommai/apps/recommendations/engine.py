import math
import re
from collections import Counter


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text):
    return TOKEN_RE.findall((text or "").lower())


def cosine_score(query, document):
    q_tokens = Counter(tokenize(query))
    d_tokens = Counter(tokenize(document))
    if not q_tokens or not d_tokens:
        return 0.0
    shared = set(q_tokens) & set(d_tokens)
    numerator = sum(q_tokens[t] * d_tokens[t] for t in shared)
    q_norm = math.sqrt(sum(v * v for v in q_tokens.values()))
    d_norm = math.sqrt(sum(v * v for v in d_tokens.values()))
    return numerator / (q_norm * d_norm) if q_norm and d_norm else 0.0


def rank_items(query, items, text_getter, limit=10):
    scored = []
    for item in items:
        score = cosine_score(query, text_getter(item))
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [{"score": round(score, 4), "item": item} for score, item in scored[:limit]]
