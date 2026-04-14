from __future__ import annotations

import os
import re
import sys
import time
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from rembg import new_session, remove

CHROMA_SUFFIX = ", on a solid bright green (#00FF00) chroma key background, studio lighting"
REMBG_MODEL = "isnet-general-use"

MODELS = {
    "fast": "imagen-4.0-fast-generate-001",
    "standard": "imagen-4.0-generate-001",
}

STYLES = {
    "pixel-art": "pixel art style",
    "watercolor": "watercolor painting style",
    "3d-render": "3D rendered style",
    "photorealistic": "photorealistic style",
    "cartoon": "cartoon style",
    "anime": "anime style",
    "oil-painting": "oil painting style",
    "flat": "flat vector illustration style",
}


def slugify(prompt: str, max_words: int = 3) -> str:
    words = re.sub(r"[^\w\s-]", "", prompt.lower()).split()[:max_words]
    return "-".join(words) or "output"


def generate_transparent_png(
    prompt: str,
    output: Path | None = None,
    n: int = 1,
    size: str = "1:1",
    style: str | None = None,
    model: str = "fast",
) -> list[Path]:
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set. Add it to .env or export it.", file=sys.stderr)
        sys.exit(1)

    model_id = MODELS.get(model)
    if not model_id:
        print(f"Error: Unknown model '{model}'. Choose from: {', '.join(MODELS)}", file=sys.stderr)
        sys.exit(1)

    full_prompt = prompt
    if style:
        style_prefix = STYLES.get(style)
        if not style_prefix:
            print(f"Error: Unknown style '{style}'. Choose from: {', '.join(STYLES)}", file=sys.stderr)
            sys.exit(1)
        full_prompt = f"{style_prefix}, {full_prompt}"
    full_prompt += CHROMA_SUFFIX

    slug = slugify(prompt)
    client = genai.Client(api_key=api_key)
    session = new_session(REMBG_MODEL)

    t0 = time.time()

    response = client.models.generate_images(
        model=model_id,
        prompt=full_prompt,
        config=types.GenerateImagesConfig(
            number_of_images=n,
            aspect_ratio=size,
        ),
    )
    t1 = time.time()
    print(f"Generated {n} image(s) in {t1 - t0:.1f}s", file=sys.stderr)

    saved: list[Path] = []
    for i, gen_image in enumerate(response.generated_images):
        img = Image.open(BytesIO(gen_image.image.image_bytes))
        result = remove(img, session=session)

        if output:
            path = output if n == 1 else output.with_stem(f"{output.stem}-{i + 1}")
        else:
            path = Path(f"{slug}.png") if n == 1 else Path(f"{slug}-{i + 1}.png")

        result.save(path)
        saved.append(path)

    t2 = time.time()
    print(f"Removed background(s) in {t2 - t1:.1f}s", file=sys.stderr)

    for path in saved:
        print(f"Saved {path}", file=sys.stderr)
    print(f"Total: {t2 - t0:.1f}s", file=sys.stderr)

    return saved
