#!/usr/bin/env python3
"""Palette management: list bundled, extract from image, generate hue-shifted ramp.

Usage:
    python palette.py --list                                # list bundled palettes
    python palette.py --show endesga-32                     # render palette as image
    python palette.py --extract photo.jpg --colors 16       # extract palette from image
    python palette.py --ramp "#5b3a3a" --steps 5            # generate hue-shifted ramp
    python palette.py --analyze sprite.png                  # analyze palette of an image
"""

from __future__ import annotations

import argparse
import colorsys
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
DESIGN_SEEDS_DIR = PALETTES_DIR / "design-seeds"


# --- Palette I/O ------------------------------------------------------------

def list_palettes() -> dict[str, list[str]]:
    """Categorize bundled palettes by filename prefix or category file."""
    palettes = {}
    if not PALETTES_DIR.exists():
        return palettes
    # Top-level palettes (hardware / lospec / cultural)
    for path in sorted(PALETTES_DIR.glob("*.hex")):
        name = path.stem
        category = "general"
        if name in ("nes", "gameboy-dmg", "gameboy-pocket", "pico-8", "ega", "cga"):
            category = "hardware"
        elif name.startswith(("db", "endesga", "aap-", "sweetie", "resurrect", "apollo",
                              "steam-lords", "slso", "nyx")):
            category = "lospec-community"
        elif name in ("obangsaek", "gugong-red-wall", "qinghua", "wuxing"):
            category = "cultural"
        elif name == "stoneshard-inspired":
            category = "indie-game"
        palettes.setdefault(category, []).append(name)
    # Design Seeds curated subdirectory
    if DESIGN_SEEDS_DIR.exists():
        for path in sorted(DESIGN_SEEDS_DIR.glob("*.hex")):
            palettes.setdefault("design-seeds", []).append("design-seeds/" + path.stem)
    return palettes


def load_design_seeds_index() -> dict:
    """Load the Design Seeds metadata index (titles, tags, moods)."""
    index_path = DESIGN_SEEDS_DIR / "_index.json"
    if not index_path.exists():
        return {"palettes": {}, "tag_index": {}}
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def search_palettes_by_tag(tag: str) -> list[dict]:
    """Search Design Seeds palettes by tag. Returns list of {slug, title, tags, mood, hex_path}."""
    idx = load_design_seeds_index()
    tag_lower = tag.lower()
    matching_slugs = idx.get("tag_index", {}).get(tag_lower, [])
    results = []
    for slug in matching_slugs:
        meta = idx.get("palettes", {}).get(slug, {})
        results.append({
            "slug": slug,
            "name": "design-seeds/" + slug,
            "title": meta.get("title", slug),
            "tags": meta.get("tags", []),
            "mood": meta.get("mood", ""),
            "best_for": meta.get("best_for", []),
            "url": meta.get("url", ""),
        })
    return results


def search_palettes_by_mood(query: str) -> list[dict]:
    """Search Design Seeds palettes by free-form mood query (substring match against mood + best_for)."""
    idx = load_design_seeds_index()
    query_lower = query.lower()
    results = []
    for slug, meta in idx.get("palettes", {}).items():
        haystack = (meta.get("mood", "") + " " + " ".join(meta.get("best_for", []))).lower()
        if query_lower in haystack:
            results.append({
                "slug": slug,
                "name": "design-seeds/" + slug,
                "title": meta.get("title", slug),
                "tags": meta.get("tags", []),
                "mood": meta.get("mood", ""),
                "best_for": meta.get("best_for", []),
                "url": meta.get("url", ""),
            })
    return results


def load_palette(name: str) -> list[str]:
    """Load a palette by name. Returns list of hex strings.

    Supports nested paths: 'design-seeds/nature-tones' loads from palettes/design-seeds/nature-tones.hex
    """
    if "/" in name:
        path = PALETTES_DIR / (name + ".hex")
    else:
        path = PALETTES_DIR / f"{name}.hex"
    if not path.exists():
        raise FileNotFoundError(f"Palette {name!r} not found in {PALETTES_DIR}")
    colors = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Skip comments (lines starting with ; or //)
            if line.startswith((";", "//")):
                continue
            # Some palette files have just hex without #
            if not line.startswith("#"):
                if all(c in "0123456789abcdefABCDEF" for c in line) and len(line) in (6, 8):
                    colors.append("#" + line)
                continue
            # Has # — make sure it's a color hex, not a comment
            if len(line) in (4, 5, 7, 9):
                colors.append(line)
    return colors


def render_palette_image(colors: list[str], swatch_size: int = 64) -> Image.Image:
    """Render a palette as a strip of swatches with hex labels."""
    n = len(colors)
    cols = min(8, n)
    rows = (n + cols - 1) // cols
    w = cols * swatch_size
    h = rows * swatch_size
    img = Image.new("RGBA", (w, h), (40, 40, 40, 255))
    for i, hex_color in enumerate(colors):
        r, c = divmod(i, cols)
        x0 = c * swatch_size
        y0 = r * swatch_size
        # Parse color
        rgb = parse_hex_color(hex_color)
        swatch = Image.new("RGBA", (swatch_size, swatch_size), rgb + (255,))
        img.paste(swatch, (x0, y0))
    return img


def parse_hex_color(s: str) -> tuple[int, int, int]:
    s = s.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    elif len(s) == 4:
        s = "".join(c * 2 for c in s[:3])
    if len(s) >= 6:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    raise ValueError(f"Invalid hex color: {s}")


# --- Palette extraction -----------------------------------------------------

def extract_palette_kmeans(image_path: str, n_colors: int = 16, max_iter: int = 30) -> list[str]:
    """K-means palette extraction (slow, high quality)."""
    img = Image.open(image_path).convert("RGBA")
    arr = np.array(img).reshape(-1, 4)
    visible = arr[arr[:, 3] > 0][:, :3].astype(np.float32)
    if len(visible) == 0:
        return []

    # Simple k-means
    rng = np.random.default_rng(42)
    indices = rng.choice(len(visible), size=min(n_colors, len(visible)), replace=False)
    centers = visible[indices].copy()

    for _ in range(max_iter):
        # Assign
        dists = np.sum((visible[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        labels = np.argmin(dists, axis=1)
        # Update
        new_centers = np.array([
            visible[labels == k].mean(axis=0) if (labels == k).any() else centers[k]
            for k in range(n_colors)
        ])
        if np.allclose(new_centers, centers, atol=1.0):
            break
        centers = new_centers

    return ["#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b)) for r, g, b in centers]


def extract_palette_median_cut(image_path: str, n_colors: int = 16) -> list[str]:
    """Median cut via Pillow (fast, balanced quality)."""
    img = Image.open(image_path).convert("RGBA")
    # Quantize ignores alpha; mask transparent first
    mask = Image.new("L", img.size, 0)
    alpha = img.split()[3]
    mask.paste(alpha, (0, 0))
    rgb = img.convert("RGB")
    quantized = rgb.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()[: n_colors * 3]
    return ["#{:02x}{:02x}{:02x}".format(palette[i], palette[i + 1], palette[i + 2])
            for i in range(0, len(palette), 3)]


def extract_palette_octree(image_path: str, n_colors: int = 16) -> list[str]:
    """Fast octree quantization via Pillow."""
    img = Image.open(image_path).convert("RGB")
    quantized = img.quantize(colors=n_colors, method=Image.Quantize.FASTOCTREE)
    palette = quantized.getpalette()[: n_colors * 3]
    return ["#{:02x}{:02x}{:02x}".format(palette[i], palette[i + 1], palette[i + 2])
            for i in range(0, len(palette), 3)]


# --- Ramp generation --------------------------------------------------------

def generate_ramp(base_hex: str, steps: int = 5, hue_shift_deg: float = 40,
                  shadow_pull: float = 0.6, highlight_lift: float = 1.4) -> list[str]:
    """Generate a hue-shifted ramp of N steps from dark to light.

    Endesga rule:
      - Shadows shift COOLER + DESATURATED (toward blue-violet)
      - Highlights shift WARMER + SATURATED (toward yellow-orange)

    Args:
        base_hex: starting color (typically the mid-tone)
        steps: number of colors in the ramp
        hue_shift_deg: total hue rotation across ramp (default 40 deg)
        shadow_pull: factor for shadow saturation/value pulldown (0-1)
        highlight_lift: factor for highlight saturation/value lift (>1)

    Returns: list of N hex colors, dark to light.
    """
    r, g, b = parse_hex_color(base_hex)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    h_deg = h * 360

    ramp = []
    for i in range(steps):
        t = i / max(1, steps - 1)  # 0 at darkest, 1 at lightest

        # Hue: rotate from cool (-hue_shift/2) to warm (+hue_shift/2)
        hue_offset = (t - 0.5) * hue_shift_deg
        # Bias: dark side rotates more cool-ward (negative hue offset)
        new_h_deg = (h_deg + hue_offset) % 360

        # Lightness: linear interpolation
        new_l = 0.15 + t * 0.75  # 0.15 dark to 0.90 light

        # Saturation: peaks in middle, drops at extremes
        sat_curve = 1 - 4 * (t - 0.5) ** 2  # parabolic, peak=1 at t=0.5
        new_s = s * (0.5 + 0.5 * sat_curve)
        new_s = max(0.1, min(1.0, new_s))

        nr, ng, nb = colorsys.hls_to_rgb(new_h_deg / 360, new_l, new_s)
        ramp.append("#{:02x}{:02x}{:02x}".format(int(nr * 255), int(ng * 255), int(nb * 255)))

    return ramp


# --- Analysis ---------------------------------------------------------------

def analyze_palette(colors: list[str]) -> dict:
    """Analyze hue rotation, value spread, sat range."""
    if len(colors) < 2:
        return {"applicable": False}

    hsls = []
    for c in colors:
        r, g, b = parse_hex_color(c)
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        hsls.append((h * 360, s, l, c))

    hsls.sort(key=lambda x: x[2])  # by lightness
    n = len(hsls)
    cut = max(1, n // 4)
    shadows = hsls[:cut]
    highlights = hsls[-cut:]
    sh_hue = sum(h for (h, _, _, _) in shadows) / len(shadows)
    hi_hue = sum(h for (h, _, _, _) in highlights) / len(highlights)
    delta = abs(sh_hue - hi_hue)
    delta = min(delta, 360 - delta)

    return {
        "color_count": len(colors),
        "shadow_mean_hue": float(sh_hue),
        "highlight_mean_hue": float(hi_hue),
        "hue_rotation_deg": float(delta),
        "rotation_passes_30": delta >= 30,
        "lightness_min": float(min(l for (_, _, l, _) in hsls)),
        "lightness_max": float(max(l for (_, _, l, _) in hsls)),
        "saturation_min": float(min(s for (_, s, _, _) in hsls)),
        "saturation_max": float(max(s for (_, s, _, _) in hsls)),
    }


# --- CLI --------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Pixel art palette tools.")
    sub = parser.add_subparsers(dest="action")

    # Use flags instead of subcommands for simplicity
    parser.add_argument("--list", action="store_true", help="List bundled palettes")
    parser.add_argument("--show", default=None, help="Render bundled palette as image")
    parser.add_argument("--extract", default=None, help="Extract palette from image")
    parser.add_argument("--colors", type=int, default=16, help="Target number of colors")
    parser.add_argument("--method", default="median-cut",
                        choices=["kmeans", "median-cut", "octree"],
                        help="Extraction method")
    parser.add_argument("--ramp", default=None, help="Base color for ramp generation")
    parser.add_argument("--steps", type=int, default=5, help="Ramp step count")
    parser.add_argument("--hue-shift", type=float, default=40, help="Hue rotation degrees")
    parser.add_argument("--analyze", default=None, help="Analyze palette of image (PNG)")
    parser.add_argument("--search-tag", default=None,
                        help="Search Design Seeds palettes by tag (e.g. 'twilight', 'dramatic', 'pinks')")
    parser.add_argument("--mood", default=None,
                        help="Search Design Seeds palettes by free-form mood query (e.g. 'night', 'dawn warm', 'romantic')")
    parser.add_argument("-o", "--output", default=None, help="Output file (for --show)")
    args = parser.parse_args()

    if args.list:
        palettes = list_palettes()
        for cat, names in sorted(palettes.items()):
            print(f"\n{cat}:")
            for name in names:
                print(f"  {name}")
        return 0

    if args.show:
        colors = load_palette(args.show)
        img = render_palette_image(colors)
        out = args.output or f"palette_{args.show}.png"
        img.save(out, "PNG")
        result = {"palette": args.show, "colors": colors, "output": out,
                  "analysis": analyze_palette(colors)}
        print(json.dumps(result, indent=2))
        return 0

    if args.extract:
        if args.method == "kmeans":
            colors = extract_palette_kmeans(args.extract, args.colors)
        elif args.method == "octree":
            colors = extract_palette_octree(args.extract, args.colors)
        else:
            colors = extract_palette_median_cut(args.extract, args.colors)
        result = {"source": args.extract, "method": args.method,
                  "colors": colors, "analysis": analyze_palette(colors)}
        print(json.dumps(result, indent=2))
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                for c in colors:
                    f.write(c + "\n")
        return 0

    if args.ramp:
        colors = generate_ramp(args.ramp, args.steps, args.hue_shift)
        result = {"base": args.ramp, "steps": args.steps,
                  "hue_shift_deg": args.hue_shift, "ramp": colors,
                  "analysis": analyze_palette(colors)}
        print(json.dumps(result, indent=2))
        return 0

    if args.analyze:
        # Load image, extract its palette, analyze
        img = Image.open(args.analyze).convert("RGBA")
        arr = np.array(img).reshape(-1, 4)
        visible = arr[arr[:, 3] > 0][:, :3]
        unique = np.unique(visible, axis=0)
        colors = ["#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b)) for r, g, b in unique]
        result = {"input": args.analyze, "color_count": len(colors),
                  "colors": colors[:64], "analysis": analyze_palette(colors)}
        print(json.dumps(result, indent=2))
        return 0

    if args.search_tag:
        results = search_palettes_by_tag(args.search_tag)
        for r in results:
            r["colors"] = load_palette(r["name"])
        print(json.dumps({"query_tag": args.search_tag, "matches": len(results), "results": results}, indent=2))
        return 0

    if args.mood:
        results = search_palettes_by_mood(args.mood)
        for r in results:
            r["colors"] = load_palette(r["name"])
        print(json.dumps({"query_mood": args.mood, "matches": len(results), "results": results}, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
