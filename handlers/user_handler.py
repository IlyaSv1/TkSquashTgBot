from telegram import Update, Message
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from config import ADMINS_CHAT_ID
from database.db import save_mapping
from utils.helpers import short_id
from utils.logger import Logger
from utils.user_formatter import format_user_for_log, format_user_for_admin

logger = Logger().get_logger()
ID_PREFIX = "Q#"


async def on_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg: Message = update.effective_message

    logger.info(f"Received message from {msg.chat.id} of type {msg.chat.type}")

    if msg.chat.type != msg.chat.PRIVATE:
        logger.info("Message ignored: not private chat")
        return

    text = msg.text or msg.caption or ""
    has_media = bool(msg.photo or msg.document or msg.video or msg.audio)

    if not text and not has_media:
        await msg.reply_text("Пожалуйста, отправь текстовый вопрос или файл.")
        logger.warning(
            f"Пользователь {msg.chat.id} отправил пустое сообщение.")
        return

    qid = short_id()
    question_text = text or ""
    file_id = None
    media_type = None

    if msg.photo:
        file_id = msg.photo[-1].file_id
        media_type = "photo"
    elif msg.document:
        file_id = msg.document.file_id
        media_type = "document"
    elif msg.video:
        file_id = msg.video.file_id
        media_type = "video"
    elif msg.audio:
        file_id = msg.audio.file_id
        media_type = "audio"

    await save_mapping(qid, msg.chat.id, question_text, question_file_id=file_id)

    user_label_admin = format_user_for_admin(update.effective_user)
    user_label_log = format_user_for_log(update.effective_user)

    header = f"❓ <b>Новый вопрос</b> от {user_label_admin}\n\n"
    header += f"{text if text else '📎 Вопрос содержит файл'}\n\n(ID:{qid})"
    logger.info(
        f"Новый вопрос {ID_PREFIX}{qid} от {user_label_log}: {question_text}")

    try:
        if media_type == "photo":
            sent = await context.bot.send_photo(
                chat_id=ADMINS_CHAT_ID,
                photo=file_id,
                caption=header,
                parse_mode=ParseMode.HTML
            )
        elif media_type == "document":
            sent = await context.bot.send_document(
                chat_id=ADMINS_CHAT_ID,
                document=file_id,
                caption=header,
                parse_mode=ParseMode.HTML
            )
        elif media_type == "video":
            sent = await context.bot.send_video(
                chat_id=ADMINS_CHAT_ID,
                video=file_id,
                caption=header,
                parse_mode=ParseMode.HTML
            )
        elif media_type == "audio":
            sent = await context.bot.send_audio(
                chat_id=ADMINS_CHAT_ID,
                audio=file_id,
                caption=header,
                parse_mode=ParseMode.HTML
            )
        else:
            sent = await context.bot.send_message(
                chat_id=ADMINS_CHAT_ID,
                text=header,
                parse_mode=ParseMode.HTML
            )

        await context.bot.send_message(
            chat_id=ADMINS_CHAT_ID,
            text="👉 <b>Ответь на это сообщение реплаем, чтобы ответить пользователю</b>.",
            reply_to_message_id=sent.message_id,
            parse_mode=ParseMode.HTML,
        )

        try:
            await context.bot.pin_chat_message(
                chat_id=ADMINS_CHAT_ID,
                message_id=sent.message_id,
                disable_notification=True,
            )
            logger.info(f"Вопрос {ID_PREFIX}{qid} закреплён в чате админов.")
        except Exception as e:
            logger.error(f"Не удалось закрепить вопрос {ID_PREFIX}{qid}: {e}")

        logger.info(f"Вопрос {ID_PREFIX}{qid} отправлен в чат админов.")

    except Exception as e:
        await msg.reply_text("Не удалось отправить вопрос. Попробуй позже.")
        logger.error(
            f"Ошибка при отправке вопроса {ID_PREFIX}{qid} в чат админов: {e}")
        return

    await msg.reply_text("Вопрос отправлен команде. Ответ придёт сюда.")


def register_handlers(dispatcher):
    dispatcher.add_handler(
        MessageHandler(filters.ALL & filters.ChatType.PRIVATE, on_user_message)
    )
