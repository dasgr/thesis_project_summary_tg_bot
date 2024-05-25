from telethon.sync import TelegramClient
from utils.config import API_ID, API_HASH

# Generate a new session file
client = TelegramClient('new_heroku_session_for_bot', API_ID, API_HASH)
client.start()

print("Session file created successfully")
client.disconnect()