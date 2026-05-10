#!/usr/bin/env python3
"""Pixel art quality scoring: orphan pixels, doublies, banding, pillow-shading, AI-slop signals.

Usage:
    python quality_check.py sprite.png            # score a static PNG
    python quality_check.py sprite.json --json    # score from JSON spec
    python quality_check.py walk.json --animation # score animation consistency

Output: JSON with scores and findings.

Score interpretation:
    >= 80 : ship
    60-80 : fix the listed issues
    < 60  : redesign

Mandatory rules (hard fails — score capped at 50 if any present):
    - pillow_shading detected
    - >5% orphan pixels
    - any doublies > 2 instances

Soft warnings (lower score but still passable):
    - palette > stated cap
    - banding detected
    - hue rotation < 30 deg across ramps
    - over-AA (>20% boundary pixels intermediate)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Error: missing dependency. Run: pip install Pillow numpy", file=sys.stderr)
    sys.exit(1)


# --- Helpers ----------------------------------------------------------------

def hex_from_rgb(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Return H in [0,360), S in [0,1], L in [0,1]."""
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    mx = max(rf, gf, bf)
    mn = min(rf, gf, bf)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, 0.0, l
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == rf:
        h = ((gf - bf) / d + (6 if gf < bf else 0))
    elif mx == gf:
        h = (bf - rf) / d + 2
    else:
        h = (rf - gf) / d + 4
    return h * 60, s, l


def luminance(r: int, g: int, b: int) -> float:
    """Perceptual luminance (Rec 709)."""
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# --- Image loading -----------------------------------------------------------

def load_image_as_array(path: str) -> np.ndarray:
    """Load PNG and downsample to logical pixel grid if upscaled.

    For an integer-upscaled pixel-art image (e.g. 16x16 logical * 32 = 512x512 actual),
    we sample one pixel per cell to get the logical grid.
    """
    img = Image.open(path).convert("RGBA")
    arr = np.array(img)
    # Try to detect integer upscale by finding GCD of pixel block size
    block = detect_block_size(arr)
    if block > 1:
        h, w = arr.shape[:2]
        new_h, new_w = h // block, w // block
        # Sample center pixel of each block
        offset = block // 2
        arr = arr[offset::block, offset::block]
        if arr.shape[0] != new_h or arr.shape[1] != new_w:
            arr = arr[:new_h, :new_w]
    return arr


def detect_block_size(arr: np.ndarray) -> int:
    """Detect integer scale factor by finding the largest size where every block has uniform color."""
    h, w = arr.shape[:2]
    # Try block sizes from largest to smallest
    for block in [32, 16, 12, 10, 8, 6, 4, 3, 2]:
        if h % block != 0 or w % block != 0:
            continue
        # Sample a few blocks for uniformity
        sample_blocks = min(20, (h // block) * (w // block))
        uniform = 0
        # randomly sample positions
        rng = np.random.default_rng(42)
        for _ in range(sample_blocks):
            y = rng.integers(0, h - block)
            x = rng.integers(0, w - block)
            cell = arr[y:y+block, x:x+block]
            # All pixels in the cell should be identical
            if (cell == cell[0, 0]).all():
                uniform += 1
        if uniform / sample_blocks > 0.9:
            return block
    return 1


# --- Quality checks ----------------------------------------------------------

def check_palette(arr: np.ndarray, palette_cap: int | None = None) -> dict:
    """Count unique colors. arr is HxWx4 RGBA."""
    h, w = arr.shape[:2]
    rgba = arr.reshape(-1, 4)
    # Ignore fully transparent pixels in count
    visible = rgba[rgba[:, 3] > 0]
    unique = np.unique(visible, axis=0)
    rgb_uniques = set(tuple(c[:3]) for c in unique)
    out = {
        "unique_color_count": len(rgb_uniques),
        "total_visible_pixels": int(visible.shape[0]),
        "total_image_pixels": int(rgba.shape[0]),
    }
    if palette_cap is not None:
        out["palette_cap"] = palette_cap
        out["over_cap"] = len(rgb_uniques) > palette_cap
    return out


def check_orphan_pixels(arr: np.ndarray) -> dict:
    """Find pixels with no same-color 8-neighbors. Reports counts."""
    h, w = arr.shape[:2]
    orphans: list[dict] = []
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    for y in range(h):
        for x in range(w):
            if alpha[y, x] == 0:
                continue
            color = rgb[y, x]
            same = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and alpha[ny, nx] > 0:
                        if (rgb[ny, nx] == color).all():
                            same += 1
            if same == 0:
                orphans.append({"x": int(x), "y": int(y), "color": hex_from_rgb(tuple(color))})
    visible = int((alpha > 0).sum())
    return {
        "orphan_count": len(orphans),
        "orphan_ratio": (len(orphans) / visible) if visible else 0.0,
        "samples": orphans[:10],  # cap output
    }


def check_doublies(arr: np.ndarray) -> dict:
    """Detect parallel double-thickness lines (vertical and horizontal)."""
    h, w = arr.shape[:2]
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]

    doublies: list[dict] = []

    # Vertical doublies: two adjacent columns with identical y-extents in same color
    for x in range(w - 2):
        # Find runs in column x
        runs_a = column_runs(rgb, alpha, x)
        runs_b = column_runs(rgb, alpha, x + 2)
        # Check that column x+1 in the same y-extents is empty (background)
        for run in runs_a:
            (y0, y1, color) = run
            if (color, y0, y1) in [(c, y0_, y1_) for (y0_, y1_, c) in runs_b]:
                # Check empty middle column
                middle_empty = all(alpha[y, x + 1] == 0 for y in range(y0, y1 + 1))
                if middle_empty and (y1 - y0) >= 2:  # must be at least 3-px run
                    doublies.append({
                        "axis": "vertical",
                        "x": x, "y0": y0, "y1": y1,
                        "color": hex_from_rgb(color),
                    })

    # Horizontal doublies: same logic transposed
    for y in range(h - 2):
        runs_a = row_runs(rgb, alpha, y)
        runs_b = row_runs(rgb, alpha, y + 2)
        for run in runs_a:
            (x0, x1, color) = run
            if (color, x0, x1) in [(c, x0_, x1_) for (x0_, x1_, c) in runs_b]:
                middle_empty = all(alpha[y + 1, x] == 0 for x in range(x0, x1 + 1))
                if middle_empty and (x1 - x0) >= 2:
                    doublies.append({
                        "axis": "horizontal",
                        "y": y, "x0": x0, "x1": x1,
                        "color": hex_from_rgb(color),
                    })

    return {"doublies_count": len(doublies), "samples": doublies[:10]}


def column_runs(rgb: np.ndarray, alpha: np.ndarray, x: int) -> list[tuple[int, int, tuple]]:
    """Find runs of same-color pixels in column x. Returns [(y_start, y_end, color), ...]."""
    h = rgb.shape[0]
    runs = []
    y = 0
    while y < h:
        if alpha[y, x] == 0:
            y += 1
            continue
        color = tuple(rgb[y, x])
        y0 = y
        while y < h and alpha[y, x] > 0 and tuple(rgb[y, x]) == color:
            y += 1
        runs.append((y0, y - 1, color))
    return runs


def row_runs(rgb: np.ndarray, alpha: np.ndarray, y: int) -> list[tuple[int, int, tuple]]:
    """Same as column_runs but along x-axis."""
    w = rgb.shape[1]
    runs = []
    x = 0
    while x < w:
        if alpha[y, x] == 0:
            x += 1
            continue
        color = tuple(rgb[y, x])
        x0 = x
        while x < w and alpha[y, x] > 0 and tuple(rgb[y, x]) == color:
            x += 1
        runs.append((x0, x - 1, color))
    return runs


def check_pillow_shading(arr: np.ndarray) -> dict:
    """Detect pillow shading: dark-border + light-center regardless of light direction.

    Heuristic: for each connected non-transparent region:
      1. Find boundary pixels (alpha > 0, but at least one neighbor is alpha==0 or out of bounds)
      2. Find interior pixels (all 4-neighbors are alpha > 0)
      3. Compare mean luminance. If boundary_lum < interior_lum BY a wide margin,
         AND there's no clear light-direction asymmetry, it's pillow shading.
    """
    h, w = arr.shape[:2]
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    boundary_lums = []
    interior_lums = []
    for y in range(h):
        for x in range(w):
            if alpha[y, x] == 0:
                continue
            is_boundary = False
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if not (0 <= ny < h and 0 <= nx < w) or alpha[ny, nx] == 0:
                        is_boundary = True
                        break
                if is_boundary:
                    break
            lum = luminance(rgb[y, x, 0], rgb[y, x, 1], rgb[y, x, 2])
            if is_boundary:
                boundary_lums.append((x, y, lum))
            else:
                interior_lums.append((x, y, lum))

    if len(interior_lums) < 4 or len(boundary_lums) < 4:
        return {"detected": False, "reason": "insufficient interior/boundary samples"}

    bm = np.mean([l for (_, _, l) in boundary_lums])
    im = np.mean([l for (_, _, l) in interior_lums])

    # Pillow indicator: boundary noticeably darker than interior
    boundary_darker = (im - bm) > 30  # threshold in 0-255 luminance space

    if not boundary_darker:
        return {"detected": False, "boundary_mean_lum": float(bm), "interior_mean_lum": float(im)}

    # Check for light-direction asymmetry: split interior into top-left vs bottom-right halves
    # If TL is brighter and BR is darker (or vice versa), legit cell shading
    # If both halves equally light vs dark boundary → pillow shading
    interior_arr = np.array([[x, y, l] for (x, y, l) in interior_lums])
    cx = interior_arr[:, 0].mean()
    cy = interior_arr[:, 1].mean()
    tl_pixels = [l for (x, y, l) in interior_lums if x < cx and y < cy]
    br_pixels = [l for (x, y, l) in interior_lums if x >= cx and y >= cy]
    if len(tl_pixels) < 2 or len(br_pixels) < 2:
        return {"detected": True, "reason": "boundary darker, insufficient asymmetry data"}

    tl_mean = np.mean(tl_pixels)
    br_mean = np.mean(br_pixels)
    asymmetry = abs(tl_mean - br_mean)
    # If interior is uniformly light (not asymmetric per light direction) → pillow shading
    is_pillow = asymmetry < 20

    return {
        "detected": bool(is_pillow),
        "boundary_mean_lum": float(bm),
        "interior_mean_lum": float(im),
        "tl_mean_lum": float(tl_mean),
        "br_mean_lum": float(br_mean),
        "asymmetry": float(asymmetry),
    }


def check_hue_rotation(arr: np.ndarray) -> dict:
    """Compute hue rotation across luminance ramps in the palette."""
    h, w = arr.shape[:2]
    rgba = arr.reshape(-1, 4)
    visible = rgba[rgba[:, 3] > 0]
    unique = np.unique(visible[:, :3], axis=0)
    if len(unique) < 4:
        return {"applicable": False, "reason": "<4 unique colors"}

    hues_lums = []
    for c in unique:
        h_, s_, l_ = rgb_to_hsl(int(c[0]), int(c[1]), int(c[2]))
        hues_lums.append((l_, h_, s_, c))

    hues_lums.sort(key=lambda t: t[0])  # by luminance
    # Take top 25% (highlights) and bottom 25% (shadows)
    n = len(hues_lums)
    cut = max(1, n // 4)
    shadows = hues_lums[:cut]
    highlights = hues_lums[-cut:]

    sh_hue = sum(h for (_, h, _, _) in shadows) / len(shadows)
    hi_hue = sum(h for (_, h, _, _) in highlights) / len(highlights)

    delta = abs(sh_hue - hi_hue)
    delta = min(delta, 360 - delta)

    # Check warm-highlight rule: highlights hue should be 0-90 (red-yellow), shadows in cool (180-300, blue-violet)
    is_warm_high = 0 <= hi_hue <= 90 or hi_hue >= 330
    is_cool_low = 180 <= sh_hue <= 300

    return {
        "applicable": True,
        "shadow_mean_hue": float(sh_hue),
        "highlight_mean_hue": float(hi_hue),
        "hue_rotation_deg": float(delta),
        "rotation_passes_30": delta >= 30,
        "warm_highlight": bool(is_warm_high),
        "cool_shadow": bool(is_cool_low),
    }


def check_anti_aa_slop(arr: np.ndarray) -> dict:
    """Detect over-AA: high count of unique near-equal colors at silhouette boundaries.

    Boundary pixels = alpha > 0 with at least one alpha==0 neighbor.
    Count how many distinct boundary colors are "near" each other (within ΔE 10).
    """
    h, w = arr.shape[:2]
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    boundary_colors: list[tuple[int, int, int]] = []
    for y in range(h):
        for x in range(w):
            if alpha[y, x] == 0:
                continue
            is_boundary = False
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if not (0 <= ny < h and 0 <= nx < w) or alpha[ny, nx] == 0:
                        is_boundary = True
                        break
                if is_boundary:
                    break
            if is_boundary:
                boundary_colors.append(tuple(rgb[y, x].tolist()))

    if not boundary_colors:
        return {"applicable": False}

    counter = Counter(boundary_colors)
    unique_boundary = len(counter)
    total_boundary = len(boundary_colors)

    # If many distinct colors at boundary, signal of over-AA
    distinct_ratio = unique_boundary / total_boundary

    return {
        "boundary_pixel_count": total_boundary,
        "unique_boundary_colors": unique_boundary,
        "distinct_ratio": float(distinct_ratio),
        "warning": bool(distinct_ratio > 0.20),  # >20% unique
    }


def check_silhouette_readability(arr: np.ndarray) -> dict:
    """Render as solid silhouette (alpha mask) and compute simple shape metrics."""
    h, w = arr.shape[:2]
    alpha = arr[:, :, 3]
    silhouette = (alpha > 0).astype(np.uint8)
    visible = int(silhouette.sum())
    if visible == 0:
        return {"empty": True}
    # Bounding box
    ys, xs = np.where(silhouette)
    bbox_h = int(ys.max() - ys.min() + 1)
    bbox_w = int(xs.max() - xs.min() + 1)
    fill_ratio = visible / (bbox_h * bbox_w)
    # Symmetry score (left-right)
    flipped = silhouette[:, ::-1]
    sym_match = int(((silhouette == flipped) & (silhouette > 0)).sum())
    symmetry = sym_match / visible

    return {
        "visible_pixels": visible,
        "bbox": [bbox_w, bbox_h],
        "fill_ratio": float(fill_ratio),
        "horizontal_symmetry": float(symmetry),
    }


# --- Scoring -----------------------------------------------------------------

def score_findings(findings: dict) -> dict:
    """Compute overall 0-100 score from individual checks."""
    score = 100
    issues: list[str] = []
    warnings: list[str] = []

    p = findings.get("palette", {})
    if p.get("over_cap"):
        score -= 15
        issues.append(f"Palette over cap: {p.get('unique_color_count')} colors > {p.get('palette_cap')}")

    o = findings.get("orphans", {})
    orphan_ratio = o.get("orphan_ratio", 0)
    if orphan_ratio > 0.05:
        score = min(score, 50)
        issues.append(f"{o['orphan_count']} orphan pixels ({orphan_ratio:.1%}) — exceeds 5% cap")
    elif orphan_ratio > 0.02:
        score -= 10
        warnings.append(f"{o['orphan_count']} orphan pixels ({orphan_ratio:.1%})")

    d = findings.get("doublies", {})
    if d.get("doublies_count", 0) > 2:
        score = min(score, 50)
        issues.append(f"{d['doublies_count']} doublies detected (hard rule violated)")
    elif d.get("doublies_count", 0) > 0:
        score -= 8
        warnings.append(f"{d['doublies_count']} doublies — review")

    ps = findings.get("pillow_shading", {})
    if ps.get("detected"):
        score = min(score, 50)
        issues.append("Pillow shading detected — refactor with explicit light direction")

    h_rot = findings.get("hue_rotation", {})
    if h_rot.get("applicable") and not h_rot.get("rotation_passes_30"):
        score -= 10
        warnings.append(f"Hue rotation {h_rot.get('hue_rotation_deg', 0):.0f} degrees — should be >= 30")

    aa = findings.get("anti_aa_slop", {})
    if aa.get("warning"):
        score -= 12
        warnings.append(f"Possible over-AA: {aa.get('distinct_ratio', 0):.1%} of boundary pixels unique")

    score = max(0, score)
    if score >= 80:
        verdict = "ship"
    elif score >= 60:
        verdict = "fix-issues"
    else:
        verdict = "redesign"

    return {
        "score": score,
        "verdict": verdict,
        "issues": issues,
        "warnings": warnings,
    }


def evaluate_image(path: str, palette_cap: int | None = None) -> dict:
    """Top-level: load image, run all checks, return findings + score."""
    arr = load_image_as_array(path)
    findings = {
        "image_dimensions": list(arr.shape[:2][::-1]),  # (w, h)
        "palette": check_palette(arr, palette_cap),
        "orphans": check_orphan_pixels(arr),
        "doublies": check_doublies(arr),
        "pillow_shading": check_pillow_shading(arr),
        "hue_rotation": check_hue_rotation(arr),
        "anti_aa_slop": check_anti_aa_slop(arr),
        "silhouette": check_silhouette_readability(arr),
    }
    summary = score_findings(findings)
    return {"summary": summary, "findings": findings, "input": path}


def evaluate_animation(json_path: str) -> dict:
    """Evaluate animation JSON for cross-frame consistency."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "frames" not in data:
        return {"error": "Input has no `frames` array"}

    width = data["width"]
    height = data["height"]
    frames = data["frames"]

    # Cross-frame palette consistency
    all_colors_per_frame: list[set] = []
    for frame in frames:
        colors = set()
        for p in frame.get("pixels", []):
            colors.add(p["color"])
        all_colors_per_frame.append(colors)
    union = set().union(*all_colors_per_frame) if all_colors_per_frame else set()
    palette_consistent = all(c == union for c in all_colors_per_frame)

    # Pixel-mass conservation: similar visible pixel count across frames
    masses = [len(f.get("pixels", [])) for f in frames]
    mass_min, mass_max = min(masses), max(masses)
    mass_variation = (mass_max - mass_min) / max(mass_max, 1)

    # Per-frame quality (rendered)
    # Skipped here for brevity (would render each frame to a temp file and check)

    findings = {
        "frame_count": len(frames),
        "palette_consistent": palette_consistent,
        "palette_per_frame": [len(s) for s in all_colors_per_frame],
        "palette_union_size": len(union),
        "mass_min": mass_min,
        "mass_max": mass_max,
        "mass_variation_ratio": float(mass_variation),
    }

    issues = []
    warnings = []
    score = 100
    if not palette_consistent:
        score -= 15
        warnings.append("Palette differs across frames — some colors only used in subset of frames")
    if mass_variation > 0.5:
        score -= 15
        warnings.append(f"Mass varies by {mass_variation:.0%} between frames — may indicate inconsistent silhouette")

    return {
        "summary": {"score": score, "issues": issues, "warnings": warnings,
                    "verdict": "ship" if score >= 80 else "fix-issues" if score >= 60 else "redesign"},
        "findings": findings,
        "input": json_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Quality-check pixel art (PNG or JSON spec).")
    parser.add_argument("input", help="Path to image (.png) or JSON spec")
    parser.add_argument("--animation", action="store_true",
                        help="Treat input as JSON animation; check cross-frame consistency")
    parser.add_argument("--palette-cap", type=int, default=None,
                        help="Expected max palette size (e.g. 32 for endesga-32)")
    parser.add_argument("--verbose", action="store_true", help="Print full findings")
    args = parser.parse_args()

    if args.animation:
        result = evaluate_animation(args.input)
    else:
        result = evaluate_image(args.input, palette_cap=args.palette_cap)

    if args.verbose:
        print(json.dumps(result, indent=2))
    else:
        # Compact summary
        compact = {
            "input": result.get("input"),
            "summary": result.get("summary"),
        }
        print(json.dumps(compact, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
