"""
analyze_defense.py — Analisi difensiva Olimpia (azioni DEFENSE) → JSON

Raggruppa le azioni DEFENSE per OPPONENTS PLAY CALLS, rimappando i campi
D SITUATION -> SITUATION e D COVERAGES -> O COVERAGES cosi' build_periods
produce lo stesso formato JSON di analisi_playcalls.json (riusabile dalla
stessa dashboard).

Uso:
    python3 analyze_defense.py
"""

import csv
import json
from collections import Counter
from pathlib import Path

from report_common import build_periods, get_opponent_play_calls

BASE = Path(__file__).parent
OUT_DIR = BASE / "output"
OUT_DIR.mkdir(exist_ok=True)

with open(OUT_DIR / "enriched.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

defense_rows = [r for r in rows if r["Row"] == "DEFENSE"]

for r in defense_rows:
    r["SITUATION"] = r.get("D SITUATION", "")
    r["O COVERAGES"] = r.get("D COVERAGES", "")

opp_play_calls = Counter(pc for r in defense_rows for pc in get_opponent_play_calls(r))

json_rows = []
for pc_name in sorted(opp_play_calls, key=lambda x: -opp_play_calls[x]):
    pc_rows = [r for r in defense_rows if pc_name in get_opponent_play_calls(r)]
    json_rows.append({"play_call": pc_name, "periods": build_periods(pc_rows)})

json_path = OUT_DIR / "analisi_difesa.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(json_rows, f, ensure_ascii=False)
print(f"JSON salvato:  {json_path}")
