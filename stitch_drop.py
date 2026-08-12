"""
stitch_drop.py — teen Veo clips ko ek lagataar descent me jodta he.

Kya karta he:
  1. sabko 1080x1920 pe laata he (Veo ne 720p aur 1080p mix diya tha)
  2. kinare se 8% crop -> Veo ka bottom-right watermark nikal jaata he
  3. har clip ka sirf kaam ka hissa leta he
  4. cross-dissolve se jodta he taaki teen clip ek hi girna lage
  5. audio hata deta he (apna score alag se aayega)

Run:  python stitch_drop.py
Out:  remotion-footy/public/drop_base.mp4
"""

import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "output", "blue")
OUT = os.path.join(ROOT, "remotion-footy", "public", "drop_base.mp4")

W, H, FPS = 1080, 1920, 30
CROP = 0.92          # 8% andar -> watermark bahar
XF = 0.7             # cross-dissolve seconds

# (file, start, duration) — kis clip ka kaunsa hissa
# clip1 static he aur surface dikhata he, isliye sirf shuruaat
# clip2 asli descent he, poora
# clip3 abyss, thoda trim
SEGMENTS = [
    ("drop1.mp4", 0.6, 3.4),
    ("drop2.mp4", 0.0, 8.0),
    ("drop3.mp4", 0.8, 6.6),
]


def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-700:])
    return r


def main():
    tmp = []
    for i, (f, ss, dur) in enumerate(SEGMENTS):
        src = os.path.join(SRC, f)
        dst = os.path.join(SRC, f"_seg{i}.mp4")
        vf = (f"crop=iw*{CROP}:ih*{CROP}:iw*{(1-CROP)/2}:ih*{(1-CROP)/2},"
              f"scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p")
        run(f'ffmpeg -y -v error -ss {ss} -t {dur} -i "{src}" '
            f'-vf "{vf}" -an -c:v libx264 -crf 16 -preset slow "{dst}"')
        tmp.append(dst)
        print(f"  [{i}] {f}  {ss}s +{dur}s -> {W}x{H}")

    # xfade chain: har jod pe cross-dissolve
    inputs = " ".join(f'-i "{t}"' for t in tmp)
    d0, d1, d2 = (s[2] for s in SEGMENTS)
    off1 = d0 - XF
    off2 = off1 + d1 - XF
    fc = (f"[0:v][1:v]xfade=transition=fade:duration={XF}:offset={off1}[a];"
          f"[a][2:v]xfade=transition=fade:duration={XF}:offset={off2}[v]")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    run(f'ffmpeg -y -v error {inputs} -filter_complex "{fc}" -map "[v]" '
        f'-c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p "{OUT}"')

    for t in tmp:
        os.remove(t)

    total = d0 + d1 + d2 - 2 * XF
    print(f"\n[stitch] {OUT}")
    print(f"[stitch] {total:.1f}s  ({d0}+{d1}+{d2} minus 2x{XF}s dissolve)")


if __name__ == "__main__":
    main()
