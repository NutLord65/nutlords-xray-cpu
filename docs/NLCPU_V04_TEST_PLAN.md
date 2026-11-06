# NLCPU v0.4 – development release acceptance and safe testing

This is a **development-only** engine. Do not replace Anomaly/bin/AnomalyDX11AVX.exe.
Do not load the permanent Invictus save. The existing v0.2 Build #5 remains the last in-game-tested engine.

## Required checks before moving to general testing

1. GitHub Actions Build DX11-AVX succeeds for the **exact v0.4 commit**.
2. Python log analysis unit tests pass.
3. Download `NLCPU-MT-DX11-AVX-executables` and `NLCPU-MT-DX11-AVX-provenance` artifacts from the same run.
4. Verify EXE SHA256 equals the manifest `ExecutableSHA256` field.
5. Install under a **new distinct filename** (e.g. `AnomalyDX11AVX_NLCPU_V04_TEST.exe`) alongside prior EXEs.
6. Add a separate MO2 executable entry, keeping the old one unchanged; preserve the SSS23 compatibility shader mod and its file priority.

## Test scenarios

**A. Rendering:** grass-dense Cordon, camera spins, shadow transitions, wind and SSS23 shaders. Try `nlcpu_grass_stats 1` and verify `packed` vs `candidates`.

**B. Effects and textures:** multiple animated .seq textures (campfire and visual effects), reload levels and inspect for broken or missing animation frames.

**C. Engine and saves:** new test-save only; load, save, level transition, inventory, PDA, dialogue, spawn activity. Run for longer sessions to catch memory/stability regressions.

**D. Timing:** turn on `nlcpu_profile 1` and collect several 300-frame log windows; compare like-for-like resolution, place, density and time of day. Run `python tools/nlcpu_profile_report.py <log.txt>` to summarize. Sampled CPU main-thread timings are **not GPU frametimes** and do not prove FPS improvement.

## Planned experiments not in v0.4 default engine

- GPU timestamp profiling through D3D11 or optional RenderDoc captures.
- oneTBB MT scheduler (#800): requires independent functional/frametime validation and dependency audit.
- Level loading parallelism (#614): unmerged and >100 files; requires thread ownership review.
- Faster grass cache update from upstream #462: significant algorithm change and no density regression data.
- Lua spatial-query addon patch (#605): MO2 scripts may override it; audit the actual GAMMA profile before installation.

Any failed shader, animation, or level-load test blocks promotion.
