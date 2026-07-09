# ☁️ GitHub Actions — 24/7 Auto Shorts (no PC needed, free)

Cron roz GitHub ke server pe video banata hai → YouTube pe unlisted upload (ya artifact
download) → tum review karke public. **PC OFF bhi chalega.**

## Kaise kaam karta hai
```
GitHub cron (roz 11:00 UTC = 16:30 IST)
   → Ubuntu runner: python deps + ffmpeg + Hindi fonts install
   → auto.py  (topic→script→Madhur voice→media→render, variety modes)
   → YouTube unlisted upload (agar YT_TOKEN secret hai) + video artifact
   → asset_history.json wapas commit (dedup chalta rahe)
```

## Ek-baar setup

### 1. GitHub repo banao
- github.com pe naya repo → **Public** rakho (public = **unlimited** free Actions minutes;
  code me koi secret nahi, keys alag secrets me jaati hain). Private bhi chalega (2000 min/mahina).

### 2. Project push karo
Terminal me (project folder me):
```
git init
git add .
git commit -m "football shorts automation"
git branch -M main
git remote add origin https://github.com/<tumhara-username>/<repo>.git
git push -u origin main
```
`.gitignore` secrets (.env, token.json, client_secret.json) ko **automatically rok deta hai** —
wo push nahi honge. `assets/bgm.mp3`, code, `.github/` push honge.

### 3. Secrets add karo
Repo → **Settings → Secrets and variables → Actions → New repository secret**:
| Secret | Value |
|--------|-------|
| `GROQ_API_KEY` | tumhari Groq key (`.env` se) |
| `PEXELS_API_KEY` | tumhari Pexels key (`.env` se) |
| `YT_CLIENT_SECRET` | *(auto-upload ke liye)* `client_secret.json` ka pura content |
| `YT_TOKEN` | *(auto-upload ke liye)* `token.json` ka pura content |

**YouTube auto-upload chahiye to** (warna skip — sirf artifact milega):
- Pehle LOCAL pe ek baar: `env\Scripts\python.exe upload_youtube.py auth` (personal Gmail se)
- Ban-ne wali `token.json` + `client_secret.json` ka content copy karke upar wale 2 secrets me daalo.

### 4. Bas! Ab
- **Roz apne aap** 16:30 IST pe chalega. Time badalna ho to `.github/workflows/daily-shorts.yml`
  me `cron: "0 11 * * *"` change karo (UTC me — IST se 5:30 ghante peeche).
- **Abhi test:** repo → **Actions** tab → "Daily Football Shorts" → **Run workflow** (count/privacy daal ke).

## Output kahan
- **Artifacts:** Actions → us run → neeche "shorts-<num>" zip (video+thumbnail+post.txt) download.
- **YouTube:** unlisted upload (agar YT_TOKEN set) → Studio me review → **Public** karo.

## Kitne/din
- Workflow default `count=1`. Zyada ke liye "Run workflow" me count badlo, ya cron ki alag lines add karo.
- Render ~10-15 min/video runner pe. Public repo = unlimited; private = 2000 min/mahina (~1-2/din easily).

## Notes
- Actions pe **CLIP off** (torch heavy) — real photos phir bhi aate hain (bas rerank nahi). Voice = **Madhur**.
- Dedup `asset_history.json` har run ke baad commit-back hota hai → videos me repeat visuals nahi.
- Review manual rakho (free-LLM kabhi fact galat) — isiliye unlisted upload, phir tum public karo.
