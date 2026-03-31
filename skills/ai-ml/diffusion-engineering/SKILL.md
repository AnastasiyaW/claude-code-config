---
name: diffusion-engineering
description: >
  Практическая инженерия диффузионных моделей: архитектуры, обучение, инференс,
  оптимизация памяти. Использовать при любых задачах с диффузионными моделями:
  проектирование или модификация архитектуры (UNet/DiT/Flow/Flux), выбор и настройка
  schedulers/samplers, дообучение (LoRA/DreamBooth/full fine-tune), оптимизация памяти
  (AMP/checkpointing/ZeRO/FSDP/quantization), замена или fusion текст-энкодеров (CLIP/Qwen),
  работа с Diffusers, отладка диффузионных пайплайнов, оценка качества (FID/CLIPScore/LPIPS),
  latent diffusion, VAE, guidance/CFG, rectified flow, Stable Diffusion, SDXL, Flux.
  Также применять при вопросах про GPU-память при обучении генеративных моделей,
  text-to-image пайплайны, ControlNet, multi-encoder fusion, WebDataset.
---

# Diffusion Engineering Skill

## Быстрая ориентация

Три инженерных решения, которые больше всего влияют на качество/скорость/стоимость:

1. **Где идёт диффузия** → пиксели (дорого) или латентное пространство (LDM/SD-семейство — практично)
2. **Backbone денойзера** → UNet (классика, проще) или Transformer/DiT/Flow (масштабируется лучше)
3. **Управление сэмплингом** → scheduler, число шагов, guidance_scale — часто дают больше, чем правка сети

---

## Reference files — читать по задаче

| Тема | Файл | Когда читать |
|---|---|---|
| Архитектуры и data flow | `references/architectures.md` | DDPM/SDE/LDM/DiT/Flux/VAE/SDXL, схема пайплайна |
| Schedulers и guidance | `references/samplers.md` | DDIM/Euler/Heun/DPM-Solver/PNDM, CFG, prediction_type |
| Обучение и дообучение | `references/training.md` | Loss/цели, LoRA/DreamBooth/full FT, гиперпараметры |
| Память и распределённость | `references/memory.md` | AMP, checkpointing, ZeRO, FSDP, quantization, FP8 |
| Текст-энкодеры и данные | `references/encoders-data.md` | CLIP/Qwen/multi-encoder, токенизация, data pipeline |
| Оценка и траблшутинг | `references/eval-debug.md` | FID/CLIPScore/LPIPS, типовые поломки и фиксы, лицензии |

---

## Быстрый чеклист «я строю/модифицирую diffusion»

- [ ] **Backbone:** UNet (проще) или DiT/Flow (масштабирование)?
- [ ] **Модули зафиксированы:** tokenizer → text encoder → `encoder_hidden_states` → denoiser → VAE decode
- [ ] **Scheduler выбран:** DDIM / Euler / DPM-Solver — A/B на фиксированных seed
- [ ] **Дообучение:** начинать с LoRA, в full fine-tune только при необходимости
- [ ] **Память:** AMP включён, при необходимости checkpointing, при масштабе ZeRO/FSDP
- [ ] **Данные:** стриминг/шардинг (HF streaming, WebDataset), валидировать throughput dataloader
- [ ] **Оценка:** FID + CLIPScore + LPIPS + human rating; отдельно дневник промптов для overfitting

---

## Trade-offs на один экран

| Ручка | Увеличить | Уменьшить |
|---|---|---|
| `num_inference_steps` | ↑ качество | ↑ время |
| `guidance_scale` (CFG) | ↑ adherence к промпту, риск «пережога» | ↑ разнообразие |
| LoRA rank | ↑ выразительность | ↑ параметры, риск overfitting |
| Шаги дообучения | ↑ адаптация | ↑ риск catastrophic forgetting |
| Batch size | ↑ стабильность градиентов | ↑ VRAM |

---

## Мини-рецепты по бюджету GPU

| Бюджет | Что делать |
|---|---|
| **8–16 GB (1 GPU)** | LoRA вместо full FT; grad accumulation; BF16/FP16; xFormers/SDPA; 8-bit оптимизатор |
| **24–48 GB (1–4 GPU)** | LoRA или partial FT; иногда FSDP; большее разрешение |
| **8+ GPU, H100** | Full FT, ZeRO-3/FSDP, float8, WebDataset стриминг, масштабный датапайплайн |
