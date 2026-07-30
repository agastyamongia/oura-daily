import os
from datetime import date, timedelta

from dotenv import load_dotenv
from supabase import create_client

from oura_pipeline import sync_range

SYNC_DAYS = 3


def sync_window(today: date) -> tuple[date, date]:
    """Return an inclusive rolling window ending today."""
    return today - timedelta(days=SYNC_DAYS - 1), today


def main() -> None:
    load_dotenv()
    start_date, end_date = sync_window(date.today())
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )

    print(f"Syncing Oura data from {start_date} to {end_date}")
    rows = sync_range(
        start_date=start_date,
        end_date=end_date,
        access_token=os.environ["OURA_ACCESS_TOKEN"],
        client=client,
    )
    print(f"\nDaily Oura sync completed successfully ({len(rows)} rows).")


if __name__ == "__main__":
    main()
