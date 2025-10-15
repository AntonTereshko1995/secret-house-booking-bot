import sys
import os
from src.services.logger_service import LoggerService

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.services.database_service import DatabaseService
from openai import APITimeoutError, OpenAI
from singleton_decorator import singleton
from src.config.config import GPT_KEY, GPT_PROMPT

GPT_MODEL = "gpt-4o-mini"


@singleton
class GptService:
    def __init__(self):
        self.client = OpenAI(api_key=GPT_KEY, timeout=30)
        self.database_service = DatabaseService()

    async def generate_response(self, message: str) -> str:
        retries = 3
        while retries > 0:
            try:
                response = self.client.chat.completions.create(
                    model=GPT_MODEL,
                    temperature=0.7,
                    max_tokens=500,
                    messages=[
                        {
                            "role": "system",
                            "content": GPT_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": message,
                        },
                    ],
                )

                return response.choices[0].message.content
            except APITimeoutError:
                print("Chat GPT Timeout Error")
                LoggerService.warning(
                    __name__, "generate_response", "Chat GPT Timeout Error. Try again."
                )
                retries -= 1
                if retries == 0:
                    LoggerService.error(
                        __name__, "generate_response", "Chat GPT Timeout Error"
                    )
                    return "Произошла ошибка. Попробуйте позже."
            except Exception as e:
                print(f"Chat GPT Error: {e}")
                LoggerService.error(__name__, "generate_response", e)
                return "Произошла ошибка. Попробуйте позже."
