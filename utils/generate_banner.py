#!/usr/bin/env python3
"""
Generate a banner image for a KidsCode project using Gemini image generation.

Usage:
    GOOGLE_API_KEY=... python utils/generate_banner.py

Reads banner_spec.json from the project root, generates the image,
crops/resizes to 2320x462, saves to static/graphics/, then deletes
banner_spec.json.
"""

import sys
import os
import json
from pathlib import Path


TARGET_W = 2320
TARGET_H = 462
TARGET_RATIO = TARGET_W / TARGET_H  # ~5.02


def load_spec():
    spec_path = Path("banner_spec.json")
    if not spec_path.exists():
        sys.exit("Error: banner_spec.json not found in project root")
    with open(spec_path) as f:
        return json.load(f), spec_path


def get_api_key():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit("Error: set GOOGLE_API_KEY or GEMINI_API_KEY in your environment or .env")
    return key


def generate_image(prompt: str, api_key: str) -> bytes:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        sys.exit("Error: google-genai not installed. Run: pip install google-genai")

    client = genai.Client(api_key=api_key)

    print("Calling Gemini image generation...")
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"]
        ),
    )

    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None) is not None:
            data = part.inline_data.data
            # SDK may return bytes or base64 string
            if isinstance(data, (bytes, bytearray)):
                return bytes(data)
            import base64
            return base64.b64decode(data)

    sys.exit("Error: Gemini returned no image. Check your prompt or API quota.")


def fit_to_banner(image_bytes: bytes, output_path: Path):
    try:
        from PIL import Image
        import io
    except ImportError:
        # Pillow not available — save as-is
        output_path.write_bytes(image_bytes)
        print(f"✅ Saved (no resize — Pillow unavailable): {output_path}")
        return

    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = img.size
    print(f"   Generated: {w}x{h} (ratio {w/h:.2f}:1, target {TARGET_RATIO:.2f}:1)")

    current_ratio = w / h

    if abs(current_ratio - TARGET_RATIO) < 0.05:
        # Already close enough — just resize
        final = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
    elif current_ratio > TARGET_RATIO:
        # Wider than target — crop left/right
        new_w = int(h * TARGET_RATIO)
        left = (w - new_w) // 2
        final = img.crop((left, 0, left + new_w, h)).resize(
            (TARGET_W, TARGET_H), Image.LANCZOS
        )
    else:
        # Taller than target — crop top/bottom (keep vertical center)
        new_h = int(w / TARGET_RATIO)
        top = (h - new_h) // 2
        final = img.crop((0, top, w, top + new_h)).resize(
            (TARGET_W, TARGET_H), Image.LANCZOS
        )

    final.save(output_path, "PNG")
    print(f"✅ Saved: {output_path} ({TARGET_W}x{TARGET_H})")


def main():
    spec, spec_path = load_spec()
    project_key = spec.get("key")
    prompt = spec.get("prompt")

    if not project_key or not prompt:
        sys.exit("Error: banner_spec.json must contain 'key' and 'prompt'")

    output_path = Path(f"static/graphics/{project_key}_banner.png")

    api_key = get_api_key()
    image_bytes = generate_image(prompt, api_key)
    fit_to_banner(image_bytes, output_path)

    spec_path.unlink()


if __name__ == "__main__":
    main()
