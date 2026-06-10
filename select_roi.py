"""
select_roi.py  —  Interactively select the scoreboard clock region from a video frame.
Run this once per broadcast type to get the crop coordinates, then pass them to extract_clock.py.

Usage:
    python select_roi.py <video_path> [--second 30]
"""

import argparse
import json
import sys
import cv2


def pick_frame(video_path: str, second: float) -> tuple:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        sys.exit(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(second * fps))
    ok, frame = cap.read()
    cap.release()

    if not ok:
        sys.exit("Could not read frame at the requested second.")

    return frame


def select_roi(frame) -> dict:
    print("\nDrag a rectangle around the CLOCK region (quarter + game time).")
    print("Press ENTER or SPACE to confirm, C to cancel.\n")

    # Scale down if frame is very large so it fits on screen
    h, w = frame.shape[:2]
    scale = min(1.0, 1280 / w, 720 / h)
    display = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1.0 else frame.copy()

    roi = cv2.selectROI("Select clock region — press ENTER to confirm", display, showCrosshair=True)
    cv2.destroyAllWindows()

    if roi == (0, 0, 0, 0):
        sys.exit("No region selected, exiting.")

    x, y, rw, rh = roi
    # Scale back to original pixel coordinates
    coords = {
        "x": int(x / scale),
        "y": int(y / scale),
        "w": int(rw / scale),
        "h": int(rh / scale),
    }
    return coords


def main():
    parser = argparse.ArgumentParser(description="Select scoreboard ROI from a video frame.")
    parser.add_argument("video", help="Path to the video file")
    parser.add_argument("--second", type=float, default=30.0,
                        help="Second in the video to use as reference frame (default: 30)")
    parser.add_argument("--output", default="roi.json",
                        help="Where to save the ROI (default: roi.json)")
    args = parser.parse_args()

    frame = pick_frame(args.video, args.second)
    coords = select_roi(frame)

    with open(args.output, "w") as f:
        json.dump(coords, f, indent=2)

    print(f"ROI saved to {args.output}:")
    print(json.dumps(coords, indent=2))


if __name__ == "__main__":
    main()
