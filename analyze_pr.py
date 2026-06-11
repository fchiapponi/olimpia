"""
analyze_pr.py — Analisi P&R (Pick & Roll) Olimpia → JSON

Filtra le azioni OFFENSE con una situation che inizia per "P&R" (P&R Handler,
P&R Screener, P&R 1on1, P&R Spot up, ...) e calcola, per ALL + ogni quarto/CT,
le statistiche complessive (stesso formato di analisi_playcalls.json) più
breakdown per Coverage, Screener, Kind of Screen, Roll, Screen Location e
Gravity (Handler/Screener).

Uso:
    python3 analyze_pr.py
"""

import csv
import json
from pathlib import Path

from report_common import build_entry, breakdown_by, breakdown_by_values, get_situations, QUARTERS_LIST

BASE = Path(__file__).parent
OUT_DIR = BASE / "output"
OUT_DIR.mkdir(exist_ok=True)

with open(OUT_DIR / "enriched.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

offense_rows = [r for r in rows if r["Row"] == "OFFENSE"]
pr_rows = [r for r in offense_rows if any(s.startswith("P&R") for s in get_situations(r))]

BREAKDOWN_FIELDS = {
    "by_coverage":        "O COVERAGES",
    "by_screener_pos":    "O SCREENER",
    "by_kind_of_screen":  "O KIND OF SCREEN",
    "by_roll":            "O ROLL",
    "by_screen_location": "O SCREEN LOCATION",
    "gravity_handler":    "GRAVITY HANDLER PLAYER",
    "gravity_screener":   "GRAVITY SCREENER PLAYER",
}

periods = {}
for period_name in ["ALL"] + QUARTERS_LIST:
    period_rows = pr_rows if period_name == "ALL" else [r for r in pr_rows if r["QUARTER"] == period_name]
    entry = build_entry(period_rows)
    entry["by_situation"] = breakdown_by_values(period_rows, get_situations)
    for key, field in BREAKDOWN_FIELDS.items():
        entry[key] = breakdown_by(period_rows, field)
    periods[period_name] = entry

json_path = OUT_DIR / "analisi_pr.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({"periods": periods}, f, ensure_ascii=False)
print(f"JSON salvato:  {json_path}")
