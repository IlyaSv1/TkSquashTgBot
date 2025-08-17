import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config import BOT_TOKEN
from database.db import init_db
from handlers.commands import cmd_start, cmd_chatid
from handlers.user_handler import on_user_message
from handlers.admin_handler import on_admin_reply
from utils.logger import Logger

logger = Logger().get_logger()

if __name__ == "__main__":
    logger.info("Инициализация базы данных…")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    logger.info("База данных инициализирована.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("chatid", cmd_chatid))
    logger.info("Команды зарегистрированы.")

    app.add_handler(MessageHandler(filters.ChatType.PRIVATE &
                    filters.TEXT, on_user_message))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT, on_admin_reply))
    logger.info("Обработчики сообщений зарегистрированы.")

    logger.info("Бот запущен. Ожидание сообщений…")
    try:
        app.run_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
