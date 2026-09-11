"""Read-only fortress lighting, water and material audit. Never saves packages."""
import unreal, json
from pathlib import Path
from collections import Counter

OUT = Path(unreal.Paths.project_saved_dir()) / "BastionPolish"
OUT.mkdir(parents=True, exist_ok=True)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/LevelPrototyping/CarrowGateGarrison")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

def props(obj, names):
    result = {}
    for name in names:
        try: result[name] = str(obj.get_editor_property(name))
        except Exception: pass
    return result

result = {"counts": dict(Counter(a.get_class().get_name() for a in actors)), "lighting": [], "water": [], "starts": [], "materials": {}}
for a in actors:
    label, cls = a.get_actor_label(), a.get_class().get_name()
    row = {"label": label, "class": cls, "location": str(a.get_actor_location()), "rotation": str(a.get_actor_rotation()), "hidden": str(a.get_editor_property("hidden"))}
    if isinstance(a, unreal.PlayerStart): result["starts"].append(row)
    if isinstance(a, unreal.PostProcessVolume):
        row.update(props(a, ["priority", "unbound", "enabled"]))
        s = a.get_editor_property("settings")
        row["settings"] = props(s, [n for n in dir(s) if any(k in n for k in ("exposure", "color_gain", "white_temp", "saturation", "contrast", "bloom", "vignette", "grain"))])
        result["lighting"].append(row)
    elif cls in ("DirectionalLight", "SkyLight", "ExponentialHeightFog", "SkyAtmosphere", "VolumetricCloud"):
        row["components"] = []
        for c in a.get_components_by_class(unreal.SceneComponent):
            row["components"].append({"class": c.get_class().get_name(), **props(c, ["intensity", "light_color", "use_temperature", "temperature", "real_time_capture", "source_type", "cubemap", "volumetric_scattering_intensity", "fog_density", "fog_inscattering_color", "directional_inscattering_color", "inscattering_color_cubemap", "volumetric_fog", "volumetric_fog_albedo", "fog_max_opacity", "fog_height_falloff", "start_distance", "material"])})
        result["lighting"].append(row)
    if cls.startswith("Water") or "Sea_Harbor" in label:
        row["components"] = [{"class": c.get_class().get_name(), **props(c, ["water_material", "visible", "hidden_in_game", "relative_location", "water_mesh_override", "far_distance_material", "tile_size", "extent_in_tiles", "tessellation_factor"])} for c in a.get_components_by_class(unreal.SceneComponent)]
        row.update(props(a, ["water_waves", "zone_extent"]))
        result["water"].append(row)
    if isinstance(a, unreal.StaticMeshActor):
        smc = a.static_mesh_component
        mats = [smc.get_material(i) for i in range(smc.get_num_materials())]
        paths = [m.get_path_name() if m else "" for m in mats]
        for m in mats:
            if m:
                key = m.get_path_name()
                result["materials"][key] = result["materials"].get(key, 0) + 1
        if any(k in (label + " ".join(paths)).lower() for k in ("water", "foam", "ocean", "surf")):
            row.update({"materials": paths, "mesh": str(smc.static_mesh), "scale": str(a.get_actor_scale3d()), "bounds": str(a.get_actor_bounds(False))})
            result["water"].append(row)

(OUT / "audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("BASTION AUDIT COMPLETE: " + str(OUT / "audit.json"))
