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
        timeout_seconds: int = 20,
        session: requests.Session | None = None,
    ) -> None:
        self.keywords = list(keywords)
        self.location = location
        self.min_delay_seconds = min_delay_seconds
        self.max_delay_seconds = max_delay_seconds
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

    def fetch_first_page_html(self) -> List[str]:
        html_chunks: List[str] = []

        for index, keyword in enumerate(self.keywords):
            logging.info("Fetching jobs for keyword: %s", keyword)
            try:
                response = self.session.get(
                    LINKEDIN_SEARCH_ENDPOINT,
                    params=self._build_params(keyword),
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                html = response.text.strip()
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
