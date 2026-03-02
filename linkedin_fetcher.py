import logging
import random
import time
from typing import Iterable, List

import requests


LINKEDIN_SEARCH_ENDPOINT = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
)


class LinkedInFetcher:
    def __init__(
        self,
        keywords: Iterable[str],
        location: str = "India",
        min_delay_seconds: float = 1.0,
        max_delay_seconds: float = 2.0,
        max_retries: int = 1,
        retry_base_seconds: float = 6.0,
        timeout_seconds: int = 20,
        session: requests.Session | None = None,
    ) -> None:
        self.keywords = list(keywords)
        self.location = location
        self.min_delay_seconds = min_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.max_retries = max_retries
        self.retry_base_seconds = retry_base_seconds
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def _build_params(self, keyword: str) -> dict[str, str]:
        return {
            "keywords": keyword,
            "location": self.location,
            "f_TPR": "r86400",
            "f_E": "2",
            "start": "0",
        }

    def _retry_delay_seconds(
        self,
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

        return self.retry_base_seconds * (2**attempt) + random.uniform(0.3, 1.2)

    def _fetch_keyword_html(self, keyword: str) -> str:
        max_attempts = self.max_retries + 1
        for attempt in range(max_attempts):
            try:
                response = self.session.get(
                    LINKEDIN_SEARCH_ENDPOINT,
                    params=self._build_params(keyword),
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                return response.text.strip()
            except requests.HTTPError as exc:
                response = exc.response
                status_code = response.status_code if response is not None else None
                if status_code == 429 and attempt < max_attempts - 1:
                    delay_seconds = self._retry_delay_seconds(response, attempt)
                    logging.warning(
                        "LinkedIn search rate limit (429) for keyword '%s'. "
                        "Retrying in %.1fs (attempt %d/%d)",
                        keyword,
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
                        self.retry_base_seconds * (attempt + 1),
                        20.0,
                    ) + random.uniform(0.2, 1.0)
                    logging.warning(
                        "Transient search request failure for keyword '%s'. "
                        "Retrying in %.1fs (attempt %d/%d)",
                        keyword,
                        delay_seconds,
                        attempt + 1,
                        max_attempts,
                    )
                    time.sleep(delay_seconds)
                    continue
                raise

        return ""

    def fetch_first_page_html(self) -> List[str]:
        html_chunks: List[str] = []

        for index, keyword in enumerate(self.keywords):
            logging.info("Fetching jobs for keyword: %s", keyword)
            try:
                html = self._fetch_keyword_html(keyword)
                if html:
                    html_chunks.append(html)
                    logging.info("Fetched HTML chunk for keyword: %s", keyword)
                else:
                    logging.warning("No jobs returned for keyword: %s", keyword)
            except requests.RequestException as exc:
                logging.exception("Failed fetch for keyword '%s': %s", keyword, exc)

            if index < len(self.keywords) - 1:
                delay_seconds = random.uniform(
                    self.min_delay_seconds, self.max_delay_seconds
                )
                logging.debug("Sleeping %.2f seconds before next keyword", delay_seconds)
                time.sleep(delay_seconds)

        return html_chunks
