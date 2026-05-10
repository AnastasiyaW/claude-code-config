# Tools and Libraries Reference

Production-grade catalog of desktop editors, Python libraries, JavaScript libraries, and AI/ML tools. Entries are ordered by relevance to this skill's workflow.

---

## 1. Desktop pixel art editors

### Aseprite — industry standard

| Attribute | Value |
|---|---|
| **Price** | $14.99 (Steam or aseprite.org) |
| **OS** | Windows, macOS, Linux |
| **Source** | aseprite.org; github.com/aseprite/aseprite (source, GPLv2 only for self-compile) |
| **Formats** | `.aseprite`, PNG, GIF, BMP, JPEG, WEBP, PCX, TGA |

**Strengths**:
- Tags system: named animation ranges with Forward/Reverse/Ping-pong modes
- Indexed color mode: palette-exact editing, palette swap workflow
- Onion skinning: configurable back/forward ghost frames
- Tilemap mode: Layer > New > New Tilemap Layer (Aseprite 1.3+)
- Lua scripting: full automation API (`app.command`, `app.sprite`, `app.activeCel`)
- CLI export: `aseprite -b input.aseprite --sheet sheet.png --data sheet.json`
- Official Korean locale support since v1.3.3 (install `aseprite-language-ko.zip`)
- CN community: Cosmolau translated docs — aseprite.cosmolau.top/zh/docs/tutorial

**Weaknesses**:
- Paid (negligible cost but a friction point for beginners)
- No built-in AI generation or complex raster operations (by design)

**Our skill uses Aseprite format for**: tags field in JSON schema (`direction: forward|reverse|pingpong`), sprite sheet conventions, indexed PNG export with palette.

### LibreSprite — OSS fork

| Attribute | Value |
|---|---|
| **Price** | Free |
| **OS** | Windows, macOS, Linux |
| **Source** | github.com/LibreSprite/LibreSprite |
| **Formats** | Same as Aseprite ~v1.1 |

**Strengths**: fully open source, no cost, familiar Aseprite interface.

**Weaknesses**: lags upstream Aseprite by several years; missing tilemap mode, advanced indexed-palette features, Lua scripting improvements. Use only for OSS-only constraints.

### Pyxel Edit

| Attribute | Value |
|---|---|
| **Price** | $9 (paid) / free older version |
| **OS** | Windows, macOS |
| **Formats** | `.pyxel` (proprietary), PNG |

**Strengths**: excellent tile-focused workflow, visual tile layout tools, animation preview.

**Weaknesses**: free version is outdated; no Linux; slower update cadence than Aseprite; less community traction.

**Use when**: tile-based world building workflow where tile-palette management is primary concern.

### GraphicsGale

| Attribute | Value |
|---|---|
| **Price** | Free |
| **OS** | Windows only |
| **Formats** | PNG, GIF, BMP, AVI, `.gal` |

**Strengths**: strong frame-by-frame animation; live GIF preview while editing; classic tool for pre-Aseprite Windows workflow.

**Weaknesses**: Windows-only; dated UI; minimal ongoing development; no macOS/Linux.

**Cited in**: gamedev.ru art forum as historical recommendation; Russian community uses this alongside GrafX2.

### Piskel — web-based

| Attribute | Value |
|---|---|
| **Price** | Free |
| **OS** | Browser + PWA |
| **Formats** | PNG, GIF, ZIP (individual frames) |

**Strengths**: zero-install; onion skinning; GIF/sprite-sheet export; works offline via PWA.

**Weaknesses**: no palette management tools; poor resize/downsample; no indexed mode; limited to smaller sprites.

**Use when**: quick demos, sharing with non-technical users, no-install environments.

### Pixilart

| Attribute | Value |
|---|---|
| **Price** | Free |
| **OS** | Browser |
| **Formats** | PNG, GIF |

**Strengths**: strong social/community layer (gallery, challenges); beginner-friendly.

**Weaknesses**: weak animation tools; limited palette management; social features add friction for production use.

### Lospec Pixel Editor

| Attribute | Value |
|---|---|
| **Price** | Free |
| **OS** | Browser |
| **Formats** | PNG |

**Strengths**: direct integration with Lospec palette library; palette-aware editing.

**Weaknesses**: less feature-complete than Aseprite; no animation.

### PixelOver

| Attribute | Value |
|---|---|
| **Price** | Paid (~$15) |
| **OS** | Windows |
| **Formats** | PNG, GIF |

**Strengths**: real-time image-to-pixel-art pipeline; skeletal rigging/bones for pixel sprites; excellent preprocessing for AI → pixel workflow.

**Weaknesses**: not designed for from-scratch drawing; Windows-only; paid.

**Use when**: converting reference photos or AI drafts to pixel art as part of hybrid workflow.

### REXPaint

| Attribute | Value |
|---|---|
| **Price** | Free |
| **OS** | Windows, Linux (Wine) |
| **Formats** | `.xp` (proprietary), PNG, CSV |

**Strengths**: text-mode / ASCII art / roguelike map design specialist.

**Weaknesses**: niche use case; not general pixel art.

### Pixelorama

| Attribute | Value |
|---|---|
| **Price** | Free, open source |
| **OS** | Windows, macOS, Linux, Web |
| **Source** | github.com/Orama-Interactive/Pixelorama |
| **Formats** | PNG, GIF, APNG, WebP, `.pxo` |

**Strengths**: Godot-based (cross-platform native); layer support; animation; active development.

**Weaknesses**: less polished than Aseprite; smaller community; fewer tutorials.

**CN community**: ghxi.com hosts 汉化版 (localized) Pixelorama alongside Aseprite.

---

## 2. Python libraries

### Pillow (PIL fork) — mandatory

```bash
pip install Pillow
```

| Use | Methods |
|---|---|
| NEAREST resize (pixel-perfect) | `image.resize((w, h), Image.NEAREST)` |
| Color quantization | `image.quantize(colors=N, method=Image.Quantize.MEDIANCUT)` |
| Posterize (reduce colors) | `ImageOps.posterize(image, bits=4)` for 16-value-per-channel reduction |
| Indexed PNG export | `image.convert("P")` then `image.save("out.png")` |
| Palette manipulation | `image.getpalette()`, `image.putpalette(flat_rgb_list)` |

**Quantization methods** (`Image.Quantize` enum):
| Method | Constant | Notes |
|---|---|---|
| Median cut | `MEDIANCUT` | Default, balanced |
| Maximum coverage | `MAXCOVERAGE` | Better for high-saturation palettes |
| Fast octree | `FASTOCTREE` | Fastest, lower quality |
| libimagequant | `LIBIMAGEQUANT` | Best quality; requires `pyimagequant` install |

**Source**: pillow.readthedocs.io; docs specifically: Image.quantize, ImageOps.posterize

### numpy + scipy — mandatory

```bash
pip install numpy scipy
```

Used for connected-component analysis (orphan/cluster detection), spatial operations.

```python
from scipy.ndimage import label
import numpy as np

# Orphan detection
labeled, n = label(mask, structure=np.ones((3,3)))  # 8-connectivity
sizes = np.bincount(labeled.ravel())[1:]
orphans = (sizes == 1).sum()
```

### scikit-image SLIC — optional

```bash
pip install scikit-image
```

`skimage.segmentation.SLIC`: superpixel segmentation in CIELAB+xy for region-aware downsampling. When downsampling a reference photo, SLIC groups perceptually similar neighboring pixels into superpixels first, then maps each superpixel to one palette color. Produces better-clustered output than naive NEAREST downsampling for organic subjects.

```python
from skimage.segmentation import slic
from skimage.color import rgb2lab

segments = slic(image_array, n_segments=target_pixel_count, compactness=10,
                start_label=0, convert2lab=True)
```

**Use when**: converting photographs of faces, animals, or complex organic subjects to pixel art.

### OpenCV + sklearn KMeans — optional

```bash
pip install opencv-python scikit-learn
```

For palette extraction from reference images:
```python
import cv2
from sklearn.cluster import KMeans

img = cv2.imread("ref.jpg")
pixels = img.reshape(-1, 3).astype(np.float32)
kmeans = KMeans(n_clusters=16, random_state=42).fit(pixels)
palette = kmeans.cluster_centers_.astype(int)
```

K-means produces slightly better palettes than median cut for photos with soft color regions, but is slower.

### pyxelate — recommended

```
github.com/sedthh/pyxelate
pip install pyxelate
```

Dedicated image-to-pixel-art library. Key implementation details:
- **Palette algorithm**: Bayesian Gaussian Mixture Model (not k-means) — better for tied gaussians in soft/pastel image regions
- **Dithering built-in**: Bayer 4×4, Floyd-Steinberg, Atkinson — all supported
- **Analysis**: 3×3 tile gradient HoG-inspired analysis
- **Dimensionality reduction**: Truncated SVD on RGB channels as low-pass filter before palette fitting

```python
from pyxelate import Pyx, Pal

p = Pyx(factor=8, palette=8, dither="bayer4")
p.fit(image)
pixel_art = p.transform(image)
```

**When to prefer over Pillow**: for photo→pixel-art conversions, especially organic subjects. Pyxelate's BGM palette is noticeably better on skin tones and foliage than median cut.

**Source**: github.com/sedthh/pyxelate

### Hitherdither — optional

```
github.com/hbldh/hitherdither
pip install hitherdither
```

Advanced dithering kernel library. Supports: Bayer (all sizes), Floyd-Steinberg, Atkinson, Stucki, Jarvis-Judice-Ninke, Sierra, and more.

Use when: need dithering algorithm not supported by Pillow or pyxelate (e.g., Stucki for maximum frequency response, or Jarvis for wider spread).

```python
from hitherdither import Bayer, FloydSteinberg

bayer = Bayer(4, threshold_map=Bayer.bayer_matrix(4))
dithered = bayer.dither(image, palette)
```

### ImageGoNord — optional

```
github.com/Schrodinger-Hat/ImageGoNord
pip install image-go-nord
```

Palette-mapping CLI/library. Forces an image into a specific Lospec-style palette (designed for Nord theme but works with any palette). Useful as a final pass to enforce strict palette adherence after quantization.

```bash
image-go-nord -i input.png -o output.png --palette endesga-32.json
```

---

## 3. JavaScript libraries

### pixelit

- **URL**: giventofly.github.io/pixelit/
- **Install**: CDN or `npm install pixelit`
- **Use**: Browser-based pixelization with custom palette support

```javascript
const pix = new pixelit({ to: canvas, from: imgElement, scale: 8, palette: [[R,G,B], ...] });
pix.draw();
pix.pixelate();
```

### pixelartmaker

- **URL**: pixelartmaker.com (community tool)
- Browser-based, similar scope to pixelit

### Canvas API + CSS

For displaying pixel art in browser without library:
```css
.pixel-canvas {
  image-rendering: pixelated;  /* Chrome, Edge */
  image-rendering: crisp-edges; /* Firefox */
  image-rendering: -moz-crisp-edges;
}
```

```javascript
const ctx = canvas.getContext("2d");
ctx.imageSmoothingEnabled = false;
ctx.drawImage(pixelArtImg, 0, 0, canvas.width, canvas.height);
```

`image-rendering: pixelated` is critical — without it, browser scales with bilinear interpolation, blurring the pixel art.

---

## 4. AI / ML pixel art tools

### Stable Diffusion + LoRA (open-source)

**Primary LoRAs for pixel art**:
| LoRA | Platform | Notes |
|---|---|---|
| `nerijs/pixel-art-xl` | HuggingFace | SDXL base; use with LCM LoRA for speed, 8 steps, guidance 1.5 |
| Pixel Art Diffusion XL v2 | Civitai | Improved pixel-shape quality vs v1 |
| 8bitdiffuser 64x | HuggingFace | Targets 64px output scale |
| Pixel Portrait LoRA | Civitai | Face/portrait focus |
| M_Pixel 像素人人 v2 | Civitai (civitai.com/models/44960/mpixel) | CN-authored; `pixel_style` trigger |
| Pixel_像素世界 | Liblib.art (liblib.art/modelinfo/b54aca58ee3f447987f5ddfc7dfe84f1) | SD1.5; larger weight = stronger pixel effect |
| Pixel3D像素世界 SDXL | Liblib.art (liblib.art/modelinfo/28a0039aa87547ba93acb009240dade0) | SDXL 3D pixel; trigger `3Dpixel` |
| 2D Pixel Toolkit | Liblib.art (liblib.art/modelinfo/d838d1b5f8e341528acf168a5006ca22) | CN-authored |

**AI generation limitations** (documented in Russian and English communities):
- AI-generated pixel art fails pixel grid discipline — pixels have "incorrect size or shape" (DTF: dtf.ru/craft/2903907)
- Requires post-processing pipeline (preprocess.py) to snap to real grid
- AI is useful to accelerate **drafts only**; final assets need manual cleanup

### Pixel Art Diffusion XL

Civitai checkpoint (not LoRA). Full model fine-tuned for pixel art output. V2 improves on pixel-shape regularity. Use as alternative to SDXL + LoRA stack when quality of pixel grid alignment matters.

### RetroDiffusion — commercial

- **URL**: retrodiffusion.ai
- **Model**: FLUX-based
- **Integration**: Aseprite extension
- **Key claim**: generates clean pixel grids without post-processing (unlike SDXL/LoRA which needs `preprocess.py`)
- **Pricing**: subscription

The FLUX architecture's higher text alignment and control allows more coherent pixel grid generation than diffusion models. Most reliable commercial option for pixel art specifically (vs Midjourney/DALLE which produce pixelated-looking but not pixel-correct output).

### PixelLab.ai — commercial

Similar scope to RetroDiffusion. Dedicated pixel art generation service, subscription-based.

### ControlNet — pose/edge conditioning

ControlNet Canny or OpenPose conditioning on top of SDXL + pixel LoRA. Allows generating pixel sprites with specific poses (character in run pose, in attack pose) without manual drawing. Workflow:

1. Draw or find reference pose image
2. Extract Canny edges or OpenPose skeleton
3. ControlNet-condition SD generation with pixel art LoRA
4. Run preprocess.py on output to snap to grid

### SD-π XL paper

**arxiv 2410.06236**: score distillation approach for low-resolution quantized imagery. Academic basis for why pixel-art-specific training approaches outperform generic fine-tuning. The paper introduces a discrete pixel-space objective that encourages integer-aligned pixel representations.

**Source**: arxiv.org/abs/2410.06236

### ModelScope flux-2-klein-4b-spritesheet-lora

```
modelscope.cn/models/AI-ModelScope/flux-2-klein-4b-spritesheet-lora
```

FLUX.2 Klein 4B model with LoRA for sprite sheet generation — outputs multiple character poses in a single image (front, side, back view; or multiple animation keyframes). CN-developed, hosted on ModelScope.

**Use for**: generating 8-direction sprite sheet starters; multiple animation keyframes in one pass.

### Liblib.art CN pixel LoRAs

Liblib.art (liblib.art) is the dominant CN LoRA hosting platform (comparable to Civitai for CN market). Hosts dozens of pixel-art-specific LoRAs including the Pixel_像素世界 family. Key detail: many CN pixel LoRAs are SD1.5-based and require SD1.5 checkpoints, not SDXL.

---

## 5. AI workflow integration

### Recommended hybrid workflow

The consensus recommendation (EN, CN, RU communities):

```
1. Generate rough → AI (SDXL + pixel LoRA at 768×768 or RetroDiffusion)
2. Downsample to target → Pillow NEAREST (NOT bicubic, NOT lanczos)
3. Quantize to palette → Pillow quantize (or pyxelate for photos)
4. Optional: dither → Bayer 4x4 for halftone; Floyd-Steinberg for photo-realism
5. Manual cleanup → Aseprite: fix orphans, doublies, banding, silhouette
6. Quality check → scripts/quality_check.py (target: ≥ 80)
```

```bash
python scripts/preprocess.py ai_output.png \
  --target-size 64x64 \
  --palette endesga-32 \
  --dither bayer4 \
  -o cleaned.png

python scripts/quality_check.py cleaned.png
# If score < 80: open in Aseprite, fix flagged issues, re-run check
```

### Aseprite tilemap mode

For tile-based world building:
```
Layer > New > New Tilemap Layer    (Aseprite 1.3+)
OR keyboard: Space+N (in some builds)
```

Tile conventions: 8×8 (NES-authentic), 16×16 (SNES/indie default), 32×32 (hi-bit).

Tiled editor (mapeditor.org) for level layout using exported tileset PNG.

---

## 6. CN-specific tools (less known in West)

| Tool | URL | Notes |
|---|---|---|
| Gridy.Art / 百格画 | api.gridy.art | Web editor + image-to-pixel converter, pixel avatar generator for Bilibili/QQ |
| Pixso | pixso.cn | CN-developed AI-native UI design tool with pixel art export mode |
| 果核剥壳 Aseprite | ghxi.com | Community-patched Chinese-font Aseprite builds |
| Pixel Studio | App Store CN | Mobile pixel editor with Simplified Chinese |

---

## 7. Quick selection guide

| Need | Tool |
|---|---|
| Primary production editor | Aseprite ($14.99) |
| OSS-only requirement | LibreSprite (free) |
| Tile-focused world building | Pyxel Edit |
| Converting photos → pixel art | PixelOver + preprocess.py |
| Quick browser demo | Piskel or Pixilart |
| Python processing pipeline | Pillow (mandatory) + pyxelate (recommended) + scipy (mandatory) |
| Advanced dithering kernels | Hitherdither |
| AI generation (open) | SDXL + nerijs/pixel-art-xl LoRA |
| AI generation (commercial, highest quality grid) | RetroDiffusion |
| CN sprite sheet generation via AI | flux-2-klein-4b-spritesheet-lora on ModelScope |
| Browser display | Canvas API + `image-rendering: pixelated` |
