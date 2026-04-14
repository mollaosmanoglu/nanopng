from __future__ import annotations

import argparse
from pathlib import Path

from nanopng.core import MODELS, STYLES, generate_transparent_png


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate transparent PNGs from text prompts")
    parser.add_argument("prompt", help="Text prompt describing the image")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output file path (default: auto from prompt)")
    parser.add_argument("-n", type=int, default=1, choices=[1, 2, 3, 4], help="Number of images (default: 1)")
    parser.add_argument("--size", default="1:1", choices=["1:1", "16:9", "9:16", "4:3", "3:4"], help="Aspect ratio (default: 1:1)")
    parser.add_argument("--style", default=None, choices=list(STYLES), help="Image style")
    parser.add_argument("--model", default="fast", choices=list(MODELS), help="Model speed (default: fast)")
    args = parser.parse_args()

    generate_transparent_png(
        prompt=args.prompt,
        output=args.output,
        n=args.n,
        size=args.size,
        style=args.style,
        model=args.model,
    )
