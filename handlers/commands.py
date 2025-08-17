from telegram import Update, Chat
from telegram.ext import ContextTypes
from utils.logger import Logger

logger = Logger().get_logger()


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Привет! Это анонимный Q&A бот.\n\n"
        "Отправь свой вопрос сюда, и он придёт команде.\n"
        "Ответ придёт обратно анонимно."
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
