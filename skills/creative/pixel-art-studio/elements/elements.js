/**
 * Pixel Art Studio - Element Library
 *
 * Reusable pixel-art elements for canvas-based scene composition.
 *
 * Each element function has signature: drawXxx(ctx, x, y, opts)
 * - ctx: canvas 2D context
 * - x, y: anchor position (interpretation depends on element)
 * - opts: { variant, palette, scale, t (animation phase 0..1), seed, ...element-specific }
 *
 * Scenes are declarative arrays of element calls:
 *   const scene = [
 *     {el: "sky", variant: "dusk"},
 *     {el: "mountain-range", x: 0, y: 220, variant: "far"},
 *     {el: "tower", x: 96, y: 90, variant: "stone", windows: 12},
 *     ...
 *   ];
 *   renderScene(ctx, W, H, scene, t);
 *
 * To preview all elements + variants: open elements/catalog.html
 */

// =============================================================
// SHARED HELPERS (mirror of helpers in render.py / bake_animation.py)
// =============================================================

const HEX_CACHE = new Map();
function hex(c) {
  const cached = HEX_CACHE.get(c);
  if (cached) return cached;
  let r = 0, g = 0, b = 0;
  if (typeof c === 'string' && c.charAt(0) === '#' && c.length >= 7) {
    r = parseInt(c.substr(1, 2), 16);
    g = parseInt(c.substr(3, 2), 16);
    b = parseInt(c.substr(5, 2), 16);
  }
  const result = [r, g, b];
  if (HEX_CACHE.size < 4096) HEX_CACHE.set(c, result);
  return result;
}
function rgb(r, g, b) {
  const h = n => Math.max(0, Math.min(255, n | 0)).toString(16).padStart(2, '0');
  return '#' + h(r) + h(g) + h(b);
}
function mix(a, b, t) {
  const A = hex(a), B = hex(b);
  return rgb(A[0]+(B[0]-A[0])*t, A[1]+(B[1]-A[1])*t, A[2]+(B[2]-A[2])*t);
}
function rect(ctx, x, y, w, h, c) { ctx.fillStyle = c; ctx.fillRect(x|0, y|0, w|0, h|0); }
function px(ctx, x, y, c) { ctx.fillStyle = c; ctx.fillRect(x|0, y|0, 1, 1); }
function hash(n) { const x = Math.sin(n * 12.9898) * 43758.5453; return x - Math.floor(x); }

function seededRandom(seed) {
  let s = seed | 0;
  return function() {
    s = (s * 1664525 + 1013904223) | 0;
    return ((s >>> 8) & 0xffffff) / 0xffffff;
  };
}

// =============================================================
// PALETTES — semantic palette references
// =============================================================

const PALETTES = {
  // Generic moods (each maps colors to semantic roles)
  "dusk-cool":   { bg1:"#080612", bg2:"#1a1a3a", bg3:"#3a3a60", bg4:"#7a7080",
                   stone:"#2a2838", stoneLight:"#3a3848", stoneDark:"#1a1820",
                   snow:"#c0d0e0", snowDim:"#a0b0c0",
                   warm:"#ff8040", warmGlow:"#ff9050",
                   pine:"#0a1218", pineMid:"#1a2230",
                   star:"#FAD493", starDim:"#7a6890" },
  "dawn-warm":   { bg1:"#3a1418", bg2:"#7a3030", bg3:"#c87060", bg4:"#fdae34",
                   stone:"#5a4848", stoneLight:"#7a6868", stoneDark:"#3a2828",
                   snow:"#fef0e0", snowDim:"#e8d8c8",
                   warm:"#ff8040", warmGlow:"#ffb060",
                   pine:"#2a1818", pineMid:"#5a3838",
                   star:"#FAD493", starDim:"#a89880" },
  "midnight":    { bg1:"#020108", bg2:"#08051a", bg3:"#120822", bg4:"#1c0a18",
                   stone:"#1a1820", stoneLight:"#2a2830", stoneDark:"#0a0810",
                   snow:"#a8b0c0", snowDim:"#80889c",
                   warm:"#a8a0c0", warmGlow:"#d0c8e0",
                   pine:"#000408", pineMid:"#080812",
                   star:"#e8d8f8", starDim:"#5a4868" },
  "autumn":      { bg1:"#3a2438", bg2:"#5a3a4a", bg3:"#7B5F52", bg4:"#8A8F75",
                   stone:"#4a3a30", stoneLight:"#6a5848", stoneDark:"#2a1a18",
                   snow:"#FBE9E3", snowDim:"#C7A49F",
                   warm:"#d68030", warmGlow:"#e8a050",
                   pine:"#2a1820", pineMid:"#5a3838",
                   star:"#FBE9E3", starDim:"#5a3838" },
};

// =============================================================
// ELEMENT 1: SKY (multi-stop gradient)
// Variants: dusk-cool, dawn-warm, midnight, autumn
// =============================================================

function drawSky(ctx, x, y, opts = {}) {
  const W = opts.w ?? ctx.canvas.width;
  const H = opts.h ?? ctx.canvas.height;
  const palette = PALETTES[opts.variant ?? "dusk-cool"] ?? PALETTES["dusk-cool"];
  const startY = y ?? 0;
  const endY = opts.endY ?? H;

  for (let yy = startY; yy < endY; yy++) {
    const t = (yy - startY) / Math.max(1, endY - startY);
    let color;
    if (t < 0.33)      color = mix(palette.bg1, palette.bg2, t * 3);
    else if (t < 0.66) color = mix(palette.bg2, palette.bg3, (t - 0.33) * 3);
    else               color = mix(palette.bg3, palette.bg4, (t - 0.66) * 3);
    rect(ctx, x ?? 0, yy, W, 1, color);
  }
}

// =============================================================
// ELEMENT 2: STARS (deterministic field)
// Variants: dense, sparse, twinkling
// Anchor: not used; covers full sky region [0, maxY]
// =============================================================

function drawStars(ctx, x, y, opts = {}) {
  const palette = PALETTES[opts.palette ?? "dusk-cool"] ?? PALETTES["dusk-cool"];
  const variant = opts.variant ?? "dense";
  const W = opts.w ?? ctx.canvas.width;
  const maxY = opts.maxY ?? 100;
  const seed = opts.seed ?? 42;
  const t = opts.t ?? 0;
  const period_s = opts.period_s ?? 8;

  const counts = { dense: 80, sparse: 25, twinkling: 60 };
  const count = opts.count ?? counts[variant] ?? 50;

  const rnd = seededRandom(seed);
  for (let i = 0; i < count; i++) {
    const sx = (rnd() * W) | 0;
    const sy = (rnd() * maxY) | 0;
    const brightness = rnd();
    const twPhase = rnd() * 6.28;

    const tw = 0.6 + 0.4 * Math.sin(t * period_s * 1.5 + twPhase);
    if (tw < 0.15) continue;
    const c = brightness > 0.85 ? palette.star : palette.starDim;
    px(ctx, sx, sy, mix('#000000', c, tw));
    if (brightness > 0.92) {
      const dim = mix('#000000', c, tw * 0.4);
      px(ctx, sx - 1, sy, dim);
      px(ctx, sx + 1, sy, dim);
      px(ctx, sx, sy - 1, dim);
      px(ctx, sx, sy + 1, dim);
    }
  }
}

// =============================================================
// ELEMENT 3: MOUNTAIN RANGE (with snow caps + atmospheric perspective)
// Variants: far (lightest), mid (medium), near (darkest)
// Anchor: bottom-left of range; range extends across W to baseY
// =============================================================

function drawMountainRange(ctx, x, y, opts = {}) {
  const palette = PALETTES[opts.palette ?? "dusk-cool"] ?? PALETTES["dusk-cool"];
  const W = opts.w ?? ctx.canvas.width;
  const variant = opts.variant ?? "mid";
  const seed = opts.seed ?? 311;
  const baseY = y ?? 220;

  // Variant-specific params
  const params = {
    far:  { count: 8,  hMin: 60, hMax: 110, slopeFactor: 0.7, darkness: 0.5 },
    mid:  { count: 12, hMin: 50, hMax: 90,  slopeFactor: 0.6, darkness: 0.7 },
    near: { count: 18, hMin: 30, hMax: 60,  slopeFactor: 0.5, darkness: 1.0 },
  };
  const p = params[variant] ?? params.mid;

  const rnd = seededRandom(seed);
  const peaks = [];
  for (let i = 0; i < p.count; i++) {
    peaks.push({
      x: i * (W / p.count) + rnd() * 8 - 4,
      h: p.hMin + rnd() * (p.hMax - p.hMin),
      asym: rnd() - 0.5,
    });
  }

  for (const peak of peaks) {
    for (let dx = -peak.h * p.slopeFactor; dx < peak.h * p.slopeFactor; dx++) {
      const slope = Math.abs(dx) / (peak.h * p.slopeFactor);
      const yOnSlope = baseY - peak.h * (1 - slope) + peak.asym * dx;
      for (let yy = yOnSlope; yy < baseY; yy++) {
        const xx = peak.x + dx;
        if (xx >= 0 && xx < W) {
          const isSnowCap = yy < yOnSlope + (variant === "far" ? 8 : variant === "mid" ? 5 : 3);
          const isShadow = (Math.abs(dx) > peak.h * p.slopeFactor * 0.6) && !isSnowCap;
          let c;
          if (isSnowCap) {
            c = mix(palette.bg3, palette.snow, 0.6 * p.darkness);
          } else if (isShadow) {
            c = palette.bg1;
          } else {
            c = mix(palette.bg2, palette.stoneLight, 0.5 * p.darkness);
          }
          px(ctx, xx, yy, c);
        }
      }
    }
  }
}

// =============================================================
// ELEMENT 4: TOWER (with brick texture, crenellations, optional flag)
// Variants: stone, ruined, runic
// Anchor: top-center of tower
// =============================================================

function drawTower(ctx, x, y, opts = {}) {
  const palette = PALETTES[opts.palette ?? "dusk-cool"] ?? PALETTES["dusk-cool"];
  const variant = opts.variant ?? "stone";
  const height = opts.height ?? 150;
  const width = opts.width ?? 14;
  const t = opts.t ?? 0;

  const tx = x;
  const towerTop = y;
  const towerBottom = y + height;

  // Brick body
  for (let yy = towerTop; yy < towerBottom; yy++) {
    for (let dx = -width / 2; dx < width / 2; dx++) {
      const xx = tx + dx;
      let baseColor;
      if (dx < -3)      baseColor = palette.stoneLight;
      else if (dx > 3)  baseColor = palette.stoneDark;
      else              baseColor = palette.stone;
      // Mortar lines every 4 vertical
      const mortarRow = (yy - towerTop) % 4 === 3;
      if (mortarRow) baseColor = mix(baseColor, '#0a0810', 0.4);
      // Variant: ruined adds gaps
      if (variant === "ruined") {
        const gap = hash(yy * 3 + dx * 7) > 0.85;
        if (gap) continue;
      }
      // Variant: runic adds glowing rune lines
      if (variant === "runic" && (yy - towerTop) % 12 === 6 && Math.abs(dx) <= 3) {
        const glow = 0.5 + 0.5 * Math.sin(t * Math.PI * 4);
        baseColor = mix(baseColor, palette.warmGlow, glow * 0.6);
      }
      px(ctx, xx, yy, baseColor);
    }
  }

  // Tower base (wider plinth)
  for (let yy = towerBottom; yy < towerBottom + 8; yy++) {
    for (let dx = -width / 2 - 2; dx < width / 2 + 2; dx++) {
      const xx = tx + dx;
      const c = (dx < -3) ? palette.stoneLight : (dx > 3) ? palette.stoneDark : palette.stone;
      px(ctx, xx, yy, c);
    }
  }

  // Crenellations (5 merlons)
  const merlonY = towerTop - 4;
  for (let m = -3; m <= 3; m += 2) {
    for (let dy = 0; dy < 4; dy++) {
      px(ctx, tx + m, merlonY + dy, palette.stoneLight);
    }
  }

  // Optional flag
  if (opts.flag !== false) {
    for (let dy = 0; dy < 8; dy++) {
      px(ctx, tx, merlonY - 8 + dy, palette.stoneDark);
    }
    const flagWave = Math.sin(t * Math.PI * 4) * 0.5;
    const flagColor = opts.flagColor ?? '#a82838';
    for (let dx = 1; dx <= 4; dx++) {
      const fy = merlonY - 7 + Math.floor(flagWave * dx);
      px(ctx, tx + dx, fy, flagColor);
      px(ctx, tx + dx, fy + 1, flagColor);
    }
  }
}

// =============================================================
// ELEMENT 5: WINDOW with volumetric glow
// Variants: lit, dark, flickering
// Anchor: top-left corner of window
// =============================================================

function drawWindow(ctx, x, y, opts = {}) {
  const palette = PALETTES[opts.palette ?? "dusk-cool"] ?? PALETTES["dusk-cool"];
  const variant = opts.variant ?? "lit";
  const t = opts.t ?? 0;
  const flickerPhase = opts.flickerPhase ?? 0;
  const w = opts.w ?? 2;
  const h = opts.h ?? 3;

  if (variant === "dark") {
    rect(ctx, x, y, w, h, palette.stoneDark);
    return;
  }

  // Flicker (variant=lit has gentle flicker, =flickering has pronounced)
  const flickerAmp = variant === "flickering" ? 0.4 : 0.2;
  const flicker = (1 - flickerAmp) + flickerAmp * Math.sin(t * Math.PI * 8 + flickerPhase * 6.28);
  const winColor = mix(palette.stoneDark, palette.warmGlow, flicker);

  for (let dy = 0; dy < h; dy++) {
    for (let dx = 0; dx < w; dx++) {
      px(ctx, x + dx, y + dy, dy === h - 1 ? mix(winColor, palette.warm, 0.3) : winColor);
    }
  }

  // Volumetric glow halo (3-pixel radius)
  for (let dy = -2; dy <= h + 1; dy++) {
    for (let dx = -2; dx <= w + 1; dx++) {
      if (dx >= 0 && dx < w && dy >= 0 && dy < h) continue;
      const cx = (w - 1) / 2, cy = (h - 1) / 2;
      const dist = Math.sqrt((dx - cx) ** 2 + (dy - cy) ** 2);
      if (dist > Math.max(w, h) / 2 && dist <= Math.max(w, h) / 2 + 2.5) {
        const alpha = (1 - (dist - Math.max(w, h) / 2) / 2.5) * flicker * 0.35;
        const haloColor = mix(palette.stone, palette.warm, alpha);
        px(ctx, x + dx, y + dy, haloColor);
      }
    }
  }
}

// =============================================================
// ELEMENT 6: PINE TREE (with branches, optional snow on branches)
// Variants: small, medium, large
// Anchor: base (bottom) of trunk
// =============================================================

function drawPine(ctx, x, y, opts = {}) {
  const palette = PALETTES[opts.palette ?? "dusk-cool"] ?? PALETTES["dusk-cool"];
  const variant = opts.variant ?? "medium";
  const heights = { small: 8, medium: 14, large: 22 };
  const h = opts.height ?? heights[variant] ?? 14;
  const depth = opts.depth ?? "fg"; // fg, mg, bg

  const colorMap = {
    fg: palette.pine,
    mg: palette.pineMid,
    bg: mix(palette.pineMid, palette.bg3, 0.3),
  };
  const c = colorMap[depth] ?? palette.pine;

  // Trunk
  for (let dy = 0; dy < h; dy++) {
    px(ctx, x, y - dy, c);
  }

  // Branches at every 2 rows for fg/mg, every 3 rows for bg
  const branchInterval = depth === "bg" ? 3 : 2;
  for (let dy = 1; dy < h; dy += branchInterval) {
    const branchW = Math.max(1, Math.floor((h - dy) / 2.5));
    for (let bw = 1; bw <= branchW; bw++) {
      px(ctx, x - bw, y - dy, c);
      px(ctx, x + bw, y - dy, c);
      // Snow on branch tip (only for fg/mg, deterministic)
      if (depth !== "bg" && bw === branchW && hash(x * 7 + dy * 13) > 0.7) {
        px(ctx, x - bw, y - dy - 1, palette.snowDim);
      }
    }
  }
}

// =============================================================
// ELEMENT 7: FOG BAND (horizontal haze, atmospheric perspective)
// Anchor: top of fog band
// =============================================================

function drawFogBand(ctx, x, y, opts = {}) {
  const palette = PALETTES[opts.palette ?? "dusk-cool"] ?? PALETTES["dusk-cool"];
  const W = opts.w ?? ctx.canvas.width;
  const h = opts.h ?? 20;
  const intensity = opts.intensity ?? 0.4;

  for (let yy = y; yy < y + h; yy++) {
    const t = (yy - y) / h;
    const a = (1 - Math.abs(t - 0.5) * 2) * intensity;
    rect(ctx, x ?? 0, yy, W, 1, mix(palette.bg3, palette.snow, a));
  }
}

// =============================================================
// ELEMENT 8: SNOW PARTICLES (deterministic falling)
// Variants: light (12 particles), heavy (32)
// Anchor: not used; covers full canvas
// =============================================================

function drawSnow(ctx, x, y, opts = {}) {
  const palette = PALETTES[opts.palette ?? "dusk-cool"] ?? PALETTES["dusk-cool"];
  const variant = opts.variant ?? "light";
  const W = opts.w ?? ctx.canvas.width;
  const H = opts.h ?? ctx.canvas.height;
  const t = opts.t ?? 0;
  const seed = opts.seed ?? 19;
  const counts = { light: 12, heavy: 32 };
  const count = opts.count ?? counts[variant] ?? 16;

  for (let i = 0; i < count; i++) {
    const seedI = i * 19 + seed;
    const snowT = (t + hash(seedI)) % 1;
    const drift = Math.sin(snowT * Math.PI * 2 + i) * 4;
    const sx = (hash(seedI * 2) * W + drift) | 0;
    const sy = (snowT * H * 1.1) | 0;
    if (sy >= 0 && sy < H && sx >= 0 && sx < W) {
      const a = Math.sin(snowT * Math.PI) * 0.9;
      px(ctx, sx, sy, mix(palette.bg2, palette.snow, a));
    }
  }
}

// =============================================================
// ELEMENT 9: GROUND/SNOW SURFACE (with texture pattern)
// Anchor: top of ground
// =============================================================

function drawGround(ctx, x, y, opts = {}) {
  const palette = PALETTES[opts.palette ?? "dusk-cool"] ?? PALETTES["dusk-cool"];
  const W = opts.w ?? ctx.canvas.width;
  const H = opts.h ?? ctx.canvas.height;
  const startY = y;
  const seed = opts.seed ?? 11;

  rect(ctx, x ?? 0, startY, W, H - startY, palette.snowDim);

  // Texture sparkles
  const textureCount = opts.textureCount ?? 40;
  for (let i = 0; i < textureCount; i++) {
    const seedI = i * 13 + seed;
    const sx = (hash(seedI) * W) | 0;
    const sy = startY + 1 + (hash(seedI * 2) * (H - startY - 2)) | 0;
    px(ctx, sx, sy, palette.snow);
  }
}

// =============================================================
// SCENE COMPOSER — render declarative scene
// =============================================================

const ELEMENT_REGISTRY = {
  "sky":            drawSky,
  "stars":          drawStars,
  "mountain-range": drawMountainRange,
  "tower":          drawTower,
  "window":         drawWindow,
  "pine":           drawPine,
  "fog-band":       drawFogBand,
  "snow":           drawSnow,
  "ground":         drawGround,
};

/**
 * Render a declarative scene array.
 *
 * scene = [
 *   {el: "sky", variant: "dusk-cool"},
 *   {el: "stars", maxY: 100, count: 80, palette: "dusk-cool"},
 *   {el: "mountain-range", x: 0, y: 220, variant: "far", palette: "dusk-cool"},
 *   ...
 * ]
 */
function renderScene(ctx, W, H, scene, t) {
  for (const item of scene) {
    const drawFn = ELEMENT_REGISTRY[item.el];
    if (!drawFn) {
      console.warn(`Unknown element: ${item.el}`);
      continue;
    }
    const opts = { ...item, t };
    delete opts.el;
    delete opts.x;
    delete opts.y;
    drawFn(ctx, item.x, item.y, opts);
  }
}

// Export to window so HTML pages can use directly
if (typeof window !== 'undefined') {
  window.PixelArtElements = {
    PALETTES, ELEMENT_REGISTRY,
    drawSky, drawStars, drawMountainRange, drawTower, drawWindow,
    drawPine, drawFogBand, drawSnow, drawGround,
    renderScene, mix, hex, rgb, hash, seededRandom,
  };
}
