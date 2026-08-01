from datetime import date
from typing import Any

SUMMARY_COLUMNS = (
    "day,sleep_score,readiness_score,activity_score,"
    "total_sleep_seconds,average_hrv,resting_hr,"
    "temperature_deviation,steps,active_calories"
)


def fetch_summary_row(
    client: Any,
    day: date | None = None,
) -> dict[str, Any]:
    """Fetch one row without retrieving the stored raw API payloads."""
    query = client.table("oura_daily").select(SUMMARY_COLUMNS)

    if day is None:
        query = query.order("day", desc=True).limit(1)
    else:
        query = query.eq("day", day.isoformat()).limit(1)

    result = query.execute()
    if not result.data:
        target = day.isoformat() if day else "the latest day"
        raise LookupError(f"No Oura data found for {target}.")
    return result.data[0]


def format_duration(seconds: int | float) -> str:
    total_minutes = round(seconds / 60)
    hours, minutes = divmod(total_minutes, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def format_number(value: int | float) -> str:
    number = float(value)
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.1f}"


def generate_summary(row: dict[str, Any]) -> str:
    """Turn one oura_daily row into a concise, post-ready summary."""
    day = date.fromisoformat(row["day"])
    lines = [f"Oura Daily • {day.strftime('%b')} {day.day}, {day.year}"]

    scores = []
    for label, field in (
        ("Sleep", "sleep_score"),
        ("Readiness", "readiness_score"),
        ("Activity", "activity_score"),
    ):
        if row.get(field) is not None:
            scores.append(f"{label} {format_number(row[field])}")
    if scores:
        lines.append(" • ".join(scores))

    sleep_metrics = []
    if row.get("total_sleep_seconds") is not None:
        sleep_metrics.append(
            f"{format_duration(row['total_sleep_seconds'])} sleep"
        )
    if row.get("average_hrv") is not None:
        sleep_metrics.append(f"HRV {format_number(row['average_hrv'])} ms")
    if row.get("resting_hr") is not None:
        sleep_metrics.append(
            f"Resting HR {format_number(row['resting_hr'])} bpm"
        )
    if sleep_metrics:
        lines.append(" • ".join(sleep_metrics))

    activity_metrics = []
    if row.get("steps") is not None:
        activity_metrics.append(f"{format_number(row['steps'])} steps")
    if row.get("active_calories") is not None:
        activity_metrics.append(
            f"{format_number(row['active_calories'])} active cal"
        )
    if activity_metrics:
        lines.append(" • ".join(activity_metrics))

    if row.get("temperature_deviation") is not None:
        deviation = float(row["temperature_deviation"])
        rounded_deviation = round(deviation, 1)
        if rounded_deviation != 0:
            sign = "+" if rounded_deviation > 0 else ""
            lines.append(
                f"Temperature deviation {sign}{rounded_deviation:.1f}°C"
            )

    if len(lines) == 1:
        raise ValueError(f"No summary metrics available for {row['day']}.")

    return "\n".join(lines)
