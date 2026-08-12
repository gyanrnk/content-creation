"""
channels.py — kaunsa channel, kaunsa token. Ek hi jagah.

Kyun: teen channel ek hi Google account pe he. Galti se galat channel pe upload
ho jaana aasaan he aur wapas nahi hota. Isliye upload se PEHLE ye module token
se channel id padhta he aur expected id se milata he. Match nahi hua to upload
hota hi nahi.

    from channels import upload_to
    url = upload_to("blue", video, title, desc, tags)
"""

import os
import json

ROOT = os.path.dirname(os.path.abspath(__file__))

CHANNELS = {
    "blue": {
        "name": "Below The Blue",
        "handle": "@belowtheblue_deep",
        "id": "UCEgiheENOydpPhNfANe13AQ",
        "niche": "deep sea / unknown ocean",
        "upload_token": os.path.join(ROOT, "tokens", "fresh.upload.json"),
        "read_token": os.path.join(ROOT, "tokens", "fresh.read.json"),
    },
    "footy": {
        "name": "Footy Gyaan ⚽",
        "handle": "@FootyGyaan",
        "id": "UCVWd1ltqBvlyX8skmkaKyDQ",
        "niche": "football shorts",
        "upload_token": os.path.join(ROOT, "token.json"),
        "read_token": os.path.join(ROOT, "analytics_token.json"),
    },
}

# Ye channel jaan-boojh ke registry me nahi he. 121 purani multi-hour streams,
# 89 lifetime views. Ispe kuch nahi jaana chahiye.
BLOCKED = {"UC7iKVpbM9imiX95nAMOr4_w": "ThechyoGyan — upload karna mana he"}


def get(label: str) -> dict:
    if label not in CHANNELS:
        raise KeyError(f"unknown channel '{label}' — options: {list(CHANNELS)}")
    return CHANNELS[label]


def whoami(label: str) -> dict:
    """Token se ASLI channel padho (registry pe bharosa mat karo)."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    ch = get(label)
    creds = Credentials.from_authorized_user_file(ch["read_token"])
    yt = build("youtube", "v3", credentials=creds)
    r = yt.channels().list(part="snippet,statistics", mine=True).execute()
    if not r.get("items"):
        raise RuntimeError(f"'{label}' ka read token kisi channel se juda nahi")
    got = r["items"][0]
    return {"id": got["id"], "title": got["snippet"]["title"],
            "handle": got["snippet"].get("customUrl"),
            "videos": got["statistics"].get("videoCount"),
            "subs": got["statistics"].get("subscriberCount")}


def verify(label: str) -> dict:
    """Registry ki id aur token ki id milti he ya nahi. Mismatch = exception."""
    want = get(label)
    got = whoami(label)
    if got["id"] in BLOCKED:
        raise RuntimeError(f"BLOCKED: {BLOCKED[got['id']]}")
    if got["id"] != want["id"]:
        raise RuntimeError(
            f"CHANNEL MISMATCH — '{label}' ka token '{got['title']}' "
            f"({got['id']}) se juda he, par hona chahiye tha '{want['name']}' "
            f"({want['id']}). Upload roka gaya. "
            f"Theek karne ke liye: python auth_channel.py <label>")
    return got


def upload_to(label: str, video: str, title: str, description: str,
              tags=None, privacy: str = "public") -> str:
    """Verify karke hi upload karo."""
    import upload_youtube as uy

    got = verify(label)
    print(f"[channels] target OK: {got['title']} ({got['handle']}) "
          f"— {got['videos']} videos, {got['subs']} subs")

    ch = get(label)
    # upload_youtube apna TOKEN constant use karta he, isliye us channel ka
    # token temporarily uske raaste pe rakhna padta he
    orig = uy.TOKEN
    try:
        uy.TOKEN = ch["upload_token"]
        return uy.upload(video, title, description, tags=tags, privacy=privacy)
    finally:
        uy.TOKEN = orig


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    for label in CHANNELS:
        try:
            g = verify(label)
            print(f"✅ {label:<6} {g['title']:<18} {g['handle']:<22} "
                  f"{g['videos']:>4} videos  {g['subs']:>4} subs")
        except Exception as e:
            print(f"❌ {label:<6} {str(e)[:100]}")
