# High-Detail Pixel Art Pipeline (Tier 3)

For book covers at the quality level of professional artists (Saint11, Slynyrd, Brandon James Greer) or high-quality AI-generated reference images at 480-720 pixel grids with atmospheric perspective, volumetric lighting, and fine textures.

This is **Tier 3** of our pipeline — the highest detail level. Tier 1 (64×96 hand-coded) is for prototyping; Tier 2 (192×288 hand-coded) for medium detail; Tier 3 (this) for production-grade output matching professional references.

---

## 1. Why Tier 3 needs a different approach

Hand-coding a 480×720 pixel scene = **345,600 pixels** to decide individually. Even with 20-layer composition logic, that's hundreds of lines per scene element. A single such cover would take 50-100 hours hand-drawn.

The reference quality we want has:
- Atmospheric perspective (distant mountains fade to blue-grey haze)
- Volumetric lighting (glow halos around all light sources, soft fog)
- Multi-temperature lights (warm window orange + cool sky blue mixed naturally)
- Fine textures (individual pine needles, brick walls, snow patterns, ridge lines)
- 50+ color palette with smooth gradient transitions
- Subtle particle work (snow drifting at varying densities, dust motes in light)

**No human can hand-code this density at production speed**. Professional pixel artists spend 40-80 hours per such piece. AI-assisted pipelines reduce this to 30-60 minutes per cover with similar quality.

---

## 2. Tier 3 architecture: AI base + canvas animation overlay

```
┌──────────────────────────────────────────────────────────────┐
│  Stage 1: AI generation (Stable Diffusion + Pixel Art LoRA)  │
│  Input:   2-paragraph scenario + style anchor tokens         │
│  Output:  768×1024 PNG with atmospheric pixel-art aesthetic  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  Stage 2: Pixel snap + palette enforcement                   │
│  Input:   AI output PNG (often has fractional pixels)        │
│  Steps:   1. NEAREST downsample to 192×288 (logical grid)    │
│           2. LIBIMAGEQUANT quantize to 64-color palette      │
│           3. Atkinson dither for gradient regions            │
│           4. Optional: rembg for background isolation        │
│  Output:  Real pixel art PNG with strict palette discipline  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  Stage 3: Manual cleanup (optional)                          │
│  In Aseprite or via quality_check.py:                        │
│  - Fix orphan pixels                                         │
│  - Eliminate doublies                                        │
│  - Tighten silhouette boundaries                             │
│  Output:  Production-grade static PNG                        │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  Stage 4: Canvas animation overlay                           │
│  Static PNG = background <img>                               │
│  Canvas overlay (transparent):                               │
│  - Snow particles (deterministic, seeded)                    │
│  - Window light flickers (per-pixel intensity modulation)    │
│  - Fog parallax (moving cloud layer)                         │
│  - Ember drift                                               │
│  Output:  Composite HTML with animated WebP bake potential   │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  Stage 5: Bake to WebP/MP4/WebM                              │
│  Use bake_animation.py with --base-image flag                │
│  Composite base PNG + animated canvas at each frame          │
│  Output:  Final animated WebP at quality 80, ~500-1500 KB    │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Stage 1: AI generation — recommended pipelines

### A) SDXL + Pixel Art XL LoRA (free, programmatic via diffusers)

```python
# pip install diffusers transformers accelerate torch
from diffusers import StableDiffusionXLPipeline, LCMScheduler
from diffusers.utils import load_image
import torch

# Load SDXL base + Pixel Art LoRA
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16
).to("cuda")

# Pixel Art XL LoRA (nerijs)
pipe.load_lora_weights("nerijs/pixel-art-xl", weight_name="pixel-art-xl.safetensors")
# LCM LoRA for 8-step generation
pipe.load_lora_weights("latent-consistency/lcm-lora-sdxl", adapter_name="lcm")
pipe.set_adapters(["default", "lcm"], adapter_weights=[1.2, 1.0])
pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)

prompt = """pixel art, 16-bit style, atmospheric, snowy mountain fortress at dusk,
stone tower on cliff, pine trees in foreground, distant mountain ridges fading to blue,
soft fog, scattered window lights, warm amber glow, cool blue sky with subtle gradient,
detailed pixel grid, painterly atmospheric perspective, masterful composition"""

negative = """blurry, photorealistic, smooth gradients, antialiased,
3d render, no pixel discipline, washed out colors, generic"""

image = pipe(
    prompt=prompt,
    negative_prompt=negative,
    width=1024,
    height=1536,
    num_inference_steps=8,
    guidance_scale=1.5,
    cross_attention_kwargs={"scale": 1.2}
).images[0]

image.save("cover_raw.png")
```

**Recommended params** (per nerijs/pixel-art-xl HuggingFace docs):
- LCM LoRA strength: 1.0
- Pixel Art XL LoRA strength: 1.2
- Steps: 8 (LCM)
- CFG: 1.5
- Resolution: 1024×1536 for book covers (2:3 aspect)

### B) FLUX-based LoRAs (newer, often higher quality)

Newer FLUX-based pixel-art LoRAs (e.g. on Civitai or HuggingFace) often produce more atmospheric results than SDXL-based ones. Search Civitai with tag `flux pixel art` and `atmospheric`.

### C) RetroDiffusion REST API (commercial, true pixel-art model)

```python
# pip install requests
import requests, base64

def retrodiffusion_generate(prompt: str, api_key: str,
                             width: int = 192, height: int = 288) -> bytes:
    response = requests.post(
        "https://api.retrodiffusion.ai/v1/inferences",
        headers={"X-RD-Token": api_key},
        json={
            "model": "RD_FLUX",
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_images": 1,
        }
    )
    response.raise_for_status()
    data = response.json()
    return base64.b64decode(data["base64_images"][0])

png_bytes = retrodiffusion_generate("snowy fortress in alpine mountains at dusk", "YOUR_KEY")
with open("cover_rd.png", "wb") as f: f.write(png_bytes)
```

50 free credits at registration; ~$0.02 per cover after. **True pixel art model** (not SD-adapted) — outputs are already on-grid, no fractional pixels. **Recommended over SDXL for production** if budget allows.

### D) MidJourney v6+ + post-process (manual, but high quality)

If using MidJourney via Discord:

```
/imagine pixel art, atmospheric snowy fortress on cliff, pine trees,
distant mountains in fog, 16-bit JRPG style, detailed pixel discipline,
volumetric lighting, masterpiece --ar 2:3 --v 6 --stylize 250
```

Output is at 1024×1536 typically. Then run through Stage 2 quantization.

MJ has no public API; manual generation only. Use SDXL or RetroDiffusion for batch automation.

---

## 4. Stage 2: Pixel snap + palette enforcement

After AI generation, output is "pixel-art-looking" but rarely on a true pixel grid. Enforce via our pipeline:

```python
# Use existing scripts/preprocess.py
import subprocess

subprocess.run([
    "python", "scripts/preprocess.py",
    "cover_raw.png",
    "--target-size", "192x288",          # logical pixel grid
    "--palette", "design-seeds/heavenly-hues",  # OR --colors 64 for auto-extract
    "--dither", "atkinson",              # smooth gradient dithering
    "--downsample", "nearest",           # pixel-perfect snap
    "--pre-lanczos", "1.5",              # gentle pre-blur for noise reduction
    "-o", "cover_snapped.png"
])
```

**Critical**: NEAREST downsample only. Bilinear/lanczos at this stage = blurry pixel art.

---

## 5. Stage 3: Manual cleanup (optional but recommended)

Open the snapped output in Aseprite or any pixel editor. Run our `quality_check.py`:

```bash
python scripts/quality_check.py cover_snapped.png --verbose
```

Look for:
- `orphan_count > 5%` → manual cleanup
- `doublies_count > 2` → fix parallel lines
- `pillow_shading.detected` → reshade with explicit light source
- Banding bands → adjust palette ramps

Use the **pixel-art-quality-board** orchestrator for comprehensive review:
```
@pixel-art-quality-board "Review cover_snapped.png against retouch-style"
```

---

## 6. Stage 4: Canvas animation overlay

Static AI-generated PNG goes as `<img>` background. Animation only for elements that benefit from motion:

```html
<!DOCTYPE html>
<html>
<head><style>
  .stage { position: relative; width: 384px; height: 576px; }
  .stage img, .stage canvas {
    position: absolute; left: 0; top: 0;
    width: 100%; height: 100%;
    image-rendering: pixelated;
  }
  .stage img { z-index: 1; }       /* AI base */
  .stage canvas { z-index: 2; }    /* animation overlay */
</style></head>
<body>
<div class="stage">
  <img src="cover_snapped.png">    <!-- AI base, pre-rendered -->
  <canvas id="overlay" width="192" height="288"></canvas>  <!-- animation -->
</div>
<script>
// Overlay only renders motion: snow particles, window flicker, fog drift
const cv = document.getElementById('overlay');
const ctx = cv.getContext('2d');
const PERIOD = 8000;
const start = performance.now();
function frame(now) {
  const t = ((now - start) % PERIOD) / PERIOD;
  ctx.clearRect(0, 0, 192, 288);
  // Snow particles (deterministic, seeded)
  for (let i = 0; i < 25; i++) {
    const seed = i * 17 + 3;
    const sx = (Math.sin(seed * 12.9898) * 43758.5453 % 1) * 192;
    const sy = ((t + Math.sin(seed * 78.233) * 43758.5453 % 1) % 1) * 288;
    ctx.fillStyle = 'rgba(220,230,240,0.7)';
    ctx.fillRect(sx | 0, sy | 0, 1, 1);
  }
  // Window flicker (modulate alpha of specific window pixel positions)
  const windows = [[140, 60], [142, 65], [148, 70]];
  for (const [wx, wy] of windows) {
    const flicker = 0.8 + 0.2 * Math.sin(t * Math.PI * 8 + wx);
    ctx.fillStyle = `rgba(255,180,80,${flicker * 0.4})`;
    ctx.fillRect(wx, wy, 2, 2);
  }
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script>
</body>
</html>
```

The static PNG carries the heavy detail; canvas only animates ~25-50 pixels per frame. **CPU usage stays low** even on mobile.

---

## 7. Stage 5: Bake composite to WebP

Extended `bake_animation.py` supports `--base-image` flag:

```bash
python scripts/bake_animation.py http://localhost:9132/composite-cover.html \
  --canvas-id overlay \
  --base-image cover_snapped.png \
  --period-ms 8000 --fps 30 \
  --format web -o cover_final.webp
```

This composites the static PNG underneath canvas overlay at each captured frame, producing the final animated WebP.

---

## 8. Cost & time per cover

| Stage | Time | Cost |
|---|---|---|
| Stage 1 (SDXL+LoRA local) | 30-60s on RTX 4080+ | $0 (electricity) |
| Stage 1 (RetroDiffusion API) | 5-15s | ~$0.02 |
| Stage 1 (MidJourney) | 30-60s + manual export | $0.10-0.30 (subscription proportion) |
| Stage 2 (preprocess) | 5-10s | $0 |
| Stage 3 (manual cleanup) | 10-30 min OR 0 (skip) | $0 |
| Stage 4 (overlay coding) | 5-15 min | $0 |
| Stage 5 (bake) | 30-60s | $0 |
| **Total per cover** | **15-60 min** | **$0-0.30** |

For batch (10 covers): ~3-5 hours, $0-3.

---

## 9. Quality benchmark vs reference

| Aspect | Tier 1 (current) | Tier 2 (192×288 hand) | Tier 3 (AI base + overlay) |
|---|---|---|---|
| Atmospheric perspective | None | Manual fade layers | Built-in by AI |
| Volumetric lighting | Single ambient | Manual halos | AI generates naturally |
| Fine textures | None | 1-2 textures | Hundreds of pixel details |
| Multi-temperature lights | 1 accent | 2-3 sources | Many natural sources |
| Color palette | 8-16 | 16-32 | 32-64 (auto-extracted) |
| Time per cover | 30 min | 2-4 h | 15-60 min |
| % of reference quality | ~20% | ~60% | ~85-95% |

**Tier 3 is the recommended approach** when reference quality is the goal.

---

## 10. Caveats

- **AI generation requires GPU** for fast iteration (RTX 4080+ / 4090 / H100). On CPU it's 10-30x slower.
- **Initial setup is ~30 min** (install diffusers, download SDXL ~6.5GB, download LoRAs)
- **Quality is variable** — sometimes you need 5-10 generations to get a good base
- **Style consistency across covers** requires either same seed family OR ip-adapter for reference image conditioning
- **Output is YOUR responsibility legally** — read each LoRA's license; some forbid commercial use
- **AI-generated assets have copyright nuance** — for client work, verify usage rights

For non-commercial / personal / portfolio: full pipeline is ready to use. For commercial: prefer RetroDiffusion (commercial-cleared model) or hand-curated AI use.

---

## 11. Sources

- [nerijs Pixel Art XL on HuggingFace](https://huggingface.co/nerijs/pixel-art-xl)
- [Civitai - Pixel Art XL LoRA](https://civitai.com/models/120096/pixel-art-xl)
- [latent-consistency/lcm-lora-sdxl](https://huggingface.co/latent-consistency/lcm-lora-sdxl)
- [RetroDiffusion API docs](https://retrodiffusion.ai/)
- [PixelLab Python SDK](https://pypi.org/project/pixellab/)
- [Diffusers library docs](https://huggingface.co/docs/diffusers)
- [Civitai pixel art tag](https://civitai.com/tag/pixel%20art)
- [pyxelate GitHub](https://github.com/sedthh/pyxelate) — for Stage 2 alternative
- [hitherdither GitHub](https://github.com/hbldh/hitherdither) — advanced dithering

See also `image-to-pixel-art-tools-2026.md` for tool catalog details, and `smoother-animation-baking.md` for Stage 5 specifics.
