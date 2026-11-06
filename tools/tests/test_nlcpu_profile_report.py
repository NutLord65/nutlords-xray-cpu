"""Regression tests for NLCPU's external log parser."""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nlcpu_profile_report as report


class ParseTests(unittest.TestCase):
    def test_v04_cpu_profile(self):
        line = ("INFO * [NLCPU PROFILE] 300 frames: main-thread avg=12.30 "
                "p95=19.20 p99=23.10 max=35.90 ms | update=1.40 "
                "prepare=0.70 limiter=0.00 render=8.10 wait=2.10 ms")
        data = report.parse_text(line)
        self.assertEqual(data["windows"][0]["frames"], 300)
        self.assertAlmostEqual(data["windows"][0]["phases_ms"]["prepare"], 0.70)
        self.assertAlmostEqual(report.summarize(data)["cpu"]["worst_window_p99_ms"], 23.10)

    def test_legacy_v03_profile(self):
        line = ("* [NLCPU PROFILE] 300 frames: main-thread avg=18.00 "
                "p95=20.00 p99=22.00 max=27.00 ms | update=4.00 "
                "render=10.00 wait=2.00 ms")
        summary = report.summarize(report.parse_text(line))["cpu"]
        self.assertEqual(summary["weighted_main_thread_avg_ms"], 18.0)
        self.assertNotIn("limiter", summary["weighted_phases_avg_ms"])

    def test_grass_stats(self):
        line = ("* [NLCPU GRASS] frame=600 candidates=900 "
                "packed=880 faded=20 capacity=262144 buffer=16.0 MiB")
        result = report.summarize(report.parse_text(line))["grass"]
        self.assertEqual(result["highest_faded"], 20)
        self.assertEqual(result["highest_instance_capacity"], 262144)

    def test_comparison(self):
        one = {"cpu": {"weighted_main_thread_avg_ms": 10.0}}
        two = {"cpu": {"weighted_main_thread_avg_ms": 12.0}}
        self.assertEqual(report.compare(one, two)["cpu_avg_walltime_change_percent"], -16.67)

    def test_no_logs(self):
        summary = report.summarize(report.parse_text("normal X-Ray log with no metrics"))
        self.assertIsNone(summary["cpu"]["weighted_main_thread_avg_ms"])
        self.assertEqual(summary["grass"]["samples"], 0)


if __name__ == "__main__":
    unittest.main()
