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

| Format | Size (4s @ 30fps) | Alpha | Embed as | Best for |
|---|---|---|---|---|
| **WebP animated** ⭐ | ~150-400 KB | full | `<img>` | **Web pages, Markdown, docs (DEFAULT for web)** |
| **GIF** | ~1-2 MB | 1-bit | `<img>` | Email, Telegram, WhatsApp, chat clients |
| **APNG** | ~1.5-4 MB | full | `<img>` | Alternative to GIF with full alpha |
| **WebM (VP9, yuva420p)** | ~200-500 KB | full | `<video>` (tag required) | Hero animations, full-screen video, compositing |
| **MP4 (h264)** | ~200-500 KB | NONE | `<video>` | Universal video player; NO alpha |
| **PNG sequence** | 5-15 MB total | full | filesystem | Game engine import (Unity/Godot/Unreal), post-prod |

### Decision tree

- **Embedding on a website / in Markdown / docs** → `--format web` (animated WebP)
  - Smallest file, full alpha, embeds as `<img>`. Modern browsers (96%+).
- **Sharing in email / Telegram / chat** → `--format gif`
  - Universal compat. Larger files, only 1-bit alpha.
- **Hero animation / fullscreen video** → `--format webm-alpha`
  - Smallest with alpha but requires `<video>` element.
- **Universal video (no alpha)** → `--format mp4`
  - Plays everywhere. Solid background only.
- **Game engine import** → `--format png-sequence`
  - Maximum quality, lossless, animation-engine controls timing.
- **Archival with full alpha** → `--format apng`
  - Pillow-native, no ffmpeg needed.

**Default is `--format web` (animated WebP)** because that's what most output is for. Override only when you have a specific target (chat embed → gif, video editor → webm-alpha).

### WebP quality tuning

For `--format web` / `--format webp`:
- Default: lossy q=80 (barely visible difference on pixel art, ~5x smaller than lossless)
- `--lossless` for pixel-perfect (use when distributing the canonical asset)
- `--quality 90` for higher fidelity if compression artifacts visible

For pixel art specifically, lossy q=80 is usually fine — pixel boundaries are sharp anyway and the JPEG-style chroma subsampling artifacts that ruin photographs are barely visible on flat-fill regions.

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
# RECOMMENDED for web: animated WebP (default)
python scripts/bake_animation.py http://localhost:9132/index-v2.html \
  --canvas-id c1 --period-ms 4000 --fps 30 \
  --format web -o twilight.webp
# (or --format webp, same thing)

# WebP lossless if you need pixel-perfect
python scripts/bake_animation.py http://localhost:9132/index-v2.html \
  --canvas-id c1 --period-ms 4000 --fps 30 \
  --format web --lossless -o twilight.webp

# GIF for email / Telegram / chat embeds
python scripts/bake_animation.py http://localhost:9132/index-v2.html \
  --canvas-id c1 --period-ms 4000 --fps 30 \
  --format gif -o twilight.gif

# WebM with alpha for video editor import
python scripts/bake_animation.py http://localhost:9132/index-v2.html \
  --canvas-id c1 --period-ms 4000 --fps 30 \
  --format webm-alpha -o twilight.webm

# PNG sequence for game engine import
python scripts/bake_animation.py http://localhost:9132/index-v2.html \
  --canvas-id c1 --period-ms 4000 --fps 30 \
  --format png-sequence -o frames/

# MP4 universal video (no alpha)
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
