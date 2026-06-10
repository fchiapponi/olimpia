"""
analyze.py — Analisi azioni Olimpia Analytics → JSON

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

from report_common import build_periods, get_play_calls, get_situations, ppp_stats

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

rows = list(csv.DictReader(open(OUT_DIR / "enriched.csv")))

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
        data = [r for r in data if any(args.play_call.lower() in pc.lower() for pc in get_play_calls(r))]
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

play_calls = Counter(pc for r in data for pc in get_play_calls(r))

# ---------------------------------------------------------------------------
# Riepilogo finale + salva
# ---------------------------------------------------------------------------

suffix = filter_desc.replace("Row=OFFENSE", "").replace("Row=DEFENSE", "DEFENSE").replace(" | ", "_").replace("=", "-").strip("_")
base_name = f"analisi_playcalls{'_' + suffix if suffix else ''}"

# JSON — struttura completa per la dashboard

json_rows = []
for pc_name in sorted(play_calls, key=lambda x: -play_calls[x]):
    pc_rows = [r for r in data if pc_name in get_play_calls(r)]
    json_rows.append({"play_call": pc_name, "periods": build_periods(pc_rows)})

json_path = OUT_DIR / f"{base_name}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_rows, f, ensure_ascii=False)
print(f"JSON salvato:  {json_path}")

# Stessa analisi raggruppata per SITUATION
situation_counts = Counter(s for r in data for s in get_situations(r))

situation_rows = []
for sit_name in sorted(situation_counts, key=lambda x: -situation_counts[x]):
    sit_rows = [r for r in data if sit_name in get_situations(r)]
    situation_rows.append({"situation": sit_name, "periods": build_periods(sit_rows)})

sit_base_name = f"analisi_situations{'_' + suffix if suffix else ''}"
sit_json_path = OUT_DIR / f"{sit_base_name}.json"
with open(sit_json_path, "w", encoding="utf-8") as f:
    json.dump(situation_rows, f, ensure_ascii=False)
print(f"JSON salvato:  {sit_json_path}")
