# Oura Daily

A personal application that retrieves Oura health and wellness data, stores it
in Supabase for historical analysis, and will create daily summaries for
posting to Threads.

## Local setup

Create a `.env` file (it is ignored by Git) with:

```dotenv
OURA_ACCESS_TOKEN=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

Install dependencies in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Import and sync

Run the historical import once:

```bash
OURA_HISTORY_START_DATE=2026-01-01 python backfill_oura.py
```

Run the daily sync:

```bash
python sync_oura.py
```

The daily job fetches and upserts an inclusive three-day window. Re-fetching
recent days accounts for late Oura calculations, updated scores, and missed
automation runs. Supabase must have a unique constraint on `oura_daily.day`.

## Generate a daily summary

Generate a post-ready summary from the newest stored row:

```bash
python generate_summary.py
```

Or generate one for a specific date:

```bash
python generate_summary.py --day 2026-07-30
```

Missing values are omitted, so an incomplete current-day activity record does
not produce placeholder text. This command only prints the summary; it does
not publish anything.

## Publish to Threads

Create a Threads app in the Meta developer dashboard and authorize a Threads
user with at least these scopes:

- `threads_basic`
- `threads_content_publish`

Add its long-lived user token to `.env`:

```dotenv
THREADS_ACCESS_TOKEN=...
```

Preview the exact post without publishing:

```bash
python publish_summary.py
python publish_summary.py --day 2026-07-30
```

Publishing requires an explicit flag:

```bash
python publish_summary.py --day 2026-07-30 --publish
```

The publisher creates a text container and then publishes that container using
Meta's official two-step Threads API flow. Keep the access token out of Git;
for automation, store it as a GitHub Actions secret named
`THREADS_ACCESS_TOKEN`.

## GitHub Actions

The `Daily Oura sync` workflow runs every day at 15:00 UTC and can also be
started manually. Add these repository secrets before running it:

- `OURA_ACCESS_TOKEN`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

The schedule corresponds to 8:00 AM Pacific during daylight saving time and
7:00 AM Pacific during standard time because GitHub cron schedules use UTC.

## Tests

```bash
python -m unittest discover -s tests
```
029YiKc4JxNth3WC
