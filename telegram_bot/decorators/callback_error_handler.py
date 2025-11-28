from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from telegram_bot.services.logger_service import LoggerService


def safe_callback_query(recovery_function=None):
    """
    Decorator for callback query handlers to gracefully handle expired queries.

    Args:
        recovery_function: Optional async function to call for recovery
                          Signature: async def recovery(update, context)

    Usage:
        @safe_callback_query(recovery_function=show_menu)
        async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.callback_query.answer()
            # ... rest of handler logic
    """
    def decorator(handler_func):
        @wraps(handler_func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            try:
                return await handler_func(update, context)
            except BadRequest as e:
                error_msg = str(e).lower()

                # Check for specific error messages
                if "query is too old" in error_msg or "query id is invalid" in error_msg:
                    LoggerService.info(
                        __name__,
                        "Callback query expired (likely bot restart)",
                        update,
                        kwargs={"error": str(e)}
                    )

                    # Try to answer with alert popup
                    try:
                        if update.callback_query:
                            await update.callback_query.answer(
                                "⚠️ Это действие больше недоступно. Обновляем меню...",
                                show_alert=True
                            )
                    except:
                        pass  # If answer also fails, ignore

                    # Call recovery function if provided
                    if recovery_function:
                        return await recovery_function(update, context)

                    # Default recovery: import and call show_menu
                    from telegram_bot.handlers import menu_handler
                    return await menu_handler.show_menu(update, context)
                else:
                    # Re-raise if it's a different BadRequest error
                    raise
            except Exception as e:
                # Log unexpected errors and re-raise
                LoggerService.error(
                    __name__,
                    "Unexpected error in callback handler",
                    exception=e,
                    update=update
                )
                raise

        return wrapper
    return decorator
