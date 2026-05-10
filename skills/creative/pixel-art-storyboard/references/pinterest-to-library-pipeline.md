# Pinterest-to-Library Pipeline

How to take 1000 raster images (JPEG/PNG, lossy compression, not on a clean pixel grid) — like Pinterest pixel art reference images — and turn them into structured element library entries that our procedural generator can use.

The user's correct insight: **Pinterest has lossy JPEGs, not vector pixel art**. We need a translation pipeline.

---

## 1. The 3-layer translation problem

```
┌──────────────────────────────────────────────────────────┐
│ Layer 1: Raster JPEG (Pinterest, ~1024×1536, lossy)      │
│    Format: JPEG with chroma subsampling artifacts        │
│    Pixels: NOT on clean grid (fractional pixel widths)   │
│    Palette: 16-million colors due to JPEG noise          │
│    Animation: none (still image)                         │
└──────────────────────────────────────────────────────────┘
                           ↓
                  STAGE A: PIXELIZATION
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 2: "True pixel art" PNG                            │
│    Format: indexed PNG, lossless                         │
│    Pixels: snapped to integer grid (e.g. 192×288)        │
│    Palette: 16-64 unique colors                          │
│    Animation: still none, but grid-aligned               │
└──────────────────────────────────────────────────────────┘
                           ↓
                STAGE B: STRUCTURED EXTRACTION
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 3: Structured representation                       │
│    Format: JSON                                          │
│    Content: { palette, segments, elements, anchors,      │
│               composition_rules, mood, style_tags }      │
│    Use: train element drawers, build library entries     │
└──────────────────────────────────────────────────────────┘
                           ↓
                STAGE C: LIBRARY INTEGRATION
                           ↓
┌──────────────────────────────────────────────────────────┐
│ Layer 4: Element library entries (canvas drawers + meta) │
│    Format: per-file .js with meta export                 │
│    Content: parameterized canvas draw functions          │
│    Use: composable scene generation                      │
└──────────────────────────────────────────────────────────┘
```

Each stage has different tools. **Pinterest images can't skip stages** — they need full pipeline.

---

## 2. Stage A: Pixelization (JPEG → grid-aligned PNG)

### Path A1: Open-source Python (pyxelate + Pillow)

```python
# pip install pyxelate Pillow numpy
from pyxelate import Pyx, Pal
import PIL.Image as Image
import numpy as np

img = Image.open("pinterest_dump_001.jpg").convert("RGB")
arr = np.array(img)

# Configure pixelizer
pyx = Pyx(
    factor=8,              # downsample factor: 1024→128
    palette=32,            # 32-color palette (auto-extracted)
    dither="atkinson",     # Atkinson dithering (clean retro look)
    sobel=2,               # edge enhancement
)
pyx.fit(arr)
out = pyx.transform(arr)
Image.fromarray(out).save("snapped_001.png")
```

Output: clean PNG at 128×192 with 32-color palette. Atkinson dithering preserves gradients without noise.

### Path A2: AI-based (SDXL + Pixel Art XL LoRA, img2img mode)

Better quality on complex Pinterest images, especially atmospheric ones with subtle shading.

```python
from diffusers import StableDiffusionXLImg2ImgPipeline
import torch
from PIL import Image

pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-refiner-1.0",
    torch_dtype=torch.float16
).to("cuda")
pipe.load_lora_weights("nerijs/pixel-art-xl")

src = Image.open("pinterest_dump_001.jpg").resize((1024, 1536))
out = pipe(
    prompt="pixel art, 16-bit, atmospheric, masterpiece",
    image=src,
    strength=0.5,           # preserve composition, change to pixel-art aesthetic
    num_inference_steps=20,
    guidance_scale=7.0,
).images[0]
out.save("ai_001.png")

# Then run through Path A1 to snap to true pixel grid:
arr = np.array(out)
pyx = Pyx(factor=4, palette=32, dither="atkinson")
pyx.fit(arr); final = pyx.transform(arr)
Image.fromarray(final).save("snapped_ai_001.png")
```

This gives best quality but requires GPU. ~30 seconds per image on RTX 4080.

### Path A3: Commercial API (RetroDiffusion)

```python
# pip install requests
import requests, base64

def pixelize_via_retrodiffusion(image_path, api_key, w=192, h=288):
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    response = requests.post(
        "https://api.retrodiffusion.ai/v1/inferences",
        headers={"X-RD-Token": api_key},
        json={
            "model": "RD_FLUX",
            "input_image": img_b64,
            "prompt": "atmospheric pixel art",
            "width": w,
            "height": h,
            "strength": 0.4,
        }
    )
    return base64.b64decode(response.json()["base64_images"][0])
```

50 free credits, ~$0.02 per image after. Best for batch (no GPU needed locally).

### Comparison for Pinterest input

| Tool | Setup | Cost | Quality | Speed (per image) | Best for |
|---|---|---|---|---|---|
| pyxelate | pip | $0 | 6/10 (bit cartoon-flat) | 5s CPU | Bulk batch, simple Pinterest input |
| Pillow LIBIMAGEQUANT | pip | $0 | 5/10 | 1s | Quick pre-pass |
| SDXL + pixel-art-xl | local GPU | $0 (electricity) | 8/10 (atmospheric) | 30s GPU | Quality matters, GPU available |
| RetroDiffusion API | API key | $0.02/img | 9/10 (true pixel model) | 5-10s API | Batch + quality + no GPU |
| FLUX-based LoRAs | local GPU | $0 | 8-9/10 (newer, more atmospheric) | 30-60s GPU | Cutting-edge quality |

**Recommendation**: pyxelate for first pass, then SDXL+LoRA refine for high-priority images.

---

## 3. Stage B: Structured extraction (PNG → JSON description)

Once pixel-aligned, extract:
- **Palette**: hex list (sorted by usage)
- **Segments**: which regions are background, midground, subject
- **Elements**: tagged objects ("tower", "mountain", "tree")
- **Composition**: anchor points, depth layers, rule-of-thirds
- **Style**: mood ("dusk-cool"), temperature distribution, dithering pattern

### Tool choices

#### B1: Vision LLM tagging (Claude / GPT-4V / Qwen-VL)

```python
import anthropic  # pip install anthropic

client = anthropic.Anthropic()
with open("snapped_001.png", "rb") as f:
    img_data = base64.standard_b64encode(f.read()).decode("utf-8")

msg = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=1500,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64",
              "media_type": "image/png", "data": img_data}},
            {"type": "text", "text": """Analyze this pixel art image. Return JSON:
{
  "elements": [{"name": str, "category": str, "approx_bbox": [x,y,w,h], "depth": "fg|mg|bg"}, ...],
  "palette_mood": str,
  "time_of_day": str,
  "dominant_subject": str,
  "composition_anchor": str,
  "atmospheric_perspective": bool,
  "style_tags": [str, ...]
}"""}
        ]
    }]
)
analysis = json.loads(msg.content[0].text)
```

Claude vision gives structured analysis. **~$0.01 per image** at Opus pricing, faster on Haiku/Sonnet.

#### B2: SAM 2 segmentation + classifier

For pixel-precision masks:

```python
# pip install segment-anything-2
from sam2.sam2_image_predictor import SAM2ImagePredictor
from sam2.build_sam import build_sam2

# SAM 2 returns instance masks. Classify each via vision LLM.
predictor = SAM2ImagePredictor(build_sam2("sam2_hiera_l.pt"))
predictor.set_image(np.array(Image.open("snapped_001.png")))
masks = predictor.predict_auto()
# Each mask = one segment. Pass to vision LLM with "what is this?"
```

Heavier (model file ~600MB) but pixel-precise. Useful when you need exact bounding regions.

#### B3: Palette + clustering only (no LLM, deterministic)

```python
from PIL import Image
import numpy as np

img = np.array(Image.open("snapped_001.png").convert("RGB"))
pixels = img.reshape(-1, 3)
unique, counts = np.unique(pixels, axis=0, return_counts=True)
palette = [(tuple(c), int(n)) for c, n in zip(unique, counts)]
palette.sort(key=lambda x: -x[1])
print("Top colors:", palette[:10])

# Style classification by palette mood
def classify_mood(palette):
    avg_brightness = np.mean([sum(c) / 3 for (c, _) in palette[:20]])
    avg_saturation = ... # compute saturation
    if avg_brightness < 80: return "dark"
    if avg_brightness > 180: return "bright"
    return "medium"

mood = classify_mood(palette)
```

No external API needed. Limited tagging but free and instant.

### Combined extraction (recommended pipeline)

```python
# Stage B combined
def extract_structure(png_path):
    img = Image.open(png_path).convert("RGB")
    arr = np.array(img)

    # Palette via numpy
    pixels = arr.reshape(-1, 3)
    unique, counts = np.unique(pixels, axis=0, return_counts=True)
    palette_hex = ["#" + bytes(c).hex() for c, _ in
                   sorted(zip(unique, counts), key=lambda x: -x[1])[:32]]

    # Vision LLM tagging
    llm_analysis = vision_llm_analyze(png_path)

    # Combine
    return {
        "palette": palette_hex,
        "size": arr.shape[:2],
        **llm_analysis
    }
```

---

## 4. Stage C: Library integration (decomposed images → element drawers)

This is the hardest stage: from "image of tower at coords (96, 90)" to "drawTower function".

### Approach C1: Manual curation aided by AI

1. Decompose 1000 images via Stages A+B → 1000 JSON descriptions
2. Cluster element descriptions (k-means on element descriptions / CLIP embeddings)
3. Identify recurring elements: "tower" appears in 50 images
4. Pick 1 best representative per cluster
5. **Human (you) writes the canvas drawer** for that element type
6. Element variants come from cluster members

This is the **practical** approach. AI does heavy lifting; human writes 50-100 element drawers manually but informed by the data.

### Approach C2: AI-assisted code generation

For each cluster, ask Claude to write the canvas drawer:

```
"Here's a 64x96 reference pixel art of a stone tower with crenellations.
Generate a JavaScript function drawTower(ctx, x, y, opts) that draws this
to a 192x288 canvas with parametric height/width. Style notes: brick texture,
mortar lines every 4 rows, 5 merlons, optional flag with sin-wave motion."
```

Claude can generate ~70-80% correct drawer; human refines.

### Approach C3: Train-then-generate

Train a small ML model on (image, drawer-code) pairs. Output drawer code from new image. **Heavy ML work, not recommended unless 10K+ pairs available.**

---

## 5. End-to-end pipeline for 1000 Pinterest images

```bash
# === Stage A: Pixelization (1000 → 1000 PNG)
python scripts/pixelize_batch.py \
  --input pinterest_dump/ \
  --output snapped/ \
  --tool pyxelate-then-sdxl-refine \
  --gpu

# 1000 × 30s on RTX 4080 = 8 hours
# Cost: $0 local, ~$20 if cloud GPU

# === Stage B: Structured extraction (1000 → 1000 JSON)
python scripts/extract_structure.py \
  --input snapped/ \
  --output extracted/ \
  --vision-llm claude-haiku  # cheaper for tagging

# 1000 × $0.005 = $5 (Haiku) or $50 (Opus)
# Time: ~2 hours sequential, ~30 min parallel

# === Stage C: Cluster + curate
python scripts/cluster_elements.py \
  --input extracted/ \
  --output clusters/

# Output: 50-200 clusters (recurring element types)
# Human review: pick best representative per cluster

# === Stage D: Generate drawer code (AI-assisted)
python scripts/generate_drawers.py \
  --clusters clusters/ \
  --output elements/auto-generated/

# 50-200 drawer.js files in elements/ folder
# Human refines each (10-30 min per drawer)

# === Stage E: Publish to library
python scripts/build_library.py
# Generates _manifest.json, _embeddings.bin, previews
```

**Total realistic estimate**:
- Stage A-B: automated, ~10 hours, ~$5-50
- Stage C-D: human review of 100 clusters, ~20 hours
- Stage E: automated, 1 hour
- **Total: ~30 hours work + minor cost = mature 100-element library**

To grow to 10K, repeat with more datasets (Lospec gallery, OpenGameArt, additional Pinterest sets).

---

## 6. Alternative: Train our own LoRA on the 1000 images

Skip extraction entirely. Train a Stable Diffusion LoRA on the 1000 Pinterest images. Use it directly via SDXL pipeline.

```bash
# pip install kohya-ss/sd-scripts
python sdxl_train_network.py \
  --pretrained_model_name_or_path stabilityai/stable-diffusion-xl-base-1.0 \
  --train_data_dir pinterest_dataset/ \
  --output_dir output/ \
  --output_name pinterest-pixel-style \
  --network_module networks.lora \
  --network_dim 32 \
  --learning_rate 1e-4 \
  --max_train_steps 5000 \
  --train_batch_size 1 \
  --resolution 1024
```

Output: `pinterest-pixel-style.safetensors` LoRA file (~120MB)

**Use case**: when generating new scenes, load this LoRA → outputs match Pinterest dataset style.

**Time**: ~6-12 hours on RTX 4090. **Cost**: $0 local; ~$10-20 cloud (vast.ai).

**Trade-off**: LoRA generates raster images, NOT structured elements. Still need Stages A+B if you want element library entries. But for direct image generation in our style, LoRA is the fastest path.

---

## 7. Hybrid pipeline (recommended)

```
1000 Pinterest JPEGs
         │
         ├──→ Train LoRA (6-12h, $0-20)
         │    Use for direct generation in our style
         │    (output: raster pixel art via SDXL+LoRA)
         │
         └──→ Pixelize + extract (Stages A-B, ~10h, ~$5-50)
              Cluster + curate (Stage C, ~20h human)
              Generate drawers (Stage D, ~30h human)
              → Element library 100-200 entries

Both paths complement each other:
- LoRA generates fast / freeform output
- Element library gives structured / composable / editable output
- Use LoRA output AS reference image for new element drawers
```

---

## 8. Legal note (Pinterest specifically)

Pinterest content is owned by individual users. Scraping considerations:

- **Personal/research use** of small samples: generally OK
- **Reference for inspiration**: OK if not redistributed
- **Direct redistribution / commercial use**: **NOT OK without artist permission**
- **Train AI model on collection + generate competing commercial output**: legally fraught (active litigation 2024-2026 on AI training fair use)

**Better data sources** with cleaner legal status:
- **Lospec gallery** — many CC-licensed
- **OpenGameArt** — explicit licensing per asset (CC0 / CC-BY)
- **PixelJoint** — artist attribution
- **HuggingFace datasets** — search "pixel-art-1m" or similar (verify license)
- **Itch.io free asset packs** — many CC0 explicitly
- **Public domain sprite collections**

Use these for training; Pinterest only for inspiration / reference.

---

## 9. Scale plan: 100 → 1,000 → 10,000

| Library size | Sources | Time | Strategy |
|---|---|---|---|
| 100 (now) | Hand-coded + LoRA-aided | 30 hours | Manual curation |
| 1,000 | + 1000 Pinterest decomposition | +30 hours | Pipeline above + human review |
| 10,000 | + Multiple datasets (Lospec, OpenGameArt, public Reddit dumps) | +200-400 hours | Mostly automated; human reviews 1% sample |

The element library grows organically with each new image batch processed.

---

## 10. Sources to research further

- [pyxelate GitHub](https://github.com/sedthh/pyxelate)
- [nerijs/pixel-art-xl HuggingFace](https://huggingface.co/nerijs/pixel-art-xl)
- [RetroDiffusion API](https://retrodiffusion.ai/)
- [Kohya-ss SD-scripts](https://github.com/kohya-ss/sd-scripts)
- [SAM 2 GitHub](https://github.com/facebookresearch/segment-anything-2)
- [ai-toolkit (HuggingFace)](https://github.com/huggingface/ai-toolkit) — newer 2025 trainer
- [fluxgym](https://github.com/cocktailpeanut/fluxgym) — FLUX LoRA training UI
- [Lospec gallery](https://lospec.com/gallery) — CC-licensed pixel art
- [OpenGameArt 2D pixel art](https://opengameart.org/art-search-advanced) — explicit licensing

See companion docs:
- `image-to-pixel-art-tools-2026.md` (general tool catalog)
- `high-detail-pipeline.md` (Tier 3 SDXL+LoRA workflow)
- `element-library-scaling-architecture.md` (library at 10K elements)
- `image-collection-learning-2026.md` (research output, after agent returns)
- `image-to-pixelart-and-training-2026.md` (research output, training-focused)
