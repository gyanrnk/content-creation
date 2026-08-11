"""
make_score.py — kisi bhi short ke liye ORIGINAL cinematic score banata he.

Kyun: free music libraries se track lena bhi theek he, par usme attribution,
license padhna aur kabhi-kabhi claim ka risk rehta he. Ye track numpy se
synthesize hoti he — koi copyright hai hi nahi, monetization pe bhi safe.

make_music.py se alag: wo ek 38s ka loop banata he. Ye ek TIMED SCORE he jo
video ke acts ke saath chalti he — sparse shuruaat, tension build, release,
phir resolve. Archive.tsx ke 4 acts ke liye tuned.

Run:  python make_score.py archive
"""

import os
import sys
import wave

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SR = 44100
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "remotion-footy", "public")


def midi(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12.0)


def _env(n: int, a: float, d: float, s: float = 0.0, r: float = 0.3) -> np.ndarray:
    """Attack/decay/sustain/release envelope, sab seconds me."""
    e = np.zeros(n)
    ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    ai, di, ri = max(ai, 1), max(di, 1), max(ri, 1)
    si = max(n - ai - di - ri, 0)
    idx = 0
    e[idx:idx + ai] = np.linspace(0, 1, ai); idx += ai
    e[idx:idx + di] = np.linspace(1, s if si else 0, min(di, n - idx)); idx += di
    if si:
        e[idx:idx + si] = s; idx += si
    if idx < n:
        e[idx:] = np.linspace(e[idx - 1] if idx else 0, 0, n - idx)
    return e


def _tone(freq: float, dur: float, harm=(1.0, 0.35, 0.16, 0.07), detune=0.0) -> np.ndarray:
    """Additive tone — thoda detune width deta he (strings jaisa)."""
    n = int(dur * SR)
    t = np.linspace(0, dur, n, False)
    sig = np.zeros(n)
    for i, amp in enumerate(harm, start=1):
        f = freq * i
        sig += amp * np.sin(2 * np.pi * f * t)
        if detune:
            sig += amp * 0.6 * np.sin(2 * np.pi * f * (1 + detune) * t)
    return sig / (len(harm) * (1.6 if detune else 1.0))


def _place(buf: np.ndarray, sig: np.ndarray, at: float, gain: float = 1.0):
    i = int(at * SR)
    j = min(i + len(sig), len(buf))
    if i < len(buf):
        buf[i:j] += sig[:j - i] * gain


def _reverb(x: np.ndarray, taps=((0.041, 0.30), (0.073, 0.22), (0.113, 0.16),
                                 (0.157, 0.11), (0.211, 0.07))) -> np.ndarray:
    """Sasta plate reverb — cinematic feel ke liye zaroori he."""
    out = x.copy()
    for delay, amt in taps:
        d = int(delay * SR)
        if d < len(x):
            out[d:] += x[:-d] * amt
    return out


def archive_score(total: float = 16.0) -> np.ndarray:
    """
    Archive.tsx ke acts ke hisaab se:
      0.0-5.2   ACT1  1966 — sparse piano, low pad, sombre (A minor)
      5.2-8.1   ACT2  58 saal ka scrub — pulse + rising tension
      8.1-13.6  ACT3  2024 — release, major lift, energy
      13.6-16.0 ACT4  '6' — swell, phir decay (loop ke liye silence)
    """
    n = int(total * SR)
    buf = np.zeros(n)

    # ── ACT 1: sombre. A minor triad pad + lone piano notes ──────────────
    for m, g in ((45, 0.16), (52, 0.12), (57, 0.10)):        # A2 E3 A3
        pad = _tone(midi(m), 5.6, harm=(1.0, 0.28, 0.10), detune=0.004)
        _place(buf, pad * _env(len(pad), a=1.1, d=1.2, s=0.55, r=2.0), 0.0, g)

    # piano-ish plucks: A, C, E, A — ek-ek karke, khaali jagah ke saath
    for at, m in ((0.35, 69), (1.55, 72), (2.75, 76), (4.05, 81)):
        p = _tone(midi(m), 1.8, harm=(1.0, 0.42, 0.20, 0.09))
        _place(buf, p * _env(len(p), a=0.004, d=1.5, s=0.0, r=0.3), at, 0.22)

    # ── ACT 2: tension. heartbeat pulse + riser ──────────────────────────
    for k in range(9):                                        # ~3 pulses/sec
        at = 5.25 + k * 0.32
        b = _tone(midi(33), 0.30, harm=(1.0, 0.2))            # low thud
        _place(buf, b * _env(len(b), a=0.002, d=0.26, s=0.0, r=0.04), at, 0.23)

    rise_d = 2.9
    rn = int(rise_d * SR)
    rt = np.linspace(0, rise_d, rn, False)
    sweep = np.sin(2 * np.pi * (midi(52) * (1 + 1.15 * (rt / rise_d) ** 2)) * rt)
    _place(buf, sweep * _env(rn, a=1.6, d=1.0, s=0.0, r=0.3), 5.2, 0.11)

    # ── ACT 3: release. C major lift, warmer + wider ─────────────────────
    # Payoff must be the LOUDEST moment. First cut had act 3 quieter than the
    # tension build, so the reveal landed as a deflation instead of a release.
    for m, g in ((48, 0.30), (60, 0.25), (64, 0.21), (67, 0.19)):   # C3 C4 E4 G4
        pad = _tone(midi(m), 5.9, harm=(1.0, 0.32, 0.14, 0.06), detune=0.005)
        _place(buf, pad * _env(len(pad), a=0.35, d=1.4, s=0.78, r=1.8), 8.05, g)

    # sustained low drone holds the floor up across the whole act
    dr = _tone(midi(36), 5.6, harm=(1.0, 0.24, 0.08), detune=0.003)
    _place(buf, dr * _env(len(dr), a=0.5, d=1.0, s=0.7, r=1.6), 8.05, 0.22)

    # impact on the 2024 hit
    imp = _tone(midi(36), 1.5, harm=(1.0, 0.3, 0.1))
    _place(buf, imp * _env(len(imp), a=0.002, d=1.3, s=0.0, r=0.2), 8.05, 0.40)

    # arpeggio — movement, taaki 5s flat na lage
    arp = [(8.6, 72), (9.2, 76), (9.8, 79), (10.4, 84), (11.0, 79), (11.6, 76),
           (12.2, 72), (12.8, 76)]
    for at, m in arp:
        p = _tone(midi(m), 1.1, harm=(1.0, 0.38, 0.15))
        _place(buf, p * _env(len(p), a=0.004, d=0.95, s=0.0, r=0.15), at, 0.24)

    # ── ACT 4: resolve, phir gir jaana (loop joint silent rehna chahiye) ─
    for m, g in ((36, 0.26), (48, 0.23), (55, 0.19), (60, 0.17)):
        pad = _tone(midi(m), 2.6, harm=(1.0, 0.30, 0.12), detune=0.004)
        _place(buf, pad * _env(len(pad), a=0.06, d=0.9, s=0.55, r=1.5), 13.5, g)

    buf = _reverb(buf)

    # soft-knee limiter — clipping se bachao, headroom chhodo
    peak = np.max(np.abs(buf)) or 1.0
    buf = np.tanh(buf / peak * 1.25) * 0.82

    # video ke last 0.35s me fade out, taaki replay pe click na sunai de
    fade = int(0.35 * SR)
    buf[-fade:] *= np.linspace(1, 0, fade)
    buf[:int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
    return buf


def write_wav(path: str, mono: np.ndarray):
    stereo = np.stack([mono, mono], axis=1)          # simple stereo
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "w") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f"[score] {path}  {len(mono) / SR:.2f}s")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "archive"
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else 16.0
    os.makedirs(OUT_DIR, exist_ok=True)
    if which == "archive":
        write_wav(os.path.join(OUT_DIR, "score_archive.wav"), archive_score(dur))
    else:
        sys.exit(f"unknown score: {which}")
