# from googleapiclient.discovery import build
# from googleapiclient.http import MediaFileUpload
# from dotenv import load_dotenv
# import os

# load_dotenv()

# def upload_video(file):

#     youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))
#     request = youtube.videos().insert(
#         part="snippet,status",
#         body={
#             "snippet":{
#                 "title":"AI Cartoon Story",
#                 "description":"Auto generated cartoon video"
#             },
#             "status":{
#                 "privacyStatus":"public"
#             }
#         },
#         media_body=MediaFileUpload(file)
#     )

#     request.execute()




"""
youtube_upload.py — Uploads the final kids cartoon video to YouTube.

Key change from original:
    - Added made_for_kids=True  (COPPA compliance — mandatory for kids content)
    - Added kid-friendly category, tags, and description
    - Added title parameter so main.py can pass dynamic title

Setup (one-time):
    1. Go to https://console.cloud.google.com
    2. Create a project → enable "YouTube Data API v3"
    3. Create OAuth 2.0 credentials → download as client_secret.json
    4. Place client_secret.json in the project root folder
    5. First run will open browser for Google account authorization

Requires:
    pip install google-api-python-client google-auth-oauthlib
"""

import os
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ── Config ────────────────────────────────────────────────────────────────────

SCOPES              = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "client_secret.json"
TOKEN_PICKLE        = "token.pickle"

# Default metadata for kids content
DEFAULT_TITLE       = "Cute Kids Cartoon Story 🐼 | Fun Moral Story for Children"
DEFAULT_DESCRIPTION = (
    "🌟 A fun and colorful 2D cartoon story for kids aged 2-10! \n\n"
    "Watch our adorable character learn an important lesson about kindness and sharing. "
    "Perfect for bedtime stories, classroom time, or just for fun!\n\n"
    "✨ Safe for kids | No ads | Educational\n\n"
    "#kidsstory #cartoonforkids #moralesstory #kidslearning #2dcartoon"
)
DEFAULT_TAGS        = [
    "kids story", "cartoon for kids", "moral story", "children's cartoon",
    "2d animation", "kids learning", "bedtime story", "baby panda",
    "educational video", "safe for kids"
]

# YouTube category ID 1 = Film & Animation (best fit for cartoons)
CATEGORY_ID = "1"

# ── Auth helper ───────────────────────────────────────────────────────────────

def get_authenticated_service():
    """Authenticate and return a YouTube API service object."""
    creds = None

    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"'{CLIENT_SECRETS_FILE}' not found. "
                    "Download it from Google Cloud Console → OAuth 2.0 credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PICKLE, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)

# ── Main upload function ──────────────────────────────────────────────────────

def upload_video(video_path: str, title: str = DEFAULT_TITLE) -> str:
    """
    Upload the final kids video to YouTube with COPPA-compliant settings.

    Args:
        video_path : Path to the final MP4 file
        title      : Video title (passed from main.py)

    Returns:
        YouTube video ID of the uploaded video
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    print(f"[youtube] Authenticating...")
    youtube = get_authenticated_service()

    request_body = {
        "snippet": {
            "title":       title,
            "description": DEFAULT_DESCRIPTION,
            "tags":        DEFAULT_TAGS,
            "categoryId":  CATEGORY_ID,
        },
        "status": {
            "privacyStatus":  "public",
            "selfDeclaredMadeForKids": True,   # ← ADDED: COPPA compliance (mandatory)
        }
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,      # Supports large file uploads without timeout
        chunksize=10 * 1024 * 1024,   # 10MB chunks
    )

    print(f"[youtube] Uploading '{title}'...")
    upload_request = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = upload_request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"[youtube] Upload progress: {pct}%")

    video_id  = response.get("id")
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"[youtube] ✅ Uploaded! Watch at: {video_url}")
    return video_id