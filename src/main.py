import sys
import os
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from telegram import Update
from telegram.ext import Application
from src.handlers import menu_handler
from src.config.config import TELEGRAM_TOKEN
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(menu_handler.get_handler())
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()