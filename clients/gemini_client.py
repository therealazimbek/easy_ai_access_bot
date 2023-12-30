import google.generativeai as genai


class GeminiClient:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel('gemini-pro')

    async def generate_response(self, user_input):
        response = self.client.generate_content(user_input)
        return response.text
