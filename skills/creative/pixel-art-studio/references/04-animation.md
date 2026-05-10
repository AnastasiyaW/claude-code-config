# Animation: Principles, Frame Counts, Techniques, Export

Pixel art animation is NOT the same as vector or raster animation. The discrete pixel grid creates specific constraints and opportunities. This file encodes what translates from classical animation theory and what doesn't, plus production-validated numbers.

---

## 1. Disney 12 principles — what translates to pixel art

Of the 12 Disney animation principles, **only 3 translate cleanly** without significant modification:

| Principle | Pixel art verdict | Implementation |
|---|---|---|
| **Timing** | Translates directly | Wind-up = long frames; action = fewest frames; recovery eases back. *"Slowing down anticipation frames and speeding up action frames will improve animations more than adding extra frames"* (saint11) |
| **Anticipation** | Translates directly | Crouch before jump; wind-up before attack; head turn before body turn. Even 1 frame of anticipation reads correctly. |
| **Squash & stretch** | Translates, scaled to pixel constraints | Even **1 pixel** of vertical compression on landing or horizontal stretch on throw is effective and readable. More than 2px usually breaks pixel grid readability. |
| Ease in/ease out | Partial — discretized | Standard easing curves don't apply directly; use staircase/step easing (see section 6) |
| Follow-through / overlapping | Partial | Cloth, hair, tails can have delayed offset (1-2 frame lag). Rigid sprites: no follow-through |
| Arcs | Difficult | Arcs must follow pixel grid; draw arc path at target size, not interpolated |
| Secondary action | Valid | Sleeve flap, hair bounce, coin jingle separate from primary walk cycle |
| Solid drawing | Valid | Maintain consistent sprite volume across frames |
| Staging | Game design concern, not animation | |
| Straight-ahead vs pose-to-pose | Valid — pose-to-pose preferred for pixel | Draw keyframes (contact, passing, high-point), then in-betweens |
| Exaggeration | Valid — CN/KR prefer strong exaggeration | Korean smear frames = exaggeration |
| Appeal | Subjective, valid | |

**Source**: saint11.art "Animation for Beginners" series; habr.com/ru/post/275703/ (Галоп пикселя часть 3 — Animation fundamentals)

---

## 2. Frame counts (production-validated, cross-cultural)

### Master table

| Animation | Min | Standard (Western) | CN mobile | KR indie | Premium |
|---|---|---|---|---|---|
| **Idle** | 2 (breathing) | 4-6 | 2-4 | 4-6 (typical 6) | 8 |
| **Walk** | 4 (Celeste) | 6 (Shovel Knight) | 4 | 6-8 (chibi: 4) | 8-12 |
| **Run** | 6 | 8 | 6 | 6-8 | 10 |
| **Attack** | 3 (anticipation/strike/recovery) | 5 | 3-5 | 4-6 + 1 anticipation | 6-8 (Dead Cells: 8-12) |
| **Death** | 4 | 6-8 | 4-6 | 6-8 | 10+ |
| **Hit reaction** | 1-2 | 2-3 | 1-2 | 2-3 | — |

**Rule**: a 16×16 character has insufficient pixels to differentiate 8 walk-frames. 4 is plenty at that resolution. Scale frame count with sprite size, not with ambition.

**Sources**:
- Western: lospec.com pixel art academy; saint11.art #11; dead cells postmortem
- CN mobile: blog.csdn.net/qq_42608732/article/details/142219430; cnblogs.com/Xiang-gu/p/18601770
- Korean: DCinside 도트 마이너 갤러리 sprite size threads; Coloso syllabi (Arkneru, Hyatsu)

---

## 3. FPS conventions

### Standard FPS by animation type

| Animation | FPS | Frame duration (ms) | Notes |
|---|---|---|---|
| Idle | 6 | 167ms | Breathing / subtle loop |
| Walk | 8 | 125ms | Western default |
| Walk (CN mobile) | **5** | **200ms** | Documented CN standard; slower than Western |
| Run | 10 | 100ms | |
| Attack | 10-12 | 83-100ms | |
| Hit flash | 15-20 | 50-67ms | Fast flicker for damage feedback |
| Cinematic | 24 | 42ms | Cutscenes, boss intros |
| Background animation | 4-8 | 125-250ms | Flames, water, clouds |

### Sweet-spot FPS values

Game engines typically work on integer frame counts. Use these FPS values that divide evenly:
`8, 10, 12, 15, 20, 24`

Avoid intermediate values (9, 11, 13) — they create uneven frame intervals when discretized.

### CN 5fps walk — documented standard

Chinese mobile RPG tutorials explicitly document **4 frames at 200ms each (5 FPS)** as the walk cycle standard. This is slower than Western 8fps and looks "deliberate" rather than "smooth" by Western indie standards.

**Do NOT correct this to 8fps for CN-style sprites** — 5fps is the target standard.

**Source**: blog.csdn.net/qq_42608732/article/details/142219430 (RPG 像素角色俯视角行走动画); cnblogs.com/Xiang-gu/p/18601770

---

## 4. Walk cycle structure

### 4-frame walk (minimum, Celeste standard)

Frames in order: `[contact, recoil, passing, high-point]`

```
Frame 0 (contact):  Lead foot down, heel strikes floor, body at lowest point
Frame 1 (recoil):   Lead foot absorbs impact, body rises, trail leg begins swing
Frame 2 (passing):  Both feet closest to neutral, body at highest point
Frame 3 (high-point): Trail foot swings forward, body at medium height, arms crossed
```

**Symmetry**: frames 0-3 = right lead; ping-pong or duplicate+mirror for left lead. Total 4-8 frames for full cycle.

### 6-frame walk (Shovel Knight, Western standard)

```
Frame 0: contact right foot
Frame 1: mid-down
Frame 2: passing
Frame 3: mid-up
Frame 4: contact left foot
Frame 5: stride
```

### 8-frame walk (premium — more differentiation)

Each of the above phases gets a 2-frame sub-step for smoother motion. Useful for hi-bit sprites (48×48+).

### 12-frame walk (premium cinematic)

Used in Metal Slug, full animated indie characters (Owlboy). Each foot has fully detailed arc. Required only for hero sprites.

**Rule**: at 16×16 use 4-frame; at 32×32 use 4-6 frame; at 48×48+ use 6-8 frame; 12-frame only for 64px+ hero-class.

**Source**: habr.com/ru/post/441562/ (Галоп пикселя часть 5 — Ходьба); habr.com/ru/articles/772588/ (часть 6 — Бег)

---

## 5. Smear frames (Korean Skul-style)

**Smear frame** = 1-2 heavily distorted/stretched intermediate frames inserted between keyframes of a fast motion (attack, dodge, throw). The smear acts as a motion blur substitute in discrete animation.

**Korean term**: 스미어 프레임

### Implementation

1. Draw keyframe A (attack windup pose)
2. Draw keyframe B (impact pose)
3. Insert 1-2 smear frames between them:
   - Limb stretches in direction of motion
   - Body remains near keyframe A position
   - Extremity extends toward keyframe B position
   - Often shown at shorter duration (50-67ms) than surrounding frames

```
Keyframe A: arm at rest
Smear 1:    arm stretched forward 2-3px toward impact (50ms frame)
Smear 2:    arm at 75% extension, slightly blurred suggestion (50ms frame)
Keyframe B: impact position (83ms frame)
```

**Heavy in Skul**: Skul: The Hero Slayer's combat animations use smear extensively — each attack has 1-2 smear frames with exaggerated limb stretching. This is cited as contributing to the "comic-book style" feel.

**Lighter in Sanabi**: Sanabi (산나비) uses smear sparingly, preferring sharp keyframes over smear-based motion blur. Heo Yu-ji's art philosophy: "almost all graphics are hand-drawn dot", favoring precision over smear exaggeration.

**Source**: garagefarm.net/ko-blog/smear-frames-enhancing-motion-in-animation; namu.wiki/w/산나비; namu.wiki/w/Skul:%20The%20Hero%20Slayer

---

## 6. Easing for pixel art

### The problem with linear easing

Linear easing = equal pixel displacement per frame. On a discrete pixel grid, linear motion looks mechanical and robotic. The "smoothness" that linear easing provides in vector/raster animation does not read correctly when positions must snap to integer coordinates.

### Staircase / step easing

The correct approach for pixel art: positions are held for N frames, then snap to new position. This creates the "punchy" feel characteristic of quality pixel art animation.

```
Linear (bad):    frame 0: x=0, frame 1: x=2, frame 2: x=4, frame 3: x=6
Staircase (good): frame 0: x=0 (hold 2f), frame 2: x=4 (hold 2f), frame 4: x=8
```

### Quantized easing (for arcing motions)

For arcs (thrown objects, jump trajectories), each frame's position rounds to the nearest pixel:

```
physics_x = start_x + velocity_x * t - 0.5 * gravity * t^2
sprite_x = round(physics_x)   # quantized to grid
```

The rounded path creates a slightly faceted arc that looks correct in pixel context.

### Easing implementation in quality_check.py

For animation review: flag if consecutive frames have identical pixel displacement (constant velocity linear motion) on a primary motion axis. Staircase easing = pass; constant-velocity = warning.

**Source**: saint11.art animation tips #7 "Easing"; habr.com/ru/post/275703/ (Галоп пикселя часть 3)

---

## 7. Sub-pixel animation

Sub-pixel animation = animating the **anti-aliasing intermediate pixels** rather than moving the full silhouette. Creates the illusion of motion smaller than one pixel.

**Use cases**:
- Breathing idle (ribcage expansion < 1px)
- Subtle head turn that should NOT move the silhouette
- Slow floating or hovering (object drifts < 0.5px)
- Cloth ripple in wind without moving body

**Implementation**: on the silhouette boundary, alternate between a "present" and "absent" intermediate-color pixel (the AA pixel). This gives the visual impression of the edge moving 0.5px without actually moving the pixel grid.

```
Frame A: . . B AA border . .    (AA pixel present on right side)
Frame B: . . B .  border . .    (AA pixel absent on right side)
```

Used by Pedro Medeiros for breathing idles on small sprites.

**Hard pixel motion vs sub-pixel motion**:
| Motion type | Use when |
|---|---|
| Hard pixel (integer displacement) | Walk cycle, run, attacks — any primary motion |
| Sub-pixel (AA toggle) | Breathing, idle sway, cloth ripple — motion too subtle to justify full pixel jump |

**Source**: Pedro Medeiros medium.com/pixel-grimoire; saint11.art "Sub-pixel Animation"; school-xyz.com/pixel-art (Russian subpixel animation curriculum)

---

## 8. Onion skinning workflow

Onion skinning = viewing previous and next frame(s) transparently while drawing current frame.

**Aseprite**: View > Onion Skin (Shift+F). Configure: how many frames back/forward (default 1-3), opacity of ghost frames.

**Recommended settings**:
- Back frames: 2-3 (see where you came from)
- Forward frames: 1 (see where you're going)
- Loop mode: useful for checking cycle continuity at frame 0 when drawing last frame

**Korean tutorial note**: Korean Aseprite community uses `양파 껍질 보기` as the term. Toggle via Aseprite toolbar.

**Best practices**:
- Always use onion skin for walk/run cycles
- Turn off when drawing faces/static details (ghost frames distract)
- For Sanabi-style hand-crafted dot quality: check silhouette consistency every frame against onion ghosts

---

## 9. Sprite sheet layouts

### Convention: rows = animation, columns = frames

The canonical game engine convention (Unity, Godot, Unreal):

```
Row 0: idle     [f0][f1][f2][f3]
Row 1: walk     [f0][f1][f2][f3][f4][f5]
Row 2: run      [f0][f1][f2][f3][f4][f5][f6][f7]
Row 3: attack   [f0][f1][f2][f3][f4]
Row 4: death    [f0][f1][f2][f3][f4][f5][f6]
```

### Padding convention

- **1px transparent padding** between cells: minimum for no bleeding
- **2px transparent padding**: recommended; prevents GPU texture-sample bleed at non-integer scales
- Power-of-2 final sheet dimensions (256×256, 512×256, 1024×512) for best GPU texture cache behavior

### Column-based layout (alternative for 8-direction)

Some CN and KR mobile RPG spritesheet tools use column-based: each column = one direction, each row = one frame. Match the target engine's importer requirements.

**8-direction spritesheet** (CN mobile dominant convention):
```
Directions: down, down-right, right, up-right, up, up-left, left, down-left
Each direction: N frames of the animation
Total sheet: 8 columns × N rows (or 8 rows × N columns)
```

### Exporting with Aseprite CLI

```bash
aseprite -b character.aseprite \
  --sheet character_sheet.png \
  --sheet-type rows \
  --sheet-pack \
  --data character_sheet.json \
  --format json-array
```

The `--data` flag outputs JSON metadata (frame positions + tag ranges) compatible with most game engines.

---

## 10. Aseprite tag system

Tags = named ranges of frames, exported as metadata alongside sprite sheets.

| Mode | Behavior |
|---|---|
| `Forward` | Plays frames from-to in order, loops |
| `Reverse` | Plays frames to-from in reverse order, loops |
| `Ping-pong` | Plays forward then backward, loops at both ends |

**Create tag**: Select frame range in timeline → right-click → Add Frame Tag → name it (`idle`, `walk`, `attack`).

Keyboard: F2 (or Frame > Properties) on a tag to rename.

**Aseprite tag export**:
```bash
aseprite -b char.aseprite --tag walk --sheet walk_sheet.png
```

The tag `"direction"` field in exported JSON: `"forward"`, `"reverse"`, `"pingpong"`.

**This maps to our JSON schema `tags[].direction` field.** See `references/08-json-schema.md`.

---

## 11. Background / foreground parallax

Multi-layer scenes use fractional scroll rates to create depth illusion:

| Layer | Scroll rate (relative to player speed) | Notes |
|---|---|---|
| Background mountains | 0.1-0.2× | Barely moves |
| Midground trees | 0.4-0.5× | Moderate scroll |
| Foreground terrain | 1.0× | Matches player |
| UI / overlay | 0.0× | Fixed |

**Celeste pixel density trick**: distant layers (background mountains) use larger, chunkier pixel clusters — the perceived "resolution" is lower than the foreground, creating depth without blur. Foreground sprites are at full 1:1 pixel fidelity; background objects have 2×2 or 4×4 effective pixel blocks.

**Source**: Celeste GDC postmortem; Pedro Medeiros Celeste pixel design notes

---

## 12. File format trade-offs

| Format | Use | Pros | Cons |
|---|---|---|---|
| **PNG indexed** | Game engine spritesheet | Smallest, exact palette, lossless | No semi-transparency |
| **PNG RGBA** | General purpose | Full alpha, lossless, wide compat | Larger than indexed |
| **GIF** | Web preview, social media | Universal, animated | 256-color cap, no semi-transparency |
| **APNG** | Web with transparency | Transparency + animation | Less universal than GIF |
| **WebP (lossless)** | Modern web | Smaller than PNG | Compatibility caveats (iOS < 14) |
| **Aseprite `.aseprite`** | Source master | Tags, layers, palette, history preserved | Aseprite-only without conversion |

**Decision rule**: if target is game engine → PNG indexed; if target is web preview → GIF (broadest compat) or APNG (better quality); if source → `.aseprite`.

**When in doubt: PNG RGBA.**

**Russian community note**: AI pixel art grid-snap pipeline outputs to PNG RGBA; then game developer imports to indexed if needed. Habr habr.com/ru/articles/930462/ covers this workflow.

---

## 13. Russian Punch Club rule: draw at 1×, render at 2-3×

**From Lazy Bear Games (Punch Club), widely cited as Russian indie standard**:

- Master art is drawn at **1× pixel scale** (one logical pixel = one image pixel in source file)
- Game engine renders at **2× or 3× via integer scaling** (`pixel_size` parameter in our renderer)
- **Never edit at 2×** — that introduces sub-pixel edits that are not pixel-perfect at 1×

This corresponds to our JSON schema `pixel_size` field:
- `"pixel_size": 1` = master at 1× (editing scale)
- `"pixel_size": 16` = rendered at 16× output (standard preview)

**DTF guide**: dtf.ru/gamedev/2510-gaid-dlya-punch-club-tonkosti-piksel-arta

---

## 14. Korean specifics: 산나비 vs 3D-filtered distinction

In Korean pixel art discourse, a key quality discriminator is:

- **손으로 직접 찍은 도트** ("hand-drawn dot") — every pixel placed deliberately by an artist. Sanabi exemplifies this. Quality premium.
- **3D 모델링 기반 픽셀 필터** ("3D-model-based pixel filter") — 3D rendered and then pixelated via filter or post-process. Looks pixel-art-like but lacks the cluster discipline and intentionality of hand-drawn. Not considered "true dot" by Korean community.

This maps to our AI-slop detection: 3D-filtered pixel art exhibits many of the same artifacts as AI-generated output (inconsistent cluster sizes, off-grid pixels, smooth gradients).

**Sanabi art lead**: 허유지 (Heo Yu-ji). Team: 1 character animator, 1 background dot designer.

**Source**: namu.wiki/w/산나비; Fast Campus pixel art course documentation

---

## Summary: quick-reference table

| Topic | Key value |
|---|---|
| Default walk FPS (Western) | 8 fps (125ms/frame) |
| CN mobile walk FPS | 5 fps (200ms/frame) |
| Min walk frames | 4 (Celeste) |
| Standard walk frames | 6 (Shovel Knight) |
| Standard idle frames | 4-6 |
| Attack frames (min) | 3 (anticipation + strike + recovery) |
| Smear frames | 1-2 between keyframes |
| Sprite sheet padding | 2px transparent |
| Sub-pixel motion | Animate AA pixels, not silhouette |
| Easing style | Staircase/step, not linear |
| KR humanoid size | 48×72 |
| Source format | `.aseprite` (master) |
| Export format | PNG indexed (engine) / APNG (web) |
