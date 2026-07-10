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

GH = r"C:\Program Files\GitHub CLI\gh.exe"
REPO = "gyanrnk/content-creation"
OUT = "videos"


def _gh(*args):
    return subprocess.run([GH, *args], capture_output=True, text=True)


def main():
    _gh("auth", "switch", "--user", "gyanrnk", "--hostname", "github.com")

    rid = sys.argv[1] if len(sys.argv) > 1 else None
    if not rid:
        r = _gh("run", "list", "--repo", REPO, "--limit", "1",
                "--json", "databaseId", "--jq", ".[0].databaseId")
        rid = (r.stdout or "").strip()
    if not rid:
        print("❌ koi run nahi mila")
        return

    tmp = tempfile.mkdtemp()
    r = _gh("run", "download", rid, "--repo", REPO, "--dir", tmp)
    if r.returncode != 0:
        print(f"❌ download fail (run {rid}): {r.stderr[:200]}")
        shutil.rmtree(tmp, ignore_errors=True)
        return

    os.makedirs(OUT, exist_ok=True)
    n = 0
    for mp4 in glob.glob(os.path.join(tmp, "**", "short.mp4"), recursive=True):
        seg = os.path.basename(os.path.dirname(mp4))                    # 01_world-cup-2026
        date = os.path.basename(os.path.dirname(os.path.dirname(mp4)))  # 2026-07-10_1040
        base = f"{date}__{seg}"
        shutil.copy(mp4, os.path.join(OUT, base + ".mp4"))
        for extra in ("thumbnail.jpg", "post.txt"):
            src = os.path.join(os.path.dirname(mp4), extra)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(OUT, f"{base}_{extra}"))
        n += 1
        print(f"  ✅ {OUT}/{base}.mp4")

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n🎉 {n} video(s) -> '{OUT}/' folder (readable naam, ek jagah)")


if __name__ == "__main__":
    main()
