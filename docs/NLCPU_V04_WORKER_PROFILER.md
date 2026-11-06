# NLCPU worker instrumentation experiment

Base: NLCPU v0.4 engine-overhaul, with prior profiling, grass telemetry, MT stability fixes and unchanged gameplay/save format.

Added opt-in `NLCPUWorkerScope` around the four MT worker job bodies: `PreRenderThread`, `PreRenderPostTransformsThread`, `CalculateBonesThread`, and `GameThread`. C++ atomics are used for writes and the main thread only reads them after the existing `secondary_tasks.wait()`.

The existing `nlcpu_profile 1` enables the worker timers along with the main-thread phase recorder. Every 300 sampled frames, a second log line appears:

`[NLCPU WORKERS] 300 frames avg: game=... prerender=... posttransforms=... bones=... ms`

The probes are disabled when `nlcpu_profile 0`; only a low-cost branch/atomic load remains in each worker call. These are **elapsed durations**, not additive percentages of the main-frame time. Worker stages can overlap with rendering. A zero can mean the job was not scheduled for that frame. `GameThread` does not include the LuaGC job it enqueues separately.

**Risk areas:** concurrency, job completion timing, class destructor behavior, and profiler overhead when enabled. Do not merge until CI and in-game tests pass. The branch is isolated; the existing v0.4 integration branch and installed v0.2 are unchanged.

The experiment does not increase FPS by itself; it helps identify where actual FPS improvements may be obtained.
