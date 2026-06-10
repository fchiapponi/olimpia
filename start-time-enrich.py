"""
enrich.py — Aggiunge quarter, game_clock, shot_clock al CSV da sync.json

Uso:
    python enrich.py                        # usa input.csv e input/sync.json
    python enrich.py mio.csv input/sync.json
"""

import csv
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent

csv_path  = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "input" / "input.csv"
json_path = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / "input" / "sync.json"
out_dir   = BASE / "output"
out_dir.mkdir(exist_ok=True)
out_path  = out_dir / "input_enriched.csv"

# Carica sync.json e indicizza per video_time
sync = json.loads(json_path.read_text())
index = {round(e["video_time"], 2): e for e in sync}
times = sorted(index)


def lookup(start_time: float) -> dict:
    """Trova il campione più vicino al timestamp dato."""
    t = round(float(start_time), 2)
    # ricerca binaria del più vicino
    import bisect
    i = bisect.bisect_left(times, t)
    candidates = []
    if i < len(times):
        candidates.append(times[i])
    if i > 0:
        candidates.append(times[i - 1])
    nearest = min(candidates, key=lambda x: abs(x - t))
    return index[nearest]


def fix_multi_quarter(rows):
    """Corregge QUARTER con valori multipli (es. '2 Q, 1 Q'), un errore di
    tagging: ogni azione appartiene a un solo quarto. Si sceglie il valore
    che coincide con la riga precedente o successiva."""
    for i, row in enumerate(rows):
        q = row["QUARTER"]
        if "," in q:
            values = [v.strip() for v in q.split(",")]
            neighbors = [rows[j]["QUARTER"] for j in (i - 1, i + 1) if 0 <= j < len(rows)]
            fixed = next((v for v in values if v in neighbors), values[0])
            print(f"QUARTER ambiguo '{q}' -> '{fixed}' (riga {i + 2})")
            row["QUARTER"] = fixed


with open(csv_path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    base = list(reader.fieldnames)
    fieldnames = base + ["ocr_quarter", "start_time_game_clock"]
    rows = list(reader)

fix_multi_quarter(rows)

enriched = []
for row in rows:
    entry = lookup(row["Start time"])
    row["ocr_quarter"]           = entry.get("quarter")
    row["start_time_game_clock"] = entry.get("game_clock")
    enriched.append(row)

with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(enriched)

print(f"Salvato: {out_path}  ({len(enriched)} righe)")
