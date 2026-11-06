#pragma once

namespace XRay::Engine
{
	void PreRenderThread();
    void PreRenderPostTransformsThread();
	void CalculateBonesThread();

    void GameThread();

    struct NLCPUWorkerProfile
    {
        double prerender_ms = 0.0;
        double posttransforms_ms = 0.0;
        double bones_ms = 0.0;
        double game_ms = 0.0;
    };

    // Diagnostic-only per-frame thread timings. Call BeginFrame before worker
    // jobs are dispatched and Read only after secondary_tasks.wait().
    void NLCPUWorkerProfilerBeginFrame(bool enabled);
    NLCPUWorkerProfile NLCPUWorkerProfilerRead();
}
