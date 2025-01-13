from src.llm.openai_client import OpenAIClient

def ask_openai(prompt: str):
    client = OpenAIClient(api_key="your-openai-api-key")
    return client.generate_response(prompt)