from telegram import Update, Chat
from telegram.ext import ContextTypes
from utils.logger import Logger
from utils.user_formatter import format_user_for_log

logger = Logger().get_logger()


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Привет! Это официальный Бот ТК АСК.\n\n"
        "Отправь свой вопрос, и он будет отправлен команде Турнирного комитета.\n\n"
        "Ответ придёт сюда!"
    )
    user = update.effective_user
    user_label = format_user_for_log(user)
    logger.info(f"Пользователь {user_label} вызвал /start.")


async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat: Chat = update.effective_chat
    await update.effective_message.reply_text(
        f"ID этого чата: `{chat.id}`", parse_mode="Markdown"
    )
    user = update.effective_user
    user_label = format_user_for_log(user)
    logger.info(f"Пользователь {user_label} вызвал /chatid в чате {chat.id}.")
