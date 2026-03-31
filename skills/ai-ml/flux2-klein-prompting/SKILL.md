---
name: flux2-klein-prompting
description: >
  Expert prompt engineering for FLUX.2 [klein] image generation and editing model.
  Use this skill whenever the user wants to create prompts for FLUX.2 [klein], generate images,
  edit photos with the klein model, work with multi-reference image editing, or needs templates
  for T2I/I2I tasks. Trigger for any mention of: FLUX.2, flux klein, BFL API, image editing prompts,
  text-to-image prompts for FLUX, product mockups, poster generation, UI mockups, sticker packs,
  character design, seamless textures, or any request to write/improve/translate prompts for
  FLUX-family models. Also trigger when user asks about guidance_scale, inference steps, distilled
  vs base modes, or multi-reference workflows.
---

# FLUX.2 [klein] — Prompt Engineering Guide

## Core principle: prose, not tags

Official BFL prompting guide requires **connected prose**, not keyword lists.
Write: who/what is in the image, where, in what style, materials/light/camera, and — for editing — what must remain unchanged.

---

## Model variants quick reference

| Axis | Options | Notes |
|---|---|---|
| Size | 4B / 9B | 9B better for complex instructions; 4B fastest |
| Mode | Distilled / Base | Distilled = 4 steps, CFG≈1.0; Base = 50 steps, CFG≈4.0 |
| License | 4B Apache-2.0 / 9B Non-Commercial | Check before commercial use |
| Task | T2I / Edit (I2I) / Multi-reference | Edit requires `input_image`; up to 4 ref images via API |

**9B uses Qwen3 8B text embedder** → solid multilingual support (Russian works natively).

---

## Prompt structure

### T2I (text-to-image)
1. **Subject** — who/what, key attributes
2. **Scene/context** — where, time of day, surroundings
3. **Composition** — framing, angle, background
4. **Light/materials** — source, softness, reflections, texture
5. **Style/genre** — photorealism, illustration, catalog, poster, UI
6. **Text in image** (if needed) — exact string in quotes + position/font

### Edit (I2I, no mask)
1. **Base anchor** — "This exact image but…"
2. **What to change** — object / background / text / color / material
3. **What to preserve** — face, lighting, style, perspective, brand elements
4. **Multi-reference** — reference by "image 2 / image 3", keep prompt concise

---

## Key rules

**Text in image** → always in straight quotes, specify position. Without this: garbled glyphs.
```
Заголовок: "ТОЧНЫЙ ТЕКСТ". Шрифт жирный гротеск, ровный кернинг. Других надписей не добавлять.
```

**Negatives → positives** → don't say "don't change X", say "preserve X"
```
❌ "не меняй освещение"
✅ "Сохрани освещение, перспективу и лицо"
```

**Multi-reference** → simplify text, use explicit indexing
```
"Возьми персонажа из image 2 и помести рядом с объектом из image 1."
```

**Distilled for previews, Base for finals**

---

## Ready-to-use templates (Russian)

### Photorealistic object
```
Фотореалистичная предметная фотография [объект] на [фон], ракурс [сверху/на уровне глаз/крупный план], мягкий студийный свет, реалистичные материалы и фактуры, аккуратные тени, высокая детализация. Без логотипов и водяных знаков.
```

### Product mockup / e-commerce
```
Каталожный product shot: [товар] в центре кадра, фон [описание], чистая композиция, цвет товара строго [HEX или словом], реалистичные отражения, нейтральный стиль, как для e-commerce.
```

### Logo / icon
```
Минималистичная иконка: [смысл/символ], плоский дизайн, 2–3 цвета, чёткий силуэт, без мелких деталей. Без текста.
```

### Character design
```
Персонаж: [кто], внешний вид: [рост/пропорции/одежда], выражение лица [эмоция], стиль [аниме/3D/иллюстрация], палитра [цвета], фон простой. Сохранить узнаваемость: [признак 1], [признак 2].
```

### Sticker pack (6 emotions)
```
Набор стикеров одного персонажа (6 штук): радость, злость, удивление, смущение, сон, восторг. Единый стиль, толстый контур, яркая палитра, прозрачный фон, без текста.
```

### Poster with readable text
```
Постер [стиль]. Вверху крупный заголовок: "ТОЧНЫЙ ТЕКСТ". Шрифт: жирный гротеск, ровный кернинг, читаемо. Ниже подзаголовок: "Ещё одна строка". Остальные надписи не добавлять.
```

### UI mockup (mobile)
```
UI‑мокап мобильного приложения [тематика]. 3 экрана в одной сетке. Читаемые заголовки на русском в кавычках: "[Экран 1]", "[Экран 2]", "[Экран 3]". Минималистичная дизайн‑система, много воздуха, аккуратная типографика, без лишнего декоративного шума.
```

### Seamless texture
```
Бесшовная текстура (seamless): [материал], равномерное освещение, без объектов, без текста, высокая детализация, натуральные вариации, без резких пятен.
```

### Edit: replace / recolor / swap background
```
Это то же изображение, но: [что изменить]. Сохрани: [освещение / перспектива / лицо / композиция / стиль]. Сделай результат фотореалистичным и согласованным по теням и отражениям.
```

### Edit: add text to sign/label
```
Это то же изображение, но добавь на [табличку/вывеску] точный текст: "[ТЕКСТ]". Сохрани стиль таблички, фон и освещение. Текст должен быть читаемым. Больше текста не добавляй.
```

### Edit: multi-reference character swap
```
Это то же изображение, но возьми персонажа из image 2 и помести рядом с персонажем из image 1. Сохрани реалистичные тени, масштаб и общую атмосферу сцены.
```

---

## API parameters

### Recommended defaults (from official BFL HF Spaces)
| Mode | Steps | guidance_scale | Use for |
|---|---|---|---|
| Distilled | 4 | ~1.0 | Fast previews, interactive |
| Base | 50 | ~4.0 | Final renders, detail/diversity |

### BFL API constraints (klein endpoints)
- `steps` / `guidance` not exposed in klein API (unlike flex) — control via prompt + seed + resolution
- Input: min 64×64, max 4MP (2048×2048), recommended ≤2MP
- Output always multiple of 16; input auto-resized to ×16
- Up to 4 reference images via API
- Result is a signed URL valid **10 minutes** — download immediately

### Available API fields (klein)
`prompt`, `input_image`, `input_image_2..4`, `seed`, `width`, `height`, `safety_tolerance`, `output_format`, `webhook`

---

## Python: BFL API (async polling)

```python
import os, time, requests

BFL_API_KEY = os.environ["BFL_API_KEY"]

# 1. Create task
create = requests.post(
    "https://api.bfl.ai/v1/flux-2-klein-4b",
    headers={"x-key": BFL_API_KEY, "Content-Type": "application/json"},
    json={
        "prompt": 'Это то же изображение, но добавь на вывеску текст "ОТКРЫТО". '
                  "Сохрани фон, освещение и перспективу. Больше текста не добавляй.",
        "input_image": "https://example.com/your-image.png",
        "seed": 42,
        "output_format": "png",
    },
    timeout=60,
)
task = create.json()

# 2. Poll until ready
while True:
    time.sleep(0.5)
    data = requests.get(task["polling_url"], headers={"x-key": BFL_API_KEY}).json()
    if data["status"] == "Ready":
        print("Done:", data["result"]["sample"])  # signed URL
        break
    if data["status"] in ("Error", "Failed"):
        raise RuntimeError(data)
```

## Python: local Diffusers

```python
import torch
from PIL import Image
from diffusers import Flux2KleinPipeline

pipe = Flux2KleinPipeline.from_pretrained(
    "black-forest-labs/FLUX.2-klein-4B", torch_dtype=torch.bfloat16
).to("cuda")

# T2I
image = pipe(
    prompt='Постер "КОФЕ". Жирный гротеск, ровный кернинг, без других надписей.',
    height=1024, width=1024,
    guidance_scale=1.0, num_inference_steps=4,
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]

# Edit (I2I)
base = Image.open("input.png").convert("RGB").resize((1024, 1024))
edited = pipe(
    prompt="Это то же изображение, но замени фон на светлую кухню. "
           "Сохрани объект, освещение и перспективу.",
    image=[base],
    height=1024, width=1024,
    guidance_scale=1.0, num_inference_steps=4,
).images[0]
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Garbled text / glyphs | Text not quoted explicitly | Exact string in quotes; say "no other text" |
| Blurry / artifacts | Distilled 4-step compromise | Switch to Base (50 steps) for finals |
| Style drift in edit | Missing preservation clause | Always add "Сохрани: свет/лицо/композицию" |
| Multi-reference "soup" | Overloaded prompt + conflicting refs | Simplify text; use "image 1 / image 2" indexing |
| Wrong resolution | Input not multiple of 16 | Pre-resize input to ×16, ≤4MP |

---

## Iteration workflow

1. Write scene in prose (one paragraph)
2. Quick preview → Distilled 4 steps
3. Fix seed, pick 1–2 best directions
4. Refine prompt: add specifics, quote text, remove filler adjectives
5. Edit iterations: one change per step, always state what to preserve
6. Switch to Base (50 steps) once composition is stable

---

## Quality metrics (for A/B testing)
- **CLIPScore** — prompt↔image alignment (reference-free)
- **FID** — realism vs real image distribution
- **Human rating** — separate scales for: (a) prompt adherence, (b) quality/realism, (c) text readability, (d) preservation of unchanged parts in edit

---

## Official sources
- Model page: https://bfl.ai/models/flux-2-klein
- Prompting guide: https://docs.bfl.ml/guides/prompting_guide_flux2_klein
- Image editing guide: https://docs.bfl.ai/flux_2/flux2_image_editing
- API reference 4B: https://docs.bfl.ai/api-reference/models/generate-or-edit-an-image-with-flux2-%5Bklein-4b%5D
- HF model card 4B: https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
- HF model card 9B: https://huggingface.co/black-forest-labs/FLUX.2-klein-9B
