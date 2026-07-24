"""
GEMINI CLIPS -> SHORT (do command, baaki sab automatic)

Kyun: Google AI Pro (Jio offer) Gemini APP me Veo deta he, par API pe nahi
(napa: veo-3.1 dono models 429 dete he). To clip banana manual he — par sirf
wahi. Baaki sab pipeline karta he: Hindi voice, captions, hook, watermark,
title/description, YouTube upload, build-log (quota guard ke liye).

FLOW:
  1) py gemini_build.py prompts
       -> queue ki agli approved script ke liye VEO PROMPTS chhaap deta he
  2) Gemini app me har prompt daalo -> video download karo
     -> assets/gemini/ me daal do (naam me 1,2,3... rakhna, order wahi rahega)
  3) py gemini_build.py build
       -> short ban ke YouTube pe public upload ho jaata he

Clip kam ho to bhi chalega — jitne he utne cycle karke lagenge.
"""
import glob
import os
import sys

CLIP_DIR = "assets/gemini"
VID_EXT = (".mp4", ".mov", ".webm", ".m4v")


def _next_script(pop=False):
    import queue_scripts as Q
    items = Q.peek()
    if not items:
        return None
    return Q.pop() if pop else items[0]


def _veo_prompt(seg, idx):
    """Segment se ek acchha Veo prompt — cinematic, vertical, bina naam ke.

    Naam JAAN-BOOJH KE nahi daalte: AI asli chehra bana nahi paata (test kiya —
    'Messi' maanga to ajnabi aadmi aaya), aur asli khiladi ka AI chehra likeness
    ka panga he. Isliye ATMOSPHERE maangte he — stadium, crowd, boots, ball.
    """
    line = (seg.get("subtitle_english") or seg.get("voice_english") or "").lower()
    # line ke MOOD se scene chuno — warna prompt "Norway" jaisa khokhla ban jaata he
    if any(w in line for w in ("goal", "scored", "score", "net", "finish")):
        scene = ("striker's boot striking a ball into the net, net rippling, "
                 "floodlit stadium erupting behind")
    elif any(w in line for w in ("sign", "transfer", "joined", "million", "deal", "clause")):
        scene = ("empty stadium tunnel at night, boots walking towards bright pitch light, "
                 "shirt hanging in a dressing room")
    elif any(w in line for w in ("trophy", "treble", "title", "won", "champion", "record")):
        scene = ("golden trophy under stadium lights, confetti falling in slow motion, "
                 "packed stands blurred behind")
    elif any(w in line for w in ("father", "boy", "young", "child", "academy", "start")):
        scene = ("young boy dribbling alone on a wet floodlit pitch at dusk, "
                 "long shadows, misty air")
    elif any(w in line for w in ("fans", "crowd", "petition", "angry", "shock")):
        scene = ("packed stadium crowd roaring in slow motion, scarves raised, "
                 "flares glowing in the stands")
    else:
        scene = ("football rolling on wet grass under floodlights, "
                 "stadium haze, dramatic rim light")
    return (f"Cinematic vertical 9:16 video, {scene}. Slow motion, shallow depth of "
            f"field, moody film grade, volumetric floodlight beams. No text, no logos, "
            f"no faces visible, no real people identifiable. 6 seconds.")


def cmd_prompts():
    item = _next_script()
    if not item:
        print("Queue khali he — review app me scripts approve karo pehle.")
        return
    d = item.get("data", {})
    segs = d.get("segments", [])
    print("=" * 68)
    print("SCRIPT:", d.get("title_english") or item.get("topic"))
    print("=" * 68)
    print("\nGemini app me ye prompts ek-ek karke daalo, video download karke")
    print(f"'{CLIP_DIR}' folder me 1.mp4, 2.mp4 ... naam se rakho.\n")
    for i, s in enumerate(segs, 1):
        print(f"--- {i}.mp4 -------------------------------------------------")
        print(_veo_prompt(s, i))
        print()
    print("Sab clip aa jaane ke baad:  py gemini_build.py build")


def cmd_build():
    clips = sorted(f for f in glob.glob(os.path.join(CLIP_DIR, "*"))
                   if f.lower().endswith(VID_EXT))
    if not clips:
        print(f"{CLIP_DIR} me koi clip nahi mili. Pehle 'prompts' chalao.")
        return
    print(f"[gemini] {len(clips)} clip mili")

    item = _next_script(pop=True)
    if not item:
        print("Queue khali he — pehle script approve karo.")
        return
    data = item["data"]
    segs = data.get("segments", [])
    print(f"[gemini] script: {data.get('title_english')}")

    import config
    import voice
    import video as V
    # clips cycle karke har segment ko background do
    media = [{"type": "video", "path": clips[i % len(clips)]} for i in range(len(segs))]
    auds = voice.generate_segment_voices(segs)
    out = V.build_short(segs, media, auds, data)
    print("[gemini] bana:", out)

    # upload — wahi rasta jo cloud use karta he
    import datetime
    import json
    from upload_youtube import upload_from_output
    outdir = os.path.dirname(out)
    url = upload_from_output("public", outdir=outdir)
    print("[gemini] UPLOADED:", url)

    # build_log — warna cloud ka quota-guard is video ko ginega nahi
    rec = {"ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "mode": item.get("mode", "gemini"), "topic": item.get("topic"),
           "provider": "gemini-clips", "title": data.get("title_english"),
           "video": {"clips": len(clips)}, "url": url}
    with open("data/build_log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[gemini] build_log me darj — ab clips hata sakte ho.")


if __name__ == "__main__":
    os.makedirs(CLIP_DIR, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prompts"
    (cmd_build if cmd == "build" else cmd_prompts)()
