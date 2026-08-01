import argparse
import os
from datetime import date

from dotenv import load_dotenv
from supabase import create_client

from daily_summary import fetch_summary_row, generate_summary
from threads_client import ThreadsClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or publish a Supabase Oura summary to Threads."
    )
    parser.add_argument(
        "--day",
        type=date.fromisoformat,
        help="Day to summarize in YYYY-MM-DD format (default: latest row).",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish the summary to Threads. Without this flag, preview only.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv()
    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )
    summary = generate_summary(fetch_summary_row(supabase, args.day))

    print(summary)
    if not args.publish:
        print("\nPreview only. Add --publish to post this summary to Threads.")
        return

    access_token = os.getenv("THREADS_ACCESS_TOKEN")
    if not access_token:
        raise RuntimeError(
            "THREADS_ACCESS_TOKEN is required when --publish is used."
        )

    thread_id = ThreadsClient(access_token).publish_text(summary)
    print(f"\nPublished to Threads successfully (id: {thread_id}).")


if __name__ == "__main__":
    main()
