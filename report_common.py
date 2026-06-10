"""
report_common.py — Helper condivisi per le statistiche per periodo
(usate da analyze.py e analyze_players.py per generare i JSON).
"""

import re
from collections import Counter

# ---------------------------------------------------------------------------
# Punti per possesso
# ---------------------------------------------------------------------------

_FT_RE         = re.compile(r"^(\d+)-(\d+)\s*FT$")       # "2-2 FT" -> 2 punti su 2 liberi
_SHOT_BONUS_RE = re.compile(r"^(\d)P\s*\+\s*(\d)$")      # "2P + 1" -> 2 (tiro) + 1 (libero bonus)
_SHOT_RE       = re.compile(r"^(IN|\dP)([+-])$")         # "IN+", "2P-", "3P+", ...


def result_points(result):
    """Ritorna (punti, è_possesso) per un valore RESULTS.

    in/2p/3p + = segnato (2 o 3 punti), - = sbagliato (0 punti)
    X-Y FT = X punti sui liberi (X segnati su Y)
    F e OB non sono possessi
    """
    r = (result or "").strip().upper()
    if not r or r in ("F", "OB"):
        return 0, False
    if r.startswith("TO"):
        return 0, True

    m = _FT_RE.match(r)
    if m:
        return int(m.group(1)), True

    m = _SHOT_BONUS_RE.match(r)
    if m:
        return int(m.group(1)) + int(m.group(2)), True

    m = _SHOT_RE.match(r)
    if m:
        base = 3 if m.group(1) == "3P" else 2
        return (base if m.group(2) == "+" else 0), True

    return 0, False


def ppp_stats(rows):
    """Punti totali, possessi e punti-per-possesso per una lista di righe."""
    points = possessions = 0
    for r in rows:
        p, is_poss = result_points(r.get("RESULTS"))
        if is_poss:
            points += p
            possessions += 1
    ppp = round(points / possessions, 2) if possessions else None
    return {"points": points, "possessions": possessions, "ppp": ppp}


def get_situations(row):
    """Espande valori multipli separati da virgola: 'OR, P&R Handler' → ['OR', 'P&R Handler']"""
    val = row.get("SITUATION", "")
    return [s.strip() for s in val.split(",")] if val else []


def get_play_calls(row):
    """PLAY CALLS più, se presenti, BOB/SOB (rimesse laterali viste come play call a sé)."""
    return [v for v in (row.get("PLAY CALLS"), row.get("BOB"), row.get("SOB")) if v]


def get_opponent_play_calls(row):
    """OPPONENTS PLAY CALLS, split su virgola e deduplicato (es. 'DRAG, DRAG' -> ['DRAG'])."""
    val = row.get("OPPONENTS PLAY CALLS", "")
    if not val:
        return []
    seen = []
    for p in (s.strip() for s in val.split(",")):
        if p and p not in seen:
            seen.append(p)
    return seen


# ---------------------------------------------------------------------------
# Statistiche per periodo (ALL + quarti) — usate da analyze.py e analyze_players.py
# ---------------------------------------------------------------------------

QUARTERS_LIST = ["1 Q", "2 Q", "3 Q", "4 Q", "CT"]


def cross(rows_a, get_a, get_b):
    """Incrocio: {val_a: {val_b: count}}"""
    result = {}
    for r in rows_a:
        for a in get_a(r):
            for b in get_b(r):
                result.setdefault(a, {})
                result[a][b] = result[a].get(b, 0) + 1
    return result


def build_entry(group_rows):
    """Statistiche complete per un gruppo di righe (play call, situation o giocatore), per un singolo periodo."""
    N = len(group_rows)

    get_res  = lambda r: [r["RESULTS"]] if r.get("RESULTS") else []
    get_sit  = lambda r: get_situations(r)
    get_pt   = lambda r: [r["PAINT TOUCHES"]] if r.get("PAINT TOUCHES") else ["Senza"]
    get_cov  = lambda r: [r["O COVERAGES"]] if r.get("O COVERAGES") else []
    get_ql   = lambda r: [r["QUALITY"]] if r.get("QUALITY") else []

    qvals = [float(r["QUALITY"]) for r in group_rows if r.get("QUALITY") and r["QUALITY"].replace('.', '').isdigit()]
    broken_n = sum(1 for r in group_rows if r.get("PLAN/BROKEN PLAY"))

    return {
        "total":       N,
        "ppp":         ppp_stats(group_rows),
        # distribuzioni complete
        "results":       dict(Counter(r["RESULTS"] for r in group_rows if r.get("RESULTS"))),
        "situations":    dict(Counter(s for r in group_rows for s in get_situations(r))),
        "shot_locations":dict(Counter(r["Shot Location"] for r in group_rows if r.get("Shot Location"))),
        "o_coverages":   dict(Counter(r["O COVERAGES"] for r in group_rows if r.get("O COVERAGES"))),
        "pressing":      dict(Counter(r["PRESSING"] for r in group_rows if r.get("PRESSING"))),
        "paint_touches": dict(Counter(r["PAINT TOUCHES"] if r.get("PAINT TOUCHES") else "Senza" for r in group_rows)),
        "quality":       dict(Counter(r["QUALITY"] for r in group_rows if r.get("QUALITY"))),
        "broken_play":      broken_n,
        "broken_play_dist": {"Broken Play": broken_n, "Non Broken": N - broken_n} if N else {},
        "quality_avg":   round(sum(qvals)/len(qvals), 2) if qvals else None,
        "paint_touch_n": sum(1 for r in group_rows if r.get("PAINT TOUCHES")),
        # legami
        "sit_x_results":  cross(group_rows, get_sit, get_res),
        "sit_x_paint":    cross(group_rows, get_sit, lambda r: [r["PAINT TOUCHES"]] if r.get("PAINT TOUCHES") else []),
        "sit_x_quality":  cross(group_rows, get_sit, get_ql),
        "cov_x_results":  cross(group_rows, get_cov, get_res),
        "paint_x_results":cross(group_rows, get_pt, get_res),
    }


def build_periods(group_rows):
    """Statistiche per tutta la partita (ALL) e per ciascun periodo (quarti + CT)."""
    periods = {"ALL": build_entry(group_rows)}
    for q in QUARTERS_LIST:
        periods[q] = build_entry([r for r in group_rows if r["QUARTER"] == q])
    return periods
