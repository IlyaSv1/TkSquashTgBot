from telegram import Update, Chat
from telegram.ext import ContextTypes
from utils.logger import Logger

logger = Logger().get_logger()


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Привет! Это официальный Бот ТК АСК.\n\n"
        "Отправь свой вопрос, и он будет отправлен команде Турнирного комитета.\n\n"
        "Ответ придёт сюда!"
    )
    user = update.effective_user
    logger.info(f"Пользователь {user.id} ({user.username}) вызвал /start.")


async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat: Chat = update.effective_chat
    await update.effective_message.reply_text(
        f"ID этого чата: `{chat.id}`", parse_mode="Markdown"
    )
    user = update.effective_user
    logger.info(
        f"Пользователь {user.id} ({user.username}) вызвал /chatid в чате {chat.id}.")
