"""
analyze_players.py — Analisi on-court giocatori Olimpia → Excel + JSON

Per ciascun giocatore di Olimpia (colonne team2_p1..5):
- Excel: un foglio con tutte le azioni (OFFENSE e DEFENSE) in cui è in campo,
  nello stesso formato dei fogli play-call di analyze.py.
- JSON: statistiche offensive (stesso formato di analisi_playcalls.json)
  per le azioni OFFENSE in cui è in campo.

Uso:
    python3 analyze_players.py
"""

import csv
import json
from collections import Counter
from pathlib import Path

import openpyxl

from report_common import build_periods, detail_sheet

BASE = Path(__file__).parent
OUT_DIR = BASE / "output"
OUT_DIR.mkdir(exist_ok=True)

with open(OUT_DIR / "enriched.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

TEAM_COLS = [f"team2_p{i}_name" for i in range(1, 6)]

on_court_counts = Counter(
    r[c] for r in rows for c in TEAM_COLS if r.get(c)
)

wb = openpyxl.Workbook()
wb.remove(wb.active)

for player in sorted(on_court_counts, key=lambda x: -on_court_counts[x]):
    player_rows = [r for r in rows if any(r.get(c) == player for c in TEAM_COLS)]
    detail_sheet(wb, player, player_rows)

xlsx_path = OUT_DIR / "analisi_giocatori.xlsx"
wb.save(xlsx_path)
print(f"Excel salvato: {xlsx_path}")

# ---------------------------------------------------------------------------
# JSON — statistiche offensive on-court, stesso formato della dashboard
# ---------------------------------------------------------------------------

offense_rows = [r for r in rows if r["Row"] == "OFFENSE"]

player_json_rows = []
for player in sorted(on_court_counts, key=lambda x: -on_court_counts[x]):
    on_court_rows = [r for r in offense_rows if any(r.get(c) == player for c in TEAM_COLS)]
    player_json_rows.append({"player": player, "periods": build_periods(on_court_rows)})

json_path = OUT_DIR / "analisi_giocatori.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(player_json_rows, f, ensure_ascii=False)
print(f"JSON salvato:  {json_path}")
