#include "stdafx.h"
#include "EngineThreading.h"
#include "CustomHUD.h"
#include "IGame_Persistent.h"
#include "IGame_Level.h"
#include "Rain.h"
#include "../../xrCDB/ISpatial.h"
#include "../../xrCDB/Frustum.h"
#include "Render.h"
#include "Irenderable.h"
#include "../../Include/xrRender/Kinematics.h"

#include <atomic>
#include <chrono>

// Lightweight wall-time probes for the MT job bodies. The clock is only
// queried when the NLCPU developer profiler is enabled in the game console.
namespace
{
    using NLCPUWorkerClock = std::chrono::steady_clock;
    std::atomic<bool> nlcpu_worker_enabled{false};
    std::atomic<u64> nlcpu_prerender_us{0};
    std::atomic<u64> nlcpu_posttransforms_us{0};
    std::atomic<u64> nlcpu_bones_us{0};
    std::atomic<u64> nlcpu_game_us{0};

    class NLCPUWorkerScope
    {
        std::atomic<u64>& output;
        bool active;
        NLCPUWorkerClock::time_point start;

    public:
        explicit NLCPUWorkerScope(std::atomic<u64>& target)
            : output(target), active(nlcpu_worker_enabled.load(std::memory_order_relaxed))
        {
            if (active)
                start = NLCPUWorkerClock::now();
        }

        ~NLCPUWorkerScope()
        {
            if (active)
            {
                const auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
                    NLCPUWorkerClock::now() - start).count();
                output.store(static_cast<u64>(elapsed), std::memory_order_relaxed);
            }
        }
    };
}

void XRay::Engine::NLCPUWorkerProfilerBeginFrame(bool enable)
{
    // Previous frame's workers must have finished before calling this.
    nlcpu_worker_enabled.store(enable, std::memory_order_relaxed);
    nlcpu_prerender_us.store(0, std::memory_order_relaxed);
    nlcpu_posttransforms_us.store(0, std::memory_order_relaxed);
    nlcpu_bones_us.store(0, std::memory_order_relaxed);
    nlcpu_game_us.store(0, std::memory_order_relaxed);
}

XRay::Engine::NLCPUWorkerProfile XRay::Engine::NLCPUWorkerProfilerRead()
{
    NLCPUWorkerProfile value;
    value.prerender_ms = nlcpu_prerender_us.load(std::memory_order_relaxed) / 1000.0;
    value.posttransforms_ms = nlcpu_posttransforms_us.load(std::memory_order_relaxed) / 1000.0;
    value.bones_ms = nlcpu_bones_us.load(std::memory_order_relaxed) / 1000.0;
    value.game_ms = nlcpu_game_us.load(std::memory_order_relaxed) / 1000.0;
    return value;
}

BOOL mt_Scheduler = TRUE;
BOOL mt_SchedulerRT = FALSE;

void XRay::Engine::PreRenderThread()
{
    NLCPUWorkerScope nlcpu_scope(nlcpu_prerender_us);
	PROF_THREAD("Secondary Task 1");

	if (g_pGamePersistent && g_pGamePersistent->pEnvironment && g_pGamePersistent->pEnvironment->eff_Rain)
	{
		PROF_EVENT("CEffect_Rain::UpdateItems");
		g_pGamePersistent->pEnvironment->eff_Rain->UpdateItems();
	}

	if (g_pGamePersistent && Device.ParticleWorkerCallback)
	{
		PROF_EVENT("Process Particles");
		Device.ParticleWorkerCallback();
	}
}

void XRay::Engine::PreRenderPostTransformsThread()
{
    NLCPUWorkerScope nlcpu_scope(nlcpu_posttransforms_us);
    PROF_THREAD("Secondary Task 1.1");
    {
        PROF_EVENT("seqParallelRender");
        for (auto& it : Device.seqParallelRender)
            it();
    }
}

struct SpatialSnapshot
{
	ISpatialShared ptr;
    IKinematics* pKin;
    float distSq;

    SpatialSnapshot(ISpatialShared _ptr, IKinematics* _pKin, float _distSq) : ptr(_ptr), pKin(_pKin), distSq(_distSq) {};
};
void XRay::Engine::CalculateBonesThread()
{
    NLCPUWorkerScope nlcpu_scope(nlcpu_bones_us);
	PROF_THREAD("Secondary Task 3");

	PROF_EVENT("CalculateBones");

	if (!g_SpatialSpace) return;
	if (Device.Paused()) return;
	if (!psDeviceFlags.test(rsDrawDynamic)) return;
	if (!g_pGameLevel || !g_pGameLevel->bReady) return;
	if (!g_pGameLevel->CurrentEntity()) return;

	static CFrustum ViewBase;
	ViewBase.CreateFromMatrix(Device.mFullTransform_saved, FRUSTUM_P_LRTB | FRUSTUM_P_FAR);

	static xr_vector<ISpatialShared> spatials = {};
    spatials.clear();
	g_SpatialSpace->q_sphere(
		spatials,
		ISpatial_DB::O_ORDERED,
		STYPE_RENDERABLE + STYPE_RENDERABLESHADOW + STYPE_PARTICLE + STYPE_LIGHTSOURCE,
		Device.vCameraPosition_saved,
		g_pGamePersistent->Environment().CurrentEnv->fog_distance
	);

	static xr_vector<SpatialSnapshot> spatialsSnapshot;
	spatialsSnapshot.clear();
	{
		for (ISpatialShared spatial : spatials)
		{
			if (!spatial)
				continue;

            float distSq = Device.vCameraPosition_saved.distance_to_sqr(spatial->spatial.sphere.P);
			if (!ViewBase.testSphere_dirty(spatial->spatial.sphere.P, spatial->spatial.sphere.R))
			{
				if (distSq > 62500.f)//250 m
					continue;
			}
				
			spatial->spatial_updatesector();

            if
            (
                (spatial->spatial.type & (STYPE_PARTICLE | STYPE_LIGHTSOURCE)) ||
                !(spatial->spatial.type & (STYPE_RENDERABLE | STYPE_RENDERABLESHADOW))
            )
                continue;

            auto renderable = spatial->dcast_Renderable();
            if (!(renderable && renderable->renderable.visual))
                continue;

            IKinematics* pKin = renderable->renderable.visual->dcast_PKinematics();
            if (!pKin)
                continue;

			spatialsSnapshot.emplace_back(spatial, pKin, distSq);
		}
	}

	static auto sortFunc = [](const SpatialSnapshot& _1, const SpatialSnapshot& _2) noexcept
	{
		return _1.distSq < _2.distSq;
	};
	std::sort(spatialsSnapshot.begin(), spatialsSnapshot.end(), sortFunc);

    for (const auto& snapshot : spatialsSnapshot)
        snapshot.pKin->CalculateBones(TRUE);
}

extern BOOL psLua_ParallelGC;
int psLua_ParallelGC_CallAmount = 25;
void XRay::Engine::GameThread()
{
    NLCPUWorkerScope nlcpu_scope(nlcpu_game_us);
	PROF_THREAD("Secondary Task 2")
		
	// we has granted permission to execute
	if (g_hud)
	{
		PROF_EVENT("g_hud OnFrameMT");
		g_hud->OnFrameMT();
	}

	if (g_pGameLevel && g_pGameLevel->bReady)
	{
		PROF_EVENT("SoundEvent_Dispatch");
		g_pGameLevel->SoundEvent_Dispatch();
	}

	if (!Device.Paused())
	{
		if (mt_Scheduler)
		{
			PROF_EVENT("Sheduler Deferred");
            if (mt_SchedulerRT)
            {
                ::Engine.Sheduler.Update();
            }
            else
            {
                ::Engine.Sheduler.UpdateDeferred();
                ::Engine.Sheduler.UpdateFinalize();
            }
		}
	}

	{
		PROF_EVENT("seqParallel");
		for (u32 pit = 0; pit < Device.seqParallel.size(); pit++)
			Device.seqParallel[pit]();
		Device.seqParallel.clear();
	}

    // demonized: While Renderer prepares frame and GPU renders it, use time opportunity to repeatedly call Lua GC with small step value
    // Reduces stutters since less work will be done in main GC step or no work at all
    static auto LuaGC = []()
    {
        PROF_EVENT("seqLuaGC");
        // Do at least once
        do
        {
            Device.LuaGCCount++;
            if (Device.LuaGC() == 1) // 1 informs that GC cycle is complete
            {
                Device.LuaGCDone = true;
                break;
            }

        } while (Device.isRendering && Device.LuaGCCount < psLua_ParallelGC_CallAmount);
    };
    if (psLua_ParallelGC && Device.LuaGC)
        Device.secondary_tasks.run(LuaGC);

	{
		PROF_EVENT("seqFrameMT");
		Device.seqFrameMT.Process(rp_Frame);
	}
}
