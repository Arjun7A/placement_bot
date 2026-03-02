import logging
from typing import Iterable

import requests

from job_parser import JobPosting


class TelegramSender:
    def __init__(
        self,
        bot_token: str,
        chat_ids: Iterable[str],
        timeout_seconds: int = 20,
        session: requests.Session | None = None,
    ) -> None:
        self.bot_token = bot_token
        self.chat_ids = [str(chat_id).strip() for chat_id in chat_ids if str(chat_id).strip()]
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    @staticmethod
    def _build_message(job: JobPosting, score: float, matched_skills: list[str]) -> str:
        matched_skills_text = ", ".join(matched_skills) if matched_skills else "None"
        return (
            "🔥 NEW FRESHER JOB (Posted Today)\n\n"
            f"🏢 Company: {job.company or 'N/A'}\n"
            f"💼 Role: {job.title or 'N/A'}\n"
            f"📍 Location: {job.location or 'N/A'}\n\n"
            f"Match Score: {score:.2f}\n"
            f"Matched Skills: {matched_skills_text}\n\n"
            f"🔗 Apply: {job.job_link}"
        )

    def send_job_alert(self, job: JobPosting, score: float, matched_skills: list[str]) -> None:
        if not self.chat_ids:
            logging.warning("No chat IDs configured; skipping Telegram send")
            return

        if not self.bot_token or self.bot_token == "<your_token_here>":
            logging.warning("Telegram bot token is not configured; skipping Telegram send")
            return

        message = self._build_message(job, score, matched_skills)

        for chat_id in self.chat_ids:
            payload = {
                "chat_id": chat_id,
                "text": message,
                "disable_web_page_preview": True,
            }
            try:
                response = self.session.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                logging.info(
                    "Telegram alert sent to chat_id=%s for job_id=%s",
                    chat_id,
                    job.job_id,
                )
            except requests.RequestException as exc:
                logging.exception(
                    "Failed to send Telegram alert to chat_id=%s for job_id=%s: %s",
                    chat_id,
                    job.job_id,
                    exc,
                )
