"""
datalog.py — HAR build ka poora record store karta hai (script + voice + render +
youtube), taaki baad me DATA se pata chale kya kaam kar raha hai — guess se nahi.

Kyun: abhi humein pata nahi chalta ki kaunsa HOOK / mode / length / voice-setting
zyada views laaya. Ye log jama hota rahega; baad me views ke saath jodkar
script-generation aur voice ko DATA-DRIVEN fine-tune kar sakte hain.

File: data/build_log.jsonl   (har line = ek video)
GitHub Actions ise commit-back karta hai -> record roz jama hote rehte hain.

Analysis: `python datalog.py` -> abhi tak ka summary (mode/length/hook stats).
"""

import os
import re
import json
import datetime
import subprocess

LOG = os.path.join("data", "build_log.jsonl")


def _duration(path: str):
    """Video ki length (sec) — ffmpeg header se, sasta."""
    try:
        import imageio_ffmpeg
        out = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", path],
                             capture_output=True, text=True).stderr
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
        if m:
            return round(int(m.group(1)) * 3600 + int(m.group(2)) * 60
                         + float(m.group(3)), 1)
    except Exception:
        pass
    return None


def log_build(mode: str, topic: str, data: dict, video_path: str = None,
              yt_url: str = None, publish_at: str = None, privacy: str = None,
              provider: str = None):
    """Ek build ka record append karo. NEVER raise — build kabhi na ruke."""
    try:
        import config
        segs = (data or {}).get("segments", []) or []
        lines = [(s.get("voice_english") or "") for s in segs]
        rec = {
            "ts": datetime.datetime.now(datetime.timezone.utc)
                          .strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": mode,
            "topic": topic,
            "provider": provider,                    # gemini / groq / pollinations
            "title": (data or {}).get("youtube_title"),
            "hook": (data or {}).get("hook_english"),
            "cta": (data or {}).get("cta_english"),
            "segments": [
                {"voice_en": t,
                 "words": len(t.split()),
                 "image_type": s.get("image_type"),
                 "image_query": s.get("image_query")}
                for s, t in zip(segs, lines)
            ],
            "script_stats": {
                "n_segments": len(segs),
                "total_words": sum(len(t.split()) for t in lines),
                "avg_words": round(sum(len(t.split()) for t in lines)
                                   / max(1, len(lines)), 1),
            },
            "voice": {"engine": getattr(config, "VOICE_PROVIDER", ""),
                      "name": getattr(config, "EDGE_VOICE", ""),
                      "rate": getattr(config, "EDGE_RATE", ""),
                      "pitch": getattr(config, "EDGE_PITCH", "")},
            "render": {"num_segments": getattr(config, "NUM_SEGMENTS", None),
                       "ken_burns_zoom": getattr(config, "KEN_BURNS_ZOOM", None),
                       "fast_cuts": getattr(config, "FAST_CUTS", None),
                       "animated_captions": getattr(config, "ANIMATED_CAPTIONS", None)},
            "video": {
                "duration_s": _duration(video_path) if video_path else None,
                "size_mb": (round(os.path.getsize(video_path) / 1e6, 2)
                            if video_path and os.path.exists(video_path) else None),
            },
            "youtube": {"url": yt_url,
                        "id": (yt_url or "").rsplit("/", 1)[-1] or None,
                        "publish_at": publish_at,
                        "privacy": privacy},
            "views": None,      # baad me analysis ke waqt bhara jaayega
        }
        os.makedirs("data", exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"[datalog] recorded -> {LOG}")
    except Exception as e:
        print(f"[datalog] skip ({e})")


def load() -> list:
    """Saare records padho."""
    if not os.path.exists(LOG):
        return []
    out = []
    with open(LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def summary():
    """Abhi tak ka data — kya trend hai (views bharne ke baad aur kaam ka)."""
    recs = load()
    if not recs:
        print("koi record nahi — abhi builds hone do")
        return
    print(f"TOTAL builds logged: {len(recs)}\n")
    by_mode = {}
    for r in recs:
        by_mode.setdefault(r.get("mode"), []).append(r)
    print("mode        | count | avg_len | avg_words | avg_views")
    print("-" * 55)
    for m, rs in sorted(by_mode.items()):
        durs = [r["video"]["duration_s"] for r in rs if r.get("video", {}).get("duration_s")]
        wrds = [r["script_stats"]["avg_words"] for r in rs if r.get("script_stats")]
        vws = [r["views"] for r in rs if r.get("views") is not None]
        print(f"{str(m):11s} | {len(rs):5d} | "
              f"{(sum(durs)/len(durs) if durs else 0):6.1f}s | "
              f"{(sum(wrds)/len(wrds) if wrds else 0):9.1f} | "
              f"{(sum(vws)/len(vws) if vws else 0):9.1f}")
    print("\n(views abhi khali — analysis ke waqt YouTube se bhar ke trend nikalenge)")


if __name__ == "__main__":
    summary()
