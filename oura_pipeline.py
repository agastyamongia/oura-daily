from collections import defaultdict
from datetime import date
from typing import Any

import requests

OURA_BASE_URL = "https://api.ouraring.com/v2/usercollection"
OURA_ENDPOINTS = (
    "daily_sleep",
    "daily_readiness",
    "daily_activity",
    "sleep",
)


def fetch_all(
    endpoint: str,
    start_date: date,
    end_date: date,
    access_token: str,
) -> list[dict[str, Any]]:
    """Fetch every page of records for one Oura endpoint."""
    records: list[dict[str, Any]] = []
    next_token: str | None = None

    while True:
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        if next_token:
            params["next_token"] = next_token

        response = requests.get(
            f"{OURA_BASE_URL}/{endpoint}",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=60,
        )
        if not response.ok:
            raise RuntimeError(
                f"{endpoint} failed ({response.status_code}): {response.text}"
            )

        payload = response.json()
        batch = payload.get("data", [])
        records.extend(batch)
        print(f"{endpoint}: fetched {len(batch)} records ({len(records)} total)")

        next_token = payload.get("next_token")
        if not next_token:
            return records


def index_by_day(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {record["day"]: record for record in records if record.get("day")}


def index_sleep_by_day(
    records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    indexed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        day = record.get("day")
        if day:
            indexed[day].append(record)
    return indexed


def choose_main_sleep(
    sleeps: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Use the longest sleep period so a short nap is not selected."""
    if not sleeps:
        return None
    return max(
        sleeps,
        key=lambda item: item.get("total_sleep_duration", 0) or 0,
    )


def build_rows(
    daily_sleep: list[dict[str, Any]],
    daily_readiness: list[dict[str, Any]],
    daily_activity: list[dict[str, Any]],
    sleep_periods: list[dict[str, Any]],
) -> list[dict[str, Any]]:
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

        rows.append(
            {
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
                    main_sleep.get("time_in_bed") if main_sleep else None
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
                    main_sleep.get("average_hrv") if main_sleep else None
                ),
                "resting_hr": (
                    main_sleep.get("lowest_heart_rate")
                    if main_sleep
                    else None
                ),
                "temperature_deviation": (
                    readiness_record.get("temperature_deviation")
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
        )
    return rows


def upsert_rows(
    client: Any,
    rows: list[dict[str, Any]],
    batch_size: int = 100,
) -> None:
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        client.table("oura_daily").upsert(
            batch,
            on_conflict="day",
        ).execute()
        print(f"Saved rows {start + 1}–{start + len(batch)}")


def sync_range(
    start_date: date,
    end_date: date,
    access_token: str,
    client: Any,
) -> list[dict[str, Any]]:
    datasets = {
        endpoint: fetch_all(endpoint, start_date, end_date, access_token)
        for endpoint in OURA_ENDPOINTS
    }
    rows = build_rows(
        daily_sleep=datasets["daily_sleep"],
        daily_readiness=datasets["daily_readiness"],
        daily_activity=datasets["daily_activity"],
        sleep_periods=datasets["sleep"],
    )
    upsert_rows(client, rows)
    return rows
