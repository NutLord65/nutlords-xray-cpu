# NLCPU v0.4 – CPU hotspot audit: scripts, AI and ballistics

**Status:** source-level audit and hypotheses; NOT measured performance results. No behavior changes. Tested v0.2 Build #5 and Invictus saves are untouched.

## Observed code paths (v0.4 engine-overhaul baseline)

| Priority | Code / path | Source evidence | Why profile it | What NOT to assume |
| --- | --- | --- | --- | --- |
| P1 | `src/xrGame/Level.cpp` → `CLevel::OnFrame` | Calls `ProcessGameEvents`, map/task updates, `inherited::OnFrame`, script process, physics commander, deferred Lua GC and attachment updates | Broad gameplay update callback; main candidate when `callbacks` is a large part of `update` | `callbacks` includes non-Lua work; not a Lua metric |
| P1 | `src/xrGame/Level_Bullet_Manager.cpp` → `try_update_bullet` | Resolves `_G.CBulletOnUpdate`, creates a `luabind::newtable`, populates it and calls Lua when the hook exists | Per-bullet frequency can be high during combat; Lua allocations and bridge may matter | Not evidence the hook is present in the *winning GAMMA MO2 scripts*; not yet benchmarked |
| P1 | `src/xrGame/Level.cpp` → `CLevel::script_gc`, `LuaGC` | GC step may run via parallel task or synchronously depending on `mtLUA_GC` and `psLua_ParallelGC` | GC bursts may affect 1% lows or worker waits | Parallel timing and synchronization need separate measurements; don't change GC settings blindly |
| P2 | `src/xrGame/ai/stalker/ai_stalker.cpp` → `CAI_Stalker::shedule_Update` | Runs AI logic, sound callbacks, visual processing and optional `_G.CNPCBeforeLookAtActor` callback when nearby | Potentially substantial in populated areas | Do not halve AI ticks or change decisions without gameplay validation |
| P2 | `src/xrServerEntities/script_process.cpp` → `CScriptProcess::update` | Executes one coroutine from its queue per update | Existing profiler misses breakdown of coroutine resume | This is NOT the sum of all gameplay Lua callbacks; don't label it “total Lua” |
| P2 | `src/xrGame/Level_Bullet_Manager.cpp` → `CBulletManager::CommitEvents` | Per-event optional `CBulletOnImpact` / `CBulletOnRemove` callbacks create tables and call Lua | Potential burst at impact-heavy scenes | Trigger paths may be infrequent; guard against double-counting across threads |

## New first-stage measurement: frame callbacks

`src/xrEngine/device.cpp` measures `Device.seqFrame.Process(rp_Frame)` behind the existing `nlcpu_profile` toggle. Added output `callbacks=... ms` is **nested inside** `update=... ms`, NEVER additive. This measures *all* frame callbacks, including CLevel when registered, not Lua itself; work performed asynchronously on workers may be absent. No added clock reads when profiling is off.

Logs retain the existing 300-frame window format and existing Python analyzers accept old logs without `callbacks`.

## Experimental protocol (before any optimization)

1. Verify Windows DX11-AVX CI and Python test suites for the exact branch commit. A green compile is not a gameplay result.
2. Run a separately named test EXE from a separate MO2 profile; never overwrite tested Build #5 and never open Invictus saves. Keep shaders and graphics settings identical.
3. Enable `nlcpu_profile 1`, capture at least two 300-frame windows in each scenario, then disable it.
4. Scenarios: (a) static Cordon without NPCs in view, (b) populated camp with active NPCs, (c) short controlled combat with frequent bullet/impact events, (d) dense-grass camera turn, (e) loading/saving and level transition for stability (not direct in-window FPS comparison).
5. Compare `update`, `callbacks`, `render`, `wait`, p95/p99 and MangoHud frame pacing. Log averages are aggregate means and cannot be combined into a global p99.
6. If `callbacks` dominates `update`, add separately gated instrumentation around level game events, object scheduling and script process. Measure before changes.
7. If combat hitches dominate, instrument bullet hooks separately on their actual execution thread (avoid thread-unsafe cross-thread accumulators) and verify with the MO2 winning `CBulletOnUpdate` hook.
8. If `wait` or stutters dominate, profile worker completion and Lua GC independently. Avoid changing parallelism/GC policies before timing data.

## Guardrails

- Avoid profiling with Lua debug hooks or allocating a Lua table in the *profiler* itself; instrumentation must remain off by default.
- Do not suppress gameplay callbacks, reduce grass/view distance/AI tick rate, alter save formats, or merge broad upstream scheduler changes as a speculative optimization.
- A pure Lua time figure requires tracing all relevant Lua bridges, which current `callbacks` does not do.
- Confirm X-Ray/Monolith engine thread ownership before adding counters around ballistics/AI or Lua GC.
- Promote only after matching A/B performance captures and rendering/save/load stability tests on disposable saves.
