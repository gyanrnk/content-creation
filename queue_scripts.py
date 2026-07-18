"""
queue_scripts.py — APPROVED scripts ka queue (human-in-the-loop).

Kyun: user script ki quality khud review karna chahta hai, par ROZ time nahi de
sakta. Solution: ek baithak me 5-10 script approve karo -> queue me chale jaate
hain -> cron roz queue me se EK nikaal ke video banata + publish karta hai.
Approval BATCH me, publishing ROZ = quality bhi, consistency bhi.

Files (data/ me, Actions commit-back karta hai to cloud ko bhi dikhte hain):
  data/pending_scripts.json  -> review ke liye bane candidates (abhi approved nahi)
  data/script_queue.json     -> APPROVED, build hone ka intezaar

Flow:
  1. python make_scripts.py 5     -> 5 candidate banao (pending me)
  2. Claude tumhe dikhata hai, tum approve/edit karte ho
  3. Claude approved ko queue me daal deta hai (approve())
  4. cron/auto.py queue se pop karke build+publish karta hai
"""

import os
import json

PENDING = os.path.join("data", "pending_scripts.json")
QUEUE = os.path.join("data", "script_queue.json")


def _load(path: str) -> list:
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except Exception:
        return []


def _save(path: str, items: list):
    os.makedirs("data", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)


# ── pending (review ke liye) ───────────────────────────────────────────────────
def set_pending(items: list):
    _save(PENDING, items)


def get_pending() -> list:
    return _load(PENDING)


def approve(indexes: list) -> int:
    """pending me se diye gaye index (1-based) approve karke QUEUE me daalo."""
    pend = get_pending()
    q = _load(QUEUE)
    picked = []
    for i in indexes:
        if 1 <= i <= len(pend):
            picked.append(pend[i - 1])
    q.extend(picked)
    _save(QUEUE, q)
    # approved ko pending se hatao
    rest = [p for j, p in enumerate(pend, 1) if j not in set(indexes)]
    _save(PENDING, rest)
    return len(picked)


# ── queue (build ke liye) ──────────────────────────────────────────────────────
def count() -> int:
    return len(_load(QUEUE))


def peek() -> list:
    return _load(QUEUE)


def pop():
    """Sabse purana approved script nikaalo (FIFO). Khali ho to None."""
    q = _load(QUEUE)
    if not q:
        return None
    item = q.pop(0)
    _save(QUEUE, q)
    return item


def add(items: list):
    """Seedha queue me daalo (jab Claude edit karke final script bana de)."""
    q = _load(QUEUE)
    q.extend(items)
    _save(QUEUE, q)
    return len(q)


if __name__ == "__main__":
    print(f"pending (review baaki): {len(get_pending())}")
    print(f"queue   (approved)    : {count()}")
    for i, it in enumerate(peek(), 1):
        print(f"  {i}. [{it.get('mode')}] {it.get('topic')} — {it.get('data',{}).get('youtube_title','')[:50]}")
