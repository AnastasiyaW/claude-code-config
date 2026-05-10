# Looped Animation Techniques

The "seam" is the moment frame N loops back to frame 0. If the two differ by one pixel, the eye sees a snap. This file covers every technique to eliminate the seam.

---

## 1. Why seams happen

Three causes:
- **State accumulation**: `pos += velocity * dt` builds float drift over time. Position at t=0 is no longer position at t=N*period.
- **Stochastic spawning**: `Math.random()` at frame K differs from frame K+period. Particles look different across cycles.
- **Frame-N != frame-0**: even hand-drawn animations sometimes forget the cycle-closure rule.

The single most important rule (from [Book of Shaders Ch. 5](https://thebookofshaders.com/05/) and [shadergif.com Perfect Loops](https://shadergif.com/guides/how-to-make-a-perfect-loop/)):

> **Never accumulate position. Always derive position from `phase = fract(time / period)`.**

```javascript
// CORRECT — drift-free, seamless by construction
const t = ((now - start) % period) / period;
const yOffset = Math.sin(t * Math.PI * 2) * amplitude;

// WRONG — accumulates float error, may seam visibly after hours
let pos = 0;
function frame(dt) { pos += velocity * dt; render(pos); }
```

---

## 2. Frame-matching techniques

| Technique | How it works | Best for | Source |
|---|---|---|---|
| **First==Last frame** | Design frame N visually identical to frame 0; export skips duplicate | Walk cycles, blink loops, breathing | Pedro Medeiros / Lospec |
| **Half-cycle ping-pong** | Animate forward to midpoint only, play in reverse on return; Aseprite tag direction `pingpong` | Symmetrical motion (idle sway, breathing, swinging lantern) | [Aseprite Tag docs](https://www.aseprite.org/docs/tags/) |
| **Phase-based parametric** | Position = `sin(t·2π)` — by definition returns to same value at t=1 | Hovering, water bob, lantern flicker, eye glow | shadergif.com |
| **Phase wrap `t = (now/period) % 1`** | Time progresses, parameter wraps cleanly to 0 every `period` seconds | Programmatic loops, drift-free over hours | The Book of Shaders |

**Aseprite gotcha**: ping-pong export to GIF must set tag direction explicitly to `pingpong`. Default `forward` will play forward-only (loses the reverse half).

---

## 3. Sub-pixel breathing

The technique with the highest impact-per-effort for ambient pixel art. From [2D Will Never Die](https://2dwillneverdie.com/tutorial/give-your-sprites-depth-with-sub-pixel-animation/):

> "To move a small sprite a small distance, don't move the sprite — move its colors."

The silhouette stays pixel-locked. What changes is **interior shading** — AA halftone pixels between light and shadow regions. Metal Slug is the canonical example.

**Why it works**: human luminance perception operates at finer resolution than positional perception. A 1px vertical bob looks like a *jump*; a luminance shift of 5-15% on a single AA pixel reads as motion smaller than a pixel.

**4-frame breathe loop recipe** (12 fps):

| Frame | Torso highlight | Torso midtone | Edge AA pixel |
|---|---|---|---|
| 0 (inhale start) | base | base | base |
| 1 (peak inhale) | +1 row, lighter | wider | softer halftone (lighter) |
| 2 (hold) | same as 1 | same | same |
| 3 (exhale) | base, fade | shrinks | base |

Loop returns to frame 0. No silhouette pixel moves; only the interior color values cycle. Slynyrd calls this the "bouncy breathing variety" idle ([Pixelblog 8](https://www.slynyrd.com/blog/2018/8/19/pixelblog-8-intro-to-animation)).

**When to apply**: any sprite ≥ 32px tall, at idle. Below 32px there usually aren't enough AA pixels to animate.

---

## 4. Parallax LCM principle

Authoritative source: [Slynyrd Pixelblog 23 - Parallax Scrolling](https://www.slynyrd.com/blog/2019/11/12/pixelblog-23-parallax-scrolling).

> "Any constant looping animation that is added to the parallax must loop in a number of frames that divides into the total number of frames."

Pick canvas widths with many divisors (96, 120, 144, 192, 240) so scroll rates of {1, 2, 3, 4, 6, 8, 12} all complete integer cycles in one canvas-width.

**Worked example (96px canvas, 96-frame loop)**:

| Layer | Scroll rate (px/frame) | Repeats in 96 frames | Image width needed |
|---|---|---|---|
| Sky / stars | 1 | 1 | 96px |
| Mountains | 2 | 2 | 48px |
| Mid hills | 3 | 3 | 32px |
| Trees | 4 | 4 | 24px |
| Foreground grass | 8 | 8 | 12px |

After 96 frames every layer has returned to its starting position simultaneously — the loop is mathematically clean.

A 4-frame car animation also fits because 4 divides 96. A 5-frame flag would NOT fit and would visibly drift over multiple cycles.

**Common-period rule**: when combining multiple animation elements, choose periods on a common LCM. Periods 2s and 3s have LCM 6s, so a 6-second composite period contains exactly 3 cycles of A and 2 cycles of B with no drift.

---

## 5. Particle loop architectures

Two viable architectures, each with a different determinism property.

### Architecture A: Spawn-die wraparound (constant density)

- Each particle has `birth_time`, `lifetime`, `velocity`
- At time t, particles where `(t - birth_time) > lifetime` respawn at the opposite edge
- Spawn rate must equal die rate (e.g., 60 particles, lifetime 4s → spawn 15/s)
- Loop period = lifetime → identical state at t=0 and t=lifetime

**Best for**: real-time game engines (Unity ParticleSystem) where simulation forward-step is acceptable.

### Architecture B: Phase-locked deterministic field (recommended for pixel art)

- For N particles, position = `f(phase, seed[i])` where `phase = (t/period) % 1`
- Each particle's trajectory is closed: ends where it started after one period
- Same input always produces same output
- **No state**, pure function of phase + seed

**Best for**: pixel art with seamless GIF export, regression-tested rendering, server-side rendering. Fireflies pattern:

```javascript
function fireflyPosition(i, phase) {
  const orbit_x = 30 + 4 * Math.sin(phase * Math.PI * 2 + i * 1.7);
  const orbit_y = 20 + 3 * Math.cos(phase * Math.PI * 2 + i * 2.3);
  return [orbit_x, orbit_y];
}
```

This is what shadergif's "Perfect GLSL Loops" guide recommends.

---

## 6. Palette interpolation (day/night cycles)

Drive palette via `t ∈ [0,1]`, key-frame interpolation between named palettes.

| Phase t | Hour | Palette anchor |
|---|---|---|
| 0.00 | midnight | deep blue, near-black, cool moon highlights |
| 0.25 | sunrise (06:00) | warm peach, soft pink, rose horizon |
| 0.50 | noon | bright sky, saturated subjects, white highlights |
| 0.75 | sunset (18:00) | amber, magenta, orange |
| 1.00 | midnight (= 0.00) | identical to t=0 |

**Linear lerp** is fine for palette ceiling 8-16 because perceptual quantization dominates. **Cubic ease** is more cinematic but more compute.

```javascript
function dayNightColor(t, anchorColors) {
  // anchorColors = [c_midnight, c_sunrise, c_noon, c_sunset, c_midnight]
  const idx = Math.floor(t * 4);
  const localT = (t * 4) - idx;
  return mix(anchorColors[idx], anchorColors[idx + 1], localT);
}
```

Source: [Stephen Schroeder Color Cycling Pixel Art Unity](https://thedeivore.medium.com/color-cycling-in-pixel-art-2-unity-233d31b2be8e).

---

## 7. Loop period selection

| Loop length | Feels like | Use for |
|---|---|---|
| 0.5-1s | Twitch / nervous | Eye blink, single hop, attack tells |
| 2-3s | "Alive" without being noticed | Idle breathe, water lap, candle flicker |
| 4-6s | Subtle motion | Breathing, slow drift, ribbon flutter |
| 8-15s | Atmospheric breathing room | Petal fall, smoke plumes, drifting clouds |
| 30-60s | Slow atmospheric | Wave breaks, far birds, distant thunder |
| 60s+ | Day-cycle ambient | Time-of-day, season change |

**Selection heuristic**: if the loop period < user's typical viewing duration ÷ 4, viewer will notice the cycle. For book covers shown for 5-30 seconds, periods of 4-10s are right; for ambient backgrounds shown for hours, prefer 60s+ with multiple sub-loops.

---

## 8. Common pitfalls

| Pitfall | Cause | Mitigation |
|---|---|---|
| Visible seam | Frame N and frame 0 differ by ≥1 pixel | First==last frame OR phase-based wrap |
| Beat de-sync | Layer A loops at 2s, layer B at 3s | Choose periods on common LCM (6s) OR phase-locked |
| Float drift | `pos += vel * dt` accumulates error over hours | Always derive from `phase = fract(t/period)` |
| GIF drops a frame | Aseprite ping-pong export defaults to forward | Set tag direction explicitly to `pingpong` |
| Random particles non-determ | `Math.random()` instead of seeded RNG | Use `f(phase, seed[i])` |
| Camera snap | Camera follows character whose position resets | Camera should also derive from `phase`, not accumulate |

---

## 9. Code patterns

### Correct (phase-derived, drift-free)

```javascript
function startCanvas(canvas, drawFn, periodMs) {
  const ctx = canvas.getContext('2d');
  const start = performance.now();
  function frame(now) {
    const t = ((now - start) % periodMs) / periodMs;
    drawFn(ctx, t);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

function drawScene(ctx, t) {
  // Everything derives from t
  const wave = Math.sin(t * Math.PI * 2);
  const bobY = 8 + wave * 2;
  const sunPhase = (t + 0.25) % 1; // offset so sunrise at t=0
  // ...
}
```

### Wrong (state accumulating)

```javascript
let pos = 0;
function frame(dt) {
  pos += 0.5 * dt;          // drift accumulates
  if (pos > 100) pos = 0;   // snap visible at threshold
  render(pos);
}
```

### Deterministic particle loop (pure function of phase)

```javascript
function hash(n) {
  const x = Math.sin(n * 12.9898) * 43758.5453;
  return x - Math.floor(x);
}

function drawFireflies(ctx, t, count = 8) {
  for (let i = 0; i < count; i++) {
    // Each firefly orbits a unique offset point with unique radius
    const cx = 32 + (hash(i) - 0.5) * 40;
    const cy = 48 + (hash(i + 100) - 0.5) * 30;
    const rx = 4 + hash(i + 200) * 6;
    const ry = 3 + hash(i + 300) * 4;
    // Phase offset per firefly so they don't sync
    const phase = (t + hash(i + 400)) * Math.PI * 2;
    const x = cx + Math.cos(phase) * rx;
    const y = cy + Math.sin(phase * 1.3) * ry;
    px(ctx, x, y, '#ffd070');
  }
}
```

This pattern is canonically seamless: at t=0 and t=1, every firefly is at the same position because `Math.cos(0)` == `Math.cos(2π)`.
