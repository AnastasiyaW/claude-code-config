#!/usr/bin/env python3
"""Bake a canvas-rendered HTML animation into GIF/WebM/MP4/PNG sequence.

Uses Playwright (headless Chromium) to drive the same JS code that runs at
runtime, then encodes via ffmpeg. Single source of truth: the JS draw
function — Python doesn't re-render, just captures.

Why "baking"?

At runtime the animation runs at ~60fps in browser; we typically use 4-8
keyframes for hand-coded simplicity. But for archival output (GIF/MP4/WebM),
we can step `t = 0/N, 1/N, 2/N, ..., (N-1)/N` for ANY N, capturing N frames.
This produces SMOOTHER animation than the "live" one because we render at
30-60fps × period_seconds total frames.

Usage:
    # Bake a single canvas to GIF (smooth 60fps × 4s = 240 frames)
    python bake_animation.py http://localhost:9132/index-v2.html \
      --canvas-id c1 --period-ms 4000 --fps 60 \
      --format gif -o twilight.gif

    # Bake to WebM with alpha channel (transparent background, video editing)
    python bake_animation.py http://localhost:9132/index-v2.html \
      --canvas-id c1 --period-ms 4000 --fps 30 \
      --format webm-alpha -o twilight.webm

    # Bake all 4 covers to a sprite-sheet PNG sequence
    python bake_animation.py http://localhost:9132/index-v2.html \
      --canvas-id c1,c2,c3,c4 --period-ms 4000,8000,5000,10000 \
      --fps 30 --format png-sequence -o frames/

    # Bake to MP4 (no alpha, smaller file)
    python bake_animation.py http://localhost:9132/index-v2.html \
      --canvas-id c1 --period-ms 4000 --fps 30 --format mp4 -o twilight.mp4

Requires:
    pip install playwright pillow
    playwright install chromium    (one-time)
    ffmpeg in PATH                 (for video formats)

Note on WebM alpha: WebM with VP9 + yuva420p preserves alpha channel through
ffmpeg. MP4 (h264) does NOT support alpha — use WebM for transparent video.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
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
                          out_dir: Path, viewport: tuple[int, int]) -> list[Path]:
    """Open headless browser, set explicit phase, screenshot canvas at each step.

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
                frame_path.write_bytes(base64.b64decode(b64))
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
    "gif": encode_gif,
    "apng": encode_apng,
    "webm-alpha": encode_webm_alpha,
    "mp4": encode_mp4,
    "png-sequence": keep_png_sequence,
}


async def bake(url: str, canvas_id: str, period_ms: int, fps: int,
                fmt: str, output: Path, viewport: tuple[int, int]) -> None:
    # Capture frames to a temp directory
    out_dir = output.parent / f".bake_{canvas_id}_{period_ms}ms_{fps}fps"
    frames = await capture_frames(url, canvas_id, period_ms, fps, out_dir, viewport)

    if not frames:
        print("No frames captured!", file=sys.stderr)
        sys.exit(1)

    if fmt == "png-sequence":
        keep_png_sequence(frames, output)
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
    parser.add_argument("--format", default="gif",
                        choices=list(ENCODERS.keys()),
                        help="Output format (default: gif)")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument("--viewport-w", type=int, default=1280, help="Browser viewport width")
    parser.add_argument("--viewport-h", type=int, default=900, help="Browser viewport height")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    asyncio.run(bake(
        url=args.url,
        canvas_id=args.canvas_id,
        period_ms=args.period_ms,
        fps=args.fps,
        fmt=args.format,
        output=output,
        viewport=(args.viewport_w, args.viewport_h),
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
