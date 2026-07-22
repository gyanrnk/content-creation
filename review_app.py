"""
review_app.py — MOBILE se script review/approve karne ka chhota Streamlit app.

Kyun alag app: app.py bhaari hai (video banata hai). Ye sirf REVIEW ke liye —
phone pe khulta hai, script padho, edit karo, approve karo. Approved script
GitHub pe wapas likhi jaati hai -> cron use uthake video banata aur publish karta.

Chalane ke 2 tareeke:
  LOCAL :  env\\Scripts\\python.exe -m streamlit run review_app.py
           (data/*.json seedha padhta/likhta hai)
  CLOUD :  Streamlit Community Cloud (FREE) pe deploy -> phone se khulega.
           Wahan filesystem temporary hai, isliye GitHub API se padhta/likhta hai.

Streamlit Cloud secrets (Settings -> Secrets):
    APP_PASSWORD = "koi-password"
    GITHUB_TOKEN = "ghp_..."          # fine-grained PAT, is repo pe Contents: Read+Write
    GITHUB_REPO  = "gyanrnk/content-creation"
"""

import os
import json
import base64

import streamlit as st
import requests

PENDING_PATH = "data/pending_scripts.json"
QUEUE_PATH = "data/script_queue.json"
API = "https://api.github.com"


# ── secrets (Streamlit Cloud ya local env dono se) ─────────────────────────────
def _sec(key: str, default: str = "") -> str:
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)


TOKEN = _sec("GITHUB_TOKEN")
REPO = _sec("GITHUB_REPO", "gyanrnk/content-creation")
PASSWORD = _sec("APP_PASSWORD")
USE_GH = bool(TOKEN)          # token hai = cloud mode (GitHub pe padho/likho)


# ── data layer: GitHub API ya local file ───────────────────────────────────────
def _gh_get(path: str):
    """(list, sha) — file GitHub se padho."""
    r = requests.get(f"{API}/repos/{REPO}/contents/{path}",
                     headers={"Authorization": f"Bearer {TOKEN}",
                              "Accept": "application/vnd.github+json"}, timeout=25)
    if r.status_code == 404:
        return [], None
    r.raise_for_status()
    j = r.json()
    try:
        data = json.loads(base64.b64decode(j["content"]).decode("utf-8"))
    except Exception:
        data = []
    return (data if isinstance(data, list) else []), j.get("sha")


def _gh_put(path: str, items: list, sha, msg: str):
    body = {"message": msg,
            "content": base64.b64encode(
                json.dumps(items, ensure_ascii=False, indent=1).encode()).decode()}
    if sha:
        body["sha"] = sha
    r = requests.put(f"{API}/repos/{REPO}/contents/{path}",
                     headers={"Authorization": f"Bearer {TOKEN}",
                              "Accept": "application/vnd.github+json"},
                     json=body, timeout=25)
    r.raise_for_status()


def load(path: str):
    if USE_GH:
        return _gh_get(path)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except Exception:
        return [], None


def save(path: str, items: list, sha, msg: str):
    if USE_GH:
        _gh_put(path, items, sha, msg)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)


# ── UI ─────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Footy Gyaan — Script Review", page_icon="⚽",
                   layout="centered", initial_sidebar_state="collapsed")

# Mode ke liye badge (rang + emoji) — ek nazar me pata chale kaunsa format hai
MODE_STYLE = {
    "story":   ("📖", "#7c3aed"), "facts":  ("⚡", "#0ea5e9"),
    "pundit":  ("🎙️", "#f59e0b"), "stats":  ("📊", "#10b981"),
    "ranking": ("🏆", "#ef4444"), "quiz":   ("❓", "#ec4899"),
    "debate":  ("🔥", "#f97316"),
}

st.markdown("""
<style>
  .block-container {padding-top: 1.8rem; max-width: 780px;}
  /* header */
  .fg-hero {background: linear-gradient(120deg,#065f46 0%,#064e3b 55%,#0f172a 100%);
            padding: 20px 22px; border-radius: 16px; margin-bottom: 14px;
            border: 1px solid rgba(255,255,255,.08);}
  .fg-hero h1 {margin:0; font-size:1.55rem; color:#fff; letter-spacing:.3px;}
  .fg-hero p  {margin:.35rem 0 0; color:#a7f3d0; font-size:.86rem;}
  /* stat pills */
  .fg-stats {display:flex; gap:10px; margin:2px 0 16px;}
  .fg-pill {flex:1; background:#111827; border:1px solid #1f2937; border-radius:12px;
            padding:12px 14px;}
  .fg-pill .n {font-size:1.7rem; font-weight:700; line-height:1; color:#f9fafb;}
  .fg-pill .l {font-size:.74rem; color:#9ca3af; text-transform:uppercase;
               letter-spacing:.6px; margin-top:4px;}
  /* stock pill rang badalti he taaki khali hone se PEHLE dikh jaaye */
  .fg-pill.ok   {border-color:#14532d; background:#0c1a12;}
  .fg-pill.ok   .n {color:#4ade80;}
  .fg-pill.warn {border-color:#78350f; background:#1a1206;}
  .fg-pill.warn .n {color:#fbbf24;}
  .fg-pill.bad  {border-color:#7f1d1d; background:#1a0c0c;}
  .fg-pill.bad  .n {color:#f87171;}
  /* script card */
  .fg-card {background:#0b1220; border:1px solid #1f2937; border-left:4px solid var(--ac);
            border-radius:14px; padding:14px 16px; margin:6px 0 10px;}
  .fg-badge {display:inline-block; background:var(--ac); color:#fff; font-size:.7rem;
             font-weight:700; padding:3px 10px; border-radius:999px;
             text-transform:uppercase; letter-spacing:.5px;}
  .fg-title {font-size:1.05rem; font-weight:700; color:#f3f4f6; margin:8px 0 2px;}
  .fg-meta {font-size:.76rem; color:#9ca3af;}
  .stTextArea textarea, .stTextInput input {font-size:.92rem !important;}
  div[data-testid="stExpander"] {border:none !important;}
</style>
""", unsafe_allow_html=True)

if PASSWORD:
    if not st.session_state.get("ok"):
        st.markdown('<div class="fg-hero"><h1>⚽ Footy Gyaan</h1>'
                    '<p>Script review — login karo</p></div>', unsafe_allow_html=True)
        pw = st.text_input("Password", type="password", label_visibility="collapsed",
                           placeholder="Password daalo")
        if st.button("Login →", use_container_width=True, type="primary"):
            if pw == PASSWORD:
                st.session_state["ok"] = True
                st.rerun()
            else:
                st.error("Galat password")
        st.stop()

pending, p_sha = load(PENDING_PATH)
queue, _ = load(QUEUE_PATH)

st.markdown(
    f'<div class="fg-hero"><h1>⚽ Script Review</h1>'
    f'<p>{"☁️ GitHub se juda" if USE_GH else "💻 Local mode"} · approve karte hi '
    f'cron us script se video bana dega</p></div>', unsafe_allow_html=True)

# BUG jo fix hua: "Din ka stock" bhi len(queue) hi dikha raha tha — yaani "Approved
# queue" ki nakal. 7 script dikhte the aur lagta tha 7 DIN ka stock he, jabki 6 video
# roz jaate he to wo sirf ~1 din ka he. Ab asli din nikaalte he.
UPLOADS_PER_DAY = 6
days = len(queue) / UPLOADS_PER_DAY
d_cls = "bad" if days < 1 else ("warn" if days < 2 else "ok")
d_txt = f"{days:.1f}"
st.markdown(
    f'<div class="fg-stats">'
    f'<div class="fg-pill"><div class="n">{len(pending)}</div>'
    f'<div class="l">📝 Review baaki</div></div>'
    f'<div class="fg-pill"><div class="n">{len(queue)}</div>'
    f'<div class="l">✅ Approved queue</div></div>'
    f'<div class="fg-pill {d_cls}"><div class="n">{d_txt}</div>'
    f'<div class="l">🎬 Din ka stock</div></div>'
    f'</div>', unsafe_allow_html=True)

if days < 1:
    st.warning(f"⚠️ Stock kam hai — {len(queue)} script bache hain, roz {UPLOADS_PER_DAY} "
               f"video jaate hain. Aaj hi khatam ho jayega. Claude se bolo: "
               f"*'naye script banao'*")

if st.button("🔄 Refresh", use_container_width=True):
    st.rerun()

if not pending:
    st.success("🎉 Sab review ho gaya! Naye chahiye to Claude se bolo: "
               "*'naye script banao'*")
    if queue:
        st.caption(f"Queue me {len(queue)} script hai — cron inse videos banata rahega.")
    st.stop()

for idx, item in enumerate(pending):
    data = item.get("data", {}) or {}
    segs = data.get("segments", []) or []
    # BUG FIX: widget keys INDEX se nahi, script ki apni STHIR id se. Index se banane
    # par ek script approve karte hi baaki list khisak jaati thi aur Streamlit purane
    # index ki value dikhata tha (header kuch, fields kuch aur).
    uid = str(item.get("id") or abs(hash(
        (item.get("topic", ""), data.get("youtube_title", ""),
         (segs[0].get("voice_english", "") if segs else "")))))
    mode = item.get("mode", "facts")
    emoji, color = MODE_STYLE.get(mode, ("⚽", "#64748b"))
    words = sum(len((s.get("voice_english") or "").split()) for s in segs)
    # ~3.2 words/sec (voice +50%) + har segment ke baad saans + CTA card
    est = words / 3.2 + len(segs) * 0.35 + 7

    st.markdown(
        f'<div class="fg-card" style="--ac:{color}">'
        f'<span class="fg-badge">{emoji} {mode}</span>'
        f'<div class="fg-title">{data.get("youtube_title", item.get("topic",""))}</div>'
        f'<div class="fg-meta">{len(segs)} lines · {words} words · ~{est:.0f}s video</div>'
        f'</div>', unsafe_allow_html=True)

    with st.expander("✏️  Edit / Approve", expanded=(idx == 0)):

        title = st.text_input("🏷️ Title (naam + hook = zyada clicks)",
                              data.get("youtube_title", ""), key=f"t_{uid}")

        st.markdown("**🎙️ Script lines** — jo yahan likhoge, **wahi TTS bolega**")
        new_lines = []
        for j, s in enumerate(segs):
            txt = s.get("voice_english", "")
            n = len(txt.split())
            # band script.py ke prompt ke sath match karna chahiye (13-16 words)
            tag = "✅" if 13 <= n <= 16 else ("⚠️ chhoti" if n < 13 else "⚠️ lambi")
            line = st.text_area(f"Line {j+1}  ·  {n} words {tag}", txt,
                                key=f"l_{uid}_{j}", height=80)
            new_lines.append(line)

        cta = st.text_input("💬 CTA (comment maangne wali line)",
                            data.get("cta_english", ""), key=f"c_{uid}")

        a, b = st.columns([2, 1])
        if a.button("✅ Approve — video banao", key=f"a_{uid}",
                    use_container_width=True, type="primary"):
            data["youtube_title"] = title
            data["cta_english"] = cta
            for j, line in enumerate(new_lines):
                if j < len(segs):
                    segs[j]["voice_english"] = line
            data["segments"] = segs
            item["data"] = data

            q, q_sha = load(QUEUE_PATH)
            q.append(item)
            save(QUEUE_PATH, q, q_sha, "approve: add script to build queue")

            rest = [p for k, p in enumerate(pending) if k != idx]
            save(PENDING_PATH, rest, p_sha, "approve: remove from pending")
            st.success("✅ Approved! Cron isse video banayega.")
            st.rerun()

        if b.button("🗑️ Reject", key=f"r_{uid}", use_container_width=True):
            rest = [p for k, p in enumerate(pending) if k != idx]
            save(PENDING_PATH, rest, p_sha, "reject: drop script")
            st.warning("🗑️ Hata diya.")
            st.rerun()
