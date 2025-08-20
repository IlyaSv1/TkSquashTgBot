import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
from config import BOT_TOKEN
from database.db import init_db
from handlers.commands import cmd_start, cmd_chatid
from handlers.user_handler import on_user_message
from handlers.admin_handler import on_admin_reply
from handlers.error_handler import error_handler
from utils.logger import Logger

logger = Logger().get_logger()


def main():
    logger.info("Инициализация базы данных…")
    asyncio.run(init_db())
    logger.info("База данных инициализирована.")

    # Создаём и устанавливаем loop вручную (для Python 3.12 / Windows)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("chatid", cmd_chatid))
    logger.info("Команды зарегистрированы.")

    # Сообщения пользователей
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT, on_user_message
    ))

    # Сообщения админов
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT, on_admin_reply
    ))
    logger.info("Обработчики сообщений зарегистрированы.")

    # Глобальный обработчик ошибок
    app.add_error_handler(error_handler)
    logger.info("Глобальный обработчик ошибок подключен.")

    logger.info("Бот запущен. Ожидание сообщений…")
    # Запускаем polling
    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(
            f"❌ Критическая ошибка при запуске бота: {e}", exc_info=True)
