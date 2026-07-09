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

PLAYERS = ["Lionel Messi", "Cristiano Ronaldo", "Neymar", "Kylian Mbappe",
           "Erling Haaland", "Pele", "Diego Maradona", "Ronaldinho",
           "Zinedine Zidane", "Luka Modric", "Mohamed Salah", "Vinicius Junior",
           "Jude Bellingham", "Kevin De Bruyne", "Sunil Chhetri"]
TEAMS = ["Brazil", "Argentina", "Portugal", "France", "Spain", "Germany",
         "Real Madrid", "Barcelona", "Manchester United", "Liverpool", "India"]

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


def topic_for_mode(mode: str, i: int = 0, query: str = None) -> str:
    """Mode ke hisaab se FITTING topic do (ranking->'Top 5 X', debate->'X vs Y', etc.).
    Warna auto-pilot ranking ko versus-topic de deta tha (mismatch)."""
    import random
    if mode == "facts":                       # timely/news
        ideas = get_ideas(3, query) or ["FIFA World Cup 2026 latest"]
        return ideas[i % len(ideas)]
    if mode == "quiz":                        # koi bhi famous player
        return random.choice(PLAYERS)
    if mode == "debate":                      # X vs Y (tribal comment-war)
        a, b = random.sample(PLAYERS[:8], 2)
        return f"{a} vs {b}"
    if mode == "ranking":                     # Top 5 <category>
        return "Top 5 " + random.choice(RANKING_CATEGORIES)
    if mode == "story":                       # rags-to-riches journey
        return f"{random.choice(PLAYERS)} career journey"
    if mode == "player":
        return random.choice(PLAYERS)
    # preview / anything else
    ideas = get_ideas(3, query) or ["FIFA World Cup 2026"]
    return ideas[i % len(ideas)]


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
