"""
bank_check.py — bank ke numbers purane to nahi ho gaye, ye batata he.

Kyun banaya: 12 Aug ko pata chala ki Ronaldo ke international goals bank me 143
the jabki WC 2026 ke baad 146 ho chuke the. Ek video us purane number ke saath
publish ho chuki thi. Bank chup-chaap sadta rehta he — koi error nahi aata,
bas number galat ho jaata he.

Ab har player pe do field he:
    volatile = true   -> abhi khel raha he, number badal sakta he
    volatile = false  -> retired/historical, number kabhi nahi badlega
    checked           -> aakhri baar kab verify hua

Ye script volatile stats ki umar dekhta he aur bolta he kya dobara check karna he.
Fixed stats kabhi expire nahi hote — unhe haath lagane ki zaroorat hi nahi.

Chalao:  python bank_check.py
"""

import os
import sys
import json
import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(ROOT, "data", "stat_bank.json")

WARN_DAYS = 30      # volatile stat itne din baad shak ke daayre me
STALE_DAYS = 60     # itne baad use hi mat karo


def _age(checked: str) -> int:
    try:
        d = datetime.date.fromisoformat(checked)
    except Exception:
        return 9999
    return (datetime.date.today() - d).days


def report() -> dict:
    with open(BANK, encoding="utf-8") as f:
        bank = json.load(f)

    rows = []
    for key, p in bank["players"].items():
        vol = p.get("volatile", True)          # pata na ho to volatile maano
        age = _age(p.get("checked", "1970-01-01"))
        state = "fixed" if not vol else ("stale" if age >= STALE_DAYS
                                         else "warn" if age >= WARN_DAYS else "ok")
        rows.append({"key": key, "name": p["name"], "volatile": vol,
                     "age": age, "state": state,
                     "stats": list(p.get("stats", {}).keys())})

    for r in bank.get("rankings", []):
        vol = r.get("volatile", True)
        age = _age(r.get("checked", "1970-01-01"))
        state = "fixed" if not vol else ("stale" if age >= STALE_DAYS
                                         else "warn" if age >= WARN_DAYS else "ok")
        rows.append({"key": r["id"], "name": r["title"], "volatile": vol,
                     "age": age, "state": state, "stats": ["ranking"]})

    return {"rows": rows,
            "stale": [r for r in rows if r["state"] == "stale"],
            "warn": [r for r in rows if r["state"] == "warn"],
            "fixed": [r for r in rows if r["state"] == "fixed"]}


def blocked_keys() -> set:
    """Wo entries jo itni purani he ki generator ko use nahi karni chahiye."""
    return {r["key"] for r in report()["stale"]}


if __name__ == "__main__":
    rep = report()
    icon = {"fixed": "🔒", "ok": "✅", "warn": "⚠️ ", "stale": "🔴"}
    print(f"{'':3} {'ENTRY':<18} {'AGE':>5}  STATS")
    print("-" * 62)
    for r in sorted(rep["rows"], key=lambda x: (x["state"] != "stale", x["state"] != "warn")):
        age = "—" if not r["volatile"] else f"{r['age']}d"
        print(f"{icon[r['state']]:3} {r['name'][:18]:<18} {age:>5}  {', '.join(r['stats'])[:32]}")

    print("-" * 62)
    print(f"🔒 {len(rep['fixed'])} fixed (kabhi check nahi karna)  "
          f"⚠️  {len(rep['warn'])} warn  🔴 {len(rep['stale'])} stale")
    if rep["stale"]:
        print("\n🔴 INHE DOBARA VERIFY KARO, warna galat number publish hoga:")
        for r in rep["stale"]:
            print(f"   - {r['name']} ({r['age']} din purana)")
    elif rep["warn"]:
        print("\n⚠️  Jaldi check kar lena:", ", ".join(r["name"] for r in rep["warn"]))
    else:
        print("\nSab taaza he.")
