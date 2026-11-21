"""Memory bank for Red Octopus AI — the big offline knowledge store.

memory_bank.jsonl holds the 300 hand-written rows, one JSON object
per line:
  {"kind": "general", "q": "What is the capital of France?", "a": "Paris."}
  {"kind": "daily",   "fact": "Drink about 2 litres of water a day."}

memory_bank_bulk.tsv.gz holds the machine-generated bulk rows
(~950,000, written by gen_bulk.py) as tab-separated lines:
  kind <TAB> normalised-question <TAB> answer
The question key is normalised once, at generation time, so loading
never re-parses JSON or re-runs the normaliser — the whole bank
loads in seconds. Gzipped, the file is ~4 MB, safe for GitHub.

Seven kinds (goal 950,000 total):
  general, myanmar, business, science, daily, health, math
Math dominates the bulk file (addition/subtraction/multiplication
tables are the only content that can be generated at this volume
with every answer verified correct), so per-kind counts are uneven
by design — see BANK_README.md for the honest breakdown.

Design for 1,000,000+ entries:
  - the files are streamed line by line, never read whole into memory
  - malformed lines are skipped and counted — a torn last line
    (e.g. an upload interrupted mid-write) never crashes the bot
  - the lookup index is built lazily on first use and cached
  - exact/normalised-question lookup first, keyword fallback second
  - math rows are exact-match only (their questions are always asked
    in canonical form, and skipping their keyword index keeps the
    first load fast)
  - bank_progress.json tracks per-kind counts so the grind that
    fills the bank is resumable and idempotent

The number Octo reports is ALWAYS the real entry count of the
bank files — never a made-up number.
"""

import gzip
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BANK_FILE = os.path.join(HERE, "memory_bank.jsonl")
BULK_FILE = os.path.join(HERE, "memory_bank_bulk.tsv.gz")
BANK_FILES = [BANK_FILE, BULK_FILE]
PROGRESS_FILE = os.path.join(HERE, "bank_progress.json")
CAPACITY = 1_000_000

KINDS = ["general", "myanmar", "business", "science", "daily", "health",
         "math"]

KIND_LABELS = {
    "general": "General knowledge",
    "myanmar": "Myanmar language & culture",
    "business": "Business & markets",
    "science": "Science & technology",
    "daily": "Daily life",
    "health": "Health",
    "math": "Mathematics",
}

# Keep + - % in normalised questions: "5 + 3" and "5 - 3" must stay
# different questions (stripping them made subtraction rows collide
# with addition rows and look up the wrong answer).
_PUNCT_RE = re.compile(r"[^\w+\-%]+", re.UNICODE)

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


def _tokenize(normalised):
    """Content words from an already-normalised string."""
    return [w for w in normalised.split()
            if len(w) >= 2 and w not in STOPWORDS]


def _open_bank(path):
    """Plain .jsonl or .tsv.gz — same line-by-line iteration."""
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def _iter_rows(path):
    """Yield (kind, key, answer) rows from a bank file.

    .jsonl: JSON objects with q/a or fact (keys normalised here).
    .tsv.gz: kind TAB normalised-key TAB answer (already normalised).
    """
    with _open_bank(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if path.endswith(".tsv.gz"):
                parts = line.split("\t")
                if len(parts) != 3:
                    yield None
                    continue
                kind, key, answer = parts
                if not kind or not key or not answer:
                    yield None
                    continue
                yield (kind, key, answer)
                continue
            try:
                obj = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                yield None
                continue
            if not isinstance(obj, dict):
                yield None
                continue
            kind = obj.get("kind")
            if "q" in obj and "a" in obj:
                q, a = str(obj["q"]).strip(), str(obj["a"]).strip()
                if not q or not a:
                    yield None
                    continue
                yield (kind, normalize(q), a)
            elif "fact" in obj:
                fact = str(obj["fact"]).strip()
                if not fact:
                    yield None
                    continue
                yield (kind, normalize(fact), fact)
            else:
                yield None


def load():
    """Stream the bank files once and build the lookup index."""
    global _INDEX, _KEYWORDS, _ANSWERS, _TOTAL, _PER_KIND, _MALFORMED
    if _INDEX is not None:
        return
    _INDEX, _KEYWORDS, _ANSWERS = {}, {}, []
    _TOTAL = 0
    _PER_KIND = {k: 0 for k in KINDS}
    _MALFORMED = 0
    if os.path.exists(BULK_FILE):
        # The big file takes a few seconds; say so on stderr (stdout
        # stays clean for one-shot/scripted use).
        sys.stderr.write("Loading brain...\n")
        sys.stderr.flush()
    for bank_file in BANK_FILES:
        if not os.path.exists(bank_file):
            continue
        for row in _iter_rows(bank_file):
            if row is None:
                _MALFORMED += 1
                continue
            kind, key, answer = row
            if kind not in KINDS:
                _MALFORMED += 1
                continue
            if key in _INDEX:
                continue  # duplicate question: keep the first
            _INDEX[key] = answer
            # Math rows are exact-match only: their questions are
            # always asked in canonical form, and skipping their
            # keyword index keeps the first load fast.
            if kind == "math":
                _PER_KIND[kind] += 1
                _TOTAL += 1
                continue
            eid = len(_ANSWERS)
            _ANSWERS.append(answer)
            for w in set(_tokenize(key)):
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
    tokens = _tokenize(key)
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
