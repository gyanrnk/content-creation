"""
channel_history.py — channel pe PEHLE SE kya ja chuka he, wo yaad rakhta he.

Kyun banana pada: 9 Aug ko ek pack upload hua jisme 976 vs 919 / 143 vs 125 /
140 vs 129 tha — bilkul wahi teen comparisons jo 6 Aug ki "Ronaldo's Difference"
me the. footy_packs.py ka novelty gate sirf apni queue dekhta tha, aur channel
ki 101 purani videos uske liye maujood hi nahi thi.

Ab har naya pack channel ke asli itihaas se bhi takraaya jaata he.
"""

import os
import re
import sys
import json
import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, "data", "channel_history.json")
TOKEN = os.path.join(ROOT, "analytics_token.json")
STALE_HOURS = 6

# 3+ same numbers ek hi purani video me = wahi content dobara ban raha he.
CLASH_HITS = 3


def refresh() -> dict:
    """YouTube se saari uploads ka title+description utha ke cache karo."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    yt = build("youtube", "v3", credentials=Credentials.from_authorized_user_file(TOKEN))
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]

    ids, tok = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=up,
                                    maxResults=50, pageToken=tok).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            break

    vids = []
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="snippet", id=",".join(ids[i:i + 50])).execute()["items"]:
            s = v["snippet"]
            text = f"{s['title']} {s.get('description', '')}"
            vids.append({
                "id": v["id"],
                "published": s["publishedAt"][:10],
                "title": s["title"],
                "numbers": sorted(set(int(n) for n in re.findall(r"\b\d{1,4}\b", text)
                                      if 2 <= int(n) <= 2000)),
            })

    data = {"fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "count": len(vids), "videos": vids}
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


def load(auto: bool = True) -> dict:
    """Cache padho. Purana ho to refresh karo (network fail = jo he wahi)."""
    data = None
    if os.path.exists(CACHE):
        try:
            with open(CACHE, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = None

    if auto:
        stale = True
        if data:
            age = datetime.datetime.now() - datetime.datetime.fromisoformat(data["fetched_at"])
            stale = age.total_seconds() > STALE_HOURS * 3600
        if stale:
            try:
                data = refresh()
            except Exception as e:
                print(f"[history] refresh fail ({e}) — purana cache use kar rahe he")
    return data or {"videos": [], "count": 0}


def clash(numbers: list, auto: bool = True) -> dict | None:
    """Agar in numbers ka bada hissa kisi EK purani video me he to wahi video lauta do."""
    want = set(int(n) for n in numbers if 2 <= int(n) <= 2000)
    if len(want) < CLASH_HITS:
        return None
    # Sabse zyada milne wali video lauta do, pehli nahi — wahi asli duplicate he.
    best = None
    for v in load(auto)["videos"]:
        hits = want & set(v["numbers"])
        if len(hits) >= CLASH_HITS and (best is None or len(hits) > len(best["hits"])):
            best = {"video": v, "hits": sorted(hits)}
    return best


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "refresh":
        d = refresh()
        print(f"[history] {d['count']} videos cache ho gayi")
    else:
        d = load()
        print(f"[history] {d['count']} videos, fetched {d.get('fetched_at')}")
        if len(sys.argv) > 1:
            nums = [int(x) for x in sys.argv[1:]]
            c = clash(nums)
            print("CLASH:", c["video"]["published"], c["video"]["title"][:50],
                  "| shared:", c["hits"]) if c else print("clash nahi")
