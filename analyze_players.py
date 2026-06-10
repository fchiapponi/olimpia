"""
analyze_players.py — Analisi on-court giocatori Olimpia → JSON

Per ciascun giocatore di Olimpia (colonne team2_p1..5): statistiche
offensive (stesso formato di analisi_playcalls.json) per le azioni
OFFENSE in cui è in campo.

Uso:
    python3 analyze_players.py
"""

import csv
import json
from collections import Counter
from pathlib import Path

from report_common import build_periods

BASE = Path(__file__).parent
OUT_DIR = BASE / "output"
OUT_DIR.mkdir(exist_ok=True)

with open(OUT_DIR / "enriched.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

TEAM_COLS = [f"team2_p{i}_name" for i in range(1, 6)]

on_court_counts = Counter(
    r[c] for r in rows for c in TEAM_COLS if r.get(c)
)

offense_rows = [r for r in rows if r["Row"] == "OFFENSE"]

player_json_rows = []
for player in sorted(on_court_counts, key=lambda x: -on_court_counts[x]):
    on_court_rows = [r for r in offense_rows if any(r.get(c) == player for c in TEAM_COLS)]
    player_json_rows.append({"player": player, "periods": build_periods(on_court_rows)})

json_path = OUT_DIR / "analisi_giocatori.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(player_json_rows, f, ensure_ascii=False)
print(f"JSON salvato:  {json_path}")

# ---------------------------------------------------------------------------
# JSON — statistiche difensive on-court (PPP concesso mentre il giocatore è in campo)
# ---------------------------------------------------------------------------

defense_rows = [r for r in rows if r["Row"] == "DEFENSE"]
for r in defense_rows:
    r["SITUATION"] = r.get("D SITUATION", "")
    r["O COVERAGES"] = r.get("D COVERAGES", "")

player_defense_json_rows = []
for player in sorted(on_court_counts, key=lambda x: -on_court_counts[x]):
    on_court_def_rows = [r for r in defense_rows if any(r.get(c) == player for c in TEAM_COLS)]
    player_defense_json_rows.append({"player": player, "periods": build_periods(on_court_def_rows)})

defense_json_path = OUT_DIR / "analisi_giocatori_difesa.json"
with open(defense_json_path, "w", encoding="utf-8") as f:
    json.dump(player_defense_json_rows, f, ensure_ascii=False)
print(f"JSON salvato:  {defense_json_path}")
