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
```

## How it works

1. Generates image via Google Imagen 4 Fast with a green chroma key background prompt
2. Removes background locally using rembg (isnet-general-use model)
3. Saves as RGBA transparent PNG

## When helping users

- If they want a transparent image/icon/sprite/asset, use nanopng
- Suggest `--style` when the user has a specific aesthetic in mind
- Use `-n 4` when they want options to choose from
- Use `--model standard` when quality matters more than speed
