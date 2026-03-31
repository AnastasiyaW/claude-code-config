# Schedulers, Samplers и Guidance

## Table of contents
1. Как работает scheduler в Diffusers
2. Обзор schedulers
3. Код: смена scheduler на инференсе
4. Classifier-Free Guidance (CFG)
5. Classifier Guidance (OpenAI)
6. prediction_type
7. Практические советы

---

## 1. Как работает scheduler в Diffusers

Scheduler задаёт **правило обновления** на каждом шаге денойзинга: сколько шума убрать, как обновить образец. Разные schedulers → разные траектории → разные компромиссы speed/quality.

```python
# Посмотреть текущий scheduler
print(pipe.scheduler.config)

# Сменить scheduler (веса модели не меняются)
from diffusers import EulerDiscreteScheduler
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
```

**Важно:** замена scheduler — один из самых дешёвых способов изменить поведение без переобучения.

---

## 2. Обзор schedulers

| Scheduler | Тип | Минимум шагов | Особенности |
|---|---|---|---|
| **DDIM** | ODE (не-марков) | ~20–30 | Детерминированный при `eta=0`; поддерживает inversion |
| **PNDM/PLMS** | Multi-step ODE | ~20–30 | Псевдо-численный; исторически popular в SD-экосистеме |
| **Euler** | ODE (EDM) | ~20–30 | Из EDM design space; широко используется в k-diffusion |
| **Heun** | ODE (2nd order) | ~15–25 | Более точный чем Euler, но 2 NFE/шаг |
| **DPM-Solver / DPM-Solver++** | High-order ODE | **10–20** | Часто лучший баланс steps/quality |
| **LCM** | Distilled | **4–8** | Requires LCM-LoRA или distilled модель |
| **DDPM** | Марковский | 1000 | Оригинал; медленно, обычно не для инференса |

---

## 3. Код: смена scheduler на инференсе

```python
import torch
from diffusers import (
    StableDiffusionPipeline,
    EulerDiscreteScheduler,
    DDIMScheduler,
    PNDMScheduler,
    DPMSolverMultistepScheduler,
)

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

pipe = StableDiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=dtype,
).to(device)

prompt = "реалистичное фото: красный автомобиль на мокрой дороге ночью, неон"
negative = "размыто, артефакты, низкое качество, водяной знак"

# Euler — хороший baseline
pipe.scheduler = EulerDiscreteScheduler.from_config(pipe.scheduler.config)
img = pipe(prompt, negative_prompt=negative,
           num_inference_steps=25, guidance_scale=6.5).images[0]

# DPM-Solver++ — часто лучшее качество за меньше шагов
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
img = pipe(prompt, negative_prompt=negative,
           num_inference_steps=15, guidance_scale=6.5).images[0]

# DDIM — детерминированный, удобен для inversion
pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)
img = pipe(prompt, negative_prompt=negative,
           num_inference_steps=30, guidance_scale=6.5, eta=0.0).images[0]
```

---

## 4. Classifier-Free Guidance (CFG)

**Механизм:** одна модель обучается в двух режимах (conditional + unconditional) через dropout кондиции. На инференсе:

```
noise_pred = unconditional + guidance_scale × (conditional − unconditional)
```

```python
# guidance_scale в стандартном пайплайне
image = pipe(
    prompt=prompt,
    negative_prompt=negative_prompt,  # unconditional направление
    guidance_scale=7.5,               # типичный диапазон: 5–12
    num_inference_steps=25,
).images[0]
```

**Эффект guidance_scale:**
- `1.0` = без guidance (чистый unconditional)
- `5–8` = хороший баланс качество/разнообразие
- `10–15` = высокий adherence к промпту, риск артефактов и «пережога»
- `>15` = обычно артефакты, потеря разнообразия

**Negative prompt** = то, что хотим минимизировать; уходит в unconditional direction.

---

## 5. Classifier Guidance (OpenAI, историческое)

Добавляет **градиент отдельного классификатора** к score-оценке диффузии:

```
score_guided = score_unconditional + γ × ∇_x log p(y|x)
```

- Требует дополнительного классификатора, обученного на зашумлённых данных
- Компромисс «качество ↔ разнообразие» регулируется γ
- В современных пайплайнах почти везде вытеснен CFG (не нужен отдельный классификатор)

---

## 6. prediction_type

Влияет на то, что именно предсказывает модель/солвер. Фиксируется в конфиге scheduler:

| Тип | Что предсказывает | Где используется |
|---|---|---|
| `epsilon` | Добавленный шум ε | DDPM, SD1.x, SDXL |
| `sample` | Исходные данные x₀ | Редко, experimental |
| `v_prediction` | «Velocity» (mix ε и x₀) | SD2.x, некоторые модели |
| `flow_prediction` | Скорость в ODE (flow matching) | Flux, rectified flow |

```python
# Проверить prediction_type текущего scheduler
print(pipe.scheduler.config.prediction_type)
```

---

## 7. Практические советы

**Начальный A/B:**
1. Зафиксировать seed: `generator = torch.Generator().manual_seed(42)`
2. Сравнить Euler 25 шагов vs DPM-Solver++ 15 шагов при одинаковом `guidance_scale`
3. Варьировать `guidance_scale` от 5 до 10 с шагом 1.5

**Когда менять scheduler:**
- Много артефактов/«мусора» → попробовать DPM-Solver++ или Heun
- Нужен inversion (image editing) → DDIM с `eta=0`
- Скорость важнее качества → LCM (нужна distilled модель)
- Distilled модель (Flux klein) → использовать рекомендованный scheduler из model card

**Ссылки:**
- DDIM: https://arxiv.org/abs/2010.02502
- EDM (Euler/Heun basis): https://arxiv.org/abs/2206.00364
- DPM-Solver: https://arxiv.org/abs/2206.00927
- PNDM: https://arxiv.org/abs/2202.09778
- CFG: https://arxiv.org/abs/2207.12598
- Diffusers schedulers overview: https://huggingface.co/docs/diffusers/en/using-diffusers/schedulers
