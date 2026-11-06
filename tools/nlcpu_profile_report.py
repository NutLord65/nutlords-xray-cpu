#!/usr/bin/env python3
"""Summarize NLCPU CPU/grassing diagnostic lines in an Anomaly game log.

Standard-library only, does not write to the game directory.
Examples:
  python tools/nlcpu_profile_report.py xray.log
  python tools/nlcpu_profile_report.py xray.log --compare baseline.log --json report.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PREFIX = re.compile(
    r"\[NLCPU PROFILE\]\s+(?P<frames>\d+) frames: "
    r"main-thread avg=(?P<avg>[\d.]+) p95=(?P<p95>[\d.]+) "
    r"p99=(?P<p99>[\d.]+) max=(?P<max>[\d.]+) ms\s*\|\s*(?P<phases>.*)"
)
PHASE = re.compile(r"(update|prepare|limiter|render|wait)=([\d.]+)")
GRASS = re.compile(
    r"\[NLCPU GRASS\]\s+frame=(\d+) candidates=(\d+) "
    r"packed=(\d+) faded=(\d+) capacity=(\d+) buffer=([\d.]+) MiB"
)


def parse_text(content: str) -> dict:
    windows: list[dict] = []
    grass: list[dict] = []
    for line in content.splitlines():
        cpu = PREFIX.search(line)
        if cpu:
            fields = cpu.groupdict()
            phases = {key: float(val) for key, val in PHASE.findall(fields["phases"])}
            if not {"update", "render", "wait"} <= phases.keys():
                continue
            windows.append({
                "frames": int(fields["frames"]),
                "avg_ms": float(fields["avg"]),
                "p95_ms": float(fields["p95"]),
                "p99_ms": float(fields["p99"]),
                "max_ms": float(fields["max"]),
                "phases_ms": phases,
            })
        detail = GRASS.search(line)
        if detail:
            frame, candidates, packed, faded, capacity, memory = detail.groups()
            grass.append({
                "frame": int(frame),
                "candidates": int(candidates),
                "packed": int(packed),
                "faded": int(faded),
                "capacity": int(capacity),
                "buffer_mib": float(memory),
            })
    return {"windows": windows, "grass_samples": grass}


def summarize(parsed: dict) -> dict:
    windows = parsed["windows"]
    grass = parsed["grass_samples"]
    frames = sum(w["frames"] for w in windows)
    def weighted(key: str) -> float | None:
        if not frames:
            return None
        return round(sum(w["frames"] * w[key] for w in windows) / frames, 3)

    phase_names = ("update", "prepare", "limiter", "render", "wait")
    phases = {}
    for name in phase_names:
        available = [w for w in windows if name in w["phases_ms"]]
        count = sum(w["frames"] for w in available)
        if count:
            phases[name] = round(
                sum(w["frames"] * w["phases_ms"][name] for w in available) / count, 3
            )

    return {
        "cpu": {
            "windows": len(windows),
            "frames": frames,
            "weighted_main_thread_avg_ms": weighted("avg_ms"),
            "worst_window_p95_ms": max((w["p95_ms"] for w in windows), default=None),
            "worst_window_p99_ms": max((w["p99_ms"] for w in windows), default=None),
            "worst_observed_frame_ms": max((w["max_ms"] for w in windows), default=None),
            "weighted_phases_avg_ms": phases,
        },
        "grass": {
            "samples": len(grass),
            "highest_visible_candidates": max((g["candidates"] for g in grass), default=None),
            "highest_packed": max((g["packed"] for g in grass), default=None),
            "highest_faded": max((g["faded"] for g in grass), default=None),
            "highest_instance_capacity": max((g["capacity"] for g in grass), default=None),
            "max_instance_buffer_mib": max((g["buffer_mib"] for g in grass), default=None),
        },
    }


def compare(candidate: dict, baseline: dict) -> dict:
    c = candidate["cpu"]["weighted_main_thread_avg_ms"]
    b = baseline["cpu"]["weighted_main_thread_avg_ms"]
    if c is None or b is None or b == 0:
        delta = None
    else:
        delta = round((c / b - 1) * 100, 2)
    return {
        "cpu_avg_walltime_change_percent": delta,
        "interpretation": (
            "Negative means less sampled main-thread time; NOT measured FPS/GPU improvement."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", type=Path, help="NLCPU Anomaly game log")
    ap.add_argument("--compare", type=Path, help="Reference log (baseline)")
    ap.add_argument("--json", type=Path, help="Optional JSON output path")
    args = ap.parse_args()
    if not args.log.is_file():
        ap.error("Game log not found: " + str(args.log))
    current = summarize(parse_text(args.log.read_text(encoding="utf-8", errors="replace")))
    report = {"candidate": current}
    if args.compare:
        if not args.compare.is_file():
            ap.error("Baseline log not found: " + str(args.compare))
        baseline = summarize(parse_text(args.compare.read_text(encoding="utf-8", errors="replace")))
        report["baseline"] = baseline
        report["comparison"] = compare(current, baseline)
    output = json.dumps(report, indent=2, ensure_ascii=False)
    print(output)
    if args.json:
        args.json.write_text(output + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
