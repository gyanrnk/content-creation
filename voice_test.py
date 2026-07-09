"""
voice_test.py — Voice samples banata hai taaki bina full render ke voice sun sako.

Run:  env\\Scripts\\python.exe voice_test.py
Phir output/ me voice_male.mp3 aur voice_female.mp3 play karke decide karo.
"""
import os
import sys
import asyncio
import edge_tts

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import config

TEXT = ("सर्जियो रामोस का बड़ा दावा सामने आया है। "
        "क्या मेसी विश्व कप जीतकर सबसे महान बन जाएंगे? "
        "करियर या वर्ल्ड कप, आपका क्या विचार है?")

os.makedirs("output", exist_ok=True)


async def gen(voice, rate, out):
    await edge_tts.Communicate(TEXT, voice, rate=rate).save(out)


for label, voice in [("male", "hi-IN-MadhurNeural"),
                     ("female", "hi-IN-SwaraNeural")]:
    out = f"output/voice_{label}.mp3"
    try:
        asyncio.run(gen(voice, config.EDGE_RATE, out))
        print(f"[{label}] {voice} @ {config.EDGE_RATE} -> {out}  "
              f"({os.path.getsize(out)} bytes)")
    except Exception as e:
        print(f"[{label}] FAILED: {e}")

print("\nDono play karke batao kaunsi behtar — config.py me EDGE_VOICE set kar denge.")
