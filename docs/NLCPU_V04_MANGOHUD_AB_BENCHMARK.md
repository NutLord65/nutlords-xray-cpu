# NLCPU v0.4 — reproducible MangoHud A/B performance captures

**Status:** standalone measurement tooling only. No engine, shader, AI, save or MO2 files changed by this benchmark implementation.

## Important distinction

The in-game `nlcpu_profile` measures selected **CPU main-thread phases** and works only in v0.4. MangoHud captures are separate **per-frame presentation intervals** and are required to compare v0.2 Build #5 vs v0.4.

Do **not** compare a v0.4 `main-thread avg` with a v0.2 screenshot's FPS. Neither a single FPS screenshot nor 300-frame aggregate engine p99 can establish an FPS or 1%-low improvement.

## Prepare each capture

1. Use the same disposable test profile and graphics options. Do not load Invictus/permadeath saves. Keep your known-good v0.2 executable untouched.
2. Make a writable folder for MangoHud CSVs (example: `mkdir -p "$HOME/Hämtningar/NLCPU-bench"`).
3. Preserve your existing MangoHud configuration. Add or temporarily set **these exact keys** in the currently used MangoHud config (use an absolute output path, not `~` in config):
   ```ini
   output_folder=/home/nutlord/Hämtningar/NLCPU-bench
   log_interval=0
   log_duration=90
   toggle_logging=Shift_L+F2
   ```
   `log_interval=0` is essential: MangoHud then captures every frame rather than periodic samples. Logging has overhead, so use the **same settings for both builds**.
4. Warm up the same Cordon test area for ~60 seconds **before starting the capture**. Run an identical ~90-second stationary view or repeatable walking route; keep in-game weather/time, NPC population and view direction as close as feasible. Do not compare captures from menu/loading screens.
5. Use `Shift+F2` to start logging after warm-up; let `log_duration=90` end capture. The log files should be identifiable by session. Move/copy them safely to `v02.csv` and `v04.csv` without replacing another run.
6. Repeat at least 3 times per engine, preferably alternating v0.2/v0.4 order. Keep distinct named captures instead of overwriting results. Capture GPU-load observations separately; CPU and GPU workloads may differ even within the same place.

## Analyze captures

From a local clone of this repository:

```bash
python3 tools/nlcpu/mangohud_compare.py \
  --v02 "$HOME/Hämtningar/NLCPU-bench/v02.csv" \
  --v04 "$HOME/Hämtningar/NLCPU-bench/v04.csv" \
  --json "$HOME/Hämtningar/NLCPU-bench/compare.json"
```

The script accepts MangoHud CSV metadata/preamble, locates the `fps,frametime` header, validates per-frame frametimes, and reports:

- **Average FPS:** frames / total sum of frame durations.
- **1% low FPS:** 1000 / mean duration of the slowest 1% of captured frames (ceil-to-one-frame rule).
- **0.1% low FPS:** same method for slowest 0.1%; interpret cautiously with short captures.
- Frame-time P95, P99, max and number of frames slower than 33.33 / 50 ms.
- Percentage change from v0.2 to v0.4, where positive FPS is better and negative frametime is better.

**Limitations:** CSV may not indicate the configured logging interval: sampled MangoHud logs can produce misleading 1% lows. The tool cannot prove scene equivalence and intentionally does not infer a regression from a single outlier. Main-thread per-window P99 from NLCPU engine logs must not be merged as a frame-level P99.

## Tests

```bash
python3 -m unittest discover -s tools/tests -p 'test_*.py'
```

The existing Windows DX11-AVX CI workflow also runs this test suite on tool changes.
