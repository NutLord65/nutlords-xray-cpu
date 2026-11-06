#!/usr/bin/env python3
"""Smoke/unit tests for NLCPU log parsing; run python3 -m unittest."""
import tempfile
import unittest
from pathlib import Path
from analyze_log import parse_log, summary

class TestNLCPULog(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'xray.log'
            f.write_text(text, encoding='utf-8')
            return parse_log(f)

    def test_v04_profile(self):
        p, g = self.read('* [NLCPU PROFILE] 300 frames: main-thread avg=10.80 p95=13.20 p99=15.50 max=22.00 ms | update=1.30 prepare=2.10 limiter=0.00 render=6.90 wait=0.50 ms\n')
        self.assertEqual(len(p), 1)
        self.assertEqual(p[0]['limiter_ms'], 0)
        self.assertEqual(summary(p, g)['weighted_main_mean_ms'], 10.8)

    def test_v04_callbacks_are_subset_of_update(self):
        p, g = self.read('* [NLCPU PROFILE] 300 frames: main-thread avg=12.50 p95=14.20 p99=15.50 max=21.00 ms | update=4.10 callbacks=3.20 prepare=1.40 limiter=0.00 render=6.20 wait=0.80 ms\\n')
        self.assertEqual(p[0]['callbacks_ms'], 3.2)
        self.assertEqual(summary(p, g)['weighted_callbacks_mean_ms'], 3.2)
        self.assertLessEqual(p[0]['callbacks_ms'], p[0]['update_ms'])

    def test_legacy_v03_profile(self):
        p, _ = self.read('2026-11-06 * [NLCPU PROFILE] 300 frames: main-thread avg=10.80 p95=13.20 p99=15.50 max=22.00 ms | update=1.30 render=6.90 wait=0.50 ms\n')
        self.assertIsNone(p[0]['callbacks_ms'])
        self.assertEqual(p[0]['prepare_ms'], None)
        self.assertEqual(p[0]['render_ms'], 6.9)

    def test_grass(self):
        _, g = self.read('2026 * [NLCPU GRASS] frame=1200 candidates=342000 packed=341980 faded=20 capacity=524288 buffer=32.0 MiB\n')
        self.assertEqual(g[0]['packed'], 341980)
        self.assertEqual(summary([], g)['grass_consistency_issues'], 0)

    def test_no_samples(self):
        p, g = self.read('unrelated log lines\n')
        self.assertEqual(summary(p,g)['sampled_main_thread_frames'], 0)
        self.assertIsNone(summary(p,g)['weighted_main_mean_ms'])

    def test_weighted_mean(self):
        p,_ = self.read('* [NLCPU PROFILE] 100 frames: main-thread avg=10.00 p95=12.00 p99=20.00 max=30.00 ms | update=1.00 prepare=2.00 limiter=0.00 render=5.00 wait=1.00 ms\n* [NLCPU PROFILE] 300 frames: main-thread avg=20.00 p95=22.00 p99=30.00 max=40.00 ms | update=3.00 prepare=2.00 limiter=0.00 render=11.00 wait=3.00 ms\n')
        self.assertEqual(summary(p,[])['weighted_main_mean_ms'], 17.5)

if __name__ == '__main__':
    unittest.main()
