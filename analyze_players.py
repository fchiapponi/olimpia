"""
analyze_players.py — Analisi on-court giocatori Olimpia → Excel

Per ciascun giocatore di Olimpia (colonne team2_p1..5), genera un foglio
con tutte le azioni (OFFENSE e DEFENSE) in cui è in campo, nello stesso
formato dei fogli play-call di analyze.py.

Uso:
    python3 analyze_players.py
"""

import csv
from collections import Counter
from pathlib import Path

import openpyxl

from report_common import detail_sheet

BASE = Path(__file__).parent
OUT_DIR = BASE / "output"
OUT_DIR.mkdir(exist_ok=True)

with open(OUT_DIR / "input_enriched.csv", encoding="utf-8") as f:
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
