# ☁️ Oracle Cloud Always Free VM — 24/7 Shorts Server

Ek **asli always-on Linux server** (free forever). Linux cron = **reliable/punctual** (GitHub
jaisा flaky nahi). Poora pipeline wahi chalega + per-video email (video attached).

## Part 1 — VM banao (TUMHARA part, ~20-30 min)

### 1. Oracle Cloud account
- [cloud.oracle.com](https://cloud.oracle.com) → **Start for free**
- Email + phone + **card** (sirf identity verify — **Always Free pe charge NAHI hota**)
- Home region soch ke chuno (jahan tum ho, e.g. India-Mumbai/Hyderabad) — baad me badalna mushkil

### 2. VM (Ampere ARM — powerful free wala) launch karo
- Console → **Menu → Compute → Instances → Create Instance**
- Name: `shorts-server`
- Image: **Ubuntu 22.04** (Canonical Ubuntu)
- Shape: **Change shape → Ampere → VM.Standard.A1.Flex** → **2 OCPU, 12 GB RAM**
  (Always Free me 4 OCPU/24GB tak free; render ke liye 2/12 kaafi)
  - ⚠️ "Out of capacity" aaye to doosra region/AD try karo ya thodी der baad (ARM popular hai)
- **SSH keys:** "Generate a key pair for me" → **Download PRIVATE key** (`.key` file — sambhaal ke rakho!)
- **Create**
- Ban-ne ke baad **Public IP address** note karo

### 3. Networking — kuch nahi chahiye
- (Hamein koi inbound port nahi chahiye — sirf outbound. Default theek hai.)

## Part 2 — Server set karo (MERA part — main karta hoon)
VM ban jaaye + tumhare paas **Public IP + private key file** ho, to mujhe do:
- VM ka **Public IP**
- Private key file ka **path** (jaha tumne download kiya, e.g. `C:\Users\...\Downloads\ssh-key.key`)

Phir main tumhare PC se **SSH karke** ye sab kar dunga (`setup_vm.sh` se):
- python + ffmpeg + Hindi fonts install
- repo clone + deps
- **cron** (10:40-14:40 IST, reliable)
- `.env` me keys (GROQ/PEXELS/MAIL — jo already hain)

### Manual chahiye to (tum khud):
```
# PC se VM me SSH:
ssh -i "C:\path\to\ssh-key.key" ubuntu@<VM-PUBLIC-IP>
# VM ke andar:
curl -sL https://raw.githubusercontent.com/gyanrnk/content-creation/main/setup_vm.sh | bash
nano ~/shorts/.env      # keys bharo
cd ~/shorts && venv/bin/python auto.py 1   # test
```

## Kya milega
- **Reliable 24/7** — Linux cron exact time pe (GitHub jaisा late/skip nahi)
- Roz 5 shorts + **per-video email (video attached)** — GitHub download ki zaroorat nahi
- Videos VM pe `~/shorts/output/auto/` me + email me
- Free forever (Always Free tier)

## Meanwhile
GitHub Actions abhi bhi chalu hai (backup) — VM ready hone tak use karo, phir GitHub band kar denge.

## Caveats (honest)
- Oracle signup pe **card** chahiye (verify only, no charge) — kuch cards/regions pe finicky
- **ARM "out of capacity"** — popular hai, thodी retry/region-change lag sakti
- VM ON rehta hai 24/7 (Always Free — free), bas Oracle account active rakhna (login kabhi-kabhi)
