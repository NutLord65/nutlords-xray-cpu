# NLCPU v0.4 – experimental animation/model load optimization

Source: [xray-monolith MT PR #777](https://github.com/themrdemonized/xray-monolith/pull/777), unmerged and therefore experimental as of 2026-11-06.

Changes `smem_container` from sorted vector insertion to a hash-table keyed by CRC, byte count, and equality of the underlying allocation. Existing reference-counting and locking are preserved. Intended to reduce O(N^2) insertion cost during animation/model loading.

Upstream author measured animation loading of 386ms to 78ms in a Cordon save on an i9-14900K, **not** a benchmark of NLCPU or this system. The actual outcome may differ and no FPS improvement is claimed.

Risks: changed container ordering, pointer-key lifetimes, memory fragmentation/hash pressure, and model unload/reload behavior. This remains an isolated experimental branch until a clean build and multiple level transitions/model loads have been tested. It does not replace the v0.4 stable development branch or installed Build #5.

Acceptance: compile DX11-AVX; repeat level transitions and loading; compare loading times and memory use against v0.4 without this patch. Run game on disposable test save only.
