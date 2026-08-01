import argparse
import os
from datetime import date

from dotenv import load_dotenv
from supabase import create_client

from daily_summary import fetch_summary_row, generate_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a post-ready summary from Supabase Oura data."
    )
    parser.add_argument(
        "--day",
        type=date.fromisoformat,
        help="Day to summarize in YYYY-MM-DD format (default: latest row).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv()
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )
    row = fetch_summary_row(client, args.day)
    print(generate_summary(row))


if __name__ == "__main__":
    main()
