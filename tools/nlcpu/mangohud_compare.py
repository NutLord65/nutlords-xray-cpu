#!/usr/bin/env python3
"""Compare two per-frame MangoHud CSV captures; Python standard library only.

MangoHud must use log_interval=0 (every frame). A sampled log is not suitable
for defensible 1% lows. The CSV does not always identify its capture interval,
so this must be confirmed by the person recording the benchmark.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import fmean


def read_frametimes(path: Path) -> tuple[list[float], int]:
    """Read frametime milliseconds from MangoHud CSV, skipping metadata and invalid rows."""
    frames: list[float] = []
    skipped = 0
    index: int | None = None
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as source:
        for row in csv.reader(source):
            if index is None:
                fields = [field.strip().lower() for field in row]
                if "fps" in fields and "frametime" in fields:
                    index = fields.index("frametime")
                continue
            if len(row) <= index:
                skipped += 1
                continue
            try:
                ms = float(row[index].strip())
            except ValueError:
                skipped += 1
                continue
            if not math.isfinite(ms) or ms <= 0:
                skipped += 1
                continue
            frames.append(ms)
    if index is None:
        raise ValueError(f"{path}: missing MangoHud header with fps,frametime columns")
    if not frames:
        raise ValueError(f"{path}: no valid frametime rows")
    return frames, skipped


def percentile(sorted_values: list[float], fraction: float) -> float:
    """Nearest-rank percentile, for transparent per-frame frametime reporting."""
    return sorted_values[max(0, math.ceil(len(sorted_values) * fraction) - 1)]


def summarize(frames: list[float], skipped: int = 0) -> dict:
    if not frames:
        raise ValueError("empty frame capture")
    ordered = sorted(frames)
    n = len(frames)
    total_ms = sum(frames)
    slow_1pct = ordered[-max(1, math.ceil(n * 0.01)):]
    slow_01pct = ordered[-max(1, math.ceil(n * 0.001)):]
    # FPS is total frames divided by elapsed frame-time, not mean of per-frame FPS.
    return {
        "frames": n,
        "duration_s": round(total_ms / 1000.0, 3),
        "average_fps": round(1000.0 * n / total_ms, 3),
        # 1%-low metric: reciprocal of mean duration of the slowest 1% frames.
        # Do not confuse this with the 1st percentile of instantaneous FPS.
        "one_percent_low_fps": round(1000.0 / fmean(slow_1pct), 3),
        "point_one_percent_low_fps": round(1000.0 / fmean(slow_01pct), 3),
        "p95_frametime_ms": round(percentile(ordered, 0.95), 3),
        "p99_frametime_ms": round(percentile(ordered, 0.99), 3),
        "max_frametime_ms": round(ordered[-1], 3),
        "frames_over_33ms": sum(ms > 33.333 for ms in frames),
        "frames_over_50ms": sum(ms > 50 for ms in frames),
        "skipped_invalid_rows": skipped,
    }


def compare(baseline: dict, candidate: dict) -> dict:
    fields = ("average_fps", "one_percent_low_fps", "point_one_percent_low_fps",
              "p95_frametime_ms", "p99_frametime_ms", "max_frametime_ms")
    return {
        field + "_delta_pct": round(100 * (candidate[field] - baseline[field]) / baseline[field], 2)
        if baseline[field] else None for field in fields
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v02", type=Path, required=True, help="Build #5 baseline MangoHud CSV")
    parser.add_argument("--v04", type=Path, required=True, help="v0.4 MangoHud CSV")
    parser.add_argument("--json", type=Path, help="Write full results to JSON")
    args = parser.parse_args()
    try:
        base = summarize(*read_frametimes(args.v02))
        cand = summarize(*read_frametimes(args.v04))
    except (OSError, ValueError, csv.Error) as error:
        parser.error(str(error))

    result = {
        "baseline_v02": base,
        "candidate_v04": cand,
        "v04_minus_v02_percent": compare(base, cand),
        "warnings": [
            "Requires MangoHud log_interval=0: CSV cannot always prove per-frame capture.",
            "1% low uses 1000 / mean(slowest 1% frame durations), not a MangoHud-defined percentile.",
            "Small samples, different scenes, shader cache, weather or NPC states invalidate conclusions.",
            "A positive FPS delta is better; a negative frametime delta is better.",
            "Capture several matched runs; isolated maximum stalls are not reproducible evidence.",
        ],
    }
    output = json.dumps(result, indent=2, ensure_ascii=False)
    print(output)
    if args.json:
        args.json.write_text(output + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
