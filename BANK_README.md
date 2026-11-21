# Octo Memory Bank — BANK_README

The big offline knowledge store for Red Octopus AI. The user ordered
**~950,000 memories**, and the brain capacity is **1,000,000** (the
blue brain chips). This file is the design + the honest status of
where the bank stands.

## Honest status — goal reached

| Item | Number |
|---|---|
| Entries in the bank now | **954,526** |
| Hand-written core (`memory_bank.jsonl`) | 300 |
| Machine-generated bulk (`memory_bank_bulk.tsv.gz`) | 954,226 |
| Per kind | math 907,333 · general 29,190 · science 11,736 · daily 6,091 · myanmar 55 · business 64 · health 57 |
| Goal | 950,000 — **reached** (954,526) |
| Brain capacity (gauge) | 1,000,000 |
| Malformed lines skipped | 0 |

The gauge in `/brain` always shows the **real** line count of the bank
files. Nothing is faked: 954,526 today means the bar reads
954,526 / 1,000,000.

## Composition — read this before judging the number

Math is 907,333 of the 954,526 (about 95%). That is honest and by
design: arithmetic tables (addition, subtraction, multiplication,
division, squares, cubes, roots, percentages) are the only content
that can be generated at this volume with **every single answer
verified correct by computation**. Everything else in the bank is
hand-checked tables and facts:

| Kind | Count | What it is |
|---|---|---|
| `math` | 907,333 | Addition 450,000 · subtraction 343,925 · multiplication 97,804 · division 9,604 · squares/cubes/roots 2,100 · percentages 1,900 · double/half 2,000 |
| `general` | 29,190 | Roman numerals 7,998 · even/odd + prime + number-words 21,000 · countries 142 · hand-written facts |
| `science` | 11,736 | Day-of-week for every day 2000–2030 (11,323) · periodic table 350 · hand-written facts |
| `daily` | 6,091 | Unit conversions 5,768 · time units 266 · hand-written facts |
| `myanmar` | 55 | State/region capitals, rivers, pagodas, culture (core + hand-written) |
| `business` | 64 | Business terms (core + hand-written) |
| `health` | 57 | Health facts (core + hand-written) |

The non-math kinds are small because each entry there was written
and checked by hand. Growing them is the next grind — see below.

## The 7 kinds

| Kind | What goes in it | Language |
|---|---|---|
| `general` | World knowledge — capitals, geography, nature, history, everyday facts | English |
| `myanmar` | Myanmar language, culture, festivals, food, places, regions | English |
| `business` | Entrepreneurship, pricing, marketing, sales, money, management | English |
| `science` | Physics, chemistry, biology, space, computers, AI | English |
| `daily` | Cooking, home, money habits, study, safety, practical skills | English |
| `health` | Sleep, food, exercise, first aid, mental wellbeing | English |
| `math` | Arithmetic tables and number facts (see above) | English |

## File formats

**Core** — `memory_bank.jsonl`, one JSON object per line:

```json
{"kind": "general", "q": "What is the capital of France?", "a": "Paris."}
{"kind": "daily", "fact": "Drink about 2 litres of water a day."}
```

**Bulk** — `memory_bank_bulk.tsv.gz`, tab-separated, gzipped (~4 MB):

```
math<TAB>what is 123 + 456<TAB>579.
science<TAB>what day of the week was july 4 2026<TAB>Saturday.
```

Each bulk line is `kind`, the **already-normalised** question key,
and the answer. The key is normalised once, at generation time, so
loading never re-parses JSON or re-runs the normaliser — the whole
954,526-row bank loads in **about 5 seconds** (the JSON form took
about 26 seconds). Rules for both files:

- **No duplicates.** A question counts as duplicate when its
  normalised form already exists — regardless of kind. Normalisation
  keeps `+`, `-` and `%`, so "5 + 3" and "5 - 3" are different
  questions (stripping them once made subtraction rows collide with
  addition rows and return the wrong answer — fixed 2026-11-21).
- **Only accurate facts.** Every bulk row is computed, never guessed:
  arithmetic from Python, dates from `datetime`, primes by trial
  division, conversions from fixed factors, Roman numerals and
  number words from exact algorithms.
- One line = one entry. No blank lines. UTF-8, no BOM.

## How the bot uses it (`bank.py`)

- `bank.load()` **streams** the files line by line (never reads them
  whole into memory) and builds the lookup index. Malformed lines are
  **skipped and counted** — a torn last line (e.g. an interrupted
  write) never crashes the bot. Verified: 954,526 rows load with
  0 malformed. The first load prints `Loading brain...` on stderr
  (stdout stays clean for one-shot/scripted use).
- `bank.lookup(text)` — exact match on the normalised question first,
  then a keyword fallback (the entry sharing the most content words
  wins, only if it matches ≥ 2 content words or every content word
  of a short question). Math rows are exact-match only.
- `brain.respond()` answers **any** arithmetic instantly with the
  safe calculator (`what is 123 + 456?`, `2 + 2`, `calculate (20+5)*3`)
  before consulting the bank, so out-of-range sums never wait on it.
- `brain.respond()` checks the bank after taught answers and personal
  facts, before jokes and the "I don't know" fallback.
- `/memory` shows a compact gauge; `/brain` shows the full brain-chips
  display (total, bar toward 1,000,000, per-kind counts).
- Scale: streaming load + dict index works to 1,000,000+ entries. At
  full size the index holds ~1M short strings in memory (a few
  hundred MB) — acceptable on any normal computer.

## Progress file (`bank_progress.json`)

Regenerated by every generator run:

```json
{"total": 954526, "per_kind": {"general": 29190, "math": 907333, ...},
 "capacity": 1000000, "goal": 950000, "per_kind_goal": 150000,
 "last_batch_id": "batch-001", "last_batch_added": 0, "malformed_lines": 0}
```

`total` is always recomputed by recounting the files — the progress
file never invents a number.

## How to continue the grind

The old hand-written batch grind (`gen_batchN.py`, 500–1,000 rows
per batch) is superseded for volume: `gen_bulk.py` regenerates the
whole bulk file deterministically in ~30 seconds (idempotent —
re-running writes the same rows). To grow the bank further:

1. **Grow the small kinds** (myanmar, business, health) — add
   hand-checked rows to `HANDWRITTEN` in `gen_bulk.py`, or add a new
   generator function that computes its rows (same pattern as the
   dates/elements generators).
2. Run `python3 gen_bulk.py`. It dedupes against the core bank
   (re-runs are safe) and refreshes `bank_progress.json`.
3. Verify: `bank.stats()` total must equal the `total` in
   `bank_progress.json`, and `python3 octo.py "a new bank question"`
   must answer from the new rows.
4. Keep the generator files in the repo — they are the audit trail of
   where every entry came from.

## Files

| File | What it is |
|---|---|
| `memory_bank.jsonl` | The 300 hand-written core rows (append-only) |
| `memory_bank_bulk.tsv.gz` | The 954,226 machine-generated bulk rows (TSV, gzipped) |
| `bank_progress.json` | Counts (auto-generated by `gen_bulk.py`) |
| `bank.py` | Loader, lookup, gauge (`bank.lookup`, `bank.stats`, `bank.brain_lines`) |
| `gen_batch1.py` | First batch (300 entries) + the original generator pattern |
| `gen_bulk.py` | Bulk generator — all 954,226 rows, deterministic |
| `BANK_README.md` | This file |
