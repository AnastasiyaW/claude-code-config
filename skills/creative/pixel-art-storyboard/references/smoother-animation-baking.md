# Smoother Animation via Baking

**The trick**: at runtime your animation runs with whatever keyframes you hand-coded (typically 4-8 frames per loop). For archival output (GIF / video), you can **render the same parametric `t`-driven function at any N**, capturing 100-300 frames per loop. The result looks **much smoother** than the live runtime, and costs nothing extra at display time because it's pre-rendered.

This file documents the workflow.

---

## 1. Why baking smoother frames is "free"

Your draw function takes `t ∈ [0, 1)` and renders the appropriate frame. At runtime browsers call it ~60 times per second; the canvas state at each call depends ONLY on `t`. There's no "between-keyframes" interpolation system — every `t` value is independently valid.

So at bake time, you can sample `t` at any density you want:

| Live runtime | Baked output |
|---|---|
| 4-8 hand-coded keyframes | 100-240 frames captured |
| 60fps render → frame drops on busy pages | 30-60fps fixed, no drops |
| Browser quality varies | Pixel-exact reproducible |
| RAF can throttle (hidden tab) | Always exactly N frames captured |
| Animation NEVER ends | Single loop, exactly 1 period |

**The smoother output costs nothing at display time** — it's a static GIF or video file.

---

## 2. Choosing target FPS and frame count

For a `period_ms` loop, baked frame count = `period_ms / 1000 × fps`.

| Loop period | 30fps frames | 60fps frames | Recommendation |
|---|---|---|---|
| 1 second (twitch) | 30 | 60 | 30fps fine |
| 2 seconds | 60 | 120 | 30fps |
| 4 seconds (subject motion) | 120 | 240 | 60fps for premium |
| 8 seconds (slow ambient) | 240 | 480 | 30fps fine — eye won't see 60fps difference at slow speeds |
| 30+ seconds (day cycle) | 900+ | 1800+ | 24fps OK — saves disk |

Trade-off: more frames = larger file. WebM compresses well; GIF is wasteful (no inter-frame compression).

**Rule of thumb**: 30fps is the sweet spot. 60fps only when motion is sub-pixel-fine (orbiting highlights on small subjects benefit; slow petal drift doesn't).

---

## 3. Output format selection

| Format | When to use | Caveats |
|---|---|---|
| **GIF** | Web preview, embed in markdown | ≤ 256 colors per frame, no semi-transparency, large files for many frames |
| **APNG** | Web with full alpha | Less compatible than GIF, larger files |
| **WebM (VP9, yuva420p)** | Video editing, transparent overlays | **Has alpha channel** — best for compositing |
| **MP4 (h264)** | Universal video player, smaller | NO alpha — solid background only |
| **PNG sequence** | Maximum quality, manual editing | Largest disk usage; for after-effects/post-prod |

**For book covers**: GIF for web previews, WebM with alpha for video editor import.
**For game sprites**: PNG sequence for engine import (Unity/Godot/Unreal).
**For social media**: MP4 (everyone can play it).

---

## 4. The bake script (`scripts/bake_animation.py`)

Built on **Playwright (headless Chromium) + ffmpeg**:

1. Open the same HTML page that runs at runtime
2. Override `requestAnimationFrame` with no-op (so we control time, not browser)
3. Wait for engine to load (drawTwilight, drawScene, etc. defined)
4. Loop `i = 0..N-1`, set `t = i/N`, call `drawXxx(ctx, W, H, t)`, capture canvas via `toDataURL`
5. Save each frame as PNG to a temp directory
6. Encode via Pillow (GIF/APNG) or ffmpeg (WebM/MP4)

### Install

```bash
pip install playwright Pillow
playwright install chromium  # one-time
# ffmpeg in PATH (for WebM/MP4)
```

### Usage

```bash
# Bake to GIF (smooth 30fps × 4s = 120 frames)
python scripts/bake_animation.py http://localhost:9132/index-v2.html \
  --canvas-id c1 --period-ms 4000 --fps 30 \
  --format gif -o twilight.gif

# Bake to WebM with alpha (transparent video for compositing)
python scripts/bake_animation.py http://localhost:9132/index-v2.html \
  --canvas-id c1 --period-ms 4000 --fps 30 \
  --format webm-alpha -o twilight.webm

# Bake to PNG sequence (for engine import)
python scripts/bake_animation.py http://localhost:9132/index-v2.html \
  --canvas-id c1 --period-ms 4000 --fps 30 \
  --format png-sequence -o frames/

# Bake to MP4 (no alpha, smaller)
python scripts/bake_animation.py http://localhost:9132/index-v2.html \
  --canvas-id c1 --period-ms 4000 --fps 30 \
  --format mp4 -o twilight.mp4
```

---

## 5. Smoother runtime (alternative to baking)

If you want SMOOTHER animation **at runtime** (not just baked), you have 3 options:

### Option A: Same code, more sub-pixel computation
Already what we do — `t = ((now-start) % period) / period`, position via `sin(t*TAU)`. The math is continuous; browser samples it at 60fps. This IS the smoothest available without baking.

### Option B: Hand-code more keyframes (more `if` branches in draw function)
Diminishing returns. Doesn't help phase-derived animations (those are already smooth in math). Helps for keyframe-based "this position at frame 2, that position at frame 5" structures — convert them to phase-derived.

### Option C: Bake the animation as `<video>` element (don't draw at runtime)
For PRODUCTION delivery, replace `<canvas>` + RAF with `<video autoplay loop muted>` pointing at the baked WebM/MP4. Pros: no JS execution, GPU video decoding, much lower CPU. Cons: file size, no parameter override at runtime (e.g. can't change time-of-day at runtime).

**Production recipe for book covers / album art**:
- Develop with `<canvas>` + RAF (interactive, parameter-tweakable)
- Bake final to WebM with alpha
- Ship as `<video>` element — viewer sees buttery-smooth pre-rendered animation

---

## 6. Quality-vs-size trade-offs

For a 256×384 cover at 30fps × 4s loop = 120 frames:

| Format | Approx file size | Notes |
|---|---|---|
| GIF (256 colors) | 800KB - 2MB | Acceptable for web embed |
| APNG | 1.5 - 4MB | Larger but better quality |
| WebM (VP9, 1Mbps) | 200-500KB | Smallest with full quality, alpha optional |
| MP4 (h264, 1Mbps) | 200-500KB | No alpha but universal compat |
| PNG sequence | 5-15MB total | Editing-grade, never deliver |

WebM consistently wins on size×quality. MP4 wins on compatibility. GIF wins on inline-markdown rendering.

---

## 7. Anti-patterns

- **Bake with RAF still running** — two clocks fight, frames inconsistent. Always override `requestAnimationFrame` to no-op before bake loop
- **Bake too many frames** — 60fps × 60s = 3600 frames is overkill for ambient day-cycle. Eye can't perceive 60fps at slow motion. Use 24-30fps.
- **Use MP4 for transparent video** — won't work. MP4 doesn't support alpha. Use WebM.
- **Skip `pixelated` rendering during bake** — make sure `image-rendering: pixelated` is in CSS so canvas is rendered crisp at viewport scale, not bilinear-blurred
- **Don't validate frame count** — count produced frames vs expected. If browser closed early or some frames failed, output will be jerky.

---

## 8. Sources

- Playwright Python docs: https://playwright.dev/python/
- ffmpeg WebM with alpha: https://trac.ffmpeg.org/wiki/Encode/VP9#Transparency
- HTMLCanvasElement.toDataURL: https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toDataURL
- Canvas image-rendering: pixelated: https://developer.mozilla.org/en-US/docs/Web/CSS/image-rendering
