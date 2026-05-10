# Retouch-Style Production Standard

**Authoritative reference**: `Grass Field with City.html` and `Elements Sheet.html` (user-provided).
This style guide formalizes the production-grade pixel-art aesthetic these reference files demonstrate.

The retouch-style is **multi-layer scene composition** with **pre-generated geometry**, **palette interpolation per phase**, and **multi-component motion**. It is one large step beyond simple "icon on background" composition.

---

## 1. Style fingerprint (visual)

A retouch-style cover or scene **always has** the following layered structure:

| Layer | Density | Purpose |
|---|---|---|
| 1. **Sky gradient** | full canvas, multi-stop | Atmospheric base, time-of-day signal |
| 2. **Atmospheric particles** | 50-300 fine pixels | Stars (night), dust motes (sun beam), snow, rain |
| 3. **Far depth** | silhouettes 8-16px tall | City skyline, mountain ridge, tree line |
| 4. **Mid depth** | 16-32px elements | Specific landmarks (tower, lighthouse), mid-ground forms |
| 5. **Near foreground** | 16-48px elements | Grass, fence, water surface |
| 6. **Subject** | 16-48px central element | The icon: character, vehicle, creature, symbolic object |
| 7. **Foreground motion** | 5-20 elements | Fireflies, falling petals, flying birds, drifting embers |
| 8. **Atmospheric overlay** | full canvas | Vignette, fog tint, dawn/dusk color pass |

**Twilight covers (current)** use only 1 + 2 + 6 + 7. Adding layers 3-5 + 8 closes the gap.

---

## 2. Palette structure

A retouch-style scene uses **3 palette tiers**:

### Tier A: Sky/atmospheric (5-7 colors)
Multi-stop gradient interpolated by time-of-day phase.

```javascript
const SKY_KEYS = [
  // [phase, top, mid, horizon]
  [0.00, '#0a0814', '#1a0e1c', '#2a1a30'],   // midnight
  [0.20, '#2a1a30', '#5a2a3a', '#a86060'],   // dawn
  [0.50, '#a8c8e8', '#d8e8f0', '#f0d8a0'],   // noon
  [0.75, '#f0a060', '#a86040', '#5a3030'],   // sunset
  [1.00, '#0a0814', '#1a0e1c', '#2a1a30'],   // back to midnight
];
```

### Tier B: Subject palette (4-6 colors per object)
Each object has its own ramp with hue-shift:
```
shadow → mid-shadow → base → highlight → spec-highlight
hue 350°  hue 0°       hue 25°  hue 50°    hue 60°
```

### Tier C: Accent (1-2 colors)
The single warm pixel in a cold scene (Rudolph's nose, lamp glow, firefly) OR vice versa. **Always** use exactly 1-2 accents per scene — more dilutes the focus.

---

## 3. Geometry pre-generation (mandatory)

Random elements (stars, grass blades, clouds, particles) **must** be generated **once** with a deterministic seed at scene init time, NOT recomputed per frame.

### Stars (230 stars in Grass Field)

```javascript
const STARS = [];
(function initStars(){
  seed(41);  // deterministic
  for (let i = 0; i < 230; i++) {
    STARS.push({
      x: (rnd() * W) | 0,
      y: (rnd() * 105) | 0,    // sky region only
      b: rnd(),                  // brightness 0-1
      tw: rnd() * 6.28,          // twinkle phase offset
    });
  }
})();
```

Per-frame:
- Brightest (b > 0.93) → 1 center pixel + 4 dim cross-plus pixels
- Medium (0.6 < b < 0.93) → 1 pixel
- Dim (b < 0.6) → 1 pixel at lower opacity
- Twinkle: `0.7 + 0.3 * Math.sin(timeSec * 2 + tw)` per-star phase

### Grass (4 layers with depth)

```javascript
const GRASS = { far: [], mid: [], near: [], bottom: [] };
// Each layer has different blade count, height range, color tier, sway amplitude
// Far: amp 0.4, blade height 2-4px
// Mid: amp 1.2, blade height 4-8px
// Near: amp 2.2, blade height 6-12px
// Bottom: amp 2.8, blade height 8-16px
```

### Clouds, mountains, city silhouettes
Same pattern: pre-generate shapes (chunky pixel puffs, mountain triangles, skyscraper rectangles) with seeded RNG, then animate position via offset.

---

## 4. Multi-component motion

Single sin-wave is too simple for organic motion. Use **2-4 component sum**:

```javascript
function windAt(x, phase, amp) {
  const travel = Math.sin((x * 0.03) - timeSec * 1.8 * ws + phase);  // wave traveling along x
  const local  = Math.sin(timeSec * 2.3 * ws + phase * 0.7);          // local oscillation
  return (travel * 0.7 + local * 0.3 + windBase * 0.3 + gust * 0.6) * amp;
}
```

Components:
- **Travel wave**: depends on position (`x`), simulates wind moving along
- **Local oscillation**: per-element jitter
- **Base wind**: scene-level slow drift
- **Gust**: occasional stronger pulse (controlled separately)

**Why this works**: human eye reads natural motion as multi-frequency. A single sin looks mechanical. Two sins offset by phase look organic.

---

## 5. Surface detail per object

Every subject ≥ 16px must have **interior detail**, not just silhouette + flat fill.

### Moon (radius 14px example)

```javascript
const R = 14;
function moonDot(dx, dy, c) { if (dx*dx + dy*dy <= R*R) px(mx+dx, my+dy, c); }

// Base sphere (3-step luminance ramp)
for (dy=-R; dy<=R; dy++) for (dx=-R; dx<=R; dx++) {
  const d = dx*dx + dy*dy;
  if (d <= R*R) {
    let color = baseColor;
    if (d <= (R-1)*(R-1)) color = midColor;
    if (d <= (R-3)*(R-3)) color = highlight;
    if (d <= (R-5)*(R-5)) color = specHighlight;
    moonDot(dx, dy, color);
  }
}

// Surface craters: 3-5 darker dots at deterministic positions
const craters = [[-4,-2,2], [3,1,1], [-1,5,2], [5,-4,1]];  // [dx, dy, radius]
craters.forEach(([dx, dy, r]) => fillCircle(mx+dx, my+dy, r, craterColor));

// Halo: soft alpha glow extending 4-6px beyond
for (dr=1; dr<=4; dr++) {
  const a = 0.15 * (1 - dr/5);
  drawRingSoft(mx, my, R+dr, `rgba(255,240,200,${a})`);
}
```

### Grass blade (height 8px example)

```javascript
// 3 colors per blade: tip / hi / mid
const tipC = '#a0d068';   // brightest
const hiC  = '#7ab050';
const midC = '#3a7028';   // base, darkest

for (let k = 0; k < blade.h; k++) {
  const bend = Math.round(windSway * (k / blade.h));  // bends more at top
  const xx = blade.x + bend + lean;
  const c = (k === blade.h - 1) ? tipC : (k > blade.h * 0.5 ? hiC : midC);
  px(xx, blade.y - k, c);
}
```

The 3-color blade is what makes grass "shimmer" rather than look flat.

---

## 6. Day/night phase system

Scene parameter `T ∈ [0, 1]` drives **all** color choices via `interpKey(SKY_KEYS, T)`. No hardcoded colors per frame — colors come from interpolation.

```javascript
function nightFactor(T) {
  // 0 at noon, 1 at midnight, smooth transition
  const dist = Math.min(T, 1 - T);
  return 1 - smoothstep(0.0, 0.35, dist);
}

function phaseName(T) {
  if (T < 0.05 || T > 0.95) return 'midnight';
  if (T < 0.20) return 'dawn';
  if (T < 0.45) return 'morning';
  if (T < 0.55) return 'noon';
  if (T < 0.75) return 'afternoon';
  return 'sunset';
}
```

Stars only render when `nightFactor > 0.08`. Sun only renders when `nightFactor < 0.7`. Moon visibility independent (some configs show moon during day too).

---

## 7. Atmospheric overlay (final pass)

After all layers drawn, **single full-canvas overlay** to unify atmosphere:

```javascript
function atmosphereOverlay(T) {
  const fogStrength = (T < 0.2 || T > 0.8) ? 0.15 : 0.05;
  const fogColor = phaseName(T) === 'dawn' ? '#ff806080'
                 : phaseName(T) === 'sunset' ? '#fa6040c0'
                 : '#0a061880';
  ctx.fillStyle = fogColor + Math.round(fogStrength*255).toString(16);
  ctx.fillRect(0, 0, W, H);
}
```

This is what unifies the "feel" of a scene. Without it, layers look pasted-together.

---

## 8. Quantitative density thresholds (retouch standard)

For a 64×96 (book cover) or 192×72 (banner) canvas, these are the **minimum** counts for retouch-style:

| Element | Minimum count | Where |
|---|---|---|
| Atmospheric particles (stars/dust/etc) | 50 | Sky region |
| Subject palette | 4-6 colors | Subject body |
| Subject surface detail dots | 3-8 | On object surface |
| Background depth layers | 2 (silhouette + ground) | Below subject |
| Foreground motion elements | 3-5 | Falling/drifting things |
| Distinct loop motion components | 3 | (e.g. subject sway + particles + atmosphere shift) |
| Total unique colors | 12-20 | Whole scene |

A scene with fewer than these counts feels "sparse" — not retouch-style.

---

## 9. Negative checklist (avoid)

- ❌ **Solid bg + 1 icon** (Twilight v1 style) — feels like a flat sticker, not a scene
- ❌ **All sin-wave with same period** — mechanical, not organic
- ❌ **Math.random() in render path** — non-deterministic, doesn't loop
- ❌ **No surface detail on subject** — flat colored shape lacks weight
- ❌ **Single color ramp per object (no hue shift)** — muddy, dull
- ❌ **Same accent color as subject** — kills the chromatic anchor
- ❌ **Particles all moving same direction at same speed** — robotic
- ❌ **Animation isolated to subject only** — atmosphere should also breathe

---

## 10. Validation checklist (retouch-pass criteria)

A scene meets retouch-quality if all 10 checks pass:

1. ✓ Sky gradient interpolated, NOT solid
2. ✓ At least 50 atmospheric particles (stars/dust/snow/rain)
3. ✓ At least 2 background depth layers (silhouettes + ground/water)
4. ✓ Subject has 4-6 color ramp WITH hue rotation ≥ 30°
5. ✓ Subject has interior detail (3-8 surface dots/lines)
6. ✓ Exactly 1-2 accent-color elements (warm in cold scene or vice versa)
7. ✓ Motion has ≥ 3 components (subject + particles + atmosphere)
8. ✓ Pre-generated geometry uses seeded RNG (not Math.random)
9. ✓ Loop seamless: position derived from `(now/period) % 1`
10. ✓ Atmospheric overlay tints whole scene by phase

Score: 8-10 = ship; 5-7 = improve; <5 = redesign.

---

## 11. Style anchor parameters (retouch palette + typography)

When user invokes "retouch-style" or "production-grade pixel art", these are the defaults:

```css
--bg: #0b0812;                  /* near-black with violet undertone */
--panel: #110c1a;               /* card backgrounds */
--fg: #a896b4;                  /* lavender-grey foreground text */
--dim: #5a4e6a;                 /* dimmer text */
--accent: #ffb4c8;              /* pale pink accent */
--border: rgba(255,255,255,.06); /* barely-visible border */
font-family: "JetBrains Mono", ui-monospace, Menlo, monospace;
letter-spacing: .25-.35em;       /* generous spacing on titles */
text-transform: uppercase;       /* on accent labels */
```

Cover dimensions canonical: **64×96 logical** (book aspect 2:3), scaled 4× via `image-rendering: pixelated`. Banner: **192×72 logical**. Square: **96×96 logical**.

---

## 12. Sources

- **Grass Field with City** (canonical reference) — single self-contained HTML, 3700+ lines, 100 functions, 8-layer scene with day/night phase, 230 stars, 4 grass layers, city silhouette, fireflies
- **Elements Sheet** (variation board) — 16 elements × 3-8 variants each (moon / tractor / UFO / cow / fireworks / wind / butterflies / bumblebees / clouds / witch / Santa / grass / landscapes / dinosaurs / dragonflies). Production review UI for art direction sign-off
- **Preview Grid** (production review UI) — seasons × times of day × moon phases parametrized iframe grid for variant comparison

These three files together demonstrate: (a) the rendering technique, (b) the variety standard, (c) the production review UI.
