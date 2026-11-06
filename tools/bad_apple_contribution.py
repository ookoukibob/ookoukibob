#!/usr/bin/env python3
"""Convert a local video into a GitHub-contribution-style animated GIF.

The output is a 53 x 7 grid by default. Every sampled video frame is reduced
into one intensity value per cell, then rendered as colored contribution
squares. No drawing or image-generation service is involved.

Install:
    python -m pip install opencv-python-headless pillow

Example:
    python tools/bad_apple_contribution.py bad_apple.mp4 \
        --output assets/bad-apple-contribution.gif --fps 8

The input video is read locally and is never copied into the output folder.
Only publish/share derivative media if you have the rights or permission to
do so. A GIF is silent; README images cannot carry the original audio track.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw
except ImportError as exc:
    missing = getattr(exc, "name", "a required package")
    raise SystemExit(
        f"Missing dependency: {missing}. Install with: "
        "python -m pip install opencv-python-headless pillow"
    ) from exc


PALETTES: dict[str, list[tuple[int, int, int]]] = {
    "github": [
        (22, 27, 34),
        (14, 68, 41),
        (0, 109, 50),
        (38, 166, 65),
        (57, 211, 83),
    ],
    "mono": [
        (13, 17, 23),
        (48, 54, 61),
        (110, 118, 129),
        (201, 209, 217),
        (255, 255, 255),
    ],
    "tokyonight": [
        (26, 27, 39),
        (65, 72, 104),
        (86, 95, 137),
        (122, 162, 247),
        (187, 154, 247),
    ],
}

LEVEL_THRESHOLDS = (24, 72, 132, 196)


def build_palette(colors: Sequence[tuple[int, int, int]]) -> list[int]:
    """Return a 256-entry RGB palette suitable for Pillow P-mode images."""
    flat = [channel for color in colors for channel in color]
    return flat + [0] * (768 - len(flat))


def render_frame(
    bgr_frame: np.ndarray,
    *,
    width: int,
    height: int,
    cell_size: int,
    gap: int,
    palette: Sequence[tuple[int, int, int]],
    invert: bool,
    equalize: bool,
) -> Image.Image:
    gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
    if equalize:
        gray = cv2.equalizeHist(gray)

    pixels = cv2.resize(gray, (width, height), interpolation=cv2.INTER_AREA)
    if invert:
        pixels = 255 - pixels

    indices = np.digitize(pixels, LEVEL_THRESHOLDS).astype(np.uint8)

    image_width = width * cell_size + (width - 1) * gap
    image_height = height * cell_size + (height - 1) * gap
    image = Image.new("P", (image_width, image_height), color=0)
    image.putpalette(build_palette(palette))
    draw = ImageDraw.Draw(image)

    for y in range(height):
        top = y * (cell_size + gap)
        for x in range(width):
            left = x * (cell_size + gap)
            index = int(indices[y, x])
            draw.rectangle(
                (left, top, left + cell_size - 1, top + cell_size - 1),
                fill=index,
            )
    return image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Turn a local video into a 53x7 contribution-grid GIF."
    )
    parser.add_argument("video", type=Path, help="Path to a local video file")
    parser.add_argument(
        "--output", type=Path, default=Path("bad-apple-contribution.gif"),
        help="Output GIF path (default: ./bad-apple-contribution.gif)",
    )
    parser.add_argument("--fps", type=float, default=8.0,
                        help="Output animation frame rate (default: 8; range 1-20)")
    parser.add_argument("--width", type=int, default=53,
                        help="Grid columns (default: 53)")
    parser.add_argument("--height", type=int, default=7,
                        help="Grid rows (default: 7)")
    parser.add_argument("--cell-size", type=int, default=10,
                        help="Square cell size in pixels (default: 10)")
    parser.add_argument("--gap", type=int, default=3,
                        help="Gap between cells in pixels (default: 3)")
    parser.add_argument("--palette", choices=tuple(PALETTES), default="github",
                        help="Cell color palette (default: github)")
    parser.add_argument("--start", type=float, default=0.0,
                        help="Start time in seconds (default: 0)")
    parser.add_argument("--duration", type=float, default=None,
                        help="Maximum output duration in seconds (default: full video)")
    parser.add_argument("--invert", action="store_true",
                        help="Invert brightness if the source has a dark subject on a light background")
    parser.add_argument("--no-equalize", action="store_true",
                        help="Disable histogram equalization")
    args = parser.parse_args()

    if not args.video.is_file():
        parser.error(f"Input video does not exist: {args.video}")
    if not (1.0 <= args.fps <= 20.0):
        parser.error("--fps must be between 1 and 20")
    if args.width < 1 or args.height < 1:
        parser.error("--width and --height must be positive")
    if not (2 <= args.cell_size <= 64):
        parser.error("--cell-size must be between 2 and 64")
    if not (0 <= args.gap <= 32):
        parser.error("--gap must be between 0 and 32")
    if args.start < 0 or (args.duration is not None and args.duration <= 0):
        parser.error("--start must be non-negative and --duration must be positive")
    return args


def main() -> int:
    args = parse_args()
    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        print(f"Error: could not open video: {args.video}", file=sys.stderr)
        return 2

    source_fps = float(capture.get(cv2.CAP_PROP_FPS))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if not np.isfinite(source_fps) or source_fps <= 0:
        capture.release()
        print("Error: video does not report a valid frame rate.", file=sys.stderr)
        return 2

    total_duration = frame_count / source_fps if frame_count > 0 else None
    if total_duration is not None and args.start >= total_duration:
        capture.release()
        print("Error: --start is beyond the end of the video.", file=sys.stderr)
        return 2

    end_time = total_duration
    if args.duration is not None:
        requested_end = args.start + args.duration
        end_time = min(requested_end, total_duration) if total_duration else requested_end

    first_frame = int(round(args.start * source_fps))
    capture.set(cv2.CAP_PROP_POS_FRAMES, first_frame)
    source_index = first_frame
    next_sample_index = float(first_frame)
    source_step = source_fps / args.fps

    frames: list[Image.Image] = []
    palette = PALETTES[args.palette]
    print(
        f"Reading {args.video} ({source_fps:.3f} fps); "
        f"sampling at {args.fps:g} fps into {args.width}x{args.height} cells..."
    )

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            current_time = source_index / source_fps
            if end_time is not None and current_time >= end_time:
                break

            if source_index + 1e-6 >= next_sample_index:
                frames.append(
                    render_frame(
                        frame,
                        width=args.width,
                        height=args.height,
                        cell_size=args.cell_size,
                        gap=args.gap,
                        palette=palette,
                        invert=args.invert,
                        equalize=not args.no_equalize,
                    )
                )
                next_sample_index += source_step

            source_index += 1
    finally:
        capture.release()

    if not frames:
        print("Error: no frames were sampled; check the input and time range.", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame_duration_ms = max(1, int(round(1000.0 / args.fps)))
    frames[0].save(
        args.output,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration_ms,
        loop=0,
        optimize=True,
        disposal=2,
    )

    actual_duration = len(frames) / args.fps
    size_mb = args.output.stat().st_size / (1024 * 1024)
    print(
        f"Created {args.output} | {len(frames)} frames | "
        f"{actual_duration:.1f}s | {frames[0].width}x{frames[0].height}px | "
        f"{size_mb:.2f} MiB"
    )
    print("Tip: use --palette mono for a black-and-white Bad Apple look.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
