"""
extract_clock.py  —  Extract game clock from a basketball video and build a sync map.

Samples one frame every --interval seconds, OCRs the scoreboard region,
and writes a JSON file mapping video_time → { quarter, game_clock }.

Usage:
    python extract_clock.py <video_path> --roi roi.json --output sync.json
    python extract_clock.py <video_path> --roi roi.json --interval 2 --output sync.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

import cv2
import easyocr
import numpy as np


# ---------------------------------------------------------------------------
# OCR helpers
# ---------------------------------------------------------------------------

_READER: easyocr.Reader | None = None


def get_reader() -> easyocr.Reader:
    global _READER
    if _READER is None:
        print("Loading EasyOCR model (first run may take a moment)...")
        _READER = easyocr.Reader(["en"], gpu=False)
    return _READER


def preprocess(crop: np.ndarray) -> np.ndarray:
    """Upscale and enhance the crop. Handles both light-on-dark and dark-on-light scoreboards."""
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    gray = cv2.resize(gray, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
    # If the image is mostly dark (white text on dark bg), invert before thresholding
    if np.mean(gray) < 128:
        gray = cv2.bitwise_not(gray)
    # CLAHE to boost local contrast on scoreboard fonts
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    gray = clahe.apply(gray)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def ocr_crop(crop: np.ndarray) -> str:
    processed = preprocess(crop)
    reader = get_reader()
    results = reader.readtext(processed, detail=0, paragraph=True)
    return " ".join(results).strip()


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

# Matches: "Q1", "1Q", "1st", "2nd", "3rd", "4th", "OT", "1OT" etc.
_QUARTER_RE = re.compile(
    r"\b(?:Q?([1-4])[a-z]*|([1-4])(?:st|nd|rd|th)|([1-4])Q|(OT|1OT|2OT))\b",
    re.IGNORECASE,
)

# Matches: "10:00", "9:58", "0:03", "10.00" (some broadcasts use dots/commas/semicolons)
_CLOCK_RE = re.compile(r"\b(\d{1,2})[:.;,'](\d{2})\b")

# Shot clock: 1-2 digit number optionally with one decimal (e.g. "3.7", "14", "24")
# Must be between 0.0 and 24.0 — appears after the game clock in the overlay
_SHOT_RE = re.compile(r"\b(2[0-4]|1\d|\d)[.,]?(\d)?\b")


def parse_text(text: str) -> dict | None:
    """Extract quarter, game clock and shot clock from raw OCR text. Returns None if not found."""
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
            quarter = m.group(4).upper()  # OT / 2OT

    clock = None
    clock_end = 0
    m2 = _CLOCK_RE.search(text)
    if m2:
        mins, secs = int(m2.group(1)), int(m2.group(2))
        if mins <= 12 and secs <= 59:
            clock = f"{mins:02d}:{secs:02d}"
            clock_end = m2.end()

    # Shot clock appears after the game clock in the text
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
# Main extraction loop
# ---------------------------------------------------------------------------

def extract(video_path: str, roi: dict, interval: float) -> list[dict]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        sys.exit(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_seconds = total_frames / fps
    step = max(1, int(interval * fps))

    x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]

    results = []
    frame_idx = 0
    prev_parsed = None
    failed_streak = 0

    print(f"Video: {total_seconds:.1f}s  |  FPS: {fps:.1f}  |  Sampling every {interval}s")
    print(f"ROI: x={x} y={y} w={w} h={h}\n")

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = cap.read()
        if not ok:
            break

        video_time = frame_idx / fps
        crop = frame[y : y + h, x : x + w]

        if crop.size == 0:
            frame_idx += step
            continue

        raw_text = ocr_crop(crop)
        parsed = parse_text(raw_text)

        if parsed:
            failed_streak = 0
            prev_parsed = parsed
            entry = {"video_time": round(video_time, 2), **parsed, "raw": raw_text}
        else:
            failed_streak += 1
            # Keep last known clock during dead-ball / timeout (up to 30s gap)
            entry = {
                "video_time": round(video_time, 2),
                "quarter": prev_parsed["quarter"] if prev_parsed else None,
                "game_clock": prev_parsed["game_clock"] if prev_parsed else None,
                "raw": raw_text,
                "interpolated": True,
            }

        results.append(entry)

        pct = video_time / total_seconds * 100
        status = f"{parsed['quarter']} {parsed['game_clock']}" if parsed else f"? ({raw_text[:30]})"
        print(f"\r[{pct:5.1f}%] {video_time:7.1f}s → {status}    ", end="", flush=True)

        frame_idx += step

    cap.release()
    print("\nDone.")
    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extract game clock sync map from basketball video.")
    parser.add_argument("video", help="Path to the video file")
    parser.add_argument("--roi", default="roi.json",
                        help="ROI JSON file from select_roi.py (default: roi.json)")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="Sampling interval in seconds (default: 1.0)")
    parser.add_argument("--output", default="sync.json",
                        help="Output sync map file (default: sync.json)")
    args = parser.parse_args()

    roi_path = Path(args.roi)
    if not roi_path.exists():
        sys.exit(f"ROI file not found: {roi_path}\nRun select_roi.py first.")

    with open(roi_path) as f:
        roi = json.load(f)

    entries = extract(args.video, roi, args.interval)

    with open(args.output, "w") as f:
        json.dump(entries, f, indent=2)

    valid = sum(1 for e in entries if e.get("quarter") and not e.get("interpolated"))
    print(f"\nSync map written to {args.output}")
    print(f"  Total samples : {len(entries)}")
    print(f"  OCR successes : {valid} ({valid / len(entries) * 100:.1f}%)")


if __name__ == "__main__":
    main()
