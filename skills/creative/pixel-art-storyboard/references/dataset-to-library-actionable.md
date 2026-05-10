# Dataset → Element Library: Actionable 2026 Pipeline

Combines findings from `image-collection-learning-2026.md` and `image-to-pixelart-and-training-2026.md` into a **single executable plan** for turning 1000+ pixel-art images into a working element library at scale.

This document is the "what to actually do" version. For deeper rationale see the two research files.

---

## TL;DR

1. **Don't use Pinterest** (legal grey area + lossy JPEG). Use HuggingFace `bghira/free-to-use-pixelart`, OpenGameArt CC0, GameTileNet (semantic-labeled academic dataset).

2. **Pixelize first** with `Pillow + libimagequant` (10 min for 1000 CPU). Optional SD-piXL for top quality subset (slow, mathematically guarantees grid alignment).

3. **For LoRA training**: convert to pixel art FIRST, then curate 200-300 best, train via `fal.ai` ($8/1000 steps) or local FLUX LoRA via `fluxgym`.

4. **Decompose to elements** via `Grounded-SAM-2` (segment) + `Qwen2.5-VL-7B` local OR `Gemini 2.5 Flash` ($0.50/1000) for tagging.

5. **Cluster** via `DINOv2` (visual style) + `UMAP` + `HDBSCAN` (auto-K). Expected 15-40 element clusters per 1000 images.

6. **Mine grammar** via `mlxtend` FP-Growth — find rules like "mountains → fog_band confidence=0.84".

7. **Generate drawer code** via Claude — feed Claude each cluster centroid PNG + structural metadata, ask it to write `drawXxx(ctx, x, y, opts)` JS function. ~70-80% correct on first pass; human refines.

8. **Evaluate** via `CMMD` (CLIP Maximum Mean Discrepancy) through `clean-fid` library — better convergence than FID for non-ImageNet domains like pixel art.

9. **Compose scenes** via `SceneSmith` pattern (arxiv 2602.09153) — designer + critic + orchestrator with 3-5 iterations.

**Total cost**: $5-25 for cloud APIs + ~30 hours human work for 100-200 element library starting from 1000 images.

---

## The full executable pipeline (commands)

### Stage 0: Data acquisition (legal-clean datasets)

```bash
# HuggingFace pixel art dataset (clean license)
pip install datasets
python -c "
from datasets import load_dataset
ds = load_dataset('bghira/free-to-use-pixelart', split='train')
ds.save_to_disk('./pixelart_dataset')
"

# OR clone GameTileNet (academic, semantic labels per tile)
git clone https://github.com/<gametilenet-repo>  # see arxiv 2507.02941 for repo
```

Avoid Pinterest scraping. If you must use Pinterest, treat as **inspiration only** — do not redistribute or train commercially.

### Stage 1: Pixelization (Pillow + libimagequant + rembg)

Best speed/quality combo for 1000 images:

```python
# pip install Pillow imagequant rembg numpy
from PIL import Image
import imagequant
from rembg import remove
import numpy as np
from pathlib import Path

INPUT_DIR = Path("pixelart_dataset/")
OUTPUT_DIR = Path("snapped/")
OUTPUT_DIR.mkdir(exist_ok=True)

for img_path in INPUT_DIR.glob("*.{jpg,jpeg,png}"):
    src = Image.open(img_path).convert("RGBA")

    # Optional: remove background for subject isolation
    fg = remove(src)  # returns RGBA with alpha=0 for background

    # Resize to logical pixel grid (e.g. 192x288 for book covers)
    target_size = (192, 288)
    snapped = fg.resize(target_size, Image.Resampling.NEAREST)

    # Quantize to 32-color palette via libimagequant (best quality)
    rgb = snapped.convert("RGB")
    quantized = imagequant.quantize_pil_image(
        rgb,
        max_colors=32,
        dithering_level=1.0,  # full Atkinson dither
    )
    quantized.save(OUTPUT_DIR / f"{img_path.stem}.png")

# 1000 images in ~10-15 min on modern CPU. No GPU needed.
```

**Output**: 1000 grid-aligned PNG files at 192×288 with 32-color palettes.

For top 20-50 high-priority images, optionally use **SD-piXL** (ETH Zurich, SIGGRAPH Asia 2024):

```bash
# SD-piXL guarantees mathematically hard grid alignment + exact palette
git clone https://github.com/ETH-Zurich/SD-piXL  # check exact URL via arxiv 2410.06236
cd SD-piXL && pip install -r requirements.txt
python sd-pixl.py --input image.jpg --target-size 192x288 --palette-size 32 --output snapped.png
# Slow: 2-10 min per image. Use for top 5% only.
```

### Stage 2: Decomposition via vision LLM

Local (free, requires GPU):

```python
# pip install transformers torch qwen-vl-utils
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import torch
from pathlib import Path
import json

model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-7B-Instruct",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")

PROMPT = """Analyze this pixel art image. Return JSON only:
{
  "elements": [{"name": str, "category": "architecture|nature|character|weather|vfx|celestial",
                "approx_bbox": [x_pct, y_pct, w_pct, h_pct], "depth": "fg|mg|bg"}, ...],
  "palette_mood": str,
  "time_of_day": str,
  "dominant_subject": str,
  "composition_anchor": "center|left-third|right-third|top-third|bottom-third",
  "atmospheric_perspective": bool,
  "style_tags": [str, ...]
}"""

decomposed = []
for png_path in Path("snapped/").glob("*.png"):
    inputs = processor(images=Image.open(png_path), text=PROMPT, return_tensors="pt").to("cuda")
    output_ids = model.generate(**inputs, max_new_tokens=500)
    text = processor.batch_decode(output_ids, skip_special_tokens=True)[0]
    parsed = json.loads(text.split("```json")[-1].split("```")[0]) if "```" in text else json.loads(text)
    decomposed.append({"file": png_path.name, **parsed})

Path("decomposed.json").write_text(json.dumps(decomposed, indent=2))
```

**Cost**: $0 if RTX 4090. Time: ~1-2 hours for 1000 images.

Cloud alternative (faster, paid):

```python
# pip install google-generativeai
import google.generativeai as genai
genai.configure(api_key="YOUR_KEY")
model = genai.GenerativeModel("gemini-2.5-flash")

for png_path in Path("snapped/").glob("*.png"):
    img = Image.open(png_path)
    response = model.generate_content([PROMPT, img])
    parsed = json.loads(response.text)
    # ... save
```

**Cost**: ~$0.50 for 1000 images via Gemini 2.5 Flash. Time: ~30 min.

### Stage 3: Style clustering via DINOv2

```python
# pip install transformers torch umap-learn hdbscan
from transformers import AutoImageProcessor, AutoModel
from PIL import Image
import torch, numpy as np

processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
model = AutoModel.from_pretrained("facebook/dinov2-base").to("cuda")

# Compute embeddings for all 1000 images
embeddings = []
files = list(Path("snapped/").glob("*.png"))
for png_path in files:
    img = Image.open(png_path).convert("RGB")
    inputs = processor(images=img, return_tensors="pt").to("cuda")
    with torch.no_grad():
        feat = model(**inputs).last_hidden_state.mean(dim=1)  # 768-dim
    embeddings.append(feat.cpu().numpy()[0])

embeddings = np.array(embeddings)
np.save("dinov2_embeddings.npy", embeddings)

# Cluster via UMAP + HDBSCAN (auto-K)
import umap, hdbscan
reducer = umap.UMAP(n_components=20, n_neighbors=15, min_dist=0.05)
reduced = reducer.fit_transform(embeddings)
clusterer = hdbscan.HDBSCAN(min_cluster_size=10)
labels = clusterer.fit_predict(reduced)

# Each cluster represents a "style family"
# E.g. cluster 0 = "cyberpunk-night", cluster 1 = "fantasy-dawn", etc.
print(f"Found {len(set(labels))} style clusters")
```

### Stage 4: Element extraction (recurring patterns)

```python
# Find elements that appear in many images via FP-Growth
# pip install mlxtend
from mlxtend.frequent_patterns import fpgrowth, association_rules
import pandas as pd

# Build per-image element bag
transactions = []
for entry in decomposed:
    elements = [e["name"] for e in entry["elements"]]
    transactions.append(elements)

df = pd.DataFrame([
    {item: True for item in tx} for tx in transactions
]).fillna(False)

freq_items = fpgrowth(df, min_support=0.05, use_colnames=True)
rules = association_rules(freq_items, metric="confidence", min_threshold=0.7)
print(rules[["antecedents", "consequents", "support", "confidence"]])

# Output:
# {mountains} → {fog_band}    confidence=0.84
# {tower}     → {flag}        confidence=0.62
# {moon}      → {stars}       confidence=0.91
# These become composition rules in scene grammar.
```

### Stage 5: Generate canvas drawer code via Claude

For each cluster (representing a recurring element type), pick the centroid image + extract its bounding box, then ask Claude:

```python
import anthropic
client = anthropic.Anthropic()

PROMPT_TEMPLATE = """I have this pixel art reference image (visible to you).
The element shown is a {category} called "{name}".

Generate a JavaScript function `draw{NameCamelCase}(ctx, x, y, opts)` that draws this
element to a canvas. Match the visual style of the reference. Parameters in opts:

- variant: {variant_options}
- palette: semantic palette object (palette.bg1..bg4, .stone, .stoneDark, .warm, etc.)
- height/width: dimensions in pixels
- t: animation phase 0..1 (if element has motion)

Use the same patterns as our existing element library:
- Layer logic (light from upper-left assumed)
- Brick textures via row-offset
- Multi-component sin waves for motion
- Volumetric glow halos for lit elements (3-pixel radial alpha-blend)

Return ONLY the JS function code (no markdown). Mock the meta object too."""

for cluster_id, centroid_img_path in cluster_centroids.items():
    name = cluster_metadata[cluster_id]["name"]
    category = cluster_metadata[cluster_id]["category"]
    variants = cluster_metadata[cluster_id]["variants"]

    img_data = base64.b64encode(open(centroid_img_path, "rb").read()).decode()
    msg = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64",
                  "media_type": "image/png", "data": img_data}},
                {"type": "text", "text": PROMPT_TEMPLATE.format(
                  category=category, name=name,
                  NameCamelCase=name.title().replace('-', ''),
                  variant_options=variants)}
            ]
        }]
    )
    code = msg.content[0].text
    Path(f"elements/{category}/{name}.v1.js").write_text(code)
```

Claude will generate ~70-80% correct drawer code. Human reviews + refines (~10-20 min per drawer).

**Cost**: ~$0.10 per drawer × 100 = $10. Time: ~30 min auto + 20 hours human review.

### Stage 6: Train style LoRA (optional but powerful)

Once you have 200-300 best pixel-art-converted images:

```bash
# Cloud option: fal.ai (fastest, $8 per training)
pip install fal-client
fal config set FAL_KEY=$YOUR_KEY
python -c "
import fal_client
result = fal_client.run(
    'fal-ai/flux-lora-fast-training',
    arguments={
        'images_data_url': 'https://your-cdn/dataset.zip',
        'trigger_word': 'pixelartstyle',
        'steps': 1000,
    }
)
print(result['diffusers_lora_file'])
"

# Or local option: fluxgym (RTX 4090+)
git clone https://github.com/cocktailpeanut/fluxgym && cd fluxgym
python app.py  # web UI for LoRA training
```

Now you can generate NEW images in your trained style:

```python
from diffusers import FluxPipeline
import torch

pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-dev",
                                      torch_dtype=torch.bfloat16).to("cuda")
pipe.load_lora_weights("./your-trained-lora.safetensors")

img = pipe(
    prompt="pixelartstyle, atmospheric snowy fortress on cliff, warm window glow at dusk",
    num_inference_steps=20,
    guidance_scale=3.5,
).images[0]
```

### Stage 7: Quality evaluation via CMMD

```bash
# pip install clean-fid clip-by-openai
python -c "
from cleanfid import fid
score = fid.compute_fid(
    generated_dir='./our_outputs/',
    real_dir='./snapped/',
    mode='clean',
    model_name='clip',  # CMMD = CLIP MMD
    num_workers=4
)
print(f'CMMD: {score}')  # lower is better; <5 = excellent match
"
```

CMMD measures distributional distance between our generated outputs and reference dataset. Use to track quality across library evolution.

---

## Recommended phased execution

### Phase 1 (Day 1, ~6 hours, $0)
- Stage 0: Download `bghira/free-to-use-pixelart` (1000+ images)
- Stage 1: Pillow+libimagequant pixelization (15 min)
- Stage 2: Qwen2.5-VL-7B local decomposition (2 hours on RTX 4090)
- Stage 3: DINOv2 clustering (10 min)
- Stage 4: FP-Growth pattern mining (instant)
- Output: 15-40 element clusters with metadata

### Phase 2 (Days 2-4, ~24 hours human, ~$10)
- Stage 5: Claude drawer code generation (30 min auto + 20 h human review)
- Output: 50-100 element drawer .js files

### Phase 3 (optional, Day 5, ~4 hours, $8)
- Stage 6: FLUX LoRA training on curated 200 images
- Output: `our-style.safetensors` LoRA file
- Use case: generate freeform reference images in our style

### Phase 4 (ongoing, weekly)
- Stage 7: CMMD evaluation against held-out test set
- Continuous library growth via additional datasets

**Total to mature 100-element library starting from 1000 images: ~30 hours work + ~$10-20 cost.**

---

## Decision matrix

| Goal | Tool | Why |
|---|---|---|
| Pixelize 1000 images fast | Pillow + libimagequant | $0, 15 min CPU, good quality |
| Pixelize 50 priority images at top quality | SD-piXL | mathematical grid + palette guarantee |
| Generate new in our style | FLUX LoRA via fal.ai | $8 once, infinite generations |
| Decompose to structure | Qwen2.5-VL local | $0 if GPU, near-GPT-4o quality |
| Decompose to structure (cheaper, no GPU) | Gemini 2.5 Flash | $0.50 per 1000 images |
| Cluster by style | DINOv2 + UMAP + HDBSCAN | texture-aware, auto-K |
| Generate drawer code | Claude vision + code | ~$10 for 100 drawers, 70-80% accuracy |
| Evaluate quality | CMMD via clean-fid | better than FID for pixel art |
| Compose scene from text | SceneSmith pattern | designer+critic+orchestrator |

---

## What we are NOT going to use

- ❌ **Pinterest scraping** — legal grey, lossy quality, alternatives exist
- ❌ **FID** — broken for pixel art (Inception trained on ImageNet)
- ❌ **Full DreamBooth fine-tune** — overkill, LoRA is sufficient
- ❌ **DALL-E / MidJourney UI-only** — no programmatic batch
- ❌ **GAN-based pixel art models** — superseded by diffusion+LoRA in 2026
- ❌ **Custom CNN from scratch** — pre-trained DINOv2/SigLIP do it better

---

## Sources

See companion research files:
- `image-collection-learning-2026.md` — full research output 1
- `image-to-pixelart-and-training-2026.md` — full research output 2
- `pinterest-to-library-pipeline.md` — conceptual 3-layer translation
- `element-library-scaling-architecture.md` — library at 10K+ scale

Citations:
- SD-piXL: [arxiv 2410.06236](https://arxiv.org/abs/2410.06236) (ETH Zurich, SIGGRAPH Asia 2024)
- SceneSmith: [arxiv 2602.09153](https://arxiv.org/abs/2602.09153) (Feb 2026)
- GameTileNet: [arxiv 2507.02941](https://arxiv.org/abs/2507.02941)
- nerijs Pixel Art XL: [HuggingFace](https://huggingface.co/nerijs/pixel-art-xl)
- DINOv2: [HuggingFace facebook/dinov2-base](https://huggingface.co/facebook/dinov2-base)
- Qwen2.5-VL: [HuggingFace Qwen/Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)
- bghira/free-to-use-pixelart: [HuggingFace](https://huggingface.co/datasets/bghira/free-to-use-pixelart)
- CMMD via clean-fid: [github.com/GaParmar/clean-fid](https://github.com/GaParmar/clean-fid)
- fluxgym: [github.com/cocktailpeanut/fluxgym](https://github.com/cocktailpeanut/fluxgym)
- ai-toolkit: [github.com/huggingface/ai-toolkit](https://github.com/huggingface/ai-toolkit)
- Grounded-SAM-2: [github.com/IDEA-Research](https://github.com/IDEA-Research)
