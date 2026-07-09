"""
make_music.py — Original cinematic sports background track generate karta hai.

Ye track NUMPY se banti hai (synthesized) — matlab kisi ka copyright NAHI,
100% safe for monetization (koi claim/strike possible nahi). assets/bgm.mp3 me save.

Run:  env\\Scripts\\python.exe make_music.py
"""
import os
import wave
import subprocess
import numpy as np
import imageio_ffmpeg

SR = 44100
BPM = 100
BEAT = 60.0 / BPM          # 0.6s
BAR = BEAT * 4
BARS = 16
DUR = BAR * BARS           # ~38s

os.makedirs("assets", exist_ok=True)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


# Dramatic minor progression: Cm - Ab - Eb - Bb (i - VI - III - VII)
CHORDS = [[48, 51, 55], [44, 48, 51], [51, 55, 58], [46, 50, 53]]
BASS = [36, 32, 39, 34]

t_total = np.linspace(0, DUR, int(SR * DUR), False)
mix = np.zeros_like(t_total)


def env(length, a=0.01, r=0.1):
    n = int(length * SR)
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] = np.linspace(1, 0, nr)
    return e


def tone(freq, length, wave_type="sine"):
    n = int(length * SR)
    tt = np.linspace(0, length, n, False)
    if wave_type == "saw":
        sig = 2 * (tt * freq - np.floor(0.5 + tt * freq))
    else:
        sig = np.sin(2 * np.pi * freq * tt)
    return sig


def add(sig, start):
    s = int(start * SR)
    e = min(len(mix), s + len(sig))
    mix[s:e] += sig[:e - s]


# ── Build bar by bar ──────────────────────────────────────────────────────────
for b in range(BARS):
    ch = CHORDS[b % 4]
    bass_note = BASS[b % 4]
    t0 = b * BAR

    # Pad (sustained chord, soft)
    for m in ch:
        s = tone(midi(m), BAR, "sine") * env(BAR, a=0.15, r=0.3) * 0.10
        s += tone(midi(m + 12), BAR, "sine") * env(BAR, a=0.2, r=0.3) * 0.05
        add(s, t0)

    # Bass pulse (har beat)
    for beat in range(4):
        s = tone(midi(bass_note), BEAT * 0.9, "saw") * env(BEAT * 0.9, 0.005, 0.15) * 0.18
        add(s, t0 + beat * BEAT)

    # Kick (beats 1 & 3) — low sine thump
    for beat in (0, 2):
        n = int(0.18 * SR)
        tt = np.linspace(0, 0.18, n, False)
        k = np.sin(2 * np.pi * (110 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 22) * 0.5
        add(k, t0 + beat * BEAT)

    # Hi-hat (har 8th) — short filtered noise
    for eighth in range(8):
        n = int(0.05 * SR)
        h = np.random.randn(n) * np.exp(-np.linspace(0, 0.05, n) * 80) * 0.06
        add(h, t0 + eighth * BEAT / 2)

# Normalize
mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.8

# Write WAV then convert to mp3
wav_path = "assets/_bgm.wav"
w = wave.open(wav_path, "w")
w.setnchannels(1)
w.setsampwidth(2)
w.setframerate(SR)
w.writeframes((mix * 32767).astype(np.int16).tobytes())
w.close()

ff = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ff, "-y", "-i", wav_path, "-b:a", "160k", "assets/bgm.mp3"],
               capture_output=True)
os.remove(wav_path)
print(f"✅ Original royalty-free track ready: assets/bgm.mp3  ({DUR:.0f}s)")
print("   100% copyright-safe (synthesized) — koi claim/strike possible nahi.")
