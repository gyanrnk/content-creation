"""
script.py — Football World Cup short ka script generate karta hai.

Output: ek structured dict jisme har segment ke liye:
  - voice_hindi      : Hindi narration (TTS ke liye)
  - subtitle_english : English subtitle (screen par burn hoga)
  - image_source     : "real" (Wikimedia/Pexels) ya "ai" (Pollinations)
  - image_query      : real photo dhoondhne ke liye search words
  - ai_prompt        : agar ai image chahiye to detailed prompt

Plus: title_hindi, hook_english (opening text), cta_english (end text).
"""

import os
import json
from dotenv import load_dotenv

import config

load_dotenv()


# ── Mode-specific guidance ──────────────────────────────────────────────────────
MODE_GUIDE = {
    "stats": (
        "A GOALS-SCORED RACE (Golden Boot = MOST goals in the tournament) from the REAL "
        "numbers in the facts above. CRITICAL LOGIC: more goals = LEADING the race; fewer "
        "goals = just BEHIND, NOT 'lost', NOT 'knocked out', NOT 'haar gaya'. Nobody "
        "loses a match here — it is a scoring chart. Being 2nd means close behind, not "
        "defeated. Reveal from FEWEST goals up to the MOST (build to the leader last). "
        "For EACH player give a DIFFERENT angle — not just the number: their team, their "
        "age, how close the gap is, or a standout detail — so no two lines sound the same. "
        "If the top two are TIED, say they are NECK-AND-NECK / joint leaders (exciting), "
        "and the gap is ZERO — never claim a gap that is not in the data. End on who is on "
        "top right now + one punchy line about the race."
    ),
    "facts": (
        "A gripping mini-story built around ONE football topic/event. Weave "
        "surprising facts into a flowing narrative (not a disconnected list) that "
        "builds curiosity and pays off near the end."
    ),
    "player": (
        "Spotlight on the player/team in the topic. Cover their journey, key "
        "stats, iconic moments — fast and exciting."
    ),
    "preview": (
        "MATCH PREVIEW + PREDICTION. Structure: seg1 hook the matchup; next "
        "segments COMPARE famous legendary players of BOTH teams (real names, "
        "stats, achievements) and head-to-head history; the LAST segment names a "
        "predicted LIKELY winner with a REASON. Do NOT invent an exact scoreline "
        "(no fake 'will win 2-1') and only predict matches that have NOT happened "
        "yet. For player/team segments set image_type 'real' and put the real "
        "player or team name in image_query."
    ),
    "quiz": (
        "GUESS-THE-PLAYER quiz. Pick ONE famous mystery player. Segments 1..(N-2) give "
        "ESCALATING CLUES (nationality, then club, then a big record/stat) WITHOUT ever "
        "naming them — build suspense and tell the viewer to guess. "
        "*** SECOND-LAST segment = the GUESS-LOCK: give the final/biggest clue AND tell "
        "them to lock their guess in the comments NOW, before the reveal (e.g. 'Naam pata "
        "chal gaya? Abhi comment karo — phir reveal!'). This is where comments come from. *** "
        "The FINAL segment REVEALS the name dramatically (this is why viewers stay to the "
        "end — never skip the reveal). *** For every CLUE segment (incl. the guess-lock) "
        "set image_type 'ai' and image_query a mysterious hidden vibe (e.g. 'mysterious "
        "football player silhouette in dark stadium') — do NOT reveal the player. ONLY the "
        "final reveal segment gets image_type 'real' with the player's exact name. ***"
    ),
    "debate": (
        "CAREER COMPARISON of TWO named players (e.g. Ronaldo vs Messi). Compare their "
        "SEPARATE careers — trophies, goals, style, iconic moments — one player per "
        "segment, alternating. Stay BALANCED to spark argument; last segment asks the "
        "viewer to decide ('aap batao'). *** DO NOT invent a match between them or fake "
        "scores/minutes/results — they may play for different countries/clubs and may "
        "never have faced each other. It is a COMPARISON, not a match report. *** "
        "Every segment: image_type 'real', relevant player name in image_query (alternate)."
    ),
    "ranking": (
        "TOP-5 style COUNTDOWN. Rank from #5 up to #1 (best/biggest LAST for suspense). "
        "Tease that #1 will shock them in the hook. Each ranked segment states the rank "
        "number + who + a SPECIFIC concrete reason (a real stat, trophy, record, or iconic "
        "moment — e.g. 'scored 800+ career goals', 'bent that free-kick vs Greece'). "
        "*** BANNED lazy/circular reasons: 'his skills are praised', 'is very good', 'is "
        "talented', 'everyone loves him', 'is amazing' — these say NOTHING. Give a real "
        "why. *** Every ranked segment: image_type 'real' with that player's exact name."
    ),
    "story": (
        "RAGS-TO-RICHES emotional player JOURNEY. ONE player. Arc: humble/struggling "
        "start → obstacles & setbacks → breakthrough → triumph/legacy. Deeply emotional, "
        "cinematic narration that makes viewers feel it. Use image_type 'ai' for early/"
        "childhood/struggle scenes (e.g. 'poor kid playing football on a dusty street at "
        "sunset') and image_type 'real' with the player's name for their career/peak."
    ),
}


def _build_messages(topic: str, mode: str, num_segments: int, context: str = ""):
    """
    Compact prompt — free reasoning-model ke liye chhota rakhna zaroori hai,
    warna wo sirf 'sochta' rehta hai aur JSON deta nahi.
    """
    mode_text = MODE_GUIDE.get(mode, MODE_GUIDE["facts"])

    system = "You are a JSON generator. Output ONLY a JSON object, no explanation."

    ground = ""
    if context:
        ground = (
            "VERIFIED FACTS (real — from today's news and/or Wikipedia. Treat as "
            "GROUND TRUTH; base the script ONLY on these, do not add unverified claims):\n"
            f"{context}\n"
            "RULES: Do NOT say anything that contradicts these facts. If a player or "
            "team has been knocked out/eliminated, do NOT imply they are still "
            "competing or will win the 2026 World Cup. For eliminated stars, frame as "
            "career/legacy (not current tournament). "
            "In a scoreline 'Team A 0-1 Team B', the team with the HIGHER number WON "
            "(here Team B beat Team A) — state the winner correctly. "
            "If an event has ALREADY happened per these facts, do NOT ask 'who will "
            "win?' or say 'X will win' — describe the ACTUAL result in past tense. "
            "Do NOT invent specific numbers (goals, assists, scores, records) that are "
            "not stated in the facts above; if unsure, make a general statement or use "
            "a timeless historical fact instead. "
            "*** The video MUST be about a REAL event listed in these facts — do NOT "
            "invent a different match, opponent, score or event that is not supported "
            "here (e.g. do not make up an 'Argentina vs Egypt' match if it's not in the "
            "facts). ***\n\n"
        )

    user = (
        ground +
        f"Write a {num_segments}-part football short narration. Topic: {topic}.\n"
        f"Style: {mode_text}\n"
        'JSON shape: {"title_english":"..","hook_english":"..","cta_english":"..",'
        '"segments":[{"voice_english":"..",'
        '"image_query":"..","image_type":"real|ai"}]}\n'
        f"- Exactly {num_segments} segments.\n"
        "*** MOST IMPORTANT: all segments must tell ONE connected STORY about a "
        "SINGLE main subject/event — with a clear flow: hook -> build-up -> "
        "emotional climax -> closing thought. Each segment must CONTINUE from the "
        "previous one (like a narrator telling one story). Do NOT list unrelated "
        "facts and do NOT jump between different matches or players. Pick the ONE "
        "most interesting angle and stay on it the whole video. ***\n"
        "*** ENTERTAINMENT: make it DRAMATIC and exciting like a hyped fan telling a "
        "juicy story — build suspense, raise the stakes, add an emotional or surprising "
        "TURN in the middle ('but then...'), and make the viewer feel it. Not a dry "
        "report. Keep the WORDS simple, but the STORY gripping and full of energy. ***\n"
        "*** WORD COUNT — STRICT BAND: every voice_english must be 13 to 17 words. "
        "COUNT them. Under 13 words = a bare FRAGMENT (WRONG — boring, no detail). "
        "Over 17 words = a RUN-ON (WRONG — video too long). Use EXACTLY ONE connector "
        "(but / so / after / when / because) — one connector, then STOP. Never chain "
        "'and ... and ... because ...'. ***\n"
        "*** NO REPEATED STRUCTURE: each segment must use a DIFFERENT sentence shape and "
        "add a NEW concrete detail — a reason, comparison, age, year, or surprising angle. "
        "Writing the SAME template five times (e.g. 'X has N goals, but who is higher?' "
        "again and again) is BANNED and boring. Do not just restate the number — say "
        "something INTERESTING about it. ***\n"
        "- voice_english = ONE FULL sentence in SIMPLE, PLAIN, everyday spoken "
        "ENGLISH, 12-16 words long (short & punchy for a fast Short), the way a normal "
        "person casually tells a friend what happened. *** It MUST be a full sentence "
        "with 2 connected clauses "
        "joined by simple words like 'but', 'and', 'so', 'after', 'when', 'because' "
        "— NEVER a short 5-8 word fragment. *** Use CONCRETE facts (exact minute, "
        "score, player age, stadium, nickname like 'CR7'). Use only SHORT COMMON "
        "words; do NOT use fancy/flowery/literary words — NO 'fairy tale', "
        "'illustrious', 'end of an era', 'true icon', 'bids farewell', 'tribute', "
        "'legacy'. Say plain things like 'dream ended', 'lost', 'cried', 'scored', "
        "'last match', 'career', 'said goodbye'. This English gets auto-translated to "
        "Hindi, so plain words = clean natural Hindi. GOLD EXAMPLE (copy this LENGTH "
        "and plainness): 'Ronaldo played the full 90 minutes, but Merino scored in "
        "the 91st minute and knocked Portugal out, and everyone saw him cry at the "
        "end.' Every segment must be this full and this simple.\n"
        "*** SPECIFIC & THRILLING (romanchak) — YEH views decide karta hai: ***\n"
        "- BANNED boring filler (in me se kuch bhi mat likho): 'worked hard', 'faced "
        "many obstacles', 'faced setbacks', 'won many awards', 'became a legend', "
        "'changed football', 'people still talk about him', 'the best player', "
        "'everyone knew his name', 'rose to greatness', 'never gave up'. Ye generic "
        "aur boring hai — viewer swipe kar dega.\n"
        "- INSTEAD: har segment ek SPECIFIC, chaunka dene wala, thos fact de (VERIFIED "
        "FACTS se): asli event ka naam, exact number/stat, saal, transfer fee/club, ek "
        "record, ya ek dramatic pal. Viewer ko kuch NAYA batao jo use nahi pata tha.\n"
        "- ARC (tension banao): seg1 = chaunka dene wali hook line; beech me ek SPECIFIC "
        "low-point/rejection AUR ek surprising TURN ('but then, in <year>, he...'); "
        "end = triumph ek asli number ke saath, hook se wapas judte hue. Har line stakes "
        "badhaye.\n"
        "- Koi bhi shabd ya idea 2 baar repeat mat karo — har line kahani ko aage badhaye.\n"
        "- image_query = for 'real' put the player's FULL unambiguous name so the "
        "right photo is found — 'Cristiano Ronaldo' (NOT just 'Ronaldo', which also "
        "means the Brazilian Ronaldo), 'Lionel Messi', 'Kylian Mbappe'. For teams use "
        "'<Country> national football team'. For 'ai' put a vivid visual scene "
        "(e.g. 'dramatic football stadium fireworks night').\n"
        "- image_type = 'real' ONLY when a specific real famous person/team/stadium "
        "is named; otherwise 'ai'. Prefer 'ai' for abstract/atmospheric segments.\n"
        "*** GROWTH RULES (for max views — apply to EVERY video): ***\n"
        "- Segment 1 = a SCROLL-STOPPING HOOK — 50-60% viewers swipe in the first 3 "
        "SECONDS, so the FIRST 3-4 WORDS must hit: a bold/shocking claim OR a curiosity-"
        "gap question that promises a payoff. Lead with the most surprising fact or the "
        "biggest name. NO intro, NO 'aaj hum baat karenge', NO greeting, NO slow build — "
        "jump straight into the punch. Withhold the payoff/answer for later segments. "
        "Good: 'Sirf ek player ne ye kiya...', 'Messi ka ye record koi nahi tod paaya...'. "
        "Bad: 'Football me bahut se players hain...' (slow, generic).\n"
        "- LOOP: the LAST segment must connect back to the hook (echo segment 1's "
        "question/theme) so the video replays seamlessly — do NOT introduce a new topic.\n"
        "- CONCLUSION (punchy, yaad rehne wala): the LAST segment must END with a SHORT "
        "mic-drop line — a bold verdict or one killer stat that LANDS (e.g. 'Sirf 2 goal "
        "ka fark — aur Golden Boot daav pe hai.'). NO weak fade-out like 'his legacy will "
        "live on' / 'time will tell'. Viewer ko ek line yaad reh jaani chahiye.\n"
        "- hook_english = 3-6 word punchy on-screen title (the hook, big text).\n"
        "- cta_english = a SPECIFIC opinion question that begs a comment (NOT generic "
        "'follow for more'). E.g. 'Messi ya Ronaldo? Comment karo', 'Isko 1-10 rate karo', "
        "'Aap kya sochte ho?'. Make it about THIS video's topic.\n"
        "- Do NOT invent quotes or statements attributed to real people (pundits, "
        "coaches, players) unless given in the facts above.\n"
        + ("*** QUIZ MODE SPECIAL: hook_english and title_english must NOT reveal or "
           "name the mystery player — keep them a teaser like 'Guess this player!' / "
           "'Pehchaan kaun?'. The name appears ONLY in the final reveal segment. ***\n"
           if mode == "quiz" else "")
        + "Output JSON only. /no_think"   # /no_think = free reasoning-model ko seedha JSON dene par majboor karta hai
    )
    return system, user


_UNITS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
          "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
          "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
          "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
         "seventy": 70, "eighty": 80, "ninety": 90}
_ORD = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
        "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
        "eleventh": 11, "twelfth": 12, "twentieth": 20, "thirtieth": 30,
        "fortieth": 40, "fiftieth": 50, "sixtieth": 60, "ninetieth": 90}


def _words_to_digits(text: str) -> str:
    """'two hundred and thirty-two matches' -> '232 matches' (stat cards + clean captions)."""
    import re as _re
    words = (list(_UNITS) + list(_TENS) + ["hundred", "thousand", "million"]
             + list(_ORD))
    nw = "(?:" + "|".join(sorted(words, key=len, reverse=True)) + ")"
    pat = _re.compile(r"\b" + nw + r"(?:[\s\-]+(?:and[\s\-]+)?" + nw + r")*\b",
                      _re.I)

    def _parse(ws):
        total, cur = 0, 0
        for w in ws:
            if w == "and":
                continue
            if w in _UNITS:
                cur += _UNITS[w]
            elif w in _TENS:
                cur += _TENS[w]
            elif w in _ORD:
                cur += _ORD[w]
            elif w == "hundred":
                cur = (cur or 1) * 100
            elif w == "thousand":
                total += (cur or 1) * 1000
                cur = 0
            elif w == "million":
                total += (cur or 1) * 1000000
                cur = 0
        return total + cur

    # sirf tab digit banao jab: bada number (hundred/thousand) HO, YA aage stat-word ho
    # (warna "first time" -> "1 time" jaisa galat na ho)
    stat_after = {"goal", "goals", "match", "matches", "trophy", "trophies",
                  "title", "titles", "year", "years", "cup", "cups", "cap", "caps",
                  "win", "wins", "record", "records", "medal", "medals", "final",
                  "finals", "assist", "assists", "appearance", "appearances"}
    out, last = [], 0
    for m in pat.finditer(text):
        phrase = m.group(0)
        ws = [w for w in _re.split(r"[\s\-]+", phrase.lower()) if w]
        has_scale = any(w in ("hundred", "thousand", "million") for w in ws)
        after = _re.findall(r"[a-zA-Z]+", text[m.end():m.end() + 40])[:2]
        near_stat = any(w.lower() in stat_after for w in after)
        out.append(text[last:m.start()])
        out.append(str(_parse(ws)) if (has_scale or near_stat) else phrase)
        last = m.end()
    out.append(text[last:])
    return "".join(out)


def _gtranslate(text: str, sl: str = "hi", tl: str = "en", tries: int = 4) -> str:
    """Free Google Translate (no key). Retry-with-backoff (batch me 429 se bachne ke liye).

    IMPORTANT: en->hi me agar fail ho to English hi return hota tha -> Remy English
    bol deti thi (invisible bug). Ab retry karta hai; har fail par thodा rukta hai.
    """
    import requests
    import time
    if not text or not text.strip():
        return text
    last_err = "?"
    for attempt in range(tries):
        try:
            r = requests.get("https://translate.googleapis.com/translate_a/single",
                             params={"client": "gtx", "sl": sl, "tl": tl, "dt": "t",
                                     "q": text},
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            if r.status_code == 200:
                out = "".join(seg[0] for seg in r.json()[0]).strip()
                if out:
                    return out
                last_err = "empty"
            else:
                last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)
        time.sleep(1.5 * (attempt + 1))   # backoff: 1.5s, 3s, 4.5s...
    print(f"[script] translate FAILED after {tries} tries ({last_err}) — "
          f"WARNING: text un-translated rahega")
    return text


# Football naam jinhe voice me LATIN (English) hi rakhna hai — Devanagari me transcribe
# karne se Remy ajeeb bolti hai ("क्रिस्टियानो रोनाल्डो" vs "Cristiano Ronaldo").
_KEEP_LATIN = [
    "Cristiano Ronaldo", "Lionel Messi", "Kylian Mbappe", "Erling Haaland",
    "Diego Maradona", "Mohamed Salah", "Wayne Rooney", "Mikel Merino",
    "Vinicius Junior", "Jude Bellingham", "Kevin De Bruyne", "Sunil Chhetri",
    "Robert Lewandowski", "Zinedine Zidane", "Karim Benzema", "Luka Modric",
    "Ronaldinho", "Neymar", "Ronaldo", "Messi", "Mbappe", "Haaland", "Pele",
    "Maradona", "Zidane", "Benzema", "Modric", "Rooney", "Merino", "Beckham",
    "Juninho", "Marcelo", "Yamal", "Salah", "Endrick",
    "Saudi Arabia", "South Korea", "United States",
    "Spain", "Portugal", "Argentina", "Brazil", "France", "Germany", "England",
    "Belgium", "Netherlands", "Croatia", "Morocco", "Italy", "Japan", "India",
    "Mexico", "Uruguay", "Egypt", "Switzerland", "Norway",
    "Real Madrid", "Manchester United", "Manchester City", "Bayern Munich",
    "Paris Saint-Germain", "Barcelona", "Liverpool", "Juventus", "Chelsea",
    "Arsenal", "Al Nassr", "Inter Miami",
    "FIFA World Cup", "World Cup", "Champions League", "Premier League",
    "La Liga", "Ballon d'Or", "Camp Nou", "Old Trafford", "La Roja", "CR7",
]


# Grammar/common words jo capitalized ho sakte (sentence-start) par NAAM nahi hain.
_STOP_CAP = {
    "the", "a", "an", "he", "she", "it", "this", "that", "these", "those", "but",
    "and", "so", "after", "when", "then", "now", "we", "they", "you", "your", "his",
    "her", "their", "my", "if", "as", "for", "to", "of", "in", "on", "at", "with",
    "by", "from", "not", "no", "yes", "did", "do", "does", "who", "what", "why",
    "how", "many", "some", "most", "one", "two", "three", "first", "next", "last",
    "here", "there", "still", "just", "also", "even", "because", "while", "before",
    "everyone", "people", "fans", "football", "soccer", "match", "goal", "team",
}


def _translate_keep_names(text_en: str, sl: str = "en", tl: str = "hi") -> str:
    """English -> Hindi, PAR proper naam (player/team/club) Latin me hi rehte hain
    (Remy sahi bolti). Naam -> placeholder (QQnQQ) -> translate -> naam wapas Latin.

    Do pass: (1) curated _KEEP_LATIN (case-insensitive), (2) GENERIC — koi bhi
    capitalized proper-noun sequence (Roberto Baggio, Zico) jo stop-word na ho.
    """
    import re as _re
    if not text_en or not text_en.strip():
        return text_en
    protected, toks = text_en, []
    ctr = [0]

    def _protect(name, flags=0):
        pat = _re.compile(r"\b" + _re.escape(name) + r"\b", flags)
        nonlocal protected
        if pat.search(protected):
            tok = f"QQ{ctr[0]}QQ"
            protected = pat.sub(tok, protected)
            toks.append((tok, name))
            ctr[0] += 1

    # 1) curated (case-insensitive) — longest first
    for name in sorted(_KEEP_LATIN, key=len, reverse=True):
        _protect(name, _re.I)
    # 2) generic capitalized proper nouns (case-sensitive), longest first
    caps = _re.findall(r"\b[A-Z][a-zA-Z.'\-]+(?:\s+[A-Z][a-zA-Z.'\-]+)*\b", protected)
    for name in sorted(set(caps), key=len, reverse=True):
        if all(w.lower() in _STOP_CAP for w in name.split()):
            continue
        _protect(name)

    hi = _gtranslate(protected, sl=sl, tl=tl)
    for tok, name in toks:
        hi = hi.replace(tok, name)
    return hi


# Real photo trigger ke liye known football names (case-insensitive)
_FOOT_NAMES = [
    "brazil", "japan", "argentina", "france", "germany", "spain", "portugal",
    "england", "italy", "netherlands", "morocco", "messi", "ronaldo", "neymar",
    "mbappe", "pele", "maradona", "ramos", "modric", "benzema", "haaland",
    "world cup", "fifa", "trophy",
]


def _local_custom(script_text: str, num_segments: int) -> dict:
    """
    My Script mode — BINA LLM ke: script ko locally split, Google Translate se
    English subtitles. Pollinations pe depend nahi -> kabhi fail nahi hota.
    """
    import re
    # sentence split (Hindi danda + . ? !)
    parts = [p.strip() for p in re.split(r"(?<=[।.!?])\s+", script_text.strip())
             if p.strip()]
    if not parts:
        parts = [script_text.strip()]

    # num_segments ke hisaab se group/split
    n = max(1, num_segments)
    if len(parts) >= n:
        per = len(parts) / n
        chunks = [" ".join(parts[int(round(i * per)):int(round((i + 1) * per))])
                  for i in range(n)]
        chunks = [c for c in chunks if c]
    else:
        chunks = parts[:]
        # kam sentences -> lambe ko comma par todo
        while len(chunks) < n:
            idx = max(range(len(chunks)), key=lambda i: len(chunks[i]))
            if "," in chunks[idx]:
                a, b = chunks[idx].split(",", 1)
                chunks[idx:idx + 1] = [a.strip(), b.strip()]
            else:
                break

    segments = []
    for c in chunks:
        en = _words_to_digits(_gtranslate(c))   # word-numbers -> digits (stat cards)
        low = en.lower()
        names = [w for w in _FOOT_NAMES if w in low]
        if names:
            itype, q = "real", " ".join(names[:2])
        else:
            itype, q = "ai", "football stadium action"
        segments.append({"voice_hindi": c, "subtitle_english": en,
                         "image_query": q, "image_type": itype})

    first_en = segments[0]["subtitle_english"] if segments else "Football"
    last = script_text.strip().rstrip("।.!? ").split("।")[-1]
    return {
        "title_hindi": script_text.strip()[:60],
        "hook_english": " ".join(first_en.split()[:4]),
        "cta_english": "Follow for more! ⚽",
        "segments": segments,
    }


def _build_custom_messages(script_text: str, num_segments: int):
    """
    User ka apna script -> segments. KUCH ADD NAHI karna (no prediction/extra facts),
    bas faithfully split + Hindi voice + English subtitle + image queries.
    """
    system = "You are a JSON generator. Output ONLY a JSON object, no explanation."
    user = (
        f"Convert THIS EXACT script into a {num_segments}-part vertical short.\n"
        f'SCRIPT: """{script_text.strip()}"""\n'
        'JSON shape: {"title_hindi":"..","hook_english":"..","cta_english":"..",'
        '"segments":[{"voice_hindi":"..","subtitle_english":"..",'
        '"image_query":"..","image_type":"real|ai"}]}\n'
        f"- Split the script into exactly {num_segments} segments, IN ORDER.\n"
        "- voice_hindi = that part of the script in natural spoken HINDI "
        "(translate faithfully; keep names/English terms as-is).\n"
        "- subtitle_english = that same part in short ENGLISH.\n"
        "- IMPORTANT: Use ONLY the script's content. Do NOT add new facts, "
        "opinions, predictions, stats, or a winner. Stay 100% faithful.\n"
        "- image_query = matching visual; image_type 'real' for named "
        "player/team/stadium, else 'ai'.\n"
        "- hook_english = 3-5 word title from the script. cta_english = the "
        "script's closing question/CTA (e.g. the final question).\n"
        "Output JSON only. /no_think"
    )
    return system, user


def _build_meta_messages(topic: str, mode: str, segments: list, context: str = ""):
    """Chhota prompt sirf posting metadata ke liye (title/description/hashtags)."""
    subs = " | ".join(s.get("subtitle_english", "") for s in segments)[:300]
    # Prediction sirf tab jab koi current-facts grounding NA ho (warna past event
    # ko galti se "future prediction" bana deta hai + fake % likh deta hai).
    pred = ("Since this is a prediction video, give a clear verdict with rough "
            "win percentages. " if (mode == "preview" and not context) else "")
    ground = ""
    if context:
        ground = (
            "CURRENT FACTS (real news as of today — GROUND TRUTH):\n"
            f"{context}\n"
            "RULES for title/description: Do NOT contradict these facts. If an event "
            "already happened, describe the ACTUAL result — do NOT frame it as a future "
            "prediction and do NOT invent win percentages or stats. State the correct "
            "winner (in 'A 0-1 B', B won).\n\n"
        )
    quiz_rule = ""
    if mode == "quiz":
        quiz_rule = ("*** THIS IS A GUESS-THE-PLAYER QUIZ: the title/title_options and "
                     "description must NOT name or reveal the mystery player — keep them "
                     "teasers like 'Guess this player? 🤔' / 'Pehchaan kaun?'. ***\n")
    # Abhi YouTube pe jo shorts CHAL RAHE hain unke titles — LLM ko dikhao taaki wo
    # aaj ka HOOK-style pakde (naam kaafi nahi, angle/curiosity asli cheez hai).
    hot = ""
    try:
        from trending import hot_titles
        ht = hot_titles(6)
        if ht:
            hot = ("These football Shorts are pulling the MOST VIEWS right now — study "
                   "the HOOK/ANGLE style (do NOT copy them, write about OUR topic):\n"
                   + "\n".join(f"  - {t}" for t in ht) + "\n\n")
    except Exception:
        pass
    system = "You are a JSON generator. Output ONLY a JSON object, no explanation."
    user = (
        ground + quiz_rule + hot +
        f"Football short topic: {topic}.\n"
        f"Video covers: {subs}\n"
        'JSON shape: {"youtube_title":"..","title_options":["..","..",".."],'
        '"description":"..","hashtags":".."}\n'
        + ("" if mode == "quiz" else
           "*** TITLE = the single biggest lever. Two rules, BOTH required:\n"
           "  (1) NAME: put the famous player/team name (Ronaldo/CR7, Messi, Mbappe, "
           "Real Madrid...) in the FIRST half of the title.\n"
           "  (2) HOOK: the name ALONE is NOT enough — it needs a curiosity-gap or a "
           "shock. Our REAL numbers prove it:\n"
           "      'CR7 ka Secret Revealed'          -> 1,274 views (name + curiosity ✅)\n"
           "      'Mbappe vs Neymar: Kaun Hai Better?' -> 8 views (name, but a flat "
           "boring question ❌)\n"
           "      'World Cup Kyun Nahi Jeet Paye Ye 5 Legends?' -> 103 (no name, but a "
           "strong hook)\n"
           "  So: NAME + a promise of something SECRET/SHOCKING/UNKNOWN. Never a bland "
           "'X vs Y: kaun better?' or 'X ke baare me jaano'. Make the viewer NEED the "
           "answer. ***\n") +
        "*** TITLE MUST MATCH THE VIDEO TYPE — do NOT mislead. A Top-5 countdown is a "
        "RANKING (title like 'Top 5 Free-Kick Kings 🎯'), NOT a 1-v-1 'X vs Y battle'. A "
        "goal-scorer chart is a RACE. Never invent a head-to-head that the video is not "
        "about. The title must describe what the viewer will ACTUALLY see. ***\n"
        "- title_options = 3 DIFFERENT scroll-stopping, CLICK-WORTHY titles (Hinglish). "
        "Use a CURIOSITY GAP or emotional/bold angle + a power word (Shocking, Emotional, "
        "Insane, Secret, Nobody, Finally, End). Angles: (1) a curiosity question, (2) a "
        "bold/shocking claim, (3) a number/listicle. Each under 65 chars, 1-2 emojis, and "
        "front-load the main SEARCHABLE keyword (player/team/'World Cup 2026') for SEO. "
        "Examples of vibe: 'CR7 ka Emotional End? 😢', 'Ye Player Messi se Aage Nikla! 🤯', "
        "'5 Reasons Spain Unstoppable Hai 🔥'. NO boring/generic titles.\n"
        "- youtube_title = the strongest, most clickable of title_options.\n"
        "- description = 3-4 punchy engaging HINGLISH lines (dost se baat wali vibe): "
        "line 1 = a hook that re-states the intrigue, then 1-2 lines of value/context, "
        "then a SPECIFIC comment-bait question. Sprinkle 2-3 relevant emojis. "
        f"{pred}\n"
        "- hashtags = 6-8 hashtags one string: 3-4 broad (#Shorts #Football #Reels #viral) "
        "+ 3-4 niche/specific (exact player/team/#WorldCup2026/#fyp) for discovery.\n"
        "Output JSON only. /no_think"
    )
    return system, user


def _call_openai(system: str, user: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0.9,
    )
    return resp.choices[0].message.content


def _call_gemini(system: str, user: str) -> str:
    """Google Gemini Flash — FREE tier (aistudio.google.com se key, NO card). Groq se
    kaafi behtar/coherent scripts. GEMINI_API_KEY na ho to raise -> Groq pe gir jaata."""
    import requests
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("no GEMINI_API_KEY")
    import time
    # Free-tier quota "PerProjectPerMODEL" hai -> HAR model ka apna alag daily quota.
    # Isliye model-CHAIN: ek ka quota khatam (429) -> turant agle model pe. ~5x free
    # capacity, bina paise. Sab khatam ho to Groq fallback (upar wala chain).
    models = (getattr(config, "GEMINI_MODELS", None)
              or [getattr(config, "GEMINI_MODEL", "gemini-flash-latest")])
    headers = {"Content-Type": "application/json", "X-goog-api-key": key,
               "User-Agent": "Mozilla/5.0"}
    body = {"contents": [{"parts": [{"text": system + "\n\n" + user}]}],
            "generationConfig": {"temperature": 0.9, "maxOutputTokens": 8192}}
    last = "no response"
    for model in models:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent")
        for attempt in range(2):
            try:
                r = requests.post(url, json=body, timeout=45, headers=headers)
                if r.status_code == 200:
                    cands = r.json().get("candidates", [])
                    if cands:
                        parts = cands[0].get("content", {}).get("parts", [{}])
                        txt = "".join(p.get("text", "") for p in parts)
                        if txt:
                            print(f"[script]   gemini model={model}")
                            return txt
                    last = f"{model} empty"
                    break                       # khali -> agla model try karo
                if r.status_code == 429:        # is model ka DIN ka quota khatam
                    last = f"{model} quota-full"
                    break                       # retry bekaar -> agla model
                last = f"{model} HTTP {r.status_code} {r.text[:80]}"
                if r.status_code in (400, 401, 403, 404):
                    break                       # bad key/model -> agla model
            except Exception as e:
                last = f"{model}: {e}"
            time.sleep(2)
    raise RuntimeError(f"Gemini failed (last: {last})")


def _call_groq(system: str, user: str) -> str:
    # Groq is OpenAI-compatible. RAW request use karte hain (OpenAI SDK NAHI) kyunki
    # SDK ka User-Agent ab Groq ke Cloudflare se 403 (error 1010) khaata hai. Browser
    # jaisa User-Agent header = Cloudflare pass. 70b busy/rate-limit ho to 8b backup.
    import requests
    key = os.getenv("GROQ_API_KEY")
    headers = {"Authorization": f"Bearer {key}",
               "Content-Type": "application/json",
               "User-Agent": "Mozilla/5.0"}
    last = "no response"
    for model in ("llama-3.3-70b-versatile", "llama-3.1-8b-instant"):
        for attempt in range(3):
            try:
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json={"model": model,
                          "messages": [{"role": "system", "content": system},
                                       {"role": "user", "content": user}],
                          "temperature": 0.9},
                    timeout=45)
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
                last = f"HTTP {r.status_code} {r.text[:120]}"
                if r.status_code in (401, 403):   # auth/CF block: retry se fayda nahi
                    break
            except Exception as e:
                last = str(e)
            import time; time.sleep(2 + attempt * 2)
    raise RuntimeError(f"Groq failed (last: {last})")


def _extract_json(text: str, required_key: str = None):
    """Text me se pehla valid JSON object nikaalo (optionally jisme required_key ho)."""
    if not text:
        return None
    text = text.replace("```json", "").replace("```", "")
    for start in range(len(text)):
        if text[start] != "{":
            continue
        depth = 0
        for end in range(start, len(text)):
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
                if depth == 0:
                    chunk = text[start:end + 1]
                    try:
                        obj = json.loads(chunk)
                        if isinstance(obj, dict) and (
                                required_key is None or obj.get(required_key)):
                            return obj
                    except Exception:
                        pass
                    break
    return None


def _pollinations_json(system: str, user: str, required_key: str,
                       tries: int = 8, label: str = "") -> dict:
    """
    Free, no API key. openai-fast + /no_think se JSON nikaalta hai.
    Har attempt par alag seed (flaky reasoning-model ke liye). Returns parsed dict.
    """
    import requests
    import time

    last = "no response"
    # Pollinations pe ab sirf 'openai-fast' (GPT-OSS 20B Reasoning) available hai.
    # reasoning_effort='low' = ~27s me valid JSON (medium/high = 40s+ ya khaali,
    # saara token-budget reasoning me chala jaata hai).
    model = "openai-fast"
    for attempt in range(tries):
        try:
            r = requests.post(
                "https://text.pollinations.ai/openai",
                headers={"Content-Type": "application/json"},
                json={"model": model,
                      "messages": [{"role": "system", "content": system},
                                   {"role": "user", "content": user}],
                      "temperature": 0.6, "seed": 100 + attempt * 7,
                      "reasoning_effort": "low",   # kam socho, JSON jaldi do
                      "max_tokens": 3000},
                timeout=75,
            )
            if r.status_code == 200:
                msg = r.json().get("choices", [{}])[0].get("message", {})
                for field in ("content", "reasoning"):
                    obj = _extract_json(msg.get(field) or "", required_key)
                    if obj:
                        print(f"[script] {label} OK (attempt {attempt + 1}, {model}).")
                        return obj
                last = "empty (model kept reasoning)"
            else:
                last = f"HTTP {r.status_code}"
        except Exception as e:
            last = str(e)
        wait = 3 + attempt
        print(f"[script] {label} retry {attempt + 1}/{tries} ({last}) in {wait}s...")
        time.sleep(wait)

    raise RuntimeError(f"Pollinations failed after {tries} tries (last: {last})")


def _json_via_provider(system, user, required_key, label, tries):
    """Provider chain: Groq (best, free-tier) -> Pollinations (free, reliable safety net).

    Groq key dead/missing ya fail ho to seamlessly Pollinations pe gir jaata hai —
    build kabhi nahi rukta. Valid Groq key = behtar quality apne aap.
    """
    # Gemini Flash sabse pehle (best quality, free) — GEMINI_API_KEY ho tabhi.
    if os.getenv("GEMINI_API_KEY"):
        try:
            obj = _extract_json(_call_gemini(system, user), required_key)
            if obj:
                print(f"[script] {label} OK (gemini).")
                obj["_provider"] = "gemini"        # datalog ke liye track
                return obj
            print(f"[script] {label} gemini empty -> groq")
        except Exception as e:
            print(f"[script] {label} gemini failed ({e}) -> groq")

    prov = getattr(config, "SCRIPT_PROVIDER", "pollinations")
    if prov == "groq":
        try:
            obj = _extract_json(_call_groq(system, user), required_key)
            if obj:
                print(f"[script] {label} OK (groq).")
                obj["_provider"] = "groq"
                return obj
            print(f"[script] {label} groq empty -> pollinations fallback")
        except Exception as e:
            print(f"[script] {label} groq failed ({e}) -> pollinations fallback")
    elif prov == "openai":
        try:
            obj = _extract_json(_call_openai(system, user), required_key)
            if obj:
                print(f"[script] {label} OK (openai).")
                return obj
        except Exception as e:
            print(f"[script] {label} openai failed ({e}) -> pollinations fallback")
    return _pollinations_json(system, user, required_key=required_key,
                              tries=tries, label=label)


def _fallback_meta(topic: str, mode: str, data: dict) -> dict:
    """Agar metadata call fail ho to local se title/description/hashtags bana do."""
    segs = data.get("segments", [])
    first = (segs[0].get("subtitle_english", "") if segs else "").strip()
    last = (segs[-1].get("subtitle_english", "") if segs else "").strip()

    # word-boundary truncate (mid-word cut nahi)
    def _clip(s, n=52):
        s = s.rstrip(" .,!?")
        if len(s) <= n:
            return s
        return s[:n].rsplit(" ", 1)[0]

    core = _clip(first)
    # curiosity hook prefix (agar already question/hook nahi hai)
    low = core.lower()
    if low.startswith(("do you know", "did you know", "what", "why", "how",
                       "the ", "this ")):
        title = f"{core}? 😱⚽"
    else:
        title = f"{core}... 😱🔥"
    opts = [
        f"{core}? 😱",
        f"You WON'T believe this! {_clip(first, 40)} ⚽🔥",
        f"{_clip(first, 45)} — Wait for it! 👀",
    ]
    desc = (f"{first} {last}\n\n"
            "Kya ye tumhe pata tha? 👀 Aur aise videos ke liye FOLLOW karo. "
            "Comment me apni raay batao! ⚽🔥")
    tags = ("#Shorts #Football #Soccer #FIFAWorldCup2026 #footballshorts "
            "#reels #viral #footyhindi #trending #fyp")
    return {"youtube_title": title, "title_options": opts,
            "description": desc.strip(), "hashtags": tags}


def _wiki_context_for(topic: str, mode: str) -> str:
    """Topic se player naam(s) nikaal ke Wikipedia REAL career facts laao (grounding).
    debate 'A vs B' -> dono; quiz/story/player -> ek. Fail par khaali."""
    import re as _re
    from trends import wiki_facts
    if mode == "debate" and _re.search(r"\bvs\.?\b", topic, _re.I):
        names = [p.strip() for p in _re.split(r"\s+vs\.?\s+", topic, flags=_re.I)[:2]
                 if p.strip()]
    else:
        t = _re.sub(r"\b(career journey|journey|career|story|biography|life story|"
                    r"rise|the untold)\b", "", topic, flags=_re.I).strip(" -–—:")
        names = [t] if t else []
    out = []
    for nm in names:
        f = wiki_facts(nm)
        if f:
            out.append(f"{nm} — {f}")
    return "\n\n".join(out)


def generate_script(topic: str = None, mode: str = None,
                    num_segments: int = None, custom_script: str = None,
                    context: str = None) -> dict:
    topic = topic or config.TOPIC
    mode = mode or config.MODE
    num_segments = num_segments or config.NUM_SEGMENTS
    custom_script = custom_script if custom_script is not None else getattr(
        config, "CUSTOM_SCRIPT", "")

    # ── 1) CORE: segments (zaroori) ──────────────────────────────────────────────
    if custom_script and custom_script.strip():
        # My Script mode = LOCAL split + Google Translate (no LLM -> kabhi fail nahi)
        mode = "custom"
        topic = custom_script.strip()[:100]
        print("[script] My Script mode — LOCAL split + translate (no LLM core)...")
        data = _local_custom(custom_script, num_segments)
    else:
        print(f"[script] Generating {mode} script for: {topic!r} "
              f"({config.SCRIPT_PROVIDER})...")
        # GROUNDING (facts LLM ko de taaki invent na kare):
        #  - timely modes (facts/preview/player): aaj ki NEWS headlines
        #  - player-centric modes (quiz/story/debate/player): WIKIPEDIA real career facts
        if context is None:
            ctx = ""
            if getattr(config, "USE_NEWS_CONTEXT", False) \
                    and mode in {"facts", "preview", "player"}:
                try:
                    from trends import current_context
                    ctx = current_context(topic) or ""
                    if ctx:
                        print(f"[script] news-grounding ON ({ctx.count(chr(10)) + 1} headlines)")
                except Exception as e:
                    print(f"[script] news-grounding skip: {e}")
            if mode in {"quiz", "story", "debate", "player"}:
                w = _wiki_context_for(topic, mode)
                if w:
                    print(f"[script] wiki-facts grounding ON ({w.count(chr(10)) + 1} entries)")
                    ctx = (ctx + "\n\n" + w).strip() if ctx else w
            if mode == "stats":                 # LIVE table/scorers = ground truth
                try:
                    from stats import current_stats
                    _t, gt = current_stats()
                    if gt:
                        print(f"[script] LIVE stats grounding ON ({gt.count(chr(10))} rows)")
                        ctx = gt
                except Exception as e:
                    print(f"[script] stats-grounding skip: {e}")
            context = ctx
        system, user = _build_messages(topic, mode, num_segments, context or "")
        data = _json_via_provider(system, user, "segments", "[core]", tries=10)
        if not data:
            raise RuntimeError("Script core JSON parse failed")

        # LLM ne script ENGLISH me likhi (natural + Groq ki strength). Ab usi Google
        # Translate se Hindi voice banao — jaisा My-Script mode karta hai. Yehi Hindi
        # Remy pe CLEAN sunai deti hai (seedhi LLM-Hindi awkward hoti hai).
        import time as _t
        _native_hi = str(getattr(config, "EDGE_VOICE", "")).startswith("hi-IN")
        print("[script] English -> Hindi (Google Translate) for natural voice"
              f" [{'native, Devanagari names' if _native_hi else 'multilingual, Latin names'}]...")
        for s in data.get("segments", []):
            ven = (s.get("voice_english") or "").strip()
            vhi = (s.get("voice_hindi") or "").strip()
            if ven:                       # normal: English -> Hindi voice
                s["subtitle_english"] = _words_to_digits(ven)
                # Native Hindi voice (Madhur) naam Devanagari me natural bolti — plain
                # translate. Multilingual voice (Remy/Brian) ke liye naam Latin rakho.
                if _native_hi:
                    s["voice_hindi"] = _gtranslate(ven, sl="en", tl="hi")
                else:
                    s["voice_hindi"] = _translate_keep_names(ven)
            elif vhi:                     # LLM ne Hindi de diya -> subtitle Hindi->Eng
                s["voice_hindi"] = vhi
                s["subtitle_english"] = _words_to_digits(_gtranslate(vhi, sl="hi", tl="en"))
            else:
                continue
            _t.sleep(0.3)                 # throttle (rate-limit se bachne ke liye)
        # title bhi English -> Hindi
        if data.get("title_english") and not data.get("title_hindi"):
            data["title_hindi"] = (_gtranslate(data["title_english"], sl="en", tl="hi")
                                   if _native_hi
                                   else _translate_keep_names(data["title_english"]))

    # ── 2) META: title/description/hashtags (attractive) ─────────────────────────
    # Core segments reliable (upar) hain; meta best-effort LLM se (attractive),
    # fail ho to behtar local fallback. Custom mode me kam tries (jaldi fallback).
    try:
        # custom mode: topic ko subtitles se banao (script[:100] se behtar context)
        meta_topic = topic
        if mode == "custom" and data.get("segments"):
            meta_topic = " ".join(s.get("subtitle_english", "")
                                  for s in data["segments"])[:300]
        m_system, m_user = _build_meta_messages(meta_topic, mode, data["segments"],
                                                context or "")
        meta = _json_via_provider(m_system, m_user, "description", "[meta]",
                                  tries=4 if mode == "custom" else 6)
        if not meta:
            raise RuntimeError("meta JSON parse failed")
    except Exception as e:
        print(f"[script] meta call failed ({e}) -> local fallback")
        meta = _fallback_meta(topic, mode, data)

    data.update({k: v for k, v in meta.items() if v})
    # title_options se youtube_title bharo agar missing
    opts = data.get("title_options") or []
    if not data.get("youtube_title") and opts:
        data["youtube_title"] = opts[0]
    if not data.get("youtube_title"):
        data.update(_fallback_meta(topic, mode, data))

    segs = data.get("segments", [])
    # QUIZ: aakhri segment = reveal -> uske PEHLE dramatic suspense pause (video.py).
    if mode == "quiz" and segs:
        segs[-1]["suspense_before"] = True

    print(f"[script] {len(segs)} segments ready.")
    print(f"[script] Title: {data.get('youtube_title','')}")
    for i, s in enumerate(segs, 1):
        q = s.get("image_query", "")
        t = s.get("image_type", "ai")
        print(f"  {i}. {s.get('subtitle_english', '')[:42]}  [{t}: {q}]")

    return data


def post_text(data: dict) -> str:
    """Posting ke liye ready title + A/B variants + description + hashtags."""
    title = data.get("youtube_title") or data.get("title_hindi") or "Football Short"
    desc = data.get("description", "")
    tags = data.get("hashtags", "#Shorts #Football")
    opts = data.get("title_options") or []

    out = f"TITLE (best):\n{title}\n"
    if opts:
        out += "\nA/B TITLE OPTIONS (test karo):\n"
        for i, o in enumerate(opts, 1):
            out += f"  {i}. {o}\n"
    out += f"\nDESCRIPTION:\n{desc}\n\n{tags}\n"
    return out


def save_post_text(data: dict, path: str) -> str:
    txt = post_text(data)
    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    return path


if __name__ == "__main__":
    import pprint
    pprint.pprint(generate_script())
