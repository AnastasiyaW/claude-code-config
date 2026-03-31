# Архитектуры диффузионных моделей

## Table of contents
1. DDPM и score-based/SDE
2. Latent Diffusion (LDM)
3. Условный UNet — data flow
4. DiT (Diffusion Transformers)
5. Rectified Flow / Flow Matching (Flux)
6. VAE/AutoencoderKL
7. Каскадные пайплайны
8. Способы впрыска условности
9. Полный data flow схема

---

## 1. DDPM и score-based/SDE

**DDPM** — прямой марковский процесс добавления гауссовского шума + нейросеть-денойзер, которая учится предсказывать шум (или эквивалентные параметризации) для обратного процесса.

**Score-based/SDE** — обобщение через стохастические дифференциальные уравнения: диффузионные модели описываются как SDE/ODE, что открывает путь к численным ODE/SDE-самплерам и унифицирует многие варианты.

Связь с denoising score matching и Langevin dynamics:
- Обучение = взвешенный вариационный нижний предел (VLB)
- `prediction_type` = `epsilon` (предсказать шум) — классика DDPM
- Альтернативы: `sample`, `v_prediction`, `flow_prediction`

---

## 2. Latent Diffusion (LDM)

Ключевая идея: диффузия происходит **в латентном пространстве** автоэнкодера, а не в пикселях.

```
Пиксели → VAE.encode() → латенты (меньше H/W, больше каналов)
                                    ↓
                           Диффузия в латентах
                                    ↓
Пиксели ← VAE.decode() ← денойзированные латенты
```

**Зачем:** радикально снижает вычислительную стоимость при сохранении качества. SD1.x: латенты `(B, 4, H/8, W/8)` вместо `(B, 3, H, W)`.

**Cross-attention** в LDM — универсальный механизм впрыска условности (текст, bbox, и др.).

---

## 3. Условный UNet — data flow

В Diffusers `UNet2DConditionModel` принимает:

```python
noise_pred = unet(
    sample,                    # (B, C, H, W) — зашумлённые латенты
    timestep,                  # (B,) — шаг диффузии
    encoder_hidden_states,     # (B, L, D) — текстовые эмбеддинги из text encoder
).sample
```

Типичные размерности для SD1.x:
- `sample`: `(B, 4, 64, 64)` для 512×512
- `encoder_hidden_states`: `(B, 77, 768)` — CLIP ViT-L/14

---

## 4. DiT (Diffusion Transformers)

**Замена UNet на Transformer**, работающий по латентным «патч-токенам».

**Ключевые свойства:**
- Масштабируется предсказуемо: больше Gflops (глубина/ширина/токены) → лучше FID
- Условность через **AdaLN / AdaLN-Zero**: timestep и class/text генерируют scale/shift для LayerNorm
- Альтернативы впрыска условности: cross-attention, in-context токены

**Варианты блок-дизайна (из DiT-paper):**
- `In-context` — кондиция как дополнительные токены последовательности
- `Cross-attention` — текст через отдельный cross-attention слой
- `AdaLN` — adaptive LayerNorm из кондиции
- `AdaLN-Zero` — то же + инициализация нулями (стабильнее)

---

## 5. Rectified Flow / Flow Matching (Flux)

**Идея:** вместо дискретного обратного марковского процесса учится **векторное поле/скорость** в ODE-траектории. «Выпрямление» траекторий ускоряет сэмплинг.

**FLUX.2 [klein]** — rectified flow transformer:
- 4B — distilled, Apache 2.0, быстрее
- 9B — base, non-commercial, гибче, с **Qwen3 text embedder**
- Поддерживает T2I и multi-reference editing

**Distilled vs Base:**
- Distilled: меньше шагов, быстрее, но менее гибкий (хуже реагирует на изменение scheduler/steps)
- Base: больше шагов, лучше реагирует на `guidance_scale`/scheduler

---

## 6. VAE / AutoencoderKL

```python
from diffusers import AutoencoderKL

vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse")

# Encode: пиксели → латенты
latents = vae.encode(pixel_images).latent_dist.sample()
latents = latents * vae.config.scaling_factor  # нормализация

# Decode: латенты → пиксели
pixel_images = vae.decode(latents / vae.config.scaling_factor).sample
```

**scaling_factor** (~0.18215 для SD1.x) — нормализация латентов перед подачей в UNet.

---

## 7. Каскадные пайплайны

Паттерн: low-res диффузия → upsampling диффузия/refiner.

**SDXL:** base + refiner
- Base: `(B, 4, 128, 128)` латенты для 1024×1024
- Refiner: дорабатывает последние шаги денойзинга
- Base использует **два text encoder**: OpenCLIP ViT/G + CLIP ViT/L
- Refiner использует только OpenCLIP

**Imagen:** диффузия + T5 encoder + upsampling-диффузионные модули. Урок: сильный text-only LLM энкодер (T5) резко улучшает text understanding.

---

## 8. Способы впрыска условности

| Метод | Как работает | Когда применять |
|---|---|---|
| **Cross-attention** | Текстовые токены → K/V; визуальные фичи → Q | Стандарт для текстовой условности в LDM/UNet |
| **Concat** | Кондиционирующие карты как доп. входные каналы | Spatial условности: depth/edges/pose (ControlNet) |
| **FiLM** | Кондиция генерирует scale/shift для фич-каналов | Компактная модуляция признаков |
| **AdaLN/AdaLN-Zero** | Adaptive LayerNorm от timestep/condition | DiT-архитектуры, трансформеры |
| **AdaIN** | Adaptive Instance Norm | Style transfer компонент |
| **In-context токены** | Кондиция как дополнительные токены seq | Простое добавление в трансформер |

---

## 9. Полный data flow

```
Текстовый промпт
    → Токенизация
    → Text Encoder (CLIP/T5/Qwen)
    → encoder_hidden_states (B, L, D)
                                        ┐
Изображение (опц.)                      │
    → VAE.encode() → латенты            ├→ Деноизер (UNet или DiT)
                                        │      ↕ (T шагов)
Шум/начальные латенты                   │  Scheduler
    → t = T..1 ──────────────────────── ┘
                    ↓
              Латенты x0
                    ↓
              VAE.decode()
                    ↓
              Изображение
```

**Ключевые sources:**
- DDPM: https://arxiv.org/abs/2006.11239
- Score-based/SDE: https://arxiv.org/abs/2011.13456
- LDM: https://arxiv.org/abs/2112.10752
- DiT: https://arxiv.org/abs/2212.09748
- Rectified Flow: https://arxiv.org/pdf/2209.03003
- FLUX.2 [klein] 4B: https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
- FLUX.2 [klein] 9B: https://huggingface.co/black-forest-labs/FLUX.2-klein-9B
