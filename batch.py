"""
batch.py — Ek saath KAI shorts generate karta hai (daily content backlog).

topics.txt me har line ek topic likho. Optional: "topic | mode" format
(mode = facts/player/preview). Khaali line / # comment ignore hota hai.

Example topics.txt:
    Brazil vs Japan — compare legends and predict winner | preview
    5 mind-blowing FIFA World Cup 2026 facts | facts
    Cristiano Ronaldo World Cup journey | player

Run:
    env\\Scripts\\python.exe batch.py
    env\\Scripts\\python.exe batch.py mytopics.txt
"""

import os
import sys
import re
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
from script import generate_script, save_post_text
from voice import generate_segment_voices
from media import fetch_media
from video import build_short
from thumbnail import make_thumbnail


def _slug(text: str, n: int) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return f"{n:02d}_{s[:40]}"


def _read_topics(path: str):
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "|" in line:
                topic, mode = [p.strip() for p in line.split("|", 1)]
            else:
                topic, mode = line, config.MODE
            items.append((topic, mode))
    return items


def build_one(topic: str, mode: str, out_dir: str, data: dict = None) -> dict:
    """Ek video out_dir me banata hai. config paths temporarily set karta hai.

    data = pehle se APPROVED script (queue se). Diya ho to naya generate NAHI hoga —
    bilkul wahi script use hoga jo user ne review/approve kiya.
    """
    # config paths is video ke liye point karo (functions call-time par padhte hain)
    config.OUTPUT_DIR = out_dir
    config.FINAL_VIDEO = os.path.join(out_dir, "short.mp4")
    os.makedirs(out_dir, exist_ok=True)

    # custom_script="" -> config.CUSTOM_SCRIPT (purana leftover) ignore karo,
    # hamesha TOPIC se generate karo (warna auto-pilot topic bekaar ho jaata hai)
    if data is None:
        data = generate_script(topic, mode, config.NUM_SEGMENTS, custom_script="")
    segments = data["segments"]
    with open(os.path.join(out_dir, "script.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    save_post_text(data, os.path.join(out_dir, "post.txt"))

    audio_paths = generate_segment_voices(segments)
    media = fetch_media(segments, mode=mode)
    build_short(segments, media, audio_paths, data)
    if config.MAKE_THUMBNAIL:
        make_thumbnail(data, media, os.path.join(out_dir, "thumbnail.jpg"))
    return data


def run(topics_file: str = "topics.txt"):
    if not os.path.exists(topics_file):
        print(f"❌ '{topics_file}' nahi mila. Ek banao — har line me ek topic.")
        print("   Example line:  Brazil vs Japan predict winner | preview")
        sys.exit(1)

    topics = _read_topics(topics_file)
    if not topics:
        print("❌ topics.txt khaali hai.")
        sys.exit(1)

    base = os.path.join("output", "batch")
    print(f"\n⚽ BATCH MODE — {len(topics)} videos\n" + "=" * 45)

    results = []
    for i, (topic, mode) in enumerate(topics, 1):
        out_dir = os.path.join(base, _slug(topic, i))
        print(f"\n[{i}/{len(topics)}] {mode.upper()} :: {topic}\n -> {out_dir}")
        try:
            build_one(topic, mode, out_dir)
            results.append((topic, "✅", os.path.join(out_dir, "short.mp4")))
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            results.append((topic, "❌", str(e)))

    print("\n" + "=" * 45 + "\n📊 BATCH SUMMARY")
    for topic, status, info in results:
        print(f"  {status}  {topic[:45]}")
    ok = sum(1 for _, s, _ in results if s == "✅")
    print(f"\n🎉 {ok}/{len(results)} videos ready in '{base}'\n")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "topics.txt")
