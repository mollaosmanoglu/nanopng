from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from rembg import new_session, remove

CONFIG_DIR = Path.home() / ".nanopng"
CONFIG_ENV = CONFIG_DIR / ".env"
CHROMA_SUFFIX = ", on a pure white background, soft studio lighting, centered"
REMBG_MODEL = "isnet-general-use"
REMBG_MODEL_PATH = Path.home() / ".u2net" / "isnet-general-use.onnx"

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


def open_image(path: Path) -> None:
    """Open an image file with the default system viewer."""
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(path)], check=False)
        elif sys.platform == "win32":  # Windows
            subprocess.run(["start", "", str(path)], check=False, shell=True)
        else:  # Linux and others
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception:
        pass  # Silently fail if opening doesn't work


def slugify(prompt: str, max_words: int = 3) -> str:
    words = re.sub(r"[^\w\s-]", "", prompt.lower()).split()[:max_words]
    return "-".join(words) or "output"


def get_api_key() -> str:
    load_dotenv(CONFIG_ENV)
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key

    print("No GEMINI_API_KEY found. Get one at https://aistudio.google.com/apikey", file=sys.stderr)
    api_key = input("Enter your Gemini API key: ").strip()
    if not api_key:
        print("Error: No API key provided.", file=sys.stderr)
        sys.exit(1)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_ENV.write_text(f"GEMINI_API_KEY={api_key}\n")
    print(f"Saved to {CONFIG_ENV}", file=sys.stderr)
    return api_key


def load_rembg_session():  # type: ignore[no-untyped-def]
    if not REMBG_MODEL_PATH.exists():
        print("Downloading background removal model (one-time, ~179MB)...", file=sys.stderr)
    return new_session(REMBG_MODEL)


def generate_with_gemini_flash(
    prompt: str,
    reference_images: list[Path],
    output: Path | None = None,
    n: int = 1,
    size: str = "1:1",
) -> list[Path]:
    """Generate images using Gemini 3.1 Flash Image with reference images."""
    api_key = get_api_key()

    # Validate reference images
    if len(reference_images) > 14:
        print("Warning: Gemini Flash supports up to 14 reference images. Using first 14.", file=sys.stderr)
        reference_images = reference_images[:14]

    # Load reference images
    loaded_images = []
    for img_path in reference_images:
        # Support stdin for piping image data
        if str(img_path) in ("-", "stdin"):
            try:
                loaded_images.append(Image.open(sys.stdin.buffer))
            except Exception as e:
                print(f"Error reading image from stdin: {e}", file=sys.stderr)
                sys.exit(1)
            continue

        # Regular file path
        if not img_path.exists():
            print(f"Error: Reference image not found: {img_path}", file=sys.stderr)
            sys.exit(1)
        try:
            loaded_images.append(Image.open(img_path))
        except Exception as e:
            print(f"Error loading image {img_path}: {e}", file=sys.stderr)
            sys.exit(1)

    slug = slugify(prompt)
    client = genai.Client(api_key=api_key)
    session = load_rembg_session()

    # Note: Gemini Flash doesn't support batch generation like Imagen
    # We'll need to make n separate requests if n > 1
    if n > 1:
        print(f"Note: Gemini Flash requires {n} separate requests for multiple images", file=sys.stderr)

    saved: list[Path] = []
    t0 = time.time()

    for i in range(n):
        # Build contents list: prompt + reference images
        contents = [prompt] + loaded_images

        # Generate with Gemini Flash
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE'],
                image_config=types.ImageConfig(
                    aspect_ratio=size,
                    image_size="1K",  # Default to 1K for now
                ),
            ),
        )

        # Extract generated images from response
        for part in response.parts:
            if part.inline_data is not None:
                # Convert Gemini image to PIL Image from inline data
                img_bytes = part.inline_data.data
                img = Image.open(BytesIO(img_bytes))

                # Apply background removal
                result = remove(img, session=session)

                # Determine output path
                if output:
                    path = output if n == 1 else output.with_stem(f"{output.stem}-{len(saved) + 1}")
                else:
                    path = Path(f"{slug}.png") if n == 1 else Path(f"{slug}-{len(saved) + 1}.png")

                result.save(path)
                saved.append(path)
                print(f"Saved {path}", file=sys.stderr)
                open_image(path)

    t1 = time.time()
    print(f"Total: {t1 - t0:.1f}s", file=sys.stderr)

    return saved


def generate_transparent_png(
    prompt: str,
    output: Path | None = None,
    reference_images: list[Path] | None = None,
    n: int = 1,
    size: str = "1:1",
    style: str | None = None,
    model: str = "fast",
) -> list[Path]:
    # Route to Gemini Flash if reference images provided
    if reference_images:
        return generate_with_gemini_flash(
            prompt=prompt,
            reference_images=reference_images,
            output=output,
            n=n,
            size=size,
        )

    # Otherwise use Imagen 4 (existing behavior)
    api_key = get_api_key()

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
    session = load_rembg_session()

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
        open_image(path)
    print(f"Total: {t2 - t0:.1f}s", file=sys.stderr)

    return saved
