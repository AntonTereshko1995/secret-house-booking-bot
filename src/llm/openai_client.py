import openai

class OpenAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        openai.api_key = self.api_key

    def generate_response(self, prompt: str, model: str = "gpt-3.5-turbo"):
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"]