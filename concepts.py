import anthropic
import base64
import json
import re
from pathlib import Path


SYSTEM_PROMPT = """You are an expert art curator and installation artist specializing in site-specific art for real-world spaces.

Given a photo of a space and an optional description, you generate 3 unique, thoughtful art or sculpture concepts that would genuinely elevate that environment.

You must respond ONLY with a valid JSON array. No preamble, no explanation, no markdown. Just raw JSON.

Each concept must have:
- title: Short, evocative name (max 6 words)
- description: 2-3 sentences describing the artwork, materials, and emotional impact
- placement: Where exactly in the space it would go (specific, not vague)
- image_prompt: A detailed, FLUX-optimized image generation prompt showing the artwork in isolation against a neutral background. Be specific about medium, style, colors, materials, lighting.
"""

USER_TEMPLATE = """Analyze this space and generate 3 art/sculpture concepts that would fit perfectly.

{optional_context}

Return ONLY a JSON array like this:
[
  {{
    "title": "...",
    "description": "...",
    "placement": "...",
    "image_prompt": "..."
  }},
  ...
]"""


def encode_image(image_bytes: bytes, media_type: str) -> str:
    return base64.standard_b64encode(image_bytes).decode("utf-8")


def generate_concepts(image_bytes: bytes, media_type: str, user_prompt: str = "") -> list[dict]:
    """
    Send image to Claude, get back 3 art concepts as a list of dicts.
    """
    client = anthropic.Anthropic()

    optional_context = f"Additional context from the user: {user_prompt}" if user_prompt.strip() else ""
    user_message = USER_TEMPLATE.format(optional_context=optional_context)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": encode_image(image_bytes, media_type),
                        },
                    },
                    {
                        "type": "text",
                        "text": user_message,
                    },
                ],
            }
        ],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if Claude wraps in them
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    concepts = json.loads(raw)
    return concepts


if __name__ == "__main__":
    # Quick local test — replace with a real image path
    test_image = Path("test.jpg")
    if test_image.exists():
        with open(test_image, "rb") as f:
            data = f.read()
        results = generate_concepts(data, "image/jpeg", "modern minimalist vibe")
        for i, c in enumerate(results, 1):
            print(f"\n--- Concept {i}: {c['title']} ---")
            print(f"Description: {c['description']}")
            print(f"Placement:   {c['placement']}")
            print(f"Prompt:      {c['image_prompt'][:80]}...")
    else:
        print("Drop a test.jpg in this folder to test.")