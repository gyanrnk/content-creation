"""
auth_channel.py — kisi DOOSRE channel ke liye token banata he.

Kyun: YouTube ka OAuth token EK channel se bandha hota he — jo tumne consent
screen pe chuna tha. Ek hi Google account pe do channel ho sakte he, par ek
token se dono ko nahi chhu sakte. Har channel ka apna token chahiye.

Chalao:
    python auth_channel.py main
        -> browser khulega
        -> Google account chuno
        -> "Choose a channel" wale screen pe MAIN channel chuno (Footy Gyaan NAHI)
        -> tokens/main.upload.json + tokens/main.read.json ban jaayenge

Phir batao, main pipeline ko us channel pe point kar dunga.

Dhyan: agar channel picker aaye hi nahi, matlab us Google account pe sirf ek hi
channel he — tab pehle YouTube pe naya channel banana padega.
"""

import os
import sys
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
TOKEN_DIR = os.path.join(ROOT, "tokens")
CLIENT_SECRET = os.path.join(ROOT, "client_secret.json")

UPLOAD_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
READ_SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly",
               "https://www.googleapis.com/auth/youtube.readonly"]


def _flow(scopes):
    from google_auth_oauthlib.flow import InstalledAppFlow
    f = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, scopes)
    # prompt=consent + select_account -> Google har baar channel picker dikhata he
    return f.run_local_server(port=0, prompt="consent")


def _whoami(creds) -> dict | None:
    from googleapiclient.discovery import build
    try:
        yt = build("youtube", "v3", credentials=creds)
        r = yt.channels().list(part="snippet,statistics", mine=True).execute()
        if r.get("items"):
            ch = r["items"][0]
            return {"id": ch["id"], "title": ch["snippet"]["title"],
                    "handle": ch["snippet"].get("customUrl"),
                    "videos": ch["statistics"].get("videoCount"),
                    "subs": ch["statistics"].get("subscriberCount")}
    except Exception as e:
        print(f"[warn] channel padha nahi ja saka: {str(e)[:120]}")
    return None


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "main"
    os.makedirs(TOKEN_DIR, exist_ok=True)

    print("\n" + "=" * 62)
    print(f"  '{label}' channel ke liye token bana rahe he")
    print("=" * 62)
    print("  Browser khulega. Channel picker pe DHYAN se sahi channel chuno.")
    print("  Footy Gyaan chunoge to purana hi token dobara ban jaayega.\n")

    print("[1/2] READ access (analytics + channel info)...")
    read = _flow(READ_SCOPES)
    who = _whoami(read)
    if who:
        print(f"      -> {who['title']}  ({who['handle']})  "
              f"{who['videos']} videos, {who['subs']} subs")
        if who["id"] == "UCVWd1ltqBvlyX8skmkaKyDQ":
            print("\n  ⚠️  Ye Footy Gyaan hi he — DOOSRA channel nahi chuna gaya.")
            print("      Dobara chalao aur picker pe main channel select karo.")
            if input("      Phir bhi save karun? (y/N): ").strip().lower() != "y":
                return

    rp = os.path.join(TOKEN_DIR, f"{label}.read.json")
    with open(rp, "w", encoding="utf-8") as f:
        f.write(read.to_json())
    print(f"      saved: {rp}")

    print("\n[2/2] UPLOAD access...")
    up = _flow(UPLOAD_SCOPES)
    upp = os.path.join(TOKEN_DIR, f"{label}.upload.json")
    with open(upp, "w", encoding="utf-8") as f:
        f.write(up.to_json())
    print(f"      saved: {upp}")

    if who:
        meta = os.path.join(TOKEN_DIR, f"{label}.channel.json")
        with open(meta, "w", encoding="utf-8") as f:
            json.dump(who, f, ensure_ascii=False, indent=2)
        print(f"      saved: {meta}")

    print("\n✅ Ho gaya. Ab Claude ko bolo — pipeline is channel pe point kar dega.")
    input("Enter dabao band karne ke liye...")


if __name__ == "__main__":
    main()
