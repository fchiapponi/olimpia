"""
analyze.py — Analisi azioni Olimpia Analytics → Excel

Uso:
    python3 analyze.py
    python3 analyze.py --quarter "1 Q"
    python3 analyze.py --pressing MAN
    python3 analyze.py --quarter "1 Q" --pressing MAN
    python3 analyze.py --situation "P&R Handler"
    python3 analyze.py --play-call HEAD
    python3 analyze.py --row DEFENSE
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import openpyxl

from report_common import detail_sheet, get_situations, ppp_stats

BASE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Argomenti
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--quarter",   help="Es: '1 Q' o '1 Q,2 Q'")
parser.add_argument("--pressing",  help="MAN o ZONE")
parser.add_argument("--situation", help="Filtra per SITUATION")
parser.add_argument("--play-call", help="Filtra per PLAY CALLS")
parser.add_argument("--row",       default="OFFENSE", help="OFFENSE (default) o DEFENSE")
args = parser.parse_args()

# ---------------------------------------------------------------------------
# Carica e filtra
# ---------------------------------------------------------------------------

OUT_DIR = BASE / "output"
OUT_DIR.mkdir(exist_ok=True)

rows = list(csv.DictReader(open(OUT_DIR / "input_enriched.csv")))

def apply_filters(data):
    if args.row:
        data = [r for r in data if r["Row"] == args.row]
    if args.quarter:
        quarters = [q.strip() for q in args.quarter.split(",")]
        data = [r for r in data if r["QUARTER"] in quarters]
    if args.pressing:
        data = [r for r in data if r["PRESSING"].upper() == args.pressing.upper()]
    if args.situation:
        data = [r for r in data if args.situation.lower() in r["SITUATION"].lower()]
    if args.play_call:
        data = [r for r in data if args.play_call.lower() in r["PLAY CALLS"].lower()]
    return data

data = apply_filters(rows)
N = len(data)

filter_parts = [f"Row={args.row}"]
if args.quarter:   filter_parts.append(f"Quarter={args.quarter}")
if args.pressing:  filter_parts.append(f"Pressing={args.pressing}")
if args.situation: filter_parts.append(f"Situation={args.situation}")
if args.play_call: filter_parts.append(f"PlayCall={args.play_call}")
filter_desc = " | ".join(filter_parts)

if N == 0:
    print("Nessuna azione con questi filtri.")
    exit()

# ---------------------------------------------------------------------------
# Workbook
# ---------------------------------------------------------------------------

wb = openpyxl.Workbook()
wb.remove(wb.active)

play_calls = Counter(r["PLAY CALLS"] for r in data if r["PLAY CALLS"])
pt_rows    = [r for r in data if r["PAINT TOUCHES"]]
situations = Counter(s for r in data for s in get_situations(r))
or_rows    = [r for r in data if any("OR" == s for s in get_situations(r)) or "OR" in r["PLAY CALLS"]]
fb_rows    = [r for r in data if any("FB" == s for s in get_situations(r)) or "FB" in r["PLAY CALLS"]]
pr_rows    = [r for r in data if any("P&R" in s for s in get_situations(r))]
grav_rows  = [r for r in data if r["GRAVITY HANDLER PLAYER"] or r["GRAVITY SCREENER PLAYER"]]
bp         = [r for r in data if r["PLAN/BROKEN PLAY"]]

# ---------------------------------------------------------------------------
# Per Play Call — un foglio per ogni play call
# ---------------------------------------------------------------------------

for pc_name in sorted(play_calls, key=lambda x: -play_calls[x]):
    pc_rows = [r for r in data if r["PLAY CALLS"] == pc_name]
    detail_sheet(wb, pc_name, pc_rows)

# ---------------------------------------------------------------------------
# Riepilogo finale + salva
# ---------------------------------------------------------------------------

suffix = filter_desc.replace("Row=OFFENSE", "").replace("Row=DEFENSE", "DEFENSE").replace(" | ", "_").replace("=", "-").strip("_")
base_name = f"analisi_playcalls{'_' + suffix if suffix else ''}"

# Excel
xlsx_path = OUT_DIR / f"{base_name}.xlsx"
wb.save(xlsx_path)
print(f"Excel salvato: {xlsx_path}")

# JSON — struttura completa per la dashboard
QUARTERS_LIST = ["1 Q", "2 Q", "3 Q", "4 Q", "CT"]

def cross(rows_a: list[dict], get_a, get_b) -> dict:
    """Incrocio: {val_a: {val_b: count}}"""
    result: dict = {}
    for r in rows_a:
        for a in get_a(r):
            for b in get_b(r):
                result.setdefault(a, {})
                result[a][b] = result[a].get(b, 0) + 1
    return result

def pivot(rows_a: list[dict], get_vals) -> dict:
    """Per ogni valore, conteggio per quarto: {val: {quarter: count}}"""
    result: dict = {}
    for r in rows_a:
        q = r.get("QUARTER", "")
        for v in get_vals(r):
            result.setdefault(v, {q: 0 for q in QUARTERS_LIST})
            result[v][q] = result[v].get(q, 0) + 1
    return result

json_rows = []
for pc_name in sorted(play_calls, key=lambda x: -play_calls[x]):
    pc_rows = [r for r in data if r["PLAY CALLS"] == pc_name]
    N = len(pc_rows)

    get_res  = lambda r: [r["RESULTS"]] if r.get("RESULTS") else []
    get_sit  = lambda r: get_situations(r)
    get_pt   = lambda r: [r["PAINT TOUCHES"]] if r.get("PAINT TOUCHES") else ["Senza"]
    get_cov  = lambda r: [r["O COVERAGES"]] if r.get("O COVERAGES") else []
    get_ql   = lambda r: [r["QUALITY"]] if r.get("QUALITY") else []
    get_press= lambda r: [r["PRESSING"]] if r.get("PRESSING") else []
    get_sl   = lambda r: [r["Shot Location"]] if r.get("Shot Location") else []
    get_bp   = lambda r: ["Broken Play"] if r.get("PLAN/BROKEN PLAY") else ["Non Broken"]

    qvals = [float(r["QUALITY"]) for r in pc_rows if r.get("QUALITY") and r["QUALITY"].replace('.','').isdigit()]

    json_rows.append({
        "play_call":   pc_name,
        "total":       N,
        "by_quarter":  {q: sum(1 for r in pc_rows if r["QUARTER"] == q) for q in QUARTERS_LIST},
        # punti per possesso
        "ppp":            ppp_stats(pc_rows),
        "ppp_by_quarter": {q: ppp_stats([r for r in pc_rows if r["QUARTER"] == q]) for q in QUARTERS_LIST},
        # distribuzioni complete
        "results":       dict(Counter(r["RESULTS"] for r in pc_rows if r.get("RESULTS"))),
        "situations":    dict(Counter(s for r in pc_rows for s in get_situations(r))),
        "shot_locations":dict(Counter(r["Shot Location"] for r in pc_rows if r.get("Shot Location"))),
        "o_coverages":   dict(Counter(r["O COVERAGES"] for r in pc_rows if r.get("O COVERAGES"))),
        "pressing":      dict(Counter(r["PRESSING"] for r in pc_rows if r.get("PRESSING"))),
        "paint_touches": dict(Counter(r["PAINT TOUCHES"] if r.get("PAINT TOUCHES") else "Senza" for r in pc_rows)),
        "quality":       dict(Counter(r["QUALITY"] for r in pc_rows if r.get("QUALITY"))),
        "broken_play":   sum(1 for r in pc_rows if r.get("PLAN/BROKEN PLAY")),
        "quality_avg":   round(sum(qvals)/len(qvals), 2) if qvals else None,
        "paint_touch_n": sum(1 for r in pc_rows if r.get("PAINT TOUCHES")),
        # pivot per quarto
        "pivot_results":    pivot(pc_rows, get_res),
        "pivot_situations": pivot(pc_rows, get_sit),
        "pivot_coverages":  pivot(pc_rows, get_cov),
        "pivot_shot_loc":   pivot(pc_rows, get_sl),
        "pivot_quality":    pivot(pc_rows, get_ql),
        "pivot_pressing":   pivot(pc_rows, get_press),
        "pivot_paint":      pivot(pc_rows, get_pt),
        "pivot_broken":     pivot(pc_rows, get_bp),
        # legami
        "sit_x_results":  cross(pc_rows, get_sit, get_res),
        "sit_x_paint":    cross(pc_rows, get_sit, lambda r: [r["PAINT TOUCHES"]] if r.get("PAINT TOUCHES") else []),
        "sit_x_quality":  cross(pc_rows, get_sit, get_ql),
        "cov_x_results":  cross(pc_rows, get_cov, get_res),
        "paint_x_results":cross(pc_rows, get_pt, get_res),
    })

json_path = OUT_DIR / f"{base_name}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_rows, f, ensure_ascii=False)
print(f"JSON salvato:  {json_path}")
