#!/usr/bin/env python3
"""Analyze NLCPU in-game log samples; requires only the Python standard library.

The profiler reports aggregates of 300 frames, not raw frame samples. Therefore
its per-window p95/p99 values cannot be merged into a real global percentile.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from pathlib import Path

NUM = r"([0-9]+(?:\.[0-9]+)?)"
PROFILE_RE = re.compile(
    r"\[NLCPU PROFILE\]\s+(\d+) frames:\s+main-thread avg=" + NUM
    + r"\s+p95=" + NUM + r"\s+p99=" + NUM + r"\s+max=" + NUM
    + r"\s+ms\s*\|\s*update=" + NUM
    + r"\s+(?:prepare=" + NUM + r"\s+limiter=" + NUM + r"\s+)?render="
    + NUM + r"\s+wait=" + NUM + r"\s+ms"
)
GRASS_RE = re.compile(
    r"\[NLCPU GRASS\]\s+frame=(\d+)\s+candidates=(\d+)"
    r"\s+packed=(\d+)\s+faded=(\d+)\s+capacity=(\d+)"
    r"\s+buffer=" + NUM + r"\s+MiB"
)
PROFILE_FIELDS = ["frames", "main_avg_ms", "main_p95_ms", "main_p99_ms", "main_max_ms",
                  "update_ms", "prepare_ms", "limiter_ms", "render_ms", "wait_ms"]
GRASS_FIELDS = ["frame", "candidates", "packed", "faded", "capacity", "buffer_mib"]


def parse_log(path: Path) -> tuple[list[dict], list[dict]]:
    profiles: list[dict] = []
    grass: list[dict] = []
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            found = PROFILE_RE.search(line)
            if found:
                groups = found.groups()
                # Old v0.3 logs did not include prepare/limiter fields.
                floats = [float(x) if x is not None else None for x in groups[1:]]
                item = dict(zip(PROFILE_FIELDS, [int(groups[0]), *floats]))
                profiles.append(item)
                continue
            found = GRASS_RE.search(line)
            if found:
                vals = found.groups()
                grass.append(dict(zip(GRASS_FIELDS, [*(int(x) for x in vals[:5]), float(vals[5])])))
    return profiles, grass


def summary(profiles: list[dict], grass: list[dict]) -> dict:
    total_frames = sum(p["frames"] for p in profiles)
    def wmean(field: str):
        valid = [p for p in profiles if p.get(field) is not None]
        denom = sum(p["frames"] for p in valid)
        return round(sum(p[field] * p["frames"] for p in valid) / denom, 3) if denom else None

    p99s = [p["main_p99_ms"] for p in profiles]
    result = {
        "profile_windows": len(profiles),
        "sampled_main_thread_frames": total_frames,
        "weighted_main_mean_ms": wmean("main_avg_ms"),
        "weighted_update_mean_ms": wmean("update_ms"),
        "weighted_prepare_mean_ms": wmean("prepare_ms"),
        "weighted_limiter_mean_ms": wmean("limiter_ms"),
        "weighted_render_mean_ms": wmean("render_ms"),
        "weighted_wait_mean_ms": wmean("wait_ms"),
        "median_window_p99_ms": round(statistics.median(p99s), 3) if p99s else None,
        "max_observed_window_max_ms": max((p["main_max_ms"] for p in profiles), default=None),
        "grass_windows": len(grass),
        "max_grass_candidates": max((g["candidates"] for g in grass), default=None),
        "max_grass_packed": max((g["packed"] for g in grass), default=None),
        "max_grass_capacity": max((g["capacity"] for g in grass), default=None),
        "warnings": [
            "Per-window p95/p99 are already aggregates; median_window_p99_ms is NOT a global p99.",
            "Main-thread timing excludes some engine work and is not a pure GPU frame time.",
            "Do not compare two logs without matching map, position, weather, graphics settings and camera route."
        ],
    }
    if grass:
        result["grass_consistency_issues"] = sum(1 for g in grass if g["candidates"] != g["packed"] + g["faded"])
    return result


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", type=Path, help="X-Ray log text path")
    ap.add_argument("--json", type=Path, help="Write JSON report")
    ap.add_argument("--csv-prefix", type=Path, help="Write <prefix>-cpu.csv and <prefix>-grass.csv")
    args = ap.parse_args()
    profiles, grass = parse_log(args.log)
    result = summary(profiles, grass)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.json:
        args.json.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.csv_prefix:
        write_csv(Path(str(args.csv_prefix) + "-cpu.csv"), profiles, PROFILE_FIELDS)
        write_csv(Path(str(args.csv_prefix) + "-grass.csv"), grass, GRASS_FIELDS)
    if not profiles and not grass:
        print("No NLCPU PROFILE or GRASS markers found; enable nlcpu_profile 1 or nlcpu_grass_stats 1 in a v0.4 test build.")

if __name__ == "__main__":
    main()
