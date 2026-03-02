import os

from dotenv import load_dotenv


load_dotenv()


def _clean_env_value(value: str) -> str:
    return value.strip().strip('"').strip("'")


TELEGRAM_BOT_TOKEN = _clean_env_value(
    os.getenv("TELEGRAM_BOT_TOKEN", "")
)

def get_telegram_chat_ids() -> list[str]:
    raw_value = os.getenv("TELEGRAM_CHAT_IDS", "")
    chat_ids = [
        chat_id.strip()
        for chat_id in raw_value.split(",")
        if chat_id.strip()
    ]
    return chat_ids


TELEGRAM_CHAT_IDS = get_telegram_chat_ids()

# Backward compatibility for existing imports.
CHAT_IDS = TELEGRAM_CHAT_IDS

FETCH_INTERVAL_SECONDS = int(os.getenv("FETCH_INTERVAL_SECONDS", "1200"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.2"))
SEARCH_MIN_DELAY_SECONDS = float(os.getenv("SEARCH_MIN_DELAY_SECONDS", "2.5"))
SEARCH_MAX_DELAY_SECONDS = float(os.getenv("SEARCH_MAX_DELAY_SECONDS", "4.0"))
SEARCH_MAX_RETRIES = int(os.getenv("SEARCH_MAX_RETRIES", "2"))
SEARCH_RETRY_BASE_SECONDS = float(os.getenv("SEARCH_RETRY_BASE_SECONDS", "8"))
DETAIL_MIN_DELAY_SECONDS = float(os.getenv("DETAIL_MIN_DELAY_SECONDS", "1.5"))
DETAIL_MAX_DELAY_SECONDS = float(os.getenv("DETAIL_MAX_DELAY_SECONDS", "3.0"))
DETAIL_MAX_RETRIES = int(os.getenv("DETAIL_MAX_RETRIES", "2"))
DETAIL_RETRY_BASE_SECONDS = float(os.getenv("DETAIL_RETRY_BASE_SECONDS", "6"))

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
