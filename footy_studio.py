"""
footy_studio.py — Remotion shorts ka REVIEW + PUBLISH app.

Sab kuch auto hota he — generate, render, title/description — LEKIN YouTube pe
kuch bhi TERE APPROVE kiye bina nahi jaata. Approve dabate hi upload ho jaata he.

Chalao:   streamlit run footy_studio.py       (ya footy.bat double-click)
"""

import os
import json
import subprocess
import datetime

import streamlit as st

import footy_packs as fp

st.set_page_config(page_title="Footy Studio", page_icon="⚽", layout="centered")

PRIVACY_DEFAULT = "public"


# ── helpers ──────────────────────────────────────────────────────────────────
def _upload(pack: dict, privacy: str) -> str:
    """YouTube upload — sirf approve ke baad call hota he."""
    import upload_youtube as uy
    yt = pack["youtube"]
    return uy.upload(
        pack["video"], yt["title"], yt["description"],
        tags=yt.get("tags"), privacy=privacy,
    )


def _save_pack(pack: dict):
    packs = fp.load_queue()
    for i, p in enumerate(packs):
        if p["id"] == pack["id"]:
            packs[i] = pack
    fp.save_queue(packs)


# ── header ───────────────────────────────────────────────────────────────────
st.title("⚽ Footy Studio")
packs = fp.load_queue()
pending = [p for p in packs if p["status"] == "pending"]
approved = [p for p in packs if p["status"] == "approved"]
published = [p for p in packs if p["status"] == "published"]

c1, c2, c3 = st.columns(3)
c1.metric("Review ke liye", len(pending))
c2.metric("Approved", len(approved))
c3.metric("Published", len(published))

# Consistency counter — channel ka #1 lever yahi he.
if published:
    last = max(p.get("published_at", "") for p in published)
    if last:
        gap = (datetime.datetime.now() - datetime.datetime.fromisoformat(last)).days
        if gap >= 1:
            st.error(f"⚠️ Aakhri upload ko {gap} din ho gaye. Gap hi channel ko maarta he.")
        else:
            st.success("✅ Aaj upload ho chuka he.")

st.divider()

# ── generate ─────────────────────────────────────────────────────────────────
with st.expander("➕ Naye shorts banao", expanded=not pending):
    n = st.slider("Kitne", 1, 5, 2)
    if st.button("Generate + Render", type="primary", use_container_width=True):
        with st.spinner("Generate ho raha he..."):
            made = fp.generate(n)
        if not made:
            st.warning("Koi naya combo nahi bacha — data/stat_bank.json me naya "
                       "player ya metric add karo.")
        for m in made:
            with st.spinner(f"Render: {m['id']} ..."):
                try:
                    fp.render(m)
                    st.success(f"✅ {m['id']}")
                except Exception as e:
                    st.error(f"❌ {m['id']}: {e}")
        st.rerun()

# ── review queue ─────────────────────────────────────────────────────────────
st.subheader("⏳ Review")

if not pending:
    st.info("Queue khali he. Upar se naye banao.")

for pack in pending:
    with st.container(border=True):
        badge = {"era": "⚔️ VS DUEL", "guess": "🤔 GUESS", "whatif": "🔄 WHAT IF"}
        st.caption(f"{badge.get(pack.get('format'), '?')} · `{pack['id']}` · "
                   f"{pack['duration_s']}s · stats as of {pack['bank_as_of']}")

        if pack.get("video") and os.path.exists(pack["video"]):
            st.video(pack["video"])
        else:
            st.warning("Video render nahi hui.")
            if st.button("Render karo", key=f"r{pack['id']}"):
                try:
                    fp.render(pack)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

        if pack.get("review_note"):
            st.warning(pack["review_note"])

        # Har number apne source ke saath — review ka asli kaam yahi he.
        st.markdown("**Content (check kar lo):**")
        props, fmt = pack["props"], pack.get("format", "era")

        if fmt == "era":
            for d in props["duels"]:
                st.markdown(
                    f"- **{d['head']}** — {d['oldName']} `{d['oldVal']}` vs "
                    f"{d['newName']} `{d['newVal']}`  →  +{d['oldVal'] - d['newVal']}"
                )
        elif fmt == "guess":
            for i, c in enumerate(props["clues"], 1):
                st.markdown(f"- Clue {i}: `{c}`")
            st.markdown(f"- **Answer:** {props['answerName']} — {props['answerLine']}")
        elif fmt == "whatif":
            for s in props["swaps"]:
                st.markdown(f"- **{s['name']}** — {s['from']} → **{s['to']}**  ·  `{s['stat']}`")
            st.caption("Transfers kalpanik hain; video pe 'IMAGINARY TRANSFER' label laga he.")
        with st.expander("Sources"):
            for who, src in pack.get("sources", {}).items():
                st.caption(f"**{who}** — {src}")

        yt = pack["youtube"]
        title = st.text_input("Title", yt["title"], key=f"t{pack['id']}")
        desc = st.text_area("Description", yt["description"], height=210,
                            key=f"d{pack['id']}")
        privacy = st.selectbox("Privacy", ["public", "unlisted", "private"],
                               index=["public", "unlisted", "private"].index(PRIVACY_DEFAULT),
                               key=f"p{pack['id']}")

        a, b = st.columns(2)
        if a.button("✅ Approve + Upload", key=f"a{pack['id']}",
                    type="primary", use_container_width=True):
            pack["youtube"]["title"] = title
            pack["youtube"]["description"] = desc
            _save_pack(pack)
            if not (pack.get("video") and os.path.exists(pack["video"])):
                st.error("Video hi nahi he — pehle render karo.")
            else:
                with st.spinner("YouTube pe ja raha he..."):
                    try:
                        url = _upload(pack, privacy)
                        fp.approve(pack["id"])
                        fp.mark_published(pack["id"], url)
                        st.success(f"📤 Live: {url}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Upload fail: {e}")
                st.rerun()

        if b.button("🗑️ Reject", key=f"x{pack['id']}", use_container_width=True):
            fp.reject(pack["id"])
            st.rerun()

# ── published log ────────────────────────────────────────────────────────────
if published:
    st.divider()
    st.subheader("📤 Published")
    for p in sorted(published, key=lambda x: x.get("published_at", ""), reverse=True)[:10]:
        st.markdown(f"- {p.get('published_at', '')[:16]} — [{p['youtube']['title'][:52]}]"
                    f"({p.get('youtube_url', '#')})")
