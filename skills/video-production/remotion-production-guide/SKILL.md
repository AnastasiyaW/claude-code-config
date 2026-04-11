---
description: "Remotion (React video framework) production guide with Apple-style design rules. Use when: 'create video with remotion', 'remotion project', 'render video', 'product demo video', 'animated video', 'video from code'. Covers project setup, animation library, spring presets, typography rules, color palettes, pacing tables, scene templates, 3D integration, and export settings for all platforms."
---

# Remotion Production Guide

Complete reference for creating production-quality videos with Remotion. Combines Apple-style design rules, motion design principles, and battle-tested animation patterns.

## Quick Start

```bash
mkdir -p src && npm init -y
npm install --save-exact remotion @remotion/cli react react-dom typescript @types/react
echo "node_modules/\ndist/\nout/\n.cache/" > .gitignore
```

## Project Structure

```
src/
  index.ts          # registerRoot
  Root.tsx           # Composition registration
  videos/
    ProductDemo/
      index.tsx      # Main composition
      scenes/        # One file per scene
      components/    # Reusable visual elements
  lib/
    constants.ts     # ALL editable values (colors, timing, fonts, sizes)
    animations.ts    # Reusable animation helpers
  public/            # Static assets (images, music, sounds)
```

## Constants-First Design

**ALWAYS** define all values in `constants.ts`. Never hardcode in components:

```tsx
export const COLORS = {
  bg: '#000000',
  text: '#FFFFFF',
  accent: '#007AFF',
  muted: '#8E8E93',
  cardBg: '#1C1C1E',
} as const;

export const TIMING = {
  fps: 30,
  fadeIn: 15,        // 500ms
  fadeOut: 12,       // 400ms
  stagger: 4,        // 133ms between items
} as const;

export const SIZES = {
  heroText: 120,     // px
  titleText: 72,
  subtitleText: 42,
  bodyText: 28,
  captionText: 20,   // NEVER below 16
} as const;
```

## Animation Library

```tsx
import { interpolate, spring, Easing } from 'remotion';

// --- Opacity ---
export const fadeIn = (frame: number, delay = 0, duration = 15) =>
  interpolate(frame, [delay, delay + duration], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

// --- Movement ---
export const slideUp = (frame: number, delay = 0, distance = 40) =>
  interpolate(frame, [delay, delay + 20], [distance, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

// --- Scale ---
export const scalePop = (frame: number, fps: number, delay = 0) =>
  Math.min(spring({ frame: frame - delay, fps, config: { damping: 12, mass: 0.5 } }), 1);

// --- Stagger ---
export const stagger = (index: number, base = 0, gap = 4) => base + index * gap;

// --- Counter ---
export const countTo = (frame: number, target: number, delay = 0, duration = 30) =>
  Math.round(target * interpolate(frame, [delay, delay + duration], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  }));
```

## Spring Presets

| Name | Config | Use Case |
|------|--------|----------|
| Smooth | `{ damping: 200 }` | Default transitions |
| Snappy | `{ damping: 20, stiffness: 200 }` | Quick appearances |
| Bouncy | `{ damping: 8, stiffness: 200 }` | Playful elements (badges, icons) |
| Gentle | `{ damping: 200, stiffness: 50 }` | Large elements (product images) |

## Typography Rules

| Role | Size | Weight | Timing on Screen |
|------|------|--------|-----------------|
| Hero number/stat | 120-200px | 800-900 | 3-5 seconds |
| Section title | 64-80px | 600 | 2-4 seconds |
| Subtitle | 36-48px | 500 | 2-3 seconds |
| Body text | 24-32px | 400 | min 2 seconds |
| Caption | 16-20px | 400 | min 1.5 seconds |
| NEVER | <16px | - | - illegible on video |

**Rules:**
- Letter-spacing: -1 to -2px for large text (>48px)
- Line-height: 1.1-1.2 for headings, 1.4 for body
- Max 7 words on screen simultaneously
- NEVER animate text while expecting reading
- Font: Inter, Geist Sans, or system-ui

## Animation Timing

| Type | Frames @30fps | ms |
|------|--------------|------|
| Text fade in | 9-15 | 300-500 |
| Text fade out | 6-12 | 200-400 |
| Slide in | 12-18 | 400-600 |
| Product appear | 18-30 | 600-1000 |
| Scale pop | 6-12 | 200-400 |
| Scene transition | 9-15 | 300-500 |
| Item stagger | 2-4 | 67-133 |

## Easing Reference

| Use Case | Easing |
|----------|--------|
| Element entering | `Easing.out(Easing.cubic)` |
| Element exiting | `Easing.in(Easing.cubic)` |
| Apple-style | `Easing.bezier(0.25, 0.1, 0.25, 1.0)` |
| Dramatic enter | `Easing.bezier(0.05, 0.7, 0.1, 1.0)` |
| Material Standard | `Easing.bezier(0.4, 0.0, 0.2, 1.0)` |
| NEVER | `linear` (except progress bars) |

## Color Palettes

**Dark theme (premium/tech):** bg #000/#0A0A0A, text #FFF, accent from brand
**Light theme (consumer/clean):** bg #F5F3EF/#FFF, text #1D1D1F, accent from brand

- Max 3 colors + black/white/gray
- Background:text contrast min 7:1
- Use `linear-gradient` for premium text (`WebkitBackgroundClip: 'text'`)

## Scene Pacing

| Format | Total | Scenes | Frame Budget @30fps |
|--------|-------|--------|-------------------|
| 15s teaser | 450 frames | 5 | ~90 each |
| 30s demo | 900 frames | 5 | ~180 each |
| 60s launch | 1800 frames | 7 | ~260 each |

**Breathing rule:** After 3+ fast cuts, add one slow shot (5-8s). Alternate rhythm: FAST→SLOW→MEDIUM.

## Cross-Fade Wrapper

```tsx
const Fade: React.FC<{ children: React.ReactNode; dur: number; fade?: number }> = 
  ({ children, dur, fade = 15 }) => {
  const frame = useCurrentFrame();
  const inVal = interpolate(frame, [0, fade], [0, 1], { extrapolateRight: 'clamp' });
  const outVal = interpolate(frame, [dur - fade, dur], [1, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  return <AbsoluteFill style={{ opacity: Math.min(inVal, outVal) }}>{children}</AbsoluteFill>;
};
```

## 3D Integration

```bash
# React Three Fiber in Remotion:
npm install @remotion/three @react-three/fiber three @types/three

# Lottie animations:
npm install @remotion/lottie lottie-web
```

- Use `<ThreeCanvas>` (not `<Canvas>`) for R3F in Remotion
- Use `useCurrentFrame()` instead of R3F's `useFrame()` 
- Spline: design in spline.design, export to R3F, import via @remotion/three

## Export Settings

| Platform | Resolution | Aspect | Command |
|----------|-----------|--------|---------|
| YouTube | 1920x1080 | 16:9 | default |
| TikTok/Reels | 1080x1920 | 9:16 | `--width 1080 --height 1920` |
| Instagram Square | 1080x1080 | 1:1 | `--width 1080 --height 1080` |

```bash
# High quality master
npx remotion render src/index.ts CompositionId out/video.mp4

# Custom quality (CRF 18 = high, 28 = web preview)
npx remotion render src/index.ts CompositionId out/video.mp4 --crf 18
```

Universal: MP4 container, H.264, AAC audio, yuv420p.

## Critical Rules

- **NEVER** use CSS transitions/animations - won't render during export
- **ALWAYS** use `useCurrentFrame()` + `interpolate()` or `spring()`
- **ALWAYS** `extrapolateRight: 'clamp'` to prevent overshoot
- `spring()` never reaches exactly 1.0 - use `Math.min(spring(...), 1)` for scale
- Use `<Img>` from remotion (not `<img>`) for reliable image loading
- First render downloads Chrome Headless Shell (~108MB), subsequent use cache
- Google Fonts: use `@remotion/google-fonts` for reliable loading

## DON'T List

- Don't rotate text
- Don't bounce text (unless playful brand)
- Don't animate 3+ elements simultaneously  
- Don't use more than 2 animation styles per video
- Don't use star wipes or random transitions
- Don't put more than 7 words on screen at once
- Don't start with a logo (start with the hook)
- Don't commit node_modules
