import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from typing import Any, Dict
import logging
from logtail import LogtailHandler
from src.config.config import LOGTAIL_TOKEN, LOGTAIL_SOURCE, DEBUG


class LoggerService:
    loggers: Dict[str, logging.Logger] = {}

    @staticmethod
    def info(file_name: str, message: str, update=None, **kwargs: Any):
        if DEBUG:
            print(f"INFO {file_name}: {message}")
            return

        logger = LoggerService.__get_logger__(file_name)

        if update:
            kwargs["chat_id"] = LoggerService.__get_chat_id__(update)

        logger.info(f"{message}", extra=kwargs)

    @staticmethod
    def error(
        file_name: str,
        message: str,
        exception: Exception = None,
        update=None,
        **kwargs: Any,
    ):
        if DEBUG:
            print(f"ERROR {message}: {exception}")
            return

        logger = LoggerService.__get_logger__(file_name)

        if update:
            kwargs["chat_id"] = LoggerService.__get_chat_id__(update)

        if exception:
            logger.exception(f"{message}", exc_info=exception, extra=kwargs)
        else:
            logger.error(message, extra=kwargs)

    @staticmethod
    def warning(file_name: str, message: str, update=None, **kwargs: Any):
        if DEBUG:
            print(f"WARNING {message}")
            return

        logger = LoggerService.__get_logger__(file_name)

        if update:
            kwargs["chat_id"] = LoggerService.__get_chat_id__(update)

        logger.warning(message, extra=kwargs)

    @staticmethod
    def __get_chat_id__(update):
        if update.message:
            return update.message.chat.id
        else:
            return update.callback_query.message.chat.id

    @staticmethod
    def __get_logger__(file_name: str) -> logging.Logger:
        if file_name in LoggerService.loggers:
            return LoggerService.loggers[file_name]

        logtail_handler = LogtailHandler(
            source_token=LOGTAIL_TOKEN,
            host=LOGTAIL_SOURCE,
        )

        logger = logging.getLogger(file_name)
        logger.setLevel(logging.INFO)
        logger.handlers = []
        logger.addHandler(logtail_handler)
        LoggerService.loggers[file_name] = logger
        return logger
