"""
run.py  —  Pipeline completa: selezione cartella → ROI → estrazione OCR → sync.json

Gestisce partite divise in segmenti (Segment 1.mp4, Segment 2.mp4, ...).
Il video_time è cumulativo tra i segmenti.

Uso:
    python run.py
"""

import json
import re
import shutil
import sys
from pathlib import Path

import cv2
import easyocr
import numpy as np


# Quando l'app gira come bundle PyInstaller, copia i modelli in ~/.EasyOCR/model
def _ensure_models():
    if not getattr(sys, "frozen", False):
        return
    bundle_models = Path(sys._MEIPASS) / "easyocr_models"
    dest = Path.home() / ".EasyOCR" / "model"
    dest.mkdir(parents=True, exist_ok=True)
    for f in bundle_models.iterdir():
        target = dest / f.name
        if not target.exists():
            shutil.copy2(f, target)

_ensure_models()


# ---------------------------------------------------------------------------
# Step 1: seleziona la cartella e trova i segmenti
# ---------------------------------------------------------------------------

def pick_segments() -> list[Path]:
    folder = Path(__file__).parent / "input"
    if not folder.is_dir():
        sys.exit(f"Cartella non trovata: {folder}")

    # Cerca file "Segment N.mp4" (case-insensitive)
    segments = sorted(
        [f for f in folder.iterdir() if re.match(r"segment\s*\d+", f.stem, re.IGNORECASE) and f.suffix.lower() in (".mp4", ".avi", ".mov", ".mkv")],
        key=lambda f: int(re.search(r"\d+", f.stem).group())
    )

    if not segments:
        # Fallback: tutti i video nella cartella in ordine alfabetico
        segments = sorted(
            [f for f in folder.iterdir() if f.suffix.lower() in (".mp4", ".avi", ".mov", ".mkv")]
        )

    if not segments:
        sys.exit(f"Nessun video trovato in: {folder}")

    print(f"Trovati {len(segments)} segmenti:")
    for i, s in enumerate(segments, 1):
        print(f"  {i}. {s.name}")

    return segments


# ---------------------------------------------------------------------------
# Step 2: selezione ROI interattiva (una volta sola sul primo segmento)
# ---------------------------------------------------------------------------

def select_roi(video_path: Path) -> dict:
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, int(fps * 5))  # salta 5 secondi per volta

    frame_idx = min(int(fps * 10), int(total * 0.1))

    print("\nNaviga il video finché il tabellone è visibile:")
    print("  → / D  : avanti 5s        ← / A  : indietro 5s")
    print("  SHIFT+→ : avanti 30s      SHIFT+← : indietro 30s")
    print("  ENTER  : conferma e seleziona ROI\n")

    win = "Naviga finché vedi il tabellone — ENTER per selezionare ROI"

    def read_frame(idx):
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, f = cap.read()
        return (ok, f)

    while True:
        frame_idx = max(0, min(frame_idx, total - 1))
        ok, frame = read_frame(frame_idx)
        if not ok:
            frame_idx = max(0, frame_idx - step)
            continue

        h, w = frame.shape[:2]
        scale = min(1.0, 1280 / w, 720 / h)
        display = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1.0 else frame.copy()

        secs = frame_idx / fps
        cv2.putText(display, f"{int(secs // 60):02d}:{int(secs % 60):02d}  (← → per navigare, ENTER per confermare)",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow(win, display)

        key = cv2.waitKey(0) & 0xFF
        if key in (13, 10):  # ENTER
            break
        elif key in (83, 100):  # → o D
            frame_idx += step
        elif key in (81, 97):  # ← o A
            frame_idx -= step
        elif key == 255:  # SHIFT+→ su alcuni sistemi
            frame_idx += step * 6
        elif key == 254:  # SHIFT+← su alcuni sistemi
            frame_idx -= step * 6

    cv2.destroyAllWindows()
    cap.release()

    if not ok:
        sys.exit("Impossibile leggere un frame dal video.")

    h, w = frame.shape[:2]
    scale = min(1.0, 1280 / w, 720 / h)
    display = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1.0 else frame.copy()

    print("Seleziona la regione del CLOCK (quarter + tempo + shot clock) — trascina e premi ENTER.\n")
    roi = cv2.selectROI("Seleziona clock — premi ENTER per confermare", display, showCrosshair=True)
    cv2.destroyAllWindows()

    if roi == (0, 0, 0, 0):
        sys.exit("Nessuna regione selezionata.")

    x, y, rw, rh = roi
    return {
        "x": int(x / scale),
        "y": int(y / scale),
        "w": int(rw / scale),
        "h": int(rh / scale),
    }


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

_QUARTER_RE = re.compile(
    r"\b(?:Q?([1-4])[a-z]*|([1-4])(?:st|nd|rd|th)|([1-4])Q|(OT|1OT|2OT))\b",
    re.IGNORECASE,
)
_CLOCK_RE = re.compile(r"\b(\d{1,2})[:.;,'](\d{2})\b")
_SHOT_RE = re.compile(r"\b(2[0-4]|1\d|\d)[.,]?(\d)?\b")


def preprocess(crop: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    gray = cv2.resize(gray, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
    if np.mean(gray) < 128:
        gray = cv2.bitwise_not(gray)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    gray = clahe.apply(gray)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def parse_text(text: str) -> dict | None:
    quarter = None
    m = _QUARTER_RE.search(text)
    if m:
        if m.group(1):
            quarter = int(m.group(1))
        elif m.group(2):
            quarter = int(m.group(2))
        elif m.group(3):
            quarter = int(m.group(3))
        else:
            quarter = m.group(4).upper()

    clock = None
    clock_end = 0
    m2 = _CLOCK_RE.search(text)
    if m2:
        mins, secs = int(m2.group(1)), int(m2.group(2))
        if mins <= 12 and secs <= 59:
            clock = f"{mins:02d}:{secs:02d}"
            clock_end = m2.end()

    shot_clock = None
    remaining = text[clock_end:] if clock_end else text
    for m3 in _SHOT_RE.finditer(remaining):
        val = float(f"{m3.group(1)}.{m3.group(2)}") if m3.group(2) else float(m3.group(1))
        if 0.0 <= val <= 24.0:
            shot_clock = val
            break

    if quarter is not None and clock is not None:
        return {"quarter": quarter, "game_clock": clock, "shot_clock": shot_clock}
    return None


# ---------------------------------------------------------------------------
# Step 3: estrazione OCR su tutti i segmenti
# ---------------------------------------------------------------------------

def extract_segments(segments: list[Path], roi: dict, interval: float = 1.0) -> list[dict]:
    reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]

    all_entries = []
    time_offset = 0.0  # secondi cumulativi
    prev = None

    for seg_idx, seg_path in enumerate(segments):
        cap = cv2.VideoCapture(str(seg_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_seconds = total_frames / fps
        step = max(1, int(interval * fps))

        print(f"\n[Segmento {seg_idx + 1}/{len(segments)}] {seg_path.name}  ({total_seconds:.0f}s)")

        frame_idx = 0
        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ok, frame = cap.read()
            if not ok:
                break

            local_time = frame_idx / fps
            video_time = round(time_offset + local_time, 2)

            crop = frame[y: y + h, x: x + w]
            if crop.size == 0:
                frame_idx += step
                continue

            processed = preprocess(crop)
            raw_parts = reader.readtext(processed, detail=0, paragraph=True)
            raw_text = " ".join(raw_parts).strip()
            parsed = parse_text(raw_text)

            if parsed:
                prev = parsed
                entry = {"video_time": video_time, "segment": seg_idx + 1, **parsed}
            else:
                entry = {
                    "video_time": video_time,
                    "segment": seg_idx + 1,
                    "quarter": prev["quarter"] if prev else None,
                    "game_clock": prev["game_clock"] if prev else None,
                    "interpolated": True,
                }

            all_entries.append(entry)

            pct = local_time / total_seconds * 100
            status = f"Q{parsed['quarter']} {parsed['game_clock']}" if parsed else f"? ({raw_text[:20]})"
            print(f"\r  [{pct:5.1f}%] {video_time:7.1f}s → {status}    ", end="", flush=True)

            frame_idx += step

        cap.release()
        time_offset += total_seconds

    print("\n\nEstrazione completata.")
    return all_entries


# ---------------------------------------------------------------------------
# Step 4: salva output
# ---------------------------------------------------------------------------

def save_output(folder: Path, entries: list[dict]) -> Path:
    out_path = folder / "sync.json"
    with open(out_path, "w") as f:
        json.dump(entries, f, indent=2)

    valid = sum(1 for e in entries if e.get("quarter") and not e.get("interpolated"))
    total = len(entries)
    accuracy = valid / total * 100 if total else 0
    duration = entries[-1]["video_time"] if entries else 0

    print(f"\nFile salvato : {out_path}")
    print(f"Durata totale: {duration:.0f}s ({duration/60:.1f} min)")
    print(f"Campioni     : {total}")
    print(f"OCR riusciti : {valid} ({accuracy:.1f}%)")

    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== Video Sync — Olimpia Analytics ===\n")

    segments = pick_segments()

    roi = select_roi(segments[0])
    print(f"ROI selezionata: {roi}")

    entries = extract_segments(segments, roi)
    out_path = save_output(segments[0].parent, entries)

    print(f"\nCaricala nell'app Olimpia Analytics: {out_path}")


if __name__ == "__main__":
    main()
