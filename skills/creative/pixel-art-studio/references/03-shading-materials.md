# Shading, Lighting, and Material Recipes

Shading is the layer where color theory meets geometry. Bad shading makes technically clean sprites read as flat or wrong. The single most common shading error is pillow shading — this file encodes how to avoid it and how to shade each material correctly.

---

## 1. Light source conventions

### Standard directions

| Direction | Use case | Notes |
|---|---|---|
| **Top-left** (default) | Old-school Western retro, JRPG | Most common — matches reading gravity |
| Top-center | Stylized / overhead dungeon | Celeste-style, flatter shadow cast |
| Top-right | Mirrored scenes, alternate game cameras | Rare, breaks cross-sprite consistency |
| Side-left / side-right | Silhouette emphasis, cinematic | Strong contrast, rim reads clearly |
| Bottom / under-light | Atmospheric, horror, magic pools | Inverts standard shadow placement |
| Rim light (back-light) | Cinematic, boss intros, death screens | Adds depth; always pair with ambient fill |

**Rule**: establish ONE light direction per scene and apply it to every sprite in that scene. Mixing directions across sprites destroys visual cohesion.

**CN-specific**: Chinese tutorials codify warm/cool contrast as a **hard rule**, not a tip. See section 4.

### Light source encoding in quality_check.py

For pillow-shading detection, the checker needs to know the intended light direction. Pass via `--light-dir top-left|top|top-right|left|right|bottom` to set the expected shadow quadrant. Default is `top-left`.

---

## 2. Shading styles

### Cell shading (recommended default)

Hard boundaries between 2-4 discrete shade values. No intermediate gradient — all transitions are pixel-sharp.

```
Light source: top-left

.  .  H  H  H  .  .     H = highlight (lightest)
.  H  H  M  M  .  .     M = midtone (base color)
.  H  M  M  D  .  .     D = dark (shadow)
.  M  M  D  D  .  .     S = shadow (darkest, against ground)
.  D  D  S  S  .  .
```

**Shade count by sprite size**:
| Sprite size | Shade count |
|---|---|
| 8×8 | 2 (base + shadow) |
| 16×16 | 2-3 |
| 32×32 (standard) | 3-4 |
| 48×48+ | 4-5 |
| Hi-bit (64×64+) | 5-6 |

**Terminator** (the boundary between light and shadow) must be pixel-sharp. If you blur it, it reads as gradient shading.

**Source**: saint11.art tutorials; Pedro Medeiros medium.com/pixel-grimoire #4; habr.com/ru/articles/242925/ (Light and shadow, Курс пиксель-арта часть 4)

### Gradient shading

Smooth dithered transitions — acceptable for large background areas, terrain, water surfaces. Avoid on small sprites (< 32×32) because the dithered transition often occupies too large a proportion of the shape.

**When to use**: backgrounds, skies, large terrain features, water. Not for small characters.

**Implementation**: use Bayer 4×4 dithering between two adjacent palette values. Blue-noise for subtle modern gradients.

### Pillow shading — ANTI-PATTERN

Dark edges around the **geometric center** of the shape regardless of where the light source is. The shape looks like it has been shaded with an oval blur.

**Detection** (automated in `quality_check.py`):
1. Find the silhouette boundary pixels
2. Find the geometric centroid of the sprite
3. Measure: are boundary pixels systematically darker than centroid-region pixels?
4. Compute gradient direction toward centroid — if it correlates with lightness increase, flag as pillow shading

```
Pillow shading (WRONG):     Cell shading (RIGHT):
. D D D D D .               . D D D D D .
. D M M M D .               . D M H H D .   <- H top-left from light
. D M H M D .               . D M M M D .
. D M M M D .               . D D D M D .   <- D bottom-right shadow
. D D D D D .               . D D D D D .
```

**Source**: Lospec "Pillow Shading" anti-pattern article by Solar Lune; derekyu.com/makegames/pixelart2.html; habr.com/ru/companies/playgendary/articles/485704/ (типичные ошибки)

---

## 3. Specular highlights

**Specular highlight** = the small bright point where light reflects most directly into the viewer's eye. Size and sharpness encode material gloss:

| Material | Specular | Shape | Size |
|---|---|---|---|
| Polished metal | Very high | Sharp point | 1-2 pixels |
| Wet skin | High | Soft dot | 2-3 pixels |
| Matte skin | Low or none | — | — |
| Glass/crystal | Very high | Linear stripe | 1 pixel wide, 3-5 long |
| Wood (lacquered) | Medium | Small oval | 2-3 pixels |
| Stone | None or trace | — | — |
| Leather (oiled) | Low-medium | Diffuse | 3-5 pixels |
| Water surface | High, animated | Horizontal stripe | 1 pixel, animated |
| Matte fabric | None | — | — |

**Color rule**: specular highlight is NOT pure white. It should be the lightest palette color, which in a hue-shifted ramp tends toward warm yellow-white. Pure `#FFFFFF` is only acceptable for glass/crystal flash effects.

**Russian term**: "блик" or "рефлекс". Sources: habr.com/ru/articles/242925/, gas13.ru/v3/tutorials/

---

## 4. Rim light (back-light)

Rim light simulates a light source behind the character, creating a bright halo on the silhouette edge facing away from the primary light source. Used for:
- Boss character introductions
- Cinematic scenes (death sequences, magic activation)
- Depth separation (foreground character vs busy background)

**Implementation**: add 1-pixel-wide highlights on the side of the sprite OPPOSITE the primary light source. Color is typically a cool blue or warm orange depending on environment (moonlight vs fire). This color does NOT need to come from the main shading ramp — it's a separate, often vivid, palette entry.

**Rim + ambient**: rim light alone looks unmoored. Pair with 1-2 shades of ambient occlusion fill to ground the sprite.

---

## 5. Ambient occlusion

Ambient occlusion (AO) = darkening in tight crevices and enclosed spaces where environmental light cannot penetrate. Even in simplified cell-shaded pixel art, AO reads correctly:

- **Armpits, groins, where limbs meet torso**: darkest shadow
- **Under eaves, beneath horizontal overhangs**: darkest shadow
- **Inside ear canals, folds in fabric**: 1-2 shades darker than surrounding area
- **Between adjacent objects that touch**: dark contact shadow line

In pixel art, AO is often represented as the darkest (4th/5th shade) used sparingly in anatomically correct crevice positions rather than everywhere the secondary shadow falls.

---

## 6. Material recipes (concrete shade counts + hue tendency)

### Skin

- **Shades**: 3-4
- **Hue tendency**: base at warm red-orange (hue 15-25°); shadows shift cool toward red-brown (hue 0-10°); highlights warm toward peach-yellow (hue 30-45°)
- **Specular**: none on matte skin; 2-3px soft dot on oily/wet skin
- **Avoid**: dithering on skin (looks like stubble or acne unless intended)
- **Outline**: use darkest skin tone, NOT pure black — typical range `#5b2d2d` to `#8b4a3a`
- **Shade count increase**: Asian skin tones may use slightly higher saturation in warm tones; dark skin uses same hue logic but shifted value range

### Metal (armor, sword, coin)

- **Shades**: 5-7 (highest range of any material — metal has high contrast)
- **Hue tendency**: cool blue cast in shadows (shadow hue near 220°); highlights go neutral-to-warm (near white or pale yellow)
- **Specular**: 1-2 px sharp white or near-white highlight; glass-specular width
- **Bevel**: for faceted metal (gems, plate armor segments), use **sub-bevel** — a bright pixel-wide stroke along the top/lit edge of each facet, then a dark pixel-wide stroke along the bottom/shadow edge
- **Distinguish polished vs matte**: polished = high contrast + specular; matte = limited to 3-4 shades, no specular
- **Source**: Pedro Medeiros pixel-grimoire material tutorials; indienova.com/column/19 像素课堂#4

### Wood

- **Shades**: 3-4
- **Hue tendency**: warm brown base (hue 25-35°); shadows toward dark red-brown; highlights toward tan/yellow
- **Texture**: wood grain represented as horizontal cluster striations — thin dark lines (2-3 px long) running with the grain direction
- **Gloss**: typically low; lacquered wood gets 1 specular dot
- **Avoid**: overly smooth shading — grain clusters define it as wood

### Stone

- **Shades**: 3-4
- **Hue tendency**: neutral to cool gray; slight warm cast in sandstone/limestone; cool blue-gray in dungeon stone
- **Texture**: irregular cluster sizes — use dithered mid-tones instead of hard boundaries for a rough surface suggestion
- **Specular**: none (matte)
- **Variation**: mossy stone adds green clusters in shadow areas (typically AO zones)

### Water

- **Shades**: 4-6 in color; plus animated highlights
- **Hue tendency**: cyan-blue ramp; deep water darker and more saturated; surface layer lighter and desaturated
- **Transparency**: simulate by partially blending bg color into water color (typically 2 palette entries that are bg-influenced)
- **Animation**: top-surface highlight pixels shift horizontally 1-2px per frame; typically 4-6 frame loop
- **Specular**: horizontal stripe 1px tall; animates with overall water cycle

### Fire

- **Shades**: 5-6
- **Hue tendency**: hottest core = white → pale yellow (hue 55-65°); medium flame = orange-red (hue 15-30°); dark outer edge = deep red or dark red-brown (hue 0-10°); cool at edge = darkest, sometimes near-black
- **Structure**: inverted from normal shading — lightest at center-bottom, darkest at top edges (flame rises, hottest near fuel)
- **Animation**: 4-6 frame loop; flame top pixels shift up and slightly side-to-side
- **Subtlety**: the dark-edge / hot-center gradient is specifically the OPPOSITE of pillow shading — valid because fire IS hottest at center

### Glass / crystal

- **Shades**: 3-5 plus specular
- **Hue tendency**: typically near-neutral or tinted by glass color; highlights extremely pale
- **Transparency**: mix bg color at ~50% opacity value with glass hue into the "body" shade; near-full bg at the far edge
- **Specular**: 1px wide linear stripe — the "Fresnel" glint — typically running diagonally from top-left to bottom-right
- **Refraction line**: 1px dark vertical or diagonal stripe slightly off-center representing light-bending artifact
- **Sub-bevel for facets**: critical for gem/crystal facets — each facet face gets its own light gradient. Bright on top face, dark on bottom face, single dark pixel between faces
- **Source**: pixel-art-shading-glass technique documented at lospec.com/pixel-art-academy; indienova像素课堂

### Leather

- **Shades**: 3-4
- **Hue tendency**: base dark brown or black; shadows near pure black; highlights in warm tan-orange if oiled, or just slightly lighter brown if matte
- **Specular**: small (2-3px) if oiled leather; none if matte
- **Texture**: subtle creasing represented as thin darker lines at natural fold points (knee joints, elbow bends)

### Fabric (cloth, cotton, linen)

- **Shades**: 3-4
- **Hue tendency**: follows color of fabric but with minimal hue shift — fabric is diffuse; hue shift ≤ 15-20° across ramp is enough
- **Specular**: none (matte)
- **Fold structure**: alternating light/dark vertical stripes in hanging fabric; curved lines in pulled fabric
- **Avoid**: shading cloth with the same specular logic as metal — cloth absorbs, it does not reflect

---

## 7. CN-specific: warm/cool contrast as hard rule

In Chinese beginner tutorials, the warm-highlight / cool-shadow rule is stated as a **mandatory constraint**, not aesthetic guidance:

> Highlights MUST shift warm (toward yellow-orange hue range).
> Shadows MUST shift cool (toward blue-violet hue range).
> No exceptions.

This is **stricter than the Endesga / Saint11 framing** (which presents it as a tip). For quality_check.py scoring:
- For CN-style sprites: warm-highlight + cool-shadow = mandatory check (failure = score deduction)
- For generic sprites: soft warning when hue shift < 15°

**Hue shift threshold** (from zhuanlan.zhihu.com/p/47540319 — 笨办法学像素画：颜色选择搭配指南):
- Minimum: 20° hue rotation across ramp to qualify as "proper shift"
- Ideal: 30-60° (Endesga rule; zhuanlan.zhihu.com/p/47540319)

---

## 8. Bevel and sub-bevel for metal and glass facets

**Bevel**: a pixel-wide strip along an edge, lighter on the top/lit face, darker on the bottom/shadow face. Creates the illusion of a flat planar surface being edge-lit.

**Sub-bevel**: applied inside a faceted shape (gem, plate armor, crown jewel) to represent each individual facet separately. Each internal face gets its own one-pixel bevel line.

```
Crystal gem example (8x8):

. . H H S S . .    <- top face: H=bright, S=shadow
. H b b b b S .    <- b = body color; H/S = bevel
. H b b b b S .
. H b b f b S .    <- f = refraction line (dark, 1px)
. . S S H H . .    <- bottom face: reversed
```

The apparent depth of a faceted object scales with number of sub-bevel lines visible. For a 16px gem: 2-3 facets. For 32px gem: 4-6 facets.

**Source**: lospec.com shading tutorials; Pedro Medeiros gemstone tutorial at saint11.art

---

## Summary table

| Material | Shades | Hue shift direction | Specular | Dither OK? | Sub-bevel? |
|---|---|---|---|---|---|
| Skin | 3-4 | Shadow cool, highlight warm | None-small | No | No |
| Metal (polished) | 5-7 | Shadow blue-cool, highlight near-neutral | Yes (sharp 1-2px) | No | Yes |
| Metal (matte) | 3-4 | Same but compressed | None | No | Minimal |
| Wood | 3-4 | Warm throughout | None-trace | No | No |
| Stone | 3-4 | Neutral-cool | None | Yes (rough) | No |
| Water | 4-6 | Cyan-blue ramp | Yes (animated) | Yes | No |
| Fire | 5-6 | Hot=warm, cool at edge | — | No | No |
| Glass/crystal | 3-5 | Tint-neutral, highlights pale | Yes (linear 1px) | No | Yes (facets) |
| Leather | 3-4 | Warm-brown | None/small | No | No |
| Fabric | 3-4 | Minimal hue shift | None | No | No |
