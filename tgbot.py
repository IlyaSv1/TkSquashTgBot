import os
import random
import string
import aiosqlite
import asyncio
import re
from typing import Optional
from telegram import Update, Message, Chat
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from config import BOT_TOKEN, ADMINS_CHAT_ID

DB_PATH = os.environ.get("BOT_DB_PATH", "qa_bot.sqlite3")
ID_PREFIX = "Q#"


def _short_id(n: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


# ===== DB =====

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS qmap (
                qid TEXT PRIMARY KEY,
                user_chat_id INTEGER NOT NULL,
                user_message_id INTEGER,
                answered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.commit()


async def save_mapping(qid: str, user_chat_id: int, user_message_id: Optional[int]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO qmap(qid, user_chat_id, user_message_id) VALUES (?, ?, ?)",
            (qid, user_chat_id, user_message_id),
        )
        await db.commit()


async def get_user_by_qid(qid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_chat_id FROM qmap WHERE qid=? AND answered=0",
            (qid,)
        ) as cur:
            return await cur.fetchone()


async def mark_answered(qid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE qmap SET answered=1 WHERE qid=?", (qid,))
        await db.commit()


# ===== Handlers =====

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Привет! Это анонимный Q&A бот.\n\n"
        "Отправь свой вопрос сюда, и он придёт команде.\n"
        "Ответ придёт обратно анонимно."
    )


async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит chat_id текущего чата"""
    chat: Chat = update.effective_chat
    await update.effective_message.reply_text(f"ID этого чата: `{chat.id}`", parse_mode="Markdown")


async def on_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg: Message = update.effective_message
    chat: Chat = update.effective_chat

    if chat.type != Chat.PRIVATE:
        return

    text = msg.text or msg.caption
    if not text:
        await msg.reply_text("Пожалуйста, отправь текстовый вопрос.")
        return

    qid = _short_id()
    await save_mapping(qid, chat.id, msg.message_id)

    user = update.effective_user
    if user.username:
        user_label = f"@{user.username}"
    elif user.full_name:
        user_label = user.full_name
    else:
        user_label = f"id:{user.id}"

    header = f"❓ Новый вопрос от {user_label}\n\n{text}\n\n(ID:{qid})"

    try:
        sent = await context.bot.send_message(chat_id=ADMINS_CHAT_ID, text=header)
        await context.bot.send_message(
            chat_id=ADMINS_CHAT_ID,
            text="👉 Ответь на это сообщение реплаем, чтобы ответить пользователю.",
            reply_to_message_id=sent.message_id,
        )
    except Exception as e:
        print(f"Ошибка при отправке вопроса в чат админов: {e}")
        await msg.reply_text("Не удалось отправить вопрос. Попробуй позже.")
        return

    await msg.reply_text("Вопрос отправлен команде. Ответ придёт сюда.")


async def on_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg: Message = update.effective_message
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
    try:
        await context.bot.send_message(
            chat_id=user_chat_id,
            text=f"💬 Ответ от команды:\n\n{msg.text}",
        )
        await mark_answered(qid)
        await msg.reply_text(f"✅ Ответ отправлен пользователю (вопрос ID:{qid}).")
    except Exception as e:
        await msg.reply_text(f"❌ Ошибка при отправке ответа: {e}")


# ===== Main =====

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("chatid", cmd_chatid))
    app.add_handler(
        MessageHandler(filters.ChatType.PRIVATE &
                       filters.TEXT, on_user_message)
    )
    app.add_handler(
        MessageHandler(filters.ChatType.GROUPS & filters.TEXT, on_admin_reply)
    )

    print("Bot is running… Press Ctrl+C to stop.")
    app.run_polling()
