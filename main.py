"""
main.py — Football World Cup Shorts generator (9:16, Hindi voice + English subs).

Pipeline (NO heavy GPU — sab API/CPU based):
  1. script.py  → Hindi narration + English subtitles + image plan (GPT)
  2. voice.py   → per-segment Hindi voiceover (Sarvam AI)
  3. media.py   → real (Wikimedia/Pexels) + AI (Pollinations) images, 9:16
  4. video.py   → Ken Burns motion + subtitles + voice + BGM → short.mp4
  5. (optional) youtube_upload.py → upload as a Short

Bas `config.py` me TOPIC / MODE change karo aur is file ko run karo:
    env\Scripts\python.exe main.py
"""

import os
import sys
import json
import shutil

# Windows console ko UTF-8 par set karo (emoji/Hindi print ke liye)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import config
from script import generate_script, save_post_text, post_text
from voice import generate_segment_voices
from media import fetch_media
from video import build_short
from thumbnail import make_thumbnail


def run():
    print("\n⚽  FOOTBALL WORLD CUP SHORTS GENERATOR\n" + "=" * 45)
    print(f"Topic : {config.TOPIC}")
    print(f"Mode  : {config.MODE}   |   Segments: {config.NUM_SEGMENTS}")
    print(f"Format: {config.WIDTH}x{config.HEIGHT} @ {config.FPS}fps "
          f"(Hindi voice + English subs)\n")

    # Fresh output folder (ignore_errors -> locked file ho to crash nahi)
    shutil.rmtree(config.OUTPUT_DIR, ignore_errors=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    # 1. Script
    try:
        data = generate_script()
        segments = data["segments"]
        with open(os.path.join(config.OUTPUT_DIR, "script.json"), "w",
                  encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # Posting ke liye title/description/hashtags
        save_post_text(data, os.path.join(config.OUTPUT_DIR, "post.txt"))
    except Exception as e:
        print(f"❌ Script generation failed: {e}")
        sys.exit(1)

    # 2. Voice (per segment)
    try:
        print("\n🎙️  Generating Hindi voiceover...")
        audio_paths = generate_segment_voices(segments)
    except Exception as e:
        print(f"❌ Voice generation failed: {e}")
        sys.exit(1)

    # 3. Media (real photos + AI images + video clips)
    try:
        print("\n🖼️  Fetching media (images + video)...")
        media = fetch_media(segments)
    except Exception as e:
        print(f"❌ Media fetch failed: {e}")
        sys.exit(1)

    # 4. Build video
    try:
        print("\n🎬  Assembling short...")
        video_path = build_short(segments, media, audio_paths, data)
        if config.MAKE_THUMBNAIL:
            print("\n🖼️  Thumbnail...")
            make_thumbnail(data, media)
        # attribution credits -> description (CC-BY safe, video me nahi)
        cpath = os.path.join(config.OUTPUT_DIR, "credits.txt")
        if os.path.exists(cpath):
            with open(cpath, encoding="utf-8") as cf:
                creds = cf.read()
            with open(os.path.join(config.OUTPUT_DIR, "post.txt"), "a",
                      encoding="utf-8") as pf:
                pf.write("\n\n" + creds)
    except Exception as e:
        print(f"❌ Video build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 45)
    print(f"🎉  DONE!  Short ready: {video_path}")
    print("\n--- POST KARNE KE LIYE (output/post.txt me bhi saved) ---\n")
    print(post_text(data))
    print("=" * 45 + "\n")


if __name__ == "__main__":
    run()
