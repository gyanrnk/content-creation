"""
app.py — Football Shorts Generator ka Streamlit UI.

Chalane ke liye:
    env\\Scripts\\python.exe -m streamlit run app.py

Features:
  - Single mode: ek video — topic, mode, voice, uploads (image/voice/bgm)
  - Batch mode: kai videos ek saath (daily content backlog)
  - Branding: brand name / handle / logo har video par
  - Auto thumbnail (YouTube 16:9) + title/description/hashtags (copy-paste)
  - Preview + Download -> manually post karo
"""

import os
import sys
import io
import json
import shutil
import zipfile
import tempfile
import subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import streamlit as st

import config
from script import generate_script, save_post_text, post_text
from voice import generate_segment_voices
from media import fetch_media
from video import build_short
from thumbnail import make_thumbnail
from trends import get_trending
from ideas import get_ideas, todays_angle

st.set_page_config(page_title="Football Shorts Generator", page_icon="⚽",
                   layout="centered")

st.title("⚽ Football Shorts Generator")
st.caption("Hindi voice + English subtitles · 9:16 · 100% free/open-source · no GPU")


def _save_uploads(files, subdir):
    if not files:
        return []
    d = os.path.join(tempfile.gettempdir(), "fb_shorts_uploads", subdir)
    os.makedirs(d, exist_ok=True)
    paths = []
    for f in files:
        p = os.path.join(d, f.name)
        with open(p, "wb") as out:
            out.write(f.getbuffer())
        paths.append(p)
    return paths


def _apply_common_settings(mode, num_segments, voice_provider, zoom,
                           brand_name, brand_handle, logo_file, edge_voice=None,
                           edge_rate=None, visuals=None):
    config.MODE = mode
    config.NUM_SEGMENTS = num_segments
    config.VOICE_PROVIDER = voice_provider
    if edge_voice:
        config.EDGE_VOICE = edge_voice
    if edge_rate:
        config.EDGE_RATE = edge_rate
    config.KEN_BURNS_ZOOM = zoom
    if visuals:
        config.VIDEO_SOURCE = visuals["video_source"]
        config.USE_REAL_PHOTO_LAYER = visuals["real_photo"]
        config.REAL_PHOTO_CLIP = visuals["real_photo_clip"]
        config.SAFE_MODE = visuals["safe_mode"]
        config.CINEMATIC_GRADE = visuals["cinematic"]
        config.VIGNETTE = visuals["cinematic"]
        config.ANIMATED_CAPTIONS = visuals["captions"]
    config.BRAND_NAME = brand_name
    config.BRAND_HANDLE = brand_handle
    if logo_file is not None:
        os.makedirs("assets", exist_ok=True)
        lp = os.path.join("assets", "logo.png")
        with open(lp, "wb") as f:
            f.write(logo_file.getbuffer())
        config.LOGO_PATH = lp


# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    mode = st.selectbox(
        "Mode",
        ["facts", "quiz", "debate", "ranking", "story", "player", "preview"],
        help="facts=news/did-you-know | quiz=Guess the Player | debate=GOAT vs "
             "(Ronaldo vs Messi) | ranking=Top 5 countdown | story=rags-to-riches "
             "journey | player=spotlight | preview=match prediction")
    num_segments = st.slider("Segments (≈6 = 30-40s, lamba script = zyada)", 4, 14,
                             config.NUM_SEGMENTS)
    voice_provider = st.selectbox(
        "Voice", ["edge", "gtts", "sarvam", "elevenlabs"],
        help="edge = free + natural (recommended). gtts = free robotic. "
             "sarvam/elevenlabs = key+credits chahiye")
    _VOICE_LABELS = {
        "fr-FR-RemyMultilingualNeural": "Remy — male, warm (chosen)",
        "en-US-BrianMultilingualNeural": "Brian — male, deep",
        "en-US-AndrewMultilingualNeural": "Andrew — male, natural",
        "hi-IN-MadhurNeural": "Madhur — Hindi male (flat)",
        "hi-IN-SwaraNeural": "Swara — Hindi female (smooth)",
    }
    _voices = list(_VOICE_LABELS)
    _default_v = config.EDGE_VOICE if config.EDGE_VOICE in _voices else _voices[0]
    edge_voice = st.selectbox("Edge voice", _voices,
                              index=_voices.index(_default_v),
                              format_func=lambda v: _VOICE_LABELS[v],
                              help="Multilingual voices (Remy/Brian/Andrew) Hindi "
                                   "bol lete hain — Hindi-native se zyada natural")
    edge_rate = st.select_slider("Voice speed",
                                 options=["+0%", "+8%", "+12%", "+15%", "+20%"],
                                 value=config.EDGE_RATE if config.EDGE_RATE in
                                 ["+0%", "+8%", "+12%", "+15%", "+20%"] else "+15%")
    zoom = st.slider("Ken Burns zoom", 1.05, 1.30, config.KEN_BURNS_ZOOM, 0.01)

    st.divider()
    st.subheader("🎨 Visuals")
    v_video = st.selectbox(
        "Atmospheric footage", ["pexels", "none"],
        index=0 if config.VIDEO_SOURCE == "pexels" else 1,
        help="pexels = real video clips (key .env me hai). none = AI images (fast).")
    v_realphoto = st.checkbox(
        "📸 Real player/team photos (Wikidata+CLIP)", value=config.USE_REAL_PHOTO_LAYER,
        help="Named players ki asli photo (Messi/Ronaldo). CC-safe + attribution card.")
    v_clip = st.checkbox("   └ CLIP best-match (accurate, thoda slow)",
                         value=config.REAL_PHOTO_CLIP, disabled=not v_realphoto)
    v_safe = st.checkbox(
        "🛡️ Safe Mode (sirf AI+Pexels, no CC scraping)", value=config.SAFE_MODE,
        help="Monetization ke liye safest. Real-photo layer isse alag chalega.")
    v_cine = st.checkbox("🎬 Cinematic grade + vignette", value=config.CINEMATIC_GRADE)
    v_caps = st.checkbox("✨ Viral animated captions", value=config.ANIMATED_CAPTIONS)
    _visuals = {"video_source": v_video, "real_photo": v_realphoto,
                "real_photo_clip": v_clip, "safe_mode": v_safe,
                "cinematic": v_cine, "captions": v_caps}

    st.divider()
    st.subheader("🏷️ Branding")
    brand_name = st.text_input("Brand name", value=config.BRAND_NAME)
    brand_handle = st.text_input("Handle", value=config.BRAND_HANDLE)
    logo_file = st.file_uploader("Logo (png, optional)", type=["png"])
    st.divider()
    st.caption("Script: Pollinations · Images: Wikimedia + Pollinations AI (free)")


def _make_zip(vp, thumb_path, data) -> bytes:
    """Video + thumbnail + post.txt ek zip me (ek click me sab download)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        if vp and os.path.exists(vp):
            z.write(vp, "short.mp4")
        if thumb_path and os.path.exists(thumb_path):
            z.write(thumb_path, "thumbnail.jpg")
        z.writestr("post.txt", post_text(data))
        if os.path.exists("output/credits.txt"):
            z.write("output/credits.txt", "credits.txt")
    return buf.getvalue()


def _show_result(vp, data, thumb_path):
    st.success("🎉 Ready! Neeche se sab ek saath download karo.")

    # ── EK CLICK: sab kuch zip me (reset/multi-download problem solved) ──────────
    st.download_button("⬇️ Download ALL (video + thumbnail + text)",
                       data=_make_zip(vp, thumb_path, data),
                       file_name="football_short.zip", mime="application/zip",
                       type="primary", use_container_width=True)
    st.caption("Zip me: short.mp4 + thumbnail.jpg + post.txt (title/description/hashtags)")

    col1, col2 = st.columns([1, 1])
    with col1:
        st.video(vp)
        with open(vp, "rb") as f:
            st.download_button("⬇️ Sirf Video", f, file_name="short.mp4",
                               mime="video/mp4", use_container_width=True)
    with col2:
        if thumb_path and os.path.exists(thumb_path):
            st.image(thumb_path, caption="YouTube thumbnail")
            with open(thumb_path, "rb") as f:
                st.download_button("⬇️ Sirf Thumbnail", f,
                                   file_name="thumbnail.jpg", mime="image/jpeg",
                                   use_container_width=True)

    st.subheader("📋 Post text (copy ya zip me post.txt)")
    yt_title = data.get("youtube_title") or data.get("title_hindi", "")
    desc = data.get("description", "")
    tags = data.get("hashtags", "#Shorts #Football")
    opts = data.get("title_options") or []
    # sab post text ek box me — hover karke copy icon se ek baar me sab copy
    block = f"TITLE:\n{yt_title}\n"
    if opts:
        block += "\nA/B OPTIONS:\n" + "\n".join(f"- {o}" for o in opts) + "\n"
    block += f"\nDESCRIPTION:\n{desc}\n\n{tags}"
    st.text_area("Sab ek saath (copy icon se copy karo)", value=block,
                 height=200, key=f"post_{vp}")

    if os.path.exists("output/credits.txt"):
        with open("output/credits.txt", encoding="utf-8") as cf:
            cred = cf.read()
        with st.expander("📷 Photo credits (description me daalo — CC-BY safe)"):
            st.text_area("Credits", value=cred, height=120, key=f"cr_{vp}")

    # ── YouTube upload ──────────────────────────────────────────────────────────
    st.subheader("⬆️ YouTube pe upload")
    try:
        import upload_youtube as ytup
        if not ytup.is_authed():
            st.warning("Ek-baar setup chahiye. Terminal me chalao:\n\n"
                       "`env\\Scripts\\python.exe upload_youtube.py auth`\n\n"
                       "(pehle `client_secret.json` project folder me daalo — "
                       "README me Google Cloud guide hai). Uske baad upload button aa jaayega.")
        else:
            pv = st.selectbox("Privacy", ["unlisted", "private", "public"],
                              key=f"pv_{vp}",
                              help="unlisted/private = pehle YouTube pe review, phir public (safe)")
            if st.button("⬆️ Upload to YouTube", key=f"up_{vp}",
                         use_container_width=True):
                with st.spinner("YouTube pe upload ho raha..."):
                    try:
                        url = ytup.upload_from_output(pv)
                        st.success(f"✅ Uploaded: {url}")
                        st.caption("Title/description/hashtags + thumbnail auto-set. "
                                   "unlisted/private hai to Studio me review karke Public karo.")
                    except Exception as e:
                        st.error(f"Upload failed: {e}")
    except Exception as e:
        st.caption(f"(YouTube upload module load nahi hua: {e})")

    with st.expander("📄 Script review (fact-check karo!)"):
        for i, s in enumerate(data.get("segments", []), 1):
            st.markdown(f"**{i}.** 🎙️ {s.get('voice_hindi','')}  \n"
                        f"💬 _{s.get('subtitle_english','')}_  "
                        f"`[{s.get('image_type','ai')}: {s.get('image_query','')}]`")
    st.info("⚠️ Free LLM kabhi galat numbers/naam de deta hai — post se pehle check karo.")


tab_single, tab_auto, tab_batch = st.tabs(
    ["🎬 Single", "🤖 Auto-pilot", "📦 Batch (kai videos)"])

# ── SINGLE ──────────────────────────────────────────────────────────────────────
with tab_single:
    with st.expander("💡 Content ideas (trending + evergreen + on-this-day)"):
        st.caption(f"📅 Aaj ka suggested angle: **{todays_angle()}**")
        c1, c2 = st.columns([3, 1])
        with c2:
            if st.button("💡 Ideas laao", use_container_width=True):
                with st.spinner("Generating..."):
                    st.session_state["trends"] = get_ideas(12)
        with c1:
            q = st.text_input("Search (optional)", placeholder="Messi / India / ...",
                              label_visibility="collapsed")
            if q and st.session_state.get("last_q") != q:
                st.session_state["trends"] = get_ideas(12, q)
                st.session_state["last_q"] = q
        trs = st.session_state.get("trends", [])
        if trs:
            pick = st.selectbox("Pick karke Topic me daalo", ["—"] + trs)
            if pick != "—":
                st.session_state["picked_topic"] = pick

    input_mode = st.radio(
        "Script kaise banega?",
        ["Auto (topic se AI banaye)", "My Script (main khud likhunga)"],
        horizontal=True,
        help="My Script = system kuch add/predict nahi karega, sirf tumhara script bolega")

    topic = st.text_area("📝 Topic / Prompt",
                         value=st.session_state.get("picked_topic", config.TOPIC),
                         height=80,
                         help="Eg: 'Brazil vs Japan — compare legends and predict winner'",
                         disabled=input_mode.startswith("My"))

    custom_script = ""
    if input_mode.startswith("My"):
        custom_script = st.text_area(
            "✍️ Apna pura script yahan paste karo (jaisa hai waisa bolega — koi prediction nahi)",
            height=160,
            placeholder="Pura script likho... System ise segments me todega, "
                        "Hindi voice + English subtitle banayega, kuch add nahi karega.")

    news_date = st.text_input(
        "📅 News/event date (optional)", value=config.NEWS_DATE,
        placeholder="e.g. 2012  ya  2022-12-18",
        help="Diya to us DATE/ERA ke aas-paas ki real photo aayegi "
             "(2012 → young Messi, 2022 → World Cup wala). Khaali = latest.")

    with st.expander("📤 Apni files upload karo (optional — AI ke saath mix)"):
        up_videos = st.file_uploader("🎬 Video clips (order = segment 1,2,3...)",
                                     type=["mp4", "mov", "webm"],
                                     accept_multiple_files=True,
                                     help="Real football clips (Pexels/Pixabay/Mixkit) "
                                          "— sabse engaging. Ya assets/library/ folder me daalo.")
        up_images = st.file_uploader("Images (order = segment 1,2,3...)",
                                     type=["jpg", "jpeg", "png"],
                                     accept_multiple_files=True)
        up_voice = st.file_uploader("Apni voice (mp3, per segment)",
                                    type=["mp3", "wav"], accept_multiple_files=True)
        up_bgm = st.file_uploader("Background music (mp3)", type=["mp3", "wav"])

    if st.button("🎬 Build Short", type="primary", use_container_width=True,
                 disabled=st.session_state.get("building", False)):
        # uploads save
        user_images = _save_uploads(up_images, "img")
        user_videos = _save_uploads(up_videos, "vid")
        user_audio = _save_uploads(up_voice, "aud")
        bgm = _save_uploads([up_bgm] if up_bgm else [], "bgm")
        logo_path = config.LOGO_PATH
        if logo_file is not None:
            os.makedirs("assets", exist_ok=True)
            logo_path = os.path.join("assets", "logo.png")
            with open(logo_path, "wb") as lf:
                lf.write(logo_file.getbuffer())

        settings = {
            "MODE": mode, "NUM_SEGMENTS": num_segments,
            "VOICE_PROVIDER": voice_provider, "EDGE_VOICE": edge_voice,
            "EDGE_RATE": edge_rate, "KEN_BURNS_ZOOM": zoom,
            "BRAND_NAME": brand_name, "BRAND_HANDLE": brand_handle,
            "LOGO_PATH": logo_path,
            "VIDEO_SOURCE": _visuals["video_source"],
            "USE_REAL_PHOTO_LAYER": _visuals["real_photo"],
            "REAL_PHOTO_CLIP": _visuals["real_photo_clip"],
            "NEWS_DATE": news_date.strip(),
            "SAFE_MODE": _visuals["safe_mode"],
            "CINEMATIC_GRADE": _visuals["cinematic"], "VIGNETTE": _visuals["cinematic"],
            "ANIMATED_CAPTIONS": _visuals["captions"],
            "BGM_PATH": bgm[0] if bgm else config.BGM_PATH,
            "MAKE_THUMBNAIL": True,
        }
        job = {"topic": topic.strip(), "custom_script": custom_script,
               "settings": settings, "user_images": user_images,
               "user_videos": user_videos, "user_audio": user_audio}
        with open("job.json", "w", encoding="utf-8") as jf:
            json.dump(job, jf, ensure_ascii=False)
        for p in ("output/done.json", "output/error.txt", "output/progress.txt"):
            try:
                os.remove(p)
            except OSError:
                pass
        st.session_state.pop("video_path", None)
        # background subprocess -> app block nahi hota, koi disconnect nahi
        subprocess.Popen([sys.executable, "build_worker.py", "job.json"])
        st.session_state["building"] = True
        st.rerun()

    # ── non-blocking polling (yahi se disconnect problem khatam) ─────────────────
    if st.session_state.get("building"):
        @st.fragment(run_every=2)
        def _poll_build():
            if os.path.exists("output/error.txt"):
                st.session_state["building"] = False
                with open("output/error.txt", encoding="utf-8") as f:
                    st.error("Build failed:\n\n" + f.read()[:1500])
                st.rerun()
            elif os.path.exists("output/done.json"):
                with open("output/done.json", encoding="utf-8") as f:
                    d = json.load(f)
                st.session_state.update(video_path=d.get("video"),
                                        script_data=d.get("data", {}),
                                        thumb=d.get("thumb"), building=False)
                st.rerun()
            else:
                prog = "shuru ho raha..."
                if os.path.exists("output/progress.txt"):
                    with open("output/progress.txt", encoding="utf-8") as f:
                        prog = f.read()
                st.info("🎬 Background me ban raha hai — app free hai, "
                        "**disconnect nahi hoga**. Har 2 sec me auto-update.")
                st.write(f"**Status:** {prog}")
        _poll_build()

    if (not st.session_state.get("building")
            and st.session_state.get("video_path")
            and os.path.exists(st.session_state["video_path"])):
        _show_result(st.session_state["video_path"],
                     st.session_state.get("script_data", {}),
                     st.session_state.get("thumb"))


# ── AUTO-PILOT ────────────────────────────────────────────────────────────────
with tab_auto:
    st.write("**Fully-auto:** topic khud uthata hai (trending + ideas.py), batch me "
             "shorts banata hai — tumhe kuch type nahi karna. Upload abhi **manual**.")
    ca, cb = st.columns([1, 2])
    with ca:
        auto_n = st.number_input("Kitne shorts?", 1, 5, 3, key="auto_n")
    with cb:
        auto_hint = st.text_input("Topic hint (optional)", key="auto_hint",
                                  placeholder="khaali = pura auto (aaj ke trending)")

    if st.button("🤖 Auto-pilot chalao", type="primary", use_container_width=True,
                 disabled=st.session_state.get("auto_building", False)):
        os.makedirs("output/auto", exist_ok=True)
        settings = {
            "MODE": mode, "NUM_SEGMENTS": num_segments,
            "VOICE_PROVIDER": voice_provider, "EDGE_VOICE": edge_voice,
            "EDGE_RATE": edge_rate, "KEN_BURNS_ZOOM": zoom,
            "BRAND_NAME": brand_name, "BRAND_HANDLE": brand_handle,
            "LOGO_PATH": config.LOGO_PATH,
            "VIDEO_SOURCE": _visuals["video_source"],
            "USE_REAL_PHOTO_LAYER": _visuals["real_photo"],
            "REAL_PHOTO_CLIP": _visuals["real_photo_clip"],
            "NEWS_DATE": "", "SAFE_MODE": _visuals["safe_mode"],
            "CINEMATIC_GRADE": _visuals["cinematic"], "VIGNETTE": _visuals["cinematic"],
            "ANIMATED_CAPTIONS": _visuals["captions"],
            "BGM_PATH": config.BGM_PATH, "MAKE_THUMBNAIL": True,
        }
        with open("output/auto/settings.json", "w", encoding="utf-8") as sf:
            json.dump(settings, sf, ensure_ascii=False)
        for p in ("output/auto/done.json", "output/auto/error.txt",
                  "output/auto/progress.txt"):
            try:
                os.remove(p)
            except OSError:
                pass
        args = [sys.executable, "auto.py", str(int(auto_n))]
        if auto_hint.strip():
            args.append(auto_hint.strip())
        subprocess.Popen(args)
        st.session_state["auto_building"] = True
        st.rerun()

    if st.session_state.get("auto_building"):
        @st.fragment(run_every=3)
        def _poll_auto():
            if os.path.exists("output/auto/error.txt"):
                st.session_state["auto_building"] = False
                with open("output/auto/error.txt", encoding="utf-8") as f:
                    st.error("Auto-pilot failed:\n\n" + f.read()[:1500])
                st.rerun()
            elif os.path.exists("output/auto/done.json"):
                st.session_state["auto_building"] = False
                st.rerun()
            else:
                prog = "shuru ho raha..."
                if os.path.exists("output/auto/progress.txt"):
                    with open("output/auto/progress.txt", encoding="utf-8") as f:
                        prog = f.read()
                st.info("🤖 Background me shorts ban rahe — app free hai, "
                        "**disconnect nahi hoga**. Har 3 sec me update.")
                st.write(f"**Status:** {prog}")
        _poll_auto()

    if (not st.session_state.get("auto_building")
            and os.path.exists("output/auto/done.json")):
        with open("output/auto/done.json", encoding="utf-8") as f:
            summary = json.load(f)
        st.success(f"🎉 {summary.get('ok', 0)}/{summary.get('total', 0)} shorts ready "
                   f"— `{summary.get('run_dir', '')}`")
        st.caption("Upload abhi manual: har video download karo (ya YouTube tab se daalo).")
        for r in summary.get("results", []):
            if not r.get("ok"):
                st.warning(f"❌ {r['topic'][:50]}: {r.get('error', '')[:120]}")
                continue
            vp, d = r["video"], r["dir"]
            with st.expander(f"🎬 {r['topic'][:55]}"):
                if os.path.exists(vp):
                    st.video(vp)
                    with open(vp, "rb") as f:
                        st.download_button("⬇️ MP4", f,
                                           file_name=os.path.basename(d) + ".mp4",
                                           mime="video/mp4", key=f"av_{d}")
                th = os.path.join(d, "thumbnail.jpg")
                if os.path.exists(th):
                    st.image(th, width=240)
                pt = os.path.join(d, "post.txt")
                if os.path.exists(pt):
                    with open(pt, encoding="utf-8") as f:
                        st.text_area("Title / description / hashtags",
                                     value=f.read(), height=180, key=f"ap_{d}")


# ── BATCH ───────────────────────────────────────────────────────────────────────
with tab_batch:
    st.write("Har line me ek topic. Format: `topic | mode` (mode optional).")
    default_topics = ("Brazil vs Japan — compare legends and predict winner | preview\n"
                      "5 mind-blowing FIFA World Cup 2026 facts | facts\n"
                      "Lionel Messi World Cup journey | player")
    topics_text = st.text_area("Topics", value=default_topics, height=160)

    if st.button("📦 Build All", type="primary", use_container_width=True):
        _apply_common_settings(mode, num_segments, voice_provider, zoom,
                               brand_name, brand_handle, logo_file, edge_voice,
                               edge_rate, visuals=_visuals)
        config.BGM_PATH = config.BGM_PATH if os.path.exists(config.BGM_PATH or "") else None

        import re
        from batch import build_one, _slug

        lines = [l.strip() for l in topics_text.splitlines()
                 if l.strip() and not l.startswith("#")]
        base = os.path.join("output", "batch")
        if os.path.exists(base):
            shutil.rmtree(base)

        done = []
        prog = st.progress(0.0, text="Starting...")
        for i, line in enumerate(lines, 1):
            if "|" in line:
                tp, md = [x.strip() for x in line.split("|", 1)]
            else:
                tp, md = line, mode
            prog.progress((i - 1) / len(lines), text=f"[{i}/{len(lines)}] {tp[:40]}")
            try:
                out_dir = os.path.join(base, _slug(tp, i))
                data = build_one(tp, md, out_dir)
                done.append((tp, os.path.join(out_dir, "short.mp4"),
                             os.path.join(out_dir, "thumbnail.jpg"), data))
            except Exception as e:
                st.warning(f"❌ {tp[:40]}: {e}")
        prog.progress(1.0, text="Done!")

        st.success(f"🎉 {len(done)}/{len(lines)} videos ready in output/batch/")
        for tp, vp, th, data in done:
            with st.expander(f"🎬 {data.get('youtube_title', tp)[:50]}"):
                c1, c2 = st.columns(2)
                with c1:
                    if os.path.exists(vp):
                        st.video(vp)
                        with open(vp, "rb") as f:
                            st.download_button("⬇️ MP4", f, file_name=f"{_slug(tp,0)}.mp4",
                                               mime="video/mp4", key=f"v{vp}")
                with c2:
                    if os.path.exists(th):
                        st.image(th)
                    st.caption(f"**{data.get('youtube_title','')}**")
                    st.text(data.get("hashtags", ""))
