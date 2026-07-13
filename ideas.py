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
]
# Mega-draw naam — data: bade naam = zyada views (Ronaldo 1120, chhote-naam debate 45).
# Topic-picker inhe pehle prefer karta hai (trending ke baad), taaki har video ka
# subject high-interest ho. Baaki PLAYERS variety/dedup ke liye rehte hain.
TOP_TIER = [
    "Cristiano Ronaldo", "Lionel Messi", "Kylian Mbappe", "Neymar",
    "Erling Haaland", "Lamine Yamal", "Jude Bellingham", "Vinicius Junior",
    "Ronaldinho", "Diego Maradona", "Pele",
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

    def _pick_star(extra_used=None):
        """Views-first player pick: pehle trending, phir mega-names, phir baaki. Dedup."""
        u = used | (extra_used or set())
        for tier in (trend_players, TOP_TIER, PLAYERS):
            fresh = [p for p in tier if p not in u]
            if fresh:
                return random.choice(fresh)
        return random.choice(PLAYERS)

    if mode == "facts":                       # timely/news (SEO + trending)
        ideas = [x for x in get_ideas(6, query) if x not in used] or \
                get_ideas(6, query) or ["FIFA World Cup 2026 latest"]
        t = ideas[i % len(ideas)]
        return t, t
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
