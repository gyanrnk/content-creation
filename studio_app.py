"""
studio_app.py — the control panel. Everything in one place.

Replaces footy_studio.py. Adds: both channels, an Overview that says where
today's run actually stopped, a Content Bank form, freshness warnings, analytics,
logs, and a Help tab that doubles as the runbook.

Run:  streamlit run studio_app.py     (or studio.bat)

UI copy is English on purpose — this is the surface the operator reads every day.
Code comments stay in the codebase's existing Hinglish style.
"""

import os
import json
import datetime

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
    """Live snapshot. 10 min cache — warna har rerun pe API hit hoti he."""
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

tabs = st.tabs(["🏠 Overview", "🎬 Queue", "📚 Content Bank",
                "📊 Analytics", "🧾 Logs", "🆘 Help"])

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
                st.metric(s["title"], f"{s['subs']} subscribers", f"{s['videos']} videos")
                st.caption(f"`{label}` · {s['handle']} · {ch['niche']}")

    st.divider()
    st.subheader("Today")

    today = datetime.date.today().isoformat()
    made_today = [p for p in queue if p["created_at"][:10] == today]
    up_today = [p for p in published if p.get("published_at", "")[:10] == today]
    rendered = [p for p in made_today if p.get("video")]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Generated", len(made_today))
    c2.metric("Rendered", len(rendered))
    c3.metric("Awaiting review", len(pending))
    c4.metric("Uploaded", len(up_today))

    if not up_today:
        last = max((p.get("published_at", "") for p in published), default="")
        if last:
            gap = (datetime.datetime.now() - datetime.datetime.fromisoformat(last)).days
            st.error(f"⚠️ Nothing uploaded today. Last upload was {gap} day(s) ago. "
                     f"Upload gaps are the single biggest cause of reach collapse.")
        else:
            st.warning("Nothing uploaded today.")
    else:
        st.success(f"✅ {len(up_today)} upload(s) published today.")

    st.divider()
    st.subheader("Content bank health")
    b1, b2, b3 = st.columns(3)
    b1.metric("🔒 Fixed (never expires)", len(fresh["fixed"]))
    b2.metric("⚠️ Re-check soon", len(fresh["warn"]))
    b3.metric("🔴 Stale (blocked)", len(fresh["stale"]))
    if fresh["stale"]:
        st.error("🔴 These entries are blocked from the generator until re-verified: "
                 + ", ".join(r["name"] for r in fresh["stale"])
                 + " — update them under Content Bank.")
    elif fresh["warn"]:
        st.warning("⚠️ Verify soon: " + ", ".join(r["name"] for r in fresh["warn"]))

# ── QUEUE ────────────────────────────────────────────────────────────────────
with tabs[1]:
    n = st.slider("How many to generate", 1, 4, 1)

    if st.button("⚡ Generate + Render", type="primary"):
        with st.spinner("Generating..."):
            made = fp.generate(n)
        if not made:
            st.warning("Nothing new was generated — the novelty gate rejected every "
                       "candidate. Add players or rankings under Content Bank.")
            log("generate_empty")
        for m in made:
            with st.spinner(f"Rendering {m['id']}..."):
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
        st.info("Queue is empty.")

    for pack in pending:
        with st.container(border=True):
            badge = {"era": "⚔️ VS DUEL", "guess": "🤔 GUESS", "whatif": "🔄 WHAT IF",
                     "rank": "📊 RANKING", "archive": "🎞️ ARCHIVE"}
            st.caption(f"{badge.get(pack.get('format'), '?')} · `{pack['id']}` · "
                       f"{pack['duration_s']}s · bank {pack.get('bank_as_of', '?')}")

            left, right = st.columns([1, 1])
            with left:
                if pack.get("video") and os.path.exists(pack["video"]):
                    st.video(pack["video"])
                else:
                    st.warning("Not rendered yet")
                    if st.button("Render now", key=f"r{pack['id']}"):
                        try:
                            fp.render(pack); st.rerun()
                        except Exception as e:
                            st.error(str(e))

            with right:
                if pack.get("review_note"):
                    st.warning(pack["review_note"])
                st.markdown("**Check the content:**")
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
            up_ch = st.selectbox("Upload to", list(channels.CHANNELS), key=f"c{pack['id']}",
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
                    st.error("There is no rendered video for this pack.")
                else:
                    with st.spinner("Uploading..."):
                        try:
                            url = channels.upload_to(
                                up_ch, pack["video"], title, desc,
                                tags=pack["youtube"].get("tags"), privacy="public")
                            fp.approve(pack["id"])
                            fp.mark_published(pack["id"], url)
                            log("upload_ok", pack=pack["id"], channel=up_ch, url=url)
                            st.success(f"📤 Published: {url}")
                            st.balloons()
                        except Exception as e:
                            log("upload_fail", pack=pack["id"], error=str(e)[:200])
                            st.error(f"Upload failed: {e}")
                    st.rerun()

            if b.button("🗑️ Reject", key=f"x{pack['id']}", use_container_width=True):
                fp.reject(pack["id"]); log("reject", pack=pack["id"]); st.rerun()

# ── CONTENT BANK ─────────────────────────────────────────────────────────────
with tabs[2]:
    bank = fp.load_bank()
    st.caption("Whatever goes in here ends up on screen. That is why a source and a "
               "date are required — an entry without them cannot be saved.")

    icon = {"fixed": "🔒", "ok": "✅", "warn": "⚠️", "stale": "🔴"}
    st.markdown("**Current bank**")
    st.dataframe(
        [{"": icon[r["state"]], "Entry": r["name"],
          "Type": "fixed" if not r["volatile"] else "volatile",
          "Age": "—" if not r["volatile"] else f"{r['age']}d",
          "Stats": ", ".join(r["stats"])} for r in fresh["rows"]],
        use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### ➕ Add a player")
    with st.form("add_player"):
        c1, c2, c3 = st.columns(3)
        key = c1.text_input("Key (short, no spaces)", placeholder="zidane")
        name = c2.text_input("Display name", placeholder="ZIDANE")
        cut = c3.text_input("Cutout file (without .png)", placeholder="zidane")
        tag = st.text_input("Tag (shown on the reveal)", placeholder="THE MAESTRO 🎩")

        st.markdown("**Stats** — fill in what you know, leave the rest at 0")
        stat_vals = {}
        mcols = st.columns(3)
        for i, (mk, mv) in enumerate(bank["metrics"].items()):
            v = mcols[i % 3].number_input(mv["label"], min_value=0, value=0, key=f"nm{mk}")
            if v > 0:
                stat_vals[mk] = int(v)

        volatile = st.checkbox("Still playing (the number can change)", value=True)
        source = st.text_area("Source — where does this number come from? *", height=70,
                              placeholder="UEFA all-time list, checked 2026-08-12")

        if st.form_submit_button("Add to bank", type="primary"):
            errs = []
            if not key or not name or not cut:
                errs.append("Key, display name and cutout file are all required.")
            if not source.strip():
                errs.append("A source is required. Without it the number cannot be trusted later.")
            if not stat_vals:
                errs.append("At least one stat is required.")
            if cut and not fp._have_cut(cut):
                errs.append(f"No cutout found at public/cut/{cut}.png — "
                            f"run `python make_cutout.py \"{name}\"` first.")
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
                st.success(f"✅ {name} added.")
                st.rerun()

    st.divider()
    st.markdown("### 🔄 Update an existing number")
    vol = [r for r in fresh["rows"] if r["volatile"] and r["key"] in bank["players"]]
    if not vol:
        st.caption("Every entry is marked fixed — nothing needs updating.")
    else:
        who = st.selectbox("Player", [r["key"] for r in vol],
                           format_func=lambda k: bank["players"][k]["name"])
        pl = bank["players"][who]
        with st.form("upd"):
            new = {}
            ucols = st.columns(3)
            for i, (mk, val) in enumerate(pl["stats"].items()):
                new[mk] = ucols[i % 3].number_input(
                    bank["metrics"][mk]["label"], min_value=0, value=int(val), key=f"u{mk}")
            src = st.text_area("Updated source", pl.get("source", ""), height=70)
            if st.form_submit_button("Update and stamp today's date"):
                pl["stats"] = {k: int(v) for k, v in new.items()}
                pl["source"] = src
                pl["checked"] = datetime.date.today().isoformat()
                save_bank(bank)
                log("bank_update", key=who)
                st.success("Updated."); st.rerun()

# ── ANALYTICS ────────────────────────────────────────────────────────────────
with tabs[3]:
    for label, ch in channels.CHANNELS.items():
        st.subheader(ch["name"])
        rows = daily_views(label)
        if not rows:
            st.caption("No analytics yet. A new channel takes 2–3 days to report.")
        else:
            st.line_chart({"views": [r[1] for r in rows]}, use_container_width=True)
            m1, m2 = st.columns(2)
            m1.metric("Views (14 days)", sum(r[1] for r in rows))
            m2.metric("Subscribers gained", f"+{sum(r[2] for r in rows)}")
        st.divider()

    st.caption("YouTube analytics run 2–3 days behind. Today's numbers appear later "
               "this week. Per-video view counts on the channel update much faster.")

# ── LOGS ─────────────────────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("Activity")
    entries = read_log()
    if not entries:
        st.info("No activity recorded yet.")
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

# ── HELP ─────────────────────────────────────────────────────────────────────
with tabs[5]:
    st.subheader("If something breaks")
    st.caption("Every problem here has actually happened. Fixes are in order of "
               "likelihood — try the first one before anything else.")

    with st.expander("🔴 Uploads suddenly stopped working (this is the big one)"):
        st.markdown("""
**Most likely cause:** the Google Cloud project is still in **Testing** mode.
In Testing, OAuth refresh tokens die after **7 days**, so uploads stop roughly a
week after they were set up — with no warning.

**Fix — do this once, permanently:**
1. Go to `console.cloud.google.com`
2. **APIs & Services → OAuth consent screen**
3. Look at **Publishing status**
4. If it says *Testing*, press **Publish app**

After that, tokens stop expiring on a timer.

**If it still fails,** re-authorise that channel:
```
python auth_channel.py fresh     (Below The Blue)
python auth_channel.py footy     (Footy Gyaan)
```
Pick the correct channel in the browser picker — the script warns you if you
select the wrong one.
        """)

    with st.expander("⚠️ 'Nothing new was generated'"):
        st.markdown("""
The novelty gate rejected every candidate. It blocks a pack when:

- the same **format** went out on the previous upload
- a **headliner** already led one of the last 3 uploads
- the exact **combination** has been built before, ever
- the numbers **already appear** in a video on the channel
- the entry is **stale** (see below)

**Fix:** add new material under **Content Bank**. One new player with three stats
unlocks several new combinations. This message is the system working, not failing —
it is what stops the channel publishing the same video twice.
        """)

    with st.expander("🔴 An entry is marked stale and blocked"):
        st.markdown("""
Stats for players who are **still playing** go out of date on their own. This has
already caused a real error: Ronaldo's international goals sat at 143 in the bank
while the true figure after the 2026 World Cup was 146 — and a video shipped with
the wrong number. Nothing errored; the bank simply rotted.

So every entry now carries:

| Mark | Meaning |
|---|---|
| 🔒 fixed | Retired player or historical record. Never expires. |
| ✅ ok | Volatile, checked recently. |
| ⚠️ warn | Volatile, over 30 days old. |
| 🔴 stale | Over 60 days old — **blocked from the generator**. |

**Fix:** look the number up again, then use **Content Bank → Update an existing
number**. That stamps today's date and unblocks it.
        """)

    with st.expander("❌ Render failed"):
        st.markdown("""
**1. Chrome missing or moved.** Rendering needs the system Chrome at:
`C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe`
If Chrome lives somewhere else, update `CHROME` at the top of `footy_packs.py`.

**2. Cutout missing.** The error names the file. Create it with:
```
python make_cutout.py "Player Name"
```
Then check the result — background removal sometimes returns a team photo, a
document, or the wrong person entirely. Always look at the PNG before using it.

**3. Node modules missing** (after a fresh clone):
```
cd remotion-footy
npm install
```
        """)

    with st.expander("❌ Upload went to the wrong channel"):
        st.markdown("""
It cannot. `channels.py` reads the real channel ID back from the token and
compares it to the registry before uploading. A mismatch raises an error and the
upload never starts.

`ThechyoGyan` is on a permanent block list and can never receive an upload.

If the guard *does* fire, the token is pointing at the wrong channel — re-run
`python auth_channel.py <label>` and pick correctly this time.
        """)

    with st.expander("📉 Views dropped to almost nothing"):
        st.markdown("""
This happened to Footy Gyaan in August 2026: from ~4,000 views a day to under 10.

**What it was not:** content quality. Retention was 176–255% and click-through
was 8× the channel average. When the videos were shown, they performed.

**What it was:** distribution. Impressions per new video fell from 517 to 7.
YouTube simply stopped showing the channel to non-subscribers — and 99.9% of all
views had always come from non-subscribers.

**Worth knowing:** subscribers are almost irrelevant on Shorts. During the
channel's best week, 56 subscribers produced 14 views in total. Chasing
subscribers does not fix this; only getting back into the feed does.

**The only lever:** upload every single day without a gap, and give it weeks.
If that does not move it, the next step is a different channel — not more tweaking.
        """)

    with st.expander("🎥 Making a Veo video (Below The Blue)"):
        st.markdown("""
Veo clips are made by hand, then assembled here.

1. **Clip 1** — Text to Video, using the full scene prompt.
2. **Clips 2 and 3** — Frame to Video, starting from the **last frame** of the
   previous clip. This keeps the colour, grain and camera motion continuous;
   three independent generations never match.
3. Put the clips in `output/blue/` as `drop1.mp4`, `drop2.mp4`, `drop3.mp4`.
4. Run `python stitch_drop.py` — it upscales, crops out the Veo watermark,
   trims each clip and cross-dissolves them into one continuous descent.
5. Render the composition in Remotion to lay the data on top.

**Prompt tips learned the hard way:** name every unwanted element explicitly
("no sunlight, no god rays, no divers, no text"). Saying "no lights" with nothing
else backfires — the model invents a sun to light the scene, and a sunlit sea
floor contradicts a video about total darkness.
        """)

    with st.expander("🎵 Music and copyright"):
        st.markdown("""
All music is generated by `make_score.py`, not downloaded. Nothing in it belongs
to anyone else, so there is nothing to claim and nothing to attribute.

Each format has its own score, timed to that format's beats — the quiz score hits
on the countdown ticks and the reveal; the descent score builds pressure and lands
on the bottom. A library track cannot do that because it does not know the edit.

**Do not** add a copyrighted song in the Shorts editor. That earns a Content ID
claim: no revenue, and blocked in some countries. This channel already had one.

If you do want library music, use **YouTube's own Audio Library**
(`studio.youtube.com → Audio Library`) — YouTube licenses it, so a claim is
impossible. Other "free" libraries are not always safe.
        """)

    with st.expander("🖼️ Photo credits and licensing"):
        st.markdown("""
Player cutouts come from Wikimedia Commons. Many are **CC BY-SA**, which legally
requires attribution.

Every credit is recorded in `data/cutout_credits.json`. When a video uses those
images, keep the credit line in the description. Removing it is exactly the kind
of thing that turns into a claim later.
        """)

    with st.expander("💥 Streamlit will not start"):
        st.markdown("""
```
pip install -r requirements.txt
pip install streamlit rembg onnxruntime
```
Then run `streamlit run studio_app.py`, or double-click `studio.bat`.

If a port is stuck, use another one:
```
streamlit run studio_app.py --server.port 8502
```
        """)

    st.divider()
    st.subheader("The daily routine")
    st.markdown("""
1. Open Studio. Read **Overview** — it says whether today's upload has happened.
2. Go to **Queue** and press **Generate + Render**.
3. Watch the video. **Read every number against its source.** This is the only
   step that cannot be automated, and it is the step that has caught every
   serious error so far.
4. Edit the title if you want to, choose the channel, press **Approve + Upload**.
5. Pin the first comment on YouTube straight away.

**Upload in the morning window, 10 AM – 1 PM.** The channel's own data puts the
median at 568 views in that window against 55 in the evening.
    """)
