# NutLord's X-Ray CPU v0.4 – engine-wide performance/stability integration

Development branch based on `work/nlcpu-v03-cpu-profiler`, commit `6f9fe82e`. Tested v0.2 Build #5 and existing v0.3 source remain unchanged.

## Backports in this commit

* [X-Ray Monolith PR #772](https://github.com/themrdemonized/xray-monolith/pull/772), merged 2026-10-20: remove unused `CALifeGraphRegistry::m_terrain` allocation and its level-load traversal. The registry was write-only and was never queried. Saves/gameplay are not intentionally changed.
* [PR #792](https://github.com/themrdemonized/xray-monolith/pull/792), merged 2026-10-30: fix unsafe `sscanf` / `sscanf_s` arguments (including an incorrect `int*` in envelope loading and `size_t` formats).
* [PR #795](https://github.com/themrdemonized/xray-monolith/pull/795), merged 2026-10-30: fix undefined control-flow in UI paths, duplicate removal in UI grids, and variable initialization across `goto` in NPC spawn processing.

All three backports were checked with exact-context hunks against our v0.3 branch, not blindly cherry-picked from a later engine release.

## Further work in separate commits

1. DX11 grass instance telemetry and capacity tracking, off by default.
2. Better per-frame CPU observability for scene/update/pre-render/workers, off by default.
3. Texture and memory diagnostics, benchmark/export support, and reproducible in-game testing.
4. Research other GPU-side optimization opportunities *without modifying grass distance, image quality, save format, or AI behavior*.

## High-risk projects NOT blindly imported

- X-Ray Monolith PR #800: oneTBB scheduler, >200 modified files, runtime dependencies and possible regressions.
- PR #614: unmerged experimental parallel-level-loading overhaul (>100 files).
- PR #778: unmerged integrated GPU profiler, 120 files.
- IX-Ray's DLSS/FSR rendering and parallel systems cannot be used as drop-in replacements for GAMMA/SSS23 shaders or the MT engine.
- PR #605: GAMMA script patch can be overridden by MO2; must audit the active modlist before deploying a script change.

## Testing status

Source imported; CI and runtime still required. A successful compile is not proof of an FPS benefit. Profile 1% lows/frametimes and VRAM use at consistent locations before claims.
