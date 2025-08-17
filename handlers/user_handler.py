import re
from telegram import Update, Message, Chat
from telegram.ext import ContextTypes
from config import ADMINS_CHAT_ID
from database.db import save_mapping
from utils.helpers import short_id
from utils.logger import Logger

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
    await save_mapping(qid, chat.id, msg.message_id)

    user = update.effective_user
    if user.username:
        user_label = f"@{user.username}"
    elif user.full_name:
        user_label = user.full_name
    else:
        user_label = f"id:{user.id}"

    header = f"❓ Новый вопрос от {user_label}\n\n{text}\n\n(ID:{qid})"
    logger.info(f"Новый вопрос {ID_PREFIX}{qid} от {user_label}: {text}")

    try:
        sent = await context.bot.send_message(chat_id=ADMINS_CHAT_ID, text=header)
        await context.bot.send_message(
            chat_id=ADMINS_CHAT_ID,
            text="👉 Ответь на это сообщение реплаем, чтобы ответить пользователю.",
            reply_to_message_id=sent.message_id,
        )
        logger.info(f"Вопрос {ID_PREFIX}{qid} отправлен в чат админов.")
    except Exception as e:
        await msg.reply_text("Не удалось отправить вопрос. Попробуй позже.")
        logger.error(
            f"Ошибка при отправке вопроса {ID_PREFIX}{qid} в чат админов: {e}")
        return

    await msg.reply_text("Вопрос отправлен команде. Ответ придёт сюда.")
