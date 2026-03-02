import json
import logging
import random
import time
from pathlib import Path

import requests

from config import (
    TELEGRAM_CHAT_IDS,
    DETAIL_MAX_DELAY_SECONDS,
    DETAIL_MAX_RETRIES,
    DETAIL_MIN_DELAY_SECONDS,
    DETAIL_RETRY_BASE_SECONDS,
    FETCH_INTERVAL_SECONDS,
    KEYWORDS,
    MATCH_THRESHOLD,
    REQUEST_TIMEOUT_SECONDS,
    SEEN_JOB_IDS_FILE,
    SEEN_JOB_IDS_LIMIT,
    SEARCH_MAX_DELAY_SECONDS,
    SEARCH_MAX_RETRIES,
    SEARCH_MIN_DELAY_SECONDS,
    SEARCH_RETRY_BASE_SECONDS,
    TELEGRAM_BOT_TOKEN,
)
from job_parser import fetch_job_description, parse_job_cards
from linkedin_fetcher import LinkedInFetcher
from resume_filter import score_job_against_resume
from telegram_sender import TelegramSender


def load_seen_job_ids(file_path: str) -> set[str]:
    store_path = Path(file_path)
    if not store_path.exists():
        return set()

    try:
        raw_data = json.loads(store_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logging.warning("Failed to read seen-job store '%s': %s", store_path, exc)
        return set()

    if not isinstance(raw_data, list):
        logging.warning("Invalid seen-job store format in '%s'; expected JSON list", store_path)
        return set()

    return {str(item).strip() for item in raw_data if str(item).strip()}


def save_seen_job_ids(file_path: str, seen_job_ids: set[str], max_items: int) -> None:
    store_path = Path(file_path)
    ids_to_store = sorted(seen_job_ids)
    if max_items > 0 and len(ids_to_store) > max_items:
        ids_to_store = ids_to_store[-max_items:]

    tmp_path = store_path.with_suffix(f"{store_path.suffix}.tmp")
    try:
        tmp_path.write_text(
            json.dumps(ids_to_store, ensure_ascii=True),
            encoding="utf-8",
        )
        tmp_path.replace(store_path)
    except OSError as exc:
        logging.warning("Failed to write seen-job store '%s': %s", store_path, exc)


def _retry_delay_seconds(
    response: requests.Response | None,
    attempt: int,
) -> float:
    if response is not None:
        retry_after_header = response.headers.get("Retry-After", "").strip()
        if retry_after_header:
            try:
                retry_after_seconds = float(retry_after_header)
                if retry_after_seconds > 0:
                    return retry_after_seconds
            except ValueError:
                pass

    jitter_seconds = random.uniform(0.3, 1.2)
    return DETAIL_RETRY_BASE_SECONDS * (2**attempt) + jitter_seconds


def fetch_job_description_with_backoff(
    session: requests.Session,
    job_link: str,
) -> str:
    max_attempts = DETAIL_MAX_RETRIES + 1

    for attempt in range(max_attempts):
        try:
            return fetch_job_description(
                session=session,
                job_link=job_link,
                timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.HTTPError as exc:
            response = exc.response
            status_code = response.status_code if response is not None else None
            if status_code == 429 and attempt < max_attempts - 1:
                delay_seconds = _retry_delay_seconds(response, attempt)
                logging.warning(
                    "LinkedIn rate limit (429) for detail page. Retrying in %.1fs "
                    "(attempt %d/%d)",
                    delay_seconds,
                    attempt + 1,
                    max_attempts,
                )
                time.sleep(delay_seconds)
                continue
            raise
        except requests.RequestException:
            if attempt < max_attempts - 1:
                delay_seconds = min(
                    DETAIL_RETRY_BASE_SECONDS * (attempt + 1),
                    15.0,
                )
                logging.warning(
                    "Transient detail-page request failure. Retrying in %.1fs "
                    "(attempt %d/%d)",
                    delay_seconds,
                    attempt + 1,
                    max_attempts,
                )
                time.sleep(delay_seconds)
                continue
            raise

    raise RuntimeError("Unreachable retry flow in fetch_job_description_with_backoff")


def run_scan_cycle(
    fetcher: LinkedInFetcher,
    sender: TelegramSender,
    session: requests.Session,
    seen_job_ids: set[str],
) -> tuple[int, int]:
    html_chunks = fetcher.fetch_first_page_html()
    jobs = parse_job_cards(html_chunks)
    unique_jobs_by_id = {job.job_id: job for job in jobs}

    logging.info(
        "Fetched %d job cards, %d unique by job_id",
        len(jobs),
        len(unique_jobs_by_id),
    )

    scanned_count = 0
    alerted_count = 0

    for job in unique_jobs_by_id.values():
        if job.job_id in seen_job_ids:
            continue

        logging.info("Processing new job_id=%s | title=%s", job.job_id, job.title or "N/A")

        try:
            job.description_text = fetch_job_description_with_backoff(session, job.job_link)
        except requests.RequestException as exc:
            logging.exception(
                "Failed to fetch detail page for job_id=%s: %s",
                job.job_id,
                exc,
            )
        else:
            score, matched_skills = score_job_against_resume(job.description_text)
            scanned_count += 1

            if score > MATCH_THRESHOLD:
                logging.info(
                    "Job passed filter: job_id=%s score=%.2f matched=%s",
                    job.job_id,
                    score,
                    matched_skills,
                )
                sender.send_job_alert(job, score, matched_skills)
                alerted_count += 1
            else:
                logging.info(
                    "Job rejected by filter: job_id=%s score=%.2f",
                    job.job_id,
                    score,
                )
        finally:
            seen_job_ids.add(job.job_id)
            delay_seconds = random.uniform(
                DETAIL_MIN_DELAY_SECONDS,
                DETAIL_MAX_DELAY_SECONDS,
            )
            logging.debug(
                "Sleeping %.2fs before next detail-page request",
                delay_seconds,
            )
            time.sleep(delay_seconds)

    return scanned_count, alerted_count


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    logging.info("Starting LinkedIn fresher job alert bot")
    logging.info("Keyword count: %d | Interval: %d seconds", len(KEYWORDS), FETCH_INTERVAL_SECONDS)
    logging.info(
        "Telegram configured: %s | chat_ids=%d",
        str(bool(TELEGRAM_BOT_TOKEN)).lower(),
        len(TELEGRAM_CHAT_IDS),
    )

    seen_job_ids = load_seen_job_ids(SEEN_JOB_IDS_FILE)
    logging.info(
        "Loaded %d seen job IDs from %s",
        len(seen_job_ids),
        SEEN_JOB_IDS_FILE,
    )
    shared_session = requests.Session()

    fetcher = LinkedInFetcher(
        keywords=KEYWORDS,
        location="India",
        min_delay_seconds=SEARCH_MIN_DELAY_SECONDS,
        max_delay_seconds=SEARCH_MAX_DELAY_SECONDS,
        max_retries=SEARCH_MAX_RETRIES,
        retry_base_seconds=SEARCH_RETRY_BASE_SECONDS,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        session=shared_session,
    )
    sender = TelegramSender(
        bot_token=TELEGRAM_BOT_TOKEN,
        chat_ids=TELEGRAM_CHAT_IDS,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        session=shared_session,
    )

    try:
        while True:
            cycle_start = time.time()
            seen_count_before_cycle = len(seen_job_ids)
            logging.info("Starting new scan cycle")

            try:
                scanned_count, alerted_count = run_scan_cycle(
                    fetcher=fetcher,
                    sender=sender,
                    session=shared_session,
                    seen_job_ids=seen_job_ids,
                )
                logging.info(
                    "Cycle complete | scanned=%d | alerted=%d | seen_total=%d",
                    scanned_count,
                    alerted_count,
                    len(seen_job_ids),
                )
            except Exception as exc:
                logging.exception("Unexpected error in scan cycle: %s", exc)
            finally:
                if len(seen_job_ids) != seen_count_before_cycle:
                    save_seen_job_ids(
                        file_path=SEEN_JOB_IDS_FILE,
                        seen_job_ids=seen_job_ids,
                        max_items=SEEN_JOB_IDS_LIMIT,
                    )
                    logging.info(
                        "Persisted seen-job store: %d IDs",
                        len(seen_job_ids),
                    )

            elapsed = time.time() - cycle_start
            sleep_seconds = max(0, FETCH_INTERVAL_SECONDS - elapsed)
            logging.info("Sleeping for %.1f seconds before next cycle", sleep_seconds)
            time.sleep(sleep_seconds)
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")


if __name__ == "__main__":
    main()
