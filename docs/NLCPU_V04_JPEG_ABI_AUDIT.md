# NLCPU v0.4 – CxImage/libjpeg ABI warning investigation

## Why this experiment exists

The successful DX11-AVX build for commit `3d1f4278fa326ff2e04114cdcf420cf613a2af24` (GitHub Actions run 42300968771) still emitted:

```text
sdk/include/jpeg/jcapimin.c(51): warning C4789:
buffer 'cinfo' of size 504 bytes will be overrun;
520 bytes will be written starting at offset 0
```

The exact warning is also present in both earlier successful builds 42298608082 and 42298499037. It predates the callback profiler and this experiment. C4789 is more serious than routine deprecation warnings and warrants an investigation before treating the build as release-ready.

## Working hypothesis and isolated source change

`sdk/include/jpeg/jmorecfg.h` defaults to `typedef int boolean` (32-bit on MSVC), which the bundled C libjpeg uses in `jpeg_compress_struct`. CxImage's `ximajpg.h` previously defined `HAVE_BOOLEAN` around `jpeglib.h`, making the C++ consumer reuse the existing platform `boolean` type (potentially 8-bit Win32 RPC boolean). That can lead to a C++ object smaller than the C library's expected size. The observed 504 vs 520 warning supports, but does not by itself prove, this hypothesis.

In this **experiment-only branch**, the JPEG header is included with a temporary `#define boolean jpeg_boolean` and *without* `HAVE_BOOLEAN`, allowing libjpeg to define its own compatible `int jpeg_boolean`. The local callback signatures `EmptyOutputBuffer` and `FillInputBuffer` use that typedef, and the macro is undefined immediately after the includes. The global Win32 boolean and unrelated code are unchanged.

## Required acceptance before considering integration

1. Rebuild Windows DX11-AVX via GitHub Actions on this isolated branch; require all existing Python tests and linker steps to pass.
2. Inspect the **actual compiler log**, not only GitHub's green status. The exact `C4789` warning must disappear. If compilation fails or warnings move elsewhere, do not merge.
3. Confirm the built `AnomalyDX11AVX.exe` remains x64, manifest hash matches the artifact, and the expected DX11 pipeline and SSS23 compatibility remain available.
4. In a disposable GAMMA/MO2 test profile, exercise JPEG decode and encode code paths where available (screenshots/export, menus/textures), along with normal startup. Do not load an Invictus save.
5. Measure A/B only after safety/compatibility. This change is a **correctness experiment**, not an expected FPS optimization.

## Isolation

The known-good v0.2 Build #5, `main`, and the existing green v0.4 test build `3d1f4278` are untouched. Do not mix the EXE artifact of this JPEG experiment into the upcoming v0.4 profiler test until the warning and runtime checks pass.
