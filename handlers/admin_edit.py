import html
import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import ADMINS_CHAT_ID
from database.db import get_user_by_qid
from utils.logger import Logger
from utils.user_formatter import format_user_for_log

logger = Logger().get_logger()


async def on_admin_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.edited_message
    if not msg:
        logger.info("Edited message is None, ignoring")
        return

    logger.info(
        f"Edited message received: chat_id={msg.chat_id}, message_id={msg.message_id}"
    )

    if not msg.text:
        logger.info("Edited message has no text, ignoring")
        return

    if msg.chat_id != ADMINS_CHAT_ID:
        logger.info(
            f"Edited message ignored: chat_id {msg.chat_id} is not admin chat"
        )
        return

    if not msg.reply_to_message:
        logger.info("Edited message has no reply_to_message, ignoring")
        return

    original_text = msg.reply_to_message.text or ""
    logger.info(f"Original replied message text: {original_text}")

    match = re.search(r"\(ID:(\w+)\)", original_text)
    if not match:
        logger.warning("No QID found in the replied message")
        return

    qid = match.group(1)
    logger.info(f"Found QID: {qid}")

    row = await get_user_by_qid(qid, include_answered=True)
    if not row:
        logger.warning(f"No database entry found for QID {qid}")
        return

    user_chat_id, question_text, answer_message_id = row
    logger.info(
        f"Database entry: user_chat_id={user_chat_id}, question_text='{question_text}', answer_message_id={answer_message_id}"
    )

    if not answer_message_id:
        logger.warning(f"For QID:{qid} there is no saved answer_message_id")
        return

    admin_user = update.effective_user
    admin_label = format_user_for_log(admin_user)

    try:
        new_text = (
            "💬 <b>Твой вопрос:</b>\n\n"
            f"{html.escape(question_text)}\n\n"
            "💡 <b>Ответ (обновлён):</b>\n\n"
            f"{html.escape(msg.text)}"
        )

        await context.bot.edit_message_text(
            chat_id=user_chat_id,
            message_id=answer_message_id,
            text=new_text,
            parse_mode=ParseMode.HTML,
        )

        logger.info(
            f"Admin {admin_label} successfully edited answer for QID:{qid} with new text: {msg.text}"
        )

    except Exception as e:
        logger.error(
            f"Error editing answer for QID:{qid}: {e}"
        )
