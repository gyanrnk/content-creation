"""
upload_youtube.py — Video ko YouTube pe upload karta hai (Data API v3, resumable).

Ek baar setup (manual, Google Cloud):
  1. https://console.cloud.google.com → naya project
  2. "YouTube Data API v3" enable karo
  3. OAuth consent screen (External, apni email test user me add)
  4. Credentials → OAuth client ID → "Desktop app" → JSON download
  5. Us file ka naam "client_secret.json" rakho, project folder me daalo
  6. Ek baar terminal me:  env\\Scripts\\python.exe upload_youtube.py auth
     (browser khulega, Google login → allow → token.json ban jaayega)

Uske baad:
  - CLI:  env\\Scripts\\python.exe upload_youtube.py upload unlisted
  - App:  "⬆️ Upload to YouTube" button
"""

import os
import sys
import json

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET = "client_secret.json"
TOKEN = "token.json"


def _save(creds):
    with open(TOKEN, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def _creds():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    if not os.path.exists(TOKEN):
        return None
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save(creds)
    return creds


def auth():
    """Ek baar browser OAuth -> token.json save."""
    from google_auth_oauthlib.flow import InstalledAppFlow
    if not os.path.exists(CLIENT_SECRET):
        print(f"❌ {CLIENT_SECRET} nahi mila. Google Cloud se OAuth 'Desktop app' JSON "
              f"download karke is naam se project folder me daalo. (docstring dekho)")
        return
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    creds = flow.run_local_server(port=0)
    _save(creds)
    print("✅ Auth done -> token.json saved. Ab upload kar sakte ho.")


def is_authed() -> bool:
    return os.path.exists(TOKEN)


def get_service():
    from googleapiclient.discovery import build
    creds = _creds()
    if not creds or not creds.valid:
        raise RuntimeError("YouTube auth nahi hai — chalao: "
                           "env\\Scripts\\python.exe upload_youtube.py auth")
    return build("youtube", "v3", credentials=creds)


def upload(video: str, title: str, description: str, tags=None,
           privacy: str = "unlisted", thumbnail: str = None) -> str:
    from googleapiclient.http import MediaFileUpload
    yt = get_service()
    title = (title or "Football Short")[:100]
    if "#shorts" not in (description or "").lower():
        description = (description or "") + "\n\n#Shorts"
    body = {
        "snippet": {"title": title, "description": description[:4900],
                    "tags": (tags or [])[:15], "categoryId": "17"},   # 17 = Sports
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video, chunksize=-1, resumable=True, mimetype="video/*")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    if thumbnail and os.path.exists(thumbnail):
        try:
            yt.thumbnails().set(videoId=vid,
                                media_body=MediaFileUpload(thumbnail)).execute()
        except Exception as e:
            print(f"[upload] thumbnail skip ({e})")
    url = f"https://youtu.be/{vid}"
    print(f"✅ Uploaded ({privacy}): {url}")
    return url


def upload_from_output(privacy: str = "unlisted", outdir: str = "output") -> str:
    """output/ me jo video+script+thumbnail bana, use upload karo."""
    with open(os.path.join(outdir, "script.json"), encoding="utf-8") as f:
        data = json.load(f)
    title = data.get("youtube_title") or data.get("title_hindi") or "Football Short"
    desc = (data.get("description", "") + "\n\n"
            + data.get("hashtags", "#Shorts #Football")).strip()
    cp = os.path.join(outdir, "credits.txt")
    if os.path.exists(cp):
        with open(cp, encoding="utf-8") as f:
            desc += "\n\n" + f.read()
    tags = [t.strip("#") for t in data.get("hashtags", "").split() if t.startswith("#")]
    return upload(os.path.join(outdir, "short.mp4"), title, desc, tags, privacy,
                  os.path.join(outdir, "thumbnail.jpg"))


def upload_auto(privacy: str = "unlisted") -> list:
    """output/auto/done.json ke saare successful videos YouTube pe upload karo
    (GitHub Actions / batch ke liye). URLs ki list return karta hai."""
    dj = os.path.join("output", "auto", "done.json")
    if not os.path.exists(dj):
        print("[upload] output/auto/done.json nahi mila — pehle build karo")
        return []
    with open(dj, encoding="utf-8") as f:
        summary = json.load(f)
    urls = []
    for r in summary.get("results", []):
        if not r.get("ok"):
            continue
        d = r.get("dir")
        if d and os.path.isdir(d):
            try:
                urls.append(upload_from_output(privacy, outdir=d))
            except Exception as e:
                print(f"[upload] FAILED {d}: {e}")
    print(f"[upload] {len(urls)} video(s) uploaded ({privacy})")
    return urls


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "auth"
    if cmd == "auth":
        auth()
    elif cmd == "upload":
        upload_from_output(sys.argv[2] if len(sys.argv) > 2 else "unlisted")
    elif cmd == "upload-auto":
        upload_auto(sys.argv[2] if len(sys.argv) > 2 else "unlisted")
    else:
        print("usage: upload_youtube.py [auth | upload <priv> | upload-auto <priv>]")
