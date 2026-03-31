# Диффузионные Модели: Архитектура и Инженерия

## Базовые формулировки

**DDPM**: прямой марковский процесс (шум) → денойзер предсказывает шум → обратный процесс
- Цель: MSE(predicted_noise, actual_noise)
- Связь с denoising score matching и Langevin dynamics

**Score-based/SDE**: унификация через SDE/ODE → открывает численные солверы

**Rectified Flow / Flow Matching**: векторное поле в ODE-траектории вместо дискретных шагов → "выпрямление" траекторий, ускорение сэмплинга (Flux.2 klein использует этот подход)

---

## Архитектуры денойзера

### UNet (классика)
- Conditional: sample (латенты) + timestep + encoder_hidden_states (text embeddings [B, L, D])
- Cross-attention — универсальный механизм условности (текст, bbox, и др.)
- В Diffusers: `UNet2DConditionModel`

### DiT (Diffusion Transformer)
- Трансформер на латентных патч-токенах
- Масштабирование: больше Gflops → лучше FID (предсказуемо)
- Conditioning через AdaLN / AdaLN-Zero / cross-attention / in-context токены

### Flux (Flow + Transformer)
- Rectified flow transformer; семейство Flux.2 [klein]: 4B (Apache-2.0) и 9B (non-commercial!)
- Flux.2 klein 9B: **встроен Qwen3 text embedder** — не меняй без полного переобучения
- distilled vs base: distilled быстрее, base гибче

**Выбор backbone**: UNet → проще интеграция с Diffusers; DiT/Flow → лучше масштабирование, но иной профиль памяти и оптимизаций

---

## Компоненты системы (data flow)

```
Промпт → Токенизатор → Text Encoder (CLIP/Qwen) → encoder_hidden_states [B, L, D]
                                                            ↓
Шум/латенты → Scheduler(t=T..1) → Деноизер (UNet/DiT) ← encoder_hidden_states
                                        ↓
                                  Латенты x0 → VAE decode → Изображение

(Для I2I: Изображение → VAE encode → латенты)
```

---

## Text Encoders

| Модель | Encoder | Особенности |
|--------|---------|-------------|
| SD 1.x | CLIP ViT-L/14 (заморожен) | Базовый, 768-dim |
| SDXL | OpenCLIP ViT/G + CLIP ViT/L | Два encoder-а, concat/fusion |
| Flux.2 klein 9B | Qwen3 8B | Встроен, non-commercial |

**Замена text encoder — НЕ plug-and-play:**
1. Другой feature_dim / seq_len → нужен projection head
2. Другое семантическое пространство → text misalignment (текст "игнорируется")
3. Другой токенизатор (BPE/SentencePiece, разная max_length)

**Правильные подходы:**
- Multi-encoder fusion (SDXL-стиль): concat или раздельные K/V в cross-attention
- Новый encoder + projection + дообучение cross-attention/LoRA
- Брать модель, где encoder уже "вшит" (Flux.2 klein 9B)

---

## VAE

- `AutoencoderKL` в Diffusers
- SD 1.x: изображение 512×512 → латенты 4×64×64 (сжатие 8×)
- `scaling_factor`: латенты умножаются при encode, делятся при decode
- KL-регуляризация для непрерывного латентного пространства

---

## Schedulers / Samplers

| Scheduler | Характеристика | Типичное число шагов |
|-----------|---------------|---------------------|
| DDIM | Детерминированный, быстрый | 20-50 |
| PNDM/PLMS | Псевдо-численный, multi-step | 20-50 |
| Euler | EDM-based, простой | 20-30 |
| Heun | EDM, 2-й порядок | 15-25 |
| DPM-Solver | Высокий порядок | 10-20 |

Разные schedulers → разные результаты при одинаковых весах.

---

## Guidance (CFG)

- **Classifier-Free Guidance**: одна модель, conditional + unconditional prediction
- Инференс: `noise = unconditional + guidance_scale * (conditional - unconditional)`
- `guidance_scale` ↑ → лучше соответствие промпту, но меньше разнообразие + артефакты ("пережог")
- CFG-обучение: дроп кондиции (~10-20% батча) → модель умеет оба режима

---

## Дообучение: сравнение методов

| Метод | Что меняется | Память | Когда использовать |
|-------|-------------|--------|-------------------|
| Full fine-tune | Все веса | Много | Максимальная адаптация |
| **LoRA** | Low-rank матрицы в attention | Мало | **Старт всегда** |
| DreamBooth | Все веса + prior preservation | Много | 3-5 фото субъекта |
| Textual Inversion | Один токен-вектор | Очень мало | Лёгкая персонализация |
| Adapter layers | Малые модули | Средне | Компромисс |

**Мини-LoRA вручную:**
```python
class LoRALinear(nn.Module):
    def __init__(self, base, r=8, alpha=16.0):
        super().__init__()
        self.base = base
        for p in self.base.parameters(): p.requires_grad = False
        self.scaling = alpha / r
        self.A = nn.Linear(base.in_features, r, bias=False)
        self.B = nn.Linear(r, base.out_features, bias=False)
        nn.init.kaiming_uniform_(self.A.weight, a=math.sqrt(5))
        nn.init.zeros_(self.B.weight)

    def forward(self, x):
        return self.base(x) + self.B(self.A(x)) * self.scaling
```

---

## Память при обучении

VRAM = веса + градиенты + состояния оптимизатора + активации

| Техника | Эффект | Когда |
|---------|--------|-------|
| AMP (BF16/FP16) | -50% активации, быстрее | Всегда |
| Activation checkpointing | -память, +время | При нехватке памяти |
| ZeRO-2 | Шардинг оптимизатора | Multi-GPU |
| ZeRO-3 + Offload | Всё на CPU/NVMe | Очень большие модели |
| FSDP | Шардинг параметров | Multi-GPU, PyTorch-нативно |
| LoRA | Меньше trainable params | Одиночный GPU |

```python
# AMP + activation checkpointing
scaler = torch.amp.GradScaler("cuda")
with torch.autocast(device_type="cuda", dtype=torch.float16):
    y = checkpoint(block, x)  # torch.utils.checkpoint
    loss = F.mse_loss(y, target)
scaler.scale(loss).backward()
scaler.step(opt); scaler.update()
```

---

## Бюджеты

**Малый (1 GPU 8-16GB):** LoRA + grad accumulation + BF16 + xFormers/SDPA + 8-bit оптимизатор

**Средний (1-4 GPU 24-48GB):** LoRA или partial fine-tune + FSDP + большее разрешение

**Большой (8+ GPU H100):** Full fine-tune + ZeRO-3/FSDP + float8 эксперименты + WebDataset стриминг

---

## Диагностика

| Симптом | Причина | Фикс |
|---------|---------|------|
| NaN/взрыв loss | LR слишком большой, AMP | Снизить LR, проверить GradScaler |
| "Текст игнорируется" | Низкий CFG или несогласованный encoder | Поднять guidance_scale; не менять encoder без адаптации |
| Потеря разнообразия | Слишком высокий CFG | Снизить guidance_scale |
| Шумы при малом числе шагов | Неподходящий sampler | Euler/Heun/DPM-Solver + больше steps |
| OOM при обучении | Нет AMP/checkpointing | Включить AMP + checkpointing + LoRA |

---

## Метрики

- **FID** — распределение реализма (не alignment к промпту)
- **CLIPScore** — text↔image alignment (reference-free)
- **LPIPS** — перцептивное сходство
- **IS** — Inception Score

Практически: FID хорош для "реалистичности распределения", CLIPScore — для alignment, но не заменяет human eval.

---

## Дата-пайплайн

- HF Datasets streaming → IterableDataset без полного скачивания (Arrow backend)
- WebDataset (TAR shards) — стандарт для больших image-text корпусов
- DataLoader: `num_workers`, `prefetch_factor`, `persistent_workers`
- Кэшировать text embeddings если encoder заморожен (как в SD-классе)

---

## Ключевые источники

- DDPM: https://arxiv.org/abs/2006.11239
- Score-based SDE: https://arxiv.org/abs/2011.13456
- DDIM: https://arxiv.org/abs/2010.02502
- Improved DDPM: https://arxiv.org/abs/2102.09672
- EDM: https://arxiv.org/abs/2206.00364
- CFG: https://arxiv.org/abs/2207.12598
- LDM (Stable Diffusion): https://arxiv.org/abs/2112.10752
- DiT: https://arxiv.org/abs/2212.09748
- Rectified Flow: https://arxiv.org/pdf/2209.03003
- SDXL: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
- Flux.2 klein 4B (Apache-2.0): https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
- Flux.2 klein 9B (non-commercial): https://huggingface.co/black-forest-labs/FLUX.2-klein-9B
- Diffusers schedulers: https://huggingface.co/docs/diffusers/en/using-diffusers/schedulers
- Diffusers LoRA: https://huggingface.co/docs/diffusers/en/training/lora
- Diffusers memory: https://huggingface.co/docs/diffusers/en/optimization/memory
- PyTorch AMP: https://docs.pytorch.org/docs/stable/amp.html
- Activation checkpointing: https://docs.pytorch.org/docs/stable/checkpoint.html
- DeepSpeed ZeRO: https://deepspeed.readthedocs.io/en/latest/zero3.html
- PyTorch FSDP: https://docs.pytorch.org/docs/stable/fsdp.html
