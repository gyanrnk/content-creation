"""
build_worker.py — ek video ko ALAG process me build karta hai (app ko block nahi karta).

app.py ek job.json likhta hai + isse subprocess ke roop me chalata hai. Ye progress
`output/progress.txt` me likhta hai, aur khatam hone par `output/done.json` (ya fail par
`output/error.txt`). Streamlit sirf in files ko poll karta hai -> koi disconnect nahi.

Run (app khud karta hai): env\\Scripts\\python.exe build_worker.py job.json
"""

import os
import sys
import json
import shutil
import traceback

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config


def _prog(msg):
    try:
        with open(os.path.join(config.OUTPUT_DIR, "progress.txt"), "w",
                  encoding="utf-8") as f:
            f.write(msg)
    except Exception:
        pass


def run(jobfile):
    with open(jobfile, encoding="utf-8") as f:
        job = json.load(f)

    # settings apply
    for k, v in job.get("settings", {}).items():
        setattr(config, k, v)
    config.OUTPUT_DIR = "output"
    config.FINAL_VIDEO = "output/short.mp4"

    # fresh output
    shutil.rmtree("output", ignore_errors=True)
    os.makedirs("output", exist_ok=True)

    try:
        from script import generate_script, save_post_text
        from voice import generate_segment_voices
        from media import fetch_media
        from video import build_short
        from thumbnail import make_thumbnail

        _prog("📝 Script bana rahe...")
        data = generate_script(job.get("topic"), config.MODE, config.NUM_SEGMENTS,
                               custom_script=job.get("custom_script", ""))
        with open("output/script.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        save_post_text(data, "output/post.txt")

        _prog(f"🎙️ Voice bana rahe ({len(data['segments'])} segments)...")
        audio = generate_segment_voices(data["segments"],
                                        user_audio=job.get("user_audio") or None)

        _prog("🖼️ Images + video clips laa rahe (real photos + Pexels)...")
        media = fetch_media(data["segments"],
                            user_images=job.get("user_images") or None,
                            user_videos=job.get("user_videos") or None)

        _prog("🎬 Video render ho raha (yeh sabse lamba step hai)...")
        vp = build_short(data["segments"], media, audio, data)

        thumb = None
        if config.MAKE_THUMBNAIL:
            _prog("🖼️ Thumbnail...")
            thumb = make_thumbnail(data, media)

        # attribution credits -> description
        if os.path.exists("output/credits.txt"):
            with open("output/credits.txt", encoding="utf-8") as cf:
                with open("output/post.txt", "a", encoding="utf-8") as pf:
                    pf.write("\n\n" + cf.read())

        with open("output/done.json", "w", encoding="utf-8") as f:
            json.dump({"video": vp, "thumb": thumb, "data": data}, f,
                      ensure_ascii=False)
        _prog("✅ Done!")
    except Exception as e:
        with open("output/error.txt", "w", encoding="utf-8") as f:
            f.write(str(e) + "\n\n" + traceback.format_exc())
        _prog(f"❌ Error: {e}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "job.json")
