"""
trends.py — Aaj ke trending football topics laata hai (FREE, no key).

Google News RSS use karta hai. Timely content = algorithm boost = zyada reach.

Use:
    env\\Scripts\\python.exe trends.py            # default football trends
    env\\Scripts\\python.exe trends.py "Messi"    # kisi topic ke trends
"""

import sys
import re
import html
import urllib.parse
import xml.etree.ElementTree as ET
import requests

_HEADERS = {"User-Agent": "Mozilla/5.0 (FootyShorts/1.0)"}


def get_trending(query: str = None, n: int = 12) -> list[str]:
    """Current football headlines -> short topic strings (clean, deduped)."""
    q = query or "football OR soccer world cup"
    url = ("https://news.google.com/rss/search?q="
           + urllib.parse.quote(q)
           + "&hl=en-IN&gl=IN&ceid=IN:en")
    try:
        r = requests.get(url, headers=_HEADERS, timeout=20)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        out = []
        for it in root.findall(".//item"):
            t = html.unescape(it.findtext("title") or "").strip()
            # " - Publisher" suffix hatao
            t = re.sub(r"\s+-\s+[^-]+$", "", t).strip()
            if t and t not in out and len(t) > 15:
                out.append(t)
            if len(out) >= n:
                break
        return out
    except Exception as e:
        print(f"[trends] failed: {e}")
        return []


def wiki_facts(name: str) -> str:
    """Player/team ka Wikipedia intro (REAL career facts: clubs, trophies, records) —
    script grounding ke liye taaki LLM invent na kare. Fail par khaali."""
    import urllib.parse
    if not name or not name.strip():
        return ""
    try:
        r = requests.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + urllib.parse.quote(name.strip().replace(" ", "_")),
            headers=_HEADERS, timeout=15)
        if r.status_code == 200:
            ex = (r.json().get("extract") or "").strip()
            return ex[:800]
    except Exception:
        pass
    return ""


def current_context(topic: str = None, n: int = 8, mode: str = "") -> str:
    """Aaj ki REAL football headlines — script LLM ko grounding dene ke liye.

    Ye 'ground truth' hai: eliminated teams, latest results etc. LLM inke against
    kuch nahi bolega (stale prediction se bachne ke liye).

    mode='pundit' pe alag search chalti he — aur ye zaroori he. Sirf player ka naam
    search karne pe aam khabrein aati thi ("Mbappe EA Sports FC 27 cover star"), jinme
    koi behes hoti hi nahi. Model ke paas jodne ko kuch nahi hota tha, to wo 'which is
    why' jaise NAKLI connector chipka deta tha. Reaction-wale shabd daalne pe asli panel
    behes milti he — jaise "Henry and Ibrahimovic reject Donovan's France 'arrogance'
    claim" — jisme scene, naam aur takraar teeno hote he.
    """
    if mode == "pundit" and topic and "what pundits" not in topic:
        # FIGHT-FIRST topic: topic khud ek headline he ("Eni Aluko defends stance amid
        # Laura Woods and Ian Wright row"). Wahi pehla fact he; uske log-naamon se aur
        # coverage kheencho taaki model ke paas 2-3 asli facts hon.
        names = [w.strip(",.'‘’“”") for w in topic.split()
                 if w[:1].isupper() and len(w) > 3][:4]
        heads = [topic]
        try:
            for h in get_trending(" ".join(names[:2]) + " football", n=n):
                if h != topic and any(nm.lower() in h.lower() for nm in names):
                    heads.append(h)
        except Exception:
            pass
        return "\n".join(f"- {h}" for h in heads[:n])

    if mode == "pundit" and topic:
        who = topic.replace("what pundits and legends are saying about", "").strip()
        heads = []
        # SIRF reaction-wali queries. Plain naam wali search yahan JAAN-BOOJH KE nahi he:
        # usse "Mbappe EA Sports FC 27 cover star" jaisi aam khabrein aa jaati thi aur
        # script beech me unhi pe bhatak jaati thi. Kam headlines behtar he, bhatakne se.
        # "football" har query me zaroori he — 'pundit' akela SNOOKER pundits ki khabrein
        # bhi le aata tha (Shaun Murphy/Stephen Hendry ek Yamal script me ghus gaye the).
        for q in (f"{who} football pundit reaction said slammed praised",
                  f"{who} football Henry Ibrahimovic Neville Rooney criticised",
                  f"{who} football pundits react debate row"):
            for h in get_trending(q, n=n):
                if h not in heads:
                    heads.append(h)
            if len(heads) >= n:
                break
        # RELEVANCE GATE: headline me player ka naam hona hi chahiye. Bina iske Google
        # ki 'pundit' ki koi bhi khabar (Paredes-Gavi jhagda, snooker drama) ghus jaati
        # thi aur model unhe silai karke bina-connection wali script bana deta tha.
        last = who.split()[-1].lower() if who else ""
        relevant = [h for h in heads if last and last in h.lower()]
        if len(relevant) >= 2:
            return "\n".join(f"- {h}" for h in relevant[:n])
        print(f"[trends] pundit: '{who}' pe sirf {len(relevant)} asli reaction "
              f"headline mili (kam se kam 2 chahiye) -> koi grounding nahi")
        return ""

    heads = get_trending(topic or "FIFA World Cup 2026 result", n=n)
    if not heads:
        # topic-specific na mile to general WC news try karo
        heads = get_trending("FIFA World Cup 2026", n=n)
    return "\n".join(f"- {h}" for h in heads) if heads else ""


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"\n🔥 Trending football topics{' for ' + repr(q) if q else ''}:\n")
    for i, t in enumerate(get_trending(q), 1):
        print(f"  {i}. {t}")
    print("\nEk topic uthao aur config.TOPIC me daalo (ya app me use karo).\n")
