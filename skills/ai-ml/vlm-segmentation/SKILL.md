---
name: vlm-segmentation-engineering
description: >
  Экспертный скилл по прикладной инженерии VLM, сегментационных моделей и диффузионных архитектур
  для GPU-деплоя. Используй ВСЕГДА когда речь идёт о: SAM2, SAM3, Florence-2, LLaVA, Grounding DINO,
  OWLv2, YOLO-World, EdgeTAM — выбор модели, интеграция, pipeline, код; диффузионных моделях —
  UNet/DiT/Flow/Flux, schedulers, LoRA, AMP, ZeRO/FSDP, text encoders (CLIP/Qwen), VAE, CFG;
  GPU-деплое — MIG, MPS, torch.compile, TorchAO, Triton, memory optimization, два инстанса на H100;
  open-vocab сегментации и phrase grounding; part-level labeling и instance masks из текстового промпта;
  замене/fusion текст-энкодеров; fine-tune/LoRA/DreamBooth диффузионных моделей.
  Триггеры: SAM, Florence, LLaVA, Grounding DINO, YOLO-World, diffusion, UNet, DiT, Flux, LoRA,
  scheduler, guidance_scale, VAE, CLIP embeddings, Qwen embedder, MIG, MPS, TorchAO, Triton inference,
  сегментация по тексту, instance masks, open-vocab detection, text-conditioned segmentation.
---

# VLM + Segmentation + Diffusion Engineering

Скилл охватывает три тесно связанных домена. Выбери нужный раздел и загрузи соответствующий reference-файл.

## Навигация по доменам

| Задача | Reference файл |
|--------|---------------|
| Выбор модели сегментации, pipeline "текст → маски", VLM-стек, part-labeling | `references/vlm-segmentation.md` |
| Диффузионные архитектуры, schedulers, обучение, LoRA, text encoder fusion | `references/diffusion-engineering.md` |
| Два инстанса SAM3 на H100, MIG/MPS, memory, профилирование | `references/gpu-deployment.md` |

**Правило выбора:** если вопрос смешивает темы (например, "как деплоить диффузионную модель на H100") — прочитай оба релевантных файла.

---

## Быстрые ответы без чтения reference-файлов

### Рекомендованный pipeline "фраза → маски" (дефолт)
```
1. SAM3 PCS (текстовый концепт) → instance masks + boxes + scores
   ИЛИ
   Grounding DINO / OWLv2 / YOLO-World → boxes → SAM2.1 → masks

2. Part-labeling: отдельный классификатор по ROI + фиксированный словарь
```

### Рекомендованный pipeline "диффузия" (дефолт)
```
1. Backbone: UNet (просто) или DiT/Flow (масштабирование)
2. Latent diffusion (VAE → латенты → денойзер → VAE decode)
3. Text encoder: CLIP (SD), два CLIP (SDXL), Qwen3 (Flux.2 klein 9B)
4. Fine-tune: начинать с LoRA, full fine-tune только если нужно
5. Memory: AMP (BF16) → checkpointing → ZeRO/FSDP при масштабе
```

### Два инстанса SAM3 на H100 (дефолт)
```
MIG (рекомендовано) → аппаратная изоляция, QoS гарантирована
sudo nvidia-smi mig -cgi 4g.40gb,3g.40gb -C
CUDA_VISIBLE_DEVICES=<MIG-UUID> python worker.py

MPS (fallback) → кооперативный шеринг, без строгой изоляции
```

---

## Ключевые характеристики моделей (быстрая справка)

| Модель | Параметры | Лицензия | Главная сильная сторона |
|--------|-----------|----------|------------------------|
| SAM3 | 848M | SAM License (gated) | Open-vocab сегментация по тексту, все инстансы |
| SAM2.1-large | 224M | Apache-2.0 | Видео-трекинг, интерактивная сегментация, 39.5 FPS A100 |
| SAM2.1-tiny | 39M | Apache-2.0 | Быстрый, 91.2 FPS A100 |
| Florence-2-large | 770M | MIT | Унифицированные задачи через task prompt |
| EdgeTAM | ~SAM2-tiny | Apache-2.0 | 16 FPS на iPhone 15 Pro Max, CoreML |
| Grounding DINO | — | Apache-2.0 | Text-conditioned detection, boxes |
| YOLO-World | — | GPL-3.0 | Real-time open-vocab OD, 52 FPS V100 |

---

## Критические предупреждения

- **SAM3**: gated access на HF, кастомная SAM License — проверь перед продакшном
- **YOLO-World**: GPL-3.0 в репо — для коммерции нужна отдельная лицензия
- **Замена text encoder**: не plug-and-play, нужен projection + переобучение cross-attention
- **MIG vs MPS**: только MIG даёт аппаратную изоляцию VRAM/SM; MPS — кооперативный шеринг
- **Русский язык в промптах**: для Grounding DINO / OWLv2 / YOLO-World надёжнее EN + маппинг на RU
