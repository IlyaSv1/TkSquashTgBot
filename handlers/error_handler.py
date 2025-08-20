from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import Logger

logger = Logger().get_logger()


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок"""
    logger.error("Произошла ошибка:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Произошла внутренняя ошибка. Команда уведомлена."
            )
        except Exception:
            pass
