from myapp.config.llm import ai_Model 
from pathlib import Path
from typing import Optional
import base64

from PIL import Image

from langchain_core.messages import HumanMessage

# ---------------------------------------------------------
    # GEMINI HANDWRITTEN KANNADA OCR
    # ---------------------------------------------------------

def extract_handwritten_text_with_gemini(image: Image.Image) -> str:

    # Convert PIL image to JPEG bytes
    image = image.convert("RGB")

    from io import BytesIO

    buffer = BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=95
    )

    image_bytes = buffer.getvalue()

    # Convert image to base64
    image_base64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    # Prompt for Gemini
    prompt = """
You are a Kannada handwriting OCR system.

Read the Kannada text written in this image.

Your task is ONLY to transcribe the text.

Rules:

1. Extract the Kannada text exactly as written.
2. Do NOT translate the Kannada text.
3. Preserve the original line breaks as much as possible.
4. Do not summarize the content.
5. Do not explain the image.
6. Do not add information that is not present.
7. If a word or character is genuinely impossible to read,
   write [unclear].
8. Return ONLY the extracted Kannada text.
"""

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": prompt
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": (
                        f"data:image/jpeg;base64,"
                        f"{image_base64}"
                    )
                }
            }
        ]
    )

    response = ai_Model.invoke(
        [message]
    )

    return response.content.strip()
