---
name: nanopng
description: Generate transparent PNG images from text prompts using the nanopng CLI
argument-hint: "[prompt] [options]"
allowed-tools: Bash(nanopng *) Read
---

Generate transparent PNG images from text prompts using the nanopng CLI.

## Setup

Requires `GEMINI_API_KEY` in `.env` or environment. Install with:

```bash
uv pip install -e .
```

## Usage

```bash
nanopng "prompt" [options]
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `-o`, `--output` | Output file path | Auto from prompt (first 3 words) |
| `-i`, `--image` | Reference image(s) to guide generation (up to 14, uses Gemini 3.1 Flash Image) | None |
| `-n` | Number of images (1-4) | 1 |
| `--size` | Aspect ratio: `1:1`, `16:9`, `9:16`, `4:3`, `3:4` | `1:1` |
| `--style` | Style preset (see below) | None |
| `--model` | `fast` (~10s) or `standard` (~17s, higher quality) | `fast` |

## Styles

`pixel-art`, `watercolor`, `3d-render`, `photorealistic`, `cartoon`, `anime`, `oil-painting`, `flat`

## Examples

```bash
# Basic usage — auto-names to fire-dragon.png
nanopng "fire dragon"

# Multiple variants to pick from
nanopng "cat wizard" -n 4

# Portrait anime style
nanopng "samurai warrior" --style anime --size 9:16

# Higher quality, custom output
nanopng "crystal sword" --model standard -o sword.png

# With reference image (uses Gemini 3.1 Flash Image)
nanopng "character in this style" -i reference.png -o output.png

# Multiple reference images (up to 14)
nanopng "combine these elements" -i img1.png -i img2.png -i img3.png

# From stdin (for piping image data)
cat reference.jpg | nanopng -i - "prompt" -o output.png
```

## How it works

**Without reference images:**
1. Generates image via Google Imagen 4 Fast with a green chroma key background prompt
2. Removes background locally using rembg (isnet-general-use model)
3. Saves as RGBA transparent PNG

**With reference images (`-i` flag):**
1. Generates image via Google Gemini 3.1 Flash Image with reference images (up to 14)
2. Removes background locally using rembg
3. Saves as RGBA transparent PNG

## Claude Code Workflow (Reference Images)

When users send images in chat to use as references:

1. **User sends image** → Image stored in `/var/folders/.../T/tos_*.png`
2. **Find the image**: `find /var/folders -name "tos_*.png" -type f | xargs ls -lt | head -1`
3. **Pipe to nanopng**: `cat [temp-file] | nanopng -i - "prompt" -o output.png`

**Example:**
```bash
# Find most recent chat image
IMG=$(find /var/folders -name "tos_*.png" -type f 2>/dev/null | xargs ls -lt 2>/dev/null | head -1 | awk '{print $NF}')

# Use it as reference
cat "$IMG" | nanopng -i - "Majin Vegeta in this anime style, black and magenta duotone" -o vegeta.png
```

**When reference images are provided:**
- Automatically uses Gemini 3.1 Flash Image (supports up to 14 reference images)
- Great for style transfer, character consistency, or combining elements

## When helping users

- If they want a transparent image/icon/sprite/asset, use nanopng
- Suggest `--style` when the user has a specific aesthetic in mind
- Use `-n 4` when they want options to choose from
- Use `--model standard` when quality matters more than speed
- **If they send an image in chat**, automatically find it in `/var/folders/.../T/tos_*.png` and pipe it via stdin
