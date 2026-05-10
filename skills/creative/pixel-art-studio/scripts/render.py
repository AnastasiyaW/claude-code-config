#!/usr/bin/env python3
"""Render pixel-art JSON to PNG (static or animation), sprite sheets, GIF, APNG.

Schema: see references/08-json-schema.md
Single sprite:
    python render.py sprite.json -o sprite.png

Animation -> GIF:
    python render.py walk.json --format gif -o walk.gif

Animation -> APNG (better than GIF for semi-transparency):
    python render.py walk.json --format apng -o walk.apng

Sprite sheet:
    python render.py walk.json --format spritesheet -o walk_sheet.png --layout horizontal

Multi-tag sprite sheet (rows=tags, cols=frames):
    python render.py character.json --format spritesheet --layout grid -o character_sheet.png
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageColor
except ImportError:
    print("Error: Pillow is not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)


SPECIAL_COLORS = {
    "transparent": (0, 0, 0, 0),
}

SCRIPT_DIR = Path(__file__).resolve().parent
PALETTES_DIR = SCRIPT_DIR / "palettes"


# --- Color parsing -----------------------------------------------------------

def parse_color(color: Any) -> tuple[int, int, int, int]:
    """Parse hex, named, transparent, or [R,G,B]/[R,G,B,A] into RGBA tuple."""
    if isinstance(color, (list, tuple)):
        if len(color) == 3:
            return tuple(color) + (255,)  # type: ignore[return-value]
        if len(color) == 4:
            return tuple(color)  # type: ignore[return-value]
        raise ValueError(f"RGB/RGBA array must have 3 or 4 elements, got {len(color)}")

    if not isinstance(color, str):
        raise ValueError(f"Unsupported color type: {type(color)}")

    color_lower = color.strip().lower()
    if color_lower in SPECIAL_COLORS:
        return SPECIAL_COLORS[color_lower]

    try:
        rgba = ImageColor.getrgb(color)
        if len(rgba) == 3:
            return rgba + (255,)
        return rgba
    except (ValueError, AttributeError):
        raise ValueError(f"Unrecognized color: {color!r}")


def load_palette_ref(palette_ref: str) -> list[str] | None:
    """Resolve `palette_ref: "endesga-32"` to list of hex strings, if file exists."""
    candidate = PALETTES_DIR / f"{palette_ref}.hex"
    if not candidate.exists():
        return None
    colors = []
    with open(candidate, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") and len(line) > 9:  # comment line
                continue
            if line.startswith("#"):
                colors.append(line)
            else:
                # plain hex without #
                colors.append("#" + line)
    return colors


# --- Single frame rendering --------------------------------------------------

def render_single_frame(
    pixels: list[dict],
    width: int,
    height: int,
    background: str | tuple = "#FFFFFF",
    pixel_size: int = 16,
    grid_lines: bool = False,
) -> Image.Image:
    """Render a list of pixels into a Pillow Image (RGBA)."""
    bg_color = parse_color(background)
    img_width = width * pixel_size
    img_height = height * pixel_size

    img = Image.new("RGBA", (img_width, img_height), bg_color)
    draw = ImageDraw.Draw(img)

    for pixel in pixels:
        x = pixel["x"]
        y = pixel["y"]
        color = parse_color(pixel["color"])

        if x < 0 or x >= width or y < 0 or y >= height:
            print(f"Warning: pixel ({x}, {y}) outside {width}x{height} grid, skipping",
                  file=sys.stderr)
            continue

        x0 = x * pixel_size
        y0 = y * pixel_size
        x1 = x0 + pixel_size
        y1 = y0 + pixel_size

        if color[3] == 0:
            # Carve transparent pixel through any background
            transparent_block = Image.new("RGBA", (pixel_size, pixel_size), (0, 0, 0, 0))
            img.paste(transparent_block, (x0, y0))
        else:
            draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=color)

    if grid_lines:
        grid_color = (0, 0, 0, 60)
        for gx in range(1, width):
            line_x = gx * pixel_size
            draw.line([(line_x, 0), (line_x, img_height - 1)], fill=grid_color, width=1)
        for gy in range(1, height):
            line_y = gy * pixel_size
            draw.line([(0, line_y), (img_width - 1, line_y)], fill=grid_color, width=1)

    return img


# --- Layer composition -------------------------------------------------------

def render_layered_frame(
    layers: list[dict],
    width: int,
    height: int,
    background: str | tuple = "transparent",
    pixel_size: int = 16,
    frame_id: int | None = None,
) -> Image.Image:
    """Compose multiple layers into a single frame.

    Each layer can have either `pixels` (static) or `frames` (animated, then frame_id is used).
    Layers are composited in order; later layers go on top.
    """
    base = Image.new("RGBA", (width * pixel_size, height * pixel_size), parse_color(background))
    for layer in layers:
        if not layer.get("visible", True):
            continue
        opacity = float(layer.get("opacity", 1.0))
        if "frames" in layer and frame_id is not None:
            # find the matching frame
            frame_pixels = None
            for f in layer["frames"]:
                if f.get("id") == frame_id:
                    frame_pixels = f.get("pixels", [])
                    break
            if frame_pixels is None:
                # fall back to frame index 0 or skip
                continue
            layer_img = render_single_frame(frame_pixels, width, height,
                                             "transparent", pixel_size, False)
        elif "pixels" in layer:
            layer_img = render_single_frame(layer["pixels"], width, height,
                                             "transparent", pixel_size, False)
        else:
            continue

        if opacity < 1.0:
            alpha = layer_img.split()[3]
            alpha = alpha.point(lambda a: int(a * opacity))
            layer_img.putalpha(alpha)

        base.alpha_composite(layer_img)

    return base


# --- Multi-frame and tags ---------------------------------------------------

def expand_tag_frames(frames: list[dict], tag: dict) -> list[int]:
    """Given a tag, expand into the actual ordered frame ID sequence accounting for direction."""
    direction = tag.get("direction", "forward")
    f_from, f_to = tag["from"], tag["to"]
    base = list(range(f_from, f_to + 1))
    if direction == "reverse":
        return list(reversed(base))
    if direction == "pingpong":
        # 0,1,2,3,2,1 (don't repeat endpoints)
        return base + base[-2:0:-1] if len(base) > 2 else base
    return base  # "forward" default


def get_frame_pixels(frames: list[dict], frame_id: int) -> list[dict] | None:
    """Find the pixels for a given frame id."""
    for f in frames:
        if f.get("id") == frame_id:
            return f.get("pixels", [])
    return None


# --- Output formats ---------------------------------------------------------

def save_static_png(img: Image.Image, output_path: str) -> None:
    img.save(output_path, "PNG")


def save_animated_gif(images: list[Image.Image], durations_ms: list[int],
                      output_path: str, loop: int = 0) -> None:
    """Save a list of frames as animated GIF.

    Note: GIF supports 256 colors max and only 1-bit alpha (transparent or solid).
    For semi-transparency use save_animated_apng.
    """
    if not images:
        raise ValueError("No frames to save")

    # GIF needs P or RGB mode; use palette-aware quantization
    converted = [im.convert("RGBA") for im in images]
    converted[0].save(
        output_path,
        save_all=True,
        append_images=converted[1:],
        duration=durations_ms,
        loop=loop,
        disposal=2,
        optimize=False,
    )


def save_animated_apng(images: list[Image.Image], durations_ms: list[int],
                       output_path: str, loop: int = 0) -> None:
    """Save APNG with full RGBA support (better than GIF for transparency)."""
    if not images:
        raise ValueError("No frames to save")
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=durations_ms,
        loop=loop,
        format="PNG",
    )


def save_spritesheet(
    images: list[Image.Image],
    output_path: str,
    layout: str = "horizontal",
    padding: int = 0,
    rows: int | None = None,
    cols: int | None = None,
    background: tuple = (0, 0, 0, 0),
) -> None:
    """Compose multiple frames into a single sprite sheet PNG.

    Layouts:
      horizontal: all frames in one row
      vertical:   all frames in one column
      grid:       use rows/cols (defaults to square-ish)
    """
    if not images:
        raise ValueError("No frames to save")

    fw, fh = images[0].size
    n = len(images)

    if layout == "horizontal":
        cols = n
        rows = 1
    elif layout == "vertical":
        cols = 1
        rows = n
    elif layout == "grid":
        if rows is None and cols is None:
            cols = int(n ** 0.5 + 0.5)
            rows = (n + cols - 1) // cols
        elif cols is None and rows:
            cols = (n + rows - 1) // rows
        elif rows is None and cols:
            rows = (n + cols - 1) // cols
    else:
        raise ValueError(f"Unknown layout: {layout!r}")

    sheet_w = cols * fw + (cols - 1) * padding
    sheet_h = rows * fh + (rows - 1) * padding
    sheet = Image.new("RGBA", (sheet_w, sheet_h), background)

    for idx, img in enumerate(images):
        r, c = divmod(idx, cols)
        x = c * (fw + padding)
        y = r * (fh + padding)
        sheet.paste(img, (x, y))

    sheet.save(output_path, "PNG")


# --- Top-level entrypoint ---------------------------------------------------

def render_from_data(data: dict, format: str = "auto",
                     output_path: str = "output.png",
                     pixel_size_override: int | None = None,
                     grid_lines_override: bool | None = None,
                     spritesheet_layout: str = "horizontal",
                     spritesheet_rows: int | None = None,
                     spritesheet_cols: int | None = None,
                     spritesheet_padding: int = 0,
                     tag_filter: str | None = None) -> dict:
    """Top-level render dispatch. Returns a small report dict."""
    width = data["width"]
    height = data["height"]
    background = data.get("background", "transparent")
    pixel_size = pixel_size_override or data.get("pixel_size", 16)
    grid_lines = data.get("grid_lines", False)
    if grid_lines_override is not None:
        grid_lines = grid_lines_override

    has_frames = "frames" in data
    has_layers = "layers" in data
    has_pixels = "pixels" in data

    # Decide format if auto
    if format == "auto":
        if has_frames:
            ext = Path(output_path).suffix.lower()
            if ext == ".gif":
                format = "gif"
            elif ext in (".apng", ".png"):
                format = "apng" if ext == ".apng" else "spritesheet"
            else:
                format = "spritesheet"
        else:
            format = "static"

    # Static path
    if format == "static" or (not has_frames and not has_layers):
        if has_pixels:
            img = render_single_frame(data["pixels"], width, height,
                                       background, pixel_size, grid_lines)
        elif has_layers:
            img = render_layered_frame(data["layers"], width, height,
                                        background, pixel_size)
        else:
            raise ValueError("No `pixels` or `frames` or `layers` in input")
        save_static_png(img, output_path)
        return {"format": "static", "size": img.size, "output": output_path}

    # Animation path
    if not has_frames:
        raise ValueError(f"Format {format!r} requires `frames` array")

    frames = data["frames"]

    # If a tag is specified, expand it; otherwise just use all frames in order
    if tag_filter:
        tag = next((t for t in data.get("tags", []) if t["name"] == tag_filter), None)
        if not tag:
            raise ValueError(f"Tag {tag_filter!r} not found")
        frame_seq = expand_tag_frames(frames, tag)
    else:
        frame_seq = sorted({f.get("id", i) for i, f in enumerate(frames)})

    # Render each frame
    images: list[Image.Image] = []
    durations: list[int] = []
    for fid in frame_seq:
        f = next((fr for fr in frames if fr.get("id") == fid), None)
        if f is None:
            continue
        if has_layers:
            img = render_layered_frame(data["layers"], width, height,
                                        background, pixel_size, frame_id=fid)
        else:
            pixels = f.get("pixels", [])
            img = render_single_frame(pixels, width, height,
                                       background, pixel_size, grid_lines)
        images.append(img)
        durations.append(int(f.get("duration_ms", 100)))

    if format == "gif":
        save_animated_gif(images, durations, output_path)
    elif format == "apng":
        save_animated_apng(images, durations, output_path)
    elif format == "spritesheet":
        save_spritesheet(images, output_path, spritesheet_layout,
                         spritesheet_padding, spritesheet_rows, spritesheet_cols)
    else:
        raise ValueError(f"Unknown format: {format!r}")

    return {
        "format": format,
        "frames": len(images),
        "total_ms": sum(durations),
        "output": output_path,
        "size": images[0].size if images else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render pixel art JSON to PNG/GIF/APNG/spritesheet.")
    parser.add_argument("input", help="Path to JSON file, or '-' for stdin")
    parser.add_argument("-o", "--output", default="output.png",
                        help="Output file path (default: output.png)")
    parser.add_argument("--format", default="auto",
                        choices=["auto", "static", "gif", "apng", "spritesheet"],
                        help="Output format. 'auto' picks based on input + extension")
    parser.add_argument("-p", "--pixel-size", type=int, default=None,
                        help="Pixels per logical pixel (default: from JSON or 16)")
    parser.add_argument("-g", "--grid-lines", action="store_true",
                        help="Draw 1px grid lines")
    parser.add_argument("--no-grid-lines", action="store_true",
                        help="Force-disable grid lines")
    parser.add_argument("--layout", default="horizontal",
                        choices=["horizontal", "vertical", "grid"],
                        help="Sprite sheet layout (default: horizontal)")
    parser.add_argument("--rows", type=int, default=None, help="Sprite sheet rows (grid layout)")
    parser.add_argument("--cols", type=int, default=None, help="Sprite sheet cols (grid layout)")
    parser.add_argument("--padding", type=int, default=0,
                        help="Padding between cells in sprite sheet (default: 0)")
    parser.add_argument("--tag", default=None,
                        help="Render only the named tag (animation subset)")
    args = parser.parse_args()

    if args.input == "-":
        raw = sys.stdin.read()
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            raw = f.read()
    data = json.loads(raw)

    grid_lines_override = None
    if args.no_grid_lines:
        grid_lines_override = False
    elif args.grid_lines:
        grid_lines_override = True

    report = render_from_data(
        data,
        format=args.format,
        output_path=args.output,
        pixel_size_override=args.pixel_size,
        grid_lines_override=grid_lines_override,
        spritesheet_layout=args.layout,
        spritesheet_rows=args.rows,
        spritesheet_cols=args.cols,
        spritesheet_padding=args.padding,
        tag_filter=args.tag,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
