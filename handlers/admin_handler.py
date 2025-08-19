import re
import html
from telegram import Update, Chat
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
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
        await msg.reply_text("Ваш ответ не отправлен (возможно на этот вопрос уже ответили).")
        return

    user_chat_id, question_text = row
    admin_user = update.effective_user

    try:
        user_answer = (
            "💬 <b>Твой вопрос:</b>\n\n"
            f"{html.escape(question_text)}\n\n"
            "💡 <b>Ответ:</b>\n\n"
            f"{html.escape(msg.text)}"
        )

        await context.bot.send_message(
            chat_id=user_chat_id,
            text=user_answer,
            parse_mode=ParseMode.HTML
        )

        await mark_answered(qid)

        try:
            await context.bot.unpin_chat_message(
                chat_id=ADMINS_CHAT_ID,
                message_id=msg.reply_to_message.message_id
            )
            logger.info(f"Вопрос ID:{qid} откреплён после ответа.")
        except Exception as e:
            logger.error(f"Не удалось открепить вопрос ID:{qid}: {e}")

        await msg.reply_text("✅ Ответ отправлен пользователю.")
        logger.info(
            f"Админ {admin_user.username} ответил на вопрос ID:{qid}: \"{msg.text}\""
        )

    except Exception as e:
        await msg.reply_text(f"❌ Ошибка при отправке ответа: {e}")
        logger.error(f"Ошибка при отправке ответа на вопрос ID:{qid}: {e}")
