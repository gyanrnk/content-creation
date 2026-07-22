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
import datetime

PENDING = os.path.join("data", "pending_scripts.json")
QUEUE = os.path.join("data", "script_queue.json")

# Bassi script kitne din baad bekaar? Mode pe depend karta he.
# News se juda content 2 din me purana ho jaata he ("Henry ne KAL ye bola",
# live standings, aane wala match). Career-journey / top-5 / legend wali kahaniyan
# kabhi bassi nahi hoti — unhe delete karna sirf nuksan he.
FRESH_DAYS = {"pundit": 2, "stats": 2, "preview": 2, "facts": 2, "controversy": 5}
DEFAULT_DAYS = 10          # story / ranking / wonderkid / debate — evergreen


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _age_days(item: dict) -> float:
    ts = item.get("created")
    if not ts:
        return 0.0                     # purani entries (date se pehle ki) -> nayi maano
    try:
        t = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc)
        return (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() / 86400
    except Exception:
        return 0.0


def is_stale(item: dict) -> bool:
    """Script itni purani he ki ab publish karna galat lagega?"""
    limit = FRESH_DAYS.get((item.get("mode") or "").lower(), DEFAULT_DAYS)
    return _age_days(item) > limit


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
    # ban-ne ka waqt yahin chipka do — umar approve se nahi, BANNE se ginni chahiye
    # (script 3 din pending padi rahe to approve hote hi wo pehle se bassi he)
    for it in items:
        it.setdefault("created", _now())
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
            it = dict(pend[i - 1])
            it.setdefault("created", _now())     # umar isi se naapi jaati he
            picked.append(it)
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
    """Sabse purana approved script nikaalo (FIFO). Khali ho to None.

    Bassi script yahin GIR jaati he — user: "agar aaj publish nahi hue to kal
    delete karo warna hum updated nahi rah payenge". News wale modes 2 din me
    bassi, evergreen (career journey / top-5) 10 din — dekho FRESH_DAYS.
    """
    q = _load(QUEUE)
    dropped = []
    while q:
        item = q.pop(0)
        if is_stale(item):
            dropped.append(item)
            continue
        if dropped:
            _drop_log(dropped)
        _save(QUEUE, q)
        return item
    if dropped:
        _drop_log(dropped)
        _save(QUEUE, q)
    return None


def _drop_log(dropped: list):
    for d in dropped:
        print(f"[queue] BASSI script hataayi ({_age_days(d):.1f} din purani, "
              f"mode={d.get('mode')}): {str(d.get('topic'))[:60]}")


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
