import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS_CHAT_ID = int(os.getenv("ADMINS_CHAT_ID"))
