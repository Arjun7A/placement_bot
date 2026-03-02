import hashlib
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class JobPosting:
    job_id: str
    title: str
    company: str
    location: str
    job_link: str
    description_text: str = ""


def _clean_text(raw_text: str) -> str:
    return re.sub(r"\s+", " ", raw_text).strip()


def _extract_job_id(card: BeautifulSoup, job_link: str) -> str:
    urn_candidates = [
        card.get("data-entity-urn", ""),
        card.get("data-id", ""),
    ]

    for candidate in urn_candidates:
        match = re.search(r"(\d{6,})", candidate or "")
        if match:
            return match.group(1)

    link_match = re.search(r"/view/(\d{6,})", job_link)
    if link_match:
        return link_match.group(1)

    parsed_url = urlparse(job_link)
    current_job_id = parse_qs(parsed_url.query).get("currentJobId")
    if current_job_id:
        return current_job_id[0]

    return hashlib.sha1(job_link.encode("utf-8")).hexdigest()[:16]


def parse_job_cards(html_chunks: list[str]) -> list[JobPosting]:
    parsed_jobs: list[JobPosting] = []

    for html in html_chunks:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("li")

        for card in cards:
            title_node = card.select_one("h3.base-search-card__title") or card.select_one(
                "h3"
            )
            company_node = card.select_one("h4.base-search-card__subtitle") or card.select_one(
                "h4"
            )
            location_node = card.select_one(
                "span.job-search-card__location"
            ) or card.select_one("span")
            link_node = card.select_one("a.base-card__full-link") or card.select_one("a")

            if not link_node:
                continue

            job_link = (link_node.get("href") or "").strip()
            if not job_link:
                continue
            job_link = urljoin("https://www.linkedin.com", job_link)

            job = JobPosting(
                job_id=_extract_job_id(card, job_link),
                title=_clean_text(title_node.get_text(" ", strip=True) if title_node else ""),
                company=_clean_text(
                    company_node.get_text(" ", strip=True) if company_node else ""
                ),
                location=_clean_text(
                    location_node.get_text(" ", strip=True) if location_node else ""
                ),
                job_link=job_link,
            )
            parsed_jobs.append(job)

    return parsed_jobs


def fetch_job_description(
    session: requests.Session, job_link: str, timeout_seconds: int = 20
) -> str:
    response = session.get(job_link, timeout=timeout_seconds)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    selectors = [
        "div.show-more-less-html__markup",
        "div.description__text",
        "section.show-more-less-html",
        "div.jobs-box__html-content",
    ]

    description_text = ""
    for selector in selectors:
        description_node = soup.select_one(selector)
        if description_node:
            description_text = description_node.get_text(" ", strip=True)
            if description_text:
                break

    if not description_text:
        description_text = soup.get_text(" ", strip=True)

    return _clean_text(description_text)
