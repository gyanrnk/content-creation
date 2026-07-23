"""
YouTube ANALYTICS ka ek-baar wala OAuth — retention data (kis second pe log
bhaagte he) padhne ke liye. Upload wala token.json alag he aur waisa hi rahega;
ye ANALYTICS_TOKEN me alag se save hota he.

Kyun: user ne pakda ki views sirf shuru me aate he, baad me ruk jaate he —
matlab algorithm ka test-batch mil raha he par video use PASS nahi kar raha.
Kahan fail ho raha he (CTA card? intro? beech me?) ye sirf retention curve
bata sakta he — isi ke liye ye scope chahiye.
"""
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]
ANALYTICS_TOKEN = "analytics_token.json"   # .gitignore me he (token* pattern)

flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0, prompt="consent")
with open(ANALYTICS_TOKEN, "w", encoding="utf-8") as f:
    f.write(creds.to_json())
print(f"\n[OK] {ANALYTICS_TOKEN} ban gaya — ab Claude retention data nikal sakta he.")
input("Enter dabao band karne ke liye...")
