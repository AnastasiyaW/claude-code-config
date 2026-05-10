# Quality Rubric: Automated Scoring and Anti-AI-Slop Detection

This file defines the complete specification for `scripts/quality_check.py`. Every check listed here must be implemented; every score weight must match what the script computes.

---

## 1. Overall scoring structure

**Total score: 0-100**

| Component | Max points | Weight | Computed by |
|---|---|---|---|
| Per-pixel hygiene | 25 | 0.25 | Section 2 |
| Cluster coherence | 20 | 0.20 | Section 3 |
| Palette discipline | 20 | 0.20 | Section 4 |
| Silhouette readability | 15 | 0.15 | Section 5 |
| Anti-AI-slop | 20 | 0.20 | Section 7 (anti-signals) |

**Score interpretation**:
| Score | Action |
|---|---|
| >= 80 | Ship — production quality |
| 60-79 | Fix listed issues, re-run |
| 40-59 | Significant redesign needed |
| < 40 | Complete restart recommended |

For animation: run per-frame checks on every frame, then add animation-consistency checks (section 6). Overall animation score = mean of per-frame scores, penalized by consistency failures.

---

## 2. Per-pixel hygiene (25 pts)

### 2.1 Orphan pixels

**Definition**: a pixel with no same-color neighbor in its 8-directional neighborhood.

**Detection**:
```python
from scipy.ndimage import label
import numpy as np

def count_orphans(image_array):
    """Count single-pixel isolated clusters per color."""
    orphan_total = 0
    for color in unique_colors(image_array):
        mask = (image_array == color).all(axis=-1).astype(int)
        labeled, num_features = label(mask, structure=np.ones((3,3)))
        sizes = np.bincount(labeled.ravel())[1:]
        orphan_total += (sizes == 1).sum()
    return orphan_total
```

**Threshold**: `orphan_ratio = orphan_count / total_pixels`
- 0.0-0.02 (0-2%): full marks
- 0.02-0.05 (2-5%): warning, minor deduction
- > 0.05 (>5%): significant deduction

**Exception**: do not count transparent pixels as orphans. Do not flag if `--allow-stipple` flag is set (for deliberate stippling textures like sand or rust).

**Scoring**: `orphan_score = max(0, 10 - (orphan_ratio * 200))`

### 2.2 Doublies (parallel double-pixel lines)

**Definition**: two parallel single-pixel-wide lines running adjacent without the intent to form a 2-pixel wide line.

**Detection**: scan column pairs (or row pairs). For each adjacent column pair, check if both columns have identical non-background pixel y-extents with the same color. If the column between them is empty, flag as doubling.

```python
def detect_doublies(image):
    """Scan for accidental parallel single-pixel lines."""
    doublies = 0
    for x in range(image.width - 2):
        col_a = get_col_pixels(image, x)
        col_b = get_col_pixels(image, x + 1)
        if col_a == col_b and are_adjacent_pixels_same_color(image, x, x+1):
            doublies += 1
    return doublies
```

**Threshold**:
- 0 doublies: full marks (5 pts)
- 1-3 doublies: minor deduction
- > 5 doublies: major deduction

**Scoring**: `doublies_score = max(0, 5 - doublies * 1.5)`

### 2.3 Banding

**Definition**: visible parallel bands in a gradient where one color's band is much wider than neighbors.

**Detection**:
```python
def detect_banding(image, ramp_axis="vertical", threshold=2.0):
    """Detect uneven color band widths along a gradient."""
    bands = group_consecutive_same_color_regions(image, ramp_axis)
    if len(bands) < 3:
        return 0  # not enough bands to detect banding
    widths = [b.pixel_count for b in bands]
    ratio = max(widths) / max(min(widths), 1)
    return ratio
```

**Threshold**:
- band_ratio <= 1.5: full marks (10 pts)
- 1.5-2.0: minor deduction
- > 2.0: significant deduction

**CN-specific note**: Chinese tutorials more aggressively flag banding. For CN-style sprites, tighten threshold to 1.5. Source: zhuanlan.zhihu.com/p/360463918.

**Scoring**: `banding_score = max(0, 10 - (max(0, band_ratio - 1.5) * 10))`

---

## 3. Cluster coherence (20 pts)

### 3.1 Silhouette contiguity

**Definition**: the sprite's main silhouette (all non-transparent pixels) should be one connected component, not a scattering of disconnected regions.

**Detection**: 4-connected component analysis on the alpha mask (non-transparent pixels). Number of components should be ≤ expected isolated elements (e.g., a character with a separate held item = 2 components is acceptable; 10 components is not).

```python
def silhouette_components(image):
    alpha_mask = (image_alpha > 0).astype(int)
    labeled, n = label(alpha_mask, structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    return n
```

**Threshold**:
- 1-2 components: full marks (10 pts)
- 3-5: acceptable (small deduction)
- > 5: silhouette is fragmented

### 3.2 Autocorrelation / cluster coherence

**Definition**: same-color pixels should be grouped, not scattered randomly. Spatial autocorrelation of color assignment should be positive.

**Simplified heuristic**: for each color, compute average cluster size (from section 2.1 connected-component analysis). If average cluster size < 2 for any non-outline color, the clusters are too small.

```python
def cluster_coherence_score(image_array):
    scores = []
    for color in non_outline_colors(image_array):
        mask = (image_array == color).all(axis=-1).astype(int)
        labeled, n = label(mask, structure=np.ones((3,3)))
        if n == 0:
            continue
        sizes = np.bincount(labeled.ravel())[1:]
        avg_size = np.mean(sizes)
        scores.append(min(1.0, avg_size / 5.0))  # normalized: 5px avg cluster = 1.0
    return np.mean(scores) if scores else 0.5
```

**Scoring**: `coherence_score = cluster_coherence_score(image) * 10`

---

## 4. Palette discipline (20 pts)

### 4.1 Unique color count

**Definition**: total unique (non-transparent) colors used must be <= the stated palette cap.

```python
def unique_color_count(image):
    pixels = [p for p in image.getdata() if p[3] > 0]  # non-transparent
    return len(set((p[0], p[1], p[2]) for p in pixels))
```

**Threshold** (when `--palette-cap N` is specified):
- count <= cap: full marks (8 pts)
- count <= cap * 1.2: minor deduction (within 20% of cap)
- count > cap * 1.5: major deduction

**Off-palette check**: if `--palette-ref endesga-32` is specified, each used color must be within CIELAB delta-E 5.0 of a palette entry. Colors outside this threshold are "off-palette."

### 4.2 Hue rotation across luminance ramp

**Definition**: for any detected ramp of ≥ 4 related colors (ordered by luminance), hue should rotate >= 30°.

**Detection**:
1. Convert all unique colors to HSL
2. Sort by L (luminance)
3. Identify "ramps" — runs of colors with similar hue (within 45°) but varying L
4. For each ramp >= 4 colors: compute delta-hue from darkest to lightest

```python
def hue_rotation_across_ramp(colors_hsl):
    sorted_by_L = sorted(colors_hsl, key=lambda c: c[2])
    if len(sorted_by_L) < 4:
        return 0
    dark_hue = sorted_by_L[0][0]
    light_hue = sorted_by_L[-1][0]
    return abs(light_hue - dark_hue) % 360
```

**Threshold**:
- >= 30°: full marks (8 pts)
- 15-30°: minor deduction (soft warning)
- < 15°: significant deduction — palette looks "muddy"

**CN strict mode** (`--strict-warm-cool`): additionally check that light-end hue is warmer (closer to yellow-orange, hue 30-60°) and dark-end hue is cooler (closer to blue-violet, hue 200-280°). Failure = additional 4pt deduction.

### 4.3 Warm-highlight / cool-shadow check

**Detection**: compare top 25% luminance colors (highlights) vs bottom 25% (shadows). Compute mean hue temperature:
- "warm" = hue in range 0-60° or 330-360° (red, orange, yellow)
- "cool" = hue in range 180-300° (blue, cyan, purple)

Scores: highlights_warm AND shadows_cool = pass (4 pts); partial = 2 pts; neither = 0 pts.

---

## 5. Silhouette readability (15 pts)

### 5.1 Render-as-solid heuristic

**Procedure**: convert the sprite to a solid silhouette (all non-transparent pixels → black, transparent pixels → white). Ask: does the shape read as the intended subject?

This is inherently heuristic. Approximation in quality_check.py:
1. Compute silhouette (binary alpha mask)
2. Compute aspect ratio
3. Compute roundness (ratio of area to perimeter^2): `roundness = 4π × area / perimeter²`
4. Detect major protrusions count (arms, legs, antennae, etc.) via concavity analysis
5. Compare to expected subject parameters if `--subject character|animal|item|building` is specified

**Simplified scoring**:
- Silhouette is a single connected component (from section 3.1): +5 pts
- Silhouette has recognizable concavities (not a blob): +5 pts
- Silhouette aspect ratio matches subject type (e.g., humanoid = 0.4-0.7 width/height): +5 pts

**Note**: full semantic readability cannot be tested algorithmically. The render-as-solid test catches catastrophically fragmented or blobby sprites; it does not guarantee artistic quality.

---

## 6. Animation consistency checks

These checks run ONLY when `--animation` flag is set. Applied to every pair of consecutive frames.

### 6.1 Palette stability

All frames in a tag must use the same palette entries. An off-palette color appearing in only some frames = flickering artifact.

```python
def palette_stability(frames):
    all_palettes = [set(unique_colors(f)) for f in frames]
    union = set.union(*all_palettes)
    intersection = set.intersection(*all_palettes)
    drift = len(union) - len(intersection)
    return drift  # 0 = perfectly stable
```

**Threshold**: drift == 0 for full marks; drift > 3 = warning; drift > 8 = failure.

### 6.2 Pixel rate consistency

Sub-pixel AA placement should be consistent: if frame 0 has an AA pixel at (5, 10), frame 1 should have it too unless intentional animation of that AA pixel.

**Simplified check**: count total AA (intermediate-value boundary) pixels per frame. Standard deviation across frames should be < 5% of mean.

### 6.3 Total mass conservation

For each non-transparent color, count total pixels per frame. The total pixel count should stay approximately constant across frames of the same animation (a 32px torso doesn't suddenly become 28px in frame 3).

```python
def mass_conservation(frames, tolerance=0.08):
    masses = [sum(1 for p in f.getdata() if p[3] > 0) for f in frames]
    mean_mass = np.mean(masses)
    deviations = [abs(m - mean_mass) / mean_mass for m in masses]
    return max(deviations)  # should be < tolerance
```

**Threshold**: max_deviation < 0.05 = full marks; 0.05-0.15 = warning; > 0.15 = failure (frame has mass-drift indicating a sizing inconsistency).

---

## 7. Anti-AI-slop signals (up to -20 points penalty)

These are DETECTION SIGNALS for AI-generated content masquerading as pixel art. Each detected signal applies a penalty. Multiple signals compound.

The 8 canonical AI-slop signals:

### Signal 1: Blurry edges

**What it is**: high count of unique near-equal colors at the silhouette boundary (antialiasing applied globally, not selectively).

**Detection**:
```python
def blurry_edges_signal(image):
    boundary_pixels = get_silhouette_boundary_pixels(image)
    unique_near_equal = count_near_equal_color_pairs(boundary_pixels, delta_e_threshold=15)
    ratio = unique_near_equal / max(len(boundary_pixels), 1)
    return ratio > 0.20  # >20% of boundary pixels are intermediate
```

**Rule**: >20% of silhouette-boundary pixels being intermediate values between two neighbors = blurry edges. Source: pixel-parmesan.com Anti-Aliasing Fundamentals; habr.com/ru/articles/241666/

**Penalty**: -5 pts if triggered.

### Signal 2: Fractional pixel widths

**What it is**: lines that appear 1.5px wide — a supersampling artifact impossible in genuine pixel art. Detected as 1-pixel-wide line segments adjacent to another 1-pixel-wide line segment of a noticeably different but related color, with no intentional shading reason.

**Detection**:
```python
def fractional_width_signal(image):
    """Detect ~1.5px effective widths via adjacent near-equal parallel lines."""
    for x in range(image.width - 1):
        for y in range(image.height):
            p1 = image.getpixel((x, y))
            p2 = image.getpixel((x + 1, y))
            if color_distance(p1, p2) < 20 and both_nonzero_alpha(p1, p2):
                # adjacent near-equal non-outline, non-outline pair
                if not_matching_any_ramp(p1, p2, image):
                    yield (x, y)
```

**Threshold**: > 5% of pixels implicated = signal triggered.

**Penalty**: -4 pts if triggered.

### Signal 3: Random/oversaturated palette

**What it is**: too many unique colors with no discernible ramp structure; colors appear random rather than chosen.

**Detection**:
- unique_color_count > 32 for a sprite <= 64×64: flag
- OR: hue distribution is roughly uniform (not concentrated in a few hue families) → flag
- OR: saturation distribution has many outliers (colors that are wildly more or less saturated than the average): flag

**Threshold**: any two of the three conditions = signal triggered.

**Penalty**: -5 pts if triggered.

### Signal 4: Noise instead of dithering

**What it is**: randomly placed transitional pixels rather than a structured dithering pattern (Bayer, Floyd-Steinberg, Atkinson).

**Detection**:
```python
def noise_vs_dithering_signal(image):
    """Check if intermediate-value pixels form a recognizable structured pattern."""
    intermediate = [(x,y) for x,y,p in pixels if is_intermediate_color(p)]
    if len(intermediate) < 20:
        return False
    # Check for Bayer 4x4 regularity: if dithering, should see period-4 or period-2 pattern
    periodicity = compute_spatial_autocorrelation(intermediate, max_lag=4)
    # Genuine dithering: periodicity > 0.3 at period 2 or 4
    return max(periodicity) < 0.15  # no periodicity = noise
```

**Penalty**: -4 pts if triggered.

### Signal 5: Gradient over flat areas

**What it is**: smooth linear interpolation between two colors over a large area, rather than stepped ramp. The "lerp instead of stepped" failure mode.

**Detection**: scan horizontal/vertical strips through the sprite. If a run of 8+ pixels shows a monotonically increasing color channel with no flat plateaus (steps), it's a gradient, not a ramp.

```python
def gradient_over_flat_signal(image):
    for row in range(image.height):
        row_colors = [image.getpixel((x, row)) for x in range(image.width)]
        runs = detect_monotone_runs(row_colors, channel='V', min_length=8)
        for run in runs:
            if run.has_no_plateaus:
                return True
    return False
```

**Penalty**: -5 pts if triggered.

### Signal 6: Pillow shading

**What it is**: darker pixels at silhouette boundary, lighter pixels toward geometric centroid, regardless of light source direction. (Defined in detail in `references/03-shading-materials.md`.)

**Detection**:
1. Find geometric centroid of sprite (center of mass of non-transparent pixels)
2. For each non-transparent pixel, compute: distance_to_centroid and luminance_value
3. Compute Pearson correlation between distance_to_centroid and luminance_value
4. If correlation > +0.4 (closer to center = brighter), it's pillow shading

```python
def pillow_shading_signal(image):
    pixels = get_nontransparent_pixels_with_coords(image)
    centroid = compute_centroid(pixels)
    distances = [euclidean_distance(p.coord, centroid) for p in pixels]
    luminances = [p.luminance for p in pixels]
    correlation = pearsonr(distances, luminances)[0]
    return correlation > 0.40
```

**Penalty**: -5 pts if triggered. (Also reported as primary quality issue in hygiene section.)

### Signal 7: Inconsistent pixel grid

**What it is**: some pixels are 1×1, others appear 1×2 or 2×2 (supersampling artifact from rendering at wrong scale and then downsampling). Detected as irregular effective pixel sizes.

**Detection**: look for repeating pixel pairs — if image has many 2×2 blocks of the same color that don't align to any power-of-2 grid, it was likely generated at higher resolution and then naively downsampled.

```python
def inconsistent_grid_signal(image):
    """Detect if effective pixel size is non-uniform."""
    run_lengths_h = get_horizontal_same_color_run_lengths(image)
    run_lengths_v = get_vertical_same_color_run_lengths(image)
    # If dominant run length is 2 but many 1s exist, mixed grid
    modal_run = mode(run_lengths_h)
    single_runs = sum(1 for r in run_lengths_h if r == 1)
    double_runs = sum(1 for r in run_lengths_h if r == 2)
    # Mixed 1 and 2 pixel runs without pattern = inconsistent grid
    if modal_run == 2 and single_runs / max(double_runs, 1) > 0.3:
        return True
    return False
```

**Penalty**: -3 pts if triggered.

### Signal 8: Off-palette colors

**What it is**: when a target palette is specified, the sprite uses colors not in that palette (not even close, beyond dithering tolerance).

**Detection**: for each unique pixel color, find the nearest palette color (Euclidean distance in CIELAB). If minimum delta-E > 10 for any used color → off-palette.

```python
def off_palette_signal(image, palette):
    off_count = 0
    for color in unique_colors(image):
        nearest_dist = min(deltaE_ciede2000(color, p) for p in palette)
        if nearest_dist > 10:
            off_count += 1
    return off_count > 0
```

**Penalty**: -4 pts per 5 off-palette colors (compounding, max -8 pts from this signal alone).

---

## 8. Quality check output format

`quality_check.py` outputs JSON:

```json
{
  "score": 73,
  "grade": "FIX",
  "components": {
    "per_pixel_hygiene": {"score": 18, "max": 25, "issues": ["3 doublies detected at (5,12), (7,12), (11,4)"]},
    "cluster_coherence": {"score": 15, "max": 20, "issues": ["silhouette has 4 components (expected ≤2)"]},
    "palette_discipline": {"score": 14, "max": 20, "issues": ["hue rotation only 12° (need ≥30°)"]},
    "silhouette_readability": {"score": 12, "max": 15, "issues": []},
    "anti_ai_slop": {"score": 14, "max": 20, "issues": ["gradient over flat area detected", "20 off-palette colors"]}
  },
  "slop_signals": {
    "blurry_edges": false,
    "fractional_widths": false,
    "random_palette": false,
    "noise_not_dithering": false,
    "gradient_over_flat": true,
    "pillow_shading": false,
    "inconsistent_grid": false,
    "off_palette": true
  },
  "recommendations": [
    "Replace smooth gradient at rows 10-18 with a 3-step cell-shaded ramp",
    "Quantize palette to 32 colors using scripts/palette.py --quantize"
  ]
}
```

---

## 9. Invoking quality_check.py

```bash
# Single frame
python scripts/quality_check.py sprite.png

# With palette constraint
python scripts/quality_check.py sprite.png --palette-ref endesga-32

# Animation
python scripts/quality_check.py --animation walk.json

# Light direction for pillow shading detection
python scripts/quality_check.py sprite.png --light-dir top-left

# Strict CN warm/cool check
python scripts/quality_check.py sprite.png --strict-warm-cool

# Verbose (includes pixel-level details)
python scripts/quality_check.py sprite.png --verbose

# Allow stippling (don't penalize orphan pixels in stipple mode)
python scripts/quality_check.py sprite.png --allow-stipple
```

Exit codes: `0` = score >= 80 (ship), `1` = score 40-79 (fix), `2` = score < 40 (redesign).

---

## 10. Quick-reference thresholds

| Check | Pass threshold | Fail threshold | Score |
|---|---|---|---|
| Orphan ratio | <= 2% | > 5% | 0-10 pts |
| Doublies count | 0 | > 5 | 0-5 pts |
| Banding ratio | <= 1.5 | > 2.0 | 0-10 pts |
| Silhouette components | <= 2 | > 5 | 0-10 pts |
| Cluster coherence | avg >= 5px | avg < 2px | 0-10 pts |
| Unique colors | <= palette cap | > cap * 1.5 | 0-8 pts |
| Hue rotation | >= 30° | < 15° | 0-8 pts |
| Warm-highlight/cool-shadow | both correct | neither | 0-4 pts |
| Blurry edges signal | < 20% boundary intermediate | >= 20% | -5 pts |
| Fractional widths signal | < 5% pixels implicated | >= 5% | -4 pts |
| Random palette signal | <=2 of 3 sub-conditions | 3 of 3 | -5 pts |
| Noise not dithering signal | periodicity >= 0.15 | < 0.15 | -4 pts |
| Gradient over flat signal | no runs of 8+ monotone | runs found | -5 pts |
| Pillow shading signal | pearsonr <= 0.40 | > 0.40 | -5 pts |
| Inconsistent grid signal | ratio <= 0.3 | > 0.3 | -3 pts |
| Off-palette signal | 0 off-palette colors | any found | -4 per 5 (max -8) |
