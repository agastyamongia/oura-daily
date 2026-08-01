import unittest

from daily_summary import format_duration, generate_summary


class DailySummaryTests(unittest.TestCase):
    def test_generates_complete_summary(self) -> None:
        summary = generate_summary(
            {
                "day": "2026-07-30",
                "sleep_score": 88,
                "readiness_score": 91,
                "activity_score": 84,
                "total_sleep_seconds": 27000,
                "average_hrv": 52.4,
                "resting_hr": 48,
                "temperature_deviation": 0.12,
                "steps": 9000,
                "active_calories": 500,
            }
        )

        self.assertEqual(
            summary,
            "\n".join(
                [
                    "Oura Daily • Jul 30, 2026",
                    "Sleep 88 • Readiness 91 • Activity 84",
                    "7h 30m sleep • HRV 52.4 ms • Resting HR 48 bpm",
                    "9,000 steps • 500 active cal",
                    "Temperature deviation +0.1°C",
                ]
            ),
        )

    def test_omits_missing_metrics(self) -> None:
        summary = generate_summary(
            {
                "day": "2026-07-30",
                "sleep_score": 88,
                "readiness_score": 91,
                "activity_score": None,
                "total_sleep_seconds": 25200,
                "average_hrv": None,
                "resting_hr": None,
                "temperature_deviation": None,
                "steps": None,
                "active_calories": None,
            }
        )

        self.assertEqual(
            summary,
            "\n".join(
                [
                    "Oura Daily • Jul 30, 2026",
                    "Sleep 88 • Readiness 91",
                    "7h sleep",
                ]
            ),
        )

    def test_rejects_row_without_metrics(self) -> None:
        with self.assertRaisesRegex(ValueError, "No summary metrics"):
            generate_summary({"day": "2026-07-30"})

    def test_formats_short_duration(self) -> None:
        self.assertEqual(format_duration(3300), "55m")

    def test_omits_temperature_that_rounds_to_zero(self) -> None:
        summary = generate_summary(
            {
                "day": "2026-07-30",
                "sleep_score": 74,
                "temperature_deviation": -0.01,
            }
        )
        self.assertNotIn("Temperature", summary)


if __name__ == "__main__":
    unittest.main()
