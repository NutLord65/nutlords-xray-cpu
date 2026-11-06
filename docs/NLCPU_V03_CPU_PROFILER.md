# NLCPU v0.3 - CPU frame observability (development only)

Built on MT X-Ray Monolith + NLCPU v0.2 Build #5; no engine settings or save format are changed.

## How to use

1. Run **only** the development EXE in the MO2 test profile, not the Invictus save.
2. Open the in-game console, enter `nlcpu_profile 1`.
3. Play for at least 300 non-paused, non-precache frames.
4. The engine emits one summary line every 300 frames into the ordinary game log:

`[NLCPU PROFILE] 300 frames: main-thread avg=... p95=... p99=... max=... ms | update=... render=... wait=... ms`

5. Enter `nlcpu_profile 0` when finished.

* `main-thread`: wall time from just after startup/benchmark checks to completion of the secondary-worker wait. It does **not** include some frame-begin and presentation overhead.
* `update`: direct time inside `CRenderDevice::FrameMove`. Not the total asynchronous AI work.
* `render`: the render submission region including potential driver/GPU waits. It is **not** pure GPU time.
* `wait`: time the main thread spends inside `secondary_tasks.wait`. Large values can indicate worker bottlenecks or scheduling overhead.
* `p95`, `p99` and `max`: sorted main-thread wall times in a window of 300 samples, without altering FPS limiter or visual settings.

Time sampling is disabled by default. When off, only a branch/check runs (no chrono calls or per-frame arrays updated).
Do not compare these figures directly with MangoHud GPU frametimes; use them to locate expensive main-thread sections.
Log only every 300 frames to limit logging overhead; samples reset when the console variable is switched.

## Next steps

When results show a bottleneck, add targeted scopes around AI/Lua or renderer calls **in a separate branch**, or enable the larger Optick experiment (upstream PR #778) when its integration is proven. Do not merge the 120-file profiler before independent review.

## Acceptance checks

- GitHub Actions DX11-AVX compile
- In-game console command works and prints a summary
- Turning command off stops all summaries
- Repeated level changes do not crash
- Compare frame pacing with and without profiling; profile data alone is not an FPS improvement
