import os
from dotenv import load_dotenv
from google.cloud import vision_v1p3beta1 as vision

load_dotenv()

vision_api_key = os.getenv("VISION_API_KEY")
vision_client = vision.ImageAnnotatorClient()


async def image_to_text_client(content) -> str:
    image = vision.Image(content=content)

    response = vision_client.text_detection(image=image)
    texts = response.text_annotations

    if response.error.message:
        return "Something went wrong. We are working on it!"

    return texts[0].description
