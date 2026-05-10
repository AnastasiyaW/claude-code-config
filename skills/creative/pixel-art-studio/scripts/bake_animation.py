#!/usr/bin/env python3
"""Bake a canvas-rendered HTML animation into WebP/GIF/WebM/MP4/PNG sequence.

Uses Playwright (headless Chromium) to drive the same JS code that runs at
runtime, then encodes via Pillow or ffmpeg. Single source of truth: the JS
draw function — Python doesn't re-render, just captures.

FORMAT GUIDE:

  --format web         RECOMMENDED for websites/markdown/docs
                       Animated WebP. ~5x smaller than GIF, full alpha,
                       embeds as <img>. Modern browsers (96%+).

  --format gif         For email / Telegram / WhatsApp / chat embeds
                       Universal compat but ~5x larger, only 1-bit alpha.

  --format webm-alpha  For full-screen video / hero headers (<video> tag)
                       Smallest size with full alpha (yuva420p VP9).
                       Cannot embed as <img>.

  --format apng        Alternative to GIF with full alpha
                       Larger than WebP but PNG family

  --format mp4         For social media / universal video player
                       NO ALPHA — solid background only

  --format png-sequence  For game engine import / max quality post-prod

Why "baking"?

At runtime the animation runs at ~60fps in browser; we typically use 4-8
keyframes for hand-coded simplicity. But for archival output (WebP/GIF/MP4/WebM),
we can step `t = 0/N, 1/N, 2/N, ..., (N-1)/N` for ANY N, capturing N frames.
This produces SMOOTHER animation than the "live" one because we render at
30-60fps × period_seconds total frames.

Usage:
    # RECOMMENDED for web: animated WebP (smallest + alpha)
    python bake_animation.py http://localhost:9132/index-v2.html \
      --canvas-id c1 --period-ms 4000 --fps 30 \
      --format web -o twilight.webp

    # For email / Telegram / chat: GIF
    python bake_animation.py http://localhost:9132/index-v2.html \
      --canvas-id c1 --period-ms 4000 --fps 30 --format gif -o twilight.gif

    # For full-screen video editing (compositing): WebM with alpha channel
    python bake_animation.py http://localhost:9132/index-v2.html \
      --canvas-id c1 --period-ms 4000 --fps 30 \
      --format webm-alpha -o twilight.webm

    # For game engine: PNG sequence
    python bake_animation.py http://localhost:9132/index-v2.html \
      --canvas-id c1 --period-ms 4000 --fps 30 --format png-sequence -o frames/

    # Universal video (no alpha): MP4
    python bake_animation.py http://localhost:9132/index-v2.html \
      --canvas-id c1 --period-ms 4000 --fps 30 --format mp4 -o twilight.mp4

Requires:
    pip install playwright pillow
    playwright install chromium    (one-time)
    ffmpeg in PATH                 (for video formats: WebM/MP4)

Note on alpha support:
    - WebP: full alpha (RGBA), embeddable as <img> — BEST for web
    - APNG: full alpha (RGBA), embeddable as <img>
    - WebM (VP9 yuva420p): full alpha, but requires <video> tag
    - GIF: only 1-bit alpha (transparent or fully solid, no semi-trans)
    - MP4 (h264): NO ALPHA — use solid background or WebM
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed. pip install Pillow", file=sys.stderr)
    sys.exit(1)


# --- Playwright frame capture -----------------------------------------------

async def capture_frames(url: str, canvas_id: str, period_ms: int, fps: int,
                          out_dir: Path, viewport: tuple[int, int],
                          base_image: Path | None = None) -> list[Path]:
    """Open headless browser, set explicit phase, screenshot canvas at each step.

    Args:
        base_image: Optional path to a static PNG. If provided, each captured
                    canvas frame is composited OVER this base image (Tier 3
                    workflow: AI-generated PNG + canvas animation overlay).

    Returns list of frame PNG paths in order.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Error: playwright not installed. pip install playwright && playwright install chromium",
              file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    n_frames = int(period_ms / 1000.0 * fps)
    print(f"Capturing {n_frames} frames at {fps}fps for {canvas_id} ({period_ms}ms loop)...")

    frames = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            context = await browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
            page = await context.new_page()
            await page.goto(url, wait_until="load")
            # Stop the runtime RAF by overriding it (we control phase manually)
            await page.evaluate("""() => {
                window.__origRAF = window.requestAnimationFrame;
                window.requestAnimationFrame = () => 0;
            }""")
            # Wait for engine to be loaded
            await page.wait_for_function("""() => {
                return typeof drawTwilight !== 'undefined'
                    || typeof drawScene !== 'undefined'
                    || typeof drawCover1 !== 'undefined'
                    || (window.__bake_ready === true);
            }""", timeout=10000)

            for i in range(n_frames):
                t = i / n_frames  # 0 to (1 - 1/N)
                # Determine which draw function to call (auto-detect)
                draw_fn_js = await page.evaluate(f"""(canvasId) => {{
                    const fns = ['drawTwilight','drawNewMoon','drawEclipse','drawBreakingDawn',
                                 'drawCover1','drawCover2','drawCover3','drawCover4',
                                 'drawScene','drawCabin','drawSprite'];
                    for (const fn of fns) {{
                        if (typeof window[fn] === 'function') {{
                            const cv = document.getElementById(canvasId);
                            if (cv) return fn;
                        }}
                    }}
                    return null;
                }}""", canvas_id)

                if draw_fn_js is None:
                    print(f"Warning: could not find draw function for canvas {canvas_id}", file=sys.stderr)
                    break

                # Map canvas_id -> draw fn (heuristic)
                fn_map = {"c1": "drawTwilight", "c2": "drawNewMoon",
                          "c3": "drawEclipse", "c4": "drawBreakingDawn"}
                draw_fn = fn_map.get(canvas_id, draw_fn_js)

                await page.evaluate(f"""(t) => {{
                    const cv = document.getElementById('{canvas_id}');
                    const ctx = cv.getContext('2d');
                    {draw_fn}(ctx, cv.width, cv.height, t);
                }}""", t)

                # Get canvas content as PNG bytes via toDataURL
                data_url = await page.evaluate(f"""() => document.getElementById('{canvas_id}').toDataURL();""")
                if not data_url.startswith("data:image/png;base64,"):
                    print(f"Warning: invalid dataURL at frame {i}", file=sys.stderr)
                    continue
                b64 = data_url.split(",", 1)[1]
                frame_path = out_dir / f"{canvas_id}_{i:04d}.png"
                raw_bytes = base64.b64decode(b64)

                # Optional composite over base image (Tier 3 workflow)
                if base_image is not None:
                    canvas_img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
                    base_img = Image.open(base_image).convert("RGBA")
                    # Resize canvas overlay to match base if needed (NEAREST to preserve pixel art)
                    if canvas_img.size != base_img.size:
                        canvas_img = canvas_img.resize(base_img.size, Image.Resampling.NEAREST)
                    # Composite: base on bottom, canvas on top
                    composite = Image.alpha_composite(base_img, canvas_img)
                    composite.save(frame_path, "PNG")
                else:
                    frame_path.write_bytes(raw_bytes)
                frames.append(frame_path)

                if i % 20 == 0:
                    print(f"  Frame {i+1}/{n_frames}")
        finally:
            await browser.close()

    print(f"Captured {len(frames)} frames in {out_dir}")
    return frames


# --- Encoders ---------------------------------------------------------------

def encode_gif(frames: list[Path], output: Path, fps: int) -> None:
    """Encode PNG frames as animated GIF via Pillow."""
    images = [Image.open(f) for f in frames]
    duration_ms = int(1000 / fps)
    images[0].save(
        output,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
        optimize=False,
    )
    print(f"Wrote GIF: {output} ({len(frames)} frames @ {fps}fps)")


def encode_apng(frames: list[Path], output: Path, fps: int) -> None:
    """Encode PNG frames as animated PNG (APNG) — preserves alpha."""
    images = [Image.open(f).convert("RGBA") for f in frames]
    duration_ms = int(1000 / fps)
    images[0].save(
        output,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
        format="PNG",
    )
    print(f"Wrote APNG: {output} ({len(frames)} frames @ {fps}fps)")


def encode_webp(frames: list[Path], output: Path, fps: int,
                 quality: int = 80, lossless: bool = False) -> None:
    """Encode PNG frames as animated WebP — RECOMMENDED for web embeds.

    Animated WebP is ~5x smaller than equivalent GIF, supports full alpha,
    and embeds as `<img>` tag (unlike WebM which needs `<video>`).

    Args:
        quality: 0-100 (default 80). Only for lossy mode.
        lossless: True for pixel-perfect (larger files). False for lossy
                  (much smaller, slight quality reduction barely visible
                  on pixel art).
    """
    images = [Image.open(f).convert("RGBA") for f in frames]
    duration_ms = int(1000 / fps)
    save_kwargs = {
        "save_all": True,
        "append_images": images[1:],
        "duration": duration_ms,
        "loop": 0,
        "format": "WebP",
        "minimize_size": True,
        "allow_mixed": True,  # mix lossy/lossless per-frame for size
    }
    if lossless:
        save_kwargs["lossless"] = True
        save_kwargs["quality"] = 100
    else:
        save_kwargs["quality"] = quality
        save_kwargs["method"] = 6  # max compression effort

    images[0].save(output, **save_kwargs)
    print(f"Wrote animated WebP: {output} ({len(frames)} frames @ {fps}fps, "
          f"{'lossless' if lossless else f'lossy q={quality}'})")


def encode_webm_alpha(frames: list[Path], output: Path, fps: int) -> None:
    """Encode PNG frames as WebM with alpha channel (VP9 + yuva420p).

    Use case: video editing software that supports transparent video.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not in PATH")
    pattern = str(frames[0].parent / (frames[0].stem.rsplit("_", 1)[0] + "_%04d.png"))
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", pattern,
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p",
        "-b:v", "1M",
        "-auto-alt-ref", "0",
        str(output),
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"Wrote WebM+alpha: {output}")


def encode_mp4(frames: list[Path], output: Path, fps: int) -> None:
    """Encode PNG frames as MP4 (h264, no alpha — solid background only)."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not in PATH")
    pattern = str(frames[0].parent / (frames[0].stem.rsplit("_", 1)[0] + "_%04d.png"))
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # ensure even dims
        str(output),
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"Wrote MP4: {output}")


def keep_png_sequence(frames: list[Path], output: Path) -> None:
    """Just keep the PNG frames, don't encode. Use output as target dir."""
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    if frames[0].parent.resolve() != out_dir.resolve():
        for f in frames:
            shutil.copy(f, out_dir / f.name)
    print(f"PNG sequence: {len(frames)} frames in {out_dir}")


# --- Top-level --------------------------------------------------------------

ENCODERS = {
    "webp": encode_webp,
    "web": encode_webp,         # alias — WebP is recommended for web
    "gif": encode_gif,
    "apng": encode_apng,
    "webm-alpha": encode_webm_alpha,
    "mp4": encode_mp4,
    "png-sequence": keep_png_sequence,
}


async def bake(url: str, canvas_id: str, period_ms: int, fps: int,
                fmt: str, output: Path, viewport: tuple[int, int],
                lossless: bool = False, quality: int = 80,
                base_image: Path | None = None) -> None:
    """Run full bake: capture frames + encode.

    Args:
        base_image: Optional static PNG to composite under canvas (Tier 3 workflow).
                    AI-generated PNG goes here as the static base.
    """
    # Capture frames to a temp directory
    out_dir = output.parent / f".bake_{canvas_id}_{period_ms}ms_{fps}fps"
    frames = await capture_frames(url, canvas_id, period_ms, fps, out_dir, viewport, base_image)

    if not frames:
        print("No frames captured!", file=sys.stderr)
        sys.exit(1)

    if fmt == "png-sequence":
        keep_png_sequence(frames, output)
    elif fmt in ("webp", "web"):
        encode_webp(frames, output, fps, quality=quality, lossless=lossless)
    else:
        ENCODERS[fmt](frames, output, fps)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bake canvas animation to GIF/WebM/MP4.")
    parser.add_argument("url", help="URL to the HTML page (e.g. http://localhost:9132/index-v2.html)")
    parser.add_argument("--canvas-id", default="c1",
                        help="Canvas element id (default: c1). For multiple, use comma-separated.")
    parser.add_argument("--period-ms", type=int, default=4000,
                        help="Loop period in milliseconds (default: 4000)")
    parser.add_argument("--fps", type=int, default=30,
                        help="Output frames per second (default: 30; use 60 for buttery smooth)")
    parser.add_argument("--format", default="web",
                        choices=list(ENCODERS.keys()),
                        help="Output format (default: web = animated WebP, recommended for web)")
    parser.add_argument("--lossless", action="store_true",
                        help="WebP only: lossless mode (pixel-perfect, larger files). "
                             "Default: lossy at q=80 (much smaller, barely visible difference on pixel art)")
    parser.add_argument("--quality", type=int, default=80,
                        help="WebP lossy quality 0-100 (default: 80)")
    parser.add_argument("--base-image", default=None,
                        help="Optional static PNG to composite UNDER the canvas overlay. "
                             "Tier 3 workflow: AI-generated detailed PNG as base, canvas "
                             "renders only animated elements (snow, glow, flicker) on top.")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument("--viewport-w", type=int, default=1280, help="Browser viewport width")
    parser.add_argument("--viewport-h", type=int, default=900, help="Browser viewport height")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    base_image_path = Path(args.base_image) if args.base_image else None
    if base_image_path and not base_image_path.exists():
        print(f"Error: --base-image {base_image_path} does not exist", file=sys.stderr)
        sys.exit(1)

    asyncio.run(bake(
        url=args.url,
        canvas_id=args.canvas_id,
        period_ms=args.period_ms,
        fps=args.fps,
        fmt=args.format,
        output=output,
        viewport=(args.viewport_w, args.viewport_h),
        lossless=args.lossless,
        quality=args.quality,
        base_image=base_image_path,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
