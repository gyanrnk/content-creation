"""
config.py — Central configuration for the Football World Cup Shorts generator.

Sab settings yahin se control hoti hain. Sirf yeh file edit karo, baaki code touch
karne ki zaroorat nahi.
"""

# ── CONTENT ───────────────────────────────────────────────────────────────────

# Short ka topic / angle. Yahan apni baat likho — jaisa prompt doge waisa banega.
# Examples:
#   "5 mind-blowing facts about FIFA World Cup 2026"          (MODE="facts")
#   "Lionel Messi World Cup journey"                          (MODE="player")
#   "Brazil vs Japan upcoming match — legends comparison and who will win"  (MODE="preview")
TOPIC = "Brazil vs Japan upcoming match — compare legends and predict the winner"

# Content MODE — kaisa short banana hai:
#   "facts"    → did-you-know / trivia / records
#   "player"   → kisi player ya team par spotlight
#   "preview"  → 2 teams ke legends ka comparison + history + match prediction
# NOTE: "preview" fake scoreline predict karta hai (credibility risk). Live tournament +
# auto-pilot ke liye "facts" safe/truthful hai. Genuine upcoming match ke liye hi "preview".
MODE = "facts"

# CUSTOM SCRIPT — agar yahan apna pura script likhoge to system sirf USE BOLEGA,
# kuch add/predict nahi karega (TOPIC/MODE ignore ho jaayenge). Khaali "" = auto-generate.
# Naya short auto banana ho to ise wapas "" kar dena.
CUSTOM_SCRIPT = ""   # khali = auto/LLM script use hoga (yahan text ho to wahi override kar deta tha)

# Kitne segments. 5 = ~35-40s video = Shorts sweet-spot (completion+loop zyada) + fast render.
# (6+ lambा video ban raha tha = 57s + slow render.)
NUM_SEGMENTS = 4          # DATA (2026-07-20): 26-27s/~45 words = 1,274 views;
                          # 40-42s/~100 words = 0-29 views. Chhota JEETTA hai.

# ── VIDEO FORMAT (9:16 vertical — Shorts / Reels / FB) ─────────────────────────

WIDTH  = 1080
HEIGHT = 1920
FPS    = 24      # cinematic standard; 30 se ~20% fast render

# Ken Burns zoom factor per image (1.10 = halka, 1.30 = strong cinematic motion)
KEN_BURNS_ZOOM = 1.42   # zyada zoom-travel = zyada motion (static feel kam) — legal
FAST_CUTS = True        # har image segment 2 shots (wide->punch-in) = har ~3s ek cut

# Crossfade between segments (seconds)
CROSSFADE = 0.25

# ── CINEMATIC LOOK ─────────────────────────────────────────────────────────────

CINEMATIC_GRADE   = True    # contrast + saturation + teal-orange tint on images
VIGNETTE          = True    # dark corners (filmi look)
FILM_GRAIN        = True    # halka grain overlay
ANIMATED_CAPTIONS = True    # word-by-word pop/highlight (viral style)
STATS_OVERLAY     = True    # "6 World Cups" jaise numbers -> bada bold stat-card

# Real video footage source for atmospheric segments:
#   "none"   -> sirf AI images (Pollinations) — koi key nahi chahiye
#   "pexels" -> real action video clips (PEXELS_API_KEY .env me hai) [ACTIVE]
VIDEO_SOURCE = "pexels"
# User: JYADATAR real video CLIPS dikhao, static images minimize. True = har segment
# ke liye pehle Pexels real football clip (motion), image sirf fallback (clip na mile to).
# NOTE: Pexels clips GENERIC football hote hain (asli footage par specific player nahi —
# broadcast footage illegal). Named player ki asli photo image-fallback me hi aayegi.
PREFER_VIDEO_CLIPS = True

# Pexels video ki max height (chhoti = kam MB + fast render). 1280 = 720x1280 HD.
# 960 = aur chhoti/fast, 1920 = full HD (bada + slow).
PEXELS_MAX_HEIGHT = 1280

# Sound effects (whoosh on cuts) — numpy whoosh cheap lagta tha, isliye OFF.
# Asli energy ke liye assets/bgm.mp3 me real music daalo (neeche BGM section).
SFX_WHOOSH = False

# Hook punch — pehle frame par quick white flash (scroll-stopping snap)
HOOK_PUNCH = True

# ── VOICE (Hindi) ──────────────────────────────────────────────────────────────

# Provider: "edge" (free, no key — DEFAULT) | "gcloud" (Google Cloud TTS — natural +
#   SSML pauses; PAR billing/card mandatory hai, isliye OFF) | "sarvam" | "elevenlabs" | "gtts"
# NOTE: gcloud code available hai (voice.py) agar future me chahiye — bas VOICE_PROVIDER
# "gcloud" + GOOGLE_TTS_API_KEY. Abhi edge (Madhur) — koi card/key nahi.
VOICE_PROVIDER = "edge"

# Google Cloud TTS settings (agar kabhi "gcloud" use karo). Male: hi-IN-Neural2-B/C.
GCLOUD_VOICE = "hi-IN-Neural2-C"
GCLOUD_RATE = 1.12
GCLOUD_PITCH = 0.0

# Edge-TTS voice. Male options: fr-FR-RemyMultilingualNeural (chosen — warm male),
#   hi-IN-MadhurNeural (Hindi-native male), en-US-BrianMultilingualNeural (deep).
#   Female: hi-IN-SwaraNeural. Multilingual voices Hindi bol lete hain.
EDGE_VOICE = "hi-IN-MadhurNeural"   # USER-LOCKED (native Hindi male). Naam Devanagari me
# natural bolti (क्रिस्टियानो रोनाल्डो) — isliye native voices ke liye name-Latin jugaad OFF
# hai (dekho script.py translate loop). Remy (fr-FR) chhod diya — robotic/foreign lag raha tha.
# Voice speed: "+0%" normal, "+8%" halka fast (natural), "+15%" fast
EDGE_RATE = "+50%"   # USER-LOCKED: samples me se "H" chuna ("same waisa hi awaz chahiye").
                     # Tez pace = utne hi time me zyada content + chhoti video. Ye rate
                     # user ne KAAN se chuna hai — bina puche mat badalna.
# Voice pitch: "+0Hz" normal, "-3Hz" deeper/warmer male, "+5Hz" lighter
EDGE_PITCH = "+0Hz"

# Sarvam speaker (bulbul:v2): anushka, manisha, vidya, arya (female) | abhilash, karun, hitesh (male)
SARVAM_SPEAKER = "anushka"
SARVAM_PACE    = 1.05      # 1.0 normal; >1 = thoda fast (shorts ke liye accha)

# ElevenLabs voice id (sirf agar VOICE_PROVIDER="elevenlabs")
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# ── SCRIPT GENERATION ──────────────────────────────────────────────────────────

# "groq" (BEST quality, FREE tier — needs valid GROQ_API_KEY in .env) | "pollinations"
# (FREE, no key, lower quality) | "openai".
# NOTE: script.py me smart fallback hai — groq fail/dead-key ho to apne aap
# Pollinations pe gir jaata hai. To 'groq' safe default hai: valid key = behtar
# quality, warna free Pollinations se kaam chalta rehta hai.
SCRIPT_PROVIDER = "groq"
# GEMINI_API_KEY (.env / GitHub secret) ho to Gemini AUTO primary ban jaata hai
# (behtar quality), Groq/Pollinations fallback rehte. Key na ho to sab pehle jaisa.
GEMINI_MODEL = "gemini-flash-latest"
# Free quota HAR MODEL ka alag hota hai (PerProjectPerModel) -> chain: ek ka din ka
# quota khatam (429) to agla. ~5x free capacity. Sab khatam -> Groq fallback.
GEMINI_MODELS = [
    "gemini-flash-latest",        # best quality
    "gemini-flash-lite-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
]

# ── IMAGES ─────────────────────────────────────────────────────────────────────

# Real photos source: "wikimedia" (free, no key) | "pexels" (needs PEXELS_API_KEY in .env)
REAL_IMAGE_SOURCE = "wikimedia"

# REAL images jyada rakho — atmospheric segments par bhi pehle REAL football photo
# (Openverse/Wikimedia, free no-key) try karo, na mile to AI. True = zyada real.
PREFER_REAL_IMAGES = True

# REAL PHOTO LAYER — named player/team segments ke liye Wikidata P18 + Wikipedia +
# Commons se ASLI photo laao (CC/PD, monetization-safe). CLIP se sentence ke liye
# best match pick. True = "sachai" wali real photos.
USE_REAL_PHOTO_LAYER = True
REAL_PHOTO_CLIP = True   # False = pehla candidate (fast), True = CLIP best-match (accurate)
# News date (optional) — "2012" ya "2012-06-15". Diya to us DATE/ERA ke aas-paas ki
# real photo prefer hogi (young Messi vs current Messi). Khaali = latest/best photo.
NEWS_DATE = ""
# News grounding: script LLM ko aaj ki REAL headlines feed karo taaki wo current
# reality ke against kuch na bole (e.g. eliminated player ko "2026 GOAT banega" na kahe).
# Live tournament me ZAROORI. False = grounding off (evergreen topics ke liye theek).
USE_NEWS_CONTEXT = True
# Attribution: in-video credits card viewing kharaab karta hai -> OFF.
# Credits phir bhi output/credits.txt + description me jaate hain (CC-BY legally safe).
SHOW_CREDITS_CARD = False

# ── SAFE MODE (monetization / copyright) ───────────────────────────────────────
# True  -> sirf AI (Pollinations, no copyright owner) + Pexels (clear license).
#          Openverse/Wikimedia real-player CC photos OFF (license uncertain = risk).
#          Monetized content ke liye SABSE SAFE. Players AI-generated dikhenge.
# False -> real+AI mix (zyada engaging). NOTE: real photos ka copyright/license
#          risk hai monetized content me — apne risk pe. Best: Pexels key add karo.
SAFE_MODE = False

# AI image model via Pollinations (free, no GPU): "flux" | "turbo"
AI_IMAGE_MODEL = "flux"

# ── MEDIA LIBRARY (tumhare apne free clips/images ka folder) ────────────────────
# assets/library/ me jo bhi .mp4/.jpg/.png daaloge, wo RANDOM use honge
# atmospheric segments me. Free clips Pexels/Pixabay/Mixkit/Coverr se download
# karke yahan daalo -> har video me alag + real footage + no repeat.
USE_LIBRARY = True
LIBRARY_DIR = "assets/library"

# ── SUBTITLES (English) ────────────────────────────────────────────────────────

SUBTITLE_FONT_SIZE = 72        # bada = punchy (auto-shrink hoga agar fit na ho)
SUBTITLE_SIDE_MARGIN = 70      # left/right safe margin (px) — text kabhi edge se nahi katega

# ── BACKGROUND MUSIC (optional) ────────────────────────────────────────────────

# Royalty-free upbeat track (pixabay.com/music). None = no BGM.
BGM_PATH    = "assets/bgm.mp3"
BGM_VOLUME  = 0.12

# ── BRANDING (har video par) ───────────────────────────────────────────────────

SHOW_WATERMARK = True
BRAND_NAME     = "Footy Gyaan"      # corner watermark text (asli channel naam)
BRAND_HANDLE   = "@FootyGyaan"      # handle (subscribe identity)
LOGO_PATH      = "assets/logo.png"  # optional — file ho to top par overlay hoga

# ── THUMBNAIL (YouTube 16:9) ───────────────────────────────────────────────────

MAKE_THUMBNAIL = True
THUMB_WIDTH    = 1280
THUMB_HEIGHT   = 720

# ── OUTPUT ─────────────────────────────────────────────────────────────────────

OUTPUT_DIR  = "output"
FINAL_VIDEO = "output/short.mp4"

# Script review UI (mobile) — make_scripts.py email me ye link bhejta hai
REVIEW_APP_URL = "https://content-creation-uvx2gfn2ovncvozavhwjdc.streamlit.app"
