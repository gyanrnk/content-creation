"""
trending.py — YouTube pe ABHI kaunse football shorts pe views aa rahe hain, usse
HOT players/topics nikaalta hai.

Idea (user): jo topic abhi trend kar raha hai, usi pe apna content banao -> us wave
pe algorithm humein bhi push karta hai. LEGAL: hum sirf TOPIC lete hain (topic pe
copyright nahi hota) — kisi ka video/script/footage copy NAHI karte, apna banate hain.

⚠️ QUOTA (zaroori): search.list = 100 units, aur upload = 1600 x 6 = 9600/din
(limit 10,000). Isliye HAR BUILD pe search NAHI kar sakte (6 x 100 = 600 -> upload
fail ho jaate). Solution: din me 1-2 baar search -> result CACHE me; har build
cache padhta hai = 0 extra quota.

Key: YOUTUBE_API_KEY (.env / GitHub secret). Na ho to () return -> ideas.py apne
purane news-based trending pe chalta rehta (kuch tootta nahi).
"""

import os
import re
import json
import time
import datetime

CACHE = os.path.join("data", "trending_cache.json")
TTL_HOURS = 12          # itni der purana cache chalega (quota bachane ko)
_API = "https://www.googleapis.com/youtube/v3/search"


def _search_titles(query: str = "football", n: int = 25) -> list:
    """Pichhle 2 din ke SABSE ZYADA VIEW wale football shorts ke titles."""
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        return []
    try:
        import requests
        after = (datetime.datetime.now(datetime.timezone.utc)
                 - datetime.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = requests.get(_API, timeout=25, params={
            "key": key, "part": "snippet", "q": query, "type": "video",
            "videoDuration": "short",        # sirf Shorts
            "order": "viewCount",            # sabse zyada views wale pehle
            "publishedAfter": after,         # sirf RECENT (2 din)
            "maxResults": n,
            "regionCode": "IN",              # India ka trend
            "relevanceLanguage": "hi",
        })
        if r.status_code != 200:
            print(f"[trending] search HTTP {r.status_code}: {r.text[:120]}")
            return []
        return [it["snippet"]["title"] for it in r.json().get("items", [])]
    except Exception as e:
        print(f"[trending] search fail: {e}")
        return []


def _fresh_cache():
    """Cache padho agar TTL ke andar hai."""
    try:
        with open(CACHE, encoding="utf-8") as f:
            c = json.load(f)
        if time.time() - c.get("ts", 0) < TTL_HOURS * 3600:
            return c
    except Exception:
        pass
    return None


def hot_subjects(force: bool = False) -> list:
    """YouTube pe abhi trend kar rahe PLAYERS/TEAMS (hamare pool me se), views ke
    order me. Cache se — din me 1-2 baar hi asli search (quota safe)."""
    c = None if force else _fresh_cache()
    if c is None:
        titles = _search_titles()
        if not titles:
            return []                      # key nahi / fail -> chup-chaap khali
        from ideas import PLAYERS, TEAMS
        blob = " || ".join(titles).lower()
        # jo naam trending titles me sabse zyada baar aaye, wahi sabse hot
        hits = []
        for nm in sorted(PLAYERS + TEAMS, key=len, reverse=True):
            cnt = blob.count(nm.lower())
            if cnt:
                hits.append((cnt, nm))
        hits.sort(reverse=True)
        c = {"ts": time.time(), "subjects": [n for _, n in hits],
             "titles": titles[:10]}
        try:
            os.makedirs("data", exist_ok=True)
            with open(CACHE, "w", encoding="utf-8") as f:
                json.dump(c, f, ensure_ascii=False, indent=1)
            print(f"[trending] refreshed: {len(c['subjects'])} hot subjects")
        except Exception:
            pass
    return c.get("subjects", [])


if __name__ == "__main__":
    subs = hot_subjects(force=True)
    print("YouTube pe ABHI hot:", subs[:10] or "(YOUTUBE_API_KEY nahi / kuch nahi mila)")
    c = _fresh_cache()
    if c:
        print("\nTrending shorts titles (sample):")
        for t in c.get("titles", [])[:6]:
            print("  -", t[:70])
