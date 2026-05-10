# Three Prompt Registers

The same scene can be described in three completely different registers depending on the consumer. Match the register to the consumer or the output is wasted.

---

## Register 1: LLM agent (Claude generating canvas program)

**Style**: explicit, parameter-heavy, machine-friendly. **Constraints first.**

The agent will translate this into a `draw{Name}(ctx, W, H, t)` function. Every ambiguity in your prompt becomes a creative-license decision the agent has to make — most of which it will get wrong. Lock the parameters explicitly.

**Example prompt:**
```
Generate a canvas pixel-art animation function.

Canvas: 64x96 logical pixels, scaled 4x via image-rendering: pixelated.
Output: drawCabin(ctx, W, H, t) where t in [0, 1) is the loop phase.

Subject: log cabin centered lower-third.
  - Cabin: 16 wide, 12 tall, dark brown wood, single bright window
  - Chimney: 2 wide on left side
  - Door: 4 wide centered

Setting: 3 depth layers from back to front:
  - Far: full moon upper-right, 6 pixel star field
  - Mid: pine forest silhouette, 24-pixel-tall ridge
  - Near: snow-covered ground, 12-pixel-tall

Lighting: cool moonlight ambient + single warm rectangle from cabin window.

Palette (6 colors, exact hex):
  midnight  #0a0e1c
  pine      #1a2a18
  snow      #d8e0f0
  cabin     #3a2418
  amber     #ffb060
  moon      #fff8e0

Motion (loop period 8000ms):
  - Smoke plume from chimney: 4-frame meander, fades at top
  - Window light: gentle 7-second flicker (sin wave * 0.15 brightness shift)
  - Snow particles: 12 particles drifting diagonally, deterministic via hash(seed)

Render method:
  - ctx.fillRect(x|0, y|0, 1, 1) per pixel
  - All animation derives from t, no Math.random() in render path
  - Use sin/cos for cyclic motion, hash(i) for per-particle seed
```

**When to use**: when generating the canvas program from a description, OR when the agent needs to reproduce a scene programmatically from spec.

---

## Register 2: Human pixel artist (commission brief)

**Style**: atmospheric, emotional, narrative. Trust the artist for technical details.

A pixel artist knows palette discipline, animation principles, and timing. What they need from you is the *intent* — what does this scene make the viewer feel.

**Example commission brief:**
> A lone log cabin in winter pines under a full moon. I want the warmth of the cabin window to feel like the only safe place in the world — everything outside is cold, blue, sleeping. Smoke drifting up from the chimney. Snow falling at a slow, restful pace. The loop should breathe — maybe 8 seconds, no rush. Cool palette overall, single warm anchor. Let the empty sky take up real room.

**When to use**: commissioning a freelance artist, briefing an in-house illustrator, talking to a collaborator who'll execute the visual.

The brief is **half what** + **half why**. The "why" tells the artist which decisions to make when the "what" is ambiguous.

---

## Register 3: SDXL Pixel Art LoRA (Stable Diffusion prompt)

**Style**: noun-heavy, comma-separated, with style anchors.

LoRAs respond to specific tokens in their training data. For pixel art LoRAs (like nerijs/pixel-art-xl), the anchor tokens are `pixel art`, `8-bit`, `16-bit`, `SNES style`. Without these anchors, the model defaults to general illustration.

**Example SDXL prompt:**
```
pixel art, 16-bit style, snes-era, log cabin in snowy pine forest, full moon,
smoke rising from chimney, warm window glow, midnight blue palette, three-quarter
view, atmospheric

Negative: blurry, photorealistic, antialiased, smooth gradients, 3d render, modern,
high resolution, digital painting

LoRA: Pixel Art XL by nerijs (https://huggingface.co/nerijs/pixel-art-xl)
LoRA weight: 1.2
Steps: 8 (LCM LoRA)
CFG: 1.5
Seed: 42 (or any fixed for reproducibility)
Resolution: 768x768 (will be downsampled later)
```

**Critical follow-up**: SD output is NOT real pixel art. It's pixelated-looking smoothness. Always run the output through pixel-art-studio's `preprocess.py`:

```bash
python preprocess.py sd_output.png --target-size 64x64 --palette aap-64 --dither none -o pixel.png
```

This downsamples via NEAREST and quantizes to a real palette, producing actual pixel art.

**When to use**: needing many variations quickly; rough drafts for client review; image-to-image flow with ControlNet.

---

## Comparison: same scene, three registers

The scene: a winter cabin in pine forest at night, with smoke and warm window glow.

| Aspect | Register 1 (LLM) | Register 2 (human) | Register 3 (SDXL LoRA) |
|---|---|---|---|
| **Length** | ~30 lines, structured | ~5 lines, prose | ~5 lines, comma-list |
| **Hex colors** | Specified exactly | "cool blues, single warm" | Color names only |
| **Motion** | Specified periods + algorithms | "drifting at restful pace" | Not specified (LoRA can't animate) |
| **Composition** | Pixel coordinates / fractions | "let sky take real room" | "three-quarter view" |
| **Constraints** | Explicit (canvas, palette, period) | Implicit (trust the artist) | Anchor tokens (16-bit, snes-era) |

---

## Anti-patterns across all registers

| Anti-pattern | Failure mode |
|---|---|
| Mixing register 1 (hex codes) with register 2 (atmospheric) | Confuses both consumers; hex codes don't tell artists intent, atmosphere doesn't tell agents what to draw |
| Register 3 prompt without anchor token "pixel art" / "8-bit" | LoRA defaults to general illustration; output looks pixelated only at low res |
| Register 1 without explicit palette | Agent picks ad-hoc colors; result fails palette discipline check in `quality_check.py` |
| Register 2 prompt to LLM agent | Agent invents details; result drifts from intent |
| Register 2 with too-long brief (10+ paragraphs) | Artist can't extract a single guiding intent; over-specification is under-direction |

---

## When user gives ambiguous register

If user types "make a cyberpunk alley pixel art" — that's somewhere between register 2 and register 3. Decide by **what comes next**:

- If you'll generate canvas program → translate to register 1, list assumptions explicitly
- If you'll commission an artist → translate to register 2, ask 1-2 clarifying questions about mood
- If you'll prompt SDXL → translate to register 3, add anchor tokens

When in doubt for the LLM-canvas case (most common), **always show the user the scene-description block** before generating the canvas program. They confirm or adjust; you proceed.

---

## Sources

- [nerijs Pixel Art XL on HuggingFace](https://huggingface.co/nerijs/pixel-art-xl)
- [Civitai - Pixel Art XL LoRA](https://civitai.com/models/120096/pixel-art-xl)
- [Filmora - Stable Diffusion Pixel Art Tutorial](https://filmora.wondershare.com/ai-prompt/stable-diffusion-pixel-art.html)
- [LetsEnhance - AI Image Prompts Guide](https://letsenhance.io/blog/article/ai-text-prompt-guide/)
