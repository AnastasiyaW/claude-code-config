---
description: "Video post-production rules: audio mastering, color, captions, platform export. Use when: 'add music', 'add voiceover', 'export for tiktok', 'add captions', 'color grade', 'audio levels', 'master audio', 'export settings', 'platform requirements'. Covers FFmpeg patterns, audio chain, subtitle standards, and platform-specific export configs."
---

# Video Post-Production Guide

Rules and FFmpeg patterns for finishing videos: audio mastering, captions, color, and platform-specific export.

## Audio Rules

### Volume Levels (dB)

| Track | Level | Notes |
|-------|-------|-------|
| Voiceover | -12 to -10 dB | Primary audio, clear and upfront |
| Music (under VO) | -32 to -24 dB | Background, should not compete |
| Music (solo, no VO) | -16 to -12 dB | Can be louder when alone |
| Sound effects | -18 to -14 dB | Accent, not distraction |
| Silence floor | -60 dB | True silence feels unnatural, keep room tone |

### Music Selection by BPM

| Mood | BPM Range | Use Case |
|------|-----------|----------|
| Calm, reflective | 60-80 | Luxury brands, testimonials |
| Confident, steady | 80-100 | Corporate, explainers |
| Moderate energy | 100-120 | Product demos, features |
| Energetic | 120-140 | Launch videos, social ads |
| High energy | 140+ | Montage, fast-cut sequences |

**Rule:** Match music tempo to edit pace. Cut on beats for professional feel.

### Audio Mastering Chain (FFmpeg)

```bash
# Full mastering chain: highpass + EQ + compression + loudness
ffmpeg -i input.mp4 -af "
  highpass=f=80,
  equalizer=f=3000:t=q:w=1.5:g=3,
  acompressor=threshold=-20dB:ratio=4:attack=5:release=50,
  loudnorm=I=-16:TP=-1.5:LRA=11
" -c:v copy output.mp4
```

### Free Music/SFX Libraries

- **Mixkit** (mixkit.co) - royalty-free, no attribution
- **Pixabay Audio** (pixabay.com/music) - free, Pixabay license
- **Freesound** (freesound.org) - CC licensed, varies
- **YouTube Audio Library** - free for YouTube content

## Caption / Subtitle Rules

### Standards

| Parameter | Value |
|-----------|-------|
| Max characters per line | 32-42 |
| Max 2 lines simultaneously | Always |
| Display duration | 1.5-7 seconds per caption |
| Min display | 1.5 seconds (even for short text) |
| Font size | 48-72px (for 1080p) |
| Font | Sans-serif, bold weight |
| Position | Bottom center, 10% from bottom edge |
| Background | Semi-transparent black (#000000AA) |

### Burn-in Captions (FFmpeg)

```bash
# Basic caption burn-in
ffmpeg -i input.mp4 -vf "subtitles=subs.srt:force_style='FontSize=24,FontName=Arial,Bold=1,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,MarginV=40'" output.mp4

# Word-by-word highlight (requires ASS format)
ffmpeg -i input.mp4 -vf "ass=styled_subs.ass" output.mp4
```

## Color Correction

### Quick Presets (FFmpeg)

```bash
# Warm punch (indoor/talking head)
ffmpeg -i input.mp4 -vf "eq=contrast=1.1:brightness=0.02:saturation=1.15,colorbalance=rs=0.05:gs=-0.02:bs=-0.05" output.mp4

# Cool tech (product/SaaS)
ffmpeg -i input.mp4 -vf "eq=contrast=1.05:saturation=0.95,colorbalance=rs=-0.03:gs=0.01:bs=0.05" output.mp4

# High contrast B&W
ffmpeg -i input.mp4 -vf "hue=s=0,eq=contrast=1.3:brightness=0.03" output.mp4
```

## Platform Export Configs

### YouTube (16:9)

```bash
ffmpeg -i input.mp4 \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart \
  youtube_output.mp4
```

### TikTok / Instagram Reels (9:16)

```bash
# Resize landscape to vertical with blur background
ffmpeg -i input_16x9.mp4 \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black[fg];[0:v]scale=1080:1920,boxblur=20:20[bg];[bg][fg]overlay=(W-w)/2:(H-h)/2" \
  -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
  -c:a aac -b:a 128k \
  tiktok_output.mp4

# Native vertical render from Remotion
npx remotion render src/index.ts Comp out/vertical.mp4 --width 1080 --height 1920
```

### Instagram Square (1:1)

```bash
# Center crop to square
ffmpeg -i input_16x9.mp4 \
  -vf "crop=ih:ih:(iw-ih)/2:0,scale=1080:1080" \
  -c:v libx264 -crf 23 -pix_fmt yuv420p \
  -c:a aac -b:a 128k \
  square_output.mp4
```

## Common FFmpeg Operations

### Trim

```bash
# Fast trim (keyframe-based, instant)
ffmpeg -ss 00:00:05 -i input.mp4 -t 15 -c copy trimmed.mp4

# Frame-accurate trim (re-encodes)
ffmpeg -i input.mp4 -ss 00:00:05 -t 15 -c:v libx264 -crf 18 trimmed.mp4
```

### Concatenate

```bash
# Create file list
echo "file 'scene1.mp4'" > list.txt
echo "file 'scene2.mp4'" >> list.txt
echo "file 'scene3.mp4'" >> list.txt

# Lossless concat (same codec/resolution)
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4

# Re-encoded concat (different sources)
ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -crf 18 output.mp4
```

### Add Background Music

```bash
# Music at -24dB under existing audio
ffmpeg -i video.mp4 -i music.mp3 \
  -filter_complex "[1:a]volume=-24dB[music];[0:a][music]amix=inputs=2:duration=first" \
  -c:v copy output.mp4
```

### Speed Change

```bash
# 2x speed (with audio pitch correction)
ffmpeg -i input.mp4 -vf "setpts=0.5*PTS" -af "atempo=2.0" fast.mp4

# 0.5x slow motion
ffmpeg -i input.mp4 -vf "setpts=2.0*PTS" -af "atempo=0.5" slow.mp4
```

### GIF Creation

```bash
# High quality GIF with palette
ffmpeg -i input.mp4 -vf "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" output.gif
```

## Quality Checklist (Post-Render)

Before publishing, verify:
- [ ] No black frames at start/end
- [ ] Audio levels consistent (no sudden jumps)
- [ ] Captions readable on mobile (test at 50% zoom)
- [ ] Colors look correct on both dark and light screens
- [ ] File size within platform limits
- [ ] Aspect ratio correct for target platform
- [ ] First frame is visually interesting (it becomes the thumbnail)
- [ ] Last frame has clear CTA visible for 2+ seconds

## Gotchas

- Always use `-pix_fmt yuv420p` - some players can't handle other formats
- Always use `-movflags +faststart` for web playback (moves metadata to file start)
- FFmpeg `-ss` BEFORE `-i` = fast seek (keyframe). AFTER `-i` = accurate (slower)
- `aac` codec needs `-strict experimental` on some FFmpeg versions
- Complex filter graphs: keep each step simple. Claude makes subtle errors in long chains
- Test on mobile FIRST - most video is watched on phones
