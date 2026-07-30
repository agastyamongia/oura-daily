import unittest
from datetime import date

from oura_pipeline import build_rows, choose_main_sleep
from sync_oura import sync_window


class OuraPipelineTests(unittest.TestCase):
    def test_sync_window_includes_three_days(self) -> None:
        self.assertEqual(
            sync_window(date(2026, 7, 30)),
            (date(2026, 7, 28), date(2026, 7, 30)),
        )

    def test_choose_main_sleep_uses_longest_period(self) -> None:
        nap = {"id": "nap", "total_sleep_duration": 1800}
        overnight = {"id": "overnight", "total_sleep_duration": 27000}
        self.assertEqual(choose_main_sleep([nap, overnight]), overnight)

    def test_build_rows_merges_sources_and_maps_temperature(self) -> None:
        rows = build_rows(
            daily_sleep=[{"day": "2026-07-30", "score": 88}],
            daily_readiness=[
                {
                    "day": "2026-07-30",
                    "score": 91,
                    "temperature_deviation": -0.1,
                }
            ],
            daily_activity=[
                {
                    "day": "2026-07-30",
                    "score": 84,
                    "steps": 9000,
                    "active_calories": 500,
                }
            ],
            sleep_periods=[
                {
                    "day": "2026-07-30",
                    "total_sleep_duration": 27000,
                    "time_in_bed": 28800,
                    "deep_sleep_duration": 5400,
                    "rem_sleep_duration": 7200,
                    "average_hrv": 52,
                    "lowest_heart_rate": 48,
                }
            ],
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sleep_score"], 88)
        self.assertEqual(rows[0]["steps"], 9000)
        self.assertEqual(rows[0]["temperature_deviation"], -0.1)
        self.assertEqual(rows[0]["total_sleep_seconds"], 27000)


if __name__ == "__main__":
    unittest.main()
