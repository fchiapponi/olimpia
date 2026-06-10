"""
lineup-enrich.py — Aggiunge lineup, punteggio, player_name e action a enriched.csv

Filtra lineups.csv ai soli eventi EA7 Emporio Armani Milano.
Join su (quarter, player_name): trova l'evento dove il giocatore di lineups
corrisponde a PLAYERS di input, poi prende il clock più vicino dopo start_time_game_clock.

Uso:
    python3 lineup-enrich.py
"""

import csv
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent

out_dir      = BASE / "output"
out_dir.mkdir(exist_ok=True)
in_path      = Path(sys.argv[1]) if len(sys.argv) > 1 else out_dir / "enriched.csv"
lineups_path = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / "input" / "lineups.csv"
out_path     = out_dir / "enriched.csv"

EA7_TEAM_ID = "235"


def clock_to_secs(clock: str) -> int:
    m, s = clock.strip().split(":")
    return int(m) * 60 + int(s)


def normalize_name(name: str) -> str:
    """Rimuove '#XX ' iniziale e spazi per confronto fuzzy."""
    name = re.sub(r"^#\d+\s*", "", name.strip())
    return name.replace(" ", "").lower()


lineups_by_quarter: dict[str, list[dict]] = {}
with open(lineups_path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        q = str(row["quarter"])
        lineups_by_quarter.setdefault(q, []).append(row)

for q in lineups_by_quarter:
    lineups_by_quarter[q].sort(key=lambda r: clock_to_secs(r["clock"]), reverse=True)


QUARTER_MAP = {"CT": "4"}

OFFENSE_ACTIONS = {
    "PERSONAL_FOUL_RECEIVED",
    "TURNOVER",
    "TWO_POINT_MADE", "TWO_POINT_MISSED",
    "THREE_POINT_MADE", "THREE_POINT_MISSED",
    "FREE_THROW_MADE", "FREE_THROW_MISSED",
}

def find_lineup(quarter, game_clock: str, players: str, is_offense: bool = True) -> dict | None:
    q_str = str(quarter or "").strip()
    q_str = QUARTER_MAP.get(q_str, q_str)
    m = re.search(r"\d+", q_str)
    q = m.group() if m else ""
    if q not in lineups_by_quarter or not game_clock:
        return None

    target     = clock_to_secs(game_clock)
    candidates = lineups_by_quarter[q]

    if is_offense:
        # OFFENSE: solo azioni rilevanti, poi match sul giocatore
        eligible = [e for e in candidates if e["action"] in OFFENSE_ACTIONS]
        norm_player = normalize_name(players) if players else ""
        matched = [e for e in eligible if normalize_name(e["player_name"]) == norm_player] if norm_player else []
        pool = matched if matched else eligible if eligible else candidates
    else:
        # DEFENSE: usa tutti gli eventi del quarto
        pool = candidates

    # Prende il clock subito dopo l'azione (clock <= target, il più vicino)
    after = [e for e in pool if clock_to_secs(e["clock"]) <= target]
    if after:
        return max(after, key=lambda e: clock_to_secs(e["clock"]))
    if not is_offense:
        # DEFENSE: nessun evento dopo, prende il più avanzato nel quarto
        return min(pool, key=lambda e: clock_to_secs(e["clock"]))
    return min(pool, key=lambda e: abs(clock_to_secs(e["clock"]) - target))


LINEUP_COLS = [
    "player_name", "action", "action_game_clock",
    "team1_score", "team2_score",
    "team1_p1_name", "team1_p2_name", "team1_p3_name", "team1_p4_name", "team1_p5_name",
    "team2_p1_name", "team2_p2_name", "team2_p3_name", "team2_p4_name", "team2_p5_name",
]

with open(in_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    base_fields = [c for c in reader.fieldnames if c not in LINEUP_COLS]
    fieldnames = base_fields + LINEUP_COLS
    rows = list(reader)

enriched = []
for row in rows:
    is_offense = row.get("Row", "OFFENSE") == "OFFENSE"
    entry = find_lineup(row.get("QUARTER"), row.get("start_time_game_clock"), row.get("PLAYERS", ""), is_offense)
    action_clock = entry["clock"] if entry else ""

    for col in LINEUP_COLS:
        if col == "action_game_clock":
            row[col] = action_clock
        else:
            row[col] = entry[col] if entry else ""
    enriched.append(row)

with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(enriched)

print(f"Salvato: {out_path}  ({len(enriched)} righe)")

# Excel
import openpyxl
xlsx_path = out_path.with_suffix(".xlsx")
wb = openpyxl.Workbook()
ws = wb.active
ws.append(fieldnames)
for row in enriched:
    ws.append([row.get(f, "") for f in fieldnames])
wb.save(xlsx_path)
print(f"Salvato: {xlsx_path}")
