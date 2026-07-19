"""
make_scripts.py — REVIEW ke liye script candidates banao (video NAHI banti, fast).

Chalao:
    python make_scripts.py 5          # 5 candidate (auto topic/mode)
    python make_scripts.py 3 story    # 3 candidate, sirf story mode

Ye sirf SCRIPT banata hai (koi image/voice/render nahi) -> har candidate ~20-30 sec.
Candidates data/pending_scripts.json me chale jaate hain; Claude tumhe dikhata hai,
tum approve karte ho, phir wo queue me jaate hain aur cron unse video banata hai.
"""

import sys

import config
import queue_scripts
from ideas import topic_for_mode
from script import generate_script

DEFAULT_MODES = ["story", "facts", "pundit", "stats", "ranking"]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    only_mode = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        import history
        used = history.used("subjects", last=12)
    except Exception:
        used = set()

    out = []
    for i in range(n):
        mode = only_mode or DEFAULT_MODES[i % len(DEFAULT_MODES)]
        topic, key = topic_for_mode(mode, i, None, used)
        used.add(key)
        print(f"\n[{i+1}/{n}] {mode} :: {topic}")
        try:
            data = generate_script(topic, mode, config.NUM_SEGMENTS, custom_script="")
            # sthir id — review UI widget keys isse bandhe hote hain (index se nahi,
            # warna ek approve karte hi baaki fields purani value dikhane lagte the)
            import uuid
            out.append({"id": uuid.uuid4().hex[:12], "mode": mode, "topic": topic,
                        "key": key, "data": data})
            print(f"    TITLE: {data.get('youtube_title')}")
            for j, s in enumerate(data.get("segments", []), 1):
                print(f"      {j}. {s.get('voice_english','')}")
        except Exception as e:
            print(f"    FAILED: {e}")

    queue_scripts.set_pending(out)
    print(f"\n{len(out)} candidate -> data/pending_scripts.json (review ke liye)")

    # Email: "script ready — review karo" + UI ka link (mobile pe kholo)
    try:
        import os
        from auto import _send_mail
        url = os.getenv("REVIEW_APP_URL", "") or getattr(config, "REVIEW_APP_URL", "")
        lines = "\n".join(
            f"{i}. [{c['mode']}] {c['data'].get('youtube_title','')}"
            for i, c in enumerate(out, 1))
        _send_mail(
            f"📝 {len(out)} naye script review ke liye taiyaar",
            f"{len(out)} script ban gaye hain — review/approve karo:\n\n{lines}\n\n"
            + (f"👉 Review karo (phone pe khol sakte ho):\n{url}\n\n" if url else
               "(REVIEW_APP_URL set karo to yahan seedha link aayega)\n\n")
            + "Approve karte hi cron un scripts se video banayega.")
    except Exception as e:
        print(f"[make_scripts] mail skip ({e})")


if __name__ == "__main__":
    main()
