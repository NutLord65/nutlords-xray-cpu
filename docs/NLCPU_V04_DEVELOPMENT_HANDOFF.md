# NutLord's X-Ray CPU – v0.4 development handoff

**Status:** development, not a public release. Base v0.2 Build #5 was previously tested in Cordon on a disposable profile; v0.4 changes require game testing. All work stays in GitHub development branches, never overwriting the GAMMA installation or Invictus saves.

## Engine changes integrated in `work/nlcpu-v04-engine-overhaul`

| Area | What changed | Intended result |
| --- | --- | --- |
| MT-TEST/DX11 | Retained original multithreading and Sam's instanced grass draw path | Keep existing v0.1 render path and SSS23 compatibility |
| Grass | Dynamic instancing capacity, corrected zero-alpha iteration, optional telemetry `nlcpu_grass_stats` | No silent drops at the old fixed capacity; diagnose rendering |
| Grass | Skip mapping/discarding instancing buffer when nothing visible | Avoid unnecessary DX11 work on empty frames |
| Texture | Deduplicate repeated `.seq` frames without changing sequence timing | Fewer duplicate allocations |
| Stability | Lua null file-list access and DX11 HRESULT initialization | Avoid crashes/undefined return values |
| Stability | Guard NPC net export until spawn network state initialized | Prevent one specific save/spawn assertion |
| Level loading | Remove unused ALife terrain registry (upstream #772) | Less work during level initialization |
| Safety | Upstream #792/#795 format parsing, UI and spawn-flow fixes | Avoid undefined behavior/unsafe inputs |
| Diagnostics | `nlcpu_profile` main-thread windowed wall-time averages, p95/p99 and phase breakdown | Identify main-thread stalls before attempting major CPU changes |
| Diagnostics | `nlcpu_about` build identity; Grass stats console; SHA256 build manifest | Easier version verification and regression reports |
| Tooling | Pure Python log report/comparison and CSV/JSON analyzer with unit tests | Reproducible capture review on Linux |

## Separate experimental branches (not merged into main development line)

- `work/nlcpu-v04-sharedmem-exp`: upstream MT PR #777 hash-based shared animation memory. Promising model/animation load-time improvement, but changes memory-container implementation and remains risky until repeated level-load testing.
- `work/nlcpu-v04-worker-profiler`: opt-in timing of GameThread, pre-render jobs, and bone update workers. Need to validate worker synchronization and nonintrusive sampling.

## Why other features are deliberately deferred

- Upstream MT oneTBB PR #800: >200 files, runtime DLL dependencies, needs careful regression and compatibility testing.
- MT GPU timeline profiler PR #779: >200 files, far too broad to merge blindly; our lightweight diagnostic path is a staging step.
- Parallel level loading PR #614: unmerged, 100+ changes and important threading/lifetime hazards.
- Lua monster registry PR #605: game-script mod must be reconciled against real MO2 winning files to avoid modpack breakage.
- Shaders/overdraw: v0.4 intentionally does not reduce grass, draw distance, or visual effects. Real GPU optimization requires render-pass profiling first.

## In-game test procedure after successful CI

1. Keep **AnomalyDX11AVX_NLCPU_V02_B5.exe** untouched.
2. Download the v0.4 GitHub Actions executable artifact and verify its SHA256 against the provenance artifact.
3. Install under a new executable name e.g. `AnomalyDX11AVX_NLCPU_V04_TEST.exe` in `Anomaly/bin/`; never replace the original.
4. In MO2, choose `NutLords-ATAK-Test`, profile-specific saves, and the already working separate SSS23 test shaders.
5. Start the v0.4 EXE via a *new* Modify Executables entry, using same Start in/arguments as v0.2.
6. Test disposable save: Cordon, a grass-rich map, weather/particle effects, a level transition, reload/weapon animations, AI, and repeated load/save.
7. Once visually correct, type `nlcpu_about`, `nlcpu_profile 1`, `nlcpu_grass_stats 1` in console. Capture samples and disable with `0`. Do not interpret main-thread wall-time samples as GPU timestamps.
8. Compare against Build #5 under same scene, camera, grass settings, resolution, weather and route; check GPU utilization, average FPS, 1%-low FPS and stutters.

## Development acceptance

- Windows VS2022 DX11-AVX compiler passes.
- Both Python analyzer test suites pass.
- Hash/provenance available, signed or trusted source checked.
- New EXE can reach the main menu and multiple map areas on dedicated test save.
- Visual effects, grass density/distance, shadows, motion vectors and savegame behavior unchanged.
- No reported extra memory growth or crashes during extended tests.
- Real-world A/B metrics are compared before claiming FPS gain.

**Notes:** A green GitHub Actions check only proves compilation and selected tests, not real gameplay stability or higher FPS.
