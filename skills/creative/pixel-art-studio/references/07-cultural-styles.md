# Cultural Style Guides

Pixel art has developed distinct regional aesthetic traditions. Match style conventions to the user's stated cultural context. Each section gives: aesthetic conventions, palette anchors, sprite size standards, frame conventions, and notable game references.

---

## 1. Western canon

### Capcom / Konami SNES era

**Aesthetic conventions**:
- Full black outline as baseline; late SNES transitions to selective outline (selout)
- 16-color sub-palettes per character (SNES hardware: 4 palettes of 16 colors each, 1 shared BG)
- High anatomical fidelity for the era; action poses with exaggerated musculature
- 3-4 shade cell shading with sharp terminators

**Outline evolution**:
- Early SNES (1990-1992): full solid outline in darkest object color
- Mid SNES (1992-1994): outline starts to vary tone (early selout)
- Late SNES (1994-1996): full selective outline — outline matches shadow on shadow side, lightens/disappears on lit side (Castlevania SotN, Metal Slug engine)

**Palette anchors**: hardware-constrained. SNES global palette 32678 colors, 256 on screen simultaneously. For modern pastiche: DB32 or NES palette for authentic feel.

**Frame conventions**: walk 6-8 frames, attack 4-8 frames, idle 2-4 frames.

**Notable games**: Castlevania: Symphony of the Night (selout excellence), Metal Slug (fluid animation), Final Fantasy VI, Chrono Trigger, Street Fighter II.

### Celeste (Maddy Thorson + Pedro Medeiros)

**Base resolution**: 320×180 (16:9 native)

**Aesthetic conventions**:
- Sharp cel shading — hard terminators, no dithered gradients on characters
- Highly limited palette per chapter (chapter 1 uses ~12 colors in environment; each chapter has distinct mood palette)
- **4-frame run** (minimum) — proves you don't need 8 frames for a readable character cycle
- Background layers use larger-effective-pixel chunks (pixel density variation for depth)
- Selectively placed 1-pixel highlights; no global specular logic — every highlight placed by hand

**Palette anchors**: each chapter's palette is custom-designed. Chapter 1 (Forsaken City): cold blue-gray. Chapter 2 (Old Site): warm amber-pink. The palette expresses story arc.

**Frame conventions**: walk 4, run 4, idle 2-4, death 8+.

**Key insight**: Celeste's 4-frame run is frequently cited as proof that temporal minimalism + high-quality poses beats high-frame-count mediocre poses. Source: Pedro Medeiros pixel-grimoire, GDC Celeste postmortem.

### Hyper Light Drifter (Heart Machine)

**Base resolution**: 480×270

**Aesthetic conventions**:
- "Pixel impressionism" — keyframes drawn at action apex; viewer's brain fills in between
- **No outlines** — sprites read via color contrast and silhouette discipline alone
- Flat colors, minimal internal detail; palette per zone is carefully chosen for mood
- Background layers extremely simplified (chunkier pixels, fewer colors)
- Heavy use of additive blending for lighting effects (glow, beam, aura) — achieved via separate layers in export

**Palette anchors**: per-zone palettes with consistent complementary contrast. Desert zone: orange-tan vs teal. Lush zone: vivid pink vs forest green.

**Frame conventions**: attack animations are few frames but well-chosen keyframes; prioritizes impact readability over temporal smoothness.

### Owlboy (D-Pad Studio)

**Base resolution**: 640×360 (9-year development, 2010-2016)

**Aesthetic conventions**:
- "Hi-bit pixel art" — painted background layers (rendered at higher fidelity) composite behind sprite-layer gameplay
- Sprites use full selective outline
- High frame counts in cinematic sequences; game sprites are standard frame counts
- Backgrounds: multiple scroll layers at fractional speed (deep parallax)

**Palette anchors**: atmospheric, often desaturated backgrounds with brighter sprites for contrast.

### Dead Cells (Motion Twin / Evil Empire)

**Base resolution**: 640×360

**Frame conventions**: attack animations use **8-12 frames** — among the highest frame counts in indie pixel art. This is the "premium attack" benchmark. Cited in production as contributing to the "feels good to attack" quality.

### Tunic (Andrew Shouldice)

**Aesthetic**: hi-bit isometric + top-down hybrid, no outlines, watercolor-inspired palette. Isometric angle is ~26° elevation (not true 45° tile isometric). Uses a unique "off-angle" perspective that gives rotatable world feel.

### Eboy (isometric commercial illustration)

**Founders**: Steffen Sauerteig, Svend Smital, Kai Vermehr (Berlin, 1997-present)

**Aesthetic conventions**:
- Isometric perspective: **1:2 axis ratio** (every horizontal step = 2px right, 1px up; every vertical step = 2px right, 1px down)
- Dense detail per area; buildings, machines, crowds
- "Pixorama" format: large isometric scenes for magazine/advertising clients
- No sprites per se — pure illustration focus
- Palette: high saturation, rich depth, no authentic hardware constraints

**Notable**: eboy.com is the definitive reference for commercial isometric pixel illustration. Not a game aesthetic but influences isometric game art heavily.

---

## 2. Chinese xianxia / wuxia / heritage

Chinese-language pixel art has developed specific conventions driven by mobile game market economics, cultural heritage, and 像素换装 (pixel costume gacha) monetization systems.

### Sword silhouette (剑)

The canonical Chinese pixel sword (`jian`, straight double-edged blade) distinguishes from Western broadsword defaults:
- **Blade**: straight, slim, double-edged — no forward taper (unlike Western broadsword)
- **Guard ornament**: prominent cross-guard or circular guard detail even at 16px scale
- **Tassel (剑穗)**: cloth/silk tassel hangs from pommel — secondary animation channel (follows wrist motion with 1-2 frame lag)
- **At 32px**: blade ≈ 2px wide, guard ≈ 4px wide, tassel ≈ 4-6px long with 3-4 frame flutter

### Robe textures (汉服 / 道袍)

- **Layered sleeves**: wide hanging sleeve ends extend beyond wrist in idle pose; fly outward in movement
- **Sash motion**: the cloth sash (腰带) is a separate animation channel — typically 2-4 frame oscillation, offset from leg cycle by 1 frame
- **Collar**: V-collar or cross-collar with visible layered edges at 48px+
- **At 32px**: simplified to suggest draping; at 64px+ full fold detail possible

**This differs from Western pixel armor**: CN robes have cloth secondary animation; Western RPG sprites typically have rigid armor with no secondary fabric motion.

### Calligraphic line work

Borrowed from 工笔 (gongbi) ink discipline:
- Outline weight varies: **clustered dark pixels on the "heavy" side** of a line (the structural edge bearing weight)
- **No outline on the opposite "light" side** — color contrast and value step carry the edge
- At pixel scale: 2-3 adjacent dark pixels on one side vs a single pixel or no pixel on the other

```
Sword blade (heavy spine side):
. D D D D D .    D = dark clustered outline (heavy side)
. D D D D D .
. D D D D D .

Sword edge (light side):
. . . . . . .    No outline; silver blade color vs background contrast carries edge
# # # # # # #
. . . . . . .
```

**Source**: indienova.com 像素课堂; 01-techniques.md CN-specific section

### Architecture sprites

Chinese curved roofs (歇山顶 hip-and-gable, 庑殿顶 hip roof):

**Working convention at 32-48px width**:
- Eave tip: **+2px elevation** from the straight eave line (the upward curl)
- Anti-alias diagonally along the upturned eave curve
- Ridge cap ornament (鸱吻): 2-3px bump at both ridge ends, even at small scale

```
Curved eave at 48px width (simplified):
. . . . . . . . . # .    <- eave tip at +2px from center eave height
. . . . . . . . # . .
. . . . . . . # . . .
# # # # # # # . . . .   <- main eave line (horizontal)
```

Lattice windows (棱格窗): 2×2 or 3×3 repeating grid pattern in wall sprites.

### Color palettes from Chinese tradition

| Palette | Colors | Hex examples | Use |
|---|---|---|---|
| 青花 (qinghua) | 4-8 | Cobalt #1A3F7E-#4A6FA5 on porcelain white #F5F0E1 | Water, porcelain themes |
| 故宫红墙 | 3-12 | Vermillion #C73E3A, imperial yellow #DDA130, gray-green brick #5B6770 | Palace, heritage scenes |
| 五行色 | 5 | Metal/white, Wood/green #4F8A57, Water/black #1A1A1A, Fire/red #C7372F, Earth/yellow #D4B254 | Skill effects (elemental) |
| 水墨 | 6 | 6-step ramp 焦/浓/重/淡/清/白 (ink-black to white) | Monochrome/ink wash aesthetic |

**Source**: 中国传统色：故宫里的色彩美学 (book, 384 named colors); figma.com/community/file/932547561953107053; zhongguose.com/en

**High-saturation preference**: CN mobile market research shows preference for high-saturation palettes. Unlike Western indie tendency toward muted/atmospheric, CN mobile pixels lean vivid for readability on high-DPI phone screens and to differentiate gacha items.

### Walk cycle: 4 frames @ 5 FPS (documented CN standard)

- **4 frames at 200ms each = 5 FPS** is the documented CN mobile RPG walk standard
- Each foot extension followed by return-to-neutral frame
- **Do NOT correct to 8fps** — 5fps is intentional
- **Source**: blog.csdn.net/qq_42608732/article/details/142219430; cnblogs.com/Xiang-gu/p/18601770

### 8-direction movement spritesheet

CN mobile RPG dominant convention: 8 directions of movement (down, down-right, right, up-right, up, up-left, left, down-left).

Western indie often uses 4-direction (down/up/left/right) or 2-direction (left/right). The 8-direction sheet is specifically driven by top-down RPG view common in CN mobile market.

**Total frames**: 8 directions × 4 walk frames = 32 frames minimum for a basic 8-dir walk spritesheet.

### Mobile scale: 48-96px

CN mobile sprites are larger than Western indie norms:
- **Western indie default**: 16×16 or 32×32
- **CN mobile default**: 48-96px
- **Driver**: phone screens with high pixel density + 像素换装 (pixel costume) monetization requires visible costume accessories

**2.5D pixel hybrid**: more accepted in CN mobile market than Western indie. Soul Knight (元气骑士) exemplifies 2.5D-pixel hybrid.

### Notable CN games

| Game | Studio | Notes |
|---|---|---|
| 戴森球计划 (Dyson Sphere Program) | Yuzucat 柚子猫 | Low-poly + retro UI pixel elements |
| 烟火 (Firework) | 月光蟑螂 | Pixel horror; rural Chinese village palette, 中元节 cultural references |
| 大侠立志传 (Wushu Chronicles) | 半瓶神仙醋 | Jianghu survival sim; typical xianxia pixel sprite conventions |
| 元气骑士 (Soul Knight) | ChillyRoom | 2.5D-pixel hybrid mobile rogue-lite; CN bestseller |
| 战魂铭人 | — | Manga-style pixel hybrid (漫画风格的像素画风) |
| 星屑之塔 | — | Mobile pixel RPG with 像素换装 system; 64-128px characters |

---

## 3. Korean dot graphic (도트)

### Lexicon

- **도트** (dot) = dominant native term. More commonly used than 픽셀 아트 in community contexts.
- **도트 그래픽** = dot graphic (medium term)
- **손으로 직접 찍은 도트** = "hand-drawn dot" — quality discriminator distinguishing manual pixel placement from 3D-model-filtered pixel art
- **도트 장인** = "dot craftsperson" (MapleStory team usage)
- Source: namu.wiki/w/픽셀%20아트

### Aesthetic conventions

- Anime/chibi blending: 8-head ratios used in realistic sprite styles; chibi 2-3 head ratios used in mobile casual. Korean dot explicitly blends Japanese anime eye proportions and SD (super-deformed) body ratios with pixel technique.
- Strong silhouettes with exaggerated keyframe poses (Skul style)
- **Comic-book-like motion**: few frames but high-impact poses, especially in attack sequences

### Sprite sizes (Korean industry standards)

| Size | Use |
|---|---|
| 16×16 | Pure retro / GameBoy aesthetic |
| 32×32 | Casual/mobile default; smallest for recognizable chibi facial detail |
| **48×72** | Standard humanoid model in Korean mobile RPGs |
| 64×64 | Portrait / detailed character art |
| Metal Slug / Owlboy class | High-end reference (far beyond mobile) |

**Source**: DCinside 도트 마이너 갤러리 sprite size threads (m.dcinside.com/board/pixelart/20298; m.dcinside.com/board/game_dev/107353); Coloso syllabi.

### Frame conventions

| Animation | Frames | FPS |
|---|---|---|
| Idle | 4-8 (typical 6) | 8-12 |
| Walk | 6-8 (chibi: 4) | 8-12 |
| Attack | 4-6 + 1 anticipation frame | 10-12 |
| Cinematic | — | 24 |

**Source**: Coloso (Arkneru, Hyatsu syllabi); Fast Campus pixel art course; DCinside frame count discussions.

### Smear frames (스미어 프레임)

Korean tutorials explicitly document smear frames for fast-motion sequences. **Heavy in Skul, lighter in Sanabi.**

- Skul: The Hero Slayer: 1-2 smear frames per attack animation; contributing to the "comic-book" animation feel. Cited as key technique in Skul's positive reception.
- Sanabi (산나비): minimal smear; prioritizes sharp hand-crafted keyframes.

**Source**: garagefarm.net Korean blog on smear frames; namu.wiki/w/Skul:%20The%20Hero%20Slayer

### Hand-drawn vs 3D-filtered distinction

> "2020년대의 픽셀 그래픽 게임은 3D 모델링을 기반으로 픽셀 필터를 입히거나 위에 덧그린 유사 도트 게임이 많으나, 본작은 거의 모든 그래픽 리소스가 손으로 직접 찍은 도트다."
> (Translation: "While most 2020s pixel games use 3D-model-based pixel filters or overdrawing, Sanabi's resources are almost entirely hand-drawn dot.")
> — namu.wiki/w/산나비

This distinction is a quality signal in the Korean community. **손으로 직접 찍은 도트** carries a premium craft connotation that 3D-filtered pixel does not.

**Sanabi art lead**: 허유지 (Heo Yu-ji). Team split: 1 character animator, 1 background dot designer, 2 programmers.

### Dithering: sky / water specific

Korean tutorials emphasize dithering specifically for **sky/water gradients** rather than general shading. Reference: "Metal Slug 3 sky uses dithering to express a wide single-color region." Korean dot practice uses dithering as a deliberate stylistic tool for large atmospheric areas.

**Source**: 디더링 - 나무위키 (namu.wiki/w/디더링)

### Palette anchors (Korean traditional)

| Palette | Colors | Notes |
|---|---|---|
| 오방색 (obangsaek) | 5 | Five-direction system; KS A 0062 KATS standard. East=blue, South=red, Center=yellow, West=white, North=black |
| 단청 | Multi | Temple painting colors; 하엽색 (lotus-leaf dark green) as central color since Goryeo dynasty |
| 한복 | Per garment | Hanbok garment palette; bride's 활옷 = red+blue+gold; mourning = white+gray |
| 90-color extended | 90 | NMMCA 1992 compilation; available as Clip Studio Asset 한국전통색상표 90색 (assets.clip-studio.com/ko-kr/detail?id=1908146) |

**Source**: KATS (kats.go.kr/content.do?cmsid=86) KS A 0062 standard; NMMCA 1992 research.

### MapleStory tradition

Nexon's MapleStory pixel art team is the longest-running professional Korean dot studio (2003-present). Term "도트 장인" (dot craftsperson) is used internally. Art team lead: 신혜영 (joined 2006).

Maplelog blog publishes regular "도트 장인" interview series documenting pixel costume design process.

**Source**: blog.maplestory.nexon.com/Tech/Content/17 (MapleStory dot master costume interview)

### Notable Korean games

| Game | Notes |
|---|---|
| 산나비 (Sanabi) | Hand-drawn dot benchmark; rope physics; 허유지 art lead |
| Skul: The Hero Slayer | 1M → 2M sales; smear-heavy comic-book dot animation |
| MapleStory | Longest-running professional 도트 studio since 2003; 도트 장인 tradition |
| Lost Castle | Korean indie rogue-lite with solid 32×32 sprite work |
| Metal Unit | Korean side-scroller; detailed attack frame counts |
| Dave the Diver | Korean indie hit; uses hi-bit layered pixel aesthetic |

---

## 4. Russian indie

### Punch Club rule: draw at 1×, render at 2-3×

**Source**: Lazy Bear Games (Punch Club), dtf.ru/gamedev/2510; shazoo.ru/2016/12/07/46717

The most widely documented Russian pixel art workflow:
- **Master**: draw at 1× (one logical pixel = one image pixel)
- **Render**: game engine scales to 2× or 3× via integer scaling
- **NEVER edit at 2×**: sub-pixel edits at 2× are not pixel-perfect at 1×

This maps to our JSON renderer's `pixel_size` parameter.

### Mandatory contour rule

> Outline is **always darker than the darkest pixel of the object**.

**Source**: Punch Club guide; Stoneshard development notes; habr.com/ru/companies/playgendary/articles/485704/ (исправляем типичные ошибки)

This extends the general outline rule: in Russian indie tradition, this is non-negotiable — there is no "no outline" style, and the outline must be visibly distinct from the darkest interior shade.

**Implementation**: if `--style russian-indie` flag is set, quality_check.py verifies outline pixels are darker than all interior pixels. Failure = error.

### Stoneshard (Ink Stains Games, Saint Petersburg)

**Aesthetic**:
- Dark fantasy muted tones — desaturated browns, greens, grays
- High detail per sprite; careful contour work
- Painterly shading with 4-5 shades per material
- Top-down view; ~32×32 character sprites with high internal detail density
- Palette: Stoneshard-inspired preset in our skill (dark fantasy muted)

> "Правильный пиксель-арт, вопреки расхожему мнению, вовсе не менее трудозатратная альтернатива обычной 2D-графике — делать его и дольше, и сложнее, и дороже"
> (Proper pixel art, contrary to popular belief, is not less labor-intensive than regular 2D — it is longer, more complex, more expensive.)
> — dtf.ru/gamedev/20015 Stoneshard interview

**Source**: habr.com/ru/post/513156/; dtf.ru/gamedev/20015

### Loop Hero (Four Quarters / Devolver Digital)

**Multi-tier sprite consistency**:
- Simplified Atari-like sprites on the loop map view
- More detailed combat sprites in battle view
- Three coexisting visual styles (map, combat, card) — **intentionally inconsistent** by design

This is unusual for pixel art (which normally demands cross-sprite consistency). Loop Hero's approach: each context has its own consistent visual language, but the contexts deliberately differ.

**Palette**: very limited ("when pixels were large and palettes were small"). Intentionally nostalgic constraint.

### The Final Station (Do My Best Games / tinyBuild)

- Two-person team: Олег Сергеев (design+art), Андрей Румак (code)
- **Simplest possible pixel art** by intentional design (one location per day at production peaks)
- **Backgrounds: intentionally degraded high-quality 3D renders** used as atmospheric backgrounds (Final Fantasy pre-rendered BG approach). Not pixel-drawn backgrounds.
- This is a legitimate hybrid approach, not an artistic compromise — creates atmospheric depth without manual background painting.

**Source**: dtf.ru/gamedev/963 Final Station interview

### Russian gaming nostalgia palette

Russian pixel art community draws from a different nostalgic pool than American 80s arcade:
- **Dendy** (Russian NES clone, 1992-1994) = Russian 8-bit archetype
- **Sega Genesis/Mega Drive clones** = 16-bit reference
- **ZX Spectrum** = older niche (1980s CIS)
- **Result**: darker, more muted palettes observable in Russian indie output (Stoneshard, Final Station) vs brighter Japanese/American counterparts

**Russian palette tendency**: dark, atmospheric, muted tones. Stoneshard-inspired preset encodes this.

---

## 5. Style selection quick-reference

| User context | Canvas | Walk frames | FPS | Palette | Outline |
|---|---|---|---|---|---|
| Western SNES retro | 16×16 - 32×32 | 6-8 | 8 | DB32 or NES | Selout |
| Celeste-style indie | 320×180 game resolution | 4 | 8 | Custom per zone | Full or selout |
| HLD pixel impressionism | 480×270 game resolution | 4-6 | 8 | Custom per zone | None |
| CN xianxia mobile | 48-96px | 4 @ 5fps | 5 | gugong / qinghua | Calligraphic |
| CN casual / Soul Knight | 32-64px | 4-6 | 8 | Saturated custom | Full |
| Korean 도트 mobile | 48×72 | 6-8 (chibi:4) | 8-12 | obangsaek / 단청 | Full selout |
| Sanabi-quality hand-dot | 48×72+ | 6-8 | 10-12 | Custom muted | Full precise |
| MapleStory costume | 64-128px | 6-8 | 8-12 | Vivid custom | Full |
| Russian indie (Stoneshard) | 32×32 | 6 | 8 | Stoneshard-inspired muted | Mandatory darker |
| Punch Club style | Any | Standard | Standard | Limited | Darker-than-darkest |
| Loop Hero simplified | 16-24px | 4 | 6 | Very limited | Full |
