# Extended JSON Schema Specification

This document defines the complete schema for the pixel-art-studio renderer. All files consumed by `scripts/render.py`, `scripts/animate.py`, and `scripts/quality_check.py --animation` must conform to this schema.

---

## 1. Top-level schema

```json
{
  "$schema": "pixel-art-studio/v1",

  "width": 32,
  "height": 32,
  "background": "transparent",
  "pixel_size": 16,
  "grid_lines": false,

  "palette_ref": "endesga-32",
  "palette": ["#FF0000", "#00FF00"],

  "pixels": [...],

  "frames": [...],
  "tags": [...],

  "layers": [...]
}
```

---

## 2. Field reference

### Canvas fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `$schema` | string | No | — | Must be `"pixel-art-studio/v1"` if present |
| `width` | integer | **Yes** | — | 1 ≤ width ≤ 4096 |
| `height` | integer | **Yes** | — | 1 ≤ height ≤ 4096 |
| `background` | color | No | `"transparent"` | See color types below |
| `pixel_size` | integer | No | `1` | 1 ≤ pixel_size ≤ 64. Logical→output multiplier. 16 = each logical pixel rendered as 16×16 block. |
| `grid_lines` | boolean | No | `false` | If true, render 1px gray lines between logical pixels (debug mode) |

**pixel_size notes**: This implements the Punch Club rule — master artwork at 1×, render at N×. `pixel_size: 16` renders a 32×32 sprite as a 512×512 PNG. Default `pixel_size: 1` renders at 1:1 (usually too small to view). Recommended preview value: **16** for 32×32 sprites, **8** for 64×64 sprites.

### Palette fields

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `palette_ref` | string | No | — | Name of a bundled palette (e.g., `"endesga-32"`). Enables palette validation. |
| `palette` | array[color] | No | — | Explicit palette array. Mutually inclusive with `palette_ref` — if both present, `palette` overrides for rendering but `palette_ref` is used for validation. |

**At least one of `palette_ref` or `palette` should be specified** to enable quality checks. Omitting both disables palette-discipline validation.

**Bundled palette names** (from `scripts/palette.py --list`):
- Hardware: `nes`, `gameboy-dmg`, `gameboy-pocket`, `pico-8`, `ega`, `cga`
- Lospec: `db16`, `db32`, `aap-64`, `endesga-32`, `endesga-64`, `sweetie-16`, `resurrect-64`, `apollo`, `steam-lords`, `slso8`, `nyx8`
- Cultural: `obangsaek`, `gugong-red-wall`, `qinghua`, `wuxing`, `stoneshard-inspired`, `danching`

### Pixel data: static sprite

`pixels` and `frames` are mutually exclusive. Use `pixels` for single-frame sprites.

```json
"pixels": [
  {"x": 0, "y": 0, "color": "#FF0000"},
  {"x": 1, "y": 0, "color": "#00FF00"},
  {"x": 0, "y": 1, "color": "transparent"}
]
```

| Field | Type | Required | Constraints |
|---|---|---|---|
| `pixels` | array[pixel] | Conditionally yes | Required unless `frames` or `layers` present |
| `pixel.x` | integer | Yes | 0 ≤ x < width |
| `pixel.y` | integer | Yes | 0 ≤ y < height |
| `pixel.color` | color | Yes | See color types below |

**Sparse format**: only specify non-transparent pixels. Unspecified positions default to `background` color.

### Pixel data: animation frames

Use `frames` instead of `pixels` for animated sprites.

```json
"frames": [
  {
    "id": 0,
    "duration_ms": 125,
    "name": "contact",
    "pixels": [
      {"x": 5, "y": 2, "color": "#C87941"}
    ]
  },
  {
    "id": 1,
    "duration_ms": 125,
    "name": "recoil",
    "pixels": [...]
  }
]
```

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `frames` | array[frame] | Conditionally yes | — | Required for animation; mutually exclusive with top-level `pixels` |
| `frame.id` | integer | Yes | — | 0-indexed, sequential |
| `frame.duration_ms` | integer | Yes | — | Must be > 0. Common values: 83 (12fps), 100 (10fps), 125 (8fps), 167 (6fps), 200 (5fps CN) |
| `frame.name` | string | No | — | Human-readable label (e.g., `"contact"`, `"recoil"`, `"passing"`, `"high-point"`) |
| `frame.pixels` | array[pixel] | Yes | — | Same format as static `pixels` |

### Tags (animation ranges)

```json
"tags": [
  {
    "name": "walk",
    "from": 0,
    "to": 3,
    "direction": "forward"
  },
  {
    "name": "idle",
    "from": 4,
    "to": 7,
    "direction": "pingpong"
  }
]
```

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `tags` | array[tag] | No | — | Optional; requires `frames` to be meaningful |
| `tag.name` | string | Yes | — | Identifier used in CLI export (`--tag walk`) |
| `tag.from` | integer | Yes | — | First frame ID (inclusive) |
| `tag.to` | integer | Yes | — | Last frame ID (inclusive); must be >= from |
| `tag.direction` | direction | No | `"forward"` | `"forward"` \| `"reverse"` \| `"pingpong"` |

**direction enum**:
| Value | Behavior |
|---|---|
| `"forward"` | Play frames from→to in order, loop |
| `"reverse"` | Play frames to→from in reverse order, loop |
| `"pingpong"` | Play forward then backward, loop at both ends |

This maps 1:1 to Aseprite's tag direction modes.

### Layers (multi-layer sprites)

Layers are rendered bottom-to-top (index 0 = bottom layer).

```json
"layers": [
  {
    "name": "body",
    "visible": true,
    "opacity": 1.0,
    "pixels": [...]
  },
  {
    "name": "sleeve",
    "visible": true,
    "opacity": 1.0,
    "frames": [
      {"id": 0, "duration_ms": 200, "pixels": [...]},
      {"id": 1, "duration_ms": 200, "pixels": [...]}
    ]
  }
]
```

| Field | Type | Required | Default | Constraints |
|---|---|---|---|---|
| `layers` | array[layer] | No | — | Mutually inclusive with `pixels` or `frames` on same object |
| `layer.name` | string | No | `"Layer N"` | Human-readable label |
| `layer.visible` | boolean | No | `true` | If false, layer is skipped in render |
| `layer.opacity` | float | No | `1.0` | 0.0 (fully transparent) to 1.0 (fully opaque). Applied via alpha blending. |
| `layer.pixels` | array[pixel] | Conditionally | — | For static layers |
| `layer.frames` | array[frame] | Conditionally | — | For animated layers. Must use same frame IDs as sibling animated layers. |

**Blending**: layers composite using standard Porter-Duff "source over" alpha blending at each pixel position.

---

## 3. Color types

All `color` fields accept any of the following formats:

### Hex strings

| Format | Example | Notes |
|---|---|---|
| `#RRGGBB` | `"#FF0000"` | Full 6-digit hex, no alpha (fully opaque) |
| `#RRGGBBAA` | `"#FF000080"` | 8-digit hex with alpha (80 = 50% opacity) |
| `#RGB` | `"#F00"` | 3-digit shorthand; expands to `#FF0000` |
| `#RGBA` | `"#F008"` | 4-digit shorthand; expands to `#FF000088` |

### Named colors

CSS named colors are accepted: `"red"`, `"blue"`, `"white"`, `"black"`, etc. Resolved via CSS Color Level 4 named color list. **Not recommended for production** — prefer hex for precision.

### Special values

| Value | Meaning |
|---|---|
| `"transparent"` | Fully transparent (RGBA 0,0,0,0) |

### Array format

```json
[R, G, B]          // integers 0-255, fully opaque
[R, G, B, A]       // integers 0-255, A=0 transparent, A=255 opaque
```

Example: `[255, 0, 0]` = `"#FF0000"`.

---

## 4. Direction enum

Used in `tag.direction`:

| Value | Type | Notes |
|---|---|---|
| `"forward"` | string | Default; play from→to |
| `"reverse"` | string | Play to→from |
| `"pingpong"` | string | Bounce; also written `"ping-pong"` (both accepted) |

---

## 5. Examples

### Example 1: Minimal 8×8 heart (static sprite)

```json
{
  "$schema": "pixel-art-studio/v1",
  "width": 8,
  "height": 8,
  "background": "transparent",
  "pixel_size": 16,
  "palette_ref": "pico-8",
  "pixels": [
    {"x": 1, "y": 1, "color": "#FF004D"},
    {"x": 2, "y": 1, "color": "#FF004D"},
    {"x": 4, "y": 1, "color": "#FF004D"},
    {"x": 5, "y": 1, "color": "#FF004D"},
    {"x": 0, "y": 2, "color": "#FF004D"},
    {"x": 1, "y": 2, "color": "#FF77A8"},
    {"x": 2, "y": 2, "color": "#FF004D"},
    {"x": 3, "y": 2, "color": "#FF004D"},
    {"x": 4, "y": 2, "color": "#FF004D"},
    {"x": 5, "y": 2, "color": "#FF77A8"},
    {"x": 6, "y": 2, "color": "#FF004D"},
    {"x": 0, "y": 3, "color": "#FF004D"},
    {"x": 1, "y": 3, "color": "#FF004D"},
    {"x": 2, "y": 3, "color": "#FF004D"},
    {"x": 3, "y": 3, "color": "#FF004D"},
    {"x": 4, "y": 3, "color": "#FF004D"},
    {"x": 5, "y": 3, "color": "#FF004D"},
    {"x": 6, "y": 3, "color": "#FF004D"},
    {"x": 1, "y": 4, "color": "#FF004D"},
    {"x": 2, "y": 4, "color": "#FF004D"},
    {"x": 3, "y": 4, "color": "#FF004D"},
    {"x": 4, "y": 4, "color": "#FF004D"},
    {"x": 5, "y": 4, "color": "#FF004D"},
    {"x": 2, "y": 5, "color": "#FF004D"},
    {"x": 3, "y": 5, "color": "#FF004D"},
    {"x": 4, "y": 5, "color": "#FF004D"},
    {"x": 3, "y": 6, "color": "#FF004D"}
  ]
}
```

**Shape**: PICO-8 red heart. Highlight at (1,2) and (5,2) uses `#FF77A8` (PICO-8 pink) for single-pixel specular.

Render: `python scripts/render.py heart.json -o heart.png`
Output: 128×128 PNG (8px × 16px/pixel).

---

### Example 2: 4-frame walk cycle (animation)

A 32×32 character, Western indie standard, 8fps walk with Shovel Knight-style frame structure.

```json
{
  "$schema": "pixel-art-studio/v1",
  "width": 32,
  "height": 32,
  "background": "transparent",
  "pixel_size": 8,
  "palette_ref": "endesga-32",
  "frames": [
    {
      "id": 0,
      "duration_ms": 125,
      "name": "contact",
      "pixels": [
        {"x": 15, "y": 4, "color": "#F5A623"},
        {"x": 15, "y": 5, "color": "#C87941"},
        {"x": 16, "y": 5, "color": "#F5A623"},
        {"x": 15, "y": 6, "color": "#8B4726"},
        {"x": 16, "y": 6, "color": "#C87941"}
      ]
    },
    {
      "id": 1,
      "duration_ms": 125,
      "name": "recoil",
      "pixels": [
        {"x": 15, "y": 5, "color": "#F5A623"},
        {"x": 15, "y": 6, "color": "#C87941"},
        {"x": 16, "y": 6, "color": "#F5A623"},
        {"x": 15, "y": 7, "color": "#8B4726"},
        {"x": 16, "y": 7, "color": "#C87941"}
      ]
    },
    {
      "id": 2,
      "duration_ms": 125,
      "name": "passing",
      "pixels": [
        {"x": 15, "y": 4, "color": "#F5A623"},
        {"x": 16, "y": 4, "color": "#F5A623"},
        {"x": 15, "y": 5, "color": "#C87941"},
        {"x": 16, "y": 5, "color": "#C87941"},
        {"x": 15, "y": 6, "color": "#8B4726"},
        {"x": 16, "y": 6, "color": "#8B4726"}
      ]
    },
    {
      "id": 3,
      "duration_ms": 125,
      "name": "high-point",
      "pixels": [
        {"x": 14, "y": 4, "color": "#F5A623"},
        {"x": 15, "y": 4, "color": "#F5A623"},
        {"x": 14, "y": 5, "color": "#C87941"},
        {"x": 15, "y": 5, "color": "#C87941"},
        {"x": 14, "y": 6, "color": "#8B4726"},
        {"x": 15, "y": 6, "color": "#8B4726"}
      ]
    }
  ],
  "tags": [
    {
      "name": "walk",
      "from": 0,
      "to": 3,
      "direction": "forward"
    }
  ]
}
```

Render animated GIF: `python scripts/animate.py walk.json --format gif -o walk.gif`
Render sprite sheet: `python scripts/animate.py walk.json --format spritesheet --layout horizontal -o walk_sheet.png`

---

### Example 3: 2-layer character with separate body + sleeve animations (advanced)

A 48×72 CN mobile RPG character (xianxia robe style). Body is static; sleeve has a 2-frame flutter animation with 1-frame offset from walk cycle.

```json
{
  "$schema": "pixel-art-studio/v1",
  "width": 48,
  "height": 72,
  "background": "transparent",
  "pixel_size": 4,
  "palette_ref": "qinghua",
  "layers": [
    {
      "name": "body",
      "visible": true,
      "opacity": 1.0,
      "pixels": [
        {"x": 23, "y": 8,  "color": "#1A3F7E"},
        {"x": 24, "y": 8,  "color": "#1A3F7E"},
        {"x": 23, "y": 9,  "color": "#4A6FA5"},
        {"x": 24, "y": 9,  "color": "#4A6FA5"},
        {"x": 22, "y": 10, "color": "#1A3F7E"},
        {"x": 23, "y": 10, "color": "#F5F0E1"},
        {"x": 24, "y": 10, "color": "#F5F0E1"},
        {"x": 25, "y": 10, "color": "#1A3F7E"}
      ]
    },
    {
      "name": "sleeve-left",
      "visible": true,
      "opacity": 1.0,
      "frames": [
        {
          "id": 0,
          "duration_ms": 200,
          "name": "sleeve-down",
          "pixels": [
            {"x": 18, "y": 20, "color": "#1A3F7E"},
            {"x": 17, "y": 21, "color": "#1A3F7E"},
            {"x": 16, "y": 22, "color": "#4A6FA5"},
            {"x": 15, "y": 23, "color": "#1A3F7E"}
          ]
        },
        {
          "id": 1,
          "duration_ms": 200,
          "name": "sleeve-out",
          "pixels": [
            {"x": 17, "y": 20, "color": "#1A3F7E"},
            {"x": 16, "y": 21, "color": "#1A3F7E"},
            {"x": 15, "y": 22, "color": "#4A6FA5"},
            {"x": 14, "y": 23, "color": "#1A3F7E"}
          ]
        }
      ]
    },
    {
      "name": "sleeve-right",
      "visible": true,
      "opacity": 1.0,
      "frames": [
        {
          "id": 0,
          "duration_ms": 200,
          "name": "sleeve-down",
          "pixels": [
            {"x": 30, "y": 20, "color": "#1A3F7E"},
            {"x": 31, "y": 21, "color": "#1A3F7E"},
            {"x": 32, "y": 22, "color": "#4A6FA5"},
            {"x": 33, "y": 23, "color": "#1A3F7E"}
          ]
        },
        {
          "id": 1,
          "duration_ms": 200,
          "name": "sleeve-out",
          "pixels": [
            {"x": 31, "y": 20, "color": "#1A3F7E"},
            {"x": 32, "y": 21, "color": "#1A3F7E"},
            {"x": 33, "y": 22, "color": "#4A6FA5"},
            {"x": 34, "y": 23, "color": "#1A3F7E"}
          ]
        }
      ]
    }
  ],
  "tags": [
    {
      "name": "sleeve-flutter",
      "from": 0,
      "to": 1,
      "direction": "pingpong"
    }
  ]
}
```

The body layer uses static `pixels`; the sleeve layers use `frames` with `pingpong` direction for a continuous flutter effect. Render: `python scripts/render.py --flatten robe_char.json -o frame0.png` or `python scripts/animate.py robe_char.json --format apng -o robe_anim.apng`.

---

## 6. Validation rules

`render.py` and `animate.py` perform these validations before rendering:

| Check | Error | Message |
|---|---|---|
| `width` and `height` present | Error | "width and height are required" |
| `pixels` XOR `frames` at top level (or `layers` present) | Error | "specify exactly one of: pixels, frames, or layers" |
| Pixel x in [0, width) | Error | "pixel x=N out of bounds (width=W)" |
| Pixel y in [0, height) | Error | "pixel y=N out of bounds (height=H)" |
| Tag.from <= tag.to | Error | "tag 'name': from must be <= to" |
| Tag references valid frame IDs | Error | "tag 'name': frame ID N not found" |
| Frame IDs are sequential from 0 | Warning | "frame IDs are not sequential — animation may be out of order" |
| `palette_ref` matches known palette name | Warning | "unknown palette_ref 'xyz' — palette validation disabled" |
| Color string is valid | Error | "invalid color value: 'xyz'" |
| `pixel_size` in [1, 64] | Error | "pixel_size must be between 1 and 64" |
| `opacity` in [0.0, 1.0] | Error | "layer opacity must be between 0.0 and 1.0" |

---

## 7. CLI render commands

```bash
# Static sprite
python scripts/render.py sprite.json -o sprite.png

# Animation: GIF
python scripts/animate.py walk.json --format gif -o walk.gif

# Animation: APNG (better quality, transparency)
python scripts/animate.py walk.json --format apng -o walk.apng

# Animation: sprite sheet (horizontal, all frames)
python scripts/animate.py walk.json --format spritesheet --layout horizontal -o sheet.png

# Animation: sprite sheet (grid layout, 4 cols)
python scripts/animate.py walk.json --format spritesheet --layout grid --cols 4 -o sheet.png

# Export only one tag
python scripts/animate.py char.json --tag walk --format gif -o walk.gif

# Flatten multi-layer to single-frame PNG
python scripts/render.py --flatten --frame 0 layers.json -o frame0.png
```
