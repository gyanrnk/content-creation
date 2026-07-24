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

# jab line kisi mood-bucket me na baithe — index se ghoomte he taaki ek hi video me
# saare clips same na ban jaayein
_FALLBACKS = [
    "football rolling on wet grass under floodlights, stadium haze, dramatic rim light",
    "aerial shot of a floodlit stadium at night, empty pitch, light beams cutting fog",
    "close-up of football boots pounding wet turf, water spraying, low camera angle",
    "corner flag trembling in wind, blurred packed stands behind, golden hour light",
    "goal net from behind, stadium lights flaring through the mesh, slow push-in",
    "dressing room bench with a folded shirt and boots, single overhead lamp, dust in air",
]

# har bucket = (keywords, scene-variants). Variants isliye taaki ek hi mood ki
# saari lines pe alag-alag clip bane.
_BUCKETS = [
    (("goal", "scored", "score", "net", "finish", "hat-trick"), [
        "striker's boot striking a ball into the net, net rippling, floodlit stadium erupting",
        "ball hitting the top corner of a goal net in extreme slow motion, water droplets flying",
        "goalkeeper diving across the frame as a ball blurs past, stadium lights streaking",
    ]),
    (("sign", "transfer", "joined", "million", "deal", "clause", "club"), [
        "empty stadium tunnel at night, boots walking towards bright pitch light",
        "a football shirt hanging alone in a dark dressing room, single spotlight, dust in air",
        "private jet on a night runway, stadium glow on the horizon, cinematic haze",
    ]),
    (("trophy", "treble", "title", "won", "champion", "record", "history"), [
        "golden trophy under stadium lights, confetti falling in slow motion",
        "trophy cabinet filling with silverware, warm museum lighting, slow dolly",
        "gold confetti raining over an empty podium, floodlights flaring behind",
    ]),
    (("father", "boy", "young", "child", "academy", "start", "age"), [
        "young boy dribbling alone on a wet floodlit pitch at dusk, long shadows",
        "small worn football boots on a concrete street pitch, golden evening light",
        "a child's silhouette juggling a ball against a huge stadium in the distance",
    ]),
    (("fans", "crowd", "petition", "angry", "shock", "protest"), [
        "packed stadium crowd roaring in slow motion, scarves raised, flares glowing",
        "sea of waving flags in a stadium stand, smoke drifting through floodlight beams",
        "thousands of phone flashlights twinkling in a dark stadium, slow aerial drift",
    ]),
    (("said", "debate", "pundit", "row", "accused", "criticis", "slam",
      "argue", "claim", "tv", "studio", "media"), [
        "empty TV studio with glowing screens and microphones, camera lights flaring",
        "close-up of a broadcast microphone under harsh studio light, dark background",
        "wall of television screens flickering in a dark control room, blue rim light",
        "newspaper pages flying through the air in slow motion, dramatic side light",
    ]),
]


def _photo_card(pil_img, W, H):
    """Player ki asli photo ko rounded card bana ke return karo (RGBA)."""
    from PIL import Image, ImageDraw
    cw = int(W * 0.62)
    chh = int(cw * 1.15)
    p = pil_img.convert("RGB")
    s = max(cw / p.width, chh / p.height)
    p = p.resize((max(1, int(p.width * s)), max(1, int(p.height * s))), Image.LANCZOS)
    p = p.crop(((p.width - cw) // 2, 0, (p.width - cw) // 2 + cw, chh))
    card = Image.new("RGBA", (cw + 16, chh + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw + 15, chh + 15], radius=26, fill=(255, 255, 255, 235))
    mask = Image.new("L", (cw, chh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw - 1, chh - 1], radius=20, fill=255)
    card.paste(p, (8, 8), mask)
    return card


def _clip_with_photo(clip_path, photo, duration, idx):
    """Gemini clip = chalta hua BACKGROUND, asli photo = upar CARD.

    Kyun: sirf AI clip lagane pe video script se align nahi hota — script me
    khiladi ka naam hota he aur screen pe khali stadium/studio (user ne pakda).
    Sirf photo lagane pe motion nahi hoti. Dono milake: motion BHI, pehchaan BHI.
    """
    import numpy as np
    from moviepy.editor import CompositeVideoClip, ImageClip
    from PIL import Image, ImageEnhance, ImageFilter

    import config
    import video as V

    bg = V._video_bg(clip_path, duration)
    if photo is None:
        return bg

    # background ko halka dabao taaki card upar ubhre
    def _dim(frame):
        im = Image.fromarray(frame).filter(ImageFilter.GaussianBlur(2))
        return np.asarray(ImageEnhance.Brightness(im).enhance(0.55))

    bg = bg.fl_image(_dim)
    card = _photo_card(photo, config.WIDTH, config.HEIGHT)
    cl = (ImageClip(np.asarray(card), ismask=False)
          .set_duration(duration)
          .set_position(("center", int(config.HEIGHT * 0.16))))
    try:                                   # halka pop-in
        cl = cl.crossfadein(0.25)
    except Exception:
        pass
    return CompositeVideoClip([bg, cl], size=(config.WIDTH, config.HEIGHT)) \
        .set_duration(duration)


def _llm_prompts(segs):
    """Script ki HAR LINE ko Gemini se hi ek Veo prompt me badlwao.

    User: "jo script hum bana rahe usko hi use karke video generate karo".
    Sahi baat — bucket wale prompts sirf MOOD pakadte the (studio/microphone),
    line ka asli action nahi. Ab line ka scene likhwate he.

    Naam phir bhi nahi jaate: Veo asli chehra banata nahi (test kiya — 'Messi'
    maanga to ajnabi aadmi aaya) aur likeness ka panga alag. Isliye LLM ko
    bola he ki insaan SILHOUETTE/back-view/haath-pair me dikhaye.
    """
    try:
        from script import _call_gemini
    except Exception:
        return None
    lines = "\n".join(f"{i}. {s.get('subtitle_english') or s.get('voice_english','')}"
                      for i, s in enumerate(segs, 1))
    system = "You output ONLY a numbered list. No preamble, no explanation."
    user = (
        "Turn each line of this football script into ONE cinematic video prompt "
        "for an AI video generator (Veo).\n\n"
        "RULES for every prompt:\n"
        "- Describe the SCENE that matches THAT line's action or emotion.\n"
        "- NEVER name any real person, club, or competition. No jerseys with "
        "crests, no logos, no readable text.\n"
        "- People may appear only as silhouettes, backs, hands, or feet — never "
        "an identifiable face.\n"
        "- End every prompt with: 'Cinematic vertical 9:16, slow motion, shallow "
        "depth of field, moody film grade, 6 seconds.'\n"
        "- One line per prompt, 25-40 words. Make each of them VISUALLY DIFFERENT "
        "from the others.\n\n"
        f"SCRIPT:\n{lines}\n\nOutput exactly {len(segs)} numbered prompts.")
    try:
        out = _call_gemini(system, user) or ""
    except Exception as e:
        print(f"[gemini] prompt-LLM fail ({e}) -> bucket prompts")
        return None
    got = []
    for ln in out.splitlines():
        ln = ln.strip()
        if ln and ln[0].isdigit():
            got.append(ln.split(".", 1)[-1].strip().lstrip(")-— ").strip())
    return got if len(got) >= len(segs) else None


def _name_matches(name: str, filename) -> bool:
    """Photo ke file-naam me insaan ke naam ka koi hissa he ya nahi.

    Wikimedia commons pe naam-wise files hoti he (Eniola_Aluko_and_Katie_Hoyle.jpg,
    ..._with_Ian_Wright_....jpg). Jab kisi ki photo hoti hi nahi, search bilkul
    alag cheez de deta he — usi ko yahan pakadte he.
    """
    fn = str(filename or "").lower()
    if not fn:
        return False
    parts = [p for p in name.lower().replace("'", "").split() if len(p) > 3]
    return any(p in fn for p in parts)


def _segment_photos(segs):
    """Har segment ke liye us line ke insaan ki ASLI photo (Wikimedia, legal).

    media.py ka _person_in use karta he — wo descriptive query me se naam
    nikaalta he ("Eni Aluko accused Ian Wright" -> "Eni Aluko"), warna Wikidata
    lookup fail ho jaata he.
    """
    from media import _person_in
    from realphoto import real_photo
    out, used = [], set()
    last = None
    for s in segs:
        name = _person_in(s.get("image_query") or "") or _person_in(
            s.get("subtitle_english") or "")
        img = None
        if name:
            try:
                img, _c, fn = real_photo(name, sentence=s.get("subtitle_english"),
                                         exclude=used)
                # NAAM-CHECK: file ke naam me insaan ka naam hona chahiye. Wikimedia
                # pe jiski photo nahi hoti (jaise TV presenter Laura Woods) uske liye
                # search KACHRA utha laata he — ek baar 1974 ki 'U_and_I.jpg' aa gayi
                # thi. Aisi photo dikhane se achha he pichli wali dikha do.
                if img is not None and not _name_matches(name, fn):
                    print(f"[gemini] '{name}' ki photo galat lagi ({fn}) -> chhodi")
                    img = None
                if img is not None:
                    used.add(str(fn))
                    last = img
            except Exception as e:
                print(f"[gemini] photo fail ({name}): {e}")
        out.append(img or last)        # na mile to pichli photo (khali frame se behtar)
        print(f"[gemini] seg{len(out)}: {name or '(koi naam nahi)'}"
              f"{' -> photo' if out[-1] is not None else ' -> sirf clip'}")
    return out


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
    # line ke MOOD se bucket chuno, phir bucket ke ANDAR index se ghumao.
    # (Pehle har bucket me ek hi scene tha -> pundit script ki saari 5 lines
    #  ek hi bucket me girti thi aur 5 IDENTICAL clips ban jaate the.)
    for words, variants in _BUCKETS:
        if any(w in line for w in words):
            return _wrap(variants[(idx - 1) % len(variants)])
    return _wrap(_FALLBACKS[(idx - 1) % len(_FALLBACKS)])


def _wrap(scene):
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
    llm = _llm_prompts(segs)
    if llm:
        print("(prompts script ki lines se bane he - Gemini ne likhe)")
    for i, s in enumerate(segs, 1):
        print(f"--- {i}.mp4 -------------------------------------------------")
        print(llm[i - 1] if llm else _veo_prompt(s, i))
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
    photos = _segment_photos(segs)
    auds = voice.generate_segment_voices(segs)

    # har segment ka background = Gemini clip (chalta hua) + asli photo card upar
    _orig = V._bg_clip

    def _hybrid(media, duration, idx):
        # idx segments se aage bhi aa sakta he (CTA card bhi background maangta he)
        ph = photos[idx] if idx < len(photos) else None
        return _clip_with_photo(clips[idx % len(clips)], ph, duration, idx)

    V._bg_clip = _hybrid
    V._two_shot_bg = _hybrid          # FAST_CUTS bhi isi rasta se jaaye
    try:
        media = [{"type": "video", "path": clips[i % len(clips)]} for i in range(len(segs))]
        out = V.build_short(segs, media, auds, data)
    finally:
        V._bg_clip = _orig
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
