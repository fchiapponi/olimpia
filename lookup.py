"""
lookup.py  —  Query the sync map in both directions.

Given a video timestamp → returns the game clock.
Given a quarter + game clock → returns the video timestamp.

Usage:
    python lookup.py --video-time 1523.4          # video ts → game clock
    python lookup.py --quarter 3 --clock 04:22    # game clock → video ts
"""

import argparse
import json
import sys
from pathlib import Path


def load_sync(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def clock_to_seconds(clock: str) -> int:
    """'04:22' → 262"""
    m, s = clock.split(":")
    return int(m) * 60 + int(s)


def video_time_to_game(entries: list[dict], video_time: float) -> dict | None:
    """Find the entry closest to the given video timestamp."""
    valid = [e for e in entries if e.get("quarter") and e.get("game_clock")]
    if not valid:
        return None
    return min(valid, key=lambda e: abs(e["video_time"] - video_time))


def game_to_video_time(entries: list[dict], quarter, clock: str) -> dict | None:
    """Find the video timestamp for a given quarter + game clock."""
    target = clock_to_seconds(clock)
    valid = [
        e for e in entries
        if str(e.get("quarter")) == str(quarter) and e.get("game_clock")
    ]
    if not valid:
        return None
    return min(valid, key=lambda e: abs(clock_to_seconds(e["game_clock"]) - target))


def fmt_video_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"


def main():
    parser = argparse.ArgumentParser(description="Query the video ↔ game clock sync map.")
    parser.add_argument("--sync", default="sync.json", help="Sync map JSON (default: sync.json)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--video-time", type=float, metavar="SECONDS",
                       help="Video timestamp in seconds → game clock")
    group.add_argument("--quarter", metavar="Q",
                       help="Quarter (1-4 or OT) for game-clock lookup")
    parser.add_argument("--clock", metavar="MM:SS",
                        help="Game clock (e.g. 04:22) — required with --quarter")
    args = parser.parse_args()

    if not Path(args.sync).exists():
        sys.exit(f"Sync file not found: {args.sync}")

    entries = load_sync(args.sync)

    if args.video_time is not None:
        result = video_time_to_game(entries, args.video_time)
        if not result:
            sys.exit("No matching entry found.")
        print(f"Video {fmt_video_time(args.video_time)}  →  Q{result['quarter']} {result['game_clock']}")

    else:
        if not args.clock:
            sys.exit("--clock MM:SS is required when using --quarter")
        result = game_to_video_time(entries, args.quarter, args.clock)
        if not result:
            sys.exit(f"No entry found for Q{args.quarter} {args.clock}")
        print(f"Q{args.quarter} {args.clock}  →  Video {fmt_video_time(result['video_time'])}  ({result['video_time']:.2f}s)")


if __name__ == "__main__":
    main()
