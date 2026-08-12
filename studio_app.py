"""
studio_app.py — poora control panel. Ek jagah se sab kuch.

Ye footy_studio.py ki jagah leta he. Farak:
  - dono channels (Footy Gyaan + Below The Blue)
  - Overview page jo batata he ki process kahan atka he
  - Content Bank me form se naya data daalna (source + date compulsory)
  - freshness warnings — purane numbers publish na ho jaayein
  - analytics dono channels ki
  - logs

Chalao:  streamlit run studio_app.py     (ya studio.bat)
"""

import os
import json
import datetime
import subprocess

import streamlit as st

import footy_packs as fp
import channels
import bank_check

ROOT = os.path.dirname(os.path.abspath(__file__))
BANK_PATH = os.path.join(ROOT, "data", "stat_bank.json")
LOG_PATH = os.path.join(ROOT, "data", "run_log.jsonl")

st.set_page_config(page_title="Studio", page_icon="🎬", layout="wide")


# ── helpers ──────────────────────────────────────────────────────────────────
def log(event: str, **kw):
    rec = {"at": datetime.datetime.now().isoformat(timespec="seconds"), "event": event, **kw}
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_log(n=60) -> list:
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, encoding="utf-8") as f:
        lines = f.readlines()[-n:]
    out = []
    for l in lines:
        try:
            out.append(json.loads(l))
        except json.JSONDecodeError:
            pass
    return list(reversed(out))


@st.cache_data(ttl=600)
def channel_stats(label: str) -> dict:
    """Channel ka live snapshot. 10 min cache — har rerun pe API nahi maarta."""
    try:
        return channels.whoami(label)
    except Exception as e:
        return {"error": str(e)[:120]}


@st.cache_data(ttl=600)
def daily_views(label: str, days: int = 14) -> list:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    try:
        ch = channels.get(label)
        c = Credentials.from_authorized_user_file(ch["read_token"])
        an = build("youtubeAnalytics", "v2", credentials=c)
        end = datetime.date.today()
        r = an.reports().query(
            ids="channel==MINE", startDate=str(end - datetime.timedelta(days=days)),
            endDate=str(end), metrics="views,subscribersGained",
            dimensions="day", sort="day").execute()
        return r.get("rows", [])
    except Exception:
        return []


def save_bank(bank: dict):
    with open(BANK_PATH, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)


# ── header ───────────────────────────────────────────────────────────────────
st.title("🎬 Studio")

queue = fp.load_queue()
pending = [p for p in queue if p["status"] == "pending"]
published = [p for p in queue if p["status"] == "published"]
fresh = bank_check.report()

tabs = st.tabs(["🏠 Overview", "🎬 Queue", "📚 Content Bank", "📊 Analytics", "🧾 Logs"])

# ── OVERVIEW ─────────────────────────────────────────────────────────────────
with tabs[0]:
    st.subheader("Channels")
    cols = st.columns(len(channels.CHANNELS))
    for col, (label, ch) in zip(cols, channels.CHANNELS.items()):
        s = channel_stats(label)
        with col:
            if "error" in s:
                st.error(f"**{ch['name']}**\n\n{s['error']}")
            else:
                st.metric(s["title"], f"{s['subs']} subs", f"{s['videos']} videos")
                st.caption(f"`{label}` · {s['handle']} · {ch['niche']}")

    st.divider()
    st.subheader("Aaj ka status")

    today = datetime.date.today().isoformat()
    made_today = [p for p in queue if p["created_at"][:10] == today]
    up_today = [p for p in published if p.get("published_at", "")[:10] == today]
    rendered = [p for p in made_today if p.get("video")]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aaj bane", len(made_today))
    c2.metric("Render hue", len(rendered))
    c3.metric("Review pending", len(pending))
    c4.metric("Aaj upload", len(up_today))

    if not up_today:
        last = max((p.get("published_at", "") for p in published), default="")
        if last:
            gap = (datetime.datetime.now() - datetime.datetime.fromisoformat(last)).days
            st.error(f"⚠️ Aaj upload nahi hua. Aakhri upload {gap} din pehle. "
                     f"Gap hi channel ko maarta he.")
        else:
            st.warning("Aaj upload nahi hua.")
    else:
        st.success(f"✅ Aaj {len(up_today)} upload ho chuka he.")

    st.divider()
    st.subheader("Content bank ki sehat")
    b1, b2, b3 = st.columns(3)
    b1.metric("🔒 Fixed (kabhi expire nahi)", len(fresh["fixed"]))
    b2.metric("⚠️ Jaldi check karo", len(fresh["warn"]))
    b3.metric("🔴 Stale (block)", len(fresh["stale"]))
    if fresh["stale"]:
        st.error("🔴 Ye entries generator me use NAHI hongi jab tak dobara verify na ho: "
                 + ", ".join(r["name"] for r in fresh["stale"]))
    elif fresh["warn"]:
        st.warning("⚠️ " + ", ".join(r["name"] for r in fresh["warn"]))

# ── QUEUE ────────────────────────────────────────────────────────────────────
with tabs[1]:
    gen_col, ch_col = st.columns([2, 1])
    n = gen_col.slider("Kitne naye banao", 1, 4, 1)
    target = ch_col.selectbox("Channel", list(channels.CHANNELS),
                              format_func=lambda k: channels.CHANNELS[k]["name"])

    if st.button("⚡ Generate + Render", type="primary"):
        with st.spinner("Ban raha he..."):
            made = fp.generate(n)
        if not made:
            st.warning("Kuch naya nahi bana — novelty gate ne rok diya. "
                       "Content Bank me naya data daalo.")
            log("generate_empty")
        for m in made:
            with st.spinner(f"Render: {m['id']}"):
                try:
                    fp.render(m)
                    st.success(f"✅ {m['format']} · {m['duration_s']}s")
                    log("render_ok", pack=m["id"], format=m["format"])
                except Exception as e:
                    st.error(f"❌ {m['id']}: {e}")
                    log("render_fail", pack=m["id"], error=str(e)[:200])
        st.rerun()

    st.divider()
    if not pending:
        st.info("Queue khali he.")

    for pack in pending:
        with st.container(border=True):
            badge = {"era": "⚔️ VS", "guess": "🤔 GUESS", "whatif": "🔄 WHAT IF",
                     "rank": "📊 RANK", "archive": "🎞️ ARCHIVE"}
            st.caption(f"{badge.get(pack.get('format'), '?')} · `{pack['id']}` · "
                       f"{pack['duration_s']}s · bank {pack.get('bank_as_of', '?')}")

            left, right = st.columns([1, 1])
            with left:
                if pack.get("video") and os.path.exists(pack["video"]):
                    st.video(pack["video"])
                else:
                    st.warning("Render nahi hui")
                    if st.button("Render", key=f"r{pack['id']}"):
                        try:
                            fp.render(pack); st.rerun()
                        except Exception as e:
                            st.error(str(e))

            with right:
                if pack.get("review_note"):
                    st.warning(pack["review_note"])
                st.markdown("**Content:**")
                props, fmt = pack["props"], pack.get("format")
                if fmt == "era":
                    for d in props.get("duels", []):
                        st.markdown(f"- **{d['head']}** — {d['oldName']} `{d['oldVal']}` "
                                    f"vs {d['newName']} `{d['newVal']}`")
                elif fmt == "guess":
                    for i, c in enumerate(props.get("clues", []), 1):
                        st.markdown(f"- Clue {i}: `{c}`")
                    st.markdown(f"- **Answer:** {props.get('answerName')}")
                elif fmt == "whatif":
                    for s in props.get("swaps", []):
                        st.markdown(f"- {s['name']}: {s['from']} → **{s['to']}** · `{s['stat']}`")
                elif fmt == "rank":
                    for k in props.get("keepers", []):
                        st.markdown(f"- #{k['rank']} **{k['name']}** — {k['value']}")

                with st.expander("Sources"):
                    for who, src in pack.get("sources", {}).items():
                        st.caption(f"**{who}** — {src}")

            title = st.text_input("Title", pack["youtube"]["title"], key=f"t{pack['id']}")
            desc = st.text_area("Description", pack["youtube"]["description"],
                                height=180, key=f"d{pack['id']}")
            up_ch = st.selectbox("Upload kahan", list(channels.CHANNELS), key=f"c{pack['id']}",
                                 format_func=lambda k: channels.CHANNELS[k]["name"])

            a, b = st.columns(2)
            if a.button("✅ Approve + Upload", key=f"a{pack['id']}", type="primary",
                        use_container_width=True):
                pack["youtube"]["title"] = title
                pack["youtube"]["description"] = desc
                q = fp.load_queue()
                for i, x in enumerate(q):
                    if x["id"] == pack["id"]:
                        q[i] = pack
                fp.save_queue(q)
                if not (pack.get("video") and os.path.exists(pack["video"])):
                    st.error("Video hi nahi he.")
                else:
                    with st.spinner("Upload..."):
                        try:
                            url = channels.upload_to(
                                up_ch, pack["video"], title, desc,
                                tags=pack["youtube"].get("tags"), privacy="public")
                            fp.approve(pack["id"])
                            fp.mark_published(pack["id"], url)
                            log("upload_ok", pack=pack["id"], channel=up_ch, url=url)
                            st.success(f"📤 {url}")
                            st.balloons()
                        except Exception as e:
                            log("upload_fail", pack=pack["id"], error=str(e)[:200])
                            st.error(f"Upload fail: {e}")
                    st.rerun()

            if b.button("🗑️ Reject", key=f"x{pack['id']}", use_container_width=True):
                fp.reject(pack["id"]); log("reject", pack=pack["id"]); st.rerun()

# ── CONTENT BANK ─────────────────────────────────────────────────────────────
with tabs[2]:
    bank = fp.load_bank()
    st.caption("Yahan jo daaloge wahi videos me aayega. Isliye source aur date compulsory he.")

    icon = {"fixed": "🔒", "ok": "✅", "warn": "⚠️", "stale": "🔴"}
    st.markdown("**Abhi bank me:**")
    st.dataframe(
        [{"": icon[r["state"]], "Entry": r["name"],
          "Type": "fixed" if not r["volatile"] else "volatile",
          "Age": "—" if not r["volatile"] else f"{r['age']}d",
          "Stats": ", ".join(r["stats"])} for r in fresh["rows"]],
        use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### ➕ Naya player daalo")
    with st.form("add_player"):
        c1, c2, c3 = st.columns(3)
        key = c1.text_input("Key (chhota, bina space)", placeholder="zidane")
        name = c2.text_input("Screen naam", placeholder="ZIDANE")
        cut = c3.text_input("Cutout file (bina .png)", placeholder="zidane")
        tag = st.text_input("Tag (reveal pe dikhega)", placeholder="THE MAESTRO 🎩")

        st.markdown("**Stats** — jitne pata ho, khali chhod do baaki")
        stat_vals = {}
        mcols = st.columns(3)
        for i, (mk, mv) in enumerate(bank["metrics"].items()):
            v = mcols[i % 3].number_input(mv["label"], min_value=0, value=0, key=f"nm{mk}")
            if v > 0:
                stat_vals[mk] = int(v)

        volatile = st.checkbox("Ye player abhi khel raha he (number badal sakta he)", value=True)
        source = st.text_area("Source — kahan se aaya ye number? *", height=70,
                              placeholder="UEFA all-time list, checked 2026-08-12")

        if st.form_submit_button("Add", type="primary"):
            errs = []
            if not key or not name or not cut:
                errs.append("key / naam / cutout khali he")
            if not source.strip():
                errs.append("source likhna zaroori he")
            if not stat_vals:
                errs.append("kam se kam ek stat chahiye")
            if cut and not fp._have_cut(cut):
                errs.append(f"cutout nahi mila: public/cut/{cut}.png "
                            f"— pehle `python make_cutout.py \"{name}\"` chalao")
            if errs:
                for e in errs:
                    st.error(e)
            else:
                bank["players"][key] = {
                    "name": name, "cut": cut, "era": "golden", "stats": stat_vals,
                    "volatile": volatile, "checked": datetime.date.today().isoformat(),
                    "source": source.strip(), "tag": tag or "THE LEGEND 🏆"}
                save_bank(bank)
                log("bank_add", key=key)
                st.success(f"✅ {name} add ho gaya")
                st.rerun()

    st.divider()
    st.markdown("### 🔄 Purana number update karo")
    vol = [r for r in fresh["rows"] if r["volatile"] and r["key"] in bank["players"]]
    if vol:
        who = st.selectbox("Kaunsa player", [r["key"] for r in vol],
                           format_func=lambda k: bank["players"][k]["name"])
        pl = bank["players"][who]
        with st.form("upd"):
            new = {}
            ucols = st.columns(3)
            for i, (mk, val) in enumerate(pl["stats"].items()):
                new[mk] = ucols[i % 3].number_input(
                    bank["metrics"][mk]["label"], min_value=0, value=int(val), key=f"u{mk}")
            src = st.text_area("Naya source", pl.get("source", ""), height=70)
            if st.form_submit_button("Update + aaj ki date lagao"):
                pl["stats"] = {k: int(v) for k, v in new.items()}
                pl["source"] = src
                pl["checked"] = datetime.date.today().isoformat()
                save_bank(bank)
                log("bank_update", key=who)
                st.success("Updated"); st.rerun()

# ── ANALYTICS ────────────────────────────────────────────────────────────────
with tabs[3]:
    for label, ch in channels.CHANNELS.items():
        st.subheader(ch["name"])
        rows = daily_views(label)
        if not rows:
            st.caption("Analytics abhi nahi mili (naya channel ho to 2-3 din lagte he).")
        else:
            st.line_chart({"views": [r[1] for r in rows]},
                          x=None, use_container_width=True)
            tot = sum(r[1] for r in rows)
            gained = sum(r[2] for r in rows)
            m1, m2 = st.columns(2)
            m1.metric("14 din ke views", tot)
            m2.metric("14 din me subs", f"+{gained}")
        st.divider()

    st.caption("YouTube analytics 2-3 din peeche chalti he — aaj ka data kal-parso dikhega.")

# ── LOGS ─────────────────────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("Kya kab hua")
    entries = read_log()
    if not entries:
        st.info("Abhi koi log nahi.")
    else:
        st.dataframe(entries, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Token status")
    for label, ch in channels.CHANNELS.items():
        try:
            g = channels.verify(label)
            st.success(f"✅ **{ch['name']}** — {g['handle']} · {g['videos']} videos")
        except Exception as e:
            st.error(f"❌ **{ch['name']}** — {str(e)[:160]}")

    st.caption("Token marr jaaye to: `python auth_channel.py <label>` chalao. "
               "Agar har hafte marr raha he to Google Cloud project 'Testing' me he — "
               "usse 'Production' me publish karna padega.")
