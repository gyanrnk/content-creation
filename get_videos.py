"""
get_videos.py — Latest cloud build ki videos ek CLEAN 'videos/' folder me laao
(readable naam ke saath). GitHub artifact ki nested folders ki jhanjhat khatam.

Chalao:  python get_videos.py           # latest run
         python get_videos.py <run_id>  # specific run

(gh CLI gyanrnk account pe hona chahiye — script khud switch kar deti hai.)
"""

import os
import sys
import glob
import shutil
import tempfile
import subprocess

try:                       # Windows cmd console (cp1252) pe emoji crash na kare
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

GH = r"C:\Program Files\GitHub CLI\gh.exe"
REPO = "gyanrnk/content-creation"
OUT = "videos"


def _gh(*args):
    return subprocess.run([GH, *args], capture_output=True, text=True)


def main():
    _gh("auth", "switch", "--user", "gyanrnk", "--hostname", "github.com")

    # Agar run-id diya hai to sirf wahi; warna pichhle 12 successful run try karo
    if len(sys.argv) > 1:
        run_ids = [sys.argv[1]]
    else:
        r = _gh("run", "list", "--repo", REPO, "--limit", "12",
                "--status", "success", "--workflow", "daily-shorts.yml",
                "--json", "databaseId", "--jq", ".[].databaseId")
        run_ids = [x for x in (r.stdout or "").split() if x.strip()]
    if not run_ids:
        print("ERROR: koi run nahi mila")
        return

    os.makedirs(OUT, exist_ok=True)
    n = 0
    for rid in run_ids:
        tmp = tempfile.mkdtemp()
        r = _gh("run", "download", rid, "--repo", REPO, "--dir", tmp)
        mp4s = glob.glob(os.path.join(tmp, "**", "short.mp4"), recursive=True)
        if r.returncode != 0 or not mp4s:
            shutil.rmtree(tmp, ignore_errors=True)
            continue                        # is run me video nahi — agla try karo
        for mp4 in mp4s:
            seg = os.path.basename(os.path.dirname(mp4))                    # 01_world-cup
            date = os.path.basename(os.path.dirname(os.path.dirname(mp4)))  # 2026-07-10_1040
            base = f"{date}__{seg}"
            dest = os.path.join(OUT, base + ".mp4")
            if os.path.exists(dest):
                continue                     # pehle se download hai — skip (dedup)
            shutil.copy(mp4, dest)
            for extra in ("thumbnail.jpg", "post.txt"):
                src = os.path.join(os.path.dirname(mp4), extra)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(OUT, f"{base}_{extra}"))
            n += 1
            print(f"  OK: {OUT}/{base}.mp4")
        shutil.rmtree(tmp, ignore_errors=True)
        if len(sys.argv) > 1:
            break                            # specific run tha to yahin ruk jao

    if n == 0:
        print("  (koi NAYI video nahi mili — sab pehle se videos/ me hain)")
    print(f"\nDONE: {n} nayi video(s) -> '{OUT}/' folder")


if __name__ == "__main__":
    main()
