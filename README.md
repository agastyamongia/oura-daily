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
