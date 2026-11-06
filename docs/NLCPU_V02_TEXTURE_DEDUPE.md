# NLCPU v0.2 - experimental sequence texture deduplication

Backports merged upstream xray-monolith PR #793 (DX11/DX10 + legacy variants).
When the same normalized frame name appears repeatedly in a .seq sequence, the
already loaded surface and SRV are reused with appropriate COM AddRef() counts.
Animation timing/order is unchanged. Unique texture allocations and reported
memory may decrease for repeated-frame sequences.

This branch is isolated from the stability worktree until compilation and
in-game testing verify correct level transitions, effects (fire, emissions),
and unloading/reloading. No measured FPS gain is claimed.

Sources: https://github.com/themrdemonized/xray-monolith/pull/793
