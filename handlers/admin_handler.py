import re
from telegram import Update, Chat
from telegram.ext import ContextTypes
from config import ADMINS_CHAT_ID
from database.db import get_user_by_qid, mark_answered
from utils.logger import Logger

logger = Logger().get_logger()


async def on_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat: Chat = update.effective_chat

    if chat.id != ADMINS_CHAT_ID:
        return

    if not msg.reply_to_message or not msg.text:
        return

    original_text = msg.reply_to_message.text or ""
    match = re.search(r"\(ID:(\w+)\)", original_text)
    if not match:
        return

    qid = match.group(1)
    row = await get_user_by_qid(qid)
    if not row:
        await msg.reply_text("Не найден пользователь для этого вопроса (возможно уже отвечен).")
        return

    user_chat_id = row[0]
    admin_user = update.effective_user

    try:
        await context.bot.send_message(
            chat_id=user_chat_id,
            text=f"💬 Ответ от команды:\n\n{msg.text}"
        )
        await mark_answered(qid)
        await msg.reply_text(f"✅ Ответ отправлен пользователю (вопрос ID:{qid}).")

        logger.info(
            f"Админ {admin_user.username} "
            f"ответил на вопрос ID:{qid}: \"{msg.text}\""
        )

    except Exception as e:
        await msg.reply_text(f"❌ Ошибка при отправке ответа: {e}")
        logger.error(f"Ошибка при отправке ответа на вопрос ID:{qid}: {e}")
