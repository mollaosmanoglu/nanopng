<p align="center">
  <img src="docs/logo.png" alt="nanopng logo" width="200"/>
</p>

# nanopng

![PyPI](https://img.shields.io/pypi/v/nanopng)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)

CLI to generate transparent PNG images from text prompts. Describe what you want, get a cutout PNG in ~12 seconds.

<p align="center">
  <img src="docs/demo.gif" alt="CLI demo" width="700"/>
</p>

## Install

```
uv tool install nanopng
```

On first run, nanopng will prompt for your Gemini API key and save it to `~/.nanopng/.env`. Get a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## Usage

```
nanopng "fire breathing dragon"
nanopng "cat wizard" -n 4
nanopng "samurai warrior" --style anime --size 9:16
nanopng "crystal sword" --model standard -o sword.png
```

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `-o`, `--output` | Output file path | Auto from prompt |
| `-n` | Number of images (1-4) | 1 |
| `--size` | Aspect ratio: `1:1`, `16:9`, `9:16`, `4:3`, `3:4` | `1:1` |
| `--style` | Style preset (see below) | None |
| `--model` | `fast` (~10s) or `standard` (~17s) | `fast` |

## Styles

`pixel-art` `watercolor` `3d-render` `photorealistic` `cartoon` `anime` `oil-painting` `flat`

## Tech Stack

| Component | Tools |
|-----------|-------|
| Language | Python 3.12 |
| Image Gen | Google Imagen 4 Fast |
| BG Removal | rembg (isnet-general-use) |
| CLI | argparse (stdlib) |

## Architecture

```
[User Input]                [System Boundary: nanopng]              [External]

┌──────────────┐                                            ┌───────────────┐
│   Terminal   │                                            │  Google API   │
│              │                                            │  (Imagen 4)   │
│ $ nanopng    │                                            └───────┬───────┘
│   "prompt"   │                                                    │
└──────┬───────┘                                                    │ HTTPS
       │                                                            │
       │ CLI Command                                                │
       ▼                                                            │
┌─────────────────────────────────────────────────────────┐         │
│              Python CLI (argparse)                       │         │
│                                                         │         │
│  ┌──────────────────────────────────────────────────┐   │         │
│  │           cli.py                                 │   │         │
│  │                                                  │   │         │
│  │  Parse args (prompt, -n, --size, --style, etc.) │   │         │
│  └──────────────┬───────────────────────────────────┘   │         │
│                 │                                       │         │
│                 ▼                                       │         │
│  ┌──────────────────────────────────────────────────┐   │         │
│  │           core.py                                │   │◀────────┘
│  │                                                  │   │ Generate
│  │  1. Build prompt + chroma key suffix             │   │
│  │  2. Call Imagen 4 Fast (google-genai)            │   │
│  │  3. Remove background (rembg, local)             │   │
│  │  4. Save RGBA transparent PNG                    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                 │
                 ▼
         prompt-slug.png
         (transparent RGBA)

Imagen 4 Fast (~10s) • rembg local inference (~2s) • ~12s total
```

## License

MIT
