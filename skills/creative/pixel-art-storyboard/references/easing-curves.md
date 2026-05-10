# Easing Curves for Pixel Art

Easing curves shape how a value transitions over time. For continuous motion (3D, vector animation) they're well-understood. For pixel art with **integer pixel grid**, naive easing produces visible "stutter steps."

This file covers easing curves with the integer-quantization issue.

---

## 1. Why linear easing feels wrong for pixel motion

A linear ease moves position by constant velocity. At sub-pixel resolution this is smooth. At pixel resolution it produces visible quantization.

Example: easing a sprite from x=0 to x=8 over 8 frames at linear:

| Frame | Linear t | Ideal x | Pixel x (rounded) |
|---|---|---|---|
| 0 | 0.000 | 0.000 | 0 |
| 1 | 0.143 | 1.143 | 1 |
| 2 | 0.286 | 2.286 | 2 |
| 3 | 0.429 | 3.429 | 3 |
| 4 | 0.571 | 4.571 | 5 |
| 5 | 0.714 | 5.714 | 6 |
| 6 | 0.857 | 6.857 | 7 |
| 7 | 1.000 | 8.000 | 8 |

Notice between frame 3 and frame 4, x jumps by 2 pixels (3 → 5). Between frame 4 and 5 it jumps by 1. The motion is uneven — even though linear t was uniform.

**The fix**: either accept the unevenness as "step easing" (intentional retro feel), OR design 8 specific frame positions and use `step8` easing where each frame snaps to a designed integer.

---

## 2. Common easing functions

| Name | Formula | Shape | Use case |
|---|---|---|---|
| **linear** | `t` | Constant velocity | Mechanical motion (clock hands, conveyor) |
| **easeInQuad** | `t * t` | Slow start, fast end | Falling objects, gravity |
| **easeOutQuad** | `1 - (1-t)²` | Fast start, slow end | Sliding to rest, button hover-out |
| **easeInOutQuad** | `t<0.5 ? 2t² : 1-(-2t+2)²/2` | S-curve, slow at both ends | UI transitions, character pose-to-pose |
| **easeOutBounce** | piecewise quadratic with bounces | Bounces at end | Landing impact, button click feedback |
| **easeOutElastic** | `sin(...)*pow(2,...)` | Overshoots and oscillates | Spring-loaded entry, "boing" feel |
| **step(N)** | `floor(t * N) / N` | Discrete steps at N positions | Pixel-art frame-by-frame, retro animations |

---

## 3. Integer-pixel quantization issue

Two ways to handle the "smooth ease maps to pixel grid" problem.

### Approach A: Accept the stutter (retro / arcade feel)
Round eased value to integer pixel each frame. The result has uneven step sizes but a coherent "ease" feel. This is how Donkey Kong's barrel rolls were done — and it's the canonical retro feel.

```javascript
function easeOutQuadPixel(t) {
  const v = 1 - (1 - t) * (1 - t);
  return Math.round(v * targetPixels);
}
```

### Approach B: Designed step easing (smooth pixel cadence)
Decide N integer positions at design time. Each frame snaps to a designed position. The motion has a deliberate cadence rather than mathematical purity.

```javascript
const positions = [0, 1, 2, 4, 6, 7, 8]; // 7 frames
function step7(t) {
  const idx = Math.min(6, Math.floor(t * 7));
  return positions[idx];
}
```

This is how Celeste's Madeline run cycle works: 4 frames, hand-tuned positions. The cadence carries the feel.

---

## 4. Custom easing for pixel art

### `pixelSnap(easingFn, gridSize)` wrapper

Snap an easing curve's output to a pixel grid:

```javascript
function pixelSnap(easingFn, gridSize) {
  return (t) => Math.round(easingFn(t) * gridSize) / gridSize;
}

// Usage:
const easeOutQuad = (t) => 1 - (1 - t) * (1 - t);
const pixelEaseOutQuad = pixelSnap(easeOutQuad, 8); // 8 discrete pixel positions

const x = startX + pixelEaseOutQuad(phaseT) * (endX - startX);
```

### `bounce` with snap

A spring-bounce that lands cleanly on integer pixels at the boundaries:

```javascript
function easeOutBouncePixel(t, finalPx) {
  const n1 = 7.5625, d1 = 2.75;
  let v;
  if (t < 1 / d1)        v = n1 * t * t;
  else if (t < 2 / d1)   { t -= 1.5 / d1; v = n1 * t * t + 0.75; }
  else if (t < 2.5 / d1) { t -= 2.25 / d1; v = n1 * t * t + 0.9375; }
  else                   { t -= 2.625 / d1; v = n1 * t * t + 0.984375; }
  return Math.round(v * finalPx);
}
```

---

## 5. Code patterns (JavaScript)

### Standard easing functions (from Febucci):
```javascript
function easeIn(t)    { return t * t; }
function easeOut(t)   { return 1 - (1 - t) * (1 - t); }
function easeInOut(t) { return t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2; }
function easeOutBounce(t) {
  const n1 = 7.5625, d1 = 2.75;
  if (t < 1/d1)        return n1 * t * t;
  if (t < 2/d1)        { t -= 1.5/d1;   return n1*t*t + 0.75; }
  if (t < 2.5/d1)      { t -= 2.25/d1;  return n1*t*t + 0.9375; }
                       { t -= 2.625/d1; return n1*t*t + 0.984375; }
}
```

### Step3 (for 3-frame attack: anticipate / strike / recover):
```javascript
function step3(t) {
  if (t < 0.5)  return 0;  // anticipate phase: held still
  if (t < 0.6)  return 1;  // strike: brief
  return 2;                // recover: held longer
}
```

The varying time-per-step is what gives the attack its punch. NOT linear.

### Phase-locked sine (drift-free for loops):
```javascript
function bobLoop(t, amplitude, periodFraction = 1) {
  return amplitude * Math.sin(t * Math.PI * 2 * periodFraction);
}

// In draw function:
const yOffset = bobLoop(t, 2);  // bob ±2 pixels over loop period
const xOffset = bobLoop(t, 1, 2);  // bob ±1 pixel at 2x frequency
```

### Frame timing: anticipation longer than action
The single most important animation principle (Disney's "Illusion of Life" applied to pixel art):

```
Anticipation: 250ms (slow, builds tension)
Strike:       60ms  (1 frame at 60fps; fast)
Recovery:     200ms (eased back, breathes out)
```

NOT 170ms each. **Slowing anticipation + speeding action ≫ adding more frames** ([sprite-ai.art Animation Principles](https://www.sprite-ai.art/guides/animation-principles)).

In a pixel-art-storyboard 3-frame attack template:

```javascript
const attackFrames = [
  { id: 0, duration_ms: 250, name: "anticipation" },
  { id: 1, duration_ms: 60,  name: "strike" },
  { id: 2, duration_ms: 200, name: "recovery" }
];
```

---

## 6. When to skip easing entirely

- **Sub-pixel breathing** — silhouette doesn't move, only AA pixels animate. No easing needed; linear value-shift on AA pixels reads as motion.
- **Hard pixel motion (1-pixel-per-frame)** — already discrete; easing over <8 pixels is moot.
- **Looped ambient** — `sin(t * TAU)` IS the easing. Don't apply easing on top of phase-derived motion; it'll fight itself.
- **Particles** — let position be `f(phase, seed)`. Easing per particle is overkill; phase-locked deterministic field handles smoothness.

Easing matters most for **discrete one-shot motions**: jump, attack, hit reaction, button press feedback. Loops should derive from phase math, not eased state.

---

## 7. Sources

- [Febucci - Easing Functions for Game Animations](https://blog.febucci.com/2018/08/easing-functions/) — canonical reference for easing implementations
- [sprite-ai.art - 12 Animation Principles for Pixel Art](https://www.sprite-ai.art/guides/animation-principles)
- [Slynyrd Pixelblog 8 - Intro to Animation](https://www.slynyrd.com/blog/2018/8/19/pixelblog-8-intro-to-animation)
- [Tweencel Aseprite Extension](https://devkidd.itch.io/tweencel) — easing curves for Aseprite (Linear, Ease In/Out, Bounce, Elastic)
