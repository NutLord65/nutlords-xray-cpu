# NLCPU log analyzer (CachyOS / Linux)

This tool parses the in-game `[NLCPU PROFILE]` and `[NLCPU GRASS]` lines emitted by the optional v0.4 diagnostics. Pure Python standard library; **does not modify game files**.

1. In the v0.4 *test* engine console enter `nlcpu_profile 1` and `nlcpu_grass_stats 1`.
2. Play normally in a test save for at least two 300-frame windows, then enter both commands with `0`.
3. Find the game log (the exact path depends on your MO2/Proton setup).
4. Run `python3 tools/nlcpu/analyze_log.py /path/to/xray.log --csv-prefix ~/Hämtningar/nlcpu-run --json ~/Hämtningar/nlcpu-run.json`.
5. The resulting `*-cpu.csv`, `*-grass.csv`, and JSON summary are safe to share for analysis.

Run local parser tests: `cd tools/nlcpu && python3 -m unittest -v` (5 tests).

**Important:** The 300-frame per-window p95/p99 measurements cannot be combined into genuine global percentiles, so the script reports median *window* p99 instead. GPU timing is not measured by this profiler; MangoHud and a GPU-specific profiler are needed. Match weather, camera, grass density, and scene across A/B tests.
