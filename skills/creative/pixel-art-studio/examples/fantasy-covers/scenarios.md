# Fantasy Book Covers — Scene Scenarios

Three classic fantasy covers reinterpreted for animated pixel art. Each scene uses
the 5-element framework (Subject + Setting + Lighting + Palette + Motion) and
references real cover iconography.

---

## Cover 1: The Lord of the Rings: The Fellowship of the Ring (Tolkien, 1954)

**Real cover iconography**:
> The original 1954 dust-jacket designed by Tolkien himself: One Ring with
> Eye of Sauron at centre; around it the red Tengwar inscription in Black
> Speech; small Narya (red-jewelled Elven ring) faces the One Ring opposite.
> Source: tolkiengateway.net/wiki/The_Lord_of_the_Rings/Original_dust-jacket_designs

**Our 5-element scene**:
- **Subject**: One Ring centered (gold band, ~22px wide), with Eye of Sauron
  carved inside (small red glowing slit). Faint Tengwar inscription circles
  the outside, glowing red-warm.
- **Setting**: Deep Mordor sky — near-black with violet undertone, scattered
  cool stars (sparse, 30-40), dark mountain silhouette at horizon.
- **Lighting**: Warm glow emanates from INSIDE the ring (fire-light), casts
  faint warm aura around the band. Rest of scene cold, no other light source.
- **Palette**: `design-seeds/heavenly-hues` — deep navy (#1B1E3E) → mid
  blue (#1D3052, #2B4D6B, #37596E) for sky gradient + warm gold
  (#E3C170, #FAD493) for ring + gold inscription. Eye = red-warm crimson
  added (#c83048).
- **Motion**: Ring rotates slowly (8s = full revolution); inscription glow
  pulses brighter every 2s (multi-component sin); 3-5 embers drift up from
  below (deterministic, seeded RNG).
- **Loop**: 8000ms.

---

## Cover 2: A Game of Thrones (Martin, 1996)

**Real cover iconography**:
> Original 1996 Bantam dust-jacket: silver/blue metallic mirror, abstract.
> Cultural iconography — what readers think of when they hear "GoT": Iron
> Throne (jagged sword-formed throne), House Stark direwolf, cold north,
> snow. We use the iconic Iron Throne in cold north because the original
> abstract cover doesn't read as pixel art.

**Our 5-element scene**:
- **Subject**: Iron Throne silhouette centered slightly lower-third
  (jagged peaks of swords forming the back, ~32px tall). Just a silhouette
  — no figure on it.
- **Setting**: Cold winter sky (overcast slate blue → pale near horizon),
  Wall-style tower silhouette behind (smaller, even further back, almost
  imperceptible), snow-covered ground at base.
- **Lighting**: Overcast cold daylight (no direct sun). Single warm torch
  on left side of throne casts amber glow on left flank of metal — chromatic
  anchor against the otherwise cold scene.
- **Palette**: Custom "frost-iron" — `#0a0e1c` (deepest sky), `#1a2a40`
  (dark steel), `#3a4858` (mid steel), `#6a7a8a` (cold light steel),
  `#c0d0e0` (snow highlight), `#e8a050` (warm amber torch — single accent).
- **Motion**: Snow falls (12 deterministic particles, slow drift); torch
  flame flickers (2s sub-cycle, multi-component sin); one raven silhouette
  flies across the upper third (8s = one pass).
- **Loop**: 8000ms.

---

## Cover 3: The Name of the Wind (Rothfuss, 2007)

**Real cover iconography**:
> Gollancz UK cover: hooded central figure with bloody red eyes, twisted
> vines framing it, dark and unsettling. Various editions feature Kvothe
> with a lute on misty/mountain backdrop. We use the hooded figure
> silhouette + autumn forest because it's the most iconic and pixel-friendly.
> Source: en.wikipedia.org/wiki/The_Name_of_the_Wind

**Our 5-element scene**:
- **Subject**: Hooded figure silhouette (full cloak, head down or facing
  wind, ~24×40px tall), centered slightly off-axis (rule of thirds).
- **Setting**: Autumn forest at dusk — tall thin tree silhouettes left
  and right (mid-depth), scattered stars upper third (sparse, ~25),
  autumn ground line at bottom.
- **Lighting**: Soft amber glow from lower-left (hidden campfire, just
  out of frame). Cool ambient overall. Single warm pixel on figure's
  forward-facing edge.
- **Palette**: `design-seeds/rose-palette` (browns/dusty rose/sage from
  catalog) — #FBE9E3 (sky highlight), #FBCFCA, #F4B9B9 (mid pinks),
  #8A8F75 (sage tree), #7B5F52 (brown trunk), #E6DCD8 (cloak highlight),
  + #d68030 (warm amber from hidden campfire — single accent).
- **Motion**: Cloak edge ripples (sub-pixel breathing on right-side AA
  pixels — Metal Slug technique); 5-7 autumn leaves drift down from
  upper-right diagonally (deterministic, varying speed); single tree
  sways minutely (1px shift over 6s).
- **Loop**: 6000ms (intentional asynchrony with the two 8s loops above
  → composite period 24s, no mechanical sync).

---

## Cross-cover design notes

**Visual variety across the 3 covers**:
- LOTR = object-focused (the Ring), warm glow, mystical
- GoT = silhouette-focused (Iron Throne), cold + single warm anchor
- NoW = character-focused (Hooded figure), autumn melancholy

**Palette source diversity**:
- 2 of 3 use Design Seeds curated palettes (validating the catalog usage)
- 1 (GoT) uses custom — demonstrates extensibility

**Loop period diversity**:
- 8s × 2 covers
- 6s × 1 cover
- LCM = 24s — composite has no perceptible sync, feels organic

**Each cover passes the 8-layer retouch standard**:
1. Sky gradient (multi-stop)
2. Atmospheric particles (stars / snow / leaves)
3. Far depth (mountains / wall / forest)
4. Mid depth (tree silhouettes / throne back)
5. Subject (Ring / Throne / Hooded figure)
6. Surface detail on subject (inscription / sword spikes / cloak folds)
7. Foreground motion (embers / snow / leaves)
8. Atmospheric overlay (vignette + warm-cool tint)

## Source references

- LOTR cover: [Tolkien Gateway - LOTR Original dust-jacket designs](https://tolkiengateway.net/wiki/The_Lord_of_the_Rings/Original_dust-jacket_designs)
- GoT 1996 first edition: bibliographic detail from AbeBooks / Bantam Spectra
- The Name of the Wind cover: [Wikipedia](https://en.wikipedia.org/wiki/The_Name_of_the_Wind), [Sense Noi tumblr cover review](https://sensenoi.tumblr.com/post/625727324470525952/rating-every-single-name-of-the-wind-cover)
- Design Seeds catalog: [design-seeds.com](https://www.design-seeds.com/) (palettes © Jessica Colaluca, used here for inspirational reference)
