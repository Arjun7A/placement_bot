# LinkedIn Fresher Job Alert Bot

A headless Python bot that fetches same-day entry-level jobs from LinkedIn guest search, filters them against resume skills, and sends matching alerts to Telegram.

## Features

- Uses LinkedIn guest endpoint only (no login, no Selenium).
- Fetches first page per keyword for the last 24 hours and entry-level (`f_TPR=r86400`, `f_E=2`).
- Extracts `job_id`, `title`, `company`, `location`, `job_link`, and full job description.
- Scores each job using resume skill matches.
- Sends alerts only when `score > 0.2`.
- Runs continuously every 20 minutes.
- Deduplicates jobs in-memory by `job_id`.

## Project Structure

```
job_alert_bot/
├── main.py
├── linkedin_fetcher.py
├── job_parser.py
├── resume_filter.py
├── telegram_sender.py
├── config.py
├── .env.example
├── requirements.txt
└── README.md
```

## Install

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

`config.py` loads environment variables using `python-dotenv`.

Create a `.env` file in `job_alert_bot/`:

```dotenv
TELEGRAM_BOT_TOKEN=123456789:AA...
CHAT_IDS=["123456789","987654321"]
FETCH_INTERVAL_SECONDS=1200
MATCH_THRESHOLD=0.2
REQUEST_TIMEOUT_SECONDS=20
SEARCH_MIN_DELAY_SECONDS=2.5
SEARCH_MAX_DELAY_SECONDS=4.0
SEARCH_MAX_RETRIES=2
SEARCH_RETRY_BASE_SECONDS=8
DETAIL_MIN_DELAY_SECONDS=1.5
DETAIL_MAX_DELAY_SECONDS=3.0
DETAIL_MAX_RETRIES=2
DETAIL_RETRY_BASE_SECONDS=6
```

Notes:
- `CHAT_IDS` can be JSON list (`["123","456"]`) or comma-separated (`123,456`).
- `FETCH_INTERVAL_SECONDS=1200` means 20 minutes.
- `TELEGRAM_BOT_TOKEN` should be set without surrounding spaces and the service must be redeployed after changing vars.
- Search API calls are throttled with randomized delays and retries (`SEARCH_*` settings).
- Detail-page fetch requests are throttled using `DETAIL_MIN_DELAY_SECONDS` and `DETAIL_MAX_DELAY_SECONDS`.
- If LinkedIn returns `429`, retry backoff is controlled by `DETAIL_MAX_RETRIES` and `DETAIL_RETRY_BASE_SECONDS`.
- If env vars are missing, placeholders in `config.py` are used.

## Get Your Telegram Chat ID (`getUpdates`)

1. Create a bot with `@BotFather` and copy the bot token.
2. Send at least one message to your bot from your Telegram account.
3. Open:

```text
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```

4. Find `chat.id` in the JSON response.
5. Put that value in `CHAT_IDS`.

## Run

From `job_alert_bot/`:

```bash
python main.py
```

The bot will:
- fetch first-page jobs for all configured keywords,
- parse and score jobs,
- send Telegram alerts for matches,
- sleep for 20 minutes and repeat.

## LinkedIn Query Configuration

Current keyword set:

- Python Developer Entry Level
- Backend Developer Python Fresher
- Django Developer Entry Level
- Flask Developer Fresher
- AI Engineer Entry Level
- Machine Learning Engineer Fresher
- LLM Engineer Entry Level
- Associate Software Engineer
- Software Engineer I
- Graduate Engineer Trainee Software

Location is fixed to `India`.

## Resume Filter Logic

Defined in `resume_filter.py`:

- Resume skills are stored in `resume_data`.
- JD text is lowercased.
- Match score = `matched_skill_count / total_skills`.
- Alert is sent only if score is strictly greater than `0.2`.

## Safety and Compliance

- No LinkedIn authentication is used.
- No Selenium/browser automation is used.
- Only guest endpoint is used:
  `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search`
- Only first page is fetched for each keyword.
- 1-2 second delay is applied between keyword requests.
- detail-page requests are rate-limited with randomized delays.
- automatic retry with backoff is applied for temporary failures and `429` responses.
- Do not reduce delays aggressively to avoid rate-limits or temporary blocking.

## Add More Keywords Later

Edit `KEYWORDS` in `config.py` and append more role strings. Keep the delay and first-page-only pattern unchanged for safe usage.

## Expected Throughput

Real-world notification volume depends on market activity and filter strictness. With the current keywords and threshold, this setup is designed to support a target of roughly 25-40 relevant fresher alerts per day when such postings are available.
