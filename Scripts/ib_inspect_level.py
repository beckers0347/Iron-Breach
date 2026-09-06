"""Read-only: open a level (arg via IB_LEVEL env or default) and dump the
lighting/atmosphere/post actors so the look-rig tunes what exists."""
import unreal, os
LEVEL = os.environ.get("IB_LEVEL", "/Game/LevelPrototyping/CarrowGateGarrison")
def log(m): unreal.log(f"IBPY: {m}")
log(f"=== inspecting {LEVEL} ===")
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
acts = unreal.EditorActorSubsystem().get_all_level_actors()
from collections import Counter
cnt = Counter(a.get_class().get_name() for a in acts)
key = ["PostProcessVolume","DirectionalLight","SkyAtmosphere","SkyLight",
       "ExponentialHeightFog","VolumetricCloud","PlayerStart","StaticMeshActor",
       "Landscape","LandscapeStreamingProxy","PointLight","SpotLight","RectLight"]
log(f"total actors: {len(acts)}")
for k in key:
    log(f"  {k}: {cnt.get(k,0)}")
log("--- other actor classes (top 15) ---")
for name,c in cnt.most_common(25):
    if name not in key:
        log(f"  {name}: {c}")
# details on the ones that matter
for a in acts:
    cn = a.get_class().get_name()
    if cn == "PostProcessVolume":
        try:
            log(f"PPV '{a.get_actor_label()}': unbound={a.get_editor_property('unbound')} priority={a.get_editor_property('priority')}")
        except Exception as e: log(f"PPV read err {e}")
    if cn == "DirectionalLight":
        comp = a.get_component_by_class(unreal.DirectionalLightComponent)
        if comp:
            log(f"Sun '{a.get_actor_label()}': intensity={comp.get_editor_property('intensity')} temp={comp.get_editor_property('temperature')} rot={a.get_actor_rotation()}")
    if cn == "ExponentialHeightFog":
        comp = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
        if comp:
            log(f"Fog '{a.get_actor_label()}': volumetric={comp.get_editor_property('volumetric_fog')} density={comp.get_editor_property('fog_density')}")
    if cn == "SkyLight":
        comp = a.get_component_by_class(unreal.SkyLightComponent)
        if comp:
            log(f"SkyLight '{a.get_actor_label()}': mobility={a.get_actor_label()} intensity={comp.get_editor_property('intensity')}")
log("=== INSPECT DONE ===")
