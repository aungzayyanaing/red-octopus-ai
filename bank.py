"""Memory bank for Red Octopus AI — the big offline knowledge store.

memory_bank.jsonl holds one JSON object per line:
  {"kind": "general", "q": "What is the capital of France?", "a": "Paris."}
  {"kind": "daily",   "fact": "Drink about 2 litres of water a day."}

Six kinds (target ~150,000 each, ~950,000 total):
  general, myanmar, business, science, daily, health

Design for 1,000,000+ entries:
  - the file is streamed line by line, never read whole into memory
  - malformed lines are skipped and counted — a torn last line
    (e.g. an upload interrupted mid-write) never crashes the bot
  - the lookup index is built lazily on first use and cached
  - exact/normalised-question lookup first, keyword fallback second
  - bank_progress.json tracks per-kind counts so the grind that
    fills the bank is resumable and idempotent

The number Octo reports is ALWAYS the real entry count of the
bank file — never a made-up number.
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BANK_FILE = os.path.join(HERE, "memory_bank.jsonl")
PROGRESS_FILE = os.path.join(HERE, "bank_progress.json")
CAPACITY = 1_000_000

KINDS = ["general", "myanmar", "business", "science", "daily", "health"]

KIND_LABELS = {
    "general": "General knowledge",
    "myanmar": "Myanmar language & culture",
    "business": "Business & markets",
    "science": "Science & technology",
    "daily": "Daily life",
    "health": "Health",
}

_PUNCT_RE = re.compile(r"[^\w]+", re.UNICODE)

# Words too common to be useful for keyword matching.
STOPWORDS = set(
    "a an the is are was were what who whom whose which when where why how "
    "do does did can could will would should may might i you he she it we they "
    "my your his her its our their me him us them this that these those there "
    "here and or but if then so as at by for in on of to from with about into "
    "over after before between through under am be been being have has had not "
    "no yes please tell give show know".split()
)
_INDEX = None       # normalised question -> answer
_KEYWORDS = None    # word -> set of entry ids
_ANSWERS = None     # entry id -> answer/fact text
_TOTAL = 0
_PER_KIND = {}
_MALFORMED = 0


def normalize(text):
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.strip().lower()
    text = _PUNCT_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokenize(text):
    words = normalize(text).split()
    return [w for w in words
            if len(w) >= 2 and w not in STOPWORDS]


def load():
    """Stream the bank file once and build the lookup index."""
    global _INDEX, _KEYWORDS, _ANSWERS, _TOTAL, _PER_KIND, _MALFORMED
    if _INDEX is not None:
        return
    _INDEX, _KEYWORDS, _ANSWERS = {}, {}, []
    _TOTAL = 0
    _PER_KIND = {k: 0 for k in KINDS}
    _MALFORMED = 0
    try:
        f = open(BANK_FILE, "r", encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                _MALFORMED += 1
                continue
            if not isinstance(obj, dict):
                _MALFORMED += 1
                continue
            kind = obj.get("kind")
            if kind not in KINDS:
                _MALFORMED += 1
                continue
            text_for_keywords = None
            answer = None
            if "q" in obj and "a" in obj:
                q, a = str(obj["q"]).strip(), str(obj["a"]).strip()
                if not q or not a:
                    _MALFORMED += 1
                    continue
                key = normalize(q)
                if key in _INDEX:
                    continue  # duplicate question: keep the first
                _INDEX[key] = a
                answer = a
                text_for_keywords = q
            elif "fact" in obj:
                fact = str(obj["fact"]).strip()
                if not fact:
                    _MALFORMED += 1
                    continue
                answer = fact
                text_for_keywords = fact
            else:
                _MALFORMED += 1
                continue
            eid = len(_ANSWERS)
            _ANSWERS.append(answer)
            for w in set(_tokenize(text_for_keywords)):
                _KEYWORDS.setdefault(w, set()).add(eid)
            _PER_KIND[kind] += 1
            _TOTAL += 1


def lookup(text):
    """Answer from the bank, or None.

    1. Exact match on the normalised question.
    2. Keyword fallback: the entry sharing the most content words
       with the question wins, but only when it matches at least
       two content words, or every content word of a short question.
    """
    load()
    key = normalize(text)
    if key in _INDEX:
        return _INDEX[key]
    tokens = _tokenize(text)
    if not tokens:
        return None
    scores = {}
    for t in set(tokens):
        for eid in _KEYWORDS.get(t, ()):  # noqa: B007 - set lookup
            scores[eid] = scores.get(eid, 0) + 1
    if not scores:
        return None
    best_eid, best_score = max(
        scores.items(), key=lambda kv: (kv[1], -len(_ANSWERS[kv[0]])))
    if best_score >= 2 or best_score == len(tokens):
        return _ANSWERS[best_eid]
    return None


def stats():
    """Real bank numbers: total, per-kind counts, capacity, bad lines."""
    load()
    return {
        "total": _TOTAL,
        "per_kind": dict(_PER_KIND),
        "capacity": CAPACITY,
        "malformed": _MALFORMED,
        "file": BANK_FILE,
    }


def gauge_bar(width=20):
    """(bar_string, fraction_filled) — the brain-chips gauge."""
    s = stats()
    pct = (s["total"] / s["capacity"]) if s["capacity"] else 0.0
    filled = int(round(pct * width))
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled), pct


def gauge_lines():
    """Compact gauge for /memory — total + bar only."""
    s = stats()
    bar, pct = gauge_bar()
    return [
        "  Brain memories: %s / %s"
        % (format(s["total"], ","), format(s["capacity"], ",")),
        "  [%s] %.1f%%" % (bar, pct * 100),
    ]


def brain_lines():
    """Full brain-chips display for /brain — total, bar, per-kind."""
    s = stats()
    bar, pct = gauge_bar()
    lines = []
    lines.append("Octo's brain — Brain Chips")
    lines.append("  Memories: %s / %s"
                 % (format(s["total"], ","), format(s["capacity"], ",")))
    lines.append("  [%s] %.1f%%" % (bar, pct * 100))
    lines.append("  By kind:")
    for kind in KINDS:
        lines.append("    %s: %s"
                     % (KIND_LABELS[kind],
                        format(s["per_kind"].get(kind, 0), ",")))
    if s["malformed"]:
        lines.append("  (%d malformed lines skipped)" % s["malformed"])
    lines.append("  Goal: 950,000 memories — about 150,000 per kind.")
    return lines
