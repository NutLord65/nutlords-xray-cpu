# NLCPU v0.4 - Grass instancing diagnostics

The working SSS23-compatible GPU instancing is preserved.

## Commands (in dev test EXE)

`nlcpu_grass_stats 1`: periodically prints the number of visible instance candidates, emitted instances, alpha-faded/hidden instances, capacity, and buffer size to the game log. Run `nlcpu_grass_stats 0` to disable. No additional per-instance work is done for counters: `faded = candidates - packed`.

Logs are emitted when a details fill occurs on an engine frame divisible by 300. This may produce uneven wall-clock spacing when grass details are not drawn or when the engine frame counter skips active detail passes. Never interpret these values as FPS.

**Fast path:** If zero grass instances are visible, invalidate all visible instance draw ranges and clear per-pass lists without mapping the GPU buffer. This does not change density or culling.

**Capacity growth:** The existing dynamic instance buffer still grows geometrically when needed. It is not reduced automatically; avoids allocation churn.

### In-game checks

- Compare same area and grass density to Build #5.
- Verify no grass disappears during camera spins or while walking through sector portals.
- Check logs for candidate vs packed counts on grass-rich frames.
- Test shadow-only / no-visible-grass frames for stale draw ranges.
- GPU buffer growth may cause one-time stutter; monitor timings using `nlcpu_profile 1`.

Source remains development-only until compiled and runtime-tested.
