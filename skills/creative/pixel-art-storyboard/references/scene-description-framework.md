# Scene Description Framework

The 5-element framework for turning a 2-paragraph narrative into a pixel-art-ready scene specification.

---

## 1. The 5-element framework

Every scene description must specify these five elements. If user input is missing one, **fill in a sensible default and list it explicitly** so they can confirm/adjust.

| Element | What to specify | Example |
|---|---|---|
| **Subject** | 1-3 foreground icons that carry meaning | "A red apple in pale hands" |
| **Setting** | Background environment, depth layers (max 3) | "Deep night void, single distant star" |
| **Lighting** | Source, direction, time of day, mood | "Cool moonlight from upper-right, warm highlight on subject" |
| **Palette** | 3-6 named colors, NOT hex codes | "Midnight black, ivory skin, deep crimson, warm highlight, single petal pink" |
| **Motion** | What loops + period in seconds | "Highlight on apple orbits in 4s; petal drifts down once per loop" |

Pixel art has more constraints than illustration, so palette and motion are *more* important — limits drive the mood.

---

## 2. Compositional shorthand

### Iconography first
"A red apple in pale hands" tells more than "fruit and skin" because pixel art reads silhouettes before details. Hyper Light Drifter's analysis on [I Draw Wearing Hats](http://idrawwearinghats.blogspot.com/2014/04/art-direction-analysis-of-hyper-light.html) describes this as "big sections of flat color with small details etched on top" — the big flat color *is* the icon.

### Symbolic accent
A single chromatic note in an otherwise restricted palette becomes the story. Hyper Light Drifter uses red on the Drifter against teal/cyan environments — split-complementary scheme drives the cold-with-hot-heart feel.

For Twilight covers: the entire saga uses 1-2 red items on dark background. The red IS the brand.

### Negative space
At 32x32 or 64x64, you cannot fill the frame. Lean into emptiness. Thomas Was Alone (per [Wikipedia](https://en.wikipedia.org/wiki/Thomas_Was_Alone)) shows minimalism with 80% empty frame is *louder* than dense detail.

---

## 3. Three reference forms

| Form | Structure | When to use |
|---|---|---|
| **Cover-style** | Central subject, symbolic accent color, brand-defining palette, minimal text overlay room | Album/book covers, store icons, splash screens |
| **Establishing shot** | Wide view, 3+ depth layers, single character silhouette tiny in frame | Game intros, ambient title screens |
| **Loop-friendly** | Subject + motion-element explicitly named with period | Animated GIF, seamless web background |

For animated covers we want the **cover-style + loop-friendly** combination: central subject + clear motion element + period.

---

## 4. Three full worked examples

### Example A: Romeo & Juliet book cover (cover-style, looped)

**5-element block:**
- **Subject**: Two single rose stems crossing diagonally; a balcony silhouette behind
- **Setting**: Moonlit night, balcony's wrought-iron lattice rendered as 1-pixel curls
- **Lighting**: Cool moonlight from upper-left casting long shadow of the lattice
- **Palette**: Deep blue night (60%), pale moonlight white (20%), blood-red rose (15%), tarnished silver railing (5%)
- **Motion**: Petals drift slowly downward from upper rose; fireflies wink in background at random offsets. Loop 8s, petals respawn at top when they fall off-screen.

**Final paragraph:**
> Two rose stems cross diagonally over a moonlit balcony silhouette. The wrought-iron lattice is rendered as 1-pixel curls — barely there, an etched suggestion. Deep blue night fills 60% of the frame; pale moonlight catches the railings; the roses are the only saturated color. From the upper rose, petals drift down slowly; in the background, fireflies wink at irregular offsets so the eye can't catch the loop. 8-second cycle, petals respawn at top.

### Example B: Lonely cabin in winter forest (establishing shot, ambient)

**5-element block:**
- **Subject**: Small log cabin centered on lower third, smoke rising from chimney
- **Setting**: Dense pine forest behind, mountains farther back, full moon high (3 depth layers)
- **Lighting**: Moonlit world with a single warm rectangle from the cabin window casting a small glow on the snow
- **Palette**: Midnight blue, snow grey-white, pine deep-green, warm window-amber
- **Motion**: Smoke plume meanders upward and dissipates (4s loop), one window light flickers gently every 7s, snow particles drift diagonally (LCM-locked to 8s). **Loop period**: 56s (LCM of 4, 7, 8).

**Final paragraph:**
> A small log cabin centered on the lower third of the frame, smoke rising from its chimney. Dense pine forest behind, mountains farther back, full moon high above. Cool moonlit blues dominate; the only warmth is a single amber rectangle of light from the cabin window, casting a small glow onto the snow in front. Smoke meanders up and dissipates in a 4-second cycle; the window flickers gently every 7 seconds; snow drifts diagonally on an 8-second cycle. The composite loop is 56 seconds, but no element is sync-detectable.

### Example C: Cyberpunk alleyway (mood ambient, looped)

**5-element block:**
- **Subject**: Single silhouetted figure standing far down the alley
- **Setting**: Narrow vertical alley between two tall buildings; neon sign hangs left, casting magenta on a puddle below
- **Lighting**: From the magenta sign and a single distant blue streetlamp; everything else in shadow
- **Palette**: Black (50%), wet-asphalt teal (25%), neon magenta (15%), cigarette ember orange (5%)
- **Motion**: Sign flickers irregularly (2s base + 3s base, LCM 6s); rain drops in vertical streaks at constant density; figure's cigarette ember dims and brightens (3s breathe). **Loop**: 6 seconds.

---

## 5. Writing for pixel-art constraints

The grid forces decisions. Description language must respect them.

| Canvas | Realistic content cap | Description should emphasize |
|---|---|---|
| **16×16** | 1 silhouette, 2 colors + outline | One concept, one accent color, no environment |
| **32×32** | 1 character + 1 accent, or 1 symbolic icon with 1 detail | Subject + palette only; setting is *implied* |
| **64×64** | Character + simple BG layer + 1 prop | Subject + minimal setting + lighting |
| **64×96** (book aspect) | Symbolic icon + 1-2 accent details + atmospheric BG | Cover-style; subject dominates upper 2/3, accent at bottom |
| **128×128** | Character + 2-3 BG depth layers + props + light source | Full 5-element framework |
| **256×256+** | Establishing shot territory | Multiple subjects, full motion specification |

**Color palette ceiling drives mood description.** A 4-color palette description should focus on which mood the palette implies rather than detail. "GameBoy DMG green palette" + "lonely traveler in fog" gives more than a list of objects.

---

## 6. Anti-patterns

| Anti-pattern | Why it fails | Fix |
|---|---|---|
| "Make it cool" | No constraints | Specify palette + 1 mood word |
| "A castle, dragon, knight, princess, sword, shield, moat..." | Pixel art reads silhouettes; >3 elements becomes mush | Pick 1-3 elements; let composition do the rest |
| "#3a4f2b for moss" | Generator can't perceive intent behind hex code | "Damp moss green" (perceptual term) |
| "Just the scene, static" (for animation) | Generator doesn't know what loops | Always add Motion element + period |
| Mixing pixel-art with photoreal language | Contradictory | Pick one; for pixel art use 8-bit/16-bit/NES/SNES anchors |
| Listing every visible asset | Pixel art is reductive; complete lists violate the medium | Describe iconographic essence, not asset count |

---

## 7. From narrative to scene description (worked example)

Input: 2-paragraph book synopsis for "Twilight" by Stephenie Meyer.

> Bella Swan, 17, moves to rainy Forks, Washington to live with her father. She meets Edward Cullen, a mysterious classmate, and slowly discovers he is a vampire — over 100 years old. The cover shows a pair of pale hands holding a red apple, a reference to the forbidden fruit of Genesis. Bella is drawn into a world of supernatural beings and forbidden love.

**Step 1: Identify canonical iconography**
- The synopsis explicitly mentions: "pale hands holding a red apple"
- Symbolism: forbidden fruit, knowledge of good and evil
- This is the Subject — no need to invent something else.

**Step 2: Build the 5-element block**
- **Subject**: Pale hands cupping a red apple, centered
- **Setting**: Deep dark void, no environment (cover composition — the icon IS the world)
- **Lighting**: Single warm highlight from upper-right on the apple; cool ambient moonlight on the hands
- **Palette**: Midnight black, ivory pale skin, skin shadow, deep crimson apple, apple highlight ivory-warm, single drifting petal in pale pink
- **Motion**: Highlight orbits the apple's surface in 4-second loop; once per loop a single petal drifts diagonally from above and fades at the bottom

**Step 3: Confirm the constraints fit the canvas**
- 64×96 book aspect, 6 colors, 2 motion elements (orbit + drift) — fits cleanly

**Step 4: Final paragraph (what goes into the canvas program comment)**
> A pair of pale, slender hands cup a perfect red apple in the center of the frame. The background is near-black night. The hands are bone-white, almost translucent — they catch a sliver of cold moonlight on their upper edges. The apple is glossy crimson with a tiny white highlight that suggests a single distant light source. The animation: the highlight on the apple's surface rotates slowly, as if the world tilts around it. Once per loop, a single apple-blossom petal drifts past from above and vanishes off-screen. Loop period: 4 seconds.

**This is now ready for the canvas program.**

---

## 8. Sources

- [I Draw Wearing Hats - Hyper Light Drifter Art Direction](http://idrawwearinghats.blogspot.com/2014/04/art-direction-analysis-of-hyper-light.html)
- [Wikipedia - Thomas Was Alone](https://en.wikipedia.org/wiki/Thomas_Was_Alone)
- [Saint11 - Consistency](https://saint11.art/blog/consistency/)
- [Daniel Silber - Pixel Art for Game Developers](https://www.routledge.com/Pixel-Art-for-Game-Developers/Silber/p/book/9781482252309)
- Twilight cover symbolism: [eNotes](https://www.enotes.com/topics/twilight/questions/what-do-all-cover-pages-book-signify-269473), [Screen Rant](https://screenrant.com/twilight-midnight-sun-books-covers-meanings-explained/)
