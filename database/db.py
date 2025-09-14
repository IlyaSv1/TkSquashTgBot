import aiosqlite
import os
from typing import Optional, Tuple

DB_PATH = os.environ.get("BOT_DB_PATH", "qa_bot.sqlite3")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS qmap (
                qid TEXT PRIMARY KEY,
                user_chat_id INTEGER NOT NULL,
                user_message_id INTEGER,
                question_text TEXT,
                answer_message_id INTEGER,   -- новое поле для ID ответа
                answered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_mapping(qid: str, user_chat_id: int, user_message_id: Optional[int], question_text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO qmap(qid, user_chat_id, user_message_id, question_text) VALUES (?, ?, ?, ?)",
            (qid, user_chat_id, user_message_id, question_text),
        )
        await db.commit()


async def get_user_by_qid(qid: str, include_answered=False):
    query = "SELECT user_chat_id, question_text, answer_message_id FROM qmap WHERE qid=?"
    if not include_answered:
        query += " AND answered=0"
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(query, (qid,)) as cur:
            return await cur.fetchone()


async def mark_answered(qid: str, answer_message_id: Optional[int] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if answer_message_id:
            await db.execute(
                "UPDATE qmap SET answered=1, answer_message_id=? WHERE qid=?",
                (answer_message_id, qid),
            )
        else:
            await db.execute("UPDATE qmap SET answered=1 WHERE qid=?", (qid,))
        await db.commit()


async def save_answer_message_id(qid: str, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE qmap SET answer_message_id=? WHERE qid=?",
            (message_id, qid)
        )
        await db.commit()
