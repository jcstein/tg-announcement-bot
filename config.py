import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '')  # Empty string as default
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")
INITIAL_ADMIN_IDS = [int(id) for id in os.getenv('INITIAL_ADMIN_IDS', '').split(',') if id]
