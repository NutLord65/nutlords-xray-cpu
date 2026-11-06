# NutLord's X-Ray CPU – v0.2 development audit (2026-11-06)

## Scope and safety

Base: `work/grass-mt-20261011`, commit `5551b178`, originally based on MT-TEST `871e2491`.
The working v0.1 test executable and the existing GAMMA/Invictus installation are not modified by this branch.
No graphics reduction, grass distance reduction, or arbitrary distance-based thinning is intended.

## v0.2 first patch

1. Fix an incorrect `break` on zero alpha in `hw_Fill_Instances()`; it used to discard all following instances in the same slot-part.
2. Replace fixed 262,144-instance buffer with geometric growth before mapping; pre-count uses the visible instance lists and is an upper bound for alpha-skipped instances.
3. Rebind vertex stream slot 1 **after** filling, because buffer growth creates a new D3D11 buffer.
4. Keep a hard invariant on the count instead of silently dropping grass at the old cap.
5. Log only when the instance buffer grows. The additional count pass costs CPU time and must be profiled before release.

A successful compile does not establish rendering correctness or performance. Test normal and high-grass-density scenes, shadow passes, wind animation, and device/reset behavior. If D3D11 cannot allocate a requested buffer, the existing R_CHK failure path remains; a future chunked fallback could improve resilience to OOM.

## Other upstream optimization candidates (reviewed, not imported yet)

- xray-monolith PR #802 (merged 2026-11-02): guard null FS_file_list; targeted stability backport candidate after checking MT ancestry.
- xray-monolith PR #789 (merged 2026-10-27): initialize/check HRESULT in DX11 device creation; targeted stability candidate.
- xray-monolith PR #687 (merged 2026-09-27): clear mapLOD during traverse to avoid LOD list accumulation; check presence on our MT baseline before any port.
- xray-monolith PR #705 (merged 2026-10-06): proper THM loader thread join and lock; verify the MT implementation and race behavior.
- xray-monolith PR #592 (merged 2026-07-05): DX11 texture eviction; check existing cache integration and memory telemetry.
- xray-monolith PR #605 (merged 2026-07-22): specialized monster registry in scripts; game data and modpack compatibility required.
- xray-monolith PR #641 (merged 2026-09-07): low-overhead LuaJIT CPU/allocation profiling; check included version.
- xray-monolith PR #614 (closed unmerged): parallel level loading; not safe to cherry-pick without large-scale integration review.
- xray-monolith PR #800 (open, >200 changed files): oneTBB scheduler; high-risk experimental branch only.

Also assess OpenXRay and IX-Ray's memory, render, AI, texture streaming, and scheduler techniques, but avoid transplanting unrelated engine subsystems blindly.

## Performance method

Collect exact same-scene frametime distributions and CPU/GPU usage, test repeated level loads and night/rain/firefights, and compare against v0.1 and the original MT executable. Investigate worst 1% frametimes in addition to average FPS. No performance improvements are claimed until measured.
