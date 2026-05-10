# Drawing Techniques: Lines, Clusters, Anti-Aliasing, Outlining

The four classical "atomic moves" of pixel art. Master these and 80% of bad output disappears.

---

## 1. Pixel-perfect lines

### The geometry problem

Pixel art lines are governed by **integer pixel ratios**, not antialiased curves. A line drawn from (0,0) to (10,5) on a discrete grid must "step" — there is no half-pixel.

### Canonical patterns

| Slope | Pattern | Visual effect |
|---|---|---|
| 1:1 (45°) | one pixel per column AND row | Perfect diagonal, never AA |
| 2:1 | repeated 2-pixel horizontal segments | Smooth shallow slope |
| 1:2 | repeated 1-pixel segments stacked 2 high | Smooth steep slope |
| 3:1 | repeated 3-pixel segments | Very shallow slope |
| Mixed (e.g. 2,3,2,3) | inconsistent step lengths | **Jaggie — to avoid** |

**Rule (Pedro Medeiros)**: *the amount of pixels in each step on a perfect curve should follow geometrical progression*. Inconsistent step lengths within what should be a smooth curve = "jaggies".

### "Jaggies" detection

Jaggies are visible when:
- Adjacent steps differ in length without geometric reason
- A line has alternating 2,1,2,1,2,1 instead of 2,2,2 or 1,1,1
- A "smooth" curve has runs that don't progress monotonically

**Fix**: replan the curve. For circles use bresenham circle pattern. For arbitrary smooth curves, draw at 4× resolution and downsample with NEAREST.

### "Doublies" (double pixels)

Two parallel single-pixel lines that visually merge into a "thick" line without intent:

```
. # . . . #
. # . . . #
. # . . . #     <- Doublies (parallel 1-px lines)
                vs.
. # . . . . . # #
. # . . . . . # #
. # . . . . . # #     <- Single thick line (intentional 2-px)
```

**Detection** (in `quality_check.py`): scan for adjacent column pairs where both have identical y-extents and the column between is empty. Flag as warning.

**Fix**: merge into single 2-px line, OR remove the redundant parallel.

---

## 2. Anti-aliasing (selective AA)

### What AA is for in pixel art

AA inserts **intermediate-color halftone pixels** at the inside corners of staircase patterns to soften the visual stepping. It is **selective and surgical** — global AA blurs the sprite.

### Hard rules (Pedro Medeiros + Pixel Parmesan)

1. **NEVER** AA 45° lines or perfectly straight (horizontal/vertical) lines
2. Only staircase patterns **longer than 1×1** qualify for AA insertion
3. AA halftone strip is **proportional to step length**: long step ⇒ long halftone
4. **Horizontal slope ⇒ horizontal AA strip; vertical slope ⇒ vertical**
5. AA color = intermediate value between the line color and the background — usually one of the existing palette mid-tones, NOT a new color

### Visual example (16×8 detail)

```
Without AA:        With selective AA:
. . . X X X X .    . . . X X X X .
. . X X . . . .    . . X X . . . .       <- step 2px wide
. X X . . . . .    . X X o . . . .       <- AA pixel "o" at corner
X X . . . . . .    X X . . . . . .
```

The "o" pixel is darker than background but lighter than the line — typically existing palette mid-tone.

### Over-AA detection (anti-pattern)

If >20% of silhouette-boundary pixels are intermediate values between two-neighbor colors → over-AA'd → "AI-slop signal". Most beginner mistake when copying photos.

**Source**:
- Pedro Medeiros, *How to Start Making Pixel Art #5*: medium.com/pixel-grimoire
- Pixel Parmesan, *Anti-Aliasing Fundamentals*: pixelparmesan.com/blog/anti-aliasing-fundamentals-for-pixel-artists
- Chinese tutorial: zhuanlan.zhihu.com/p/469647969 — confirms horizontal/vertical AA-direction rule

---

## 3. Cluster theory

### What clusters are

A **cluster** = intentional group of same-color pixels that read as a shape, shadow, or form. The defining sentence (Saint11): *modern pixel art organizes pixels into intentional groups to better define textures of subject matter*.

### Cluster rules

1. **Every pixel should belong to a cluster** — no orphans (single isolated pixels) unless intentional texture (sparkles, stippling, scattered detail like sand)
2. Clusters of size 1 are 99% errors — usually missed cleanup or visual noise
3. Clusters of size ≥ 3 are clearly intentional shapes
4. **For medium-density textures**, clusters should be 3-7 pixels — smaller looks noisy, larger looks blobby
5. Clusters should have **clear boundaries** — pixels at the edge of a cluster should not bleed into background-color cluster except through intentional AA

### "Orphan pixel" detection

A pixel is orphan when none of its 8 neighbors share its color. Connected-component analysis (4-connectivity or 8-connectivity, both work) → cluster sizes → flag size-1.

In `quality_check.py`:
```python
from scipy.ndimage import label
mask = (image_array == target_color).astype(int)
labeled, num = label(mask, structure=np.ones((3,3)))  # 8-connectivity
sizes = np.bincount(labeled.ravel())[1:]  # skip background
orphans = (sizes == 1).sum()
```

### When orphans are OK

- Sparkles / glitter / stars / fireflies (visual noise that makes sense narratively)
- Stippling on rough materials (rust, sand, leather)
- Eye highlights (single bright pixel in a dark eye is iconic)

The skill should ask user before flagging these as errors.

**Source**:
- Saint11 / Pedro Medeiros pixel-grimoire #2
- Adam C. Younis "Pixel Art Class" YouTube series
- Pixnote.net glossary of pixel art terms

---

## 4. Outlining styles

### Three production styles

#### A) Full black outline
1-pixel solid outline around entire silhouette, in darkest color (NOT pure black `#000000` — try `#1A1C2C` or `#181425`).

**Use when**: action game, top-down RPG, target acquisition matters, sprite must read against any background.

**Examples**: Game Boy, NES sprites, most beginner tutorials, Stardew Valley NPCs.

#### B) Selective outline (selout)
Outline color **varies** along the silhouette:
- Where shadow falls → outline is dark (matches inner shadow)
- Where light hits → outline is lighter (or removed entirely against negative space)
- Where silhouette meets background → outline still present but takes on contextual tone

**Rule**: take the bordering pixel's value, then go one shade lower for the outline. Outline is one step darker than what it abuts.

**Use when**: hi-bit aesthetic, painterly look, atmospheric mood. Capcom/Konami late-SNES sprites use selout heavily.

**Examples**: Castlevania: Symphony of the Night, Metal Slug, Vagrant Story.

#### C) No outline (hi-bit / Eboy)
Relies on color contrast and silhouette discipline. Sprite reads through internal shading and palette choice rather than a hard border.

**Use when**: cinematic style, hi-bit aesthetic with strong palette. Risk: poor readability on busy backgrounds.

**Examples**: Owlboy, Hyper Light Drifter (the canonical no-outline hi-bit games), Tunic, Eboy commercial illustration.

### Pillow shading — anti-pattern

The wrong way: dark outline + progressive lightening toward geometric center, **regardless** of where the light source is.

```
Wrong (pillow):           Right (cell shaded):
. d d d d .               . d d d d .         <- light from top-left
. d m m d .               . d m m d .
. d m l d .               . d m m d .         <- inner pixels follow light direction,
. d d d d .               . d d D D .            shadow accumulates on opposite side
                                                 (D = darkest)
```

Detection: if every pixel touching silhouette boundary is dark, AND the inner pixels are progressively lighter toward geometric center (regardless of which side a light source would be on), it's pillow shading. Hard rule: refactor with explicit light source.

**Source**:
- Lospec articles: pixel-art-outlines (parts 1 & 2), Pillow Shading anti-pattern by Solar Lune
- Derek Yu: derekyu.com/makegames/pixelart2.html
- Yarrninja Pixel Tutorial Ch. 12 (selective outlining)
- Russian: Punch Club guide explicit rule "outline always darker than darkest pixel of object"

---

## 5. Russian "Punch Club rule" — draw at 1× render at 2-3×

Discovered as standard practice in Russian indie scene (Lazy Bear Games / Punch Club, widely cited at gamedev.ru):

**Rule**: Master art at 1× pixel scale (one logical pixel = one image pixel). Game engine renders at 2× or 3× via integer scaling. **Never** edit at 2x because that introduces sub-pixel edits that are not pixel-perfect at 1x.

In our renderer: master at JSON `width × height`; `pixel_size` parameter handles the upscale at render time.

**Source**: Shazoo Punch Club guide (shazoo.ru/2016/12/07/46717), DTF Punch Club guide (dtf.ru/gamedev/2510)

---

## 6. CN-specific: calligraphic outlining

Chinese tutorials (zhihu pixel art guides) reference 工笔 (gongbi, "fine brush") line work. Convention: **outline weight varies via clustered dark pixels on heavy side, lighter side gets no outline at all**.

This bridges (B) selective outline with traditional Chinese ink discipline. Useful for xianxia/wuxia art where line work feels brushed rather than mechanical.

```
Heavy side (sword spine):  . D D D D .
                           . D D D D .
                           . D D D D .

Light side (sword edge):   . . . . . .  <- no outline, color contrast only
                           # # # # # #     (silver vs background)
                           . . . . . .
```

**Source**: Chinese pixel tutorials at indienova.com 像素课堂, 32comic.com, zhuanlan.zhihu.com 像素画教程

---

## Summary table

| Technique | Hard rule | Soft rule | Detection in quality_check.py |
|---|---|---|---|
| 45° lines | NEVER AA | — | check for AA on perfect diagonals |
| Straight lines | NEVER AA | — | check for AA on horizontal/vertical |
| Selective AA | Only on staircase >1×1 | Halftone proportional to step | over-AA = >20% boundary pixels intermediate |
| Cluster | No orphans (size 1) | Cluster ≥ 3 for textures | connected-component count |
| Doublies | No accidental parallel 1-px lines | — | column-pair y-extent match |
| Outline | If full outline, ≥ darkest object pixel (Punch Club) | — | sample boundary pixels vs interior |
| Pillow shading | NEVER (anti-pattern) | — | dark-border + light-center against light direction |
