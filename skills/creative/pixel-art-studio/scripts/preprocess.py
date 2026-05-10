#!/usr/bin/env python3
"""Image to pixel-art preprocessing pipeline.

Pipeline:
1. Downsample via Image.NEAREST (NOT bicubic — that produces fractional pixels = AI-slop)
2. Extract or apply palette (k-means / median cut / explicit)
3. Quantize to palette
4. Optional dithering (Bayer / Floyd-Steinberg / Atkinson)
5. Output PNG

Usage:
    python preprocess.py photo.jpg --target-size 64x64 --palette endesga-32 -o pixel.png
    python preprocess.py photo.jpg --target-size 32x32 --colors 16 --dither floyd-steinberg
    python preprocess.py ai_output.png --target-size 48x48 --palette aap-64 --dither bayer4

NOTE: AI-generated images (Stable Diffusion, Midjourney) often have fractional pixels and noise.
The preprocess pipeline forces them to a real pixel grid + palette discipline.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Error: missing dependency. pip install Pillow numpy", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from dither import dither_image, ALGORITHMS  # type: ignore[no-redef]
from palette import load_palette as _load_palette_hex, parse_hex_color  # type: ignore[no-redef]


def parse_size(s: str) -> tuple[int, int]:
    """Parse '64x64' into (64, 64)."""
    if "x" not in s:
        raise ValueError(f"Size must be WxH, got {s!r}")
    w, h = s.split("x", 1)
    return int(w), int(h)


def downsample(image_path: str, target_size: tuple[int, int],
               method: str = "nearest") -> Image.Image:
    """Downsample image to target size via NEAREST (recommended for pixel art)."""
    img = Image.open(image_path).convert("RGBA")
    if method == "nearest":
        resample = Image.Resampling.NEAREST
    elif method == "lanczos":
        # Quick "summary" of detail before nearest — sometimes preserves features better
        resample = Image.Resampling.LANCZOS
    elif method == "bilinear":
        resample = Image.Resampling.BILINEAR
    else:
        raise ValueError(f"Unknown downsample method: {method!r}")
    return img.resize(target_size, resample)


def upscale_for_display(img: Image.Image, scale: int) -> Image.Image:
    """Integer upscale via NEAREST for display."""
    return img.resize((img.width * scale, img.height * scale), Image.Resampling.NEAREST)


def preprocess(
    image_path: str,
    target_size: tuple[int, int] = (64, 64),
    palette_name: str | None = None,
    colors: int = 16,
    dither_algorithm: str = "none",
    downsample_method: str = "nearest",
    pre_lanczos_factor: float = 1.5,
) -> tuple[Image.Image, dict]:
    """Run full preprocessing pipeline.

    For pre_lanczos_factor: optional intermediate downsample via LANCZOS to reduce noise
    before final NEAREST. e.g. 1.5 means downsample to 1.5× target via LANCZOS first,
    then NEAREST to final. Set to 1.0 to skip.

    Returns (output_image, report dict)
    """
    target_w, target_h = target_size

    src = Image.open(image_path).convert("RGBA")
    src_size = src.size

    # Optional pre-step: smart downsample with LANCZOS to reduce noise
    if pre_lanczos_factor > 1.0 and downsample_method == "nearest":
        intermediate_w = int(target_w * pre_lanczos_factor)
        intermediate_h = int(target_h * pre_lanczos_factor)
        if intermediate_w < src.width and intermediate_h < src.height:
            src = src.resize((intermediate_w, intermediate_h), Image.Resampling.LANCZOS)

    # Final downsample to target via NEAREST
    if downsample_method == "nearest":
        downsampled = src.resize(target_size, Image.Resampling.NEAREST)
    elif downsample_method == "lanczos":
        downsampled = src.resize(target_size, Image.Resampling.LANCZOS)
    elif downsample_method == "bilinear":
        downsampled = src.resize(target_size, Image.Resampling.BILINEAR)
    else:
        downsampled = src.resize(target_size, Image.Resampling.NEAREST)

    # Save downsampled to a temp file for dither.py to load
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    downsampled.save(tmp_path, "PNG")

    try:
        # Apply dithering and palette
        if dither_algorithm == "none":
            # Just quantize to palette without dither
            result = dither_image(tmp_path, algorithm="none",
                                  palette_name=palette_name, colors=colors)
        else:
            result = dither_image(tmp_path, algorithm=dither_algorithm,
                                  palette_name=palette_name, colors=colors)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    report = {
        "source": image_path,
        "source_size": src_size,
        "target_size": target_size,
        "palette": palette_name or f"auto-extracted-{colors}",
        "dither_algorithm": dither_algorithm,
        "downsample_method": downsample_method,
        "pre_lanczos_factor": pre_lanczos_factor,
    }
    return result, report


def main() -> int:
    parser = argparse.ArgumentParser(description="Image-to-pixel-art preprocessing pipeline.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("-o", "--output", default="pixel.png", help="Output path")
    parser.add_argument("--target-size", default="64x64", help="Target pixel grid (default: 64x64)")
    parser.add_argument("--palette", default=None, help="Bundled palette name (e.g. endesga-32)")
    parser.add_argument("--colors", type=int, default=16,
                        help="If no palette, target color count (default: 16)")
    parser.add_argument("--dither", default="none",
                        choices=list(ALGORITHMS.keys()),
                        help="Dithering algorithm (default: none)")
    parser.add_argument("--downsample", default="nearest",
                        choices=["nearest", "lanczos", "bilinear"],
                        help="Final downsampling method (default: nearest, recommended for pixel art)")
    parser.add_argument("--pre-lanczos", type=float, default=1.5,
                        help="Pre-downsample factor via LANCZOS (default 1.5; set to 1.0 to skip)")
    parser.add_argument("--upscale-display", type=int, default=0,
                        help="Optional integer upscale of output via NEAREST (e.g. 16 for 16× display)")
    args = parser.parse_args()

    target_size = parse_size(args.target_size)

    img, report = preprocess(
        args.input,
        target_size=target_size,
        palette_name=args.palette,
        colors=args.colors,
        dither_algorithm=args.dither,
        downsample_method=args.downsample,
        pre_lanczos_factor=args.pre_lanczos,
    )

    if args.upscale_display:
        img = upscale_for_display(img, args.upscale_display)
        report["display_scale"] = args.upscale_display

    img.save(args.output, "PNG")
    report["output"] = args.output
    report["output_size"] = img.size
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
