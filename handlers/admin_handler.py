import re
import html
from telegram import Update, Chat
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import ADMINS_CHAT_ID
from database.db import get_user_by_qid, save_answer_message_id
from utils.logger import Logger
from utils.user_formatter import format_user_for_log

logger = Logger().get_logger()


async def on_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat: Chat = update.effective_chat

    logger.info(f"on_admin_reply triggered by chat_id={chat.id}")

    if chat.id != ADMINS_CHAT_ID:
        logger.info("Message ignored: not from admin chat")
        return

    if not msg.reply_to_message or not msg.text:
        logger.info("Message ignored: no reply_to_message or no text")
        return

    original_text = msg.reply_to_message.text or ""
    match = re.search(r"\(ID:(\w+)\)", original_text)
    if not match:
        logger.warning("No QID found in replied message")
        return

    qid = match.group(1)
    logger.info(f"Found QID: {qid}")

    row = await get_user_by_qid(qid, include_answered=True)
    if not row:
        logger.warning(f"No user found for QID {qid}")
        await msg.reply_text(
            "Ваш ответ не отправлен (возможно, на этот вопрос уже ответили)."
        )
        return

    user_chat_id, question_text, answer_message_id = row
    logger.info(
        f"User chat_id={user_chat_id}, question_text={question_text}, answer_message_id={answer_message_id}"
    )

    admin_user = update.effective_user
    admin_label = format_user_for_log(admin_user)

    user_answer = (
        "💬 <b>Твой вопрос:</b>\n\n"
        f"{html.escape(question_text)}\n\n"
        "💡 <b>Ответ:</b>\n\n"
        f"{html.escape(msg.text)}"
    )

    try:
        if not answer_message_id:
            sent_msg = await context.bot.send_message(
                chat_id=user_chat_id,
                text=user_answer,
                parse_mode=ParseMode.HTML,
            )
            logger.info(
                f"Message sent to user {user_chat_id}, message_id={sent_msg.message_id}"
            )

            await save_answer_message_id(qid, sent_msg.message_id)

            try:
                await context.bot.unpin_chat_message(
                    chat_id=ADMINS_CHAT_ID,
                    message_id=msg.reply_to_message.message_id,
                )
                logger.info(
                    f"Question QID:{qid} successfully unpinned in admin chat")
            except Exception as e:
                logger.error(f"Failed to unpin question QID:{qid}: {e}")

            await msg.reply_text("✅ Ответ отправлен пользователю.")
            logger.info(f"Admin {admin_label} answered QID {qid}: {msg.text}")

        else:
            await context.bot.edit_message_text(
                chat_id=user_chat_id,
                message_id=answer_message_id,
                text=user_answer,
                parse_mode=ParseMode.HTML,
            )
            logger.info(
                f"Admin {admin_label} edited previous answer for QID {qid}"
            )

    except Exception as e:
        logger.error(f"Error sending/editing reply for QID {qid}: {e}")
        await msg.reply_text(f"❌ Ошибка при отправке ответа: {e}")
