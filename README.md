# ⚽ Football World Cup Shorts Generator

30-40 second vertical (9:16) shorts — **Hindi voice + English subtitles** — for
YouTube Shorts, Instagram Reels & Facebook. **No heavy GPU needed.** Sab kuch
free APIs par chalta hai.

## ⚖️ SAFETY / COPYRIGHT (monetize karne se pehle padho)

| Cheez | Rule |
|-------|------|
| 🎵 **Music** | SIRF royalty-free (Pixabay / YT Audio Library). Copyrighted = **instant strike/Content-ID claim**. Kabhi gaana mat ripp karna. |
| 🖼️ **Images** | `SAFE_MODE = True` (default) → sirf AI (Pollinations) + Pexels (clear license). Real-player CC photos OFF (license uncertain = risk). |
| 🎙️ **Voice** | edge-tts commercial use grey-area hai (copyright nahi). Strike rarely. Full safety chahiye to licensed TTS. |
| 📝 **Content** | Fake/unverified quotes = misinformation flag. Facts check karo (`output/script.json`). Unverified ho to clearly bolo. |
| 🤖 **AI disclosure** | YT/Meta pe AI-generated content disclose karna pad sakta hai — posting ke waqt option on karo. |
| 🔁 **Volume** | Pure faceless AI mass-content YT pe demonetize ho sakta — apni analysis/voice se value add karo. |

**TL;DR:** `SAFE_MODE=True` + royalty-free music + fact-check = clean for monetization.

## Kaise chalayein

### Option A — Streamlit App (recommended, UI ke saath) 🖥️
```
env\Scripts\streamlit run app.py
```
Browser khulega. Wahan:
1. Topic likho, Mode/voice/segments choose karo
2. (Optional) **apni images / voice / background music upload** karo — AI ke saath mix ho jaayengi
3. **🎬 Build Short** dabao → video ban jaayega
4. Preview dekho → **⬇️ Download MP4** → manually YT/FB/Insta par post karo
5. "Script review" me facts check kar lo

### Option B — Command line
1. `config.py` me `TOPIC` aur `MODE` set karo.
2. Run: `env\Scripts\python.exe main.py`
3. Final video: `output/short.mp4`

## Apni files upload (app me)

| Upload | Kaam |
|--------|------|
| Images | Segment order me lagti hain (1st = segment 1). Chhoote segment ke liye AI image. |
| Voice (mp3) | Per-segment, order me. Jo do uske liye TTS skip, baaki gTTS. |
| Background music | Poore video ke neeche low volume par. |

## config.py — main settings

| Setting | Kya karta hai |
|---------|---------------|
| `TOPIC` | Short ka subject (e.g. "Lionel Messi at the World Cup") |
| `MODE`  | `facts` / `player` / `preview` |
| `NUM_SEGMENTS` | Kitne parts (5-6 = ~30-40 sec) |
| `VOICE_PROVIDER` | `edge` (free + **natural**, default) · `gtts` (free robotic) · `sarvam`/`elevenlabs` (key chahiye) |
| `EDGE_VOICE` | `hi-IN-SwaraNeural` (female) / `hi-IN-MadhurNeural` (male) |
| `BGM_PATH` | `assets/bgm.mp3` rakho to background music lag jaayega |

## Pipeline (sab FREE)

```
script.py  → Pollinations LLM (no key)      → Hindi narration + English subs + image keywords
voice.py   → gTTS Hindi (no key)            → per-segment voiceover (subtitle perfectly synced)
media.py   → Wikimedia (real) + Pollinations FLUX (AI)  → 9:16 images
video.py   → moviepy Ken Burns + subtitles  → output/short.mp4 (1080x1920, 30fps)
```

## ⚠️ Zaroori baatein

- **Fact-check karo!** Free LLM kabhi-kabhi galat numbers de deta hai
  (e.g. "80 matches" — actually 2026 me 104 matches hain). Post karne se pehle
  `output/script.json` ek baar padh lo.
- **Voice quality**: gTTS thodi robotic hai. Sarvam/ElevenLabs key recharge
  karke `config.py` me `VOICE_PROVIDER` badal do — natural Hindi voice mil jaayegi.
- **Real player photos**: Wikimedia se aate hain. Behtar quality ke liye
  free Pexels API key `.env` me `PEXELS_API_KEY=...` daal do aur
  `config.REAL_IMAGE_SOURCE = "pexels"` set karo.
- **YouTube upload**: `youtube_upload.py` purana (kids) wala hai — football
  ke liye title/tags update karne padenge. Abhi disabled hai.

## Naya short banane ka tareeqa

`config.py` me bas `TOPIC` change karo aur dubara `main.py` chala do.
Har run `output/` folder fresh bana deta hai.
