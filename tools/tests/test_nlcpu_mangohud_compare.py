"""Tests for per-frame MangoHud comparisons without an installed game or GPU."""
import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "nlcpu"))
import mangohud_compare as benchmark


class MangoHudBenchmarkTests(unittest.TestCase):
    def capture(self, text: str):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "capture.csv"
            path.write_text(text, encoding="utf-8")
            return benchmark.read_frametimes(path)

    def test_metadata_preamble_and_invalid_values(self):
        frames, invalid = self.capture(
            "MangoHud,0.8.0\nOS,Linux\nCPU,Ryzen\n"
            "fps,frametime,gpu_load\n"
            "100,10,98\n80,12.5,99\n"
            "0,0,100\n50,inf,99\n"
            "fps,frametime,gpu_load\n"
        )
        self.assertEqual(frames, [10.0, 12.5])
        self.assertEqual(invalid, 3)

    def test_100_frames_one_percent_low(self):
        frames = [10.0] * 99 + [100.0]
        result = benchmark.summarize(frames)
        self.assertEqual(result["frames"], 100)
        self.assertEqual(result["one_percent_low_fps"], 10)
        self.assertEqual(result["p99_frametime_ms"], 10)
        self.assertEqual(result["max_frametime_ms"], 100)
        self.assertEqual(result["frames_over_50ms"], 1)
        self.assertAlmostEqual(result["average_fps"], 91.743, places=3)

    def test_two_slowest_frames_are_used(self):
        frames = [10.0] * 198 + [40.0, 60.0]
        result = benchmark.summarize(frames)
        self.assertEqual(result["one_percent_low_fps"], 20)
        self.assertEqual(result["frames_over_33ms"], 2)

    def test_missing_header_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing MangoHud header"):
            self.capture("metadata\n60,16.667\n")

    def test_bad_sample_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no valid frametime rows"):
            self.capture("fps,frametime\n0,0\n0,nan\n")

    def test_comparison_signs(self):
        a = benchmark.summarize([20] * 200)
        b = benchmark.summarize([10] * 200)
        diff = benchmark.compare(a, b)
        self.assertEqual(diff["average_fps_delta_pct"], 100)
        self.assertEqual(diff["one_percent_low_fps_delta_pct"], 100)
        self.assertEqual(diff["p99_frametime_ms_delta_pct"], -50)

    def test_nonfinite_or_negative_rows_are_rejected(self):
        frames, invalid = self.capture(
            "fps,frametime\n100,-1\n100,nan\n100,inf\n100,\n100,5\n"
        )
        self.assertEqual(frames, [5.0])
        self.assertEqual(invalid, 4)

    def test_empty_sample_list_fails(self):
        with self.assertRaisesRegex(ValueError, "empty frame capture"):
            benchmark.summarize([])


if __name__ == "__main__":
    unittest.main()
