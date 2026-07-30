import os
from collections import defaultdict
from datetime import date

import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

OURA_ACCESS_TOKEN = os.environ["OURA_ACCESS_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

# Use a date earlier than when you first started using Oura.
START_DATE = os.getenv("OURA_HISTORY_START_DATE", "2020-01-01")
END_DATE = date.today().isoformat()

OURA_BASE_URL = "https://api.ouraring.com/v2/usercollection"

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)

headers = {
    "Authorization": f"Bearer {OURA_ACCESS_TOKEN}",
}


def fetch_all(endpoint: str) -> list[dict]:
    """Fetch every page of records for one Oura endpoint."""
    records: list[dict] = []
    next_token: str | None = None

    while True:
        params = {
            "start_date": START_DATE,
            "end_date": END_DATE,
        }

        if next_token:
            params["next_token"] = next_token

        response = requests.get(
            f"{OURA_BASE_URL}/{endpoint}",
            headers=headers,
            params=params,
            timeout=60,
        )

        if not response.ok:
            raise RuntimeError(
                f"{endpoint} failed ({response.status_code}): "
                f"{response.text}"
            )

        payload = response.json()
        batch = payload.get("data", [])
        records.extend(batch)

        print(
            f"{endpoint}: fetched {len(batch)} records "
            f"({len(records)} total)"
        )

        next_token = payload.get("next_token")

        if not next_token:
            break

    return records


def index_by_day(records: list[dict]) -> dict[str, dict]:
    return {
        record["day"]: record
        for record in records
        if record.get("day")
    }


def index_sleep_by_day(
    records: list[dict],
) -> dict[str, list[dict]]:
    indexed: dict[str, list[dict]] = defaultdict(list)

    for record in records:
        day = record.get("day")

        if day:
            indexed[day].append(record)

    return indexed


def choose_main_sleep(
    sleeps: list[dict],
) -> dict | None:
    """
    Prefer the longest sleep period for a day.

    This avoids accidentally using a short nap as the day's
    primary sleep record.
    """
    if not sleeps:
        return None

    return max(
        sleeps,
        key=lambda item: item.get("total_sleep_duration", 0) or 0,
    )


def build_rows(
    daily_sleep: list[dict],
    daily_readiness: list[dict],
    daily_activity: list[dict],
    sleep_periods: list[dict],
) -> list[dict]:
    sleep_scores = index_by_day(daily_sleep)
    readiness_scores = index_by_day(daily_readiness)
    activity_scores = index_by_day(daily_activity)
    sleep_by_day = index_sleep_by_day(sleep_periods)

    all_days = sorted(
        set(sleep_scores)
        | set(readiness_scores)
        | set(activity_scores)
        | set(sleep_by_day)
    )

    rows = []

    for day in all_days:
        daily_sleep_record = sleep_scores.get(day)
        readiness_record = readiness_scores.get(day)
        activity_record = activity_scores.get(day)
        main_sleep = choose_main_sleep(sleep_by_day.get(day, []))

        row = {
            "day": day,

            "sleep_score": (
                daily_sleep_record.get("score")
                if daily_sleep_record
                else None
            ),
            "readiness_score": (
                readiness_record.get("score")
                if readiness_record
                else None
            ),
            "activity_score": (
                activity_record.get("score")
                if activity_record
                else None
            ),

            "total_sleep_seconds": (
                main_sleep.get("total_sleep_duration")
                if main_sleep
                else None
            ),
            "time_in_bed_seconds": (
                main_sleep.get("time_in_bed")
                if main_sleep
                else None
            ),
            "deep_sleep_seconds": (
                main_sleep.get("deep_sleep_duration")
                if main_sleep
                else None
            ),
            "rem_sleep_seconds": (
                main_sleep.get("rem_sleep_duration")
                if main_sleep
                else None
            ),
            "average_hrv": (
                main_sleep.get("average_hrv")
                if main_sleep
                else None
            ),
            "resting_hr": (
                main_sleep.get("lowest_heart_rate")
                if main_sleep
                else None
            ),
            "temperature_deviation": (
                readiness_record
                .get("contributors", {})
                .get("body_temperature")
                if readiness_record
                else None
            ),
            "steps": (
                activity_record.get("steps")
                if activity_record
                else None
            ),
            "active_calories": (
                activity_record.get("active_calories")
                if activity_record
                else None
            ),

            "sleep_raw": {
                "daily": daily_sleep_record,
                "periods": sleep_by_day.get(day, []),
            },
            "readiness_raw": readiness_record,
            "activity_raw": activity_record,
        }

        rows.append(row)

    return rows


def upsert_rows(
    rows: list[dict],
    batch_size: int = 100,
) -> None:
    for start in range(0, len(rows), batch_size):
        batch = rows[start:start + batch_size]

        (
            supabase
            .table("oura_daily")
            .upsert(batch, on_conflict="day")
            .execute()
        )

        print(
            f"Saved rows {start + 1}–"
            f"{start + len(batch)}"
        )


def main() -> None:
    print(f"Importing Oura history from {START_DATE} to {END_DATE}")

    daily_sleep = fetch_all("daily_sleep")
    daily_readiness = fetch_all("daily_readiness")
    daily_activity = fetch_all("daily_activity")
    sleep_periods = fetch_all("sleep")

    rows = build_rows(
        daily_sleep=daily_sleep,
        daily_readiness=daily_readiness,
        daily_activity=daily_activity,
        sleep_periods=sleep_periods,
    )

    print(f"\nPrepared {len(rows)} daily rows.")

    upsert_rows(rows)

    print("\nHistorical Oura import completed successfully.")


if __name__ == "__main__":
    main()