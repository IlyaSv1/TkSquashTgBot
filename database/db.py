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
                answered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
            "SELECT user_chat_id FROM qmap WHERE qid=? AND answered=0", (qid,)
        ) as cur:
            return await cur.fetchone()


async def mark_answered(qid: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE qmap SET answered=1 WHERE qid=?", (qid,))
        await db.commit()
