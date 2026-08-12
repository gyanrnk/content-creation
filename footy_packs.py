"""
footy_packs.py — Remotion shorts ka GENERATOR + RENDER + QUEUE.

Flow:
    generate()  -> data/pack_queue.json me "pending" pack daalta he
    render()    -> pack ko output/packs/<id>.mp4 me render karta he
    approve()   -> TERE click pe (footy_studio.py)
    publish()   -> approve ke turant baad YouTube

TEEN NIYAM jo code me hi bandhe he:

1. KOI LLM NUMBER NAHI. Har stat data/stat_bank.json se aata he jahan source +
   as_of likha he. Jis metric pe dono players ka verified number nahi, wo duel
   banta hi nahi.

2. NOVELTY GATE. Sirf "same combo dobara nahi" kaafi nahi tha — usse har video
   ek jaisi lagti thi. Ab teen shart:
      - format lagataar repeat nahi (rotation)
      - pichhle COOLDOWN packs ka headliner dobara headline nahi karega
      - exact signature kabhi repeat nahi (all-time)

3. 20s CAP. Channel data: 33s video ki retention 36% pe gir gayi thi.

Chalao:
    python footy_packs.py generate 3
    python footy_packs.py list
"""

import os
import re
import sys
import json
import random
import subprocess
import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
BANK_PATH = os.path.join(ROOT, "data", "stat_bank.json")
QUEUE_PATH = os.path.join(ROOT, "data", "pack_queue.json")
REMOTION_DIR = os.path.join(ROOT, "remotion-footy")
PACKS_DIR = os.path.join(ROOT, "output", "packs")
CUT_DIR = os.path.join(REMOTION_DIR, "public", "cut")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
MAX_SECONDS = 20.0
FPS = 30
COOLDOWN = 3          # itne packs tak wahi headliner dobara headline nahi karega


# ── queue io ─────────────────────────────────────────────────────────────────
def load_queue() -> list:
    if not os.path.exists(QUEUE_PATH):
        return []
    with open(QUEUE_PATH, encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_queue(packs: list):
    os.makedirs(os.path.dirname(QUEUE_PATH), exist_ok=True)
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(packs, f, ensure_ascii=False, indent=2)


def load_bank() -> dict:
    with open(BANK_PATH, encoding="utf-8") as f:
        return json.load(f)


def _set_status(pack_id: str, status: str, **extra):
    packs = load_queue()
    for p in packs:
        if p["id"] == pack_id:
            p["status"] = status
            p.update(extra)
    save_queue(packs)
    return packs


def approve(pack_id: str):
    return _set_status(pack_id, "approved",
                       approved_at=datetime.datetime.now().isoformat(timespec="seconds"))


def reject(pack_id: str):
    return _set_status(pack_id, "rejected")


def mark_published(pack_id: str, url: str):
    return _set_status(pack_id, "published", youtube_url=url,
                       published_at=datetime.datetime.now().isoformat(timespec="seconds"))


# ── novelty gate ─────────────────────────────────────────────────────────────
def _recent(n: int) -> list:
    """Rejected chhod ke, sabse naye n packs (title dedup ke liye)."""
    live = [p for p in load_queue() if p["status"] != "rejected"]
    return sorted(live, key=lambda p: p["created_at"], reverse=True)[:n]


def _recent_published(n: int) -> list:
    """Sirf wo packs jo ACTUALLY upload ho chuke.

    Rotation isi pe honi chahiye. Pehle ye _recent() dekhta tha, jisme queue me
    pade pending packs bhi aate the — natija: 8 aur 9 Aug dono din Guess chali
    gayi, kyunki beech me ek pending WhatIf baitha tha jisne gate ko laga diya
    ki format badal chuka he. Darshak ko pending pack dikhta hi nahi.
    """
    pub = [p for p in load_queue() if p["status"] == "published"]
    return sorted(pub, key=lambda p: p.get("published_at", p["created_at"]), reverse=True)[:n]


def _pack_numbers(pack: dict) -> list:
    """Pack ke saare stat numbers — channel-history clash check ke liye."""
    p, out = pack["props"], []
    for d in p.get("duels", []):
        out += [d["oldVal"], d["newVal"]]
    for s in p.get("swaps", []):
        out += [int(n) for n in re.findall(r"\d+", s.get("stat", ""))]
    for c in p.get("clues", []):
        out += [int(n) for n in re.findall(r"\d+", c)]
    for k in p.get("keepers", []):          # CleanSheet ranking format
        out.append(k["value"])
    return out


def _novel(fmt: str, signature: str, headliners: list) -> tuple[bool, str]:
    if any(p.get("signature") == signature for p in load_queue()):
        return False, "same signature pehle bhi bana"

    recent = _recent_published(COOLDOWN)
    if recent and recent[0].get("format") == fmt:
        return False, f"format '{fmt}' pichhli upload me hi gaya tha"

    hot = set()
    for p in recent:
        hot |= set(p.get("headliners", []))
    if headliners and set(headliners) <= hot:
        return False, f"headliners {headliners} pichhli {COOLDOWN} uploads me aa chuke"

    return True, ""


# ── live data ────────────────────────────────────────────────────────────────
def live_ranking() -> list:
    """stats.py se aaj ka LIVE ranking (golden boot ya league). [] agar fail."""
    try:
        import stats
        _topic, text = stats.current_stats()
    except Exception as e:
        print(f"[live] skip ({e})")
        return []
    out = []
    for line in str(text).splitlines():
        m = re.match(r"\s*\d+\.\s*(.+?)\s*\((.+?)\)\s*[—-]\s*(\d+)\s*(\w+)", line)
        if m:
            out.append({"name": m.group(1).strip(), "team": m.group(2).strip(),
                        "value": int(m.group(3)), "unit": m.group(4)})
    return out


def _live_clue_for(player_name: str) -> str | None:
    """Agar aaj ke live data me ye player he to ek CURRENT clue lauta do."""
    last = player_name.split()[-1].lower()
    for row in live_ranking():
        if last in row["name"].lower():
            return f"{row['value']} {row['unit']} at World Cup 2026"
    return None


# ── format builders ──────────────────────────────────────────────────────────
def _dur_era(n):    return 60 + n * 132 + 126 - (n * 14 + 10)
def _dur_whatif(n): return 54 + n * 126 + 120 - (n * 12 + 10)
DUR_GUESS = 40 + 3 * 75 + 45 + 150


def _have_cut(slug: str) -> bool:
    return os.path.exists(os.path.join(CUT_DIR, f"{slug}.png"))


def _build_era(bank: dict) -> dict | None:
    tpl = random.choice([t for t in bank["templates"]])
    players, metrics = bank["players"], bank["metrics"]
    allowed = tpl.get("metrics_only") or list(metrics.keys())

    opts = []
    for lk in tpl["left_pool"]:
        for rk in tpl["right_pool"]:
            if lk == rk:
                continue
            L, R = players[lk], players[rk]
            for m in allowed:
                if m in L["stats"] and m in R["stats"] and L["stats"][m] >= R["stats"][m]:
                    opts.append({"head": metrics[m]["head"],
                                 "oldFile": L["cut"], "oldName": L["name"], "oldVal": L["stats"][m],
                                 "newFile": R["cut"], "newName": R["name"], "newVal": R["stats"][m],
                                 "_m": m, "_l": lk, "_r": rk})
    random.shuffle(opts)
    duels, seen_m = [], set()
    for o in opts:
        if len(duels) >= 3:
            break
        if o["_m"] in seen_m:
            continue
        seen_m.add(o["_m"])
        duels.append(o)
    if len(duels) < 3:
        return None
    if any(not _have_cut(d["oldFile"]) or not _have_cut(d["newFile"]) for d in duels):
        return None

    winners = list(dict.fromkeys((d["oldFile"], d["oldName"]) for d in duels))
    faces = [w[0] for w in winners][:2]
    names = " + ".join(dict.fromkeys(w[1] for w in winners))

    lines = [f"{d['head'].title():<26} {d['oldName']} {d['oldVal']}  vs  "
             f"{d['newName']} {d['newVal']}   (+{d['oldVal'] - d['newVal']})" for d in duels]
    return {
        "format": "era", "composition": "EraBattle", "template": tpl["id"],
        "signature": "era|" + "|".join(sorted(f"{d['oldFile']}>{d['newFile']}:{d['_m']}" for d in duels)),
        "headliners": sorted({d["oldFile"] for d in duels}),
        "duration_s": round(_dur_era(len(duels)) / FPS, 1),
        "props": {
            "titleTop": tpl["titleTop"], "titleBottom": tpl["titleBottom"],
            "subtitle": tpl["subtitle"], "footer": tpl["footer"],
            "duels": [{k: v for k, v in d.items() if not k.startswith("_")} for d in duels],
            "score": f"{len(duels)} - 0", "finaleLine": tpl["finaleLine"],
            "finaleNames": names, "finaleFaces": faces,
            "bait": tpl["bait"], "baitSub": tpl["baitSub"],
        },
        "sources": {d["_l"]: players[d["_l"]]["source"] for d in duels}
                   | {d["_r"]: players[d["_r"]]["source"] for d in duels},
        "review_note": None,
        "youtube": {
            "title": tpl["yt_title"],
            "description": f"{tpl['yt_hook']}\n\n⚔️ THE NUMBERS\n" + "\n".join(lines) +
                           f"\n\n💬 {tpl['yt_question']}\n\nDaily football stats and rankings. "
                           f"Subscribe. ⚽\n\n" + " ".join(f"#{t}" for t in tpl["yt_tags"]),
            "tags": tpl["yt_tags"],
        },
    }


def _build_guess(bank: dict) -> dict | None:
    players = bank["players"]
    metrics = bank["metrics"]
    cands = [k for k, v in players.items() if _have_cut(v["cut"]) and len(v["stats"]) >= 2]
    if not cands:
        return None
    key = random.choice(cands)
    P = players[key]

    # Clue order = vague se giveaway tak. Warna "8 Ballon d'Ors" pehle clue me hi
    # jawab de deta he aur quiz khatam — countdown tak koi rukega hi nahi.
    # kam number = pehle dikhega (vague), zyada = giveaway, aakhir me
    GIVEAWAY = {"ucl_titles": 1, "intl_goals": 1, "ucl_goals": 2,
                "career_goals": 3, "red_cards_laliga": 4, "ballon_dor": 4}
    # 'clue' label use karo, 'label'.lower() nahi — warna "UCL goals" -> "ucl goals".
    scored = [(GIVEAWAY.get(m, 2), f"{v} {metrics[m].get('clue', metrics[m]['label'])}")
              for m, v in P["stats"].items()]
    live = _live_clue_for(P["name"])
    if live:
        scored.append((1, live))
    if len(scored) < 3:
        return None
    scored.sort(key=lambda x: x[0])
    clues = [c for _, c in scored[:3]]

    return {
        "format": "guess", "composition": "GuessPlayer", "template": "guess_player",
        "signature": "guess|" + key + "|" + "|".join(sorted(clues)),
        "headliners": [P["cut"]],
        "duration_s": round(DUR_GUESS / FPS, 1),
        "props": {
            "category": "GUESS THE PLAYER",
            "clues": clues,
            "answerFile": P["cut"], "answerName": P["name"],
            "answerLine": P.get("tag", "THE LEGEND 🏆"),
            "bait": "GOT IT? 👇", "baitSub": "COMMENT KARO 🔥",
        },
        "sources": {key: P["source"]},
        "review_note": None,
        "youtube": {
            "title": f"Guess the Player 🤔 3 Clues, Can You Get It? ⚽ #shorts",
            "description": ("Three clues. One player. Most people need all three. 👀\n\n"
                            "🔍 THE CLUES\n" + "\n".join(f"• {c}" for c in clues) +
                            "\n\n💬 Did you get it before the reveal? Comment below. 👇\n\n"
                            "Daily football quizzes and stats. Subscribe. ⚽\n\n"
                            "#football #footballquiz #guesstheplayer #shorts #quiz"),
            "tags": ["football", "footballquiz", "guesstheplayer", "quiz", "shorts"],
        },
    }


def _build_whatif(bank: dict) -> dict | None:
    players, clubs = bank["players"], bank["clubs"]
    metrics = bank["metrics"]
    movable = [k for k, v in players.items() if v.get("club") and _have_cut(v["cut"])]
    if len(movable) < 3:
        return None
    picked = random.sample(movable, 3)

    swaps = []
    used_dest = set()          # ek video me do bande same club nahi ja sakte
    for k in picked:
        P = players[k]
        dests = [c for c in clubs if c != P["club"] and c not in used_dest]
        if not dests:
            return None
        to = random.choice(dests)
        used_dest.add(to)
        # Stat = us player ki SABSE MAZBOOT cheez, random nahi. Aur zero kabhi nahi:
        # "0 Ballon d'Ors" selling point ki jagah kamzori dikhata he.
        PREF = ["career_goals", "ucl_goals", "intl_goals", "ballon_dor"]
        usable = [(k, v) for k, v in P["stats"].items() if v > 0]
        if not usable:
            return None
        usable.sort(key=lambda kv: PREF.index(kv[0]) if kv[0] in PREF else 99)
        m, val = usable[0]
        swaps.append({"player": P["cut"], "name": P["name"], "from": P["club"],
                      "to": to, "toColor": clubs[to],
                      "stat": f"{val} {metrics[m].get('clue', metrics[m]['label'])}", "_k": k})

    lines = [f"{s['name']}: {s['from']} → {s['to']}  ({s['stat']})" for s in swaps]
    return {
        "format": "whatif", "composition": "WhatIf", "template": "what_if",
        "signature": "whatif|" + "|".join(sorted(f"{s['_k']}>{s['to']}" for s in swaps)),
        "headliners": sorted(s["player"] for s in swaps),
        "duration_s": round(_dur_whatif(len(swaps)) / FPS, 1),
        "props": {
            "title": "WHAT IF?", "subtitle": "Imaginary moves. Real numbers. 👀",
            "swaps": [{k: v for k, v in s.items() if not k.startswith("_")} for s in swaps],
            "footer": "IMAGINARY TRANSFER · REAL STATS",
            "finaleLine": "WHICH ONE BREAKS THE LEAGUE?",
            "bait": "PICK ONE 👇", "baitSub": "COMMENT KARO 🔥",
        },
        "sources": {s["_k"]: players[s["_k"]]["source"] for s in swaps},
        # Club field factual he — review pe ek nazar zaroori.
        "review_note": "Clubs check kar lo (bank ke 'club' field se aaye he). "
                       "Transfers KALPANIK he — video pe label laga hua he.",
        "youtube": {
            "title": "WHAT IF these transfers were REAL? 👀🔥 #shorts",
            "description": ("Imaginary moves — but every stat attached is real. 👀\n\n"
                            "🔄 THE MOVES\n" + "\n".join(f"• {l}" for l in lines) +
                            "\n\n(These transfers are hypothetical — just for fun.)\n\n"
                            "💬 Which one would break the league? Pick one. 👇\n\n"
                            "Daily football what-ifs and stats. Subscribe. ⚽\n\n"
                            "#football #transfers #whatif #shorts #footballshorts"),
            "tags": ["football", "transfers", "whatif", "shorts", "footballshorts"],
        },
    }


def _build_rank(bank: dict) -> dict | None:
    """CleanSheet format — koi bhi verified ranking, alag visual language me."""
    ranks = bank.get("rankings") or []
    ranks = [r for r in ranks if all(_have_cut(e["file"]) for e in r["entries"])]
    if not ranks:
        return None
    r = random.choice(ranks)
    ents = sorted(r["entries"], key=lambda e: -e["rank"])   # 3 -> 1
    top = ents[-1]

    lines = [f"#{e['rank']}  {e['name']:<10} {e['value']} — {e['club']}" for e in sorted(r["entries"], key=lambda e: e["rank"])]
    return {
        "format": "rank", "composition": "CleanSheet", "template": r["id"],
        "signature": "rank|" + r["id"] + "|" + "|".join(f"{e['file']}:{e['value']}" for e in ents),
        "headliners": [top["file"]],
        "duration_s": round((50 + len(ents) * 110 + 120 - (len(ents) * 12 + 10)) / FPS, 1),
        "props": {
            "kicker": r["kicker"], "title": r["title"], "subtitle": r["subtitle"],
            "unit": r["unit"], "footer": r["footer"],
            "keepers": [{k: v for k, v in e.items()} for e in ents],
            "max": max(e["value"] for e in ents),
            "finaleLine": r["finaleLine"], "bait": r["bait"], "baitSub": r["baitSub"],
        },
        "sources": {r["id"]: r["source"]},
        "review_note": None,
        "youtube": {
            "title": random.choice(r["yt_titles"]),
            "description": (f"{r['yt_hook']}\n\n🧤 {r['footer']}\n" + "\n".join(lines) +
                            f"\n\n💬 {r['yt_question']}\n\nDaily football records and stats. "
                            f"Subscribe. ⚽\n\n" + " ".join(f"#{t}" for t in r["yt_tags"])),
            "tags": r["yt_tags"],
        },
    }


BUILDERS = {"era": _build_era, "guess": _build_guess,
            "whatif": _build_whatif, "rank": _build_rank}

# Ek hi title baar-baar = wahi sameness jo content me thi. Har pack ke liye
# aisa title chuno jo pichhle packs me use na hua ho.
TITLE_POOL = {
    "guess": [
        "Guess the Player 🤔 3 Clues, Can You Get It? ⚽ #shorts",
        "3 Clues, 1 Legend 🤔 Did You Get It? ⚽ #shorts",
        "Only Real Fans Get This in 3 Clues 👀⚽ #shorts",
        "Can You Name Him From 3 Numbers? 🤔🐐 #shorts",
        "Guess the Player 👑 Most People Need All 3 Clues ⚽ #shorts",
    ],
    "whatif": [
        "WHAT IF these transfers were REAL? 👀🔥 #shorts",
        "3 Transfers That Would BREAK Football 😱⚽ #shorts",
        "WHAT IF? 🔄 Imaginary Moves, Real Numbers 🔥 #shorts",
        "These Transfers Would Change Everything 👀🔥 #shorts",
        "WHAT IF Your Club Signed HIM? 😱⚽ #shorts",
    ],
    "era": [
        "Golden Era vs New Era ⚔️ Can They EVER Catch Up? 👑 #shorts",
        "The Gap Nobody Talks About ⚔️🐐 #shorts",
        "3 Records. One Winner. ⚔️👑 #shorts",
        "These Numbers End the Debate 🐐🔥 #shorts",
        "Who Actually Wins on the Numbers? ⚔️👑 #shorts",
    ],
}


def _fresh_title(fmt: str, fallback: str) -> str:
    used = {p.get("youtube", {}).get("title") for p in _recent(8)}
    pool = TITLE_POOL.get(fmt) or [fallback]
    free = [t for t in pool if t not in used]
    return random.choice(free or pool)


def _next_formats() -> list:
    """Rotation — jo format sabse pehle PUBLISH hua tha wo pehle aayega."""
    recent = [p.get("format") for p in _recent_published(10)]
    order = sorted(BUILDERS, key=lambda f: recent.index(f) if f in recent else 99, reverse=True)
    return order


# ── generation ───────────────────────────────────────────────────────────────
def generate(count: int = 1) -> list:
    bank = load_bank()
    made = []
    blocked = []

    # Stale volatile entries hata do — inka number badal chuka ho sakta he.
    # (12 Aug: Ronaldo ke intl goals 143 se 146 ho gaye the aur bank ko pata
    #  hi nahi tha. Ab purani entry se pack ban hi nahi sakta.)
    try:
        import bank_check
        stale = bank_check.blocked_keys()
        if stale:
            bank = json.loads(json.dumps(bank))          # copy, file ko haath nahi
            bank["players"] = {k: v for k, v in bank["players"].items() if k not in stale}
            bank["rankings"] = [r for r in bank.get("rankings", []) if r["id"] not in stale]
            print(f"[bank] {len(stale)} stale entries skip: {sorted(stale)}")
    except Exception as e:
        print(f"[bank] freshness check skip ({e})")

    for _ in range(count * 12):
        if len(made) >= count:
            break
        for fmt in _next_formats():
            pack = BUILDERS[fmt](bank)
            if not pack:
                continue
            if pack["duration_s"] > MAX_SECONDS:
                continue
            ok, why = _novel(pack["format"], pack["signature"], pack["headliners"])
            if not ok:
                blocked.append(why)
                continue

            # Channel pe pehle se aisi hi video to nahi? (9 Aug: 976/919/143/125/
            # 140/129 wala pack ban gaya tha jabki 6 Aug ki video me wahi teen
            # comparisons the — queue-only gate use pakad hi nahi sakta tha.)
            try:
                import channel_history
                cl = channel_history.clash(_pack_numbers(pack))
            except Exception as e:
                print(f"[history] check skip ({e})")
                cl = None
            if cl:
                blocked.append(f"channel pe pehle se he — {cl['video']['published']} "
                               f"'{cl['video']['title'][:38]}' (same: {cl['hits']})")
                continue

            pack["youtube"]["title"] = _fresh_title(pack["format"], pack["youtube"]["title"])
            pack.update({
                "id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{random.randint(100, 999)}",
                "status": "pending",
                "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "bank_as_of": bank["as_of"],
                "video": None,
            })
            q = load_queue()
            q.append(pack)
            save_queue(q)
            made.append(pack)
            break

    if not made and blocked:
        print("[novelty] sab reject:", "; ".join(dict.fromkeys(blocked[-4:])))
    return made


# ── render ───────────────────────────────────────────────────────────────────
def render(pack: dict, quiet: bool = True) -> str:
    os.makedirs(PACKS_DIR, exist_ok=True)
    out = os.path.join(PACKS_DIR, f"{pack['id']}.mp4")
    props_file = os.path.join(PACKS_DIR, f"{pack['id']}.props.json")
    with open(props_file, "w", encoding="utf-8") as f:
        json.dump(pack["props"], f, ensure_ascii=False)

    cmd = ["npx", "remotion", "render", pack["composition"], out,
           f"--props={props_file}", f"--browser-executable={CHROME}"]
    r = subprocess.run(cmd, cwd=REMOTION_DIR, shell=True, capture_output=quiet, text=True)
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "")[-800:] if quiet else ""
        raise RuntimeError(f"remotion render fail (rc={r.returncode})\n{tail}")

    packs = load_queue()
    for p in packs:
        if p["id"] == pack["id"]:
            p["video"] = out
    save_queue(packs)
    return out


# ── cli ──────────────────────────────────────────────────────────────────────
def _cli():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "generate":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        made = generate(n)
        if not made:
            print("[generate] kuch naya nahi bana — stat_bank.json me naya player/metric daalo.")
            return
        for p in made:
            print(f"[generate] {p['id']}  {p['format']:<7} {p['duration_s']}s  "
                  f"headliners={p['headliners']}")
            print("           rendering...")
            try:
                print(f"           ✅ {render(p)}")
            except Exception as e:
                print(f"           ❌ {e}")
    elif cmd == "list":
        for p in load_queue():
            mark = {"pending": "⏳", "approved": "✅", "published": "📤", "rejected": "🗑️"}.get(p["status"], "?")
            print(f"{mark} {p['id']}  {p['status']:<10} {p.get('format', '?'):<7} "
                  f"{p['duration_s']}s  {p['youtube']['title'][:42]}")
    else:
        print(__doc__)


if __name__ == "__main__":
    _cli()
