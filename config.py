import json
import os

from dotenv import load_dotenv


load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "<your_token_here>")

_chat_ids_env = os.getenv("CHAT_IDS", "<your_chat_id>")
try:
    _chat_ids_parsed = json.loads(_chat_ids_env)
    if isinstance(_chat_ids_parsed, list):
        CHAT_IDS = [str(chat_id).strip() for chat_id in _chat_ids_parsed if str(chat_id).strip()]
    else:
        CHAT_IDS = [chat_id.strip() for chat_id in _chat_ids_env.split(",") if chat_id.strip()]
except json.JSONDecodeError:
    CHAT_IDS = [chat_id.strip() for chat_id in _chat_ids_env.split(",") if chat_id.strip()]

FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", "1200"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.2"))

KEYWORDS = [
    "Python Developer Entry Level",
    "Backend Developer Python Fresher",
    "Django Developer Entry Level",
    "Flask Developer Fresher",
    "AI Engineer Entry Level",
    "Machine Learning Engineer Fresher",
    "LLM Engineer Entry Level",
    "Associate Software Engineer",
    "Software Engineer I",
    "Graduate Engineer Trainee Software",
]
