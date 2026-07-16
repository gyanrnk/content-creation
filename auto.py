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
# QUIZ-HEAVY (research: quiz = #1 faceless format — guess-the-player me log answer
# mann me dete + reveal tak rukte + tag karte). 6 me se 3 quiz, baaki engaging formats.
# (Top channels: quiz+debate+stats core; facts/story weaker the -> daily se hataya.)
_AUTO_MODES = ["quiz", "stats", "quiz", "debate", "quiz", "ranking"]


def _prog(msg: str):
    print(msg)
    try:
        os.makedirs(AUTO_DIR, exist_ok=True)
        with open(os.path.join(AUTO_DIR, "progress.txt"), "w", encoding="utf-8") as f:
            f.write(msg)
    except Exception:
        pass


def _send_mail(subject: str, body: str, attach: str = None):
    """Har short ban-ne par turant email (Gmail SMTP), VIDEO attached (inbox me hi
    mil jaaye — GitHub download ki zaroorat nahi). MAIL_USERNAME/MAIL_PASSWORD chahiye.
    Video 24MB+ ho to attach nahi (Gmail limit) — sirf note."""
    import smtplib
    from email.message import EmailMessage
    user = os.getenv("MAIL_USERNAME")
    pw = os.getenv("MAIL_PASSWORD")
    if not (user and pw):
        return
    # 18MB cap: base64 encode ~37% inflate karta hai -> Gmail 25MB limit me rahe.
    can_attach = bool(attach and os.path.exists(attach)
                      and os.path.getsize(attach) < 18 * 1024 * 1024)
    if attach and os.path.exists(attach) and not can_attach:
        body += ("\n\n(Video bada hai — email me attach nahi ho payi; GitHub Actions "
                 "artifact se download karo.)")
    try:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = user, user, subject
        msg.set_content(body)
        if can_attach:
            with open(attach, "rb") as f:
                msg.add_attachment(f.read(), maintype="video", subtype="mp4",
                                   filename=os.path.basename(attach))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=180) as s:
            s.login(user, pw.replace(" ", ""))   # app-password bina spaces
            s.send_message(msg)
        print(f"[auto] 📧 email sent{' (video attached)' if can_attach else ''}: {subject}")
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
    # AUTO_MODE env se ek mode FORCE kar sakte ho (e.g. abhi wala hot stats short).
    forced = os.getenv("AUTO_MODE", "").strip().lower()
    if forced and forced not in _AUTO_MODES:
        print(f"[auto] unknown AUTO_MODE={forced!r} — rotation use karenge")
        forced = ""
    if forced:
        print(f"[auto] MODE FORCED -> {forced}")
    plan = []
    for i in range(n):
        mode = forced or _AUTO_MODES[(day_off + hour + i) % len(_AUTO_MODES)]
        if i == 0 and query:
            topic, key = query, query          # user hint -> pehla video usi pe
        else:
            topic, key = topic_for_mode(mode, i, query, used)
        used.add(key)                          # is batch me dobara na aaye
        plan.append((topic, mode, key))

    print(f"\n🤖 AUTO-PILOT — {n} shorts\n" + "=" * 45)
    # Auto-upload sirf tab jab token.json ho (cloud pe secret se banta hai; local pe nahi).
    do_upload = os.path.exists("token.json")
    privacy = os.getenv("UPLOAD_PRIVACY", "public")
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
            vpath = os.path.join(out_dir, "short.mp4")
            results.append({"topic": topic, "mode": mode, "ok": True,
                            "dir": out_dir, "title": title, "video": vpath})

            # --- ban-ne ke turant baad UPLOAD (agar token hai) ---
            yt_url = ""
            if do_upload:
                try:
                    import upload_youtube
                    yt_url = upload_youtube.upload_from_output(privacy, outdir=out_dir)
                    results[-1]["url"] = yt_url
                    print(f"[auto] ⬆️ uploaded ({privacy}): {yt_url}")
                except Exception as ue:
                    yt_url = f"__FAIL__{ue}"
                    print(f"[auto] ⚠️ upload failed: {ue}")

            # --- phir EMAIL (upload ke baad, live link ke saath) ---
            run_url = os.getenv("RUN_URL", "")
            tail = (f"\n(GitHub run: {run_url})" if run_url else "")
            if yt_url.startswith("http"):                    # upload success
                _send_mail(
                    f"✅ Short {i}/{n} LIVE: {title[:55]}",
                    f"[{mode}] {title}\nTopic: {topic}\n\n"
                    f"🎉 YouTube pe LIVE ho gaya ({privacy}):\n{yt_url}\n" + tail)
            elif yt_url.startswith("__FAIL__"):              # bana par upload fail
                _send_mail(
                    f"⚠️ Short {i}/{n} bana, UPLOAD FAIL: {title[:45]}",
                    f"[{mode}] {title}\nTopic: {topic}\n\n"
                    f"Upload error: {yt_url[8:]}\nVideo attached — manually daal do.\n" + tail,
                    attach=vpath)
            else:                                            # upload off (local)
                _send_mail(
                    f"🎬 Short {i}/{n} ready: {title[:60]}",
                    f"[{mode}] {title}\nTopic: {topic}\n\n"
                    "Video email me attached hai. ⚽\n" + tail,
                    attach=vpath)
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
    print(f"\n🎉 {ok}/{len(results)} ready in '{run_dir}'  (auto-upload on cloud)\n")
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
