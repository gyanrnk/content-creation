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

# 5 DISTINCT varieties. n=5 (daily default) => har format ka EK-EK short (full variety).
# n<5 => day-offset rotation se har din alag format. Sab generic auto topics pe kaam karte.
_AUTO_MODES = ["facts", "story", "ranking", "quiz", "debate"]


def _prog(msg: str):
    print(msg)
    try:
        os.makedirs(AUTO_DIR, exist_ok=True)
        with open(os.path.join(AUTO_DIR, "progress.txt"), "w", encoding="utf-8") as f:
            f.write(msg)
    except Exception:
        pass


def _send_mail(subject: str, body: str):
    """Har short ban-ne par turant email (Gmail SMTP). MAIL_USERNAME/MAIL_PASSWORD
    env/.env me chahiye (Actions me secrets se). Na ho to chup-chaap skip."""
    import smtplib
    from email.message import EmailMessage
    user = os.getenv("MAIL_USERNAME")
    pw = os.getenv("MAIL_PASSWORD")
    if not (user and pw):
        return
    try:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = user, user, subject
        msg.set_content(body)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
            s.login(user, pw.replace(" ", ""))   # app-password bina spaces
            s.send_message(msg)
        print(f"[auto] 📧 email sent: {subject}")
    except Exception as e:
        print(f"[auto] email skip: {e}")


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
    try:
        import history
        used = history.used("subjects")       # cross-run/cross-day subject dedup
    except Exception:
        history, used = None, set()
    # Day + HOUR offset rotation: har GHANTE wala staggered cron run ALAG variety de
    # (10:30=facts, 11:30=story, ...), aur roz shuruaat shift ho. (hour = run ka ghanta.)
    now = datetime.datetime.now()
    day_off = now.timetuple().tm_yday
    hour = now.hour
    plan = []
    for i in range(n):
        mode = _AUTO_MODES[(day_off + hour + i) % len(_AUTO_MODES)]
        if i == 0 and query:
            topic, key = query, query          # user hint -> pehla video usi pe
        else:
            topic, key = topic_for_mode(mode, i, query, used)
        used.add(key)                          # is batch me dobara na aaye
        plan.append((topic, mode, key))

    print(f"\n🤖 AUTO-PILOT — {n} shorts\n" + "=" * 45)
    results = []
    for i, (topic, mode, key) in enumerate(plan, 1):
        out_dir = os.path.join(run_dir, batch._slug(topic, i))
        _prog(f"[{i}/{n}] 🎬 [{mode}] {topic}")
        print(f" -> {out_dir}")
        try:
            data = batch.build_one(topic, mode, out_dir)
            if history:
                history.mark("subjects", key)  # future runs isko repeat na karein
            title = (data or {}).get("youtube_title") or topic
            results.append({"topic": topic, "mode": mode, "ok": True,
                            "dir": out_dir, "title": title,
                            "video": os.path.join(out_dir, "short.mp4")})
            # HAR short ban-ne ke turant baad email
            run_url = os.getenv("RUN_URL", "")
            _send_mail(
                f"🎬 Short {i}/{n} ready: {title[:60]}",
                f"[{mode}] {title}\nTopic: {topic}\n\n"
                + (f"Run/logs: {run_url}\n" if run_url else "")
                + "Poora batch complete hone par video download link (artifact) milega.\n"
                + "Review karke YouTube pe daalo. ⚽")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results.append({"topic": topic, "ok": False, "error": str(e)})
            _send_mail(f"❌ Short {i}/{n} FAILED: {topic[:50]}", f"Error: {e}")

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
