"""
video.py — Static images ko "animated" 9:16 short me convert karta hai.

Technique (no GPU!):
  - Ken Burns effect : har image par slow zoom/pan → motion ka feel
  - Crossfade        : segments ke beech smooth transition
  - English subtitles: PIL se render (ImageMagick ki zaroorat NAHI)
  - Hindi voiceover  : per-segment audio, perfectly synced
  - Optional BGM     : background music low volume par

Output: output/short.mp4 (1080x1920, 30fps)
"""

import os
import re

# ── FIX: Pillow 10+ ne ANTIALIAS hata diya, moviepy 1.0.3 use karta hai ──────────
from PIL import Image, ImageDraw, ImageFont
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

import numpy as np
from moviepy.editor import (
    ImageClip, VideoClip, VideoFileClip, ColorClip, AudioFileClip,
    CompositeVideoClip, CompositeAudioClip, concatenate_videoclips,
)
try:
    from moviepy.audio.fx.all import audio_loop
except Exception:
    audio_loop = None
try:
    from moviepy.video.fx.all import loop as _vloop, crop as _vcrop
except Exception:
    _vloop = _vcrop = None

import config

W, H = config.WIDTH, config.HEIGHT


# ── Font helper (Windows) ────────────────────────────────────────────────────────
def _font(size: int):
    for name in ("arialbd.ttf", "Arial Bold.ttf", "arial.ttf", "segoeuib.ttf",
                 # Linux (GitHub Actions) — English captions ke liye
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                 "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _line_w(draw, text, font) -> int:
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]


def _wrap_px(draw, text, font, max_width) -> list[str]:
    """Pixel-based word wrap — har line max_width ke andar."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if _line_w(draw, trial, font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fit_text(draw, text, max_width, start_size, min_size=30):
    """
    Font size dhoondo jisme saari wrapped lines max_width ke andar fit ho jaayein.
    Returns (lines, font, size).
    """
    size = start_size
    while size >= min_size:
        font = _font(size)
        lines = _wrap_px(draw, text, font, max_width)
        if all(_line_w(draw, ln, font) <= max_width for ln in lines):
            return lines, font, size
        size -= 4
    font = _font(min_size)
    return _wrap_px(draw, text, font, max_width), font, min_size


def _draw_centered(draw, lines, font, size, y_start, fill, stroke=(0, 0, 0, 235),
                   sw=3):
    line_h = size + 18
    y = y_start
    for line in lines:
        x = (W - _line_w(draw, line, font)) // 2
        for dx in range(-sw, sw + 1, sw):
            for dy in range(-sw, sw + 1, sw):
                draw.text((x + dx, y + dy), line, font=font, fill=stroke)
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h
    return y


# ── Subtitle overlay (transparent PNG) ───────────────────────────────────────────
def _make_subtitle_png(text: str, idx: int) -> str:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    max_w = W - 2 * config.SUBTITLE_SIDE_MARGIN
    lines, font, size = _fit_text(draw, text.upper(), max_w,
                                  config.SUBTITLE_FONT_SIZE)

    line_h = size + 18
    y = int(H * 0.78) - (line_h * len(lines)) // 2   # lower-third, vertically centered
    _draw_centered(draw, lines, font, size, y, fill=(255, 255, 255, 255))

    out_dir = os.path.join(config.OUTPUT_DIR, "subs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"sub_{idx:02d}.png")
    img.save(path)
    return path


def _strip_emoji(text: str) -> str:
    """Arial emoji render nahi karta -> tofu box. Emoji/symbols hata do."""
    return "".join(c for c in text if ord(c) < 0x2190).strip()


def _make_banner_png(text: str, name: str, top: bool = True) -> str:
    """Hook title / CTA banner ke liye bada yellow text."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    max_w = W - 2 * config.SUBTITLE_SIDE_MARGIN
    lines, font, size = _fit_text(draw, _strip_emoji(text).upper(), max_w, 92, min_size=48)

    line_h = size + 22
    y = int(H * 0.10) if top else int(H * 0.40)
    _draw_centered(draw, lines, font, size, y, fill=(255, 222, 60, 255), sw=4)

    out_dir = os.path.join(config.OUTPUT_DIR, "subs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"banner_{name}.png")
    img.save(path)
    return path


def _make_credits_card(credits: list) -> str:
    """Real photos ke liye attribution card (CC-BY safe banata hai)."""
    img = Image.new("RGB", (W, H), (12, 14, 20))
    d = ImageDraw.Draw(img)
    hf, f = _font(58), _font(34)
    d.text((70, int(H * 0.28)), "PHOTO CREDITS", font=hf, fill=(255, 222, 60))
    y = int(H * 0.28) + 100
    for c in credits[:8]:
        for ln in _wrap_px(d, "• " + c, f, W - 140):
            d.text((70, y), ln, font=f, fill=(232, 232, 232))
            y += 44
        y += 12
    d.text((70, int(H * 0.86)), "Images: Wikimedia Commons (CC / Public Domain)",
           font=f, fill=(150, 150, 150))
    out_dir = os.path.join(config.OUTPUT_DIR, "subs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "credits.jpg")
    img.save(path)
    return path


def _make_brand_overlay() -> str | None:
    """Persistent watermark: handle text + optional logo. Poore video par dikhta hai."""
    if not config.SHOW_WATERMARK:
        return None
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Handle text — top-left, halka transparent
    handle = config.BRAND_HANDLE or config.BRAND_NAME
    if handle:
        font = _font(40)
        x, y = 36, 40
        for dx in (-2, 0, 2):
            for dy in (-2, 0, 2):
                draw.text((x + dx, y + dy), handle, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y), handle, font=font, fill=(255, 255, 255, 220))

    # Logo — top-right (agar file ho)
    if config.LOGO_PATH and os.path.exists(config.LOGO_PATH):
        try:
            logo = Image.open(config.LOGO_PATH).convert("RGBA")
            lw = 140
            logo = logo.resize((lw, int(logo.height * lw / logo.width)),
                               Image.LANCZOS)
            img.alpha_composite(logo, (W - lw - 36, 32))
        except Exception as e:
            print(f"[video] logo skip ({e})")

    out_dir = os.path.join(config.OUTPUT_DIR, "subs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "brand.png")
    img.save(path)
    return path


# ── Ken Burns clip (varied motion) ──────────────────────────────────────────────
_MOTIONS = ["in", "left", "out", "right", "up", "in", "down"]


def _ken_burns(img_path: str, duration: float, motion: str = "in"):
    """
    FAST Ken Burns — image ko ek baar bada karke har frame me sirf numpy CROP
    (slicing) karta hai. Per-frame resize NAHI (moviepy ka bottleneck) -> 10x fast.
    Motion = moving pan window (in/out diagonal, left/right/up/down).
    """
    z = config.KEN_BURNS_ZOOM
    bw, bh = int(W * z), int(H * z)
    big = Image.open(img_path).convert("RGB").resize((bw, bh), Image.LANCZOS)
    arr = np.asarray(big)
    ex, ey = bw - W, bh - H

    def offs(t):
        f = max(0.0, min(1.0, t / duration))
        if motion == "left":   return ex * f,        ey // 2
        if motion == "right":  return ex * (1 - f),  ey // 2
        if motion == "up":     return ex // 2,       ey * f
        if motion == "down":   return ex // 2,       ey * (1 - f)
        if motion == "out":    return ex * (1 - f),  ey * (1 - f)
        return ex * f, ey * f   # "in" -> diagonal push

    def make_frame(t):
        x, y = offs(t)
        x = int(max(0, min(ex, x)))
        y = int(max(0, min(ey, y)))
        return arr[y:y + H, x:x + W]

    return VideoClip(make_frame, duration=duration)


def _video_bg(path: str, duration: float):
    """Pexels video clip ko 9:16 cover + loop/trim karke segment bg banata hai."""
    clip = VideoFileClip(path).without_audio()
    if clip.duration < duration and _vloop is not None:
        clip = clip.fx(_vloop, duration=duration)
    else:
        clip = clip.subclip(0, min(duration, clip.duration))
    clip = clip.set_duration(duration)
    scale = max(W / clip.w, H / clip.h)
    clip = clip.resize(scale)
    if _vcrop is not None:
        clip = clip.fx(_vcrop, x_center=clip.w / 2, y_center=clip.h / 2,
                       width=W, height=H)
    return CompositeVideoClip([clip], size=(W, H)).set_duration(duration)


def _bg_clip(media: dict, duration: float, idx: int):
    """Media descriptor se segment background banao (video ya Ken Burns image)."""
    if media.get("type") == "video":
        try:
            return _video_bg(media["path"], duration)
        except Exception as e:
            print(f"[video]   video clip failed ({e}) -> color bg")
            return ColorClip((W, H), color=(15, 30, 60)).set_duration(duration)
    motion = _MOTIONS[idx % len(_MOTIONS)]
    return _ken_burns(media["path"], duration, motion)


# ── Combined overlay: vignette + grain + watermark + logo (ek hi static layer) ───
def _make_overlay():
    """Sab static overlays ek PNG me (1 composite layer = fast render)."""
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    if config.VIGNETTE:
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        v = np.clip((d - 0.7) / 0.7, 0, 1)
        arr[..., 3] = (v * 140).astype(np.uint8)
    if config.FILM_GRAIN:
        mask = np.random.rand(H, W) < 0.05
        arr[mask, 0] = arr[mask, 1] = arr[mask, 2] = 180
        arr[mask, 3] = np.maximum(arr[mask, 3], 30)

    img = Image.fromarray(arr, "RGBA")
    draw = ImageDraw.Draw(img)

    if config.SHOW_WATERMARK:
        handle = config.BRAND_HANDLE or config.BRAND_NAME
        if handle:
            font = _font(40)
            x, y = 36, 40
            for dx in (-2, 0, 2):
                for dy in (-2, 0, 2):
                    draw.text((x + dx, y + dy), handle, font=font, fill=(0, 0, 0, 180))
            draw.text((x, y), handle, font=font, fill=(255, 255, 255, 220))
        if config.LOGO_PATH and os.path.exists(config.LOGO_PATH):
            try:
                logo = Image.open(config.LOGO_PATH).convert("RGBA")
                lw = 140
                logo = logo.resize((lw, int(logo.height * lw / logo.width)),
                                   Image.LANCZOS)
                img.alpha_composite(logo, (W - lw - 36, 32))
            except Exception as e:
                print(f"[video] logo skip ({e})")

    out_dir = os.path.join(config.OUTPUT_DIR, "subs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "overlay.png")
    img.save(path)
    return path


# ── Animated word-by-word captions ───────────────────────────────────────────────
def _caption_clips(text: str, duration: float, idx: int):
    """Word-by-word reveal captions (viral style). Returns list of timed ImageClips."""
    words = text.upper().split()
    if not words:
        return []

    tmp = Image.new("RGBA", (W, H))
    draw = ImageDraw.Draw(tmp)
    max_w = W - 2 * config.SUBTITLE_SIDE_MARGIN

    # full sentence ke liye font + wrapping (layout stable rahe)
    lines, font, size = _fit_text(draw, " ".join(words), max_w,
                                  config.SUBTITLE_FONT_SIZE)
    # words ko lines me wrap karo (same font)
    wrapped, cur = [], []
    for w in words:
        trial = " ".join(cur + [w])
        if _line_w(draw, trial, font) <= max_w or not cur:
            cur.append(w)
        else:
            wrapped.append(cur); cur = [w]
    if cur:
        wrapped.append(cur)

    line_h = size + 18
    y0 = int(H * 0.78) - (line_h * len(wrapped)) // 2

    # har word ki absolute (x,y) position
    positions, gi = [], 0
    for li, line in enumerate(wrapped):
        lw = _line_w(draw, " ".join(line), font)
        x = (W - lw) // 2
        y = y0 + li * line_h
        for w in line:
            positions.append((w, x, y))
            x += _line_w(draw, w + " ", font)
            gi += 1

    n = len(positions)
    per = duration / n
    out_dir = os.path.join(config.OUTPUT_DIR, "subs")
    os.makedirs(out_dir, exist_ok=True)

    clips = []
    for k in range(n):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for j in range(k + 1):
            w, x, y = positions[j]
            if j == k:
                # ACTIVE word -> yellow highlight box + dark text (viral pop)
                bb = d.textbbox((x, y), w, font=font)
                pad = 10
                d.rounded_rectangle([bb[0] - pad, bb[1] - pad // 2,
                                     bb[2] + pad, bb[3] + pad // 2],
                                    radius=12, fill=(255, 200, 30, 255))
                d.text((x, y), w, font=font, fill=(15, 15, 15, 255))
            else:
                for dx in (-3, 0, 3):
                    for dy in (-3, 0, 3):
                        d.text((x + dx, y + dy), w, font=font, fill=(0, 0, 0, 235))
                d.text((x, y), w, font=font, fill=(255, 255, 255, 255))
        p = os.path.join(out_dir, f"cap_{idx:02d}_{k:02d}.png")
        img.save(p)
        start = k * per
        # NON-OVERLAPPING slices -> har time sirf 1 caption layer (fast render)
        dur_k = per if k < n - 1 else (duration - start)
        clips.append(ImageClip(p).set_start(start).set_duration(dur_k)
                     .set_position(("center", "center")))
    return clips


# ── Whoosh SFX (numpy se generate) ───────────────────────────────────────────────
def _make_whoosh():
    try:
        import wave
        sr, dur = 44100, 0.35
        t = np.linspace(0, dur, int(sr * dur), False)
        env = np.exp(-t * 7)
        noise = np.random.randn(len(t)) * 0.4
        sweep = np.sin(2 * np.pi * (180 + (t / dur) * 1300) * t) * 0.3
        sig = (noise + sweep) * env
        sig = sig / (np.max(np.abs(sig)) + 1e-9) * 0.5
        path = os.path.join(config.OUTPUT_DIR, "whoosh.wav")
        w = wave.open(path, "w")
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((sig * 32767).astype(np.int16).tobytes())
        w.close()
        return path
    except Exception as e:
        print(f"[video] whoosh skip ({e})")
        return None


# ── Stat card (bade bold numbers — "6 World Cups") ───────────────────────────────
_STAT_WORDS = {"cup", "cups", "goal", "goals", "match", "matches", "trophy",
               "trophies", "title", "titles", "year", "years", "cap", "caps",
               "assist", "assists", "win", "wins", "record", "records", "medal",
               "medals", "final", "finals", "appearance", "appearances", "hat-trick"}


def _stat_from_subtitle(text: str):
    """'6 World Cups...' -> ('6','WORLD CUPS'). Label = number ke baad stat-word tak."""
    if not text:
        return None
    m = re.search(r"(\d[\d,]{0,9})\s+([A-Za-z][A-Za-z\- ]{2,30})", text)
    if not m:
        return None
    num, words = m.group(1), m.group(2).split()
    for j, w in enumerate(words):
        if w.lower().strip(".,") in _STAT_WORDS:
            return num, " ".join(words[:j + 1]).upper()   # e.g. "WORLD CUPS"
    return None


def _make_stat_png(number: str, label: str, idx: int) -> str:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # dark scrim (center band) taaki number kisi bhi bg pe readable rahe
    d.rounded_rectangle([90, int(H * 0.24), W - 90, int(H * 0.56)],
                        radius=40, fill=(0, 0, 0, 150))
    # accent top line
    d.rounded_rectangle([W // 2 - 90, int(H * 0.255), W // 2 + 90, int(H * 0.255) + 10],
                        radius=5, fill=(255, 210, 40, 255))
    # HUGE number
    nf = _font(300)
    nb = d.textbbox((0, 0), number, font=nf)
    nx = (W - (nb[2] - nb[0])) // 2
    ny = int(H * 0.28)
    for dx in (-6, 0, 6):
        for dy in (-6, 0, 6):
            d.text((nx + dx, ny + dy), number, font=nf, fill=(0, 0, 0, 240))
    d.text((nx, ny), number, font=nf, fill=(255, 210, 40, 255))
    # label neeche
    lf = _font(80)
    lines, font, size = _fit_text(d, label, W - 160, 80, min_size=52)
    y = ny + (nb[3] - nb[1]) + 40
    _draw_centered(d, lines, font, size, y, fill=(255, 255, 255, 255), sw=4)
    out_dir = os.path.join(config.OUTPUT_DIR, "subs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"stat_{idx:02d}.png")
    img.save(path)
    return path


# ── Silence trim (voice ko tight/continuous banane ke liye) ──────────────────────
def _trim_silence_file(path: str) -> str:
    """edge-tts ki leading/trailing silence ffmpeg se hatao. Returns trimmed path."""
    try:
        import subprocess
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()
        out = os.path.splitext(path)[0] + "_t.mp3"
        # -45dB threshold = SAFE (soft speech na kate). start_silence 0.05 =
        # sirf 0.05s silence rakho -> gaps chhote (~0.17s) par speech intact.
        one = ("silenceremove=start_periods=1:start_silence=0.05:"
               "start_threshold=-45dB:detection=peak")
        filt = f"{one},areverse,{one},areverse"
        r = subprocess.run([ff, "-y", "-i", path, "-af", filt, out],
                           capture_output=True)
        if r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 1000:
            return out
    except Exception as e:
        print(f"[video]   trim skip ({e})")
    return path


# ── Main ──────────────────────────────────────────────────────────────────────────
def build_short(segments: list[dict], media: list, audio_paths: list[str],
                script_data: dict) -> str:
    # media: list of {"type","path"} (ya purane format me string image paths)
    media = [{"type": "image", "path": m} if isinstance(m, str) else m
             for m in media]
    assert len(segments) == len(media) == len(audio_paths), \
        "segments, media, audio counts must match"

    print("[video] Building segments...")
    seg_clips, seg_durs = [], []

    for i, seg in enumerate(segments):
        # silence trim -> voice tight (edge-tts ki random silence hatao). PHIR apne
        # CONTROLLED pauses add karo: har segment ke baad breathing pause; quiz reveal
        # (suspense_before) se PEHLE bada dramatic pause = suspense.
        voice = AudioFileClip(_trim_silence_file(audio_paths[i]))
        lead = 0.9 if seg.get("suspense_before") else 0.0   # reveal se pehle suspense
        breath = 0.35                                        # har segment ke baad saans
        dur = lead + voice.duration + config.CROSSFADE + breath
        if lead:
            from moviepy.editor import CompositeAudioClip
            audio = CompositeAudioClip([voice.set_start(lead)]).set_duration(dur)
        else:
            audio = voice

        bg = _bg_clip(media[i], dur, i)
        layers = [bg]

        sub = seg.get("subtitle_english", "")
        stat = _stat_from_subtitle(sub) if getattr(config, "STATS_OVERLAY", False) else None

        if stat:
            # BIG stat card (number + label) + chhota static subtitle neeche
            print(f"[video]   stat card: {stat[0]} {stat[1]}")
            layers.append(ImageClip(_make_stat_png(stat[0], stat[1], i))
                          .set_duration(dur).set_position(("center", "center")))
            layers.append(ImageClip(_make_subtitle_png(sub, i)).set_duration(dur)
                          .set_position(("center", "center")))
        elif config.ANIMATED_CAPTIONS:
            try:
                layers += _caption_clips(sub, dur, i)
            except Exception as e:
                print(f"[video]   caption anim failed ({e}) -> static")
                layers.append(ImageClip(_make_subtitle_png(sub, i)).set_duration(dur)
                              .set_position(("center", "center")))
        else:
            layers.append(ImageClip(_make_subtitle_png(sub, i)).set_duration(dur)
                          .set_position(("center", "center")))

        if i == 0 and script_data.get("hook_english"):
            hook_png = _make_banner_png(script_data["hook_english"], "hook", top=True)
            layers.append(ImageClip(hook_png).set_duration(dur)
                          .set_position(("center", "center")))

        clip = CompositeVideoClip(layers, size=(W, H)).set_duration(dur).set_audio(audio)
        if i > 0 and config.CROSSFADE > 0:
            clip = clip.crossfadein(config.CROSSFADE)
        seg_clips.append(clip)
        seg_durs.append(dur)
        print(f"[video]   segment {i+1}/{len(segments)} ({dur:.1f}s) "
              f"[{media[i]['type']}]")

    # CTA end card
    cta_text = script_data.get("cta_english", "Follow for more!")
    cta_png = _make_banner_png(cta_text, "cta", top=False)
    cta_bg = _bg_clip(media[-1], 1.8, len(segments))
    cta_clip = CompositeVideoClip(
        [cta_bg, ImageClip(cta_png).set_duration(1.8).set_position(("center", "center"))],
        size=(W, H)).set_duration(1.8).crossfadein(config.CROSSFADE)
    seg_clips.append(cta_clip)
    seg_durs.append(1.8)

    # ── Attribution (real photos — CC-BY). Card OFF; credits.txt hamesha likhega ──
    credits = list(dict.fromkeys(m.get("credit") for m in media if m.get("credit")))
    if credits:
        try:
            with open(os.path.join(config.OUTPUT_DIR, "credits.txt"), "w",
                      encoding="utf-8") as f:
                f.write("Photo credits (Wikimedia Commons, CC/PD):\n"
                        + "\n".join("- " + c for c in credits))
        except Exception:
            pass
        if getattr(config, "SHOW_CREDITS_CARD", False):   # video me card (default OFF)
            cc_png = _make_credits_card(credits)
            seg_clips.append(ImageClip(cc_png).set_duration(2.8))
            seg_durs.append(2.8)
            print(f"[video] Attribution card added ({len(credits)} credits).")
        else:
            print(f"[video] {len(credits)} credits -> credits.txt (description ke liye)")

    print("[video] Concatenating...")
    pad = -config.CROSSFADE if config.CROSSFADE > 0 else 0
    final = concatenate_videoclips(seg_clips, method="compose", padding=pad)

    # ── Overlay (vignette + grain + watermark + logo) — ek hi layer ──────────────
    ov_png = _make_overlay()
    if ov_png:
        final = CompositeVideoClip(
            [final, ImageClip(ov_png).set_duration(final.duration)], size=(W, H))
        print("[video] Cinematic overlay + watermark added.")

    # ── Hook punch: opening white flash (scroll-stopping snap) ────────────────────
    if getattr(config, "HOOK_PUNCH", False):
        try:
            flash = (ColorClip((W, H), color=(255, 255, 255))
                     .set_duration(0.18).set_opacity(0.65).crossfadeout(0.18))
            final = CompositeVideoClip([final, flash.set_start(0)], size=(W, H))
            print("[video] Hook flash added.")
        except Exception as e:
            print(f"[video] flash skip ({e})")

    # ── Audio: voice + whoosh SFX + BGM ──────────────────────────────────────────
    audio_tracks = [final.audio]

    if config.SFX_WHOOSH:
        whoosh = _make_whoosh()
        if whoosh:
            try:
                starts, acc = [], 0.0
                for d in seg_durs[:-1]:
                    acc += d - (config.CROSSFADE if config.CROSSFADE > 0 else 0)
                    starts.append(acc)
                for stt in starts:
                    audio_tracks.append(
                        AudioFileClip(whoosh).volumex(0.2).set_start(max(0, stt - 0.12)))
                print(f"[video] {len(starts)} whoosh SFX added.")
            except Exception as e:
                print(f"[video] SFX skip ({e})")

    if config.BGM_PATH and os.path.exists(config.BGM_PATH):
        try:
            print("[video] Mixing background music...")
            print("[video] ⚠️ SAFETY: BGM sirf ROYALTY-FREE honi chahiye "
                  "(Pixabay/YT Audio Library). Copyrighted music = strike/claim!")
            bgm = AudioFileClip(config.BGM_PATH).volumex(config.BGM_VOLUME)
            if audio_loop is not None:
                bgm = audio_loop(bgm, duration=final.duration)
            else:
                bgm = bgm.set_duration(final.duration)
            audio_tracks.append(bgm)
        except Exception as e:
            print(f"[video] BGM skip ({e})")
    elif config.BGM_PATH:
        print(f"[video] No BGM at '{config.BGM_PATH}' — voiceover only.")

    if len(audio_tracks) > 1:
        final = final.set_audio(CompositeAudioClip(audio_tracks))

    # ── Export ───────────────────────────────────────────────────────────────────
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    out = config.FINAL_VIDEO
    print(f"[video] Rendering -> {out} (this may take a minute)...")
    # Temp audio ko OUTPUT_DIR ke andar unique naam do — warna do parallel builds
    # (batch/auto) same 'shortTEMP_MPY_wvf_snd.mp4' pe clash karte hain (WinError 32).
    temp_audio = os.path.join(config.OUTPUT_DIR, "_render_audio.m4a")
    final.write_videofile(
        out, fps=config.FPS, codec="libx264", audio_codec="aac",
        threads=os.cpu_count() or 4, preset="veryfast",
        temp_audiofile=temp_audio,
        # crf 28 = chhoti file (~18MB vs 67MB) quality almost same; faststart = mobile
        ffmpeg_params=["-crf", "28", "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    print(f"[video] ✅ Done: {out}  ({final.duration:.1f}s)")
    return out
