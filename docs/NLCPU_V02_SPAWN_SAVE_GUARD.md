# NLCPU v0.2 – safe NPC export during spawn

Source: [X-Ray Monolith PR #763](https://github.com/themrdemonized/xray-monolith/pull/763), merged October 21, 2026.

During `net_Spawn`, stalkers and mutants can temporarily have an empty `NET` update queue. A save or level change during this short window may call `CCustomMonster::net_Export` and assert on `!NET.empty()`.

This isolated backport overrides `CCustomMonster::net_Relevant()`, retaining the base object's relevance check but declining export until `NET` has initial data.

Scope: no changes to rendering, spawns, game data, saved games, or network packet format. The normal export path is unchanged.

Review/testing: build DX11-AVX; test repeated saves and level transitions with AI activity; verify after death/reload and that no incomplete monster state is serialized. Do not perform destructive save experiments on an Invictus save. Prior tested v0.1 and v0.2 binaries are unaffected.

This patch is a stability guard, not an FPS optimization.
