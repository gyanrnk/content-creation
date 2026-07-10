#!/usr/bin/env bash
# ============================================================================
# setup_vm.sh — Oracle Cloud (Ubuntu ARM) pe football-shorts 24/7 server setup.
# VM ke andar SSH karke ye chalao:  bash setup_vm.sh
# (ya PC se: ssh ubuntu@<VM-IP> 'bash -s' < setup_vm.sh)
# ============================================================================
set -e
REPO="https://github.com/gyanrnk/content-creation.git"
DIR="$HOME/shorts"

echo "==> [1/6] Timezone -> IST"
sudo timedatectl set-timezone Asia/Kolkata || true

echo "==> [2/6] System deps (python, ffmpeg, Hindi fonts)"
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg git \
  fonts-noto-core fonts-lohit-deva fonts-dejavu-core

echo "==> [3/6] Repo clone/pull"
if [ -d "$DIR/.git" ]; then cd "$DIR" && git pull; else git clone "$REPO" "$DIR"; fi
cd "$DIR"

echo "==> [4/6] Python venv + deps"
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

echo "==> [5/6] CLIP off (light/fast, jaisा Actions)"
sed -i 's/^REAL_PHOTO_CLIP = True/REAL_PHOTO_CLIP = False/' config.py || true

echo "==> [6/6] .env check + cron"
if [ ! -f .env ]; then
  cat > .env <<'EOF'
GROQ_API_KEY="PASTE_HERE"
PEXELS_API_KEY=PASTE_HERE
MAIL_USERNAME=gyana.gk@gmail.com
MAIL_PASSWORD="PASTE_APP_PASSWORD"
EOF
  echo "   !! .env banaya — ISME apni keys bharo:  nano $DIR/.env"
fi

# Cron: 5 shorts, har ghanta 1 (10:40..14:40 IST). Linux cron = reliable/punctual.
CRON="PYTHONIOENCODING=utf-8
40 10 * * * cd $DIR && venv/bin/python auto.py 1 >> $DIR/cron.log 2>&1
40 11 * * * cd $DIR && venv/bin/python auto.py 1 >> $DIR/cron.log 2>&1
40 12 * * * cd $DIR && venv/bin/python auto.py 1 >> $DIR/cron.log 2>&1
40 13 * * * cd $DIR && venv/bin/python auto.py 1 >> $DIR/cron.log 2>&1
40 14 * * * cd $DIR && venv/bin/python auto.py 1 >> $DIR/cron.log 2>&1"
echo "$CRON" | crontab -
echo "   cron set (crontab -l se dekho)"

echo ""
echo "✅ DONE. Ab:"
echo "   1) .env me keys bharo:  nano $DIR/.env"
echo "   2) Test:  cd $DIR && venv/bin/python auto.py 1"
echo "   3) Video ban ke email aayega. Cron roz 10:40-14:40 IST khud chalega."
