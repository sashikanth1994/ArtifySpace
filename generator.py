import replicate
import requests
from io import BytesIO
from PIL import Image


FLUX_MODEL = "black-forest-labs/flux-schnell"

# Style suffix appended to every prompt for consistency
STYLE_SUFFIX = (
    "professional art photography, gallery lighting, clean neutral background, "
    "high detail, 4k, photorealistic render"
)


def generate_concept_image(image_prompt: str, width: int = 1024, height: int = 768) -> Image.Image:
    """
    Generate a single concept image via Replicate FLUX.1-schnell.
    Returns a PIL Image.
    """
    full_prompt = f"{image_prompt}. {STYLE_SUFFIX}"

    output = replicate.run(
        FLUX_MODEL,
        input={
            "prompt": full_prompt,
            "width": width,
            "height": height,
            "num_inference_steps": 4,   # schnell is optimized for 4 steps
            "output_format": "webp",
            "output_quality": 90,
        },
    )

    # Replicate returns a list of FileOutput objects
    image_url = output[0] if isinstance(output, list) else output

    response = requests.get(str(image_url), timeout=30)
    response.raise_for_status()

    img = Image.open(BytesIO(response.content)).convert("RGB")
    return img


def generate_all_concepts(concepts: list[dict]) -> list[Image.Image]:
    """
    Generate images for all 3 concepts. Returns list of PIL Images.
    """
    images = []
    for concept in concepts:
        img = generate_concept_image(concept["image_prompt"])
        images.append(img)
    return images


if __name__ == "__main__":
    # Quick test
    test_prompt = (
        "A large abstract bronze sculpture with flowing organic curves, "
        "modern minimalist style, warm golden tones"
    )
    print("Generating test image...")
    img = generate_concept_image(test_prompt)
    img.save("test_output.webp")
    print(f"Saved to test_output.webp — size: {img.size}")