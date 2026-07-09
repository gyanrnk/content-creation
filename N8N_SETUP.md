# n8n Automation — Football Shorts

Ye setup roz apne aap short banata hai, tumhe notify karta hai, phir tum review karke
upload karte ho. (Fully-auto upload nahi — free-LLM kabhi fact galat karta hai, isliye
review zaroori.)

## Architecture (kaise kaam karta hai)
```
n8n (scheduler + notify + upload trigger)
        │  HTTP
        ▼
server.py  (http://localhost:8000)  ← ye tumhare PC pe chalta hai
        │  calls
        ▼
auto.py → script(Groq→translate) → voice(Remy) → media → render → output/auto/<date>/
```
n8n sirf "boss" hai; asli kaam `server.py` + pipeline karta hai. Isliye n8n local ya
Docker — dono chalega.

---

## Step 1 — API server chalao (ek baar, background me)
```
cd "C:\Users\Gyanaranjan kabi\Desktop\content-creation"
env\Scripts\python.exe server.py
```
`http://localhost:8000` pe chalega. Test:
```
curl http://localhost:8000/health      →  {"ok": true}
```
(PC restart pe dobara chalana padega — ya Task Scheduler se auto-start kar sakte ho.)

## Step 2 — n8n install + chalao
Sabse aasaan (Node.js hai to):
```
npx n8n
```
→ browser me `http://localhost:5678` khulega.

**Ya Docker se:**
```
docker run -it --rm -p 5678:5678 -v n8n_data:/home/node/.n8n docker.n8n.io/n8nio/n8n
```

## Step 3 — workflow import karo
n8n me: **Workflows → ⋯ (top right) → Import from File** → `n8n_workflow.json` chuno.

Isme 4 node hain: **Daily 9AM → Build Short → Format Message → (notify placeholder)**.

### ⚠️ URL theek karo (zaroori)
`Build Short` node me URL:
- **n8n `npx` se (same PC pe)** chala rahe ho → URL: `http://127.0.0.1:8000/build`
  (⚠️ `localhost` mat use karo — Node.js `localhost` ko IPv6 `::1` pe try karta hai aur
   "connection refused" deta hai; `127.0.0.1` = IPv4 force, ye chalta hai. Default isi pe set hai.)
- **n8n Docker me** hai → URL: `http://host.docker.internal:8000/build`
  - Linux Docker pe `host.docker.internal` na chale to apne PC ka LAN IP daalo (e.g. `http://192.168.1.5:8000/build`)

## Step 4 — schedule set karo
`Daily 9AM` node me cron `0 9 * * *` = roz subah 9 baje. Apne hisab se badlo
(e.g. `0 18 * * *` = shaam 6 baje). Kitne shorts: `Build Short` node ke body me `"n": 1`
ko `2`/`3` kar do.

## Step 5 — notification lagao (optional, recommended)
Aakhri "→ Telegram/Email/Slack" node ko delete karke apna notifier lagao:
- **Telegram**: Telegram node → "Send Message" → text: `={{$json.message}}` (Format Message se)
- **Email**: Send Email node → body `={{$json.message}}`
- Isse tumhe roz message aayega: "1 short ready, folder X, review karo".

## Step 6 — review + upload
Message aane pe:
1. `output\auto\<date>\01_...\short.mp4` dekho (facts sahi hain? — free-LLM check).
2. Sahi lage to upload:
   - **App se**: streamlit me ⬆️ Upload button, YA
   - **n8n se**: ek naya "Manual Trigger → HTTP Request" workflow banao jo
     `POST http://localhost:8000/upload` body `{"dir":"output/auto/<date>/01_...","privacy":"unlisted"}`
     bheje. (Pehle `python upload_youtube.py auth` — personal Gmail se.)

---

## Endpoints (server.py) — reference
| Method | Path | Body | Kaam |
|--------|------|------|------|
| GET | `/health` | — | server zinda hai? |
| POST | `/build` | `{"n":1,"topic":""}` | shorts banao (sync, ~6min/video) |
| GET | `/latest` | — | pichhle build ka summary |
| POST | `/upload` | `{"dir":"...","privacy":"unlisted"}` | YouTube upload (token.json chahiye) |

---

## 📧 Email notification setup (Gmail)
Workflow me ab `Email Me` node hai. Isse chalane ke liye Gmail SMTP credential chahiye:

1. **Gmail App Password banao** (normal password kaam nahi karega):
   - Google Account → **Security** → **2-Step Verification** ON karo (zaroori)
   - Phir **Security → App passwords** → app "Mail" → **Generate** → 16-char password copy karo
2. **n8n me credential banao**: Credentials → **New** → **SMTP** →
   - Host: `smtp.gmail.com`
   - Port: `465`  (SSL ON)  — ya `587` (TLS)
   - User: `tumhari@gmail.com`
   - Password: **App Password** (jo abhi banaya, normal Gmail password nahi)
3. Workflow ke **`Email Me` node** me:
   - Credential: upar wala SMTP select karo
   - `From Email` aur `To Email`: apni email daalo (`YOUR_EMAIL@gmail.com` ki jagah)
4. **Test**: node pe **"Execute step"** dabao → tumhari inbox me test mail aani chahiye.

Har build ke baad tumhe mail aayega: "Football Short ready — review karo" + folder path.

---

## 🔎 n8n check/monitor kaise karein (chal raha hai ki nahi)

**1. Workflow ACTIVE hai?**
- Workflow khol ke top-right **"Active" toggle ON** karo. Active = schedule (9AM) khud chalega.
- Toggle OFF = sirf manual chalega, schedule nahi.

**2. Abhi turant test karo (9AM ka wait mat karo):**
- Workflow me **"Test workflow"** (ya "Execute Workflow") button dabao → poora flow abhi chalega.
- Har node pe green ✓ = pass, red = fail. Node pe click karke uska output/error dekho.

**3. History — kab kab chala, pass/fail:**
- Left menu → **Executions** → har run dikhta hai (time, Success/Error, duration).
- Kisi run pe click → node-by-node kya hua, error kya tha — sab dikhता hai.

**4. Server (server.py) chal raha hai?** (n8n isi pe depend karta hai)
- Browser me kholo: `http://localhost:8000/health` → `{"ok": true}` aana chahiye.
- Ya server wali terminal window dekho — har request pe `[server] ...` log aata hai.
- `http://localhost:8000/latest` → pichhle build ka summary (kab, kitne bane).

**5. Common problems:**
| Dikh raha | Matlab | Fix |
|-----------|--------|-----|
| Build node "connection refused" | server.py band hai | `python server.py` chalao |
| Build node timeout | video 6min+ le raha | node timeout badhao (already 30min) |
| Email node fail | SMTP/App-password galat | App Password dobara, port 465 |
| Schedule fire nahi hua | workflow Active nahi | Active toggle ON |
| 409 "build already running" | pichhla build chal raha | ek khatam hone do |

## Zaroori baatein
- **PC ON + internet** hona chahiye jab schedule chale.
- Build **~6 min/video (CPU)** — isliye n8n HTTP node ka **timeout 1800000ms** set hai.
- **Upload manual/review ke baad** — fully-auto publish risky (fact errors).
- Ek time pe ek hi build (server lock karta hai; busy ho to 409 deta hai).
