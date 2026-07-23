"""
ideas.py — Content Idea Engine (Phase 1 of automation).

Roz naye football topics deta hai taaki content KABHI khatam na ho — World Cup ke
baad bhi. Mix of:
  - Evergreen templates (legends, GOAT debates, top-5, records, player stories)
  - Trending (trends.py — abhi ke hot topics)
  - "On this day" football events (Wikipedia, free)
  - Weekday content calendar (din-wise angle)

Use:
    env\\Scripts\\python.exe ideas.py            # aaj ke ideas
    from ideas import get_ideas, todays_angle
"""

import sys
import random
import datetime
import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from trends import get_trending

_H = {"User-Agent": "FootyShorts/1.0"}

PLAYERS = [
    # current stars (variety — Messi/Ronaldo ko dominate mat karne do)
    "Kylian Mbappe", "Erling Haaland", "Vinicius Junior", "Jude Bellingham",
    "Lamine Yamal", "Mohamed Salah", "Harry Kane", "Kevin De Bruyne",
    "Rodri", "Bukayo Saka", "Florian Wirtz", "Jamal Musiala", "Lautaro Martinez",
    "Victor Osimhen", "Bruno Fernandes", "Antoine Griezmann", "Rafael Leao",
    "Phil Foden", "Endrick", "Cole Palmer",
    # legends / evergreen
    "Lionel Messi", "Cristiano Ronaldo", "Neymar", "Pele", "Diego Maradona",
    "Ronaldinho", "Zinedine Zidane", "Luka Modric", "Sunil Chhetri",
    # aur legends — ye pool me na hone se _main_subject unki jagah TEAM pakad leta tha
    # (Baggio -> "Italy" -> team group photo). Naam pool me = unki asli photo aayegi.
    "Roberto Baggio", "Paolo Maldini", "Johan Cruyff", "Franz Beckenbauer",
    "Michel Platini", "Eusebio", "George Best", "Ferenc Puskas", "Garrincha",
    "Romario", "Ronaldo Nazario", "Andrea Pirlo", "Xavi Hernandez",
    "Andres Iniesta", "Iker Casillas", "Thierry Henry", "David Beckham",
    "Steven Gerrard", "Frank Lampard", "Kaka", "Samuel Etoo", "Didier Drogba",
]
# Mega-draw naam — data: bade naam = zyada views (Ronaldo 1120, chhote-naam debate 45).
# Topic-picker inhe pehle prefer karta hai (trending ke baad), taaki har video ka
# subject high-interest ho. Baaki PLAYERS variety/dedup ke liye rehte hain.
TOP_TIER = [
    "Cristiano Ronaldo", "Lionel Messi", "Kylian Mbappe", "Neymar",
    "Erling Haaland", "Lamine Yamal", "Jude Bellingham", "Vinicius Junior",
    "Ronaldinho", "Diego Maradona", "Pele",
]
# WONDERKIDS — 14-24 audience ka favourite, low competition, evergreen search.
# (Umar badhne par yahan se hata dena — "wonderkid" 24+ pe fit nahi baithta.)
WONDERKIDS = [
    "Lamine Yamal", "Endrick", "Arda Guler", "Pau Cubarsi", "Warren Zaire-Emery",
    "Kobbie Mainoo", "Rodrigo Mora", "Estevao Willian", "Franco Mastantuono",
    "Ethan Nwaneri", "Desire Doue", "Mathys Tel", "Kenan Yildiz", "Savinho",
]

# CONTROVERSY angles — asli, well-documented cheezein (jhoothi kahani NAHI).
# News grounding se aur bhi taaza mile to wo prefer hota hai.
# SPECIFIC, well-documented incidents — vague angles ("the offside call that changed
# a final") pe LLM kahani GADH deta tha (test me "Argentina lost the 2022 final" likh
# diya, jabki Argentina JEETA tha). Naam-wale asli waqiye = LLM ki knowledge pakki +
# Wikipedia grounding bhi milti hai.
CONTROVERSY_ANGLES = [
    "Maradona Hand of God goal 1986 England",
    "Thierry Henry handball against Ireland 2009 playoff",
    "Frank Lampard ghost goal England Germany 2010",
    "Zinedine Zidane headbutt 2006 World Cup final",
    "Luis Suarez handball against Ghana 2010",
    "Figo transfer from Barcelona to Real Madrid 2000",
    "Battle of Nuremberg 2006 Portugal Netherlands red cards",
    "Roy Keane tackle on Alf-Inge Haaland",
    "Sergio Ramos challenge on Mohamed Salah 2018 final",
    "Ronaldinho free kick over David Seaman 2002",
]

TEAMS = ["Brazil", "Argentina", "Portugal", "France", "Spain", "Germany",
         "England", "Netherlands", "Italy", "Belgium", "Morocco", "Croatia",
         "Real Madrid", "Barcelona", "Manchester City", "Manchester United",
         "Liverpool", "Bayern Munich", "India"]

# Evergreen topic templates (WC ke baad bhi kaam ke)
EVERGREEN = [
    "5 shocking facts about {player}",
    "{player} vs {player2}: kaun hai asli GOAT?",
    "The untold rise of {player}",
    "{player} ke 5 sabse yaadgar moments",
    "Top 5 {team} players of all time",
    "5 records jo {player} ne banaye",
    "{player}'s emotional journey to the top",
    "Jab {player} ne poori duniya ko chaunka diya",
    "{team} ki sabse badi rivalry",
    "Why {player} is a once-in-a-generation talent",
    "5 young players jo future ke superstar hain",
    "{player} ka woh goal jise koi nahi bhula",
]

# Weekday -> content angle (Mon=0)
CALENDAR = {
    0: "Weekend match highlights & reactions",
    1: "Legend spotlight — ek player ki kahani",
    2: "Champions League / big match preview",
    3: "Throwback — iconic football moment",
    4: "Match prediction — kaun jeetega",
    5: "GOAT debate / player comparison",
    6: "5 football facts / records",
}


def _fill(t: str) -> str:
    p = random.choice(PLAYERS)
    p2 = random.choice([x for x in PLAYERS if x != p])
    return t.format(player=p, player2=p2, team=random.choice(TEAMS))


def on_this_day() -> list:
    """Aaj ke din ke historical football events (Wikipedia, free)."""
    try:
        d = datetime.date.today()
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/"
            f"{d.month}/{d.day}", headers=_H, timeout=20)
        evs = r.json().get("events", [])
        kws = ("football", "soccer", "world cup", "fifa", "uefa", "champions league")
        out = []
        for e in evs:
            txt = e.get("text", "")
            if any(k in txt.lower() for k in kws):
                yr = e.get("year", "")
                out.append(f"On this day ({yr}): {txt}")
        return out[:3]
    except Exception:
        return []


def todays_angle() -> str:
    return CALENDAR.get(datetime.date.today().weekday(), "Football facts")


def _seo_topics(n: int, query: str):
    """SEO topics (real YouTube search demand). Network fail par khaali list."""
    try:
        from seo import seo_topics, suggest, _titlecase
        if query:                                # user hint diya -> uske real queries
            qs = [_titlecase(q) for q in suggest(query)][:n]
            return qs or seo_topics(n)
        return seo_topics(n)
    except Exception as e:
        print(f"[ideas] seo skip: {e}")
        return []


RANKING_CATEGORIES = [
    "highest goalscorers of all time", "best free-kick takers ever",
    "most expensive transfers ever", "best dribblers in football history",
    "greatest World Cup moments", "best goalkeepers of all time",
    "most Ballon d'Or winners", "fastest players in football",
    "best captains in football history", "greatest underdog stories in football",
    "best players never to win the World Cup", "most iconic football rivalries",
]


def trending_subjects(n: int = 12) -> list:
    """Aaj ke football news headlines se ACTUAL trending player/team naam nikaalo
    (SEO/trending-driven — taaki har baar Messi/Ronaldo na aaye)."""
    try:
        heads = get_trending("football OR soccer world cup transfer", n=18)
    except Exception:
        heads = []
    blob = " || ".join(heads).lower()
    known = sorted(PLAYERS + TEAMS, key=len, reverse=True)   # longer naam pehle match
    found = []
    for name in known:
        if name.lower() in blob and name not in found:
            found.append(name)
    return found[:n]


def _pick(pool: list, used: set):
    """pool me se ek jo `used` me na ho; sab use ho gaye to koi bhi (random)."""
    import random
    fresh = [x for x in pool if x not in (used or set())]
    return random.choice(fresh) if fresh else random.choice(pool)


def topic_for_mode(mode: str, i: int = 0, query: str = None, used: set = None):
    """(topic, subject_key) do — TRENDING-driven + `used` se dedup (no repeat).
    ranking->'Top 5 X', debate->'X vs Y', quiz/story->trending player.
    Subject pehle trending news se, warna diverse PLAYERS pool se (Messi/Ronaldo-heavy nahi)."""
    import random
    used = used or set()
    trend = trending_subjects()
    # trending players (news me aaye) — views ke liye sabse pehle inhe
    trend_players = [x for x in trend if x in PLAYERS]

    # YouTube pe ABHI jin players ke shorts pe views aa rahe (trend-riding) — sabse
    # strong signal, isliye news/mega-names se bhi pehle. Cache se aata (0 quota).
    try:
        from trending import hot_subjects
        yt_hot = [p for p in hot_subjects() if p in PLAYERS]
        if yt_hot:
            print(f"[ideas] YouTube-trending: {yt_hot[:4]}")
    except Exception:
        yt_hot = []

    def _pick_star(extra_used=None):
        """Views-first pick: YouTube-hot -> news-trending -> mega-names. Dedup.

        CHANNEL DATA (23 Jul tak): top-10 videos me 5 Ronaldo/Messi ke, plus Yamal 831,
        Bellingham 882. Bottom: Salah 1, Zidane 0, chhote-naam debates 0-7. Isliye
        poore PLAYERS pool wala fallback JAAN-BOOJH KE hataya — dedup ke baad wahi
        Salah/Zidane-type pick aate the. Ab bada naam REPEAT hota he (angle roz alag
        hota he, isliye repeat theek he); chhota naam kabhi nahi aata.
        """
        u = used | (extra_used or set())
        for tier in (yt_hot, trend_players, TOP_TIER):
            fresh = [p for p in tier if p not in u]
            if fresh:
                return random.choice(fresh)
        return random.choice(TOP_TIER)        # sab "used"? -> bada naam hi repeat karo

    if mode == "facts":                       # timely/news (SEO + trending)
        ideas = [x for x in get_ideas(6, query) if x not in used] or \
                get_ideas(6, query) or ["FIFA World Cup 2026 latest"]
        t = ideas[i % len(ideas)]
        return t, t
    if mode == "stats":                       # LIVE data (golden boot / league table)
        try:
            from stats import current_stats
            t, _gt = current_stats()
            if t:
                return t, t                   # roz naya data = roz fresh (repeat OK)
        except Exception:
            pass
        return "Top 5 goal scorers in football right now", "stats"
    if mode == "wonderkid":
        u = used
        fresh = [w for w in WONDERKIDS if w not in u] or WONDERKIDS
        w = random.choice(fresh)
        return f"{w} young football wonderkid records and hype", w
    if mode == "controversy":
        a = _pick(CONTROVERSY_ANGLES, used)
        return a, a
    if mode == "pundit":
        # FIGHT-FIRST: pehle ASLI jhagda dhoondo, phir usi pe video. Pehle player
        # chunte the aur uspe behes dhoondte the — jo aksar HOTI HI NAHI thi (test:
        # Yamal/Mbappe/Haaland teeno pe 0-1 reaction headline). Model phir alag-alag
        # kahaniyan silai karta tha — ek baar SNOOKER pundits tak Yamal video me
        # ghus gaye. Ab: headline hi topic he; na mile to player-anchored fallback
        # (jo script.py ke relevance-gate se guzarna hoga, warna skip).
        _NOT_FOOTBALL = ("wimbledon", "tennis", "snooker", "cricket", "darts",
                         "rugby", "golf", "boxing", "f1", "nba", "nfl")
        try:
            from trends import get_trending
            for q in ("football pundits clash row slammed argument",
                      "football pundit slammed defended live tv row"):
                for h in get_trending(q, n=6):
                    hl = h.lower()
                    caps = [w for w in h.split() if w[:1].isupper() and len(w) > 3]
                    if len(caps) >= 2 and not any(x in hl for x in _NOT_FOOTBALL) \
                            and h not in used:
                        return h, h            # headline HI topic he — poori story usi me
        except Exception:
            pass
        s = _pick_star()
        return f"what pundits and legends are saying about {s}", s
    if mode == "crossover":
        # DUSRE SPORTS ke sitare football stars ko kya bolte he (LeBron -> Messi,
        # Kohli -> Ronaldo). Pundit jaisa hi FIGHT-FIRST: asli headline hi topic —
        # bina iske model quotes GADHTA he, jo defamation-risk he. Na mile to
        # player-anchored fallback (trends.py ka relevance-gate pass karna hoga,
        # warna slot skip — silai se khali behtar).
        _X_HINT = ("nba", "basketball", "cricket", "tennis", "f1", "formula",
                   "ufc", "boxing", "nfl", "olympic", "golf", "sprinter",
                   "lebron", "kohli", "djokovic", "nadal", "hamilton",
                   "verstappen", "curry", "bolt", "mcgregor", "jordan")
        # FOOTBALLER hi hero he, bolne wale mehmaan (user: "final lead football ka
        # hi player hona chahiye — Ronaldo ko aur kaun-kaun ne praise kiya, agle
        # short me Messi ko"). Isliye headline TOPIC nahi banti — headline me se
        # TOP_TIER footballer ka naam nikaalte he aur usi pe anchor karte he;
        # grounding phir USKE saare admirers ki coverage jama karti he.
        try:
            from trends import get_trending
            for q in ("NBA cricket tennis star praises Messi Ronaldo Yamal football",
                      "LeBron Kohli Djokovic hails football star World Cup",
                      "athlete reacts football star praise tweet"):
                for h in get_trending(q, n=6):
                    hl = h.lower()
                    if not any(x in hl for x in _X_HINT):
                        continue
                    star = next((p for p in TOP_TIER
                                 if p.split()[-1].lower() in hl), None)
                    if star and star not in used:
                        return f"how stars from other sports praise {star}", star
        except Exception:
            pass
        s = _pick_star()
        return f"how stars from other sports praise {s}", s
    if mode == "quiz":
        s = _pick_star()
        return s, s
    if mode == "debate":                      # X vs Y — dono BADE naam (flop se bacho)
        a = _pick_star()
        b = _pick_star({a})
        return f"{a} vs {b}", f"{a} vs {b}"
    if mode == "ranking":                     # Top 5 <category> (categories diverse)
        c = _pick(RANKING_CATEGORIES, used)
        return "Top 5 " + c, c
    if mode == "story":                       # rags-to-riches journey
        s = _pick_star()
        return f"{s} career journey", s
    if mode == "player":
        s = _pick_star()
        return s, s
    ideas = get_ideas(3, query) or ["FIFA World Cup 2026"]
    t = ideas[i % len(ideas)]
    return t, t


def get_ideas(n: int = 9, query: str = None) -> list:
    """SEO (real search demand) + trending + on-this-day + evergreen ka mix — deduped.

    SEO topics sabse aage (jo log actually search karte hain), phir baaki fill karte hain.
    """
    ideas = []
    ideas += _seo_topics(max(4, n // 2), query)  # real search demand (SEO) — priority
    ideas += get_trending(query, n=3)            # abhi ke hot news topics
    ideas += on_this_day()                       # aaj ke din ke events
    tmpls = random.sample(EVERGREEN, min(len(EVERGREEN), n))
    ideas += [_fill(t) for t in tmpls]           # evergreen filled

    seen, out = set(), []
    for i in ideas:
        i = (i or "").strip()
        if i and i.lower() not in seen:
            seen.add(i.lower())
            out.append(i)
    return out[:n]


if __name__ == "__main__":
    print(f"\n📅 Aaj ka angle: {todays_angle()}\n")
    print("💡 Content ideas:\n")
    for i, t in enumerate(get_ideas(10), 1):
        print(f"  {i}. {t}")
    print()
