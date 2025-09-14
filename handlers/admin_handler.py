import re
import html
from telegram import Update, Chat
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import ADMINS_CHAT_ID
from database.db import (
    get_user_by_qid,
    save_answer_message_id,
    save_answer_file_id,
    save_answer_type,
    mark_answered
)
from utils.logger import Logger
from utils.user_formatter import format_user_for_log

logger = Logger().get_logger()


async def on_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat: Chat = update.effective_chat

    if chat.id != ADMINS_CHAT_ID or not msg.reply_to_message:
        return

    has_content = msg.text or msg.caption or msg.photo or msg.document or msg.video or msg.audio
    if not has_content:
        return

    original_text = msg.reply_to_message.text or msg.reply_to_message.caption or ""
    match = re.search(r"\(ID:(\w+)\)", original_text)
    if not match:
        return

    qid = match.group(1)
    row = await get_user_by_qid(qid, include_answered=True)
    if not row:
        await msg.reply_text(
            "Ваш ответ не отправлен (возможно, на этот вопрос уже ответили)."
        )
        return

    user_chat_id, question_text, answer_message_id, question_file_id, answer_type = row
    admin_user = update.effective_user
    admin_label = format_user_for_log(admin_user)

    answer_content = msg.text or msg.caption or ""
    user_text = (
        "💬 <b>Твой вопрос:</b>\n\n"
        f"{html.escape(question_text)}\n\n"
        "💡 <b>Ответ:</b>\n\n"
        f"{html.escape(answer_content)}"
    )

    try:
        if not answer_message_id:
            if msg.photo:
                sent_msg = await context.bot.send_photo(
                    chat_id=user_chat_id,
                    photo=msg.photo[-1].file_id,
                    caption=user_text,
                    parse_mode=ParseMode.HTML
                )
                await save_answer_file_id(qid, msg.photo[-1].file_id)
                await save_answer_type(qid, "media")
            elif msg.document:
                sent_msg = await context.bot.send_document(
                    chat_id=user_chat_id,
                    document=msg.document.file_id,
                    caption=user_text,
                    parse_mode=ParseMode.HTML
                )
                await save_answer_file_id(qid, msg.document.file_id)
                await save_answer_type(qid, "media")
            elif msg.video:
                sent_msg = await context.bot.send_video(
                    chat_id=user_chat_id,
                    video=msg.video.file_id,
                    caption=user_text,
                    parse_mode=ParseMode.HTML
                )
                await save_answer_file_id(qid, msg.video.file_id)
                await save_answer_type(qid, "media")
            elif msg.audio:
                sent_msg = await context.bot.send_audio(
                    chat_id=user_chat_id,
                    audio=msg.audio.file_id,
                    caption=user_text,
                    parse_mode=ParseMode.HTML
                )
                await save_answer_file_id(qid, msg.audio.file_id)
                await save_answer_type(qid, "media")
            else:
                sent_msg = await context.bot.send_message(
                    chat_id=user_chat_id,
                    text=user_text,
                    parse_mode=ParseMode.HTML
                )
                await save_answer_type(qid, "text")

            await save_answer_message_id(qid, sent_msg.message_id)

            try:
                await context.bot.unpin_chat_message(
                    chat_id=ADMINS_CHAT_ID,
                    message_id=msg.reply_to_message.message_id
                )
            except Exception as e:
                logger.error(f"Failed to unpin question QID:{qid}: {e}")

            await msg.reply_text("✅ Ответ отправлен пользователю.")
            logger.info(f"Admin {admin_label} answered QID {qid}")

        else:
            if answer_type == "text":
                if msg.photo or msg.document or msg.video or msg.audio:
                    try:
                        await context.bot.delete_message(
                            chat_id=user_chat_id,
                            message_id=answer_message_id
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to delete old message QID:{qid}: {e}")

                    if msg.photo:
                        sent_msg = await context.bot.send_photo(
                            chat_id=user_chat_id,
                            photo=msg.photo[-1].file_id,
                            caption=user_text,
                            parse_mode=ParseMode.HTML
                        )
                        await save_answer_file_id(qid, msg.photo[-1].file_id)
                    elif msg.document:
                        sent_msg = await context.bot.send_document(
                            chat_id=user_chat_id,
                            document=msg.document.file_id,
                            caption=user_text,
                            parse_mode=ParseMode.HTML
                        )
                        await save_answer_file_id(qid, msg.document.file_id)
                    elif msg.video:
                        sent_msg = await context.bot.send_video(
                            chat_id=user_chat_id,
                            video=msg.video.file_id,
                            caption=user_text,
                            parse_mode=ParseMode.HTML
                        )
                        await save_answer_file_id(qid, msg.video.file_id)
                    elif msg.audio:
                        sent_msg = await context.bot.send_audio(
                            chat_id=user_chat_id,
                            audio=msg.audio.file_id,
                            caption=user_text,
                            parse_mode=ParseMode.HTML
                        )
                        await save_answer_file_id(qid, msg.audio.file_id)

                    await save_answer_message_id(qid, sent_msg.message_id)
                    await save_answer_type(qid, "media")

                else:
                    await context.bot.edit_message_text(
                        chat_id=user_chat_id,
                        message_id=answer_message_id,
                        text=user_text,
                        parse_mode=ParseMode.HTML
                    )

            else:
                await context.bot.edit_message_caption(
                    chat_id=user_chat_id,
                    message_id=answer_message_id,
                    caption=user_text,
                    parse_mode=ParseMode.HTML
                )

            logger.info(
                f"Admin {admin_label} edited previous answer for QID {qid}")

        await mark_answered(qid)

    except Exception as e:
        logger.error(f"Error sending/editing reply for QID {qid}: {e}")
        await msg.reply_text(f"❌ Ошибка при отправке ответа: {e}")
