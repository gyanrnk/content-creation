"""
voice.py — Hindi voiceover generator (per-segment).

Har segment ka alag MP3/WAV banta hai. Isse subtitle aur image ka timing
audio ke saath PERFECTLY sync ho jaata hai (kyunki har segment ki exact
duration pata hoti hai).

Providers:
  - "sarvam"     → best Hindi quality (Indian model)  [default]
  - "elevenlabs" → high quality multilingual
  - "gtts"       → free fallback (Google TTS)
"""

import os
import base64
import requests
from dotenv import load_dotenv

import config

load_dotenv()


# ── Edge-TTS (free, natural, no key — DEFAULT) ───────────────────────────────────
def _edge(text: str, out_path: str) -> bool:
    try:
        import asyncio
        import edge_tts

        async def _go():
            rate = getattr(config, "EDGE_RATE", "+0%")
            pitch = getattr(config, "EDGE_PITCH", "+0Hz")
            comm = edge_tts.Communicate(text, config.EDGE_VOICE,
                                        rate=rate, pitch=pitch)
            await comm.save(out_path)

        asyncio.run(_go())
        return os.path.exists(out_path) and os.path.getsize(out_path) > 0
    except Exception as e:
        print(f"[voice] Edge-TTS failed ({e}) — falling back to gTTS.")
        return False


# ── Sarvam AI (best Hindi) ──────────────────────────────────────────────────────
def _sarvam(text: str, out_path: str) -> bool:
    key = os.getenv("SARVAM_API_KEY")
    if not key:
        return False
    try:
        r = requests.post(
            "https://api.sarvam.ai/text-to-speech",
            headers={"api-subscription-key": key,
                     "Content-Type": "application/json"},
            json={
                "text": text,
                "target_language_code": "hi-IN",
                "speaker": config.SARVAM_SPEAKER,
                "model": "bulbul:v2",
                "pace": config.SARVAM_PACE,
                "speech_sample_rate": 22050,
                "enable_preprocessing": True,
            },
            timeout=90,
        )
        r.raise_for_status()
        audio_b64 = r.json()["audios"][0]
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(audio_b64))
        return True
    except Exception as e:
        print(f"[voice] Sarvam failed ({e}) — falling back to gTTS.")
        return False


# ── ElevenLabs ──────────────────────────────────────────────────────────────────
def _elevenlabs(text: str, out_path: str) -> bool:
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        return False
    try:
        vid = config.ELEVENLABS_VOICE_ID
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={"text": text, "model_id": "eleven_multilingual_v2",
                  "voice_settings": {"stability": 0.4, "similarity_boost": 0.75}},
            timeout=90,
        )
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"[voice] ElevenLabs failed ({e}) — falling back to gTTS.")
        return False


# ── gTTS (free fallback) ────────────────────────────────────────────────────────
def _gtts(text: str, out_path: str) -> bool:
    try:
        from gtts import gTTS
        gTTS(text=text, lang="hi", slow=False).save(out_path)
        return True
    except Exception as e:
        print(f"[voice] gTTS failed: {e}")
        return False


def generate_segment_voices(segments: list[dict],
                            user_audio: list[str] = None) -> list[str]:
    """
    Har segment ke Hindi text se ek audio file banata hai.

    user_audio: optional — user ki apni per-segment voice files (order me).
    Jo segment cover ho jaate hain unke liye wahi use hoti hai; baaki TTS se.

    Returns: list of audio file paths (segment order me).
    """
    import shutil
    audio_dir = os.path.join(config.OUTPUT_DIR, "audio")
    os.makedirs(audio_dir, exist_ok=True)

    user_audio = user_audio or []
    provider = config.VOICE_PROVIDER
    paths = []

    for i, seg in enumerate(segments):
        out = os.path.join(audio_dir, f"seg_{i:02d}.mp3")

        # User ne apni voice di hai? -> wahi use karo
        if i < len(user_audio) and user_audio[i]:
            try:
                shutil.copy(user_audio[i], out)
                print(f"[voice] Segment {i+1}/{len(segments)} -> USER audio")
                paths.append(out)
                continue
            except Exception as e:
                print(f"[voice] Segment {i+1}: user audio failed ({e}) -> TTS")

        text = seg.get("voice_hindi", "").strip()
        if not text:
            text = "..."

        ok, used = False, provider
        if provider == "edge":
            ok = _edge(text, out)
        elif provider == "sarvam":
            ok = _sarvam(text, out)
        elif provider == "elevenlabs":
            ok = _elevenlabs(text, out)

        if not ok:
            used = "gtts (FALLBACK — robotic!)"
            ok = _gtts(text, out)   # universal fallback

        if not ok:
            raise RuntimeError(f"Voice generation failed for segment {i+1}")

        print(f"[voice] Segment {i+1}/{len(segments)} -> {out}  [via {used}]")
        paths.append(out)

    return paths


if __name__ == "__main__":
    demo = [{"voice_hindi": "क्या आप जानते हैं? यह वर्ल्ड कप इतिहास का सबसे बड़ा है!"}]
    print(generate_segment_voices(demo))
