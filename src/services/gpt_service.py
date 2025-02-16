import sys
import os

from src.services.logger_service import LoggerService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.database_service import DatabaseService
from openai import OpenAI
from singleton_decorator import singleton
from src.config.config import TELEGRAM_KEY, TELEGRAM_PROMPT

GPT_MODEL = "gpt-4o-mini"

@singleton
class GptService:
    def __init__(self):
        self.client = OpenAI(api_key=TELEGRAM_KEY)
        self.database_service = DatabaseService()

    async def generate_response(self, message: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                temperature=0.7,
                max_tokens=500,
                messages=[
                    {
                        "role": "system",
                        "content": TELEGRAM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": message,
                    },
                ])

            return response.choices[0].message.content
        except Exception as e:
            print(f"Chat GPT Error: {e}")
            LoggerService.error(__name__, f"generate_response", e)
            return "Произошла ошибка. Попробуйте позже."