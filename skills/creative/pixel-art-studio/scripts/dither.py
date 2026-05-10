#!/usr/bin/env python3
"""Dithering algorithms: Bayer 2/4/8, Floyd-Steinberg, Atkinson, Ordered, Blue Noise.

Usage:
    python dither.py input.png --algorithm bayer4 --palette endesga-32 -o out.png
    python dither.py input.png --algorithm floyd-steinberg --colors 16 -o out.png
    python dither.py input.png --algorithm atkinson --palette gameboy-dmg -o out.png

When --palette is given, the output is forced to use only those colors (with dithering to
approximate intermediates). When --colors is given, the palette is auto-extracted via median cut.
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
PALETTES_DIR = SCRIPT_DIR / "palettes"


# --- Bayer thresholds -------------------------------------------------------

BAYER_2 = np.array([
    [0, 2],
    [3, 1],
]) / 4.0 - 0.5

BAYER_4 = np.array([
    [0,  8,  2, 10],
    [12, 4, 14, 6],
    [3, 11, 1,  9],
    [15, 7, 13, 5],
]) / 16.0 - 0.5

BAYER_8 = np.array([
    [0,  32, 8,  40, 2,  34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4,  36, 14, 46, 6,  38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [3,  35, 11, 43, 1,  33, 9,  41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7,  39, 13, 45, 5,  37],
    [63, 31, 55, 23, 61, 29, 53, 21],
]) / 64.0 - 0.5


# --- Helpers ----------------------------------------------------------------

def load_palette(name: str) -> list[tuple[int, int, int]]:
    path = PALETTES_DIR / f"{name}.hex"
    colors = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith((";", "//")):
                continue
            if line.startswith("#"):
                hex6 = line.lstrip("#")[:6]
                if len(hex6) == 6:
                    colors.append((int(hex6[0:2], 16), int(hex6[2:4], 16), int(hex6[4:6], 16)))
    return colors


def closest_palette_color(rgb: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """Find nearest palette color for each pixel. rgb shape (H,W,3), palette shape (P,3)."""
    diff = rgb[:, :, None, :].astype(np.int32) - palette[None, None, :, :].astype(np.int32)
    dist = np.sum(diff ** 2, axis=3)
    indices = np.argmin(dist, axis=2)
    return palette[indices]


def find_closest(pixel: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """Find single closest palette color to pixel."""
    diff = palette.astype(np.int32) - pixel.astype(np.int32)
    dist = np.sum(diff ** 2, axis=1)
    return palette[np.argmin(dist)]


# --- Bayer (ordered) dithering ----------------------------------------------

def bayer_dither(arr: np.ndarray, palette: np.ndarray, matrix_size: int = 4) -> np.ndarray:
    """Bayer ordered dithering. arr: HxWx3 RGB. Returns dithered RGB."""
    h, w = arr.shape[:2]
    if matrix_size == 2:
        threshold = BAYER_2
    elif matrix_size == 4:
        threshold = BAYER_4
    elif matrix_size == 8:
        threshold = BAYER_8
    else:
        raise ValueError(f"matrix_size must be 2, 4, or 8 — got {matrix_size}")
    ms = threshold.shape[0]
    # Estimate quantization step from palette
    palette_int = palette.astype(np.float32)
    # Distance to nearest palette color, average — use as offset magnitude
    avg_step = 32.0  # heuristic; works for typical 16-32 color palettes

    arr_f = arr.astype(np.float32)
    h_pad = (np.arange(h)[:, None] % ms)
    w_pad = (np.arange(w)[None, :] % ms)
    threshold_map = threshold[h_pad, w_pad][:, :, None] * avg_step

    biased = np.clip(arr_f + threshold_map, 0, 255)
    return closest_palette_color(biased.astype(np.uint8), palette)


# --- Floyd-Steinberg --------------------------------------------------------

def floyd_steinberg(arr: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """Error-diffusion to 4 neighbors: right (7/16), down-left (3/16), down (5/16), down-right (1/16)."""
    arr_f = arr.astype(np.float32).copy()
    h, w = arr_f.shape[:2]
    out = np.zeros_like(arr, dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            old = arr_f[y, x].copy()
            new = find_closest(np.clip(old, 0, 255).astype(np.uint8), palette).astype(np.float32)
            out[y, x] = new.astype(np.uint8)
            err = old - new
            if x + 1 < w:
                arr_f[y, x + 1] += err * 7 / 16
            if y + 1 < h:
                if x > 0:
                    arr_f[y + 1, x - 1] += err * 3 / 16
                arr_f[y + 1, x] += err * 5 / 16
                if x + 1 < w:
                    arr_f[y + 1, x + 1] += err * 1 / 16
    return out


# --- Atkinson ---------------------------------------------------------------

def atkinson(arr: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """Atkinson dithering: distributes only 6/8 of error to 6 neighbors. Lighter, airier output."""
    arr_f = arr.astype(np.float32).copy()
    h, w = arr_f.shape[:2]
    out = np.zeros_like(arr, dtype=np.uint8)
    # Atkinson kernel (6 neighbors, 1/8 each):
    # . . X 1 1
    # 1 1 1 . .
    # . 1 . . .
    offsets = [(0, 1), (0, 2), (1, -1), (1, 0), (1, 1), (2, 0)]
    for y in range(h):
        for x in range(w):
            old = arr_f[y, x].copy()
            new = find_closest(np.clip(old, 0, 255).astype(np.uint8), palette).astype(np.float32)
            out[y, x] = new.astype(np.uint8)
            err = (old - new) / 8
            for dy, dx in offsets:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w:
                    arr_f[ny, nx] += err
    return out


# --- Ordered (clustered-dot) ------------------------------------------------

def ordered_dither(arr: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """Clustered-dot ordered dithering — newspaper halftone feel.

    Uses a clustered-dot 4×4 matrix instead of dispersed Bayer.
    """
    cluster = np.array([
        [12, 5, 6, 13],
        [4, 0, 1, 7],
        [11, 3, 2, 8],
        [15, 10, 9, 14],
    ]) / 16.0 - 0.5

    h, w = arr.shape[:2]
    arr_f = arr.astype(np.float32)
    h_pad = (np.arange(h)[:, None] % 4)
    w_pad = (np.arange(w)[None, :] % 4)
    threshold_map = cluster[h_pad, w_pad][:, :, None] * 32.0

    biased = np.clip(arr_f + threshold_map, 0, 255)
    return closest_palette_color(biased.astype(np.uint8), palette)


# --- Blue noise -------------------------------------------------------------

def blue_noise_dither(arr: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """Blue noise dithering. Generates a void-and-cluster blue noise mask procedurally.

    For real production use, prefer pre-computed blue noise textures (momentsingraphics.de).
    Here we generate a simple approximation using random + low-pass-then-high-pass.
    """
    h, w = arr.shape[:2]
    rng = np.random.default_rng(0)
    noise = rng.random((h, w))
    # Approximate high-frequency-only noise via subtracting a 3x3 averaged version
    from scipy.ndimage import uniform_filter
    try:
        smoothed = uniform_filter(noise, size=3)
        blue = noise - smoothed + 0.5
        blue = np.clip(blue, 0, 1)
    except ImportError:
        blue = noise

    threshold = (blue - 0.5)[:, :, None] * 32.0
    arr_f = arr.astype(np.float32)
    biased = np.clip(arr_f + threshold, 0, 255)
    return closest_palette_color(biased.astype(np.uint8), palette)


# --- Quantize without dither ------------------------------------------------

def quantize_no_dither(arr: np.ndarray, palette: np.ndarray) -> np.ndarray:
    """Simple nearest-palette quantization, no dithering."""
    return closest_palette_color(arr, palette)


# --- Top-level --------------------------------------------------------------

ALGORITHMS = {
    "bayer2": lambda a, p: bayer_dither(a, p, 2),
    "bayer4": lambda a, p: bayer_dither(a, p, 4),
    "bayer8": lambda a, p: bayer_dither(a, p, 8),
    "floyd-steinberg": floyd_steinberg,
    "atkinson": atkinson,
    "ordered": ordered_dither,
    "blue-noise": blue_noise_dither,
    "none": quantize_no_dither,
}


def dither_image(image_path: str, algorithm: str = "bayer4",
                 palette_name: str | None = None,
                 colors: int = 16) -> Image.Image:
    """Apply dithering. Returns Pillow Image with alpha preserved."""
    img = Image.open(image_path).convert("RGBA")
    arr = np.array(img)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

    if palette_name:
        palette = np.array(load_palette(palette_name), dtype=np.uint8)
    else:
        # Auto-extract via median cut (simple route)
        rgb_only = Image.fromarray(rgb)
        quantized = rgb_only.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
        pal = quantized.getpalette()[: colors * 3]
        palette = np.array([(pal[i], pal[i + 1], pal[i + 2]) for i in range(0, len(pal), 3)],
                           dtype=np.uint8)

    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {algorithm!r}. Available: {list(ALGORITHMS)}")

    dithered_rgb = ALGORITHMS[algorithm](rgb, palette)
    out_rgba = np.zeros_like(arr)
    out_rgba[:, :, :3] = dithered_rgb
    out_rgba[:, :, 3] = alpha
    return Image.fromarray(out_rgba, mode="RGBA")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply dithering algorithm to an image.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("-o", "--output", default="dithered.png", help="Output path")
    parser.add_argument("--algorithm", default="bayer4",
                        choices=list(ALGORITHMS.keys()),
                        help="Dithering algorithm (default: bayer4)")
    parser.add_argument("--palette", default=None, help="Bundled palette name (e.g. endesga-32)")
    parser.add_argument("--colors", type=int, default=16,
                        help="If no --palette, target color count for auto-extracted palette")
    args = parser.parse_args()

    img = dither_image(args.input, args.algorithm, args.palette, args.colors)
    img.save(args.output, "PNG")
    print(json.dumps({
        "algorithm": args.algorithm,
        "palette": args.palette or f"auto-extract-{args.colors}",
        "input": args.input,
        "output": args.output,
        "size": img.size,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
