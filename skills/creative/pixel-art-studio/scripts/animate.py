#!/usr/bin/env python3
"""Animation helpers: walk-cycle generation, easing curves for pixel art, sprite sheet from images.

Usage:
    # Render an animation JSON to GIF/APNG/spritesheet (delegates to render.py)
    python animate.py walk.json --format gif -o walk.gif

    # Generate walk-cycle template (4-frame, with bounce)
    python animate.py --template walk-4frame --output walk-template.json

    # Combine separate frame PNG files into a sprite sheet
    python animate.py --combine-frames frame_0.png frame_1.png frame_2.png frame_3.png \
                      --layout horizontal -o sheet.png

    # Generate easing waypoints for sub-pixel motion (e.g. for engine import)
    python animate.py --easing step --frames 8 --start 0 --end 16

Templates available:
    walk-4frame   - 4 frames at 8 FPS (Western indie default)
    walk-6frame   - 6 frames at 8 FPS (Shovel Knight quality)
    walk-cn-4    - 4 frames at 5 FPS (CN mobile RPG documented standard)
    idle-4frame   - 4 frames at 6 FPS, breathing
    attack-3frame - 3 frames at 12 FPS, anticipation/strike/recovery
    death-6frame  - 6 frames at 8 FPS, fall + fade

Easing curves (for sub-pixel motion or external import):
    linear     - constant velocity (avoid for short pixel motions)
    step       - integer step quantized (recommended for pixel art)
    ease-in    - quadratic ease-in
    ease-out   - quadratic ease-out
    ease-inout - sigmoid
    bounce     - bouncing easing curve
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: missing dependency. pip install Pillow", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from render import render_from_data, save_spritesheet  # type: ignore[no-redef]


# --- Templates --------------------------------------------------------------

TEMPLATES: dict[str, dict] = {
    "walk-4frame": {
        "description": "4-frame walk @ 8fps (Western indie default, Celeste-style)",
        "width": 32, "height": 32, "background": "transparent",
        "palette_ref": "endesga-32",
        "frames": [
            {"id": 0, "duration_ms": 125, "name": "contact", "pixels": []},
            {"id": 1, "duration_ms": 125, "name": "recoil", "pixels": []},
            {"id": 2, "duration_ms": 125, "name": "passing", "pixels": []},
            {"id": 3, "duration_ms": 125, "name": "high-point", "pixels": []},
        ],
        "tags": [{"name": "walk", "from": 0, "to": 3, "direction": "forward"}],
    },
    "walk-6frame": {
        "description": "6-frame walk @ 8fps (Shovel Knight quality)",
        "width": 32, "height": 32, "background": "transparent",
        "palette_ref": "endesga-32",
        "frames": [
            {"id": i, "duration_ms": 125, "pixels": []} for i in range(6)
        ],
        "tags": [{"name": "walk", "from": 0, "to": 5, "direction": "forward"}],
    },
    "walk-cn-4": {
        "description": "4-frame walk @ 5fps (CN mobile RPG documented standard, 200ms/frame)",
        "width": 48, "height": 72, "background": "transparent",
        "palette_ref": "endesga-32",
        "frames": [
            {"id": i, "duration_ms": 200, "pixels": []} for i in range(4)
        ],
        "tags": [{"name": "walk", "from": 0, "to": 3, "direction": "forward"}],
    },
    "idle-4frame": {
        "description": "4-frame breathing idle @ 6fps (subtle vertical sub-pixel motion)",
        "width": 32, "height": 32, "background": "transparent",
        "palette_ref": "endesga-32",
        "frames": [
            {"id": i, "duration_ms": 167, "pixels": []} for i in range(4)
        ],
        "tags": [{"name": "idle", "from": 0, "to": 3, "direction": "pingpong"}],
    },
    "attack-3frame": {
        "description": "3-frame attack @ 12fps (anticipation slow, strike fast, recovery eased)",
        "width": 32, "height": 32, "background": "transparent",
        "palette_ref": "endesga-32",
        "frames": [
            {"id": 0, "duration_ms": 250, "name": "anticipation", "pixels": []},
            {"id": 1, "duration_ms": 60,  "name": "strike",       "pixels": []},
            {"id": 2, "duration_ms": 200, "name": "recovery",     "pixels": []},
        ],
        "tags": [{"name": "attack", "from": 0, "to": 2, "direction": "forward"}],
    },
    "death-6frame": {
        "description": "6-frame death @ 8fps (fall + dissolve)",
        "width": 32, "height": 32, "background": "transparent",
        "palette_ref": "endesga-32",
        "frames": [
            {"id": i, "duration_ms": 125, "pixels": []} for i in range(6)
        ],
        "tags": [{"name": "death", "from": 0, "to": 5, "direction": "forward"}],
    },
}


# --- Easing curves ----------------------------------------------------------

def easing_step(t: float) -> float:
    """Step easing — quantized to integer pixel positions (recommended for pixel art)."""
    return t  # rounding done by caller in pixel space


def easing_linear(t: float) -> float:
    return t


def easing_in(t: float) -> float:
    return t * t


def easing_out(t: float) -> float:
    return 1 - (1 - t) ** 2


def easing_inout(t: float) -> float:
    if t < 0.5:
        return 2 * t * t
    return 1 - (-2 * t + 2) ** 2 / 2


def easing_bounce(t: float) -> float:
    """Bouncing curve — useful for landing impact / squash-stretch."""
    n1 = 7.5625
    d1 = 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


EASING_FUNCS = {
    "linear": easing_linear,
    "step": easing_step,
    "ease-in": easing_in,
    "ease-out": easing_out,
    "ease-inout": easing_inout,
    "bounce": easing_bounce,
}


def compute_easing_waypoints(curve: str, frames: int, start: float, end: float) -> list[dict]:
    """Compute per-frame integer-quantized positions for an easing curve.

    Returns list of {"frame": i, "t": t, "value_raw": v_raw, "value_int": v_int}.
    For pixel art, value_int is what you actually use; value_raw is the smooth target.
    """
    fn = EASING_FUNCS[curve]
    span = end - start
    waypoints = []
    for i in range(frames):
        t = i / max(1, frames - 1)
        eased = fn(t)
        raw = start + eased * span
        rounded = round(raw)
        waypoints.append({
            "frame": i,
            "t": round(t, 4),
            "eased_t": round(eased, 4),
            "value_raw": round(raw, 3),
            "value_int": int(rounded),
        })
    return waypoints


# --- Sprite-sheet from frame PNGs -------------------------------------------

def combine_frame_pngs(image_paths: list[str], output: str,
                       layout: str = "horizontal",
                       padding: int = 0,
                       rows: int | None = None,
                       cols: int | None = None) -> dict:
    images = [Image.open(p).convert("RGBA") for p in image_paths]
    save_spritesheet(images, output, layout, padding, rows, cols)
    return {"input_count": len(images), "output": output, "layout": layout}


# --- CLI --------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Animation helpers.")
    parser.add_argument("input", nargs="?", help="JSON animation spec (optional)")
    parser.add_argument("-o", "--output", default=None, help="Output path")
    parser.add_argument("--format", default="auto",
                        choices=["auto", "gif", "apng", "spritesheet"],
                        help="Output format")
    parser.add_argument("--layout", default="horizontal",
                        choices=["horizontal", "vertical", "grid"])
    parser.add_argument("--rows", type=int, default=None)
    parser.add_argument("--cols", type=int, default=None)
    parser.add_argument("--padding", type=int, default=0)
    parser.add_argument("--tag", default=None, help="Render only the named tag")

    parser.add_argument("--template", default=None,
                        choices=list(TEMPLATES),
                        help="Generate empty animation template JSON")
    parser.add_argument("--combine-frames", nargs="+", default=None,
                        help="Combine frame PNG files into sprite sheet")
    parser.add_argument("--easing", default=None, choices=list(EASING_FUNCS),
                        help="Compute easing waypoints")
    parser.add_argument("--frames", type=int, default=8, help="Number of waypoints (for easing)")
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--end", type=float, default=16.0)
    args = parser.parse_args()

    if args.template:
        template = dict(TEMPLATES[args.template])
        out = args.output or f"{args.template}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=2)
        print(json.dumps({"template": args.template, "output": out,
                          "frame_count": len(template["frames"])}, indent=2))
        return 0

    if args.combine_frames:
        out = args.output or "sheet.png"
        report = combine_frame_pngs(args.combine_frames, out, args.layout,
                                     args.padding, args.rows, args.cols)
        print(json.dumps(report, indent=2))
        return 0

    if args.easing:
        waypoints = compute_easing_waypoints(args.easing, args.frames, args.start, args.end)
        print(json.dumps({"curve": args.easing, "waypoints": waypoints}, indent=2))
        return 0

    if args.input:
        # Delegate to render.py-style rendering
        out = args.output or "animation.gif"
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        report = render_from_data(
            data,
            format=args.format if args.format != "auto" else "gif",
            output_path=out,
            spritesheet_layout=args.layout,
            spritesheet_rows=args.rows,
            spritesheet_cols=args.cols,
            spritesheet_padding=args.padding,
            tag_filter=args.tag,
        )
        print(json.dumps(report, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
