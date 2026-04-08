# 12 - Low-Signal Residual Training: Traps and Solutions

**Source:** Retouch overlay prediction training (2026-04-02 to 2026-04-08), 4 rounds of failure + sweep analysis.

## Overview

"Low-signal residual" tasks predict **small deviations from a constant baseline**. Examples:
- Dodge&Burn overlay maps (residuals std ~1% of pixel range)
- Denoising residuals (noise component on clean image)
- Color correction deltas (tiny shifts in LAB)
- Seismic residuals after baseline subtraction
- Any task where "predict zero" scores well on naive metrics

The defining property: **most of the target is near-constant, with small but important deviations at specific pixels**. This combination traps naive training approaches in ways that look like success but aren't.

---

## Trap 1: The "Predict Zero" Attractor

**Symptom**: loss drops fast, model visually outputs flat gray, metrics look OK.

**Cause**: If target std is 0.013 and your model predicts 0.000, L1 loss is 0.013 - lower than any imperfect prediction of real structure. The optimizer finds the constant solution and stays there. TV regularization *accelerates* this collapse by penalizing any non-constant prediction.

**Why pretrained encoders collapse faster**: ImageNet-pretrained features are tuned for high-variance inputs. When decoder learns "output = constant", backprop drives encoder features toward mush to minimize disagreement with the constant decoder.

### Fix: Signal amplification in the dataset, not the loss

```python
# WRONG: amplify in loss function
loss = mse_loss(pred * 10, target * 10)  # Gradients explode ×100

# RIGHT: amplify targets in dataset
class Dataset:
    def __getitem__(self, i):
        target_residual = (target - neutral) * AMPLIFY_FACTOR
        return input, target_residual
```

Why this matters: amplifying in loss creates gradient spikes (∇L ∝ amp²). Amplifying in data gives the model a training distribution with healthy signal magnitude, and optimizer behaves normally.

**Sweet spot is surprisingly low**: experiments with amp={1,3,5,10,20} showed amp=5 wins by pixel MAE, while amp=10-20 causes instability. Start at amp=3-5, not higher.

---

## Trap 2: PSNR That Lies About Amplified Space

**Symptom**: val_psnr metric shows big differences between configs (e.g. 30 dB vs 20 dB) that don't match visual or pixel-level comparison.

**Cause**: Standard PSNR formula `10*log10(data_range² / MSE)` assumes `data_range=1`. If you amplified targets ×N, the effective data range is ±N/2 (not 1), but your code still uses `data_range=1`. This makes PSNR artificially inflated for high-amp configs:

```
PSNR_logged = 10*log10(1 / MSE_amplified)
PSNR_real   = 10*log10(1 / MSE_unamplified)
            = PSNR_logged + 20*log10(amplify_factor)
```

Two configs with different amp can have identical real PSNR but 20+ dB difference in logged PSNR.

### Fix: Pass amplify_factor into PSNR computation

```python
def compute_psnr(pred, target, amplify_factor=1.0):
    mse_amplified = F.mse_loss(pred, target).item()
    mse_unamplified = mse_amplified / (amplify_factor ** 2)
    return 10.0 * np.log10(1.0 / mse_unamplified)
```

**Better yet**: track pixel-space MAE directly. It's interpretable ("how far off are we on average") and comparable across configurations.

---

## Trap 3: Lossy Targets Poison Training

**Symptom**: model outputs look blurry or learn artifacts that are not in the true signal.

**Cause**: JPEG compression introduces ~0.5-1% pixel noise. When your residual signal is std=1.3%, JPEG noise is **50-100% of the signal magnitude**. The model cannot tell your signal apart from quantization noise, so it learns both.

### Fix: Lossless targets (PNG for integer, EXR for float)

Keep inputs as JPEG if size matters - noise on inputs works as implicit augmentation. But **targets must be lossless**. Convert existing JPEG targets in place:

```python
# Fast parallel conversion, deletes originals
for jpg in target_dir.glob("*.jpg"):
    img = cv2.imread(str(jpg), cv2.IMREAD_UNCHANGED)
    cv2.imwrite(str(jpg.with_suffix('.png')), img)
    jpg.unlink()
```

---

## Trap 4: Saturation Wrappers Kill Outlier Learning

**Symptom**: model learns most of the structure but completely misses the brightest/darkest corrections.

**Cause**: Wrappers like `output = tanh(raw) * 0.5` saturate gradients for outputs near the edges. If 96% of pixels want output near 0 and 4% want output near ±0.4, the tanh gradient at ±0.4 is ~0.4 (vs 1.0 near zero), so the outlier pixels learn 2.5× slower than the bulk. They never catch up.

### Fix: Use clamp or no wrapper at all

```python
# WRONG: saturates gradients
def forward(self, x):
    return torch.tanh(self.model(x)) * 0.5

# RIGHT: linear within range, hard boundary outside
def forward(self, x):
    return torch.clamp(self.model(x), -self.max_val, self.max_val)
```

With amplified targets in [-1, 1], `clamp(±1.5)` gives headroom without losing gradients anywhere inside the active range.

---

## Trap 5: Subject Background Pollution

**Symptom**: 30-50% of your training tiles are pure background (walls, sky, floor). Model rewards for doing nothing.

**Cause**: Datasets often have the subject in the center of the frame. Naive tiling cuts as many background tiles as subject tiles. Background tiles have zero useful signal for a residual task - the correct answer is literally "predict zero", which is the trap from Trap 1.

### Fix: Subject detection + crop before tiling

```python
# Use YOLOv8 or similar on the INPUT image
detections = yolo.detect(input_img, class='person')
if detections:
    bbox = union_bbox(detections) + padding  # e.g. 15%
    # Apply SAME bbox to input, target, mask
    input_cropped = input_img[bbox.y1:bbox.y2, bbox.x1:bbox.x2]
    target_cropped = target_img[bbox.y1:bbox.y2, bbox.x1:bbox.x2]
```

Expected: 20-40% pixel reduction, much higher signal density. Convergence drastically faster.

---

## Trap 6: Warmup and EMA Timing

**Symptom**: loss diverges or NaN in first few epochs; or model is worse than epoch 0 at epoch 10.

**Cause A (no warmup)**: Full learning rate from step 0 destroys pretrained features before the decoder learns to use them. Random-init models (NAFNet, Restormer) amplify this into NaN explosions because there are no stable features to anchor optimization.

**Cause B (EMA from epoch 0)**: Exponential Moving Average of weights starting at epoch 0 averages a random decoder with the trained decoder. The average is worse than both. With `decay=0.999`, it takes 1000+ steps for the random initialization to wash out.

### Fix: Warmup + delayed EMA

```python
# Warmup: LR ramps 1% → 100% over first N epochs
warmup = LinearLR(opt, start_factor=0.01, end_factor=1.0, total_iters=5)
cosine = CosineAnnealingLR(opt, T_max=epochs - 5, eta_min=1e-7)
scheduler = SequentialLR(opt, [warmup, cosine], milestones=[5])

# EMA: lazy init after epoch N, when decoder has stabilized
if epoch >= ema_start_epoch:
    if ema_model is None:
        ema_model = AveragedModel(model, decay=0.999)
    else:
        ema_model.update_parameters(model)
```

Rule of thumb: warmup_epochs = 5 for pretrained encoders, 10+ for random-init architectures. EMA start = same as warmup end.

---

## Trap 7: Loss Asymmetry on Bipolar Residuals

**Symptom**: model learns one side of the distribution (e.g., bright corrections) but completely misses the other side (e.g., dark corrections). Metrics look reasonable because the missed side contributes less to mean error. Visual inspection reveals the gap.

**Cause**: When residuals are bipolar (both positive and negative deviations from baseline), L2 gradient `2 × error` scales with error magnitude. If one side of the distribution has larger typical deviations than the other, L2 prioritizes the larger side and effectively ignores the smaller one. The model converges to predict "zero" for the smaller-magnitude side, which still reduces loss because most pixels there are near zero anyway.

This is distinct from Trap 1 (Predict Zero Attractor). Trap 1 is global collapse. Trap 7 is **half collapse**: the model learns structure on one side, zero on the other.

Examples:
- **Dodge & Burn overlays**: artists apply brighter dodges (+5%) and darker burns (-2%) - the +5% side dominates L2 gradients
- **Temperature shifts**: warming edits typically more aggressive than cooling
- **Sharpening residuals**: positive overshoots often stronger than negative undershoots
- Any residual with asymmetric magnitude distribution

**Diagnosis**: Enhance contrast of GT target and model prediction separately (`×5-10`). If GT shows both bright and dark corrections but prediction shows only bright (or only dark), you have this trap. MAE might be acceptable because the missing side contributes less absolute error, but visually the output is wrong.

### Fix: L1 or Huber loss instead of L2

```python
# WRONG for bipolar residuals
criterion = nn.MSELoss()  # grad ∝ error magnitude → biased toward larger side

# RIGHT: L1 treats + and - equally regardless of magnitude
criterion = nn.L1Loss()  # grad = ±1 constant

# ALSO RIGHT: Huber - L2 smoothness near zero, L1 robustness on tails
criterion = nn.HuberLoss(delta=0.1)
```

**L1 caveat**: Can NaN during warmup at high amplify factor because constant gradients don't scale down on small errors. Use gradient clipping (`clip_grad_norm=1.0`) and lower LR if L1 spikes.

**Huber recommendation**: Best general-purpose choice for bipolar residuals. You get L2's smooth convergence near zero AND L1's equal treatment of both sides on outliers. Survives warmup more reliably than pure L1.

**Active pixel weighting** as an alternative: keep L2 but weight pixels with `|target| > threshold` higher. This forces attention on non-neutral pixels regardless of sign. Experimentally: works BETTER than L1/Huber on **complex scenes** with dense corrections (many active pixels per tile), WORSE on **sparse scenes** where L1/Huber remain more balanced.

### The Two-Stage Diagnostic

1. **Check metric**: does MAE or PSNR look OK?
2. **Check visual**: enhance contrast ×8 on GT and prediction. Look at both sides.
   - If both sides present in both: loss is fine
   - If prediction missing one side: switch to L1/Huber

Don't skip step 2. Metrics can look great while the model is silently ignoring half the signal.

---

## Which Loss?

**L2 (MSE)**: Standard default. Works on **symmetric** residual distributions. **Fails on bipolar/asymmetric** distributions (Trap 7): grad ∝ magnitude biases toward the larger side. Wins on metrics but loses half the signal.

**L1**: Constant gradient ±1 treats both sides equally. Best for **bipolar residuals** like Dodge&Burn. **Caveat**: can NaN during warmup at high amplify; may recover within a few epochs. Use gradient clipping.

**Huber**: Best general-purpose choice for low-signal bipolar tasks. L2 smooth convergence near zero + L1 balanced treatment on outliers. **Most stable** of the three in our sweep - never NaN'd. Slightly behind pure L1 on final metric but visually preserves both sides of distribution.

**Active weighting** (L2 + weight pixels with |target| > threshold higher): initial assumption was "doesn't help". **Revised after visual inspection**: helps on **complex scenes with dense active pixels** (details, contrast, intricate body poses). Hurts or is neutral on **sparse scenes** (simple subject, mostly empty background). Consider **scene-adaptive routing** if your dataset is heterogeneous.

**Key learning**: For bipolar residual prediction, the right loss depends on **your data distribution**, not just theoretical properties. Run a parallel sweep (L2, L1, Huber, L2+active) on 5-10 epochs, compare by **visual contrast enhancement** (not just metrics), pick winner per-scene-type or pick Huber as safe default.

---

## Diagnostic Checklist

When a low-signal residual training underperforms, check in this order:

1. **Is the model outputting constant?** Visualize a prediction with contrast enhancement (×5-10). If it's all one color, you have the Trap 1 collapse.
2. **Are targets lossless?** Check file extensions and sizes. JPEG targets = Trap 3.
3. **Is there a saturation wrapper?** Grep for `tanh`, `sigmoid` in the model output. Trap 4.
4. **What's the pixel MAE vs val_psnr?** If they disagree, you have the Trap 2 metric lie. Fix PSNR or trust MAE.
5. **How much of each tile is background?** Sample 20 tiles visually. If most are empty, you have Trap 5.
6. **When did val_loss diverge?** If epoch 1-3, you likely have warmup problems. If later, it's overfitting - look at the train/val gap.
7. **What amp factor?** Start at 3-5. Higher is not better. Test with a small sweep.
8. **Compare enhanced prediction vs enhanced GT side-by-side.** Does the prediction capture BOTH sides of the bipolar signal? If GT has bright highlights AND dark shadows but prediction shows only one side, you have Trap 7 - switch to L1 or Huber loss.

---

## Quick Reference Config

Known-good config for low-signal residual training (U-Net + EfficientNet-B4, ImageNet pretrained):

```yaml
model:
  clamp_max: 1.0          # no tanh
  encoder: efficientnet-b4
  encoder_weights: imagenet

data:
  amplify_factor: 5.0     # sweet spot, not 20
  targets_format: png     # lossless

loss:
  loss_fn: huber          # bipolar residuals - L2 loses half the signal (Trap 7)
  active_weight: 0.0      # 0 for sparse scenes, 3-5 for dense detailed scenes
  tv_weight: 0.0          # TV kills low-signal learning

training:
  lr: 5.0e-4
  warmup_epochs: 5
  ema_start_epoch: 5
  batch_size: 16
  clip_grad_norm: 1.0     # just in case (required for L1)
```

This config came from a sweep that tested 7 variations in parallel over 10 epochs on 2.1M tiles, after 4 rounds of collapse failures on incorrect configurations. The loss choice was determined by **visual contrast enhancement** of epoch 4 predictions vs ground truth, not by metrics alone - the metric-based winner (L2 amp5) was visually worst because it learned only one side of the bipolar distribution.

---

## Sources

- Direct experimental results, retouch project 2026-04-02 to 2026-04-08
- 4 rounds of training failure (tanh, JPEG targets, amp-in-loss, amp=20, no warmup, EMA from epoch 0)
- 7-config parallel sweep on 6× H200 GPUs
- Pixel MAE vs val_psnr disagreement analysis revealed metric bug in compute_psnr
