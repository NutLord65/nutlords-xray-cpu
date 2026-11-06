# NutLord's X-Ray CPU v0.4 – CPU, grass, and build diagnostics

## In-game console commands

| Command | Description |
|---|---|
| `nlcpu_about` | Prints the v0.4 dev label and available commands in the game log |
| `nlcpu_profile 1` | Enables 300-frame CPU wall-time sampling |
| `nlcpu_profile 0` | Disables CPU sampling |
| `nlcpu_grass_stats 1` | Logs grass instance capacity and alpha fade stats |
| `nlcpu_grass_stats 0` | Disables grass statistics |

All diagnostics are off by default, to minimize runtime overhead.

## CPU profiler output

Every 300 non-paused/non-precache sampled frames:

`[NLCPU PROFILE] 300 frames: main-thread avg=... p95=... p99=... max=... ms | update=... callbacks=... prepare=... limiter=... render=... wait=... ms`

- **main-thread**: measured part of the main thread's frame. Not a total GPU frametime measurement.
- **update**: direct cost of `FrameMove()`, including callbacks that run synchronously there.
- **callbacks** (new diagnostic field): time inside `Device.seqFrame.Process(rp_Frame)`, a **subset of update**, not an additional phase. Includes CLevel and other frame callbacks (potentially Lua/AI indirectly); **not** pure Lua timing. Older v0.3/v0.4 logs omit it.
- **callbacks_share_of_update_pct** (analyzer only): approximate percentage of `update` spent in `seqFrame` callbacks; calculated **only over matching new-format windows**. It is not a share of total frame time, total Lua time or AI time. `callbacks_coverage_frames` indicates how many frames were eligible for this ratio.
- **prepare**: particles, camera/shader matrices, and enqueueing background work after `FrameMove`.
- **limiter**: optional `ECO_RENDER` FPS cap/pacing wait; separated to avoid confusing capping with render overhead.
- **render**: render submission, present/device operations; may include waiting on GPU or driver, *not* standalone GPU execution time.
- **wait**: the main thread's wait for worker tasks. It does not itself report which worker was expensive.
- `p95`, `p99`, `max`: per-window main-thread wall-time spikes.

**Do not infer FPS improvement from these diagnostics without an A/B test.** Graphics features and render distance are unchanged by this profiler patch. The CPU profiler still measures on the main thread and cannot attribute Lua/AI sub-tasks running on workers; add specific worker scopes after reviewing data.

## Recommended captures

At the same map, resolution and settings:
1. Stand still by NPCs and capture at least two windows (600+ frames).
2. Turn slowly toward dense vegetation and repeat.
3. Enter a populated area to provoke NPC updates.
4. Compare to a second engine build with the same test-save (never an Invictus save).

Use RenderDoc via already-existing `rdoc_capture` for deeper DX11 calls and GPU pipeline inspection. The profiler is not a replacement for a GPU timestamp query analysis.
