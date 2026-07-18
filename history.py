"""
history.py — cross-video asset dedup.

Jo real photos / Pexels clips pehle ki videos me use ho chuke, unhe track karta hai
taaki har NAYI video me ALAG visuals aayein (same image/clip reuse na ho).

`asset_history.json` project root me save hota hai.
"""

import os
import json

_PATH = os.path.join(os.path.dirname(__file__), "asset_history.json")
_CAP = 800   # per kind, purane bhulte jao


def _load() -> dict:
    try:
        with open(_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(d: dict):
    try:
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception:
        pass


def used(kind: str, last: int = None) -> set:
    """kind = 'real_photos' | 'pexels_ids' | 'subjects'. Used keys ka set.

    last = sirf AAKHRI N entries (list append-order me hai, to aakhri = sabse naye).
    Trending subjects ke liye zaroori: pura history dekhein to Messi/Ronaldo hamesha
    "used" rehte hain aur TRENDING kabhi pick hi nahi hota — hot player hafte baad
    naye angle se dobara banana theek hai, bas turant repeat nahi.
    """
    lst = [str(k) for k in _load().get(kind, [])]
    if last is not None:
        lst = lst[-last:]
    return set(lst)


def mark(kind: str, key) -> None:
    d = _load()
    lst = d.get(kind, [])
    key = str(key)
    if key in lst:
        return
    lst.append(key)
    d[kind] = lst[-_CAP:]
    _save(d)
