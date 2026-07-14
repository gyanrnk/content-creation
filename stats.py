"""
stats.py — ASLI live football stats (free, no API key) script ki GROUND TRUTH ke liye.

Sources:
  1. Wikipedia "2026 FIFA World Cup" -> Goalscorers section (Golden Boot race, LIVE)
  2. TheSportsDB (key-free) -> league table (jab club season chalu ho, Aug-May)

`current_stats()` khud chun leta hai ki abhi kya LIVE hai (WC chal raha ho to golden
boot; warna league table). LLM ko ye asli numbers hi diye jaate hain -> koi hallucination
nahi, har din data BADALTA hai = roz fresh content.
"""

import re
import html
import requests

_H = {"User-Agent": "FootyShorts/1.0 (educational content generator)"}
_WIKI = "https://en.wikipedia.org/w/api.php"
_SDB = "https://www.thesportsdb.com/api/v1/json/3"

# TheSportsDB league ids
_LEAGUES = [("4328", "Premier League"), ("4335", "La Liga"),
            ("4332", "Serie A"), ("4331", "Bundesliga")]


def _section_index(page: str, want: str):
    """Page ke sections me se `want` (regex) wala section index dhoondo."""
    try:
        r = requests.get(_WIKI, params={"action": "parse", "page": page,
                                        "prop": "sections", "format": "json"},
                         headers=_H, timeout=20)
        for s in r.json().get("parse", {}).get("sections", []):
            if re.search(want, s.get("line", ""), re.I):
                return s.get("index")
    except Exception:
        pass
    return None


def wc_top_scorers(page: str = "2026 FIFA World Cup", n: int = 6):
    """Golden Boot race — LIVE Wikipedia se. Returns (rows, summary_line).
    rows = [(player, goals, team), ...] goals ke hisaab se sorted."""
    idx = _section_index(page, r"goalscorer")
    if not idx:
        return [], ""
    try:
        r = requests.get(_WIKI, params={"action": "parse", "page": page,
                                        "prop": "text", "section": idx,
                                        "format": "json"}, headers=_H, timeout=25)
        t = r.json().get("parse", {}).get("text", {}).get("*", "")
    except Exception:
        return [], ""

    sm = re.search(r"There have been ([\d,]+) goals scored in ([\d,]+) matches"
                   r"[^<]*?average of ([\d.]+)", t)
    summary = (f"{sm.group(1)} goals in {sm.group(2)} matches "
               f"({sm.group(3)} per match)") if sm else ""

    rows = []
    parts = re.split(r"<b>(\d+)\s*goals?</b>", t)     # "<b>8 goals</b>" ke baad list
    for i in range(1, len(parts) - 1, 2):
        goals = int(parts[i])
        for li in re.findall(r"<li>(.*?)</li>", parts[i + 1], re.S):
            links = [html.unescape(x) for x in re.findall(r'title="([^"]+)"', li)]
            team = next((x for x in links if "national football team" in x), "")
            player = next((x for x in links
                           if "national football team" not in x and ":" not in x), None)
            if player:
                rows.append((player, goals, team.replace(" national football team", "")))
        if len(rows) >= n:
            break
    return rows[:n], summary


def league_table(n: int = 5):
    """Club season chalu ho to league table (TheSportsDB, key-free).
    Returns (league_name, [(rank, team, points), ...])."""
    import datetime
    yr = datetime.date.today().year
    for season in (f"{yr}-{yr + 1}", f"{yr - 1}-{yr}"):
        for lid, lname in _LEAGUES:
            try:
                r = requests.get(f"{_SDB}/lookuptable.php",
                                 params={"l": lid, "s": season},
                                 headers=_H, timeout=20)
                tbl = r.json().get("table") or []
                rows = [(x.get("intRank"), x.get("strTeam"), x.get("intPoints"))
                        for x in tbl[:n] if x.get("strTeam")]
                if len(rows) >= 3:
                    return lname, rows
            except Exception:
                continue
    return "", []


def current_stats():
    """Abhi jo LIVE hai wahi do. Returns (topic, ground_truth_text) ya (None, "")."""
    rows, summary = wc_top_scorers()
    if len(rows) >= 3:
        lines = [f"{i + 1}. {p} ({tm}) — {g} goals"
                 for i, (p, g, tm) in enumerate(rows)]
        gt = ("GOLDEN BOOT RACE — FIFA World Cup 2026 (LIVE, aaj ka data):\n"
              + "\n".join(lines)
              + (f"\nTournament total: {summary}" if summary else ""))
        return "World Cup 2026 Golden Boot race — top scorers", gt

    lname, rows = league_table()
    if rows:
        lines = [f"{r}. {t} — {p} points" for r, t, p in rows]
        gt = f"{lname} TABLE (LIVE, aaj ka data):\n" + "\n".join(lines)
        return f"{lname} table — top 5 teams", gt

    return None, ""


if __name__ == "__main__":
    topic, gt = current_stats()
    print("TOPIC:", topic)
    print(gt)
