from google.cloud import vision_v1p3beta1 as vision


class VisionClient:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    async def image_to_text_client(self, content) -> str:
        image = vision.Image(content=content)

        response = self.client.text_detection(image=image)
        texts = response.text_annotations

        if response.error.message:
            return "Something went wrong. We are working on it!"

        return texts[0].description
