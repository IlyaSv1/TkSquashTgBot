# database/db.py
import aiosqlite
import os
from typing import Optional

DB_PATH = os.environ.get("BOT_DB_PATH", "qa_bot.sqlite3")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS qmap (
                qid TEXT PRIMARY KEY,
                user_chat_id INTEGER NOT NULL,
                user_message_id INTEGER,
                question_text TEXT,
                question_file_id TEXT,
                answer_message_id INTEGER,
                answer_file_id TEXT,
                answered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_mapping(qid: str, user_chat_id: int, question_text: str, question_file_id: Optional[str] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO qmap(qid, user_chat_id, question_text, question_file_id) VALUES (?, ?, ?, ?)",
            (qid, user_chat_id, question_text, question_file_id)
        )
        await db.commit()


async def get_user_by_qid(qid: str, include_answered: bool = False):
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
            SELECT user_chat_id, question_text, answer_message_id, question_file_id, answer_type
            FROM qmap
            WHERE qid=?
        """
        if not include_answered:
            query += " AND answered=0"
        async with db.execute(query, (qid,)) as cur:
            return await cur.fetchone()


async def mark_answered(qid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE qmap SET answered=1 WHERE qid=?", (qid,))
        await db.commit()


async def save_answer_message_id(qid: str, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE qmap SET answer_message_id=? WHERE qid=?", (message_id, qid))
        await db.commit()


async def save_answer_file_id(qid: str, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE qmap SET answer_file_id=? WHERE qid=?", (file_id, qid))
        await db.commit()


async def save_answer_type(qid: str, answer_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE qmap SET answer_type=? WHERE qid=?",
            (answer_type, qid)
        )
        await db.commit()
