from telegram import Update, Message, Chat
from telegram.ext import ContextTypes
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
    chat: Chat = update.effective_chat

    if chat.type != Chat.PRIVATE:
        return

    text = msg.text or msg.caption
    if not text:
        await msg.reply_text("Пожалуйста, отправь текстовый вопрос.")
        logger.warning(f"Пользователь {chat.id} отправил пустое сообщение.")
        return

    qid = short_id()
    question_text = text
    await save_mapping(qid, chat.id, msg.message_id, question_text)

    user_label_admin = format_user_for_admin(
        update.effective_user)
    user_label_log = format_user_for_log(
        update.effective_user)

    header = f"❓ <b>Новый вопрос</b> от {user_label_admin}\n\n{text}\n\n(ID:{qid})"
    logger.info(f"Новый вопрос {ID_PREFIX}{qid} от {user_label_log}: {text}")

    try:
        sent = await context.bot.send_message(
            chat_id=ADMINS_CHAT_ID,
            text=header,
            parse_mode=ParseMode.HTML,
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
            f"Ошибка при отправке вопроса {ID_PREFIX}{qid} в чат админов: {e}"
        )
        return

    await msg.reply_text("Вопрос отправлен команде. Ответ придёт сюда.")
