import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()
BASE_DIR = Path(__file__).resolve().parent


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
SEARCH_PAGES = max(1, int(os.getenv("SEARCH_PAGES", "3")))
DETAIL_MIN_DELAY_SECONDS = float(os.getenv("DETAIL_MIN_DELAY_SECONDS", "1.5"))
DETAIL_MAX_DELAY_SECONDS = float(os.getenv("DETAIL_MAX_DELAY_SECONDS", "3.0"))
DETAIL_MAX_RETRIES = int(os.getenv("DETAIL_MAX_RETRIES", "2"))
DETAIL_RETRY_BASE_SECONDS = float(os.getenv("DETAIL_RETRY_BASE_SECONDS", "6"))
_seen_job_ids_file_raw = os.getenv("SEEN_JOB_IDS_FILE", "seen_job_ids.json").strip()
_seen_job_ids_path = Path(_seen_job_ids_file_raw)
if not _seen_job_ids_path.is_absolute():
    _seen_job_ids_path = BASE_DIR / _seen_job_ids_path
SEEN_JOB_IDS_FILE = str(_seen_job_ids_path)
SEEN_JOB_IDS_LIMIT = int(os.getenv("SEEN_JOB_IDS_LIMIT", "0"))

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
    "FastAPI Developer Fresher",
    "Junior Python Developer",
    "Junior Backend Developer Python",
    "Python Software Engineer Fresher",
    "Data Scientist Entry Level",
    "NLP Engineer Fresher",
    "Generative AI Engineer Fresher",
    "MLOps Engineer Entry Level",
    "Junior Django Developer",
    "Junior Flask Developer",
    "AI ML Engineer Entry Level",
    "Backend Engineer Entry Level",
]
