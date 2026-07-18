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
                   layout="centered")

if PASSWORD:
    if not st.session_state.get("ok"):
        st.title("⚽ Footy Gyaan — Review")
        pw = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if pw == PASSWORD:
                st.session_state["ok"] = True
                st.rerun()
            else:
                st.error("Galat password")
        st.stop()

st.title("⚽ Script Review")
st.caption(f"{'☁️ GitHub mode' if USE_GH else '💻 Local mode'} — approve karo, phir "
           "cron us script se video banayega")

pending, p_sha = load(PENDING_PATH)
queue, _ = load(QUEUE_PATH)

c1, c2 = st.columns(2)
c1.metric("Review baaki", len(pending))
c2.metric("Approved queue", len(queue))

if st.button("🔄 Refresh", use_container_width=True):
    st.rerun()

if not pending:
    st.success("Koi script review ke liye nahi. Claude se bolo: *'naye script banao'*")
    st.stop()

st.divider()

for idx, item in enumerate(pending):
    data = item.get("data", {}) or {}
    segs = data.get("segments", []) or []
    with st.expander(
            f"#{idx+1}  [{item.get('mode')}]  {data.get('youtube_title', item.get('topic'))[:60]}",
            expanded=(idx == 0)):

        title = st.text_input("Title", data.get("youtube_title", ""), key=f"t{idx}")

        st.markdown("**Script lines** (edit kar sakte ho — yahi TTS bolega)")
        new_lines = []
        for j, s in enumerate(segs):
            line = st.text_area(f"Line {j+1}", s.get("voice_english", ""),
                                key=f"l{idx}_{j}", height=80)
            new_lines.append(line)

        cta = st.text_input("CTA", data.get("cta_english", ""), key=f"c{idx}")

        a, b = st.columns(2)
        if a.button("✅ Approve", key=f"a{idx}", use_container_width=True):
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
            st.success("Approved! Cron isse video banayega.")
            st.rerun()

        if b.button("🗑️ Reject", key=f"r{idx}", use_container_width=True):
            rest = [p for k, p in enumerate(pending) if k != idx]
            save(PENDING_PATH, rest, p_sha, "reject: drop script")
            st.warning("Hata diya.")
            st.rerun()
