"""
auto.py — AUTO-PILOT: topic khud uthata hai -> script + short bana ke ready rakhta hai.

Fully-auto: ideas.py se aaj ke topics pick karta hai (tumhe kuch type nahi karna),
batch me 3-5 shorts banata hai, alag-alag folder me. Upload MANUAL (abhi ke liye).

Ye Phase 3 scheduler ki neev hai — headless chalta hai, poll-able progress likhta hai.

Run:
    env\\Scripts\\python.exe auto.py            # 3 shorts (default)
    env\\Scripts\\python.exe auto.py 5          # 5 shorts
    env\\Scripts\\python.exe auto.py 4 "Messi records"   # topic hint (trending is par jhukega)

Output:
    output/auto/<timestamp>/01_<slug>/short.mp4 (+ thumbnail, post.txt, credits.txt)
    output/auto/done.json     -> latest run ka summary (app isse padhta hai)
    output/auto/progress.txt  -> live progress (app poll karta hai)
"""

import os
import sys
import json
import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
import batch
from ideas import get_ideas

AUTO_DIR = os.path.join("output", "auto")

# Content-variety rotation (research-backed mix; all work on generic auto topics).
# facts sabse zyada (evergreen/shareable), phir story/ranking/quiz/debate.
_AUTO_MODES = ["facts", "story", "ranking", "quiz", "facts", "debate"]


def _prog(msg: str):
    print(msg)
    try:
        os.makedirs(AUTO_DIR, exist_ok=True)
        with open(os.path.join(AUTO_DIR, "progress.txt"), "w", encoding="utf-8") as f:
            f.write(msg)
    except Exception:
        pass


def _apply_settings():
    """Agar output/auto/settings.json hai (app ne likha), config me apply karo."""
    p = os.path.join(AUTO_DIR, "settings.json")
    if not os.path.exists(p):
        return
    try:
        with open(p, encoding="utf-8") as f:
            for k, v in json.load(f).items():
                setattr(config, k, v)
    except Exception:
        pass


def autopilot(n: int = 3, query: str = None) -> dict:
    """n shorts auto-topic se banata hai. Summary dict return karta hai."""
    os.makedirs(AUTO_DIR, exist_ok=True)
    _apply_settings()
    # purane status files hatao (run dirs rehne do — abhi tak upload nahi hue honge)
    for f in ("done.json", "error.txt"):
        p = os.path.join(AUTO_DIR, f)
        if os.path.exists(p):
            os.remove(p)

    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    run_dir = os.path.join(AUTO_DIR, stamp)

    _prog("💡 Topics + modes chun rahe (variety + matched)...")
    # Har slot ke liye: mode rotate karo, phir us mode ke LIYE fitting topic banao
    # (ranking->'Top 5 X', debate->'X vs Y', quiz->player). Agar user ne query di to
    # pehla video usi pe (facts).
    from ideas import topic_for_mode
    plan = []
    for i in range(n):
        mode = _AUTO_MODES[i % len(_AUTO_MODES)]
        if i == 0 and query:
            topic = query          # user hint -> pehla video usi pe
        else:
            topic = topic_for_mode(mode, i, query)
        plan.append((topic, mode))

    print(f"\n🤖 AUTO-PILOT — {n} shorts\n" + "=" * 45)
    results = []
    for i, (topic, mode) in enumerate(plan, 1):
        out_dir = os.path.join(run_dir, batch._slug(topic, i))
        _prog(f"[{i}/{n}] 🎬 [{mode}] {topic}")
        print(f" -> {out_dir}")
        try:
            batch.build_one(topic, mode, out_dir)
            results.append({"topic": topic, "mode": mode, "ok": True,
                            "dir": out_dir,
                            "video": os.path.join(out_dir, "short.mp4")})
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results.append({"topic": topic, "ok": False, "error": str(e)})

    ok = sum(1 for r in results if r["ok"])
    summary = {"run_dir": run_dir, "stamp": stamp,
               "total": len(results), "ok": ok, "results": results}
    with open(os.path.join(AUTO_DIR, "done.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 45 + "\n📊 AUTO-PILOT SUMMARY")
    for r in results:
        mark = "✅" if r["ok"] else "❌"
        print(f"  {mark}  {r['topic'][:45]}")
    _prog(f"✅ Done — {ok}/{len(results)} shorts ready in {run_dir}")
    print(f"\n🎉 {ok}/{len(results)} ready in '{run_dir}'  (upload manual)\n")
    return summary


if __name__ == "__main__":
    try:
        n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    except ValueError:
        n = 3
    q = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        autopilot(n, q)
    except Exception as e:
        import traceback
        os.makedirs(AUTO_DIR, exist_ok=True)
        with open(os.path.join(AUTO_DIR, "error.txt"), "w", encoding="utf-8") as f:
            f.write(str(e) + "\n\n" + traceback.format_exc())
        _prog(f"❌ Error: {e}")
        raise
