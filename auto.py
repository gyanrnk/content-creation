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
# MATURE data (48h+ purane videos) se — NAYE video ke views dekh ke faisla MAT karo,
# wo 0-2 se 600-900 tak badhte hain (Norway quiz: 3 -> 612; France facts: 1 -> 959):
#   facts/story (ek bade player/event ki kahani): 1623, 1300, 1120, 1090, 959, 822  <- JEET
#   quiz (Pehchaan kaun)                        : 777, 612                          <- chalta hai!
#   ranking (Top 5)                             : 241, 103                          <- theek
#   debate (X vs Y)                             : 45, 8, 8                          <- sabse kamzor
# Isliye: facts/story heavy + quiz wapas; debate abhi bahar (sabse kam). Variety bhi
# rehti hai (inauthentic-policy safe). RULE: 48h se naye video pe format mat badlo.
_AUTO_MODES = [
    "story",         # emotional angle rotate (tragedy/rejected/injury/mentality/migration)
    "controversy",   # outrage + debate = highest comment rate
    "wonderkid",     # 14-24 audience, low competition, evergreen search
    "stats",         # live numbers (Golden Boot / league table)
    "ranking",       # controversial countdown
    "pundit",        # "why everyone is talking about X"
]


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


def _publish_at_iso(offset: int = 0):
    """Scheduled publish ("offline push") ke liye ISO-UTC timestamp + IST display.
    Video PRIVATE upload hoti hai, YouTube use PEAK time pe khud PUBLIC karta —
    build kabhi bhi ho (cron flaky), publish exact peak pe. India Shorts peak:
    7-10 PM IST (+ midday). Slot nikal gaya (build already peak/late) -> (None, None) = turant public."""
    IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now = datetime.datetime.now(IST)
    # BUG FIX: pehle "hour % len(slots)" se slot chunta tha -> kabhi PAST slot aa jaata
    # (5 PM build ko 1:30 PM mil gaya) -> schedule cancel hoke turant public ho jaata.
    # Ab: sirf FUTURE evening slots me se chuno, offset se un्ही me spread.
    evening = [(19, 0), (20, 0), (21, 0), (22, 0)]        # India Shorts peak
    # Build KHUD peak me ho raha he (7 PM ke baad) -> schedule karne ka matlab nahi,
    # turant public karo. Warna shaam ke dono late builds 10 PM pe dher ho jaate the.
    if now.hour >= evening[0][0]:
        return None, None
    future = []
    for h, m in evening:
        t = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if t > now + datetime.timedelta(minutes=6):
            future.append(t)
    if not future:                       # saare slot nikal gaye (late build) -> turant
        return None, None
    # BUG FIX 2: har cron run n=1 video banata he, to offset HAMESHA 0 tha -> har build
    # ko future[0] milta tha -> din ke saare videos EK HI 7 PM slot pe dher ho jaate the
    # (aaj dono 13:30Z pe schedule hue). Ab slot BUILD KE GHANTE se chunte he — stateless,
    # isliye queue-persist bug se bhi safe. 11-12 IST->7PM, 13-14->8PM, 15-16->9PM, 17+->10PM.
    idx = (now.hour - 11) // 2 + offset
    target = future[min(max(idx, 0), len(future) - 1)]
    iso = target.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    disp = target.strftime("%I:%M %p IST").lstrip("0")
    return iso, disp


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
        # SIRF pichhle ~12 subjects (≈2 din) ka dedup. Pura history dekhne se
        # Messi/Ronaldo/Yamal hamesha "used" rehte the -> TRENDING kabhi pick hi
        # nahi hota tha (videos random players pe ban rahe the). Hot player ko
        # 2 din baad naye angle se dobara banana theek hai.
        used = history.used("subjects", last=12)
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
            # APPROVED queue se hi banao. User ne "strict review" chuna (option A):
            # queue khali = koi video NAHI (bina review kuch publish na ho).
            approved = None
            try:
                import queue_scripts
                approved = queue_scripts.pop()
            except Exception as qe:
                print(f"[auto] queue padhne me dikkat ({qe})")
            if not approved and getattr(config, "REQUIRE_APPROVED_SCRIPT", True):
                print("[auto] ⏸️  Approved queue KHALI — is slot me koi video nahi "
                      "(review app me approve karo). Strict review ON hai.")
                results.append({"topic": topic, "ok": False,
                                "error": "no approved script in queue"})
                # Ek hi baar batao (har slot pe 6 mail na aayein)
                if not globals().get("_QUEUE_MAIL_SENT"):
                    globals()["_QUEUE_MAIL_SENT"] = True
                    _send_mail(
                        "⏸️ Video nahi bana — approved queue khali",
                        "Strict review ON hai, aur queue me koi approved script nahi,\n"
                        "isliye is slot me koi video publish NAHI hua.\n\n"
                        "👉 Review app me jaake approve karo:\n"
                        f"{getattr(config, 'REVIEW_APP_URL', '')}\n\n"
                        "(Har slot pe video chahiye bina review ke, to config me\n"
                        " REQUIRE_APPROVED_SCRIPT = False kar dena.)")
                continue
            if approved:
                topic = approved.get("topic", topic)
                mode = approved.get("mode", mode)
                print(f"[auto] ✅ APPROVED script use ho raha (queue me "
                      f"{queue_scripts.count()} aur bache)")
            data = batch.build_one(topic, mode, out_dir,
                                   data=(approved or {}).get("data"))
            if history:
                history.mark("subjects", key)  # future runs isko repeat na karein
            title = (data or {}).get("youtube_title") or topic
            vpath = os.path.join(out_dir, "short.mp4")
            results.append({"topic": topic, "mode": mode, "ok": True,
                            "dir": out_dir, "title": title, "video": vpath})

            # --- ban-ne ke baad UPLOAD — TURANT public (scheduling BAND) ---
            # 16 July ko maine scheduled publish daala tha (private upload -> 7 PM pe
            # public). Soch thi ki peak time pe jaayegi to zyada views. ULTA HUA:
            #   14-16 Jul (bina scheduling): 1471 / 2143 / 1600 total views/din
            #   17 Jul se (scheduling ke saath): 798 / 792 / 249 / 113 / 119
            # Lagta he Shorts feed video ko UPLOAD ke waqt se test karta he, publish ke
            # waqt se nahi — to 7 PM tak wo algorithm ke liye purani ho chuki hoti thi.
            # Ab peak timing CRON se aati he (workflow me crons peak hours me hain) aur
            # video bante hi turant public jaati he. Wapas laana ho to:
            #   pub_at, pub_disp = _publish_at_iso(i - 1) if do_upload else (None, None)
            yt_url = ""
            pub_at, pub_disp = (None, None)
            if do_upload:
                try:
                    import upload_youtube
                    yt_url = upload_youtube.upload_from_output(
                        privacy, outdir=out_dir, publish_at=pub_at)
                    results[-1]["url"] = yt_url
                    print(f"[auto] ⬆️ uploaded "
                          f"({'scheduled ' + pub_disp if pub_at else privacy}): {yt_url}")
                except Exception as ue:
                    yt_url = f"__FAIL__{ue}"
                    print(f"[auto] ⚠️ upload failed: {ue}")

            # --- DATA LOG: script + voice + render + youtube (fine-tune ke liye) ---
            try:
                import datalog
                datalog.log_build(
                    mode, topic, data, video_path=vpath,
                    yt_url=(yt_url if yt_url.startswith("http") else None),
                    publish_at=pub_at, privacy=privacy,
                    provider=(data or {}).get("_provider"))
            except Exception as le:
                print(f"[auto] datalog skip ({le})")

            # --- phir EMAIL (upload ke baad, live/scheduled link ke saath) ---
            run_url = os.getenv("RUN_URL", "")
            tail = (f"\n(GitHub run: {run_url})" if run_url else "")
            if yt_url.startswith("http") and pub_at:         # scheduled at peak
                _send_mail(
                    f"⏰ Short {i}/{n} SCHEDULED ({pub_disp}): {title[:45]}",
                    f"[{mode}] {title}\nTopic: {topic}\n\n"
                    f"⏰ YouTube khud PUBLIC karega peak time pe: {pub_disp}\n{yt_url}\n"
                    "(abhi private hai, us time apne-aap live ho jaayega)\n" + tail)
            elif yt_url.startswith("http"):                  # upload success (immediate)
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
