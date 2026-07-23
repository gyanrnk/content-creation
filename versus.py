"""
VERSUS MODE — player vs player scorecard, "balloon-grammar" pe bana:
  sawaal shuru me -> har second kuch hilta he -> faisla AANKH se dikhta he.

(Blueprint: 17.9M ka #1 short isi format ka tha; 5.7M wala props-video isi
grammar pe tha. Dono ka analysis memory me — versus-mode-plan.)

User ki shart: VARIETY — payoff har video me alag ho. Isliye PAYOFFS registry
he; video banate waqt ek chunte he (rotation). Round data hamesha grounded
facts se aana chahiye (stats/wiki), kabhi invent nahi — ye caller ki zimmedari.

Sab kuch PIL se drawn he — koi footage nahi, koi download ke alawa asset nahi
(sirf players ki legal photos, realphoto se).
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import config
from video import _font

INK = (18, 22, 30)
BG_TOP = (16, 24, 44)
BG_BOT = (40, 14, 60)
GOLD = (255, 205, 60)
RED = (235, 60, 50)
BLUE = (70, 140, 255)
WHITE = (245, 246, 250)


# ── chhote helpers ──────────────────────────────────────────────────────────────
def _ease(t):
    return 3 * t * t - 2 * t * t * t if 0 <= t <= 1 else (0 if t < 0 else 1)


def _bg(W, H, col1=None, col2=None):
    """TEAM-COLORS split background: tirchhi laker, har taraf apne player ke team
    ka rang (dark shade), upar floodlight beams, vignette. User: plain gradient
    boring tha. Sab ek baar precompute hota he — per-frame sirf copy."""
    col1 = np.array(col1 or (28, 60, 110), float)     # default: neela
    col2 = np.array(col2 or (110, 25, 35), float)     # default: laal
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    # tirchhi boundary + halka gradient neeche ki taraf dark
    split = (xx / W) + 0.18 * (yy / H - 0.5)
    dark = (0.55 + 0.45 * (1 - yy / H))[:, :, None]   # upar bright, neeche dark
    img = np.where((split < 0.5)[:, :, None],
                   col1[None, None, :], col2[None, None, :]) * dark
    # beech ki chamakti laker
    edge = np.abs(split - 0.5)
    img += (np.clip(1 - edge * 18, 0, 1) ** 2)[:, :, None] * 70
    # floodlight beams (dono upar ke kono se)
    for cx in (0.08, 0.92):
        dxn = xx / W - cx
        beam = np.clip(1 - np.abs(dxn * 4 - (yy / H) * (0.9 if cx < 0.5 else -0.9) * 0) , 0, 1)
        beam = np.clip(1 - np.abs(dxn) * 5, 0, 1) * np.clip(1 - yy / (H * 0.7), 0, 1)
        img += (beam ** 2)[:, :, None] * 26
    return np.clip(img, 0, 235).astype(np.uint8)


def _streaks(img_np, t, W, H):
    """Dheeme chalti diagonal light streaks — har frame halki harkat (alive feel)."""
    img = Image.fromarray(img_np)
    d = ImageDraw.Draw(img, "RGBA")
    period = W * 0.9
    off = (t * W * 0.06) % period
    for i in range(3):
        x0 = -H * 0.4 + off + i * period / 3
        d.line([x0, H, x0 + H * 0.45, 0], fill=(255, 255, 255, 14), width=int(W * 0.05))
    return np.asarray(img)


def _card(photo: Image.Image, name: str, W: int) -> Image.Image:
    """Player ka photo-card: rounded photo + naam ki patti."""
    cw, ch = int(W * 0.40), int(W * 0.52)
    ph = ch - int(W * 0.085)
    img = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=18, fill=(255, 255, 255, 255))
    p = photo.copy()
    s = max(cw / p.width, ph / p.height)
    p = p.resize((int(p.width * s), int(p.height * s)))
    p = p.crop(((p.width - cw + 8) // 2, 0, (p.width - cw + 8) // 2 + cw - 8, ph))
    img.paste(p, (4, 4))
    f = _font(int(W * 0.042))
    b = d.textbbox((0, 0), name, font=f)
    d.text(((cw - b[2] + b[0]) / 2, ph + int(W * 0.012)), name, font=f, fill=INK)
    return img


def _paste(base_np, img, x, y):
    base = Image.fromarray(base_np)
    base.paste(img, (int(x), int(y)), img if img.mode == "RGBA" else None)
    return np.asarray(base)


def _text(base_np, txt, y, size, fill, W, stroke=3):
    img = Image.fromarray(base_np)
    d = ImageDraw.Draw(img)
    f = _font(size)
    b = d.textbbox((0, 0), txt, font=f)
    x = (W - b[2] + b[0]) / 2
    d.text((x, y), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    return np.asarray(img)


# ── PAYOFFS (variety — har video me alag) ───────────────────────────────────────
def _payoff_balloon(d, img, t, lx, ly, cw, W):
    """Haarne wale ke upar gubbara phoolta he aur PHAT jaata he (5.7M ko salaam)."""
    cx, cy = lx + cw // 2, ly - int(W * 0.06)
    if t < 0.72:                                   # phoolna
        r = int(W * 0.03 + W * 0.11 * _ease(t / 0.72))
        d.ellipse([cx - r, cy - r * 1.15, cx + r, cy + r * 0.85], fill=RED)
        d.line([cx, cy + r * 0.85, cx, cy + r * 0.85 + 14], fill=WHITE, width=3)
    elif t < 0.92:                                 # PHAT — tukde
        k = (t - 0.72) / 0.20
        r0 = int(W * 0.14)
        for i in range(10):                        # deterministic shards
            a = i * 0.628 + 0.3
            rr = r0 * (0.4 + 1.6 * k)
            x2, y2 = cx + rr * math.cos(a), cy + rr * math.sin(a)
            d.line([cx + r0 * 0.3 * math.cos(a), cy + r0 * 0.3 * math.sin(a), x2, y2],
                   fill=RED, width=max(2, int(6 * (1 - k))))
    return img


def _payoff_cardfall(card_img, t):
    """Haarne wale ka card jhuk ke gir jaata he. Rotation+drop return karta he."""
    ang = -28 * _ease(min(1, t / 0.6))
    drop = int(_ease(max(0, (t - 0.35) / 0.65)) ** 2 * card_img.height * 2.2)
    return card_img.rotate(ang, expand=True, resample=Image.BILINEAR), drop


PAYOFFS = ("balloon", "cardfall")   # aur aayenge: tugofwar, penalty, ladder, healthbar


# ── mukhya renderer ─────────────────────────────────────────────────────────────
def versus_frames(p1, p2, img1, img2, rounds, phases, payoff="balloon",
                  col1=None, col2=None):
    """frame(t) function banata he.

    p1/p2   : naam;  img1/img2: PIL photos (legal, realphoto se)
    rounds  : [{"label":"BALLON D'OR","v1":8,"v2":5,"win":1}, ...]  win: 1|2
    phases  : har phase ki (start,end) — [intro, r1..rN, payoff] (voice se aayi)
    col1/2  : players ke TEAM colors (background split ke liye)
    """
    W, H = config.WIDTH, config.HEIGHT
    base = _bg(W, H, col1, col2)
    c1 = _card(img1, p1, W)
    c2 = _card(img2, p2, W)
    cw, chh = c1.width, c1.height
    y_cards = int(H * 0.20)
    x1f, x2f = int(W * 0.055), W - int(W * 0.055) - cw
    total_end = phases[-1][1]
    wins_after = []                                 # score progression
    s1 = s2 = 0
    for r in rounds:
        s1, s2 = s1 + (r["win"] == 1), s2 + (r["win"] == 2)
        wins_after.append((s1, s2))
    winner_is_1 = s1 >= s2

    def frame(t):
        t = min(t, total_end - 0.01)
        img = _streaks(base.copy(), t, W, H)
        # kaunsa phase?
        pi = 0
        for i, (a, b) in enumerate(phases):
            if a <= t < b:
                pi = i
                break
        else:
            pi = len(phases) - 1
        pt = (t - phases[pi][0]) / max(0.1, phases[pi][1] - phases[pi][0])

        # score ab tak
        done = max(0, pi - 1) if pi < len(phases) - 1 else len(rounds)
        # round ke andar point milne ke BAAD hi score badhe (70% par)
        if 1 <= pi <= len(rounds) and pt > 0.7:
            done = pi
        sc1, sc2 = wins_after[done - 1] if done > 0 else (0, 0)

        # SHAKE jab point lage
        dx = dy = 0
        if 1 <= pi <= len(rounds) and 0.7 < pt < 0.85:
            k = (pt - 0.7) / 0.15
            dx = int(math.sin(t * 90) * 9 * (1 - k))
            dy = int(math.cos(t * 70) * 6 * (1 - k))

        # cards (intro me slide-in)
        if pi == 0:
            e = _ease(pt)
            x1 = int(-cw + (x1f + cw) * e)
            x2 = int(W + (x2f - W) * e)
        else:
            x1, x2 = x1f, x2f

        pay_t = pt if pi == len(phases) - 1 else -1
        cc2, drop2 = (c2, 0)
        cc1, drop1 = (c1, 0)
        if pay_t >= 0 and payoff == "cardfall":
            if winner_is_1:
                cc2, drop2 = _payoff_cardfall(c2, pay_t)
            else:
                cc1, drop1 = _payoff_cardfall(c1, pay_t)
        img = _paste(img, cc1, x1 + dx, y_cards + dy + drop1)
        img = _paste(img, cc2, x2 + dx, y_cards + dy + drop2)

        # winner glow (payoff me)
        if pay_t >= 0:
            wim = Image.fromarray(img)
            dd = ImageDraw.Draw(wim)
            wx = x1f if winner_is_1 else x2f
            glow = int(4 + 3 * math.sin(t * 6))
            dd.rounded_rectangle([wx - glow, y_cards - glow,
                                  wx + cw + glow, y_cards + chh + glow],
                                 radius=20, outline=GOLD, width=5)
            img = np.asarray(wim)

        # VS badge
        wim = Image.fromarray(img)
        dd = ImageDraw.Draw(wim)
        bx, by, br = W // 2, y_cards + chh // 2, int(W * 0.065)
        pop = 1 + 0.1 * math.sin(t * 4)
        r = int(br * pop)
        dd.ellipse([bx - r, by - r, bx + r, by + r], fill=RED, outline=WHITE, width=4)
        f = _font(int(r * 0.9))
        b = dd.textbbox((0, 0), "VS", font=f)
        dd.text((bx - (b[2] - b[0]) / 2, by - (b[3] - b[1]) / 2 - 6), "VS",
                font=f, fill=WHITE)
        img = np.asarray(wim)

        # SCORE bade number
        img = _text(img, f"{sc1}   -   {sc2}", int(H * 0.055), int(W * 0.10),
                    GOLD, W, stroke=4)

        if pi == 0:
            img = _text(img, "KAUN JEETEGA?", int(H * 0.80), int(W * 0.075),
                        WHITE, W)
        elif 1 <= pi <= len(rounds):
            r = rounds[pi - 1]
            img = _text(img, f"ROUND {pi} — {r['label']}", int(H * 0.60),
                        int(W * 0.052), WHITE, W)
            # values count-up
            k = _ease(min(1, pt / 0.6))
            v1 = f"{r['v1'] * k:.0f}" if isinstance(r['v1'], (int, float)) else r['v1']
            v2 = f"{r['v2'] * k:.0f}" if isinstance(r['v2'], (int, float)) else r['v2']
            wim = Image.fromarray(img)
            dd = ImageDraw.Draw(wim)
            f = _font(int(W * 0.105))
            for val, xc, win in ((v1, x1f + cw // 2, r['win'] == 1),
                                 (v2, x2f + cw // 2, r['win'] == 2)):
                b = dd.textbbox((0, 0), str(val), font=f)
                col = GOLD if (win and pt > 0.7) else WHITE
                dd.text((xc - (b[2] - b[0]) / 2, int(H * 0.66)), str(val), font=f,
                        fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
            img = np.asarray(wim)
        else:                                       # payoff
            if payoff == "balloon":
                wim = Image.fromarray(img)
                dd = ImageDraw.Draw(wim)
                lx = x2f if winner_is_1 else x1f
                _payoff_balloon(dd, wim, pay_t, lx, y_cards, cw, W)
                img = np.asarray(wim)
            # winner ke card se GOLD sparks (deterministic — resume-safe)
            wim = Image.fromarray(img)
            dd = ImageDraw.Draw(wim, "RGBA")
            wx = (x1f if winner_is_1 else x2f) + cw // 2
            wy = y_cards + chh // 2
            for i in range(22):
                a = i * 0.286 + (i % 3) * 0.4
                sp = 0.55 + (i % 5) * 0.14
                rr = pay_t * sp * W * 0.55
                px, py = wx + rr * math.cos(a), wy + rr * math.sin(a) * 1.4
                fade = max(0, 1 - pay_t * sp * 1.3)
                if fade > 0:
                    sz = max(2, int(W * 0.008 * fade))
                    dd.ellipse([px - sz, py - sz, px + sz, py + sz],
                               fill=(255, 210, 70, int(230 * fade)))
            img = np.asarray(wim)
            wname = p1 if winner_is_1 else p2
            img = _text(img, "WINNER", int(H * 0.60), int(W * 0.06), GOLD, W)
            img = _text(img, wname.upper(), int(H * 0.655), int(W * 0.085), WHITE, W)
            img = _text(img, "Aapka winner? COMMENT karo!", int(H * 0.78),
                        int(W * 0.042), WHITE, W)
        return img

    return frame


def build_versus_clip(p1, p2, img1, img2, rounds, voice_files, payoff="balloon",
                      col1=None, col2=None):
    """Voice segments ke duration se phases banao aur poora clip return karo.

    PACING (user: "round ke baad pause nahi leta, agla stat bol padta he"):
    har phase me voice LEAD ke baad shuru hoti he aur khatam hone ke baad
    BREATH ka saans-bhar sannata rehta he — rounds ab ek doosre me nahi ghuste.
    """
    from moviepy.editor import AudioFileClip, CompositeAudioClip, VideoClip
    from video import _trim_silence_file

    LEAD, BREATH = 0.35, 0.85
    auds = [AudioFileClip(_trim_silence_file(f)).audio_fadein(0.03).audio_fadeout(0.06)
            for f in voice_files]
    phases, t0 = [], 0.0
    for a in auds:
        dur = max(2.4, LEAD + a.duration + BREATH)
        phases.append((t0, t0 + dur))
        t0 += dur
    total = phases[-1][1]
    frame = versus_frames(p1, p2, img1, img2, rounds, phases, payoff, col1, col2)
    clip = VideoClip(lambda t: frame(t), duration=total)
    audio = CompositeAudioClip([a.set_start(phases[i][0] + LEAD)
                                for i, a in enumerate(auds)]).set_duration(total)
    return clip.set_audio(audio)
