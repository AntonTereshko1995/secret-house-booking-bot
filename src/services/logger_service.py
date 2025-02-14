import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from loguru import logger
from logtail import LogtailHandler
from src.config.config import LOGTAIL_TOKEN

class LoggerService:
    @staticmethod
    def init_logger():
        logtail_handler = LogtailHandler(source_token=LOGTAIL_TOKEN)
        logger.remove()  # Remove default loguru handler
        logger.add(logtail_handler, level="INFO")  # Attach Logtail handler

    @staticmethod
    def info(message: str, update=None):
        if update:
            if update.message:
                chat_id = update.message.chat.id
            else:
                chat_id = update.callback_query.message.chat.id
            logger.info(f"{message} [Chat {chat_id}]")
        else:
            logger.info(message)

    @staticmethod
    def error(message: str, exception: Exception = None):
        if exception:
            logger.error(f"{message} | Exception: {exception}")
        else:
            logger.error(message)

    @staticmethod
    def debug(message: str):
        logger.debug(message)

    @staticmethod
    def warning(message: str, update=None):
        logger.warning(message)