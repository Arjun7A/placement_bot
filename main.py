import logging
import time

import requests

from config import (
    CHAT_IDS,
    FETCH_INTERVAL_SECONDS,
    KEYWORDS,
    MATCH_THRESHOLD,
    REQUEST_TIMEOUT_SECONDS,
    TELEGRAM_BOT_TOKEN,
)
from job_parser import fetch_job_description, parse_job_cards
from linkedin_fetcher import LinkedInFetcher
from resume_filter import score_job_against_resume
from telegram_sender import TelegramSender


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
            job.description_text = fetch_job_description(
                session,
                job.job_link,
                timeout_seconds=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            logging.exception(
                "Failed to fetch detail page for job_id=%s: %s",
                job.job_id,
                exc,
            )
            continue

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

        seen_job_ids.add(job.job_id)

    return scanned_count, alerted_count


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    logging.info("Starting LinkedIn fresher job alert bot")
    logging.info("Keyword count: %d | Interval: %d seconds", len(KEYWORDS), FETCH_INTERVAL_SECONDS)

    seen_job_ids: set[str] = set()
    shared_session = requests.Session()

    fetcher = LinkedInFetcher(
        keywords=KEYWORDS,
        location="India",
        min_delay_seconds=1.0,
        max_delay_seconds=2.0,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        session=shared_session,
    )
    sender = TelegramSender(
        bot_token=TELEGRAM_BOT_TOKEN,
        chat_ids=CHAT_IDS,
        timeout_seconds=REQUEST_TIMEOUT_SECONDS,
        session=shared_session,
    )

    try:
        while True:
            cycle_start = time.time()
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

            elapsed = time.time() - cycle_start
            sleep_seconds = max(0, FETCH_INTERVAL_SECONDS - elapsed)
            logging.info("Sleeping for %.1f seconds before next cycle", sleep_seconds)
            time.sleep(sleep_seconds)
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")


if __name__ == "__main__":
    main()
