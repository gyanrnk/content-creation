# 📅 Kal ka Plan — Football Shorts (set: 2026-07-08)

## ✅ Jo READY hai (system complete)
- **Voice+script formula:** Groq (English) → Google Translate → Hindi, **naam Latin me** (Cristiano
  Ronaldo/Spain/World Cup), Remy voice. Clean + natural.
- **4 content formats:** facts, quiz (Pehchaan Kaun), debate (X vs Y), ranking (Top 5), story (journey).
  Auto-pilot inhe rotate karta hai + **matched topic** deta hai (ranking→"Top 5 X", debate→"X vs Y").
- **Views mechanics (har video):** frame-1 hook, loop-ending, specific comment-bait, no invented quotes.
- **Factual accuracy:** facts-mode ab real news se baandha (invented match nahi).
- **Image fixes:** "Ronaldo"→Cristiano (Brazil-Ronaldo bug gaya), statue/junk skip, cross-video dedup OK.
- **Automation:** n8n workflow (Daily 9AM → Build → Email) + server.py API. Email set (gyana.gk@gmail.com).
- **Upload:** manual/review (semi-auto) — `upload_youtube.py` + app button ready.

## 🎯 Kal karne ka (order)
1. **Voice pick:** `output\vtest_1..5` sun ke ek chuno (Remy/Brian/Andrew/Madhur/Swara). Bata dena → lock.
   - Chaho to **Google Cloud TTS (hi-IN Neural2)** — free tier, sabse natural Hindi. Setup 10 min.
2. **Fresh test batch:** `env\Scripts\python.exe auto.py 4` — sab naye fixes ke saath (matched topics +
   entertainment + Latin names). 4 videos ~50 min (CPU). Review karo.
3. **Best videos upload** karo (unlisted → check → public).
4. **n8n Active** karo (toggle ON) → roz 9 baje khud chalega. `"n"` badal ke 1-3/din set karo.

## 📈 Views strategy (LOCKED — research-backed)
- **Content mix:** ~40% facts · 25% story · 20% ranking/debate · 15% timely. (auto rotation isi taraf)
- **Har video:** killer 2-sec hook, loop-back ending, 1 specific comment-bait sawaal.
- **Length:** short (20-35s) loop better; A/B test short vs medium (build karna baaki).
- **Post:** 1-2/din, ~4:30-5:30 PM IST (peak 7-11 PM). Consistency > burst.
- **Engagement:** pehle 2 ghante me comments ka reply.
- **Cross-post:** clean file (NO watermark), har platform ka native export.
- **Monetization safe:** har video unique angle (mass-duplicate = demonetize), no match footage, verify facts.

## ⏳ Pending / decisions
- [ ] Voice pick (1-5) ya Google Cloud TTS?
- [ ] A/B length (short vs medium) system banana
- [ ] Fancy visuals v2 (blur-reveal quiz, split-screen debate, countdown cards)
- [ ] Ranking rare rank-skip + "David Beckham" latin (minor)

## ▶️ Daily run (yaad rakhna)
1. `env\Scripts\python.exe server.py` chalu rakho (ya Task Scheduler se auto-start)
2. n8n **Active** ho → 9 baje auto build → email aayega
3. Email pe: video review → upload. PC ON + internet chahiye.
