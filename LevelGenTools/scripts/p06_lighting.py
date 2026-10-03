"""p06_lighting.py - Phase 6: golden-hour/dusk lighting, atmosphere, fog, post-process, interior lights.

Run (after p05):   py "X:/IronBreach/LevelGenTools/scripts/p06_lighting.py"

Spawns (all tagged GEN_Phase6, replaced on every run):
  Sun (DirectionalLight, WSW, low), SkyAtmosphere, SkyLight (real-time capture), ExponentialHeightFog (volumetric),
  an unbound PostProcessVolume (manual exposure, bloom, Lumen GI + reflections) and one PointLight per entry in
  every building's JSON "lights" list (amber / blue / white / red), placed at the building's world transform.

Look for:
  [Thornfield] VERIFY: sun PASS
  [Thornfield] VERIFY: atmosphere PASS
  [Thornfield] VERIFY: fog PASS
  [Thornfield] VERIFY: post_process PASS
  [Thornfield] VERIFY: interior_lights PASS (<n> lights)
"""
import os
import sys
import json
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)

PHASE = 6
WHITE = [1.0, 0.92, 0.80]
RED = [1.0, 0.1, 0.05]


def _color(rgb):
    return unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)


def _set(obj, prop, val, label=None):
    """set_editor_property that logs a warning instead of raising."""
    try:
        obj.set_editor_property(prop, val)
        return True
    except Exception as e:
        G.warn("Could not set %s%s: %r" % (label + "." if label else "", prop, e))
        return False


def _rot(x, y, yaw_deg):
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    return x * c - y * s, x * s + y * c


def main():
    G.init_log("p06_lighting")
    try:
        level = G.load_json("level.json")
        assets = G.load_json("assets.json")
        layout = G.load_json("layout.json")
        cfg = G.load_json("lighting.json")
        b = level["bounds_cm"]
        cx, cy = (b["min"][0] + b["max"][0]) / 2.0, (b["min"][1] + b["max"][1]) / 2.0
        zt = level["base_plateau_z"]

        G.cleanup_phase(PHASE)

        # ---------------------------------------------------------------- sun
        s = cfg["sun"]
        # compass direction the sun is IN -> direction light travels (opposite) -> UE yaw (north=-Y, east=+X)
        travel = (s["from_compass_deg"] + 180.0) % 360.0
        ue_dir_x, ue_dir_y = math.sin(math.radians(travel)), -math.cos(math.radians(travel))
        sun_yaw = math.degrees(math.atan2(ue_dir_y, ue_dir_x))
        sun = G.spawn_by_class(unreal.DirectionalLight, (cx, cy, 20000.0), (s["pitch_deg"], sun_yaw, 0), "Sun_GoldenHour", PHASE)
        sc = sun.get_component_by_class(unreal.DirectionalLightComponent)
        sc.set_editor_property("intensity", float(s["intensity_lux"]))
        sc.set_editor_property("light_color", unreal.Color(r=int(s["color_rgb"][0] * 255), g=int(s["color_rgb"][1] * 255), b=int(s["color_rgb"][2] * 255), a=255))
        _set(sc, "light_source_angle", float(s["source_angle_deg"]), "sun")
        _set(sc, "atmosphere_sun_light", True, "sun")
        G.log("Sun: pitch %.1f, yaw %.1f (sun in the %.1f compass direction), %.1f lux" % (s["pitch_deg"], sun_yaw, s["from_compass_deg"], s["intensity_lux"]))
        G.verify("sun", sc.get_editor_property("intensity") > 0.0, "%.1f lux, yaw %.1f" % (s["intensity_lux"], sun_yaw))

        # ---------------------------------------------------------------- atmosphere + sky light
        atm = G.spawn_by_class(unreal.SkyAtmosphere, (cx, cy, zt), (0, 0, 0), "SkyAtmosphere", PHASE)
        sk = G.spawn_by_class(unreal.SkyLight, (cx, cy, zt + 5000.0), (0, 0, 0), "SkyLight", PHASE)
        skc = sk.get_component_by_class(unreal.SkyLightComponent)
        _set(skc, "intensity", float(cfg["sky_light"]["intensity"]), "skylight")
        sc_col = cfg["sky_light"].get("color_rgb")
        if sc_col:
            _set(skc, "light_color", unreal.Color(r=int(sc_col[0] * 255), g=int(sc_col[1] * 255), b=int(sc_col[2] * 255), a=255), "skylight")
        _set(skc, "real_time_capture", bool(cfg["sky_light"]["real_time_capture"]), "skylight")
        G.verify("atmosphere", atm is not None and sk is not None, "SkyAtmosphere + SkyLight (real-time capture)")

        # ---------------------------------------------------------------- fog
        f = cfg["fog"]
        fog = G.spawn_by_class(unreal.ExponentialHeightFog, (cx, cy, zt + 200.0), (0, 0, 0), "HeightFog", PHASE)
        fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
        _set(fc, "fog_density", float(f["density"]), "fog")
        _set(fc, "fog_height_falloff", float(f["falloff"]), "fog")
        _set(fc, "start_distance", float(f["start_distance_cm"]), "fog")
        names = [n for n in dir(fc) if not n.startswith("_")]
        G.log("Fog properties available: %s" % [n for n in names if any(k in n for k in ("volumetric", "inscatter"))])
        for cands, val in ((["fog_inscattering_luminance", "fog_inscattering_color"], _color(f["color_rgb"])),
                           (["volumetric_fog", "enable_volumetric_fog"], bool(f["volumetric"])),
                           (["volumetric_fog_scattering_distribution", "volumetric_fog_distribution_contribution"], float(f.get("volumetric_distribution", 0.9)))):
            hit = next((n for n in cands if n in names), None)
            if hit:
                _set(fc, hit, val, "fog")
            else:
                G.warn("No fog property found among %s" % cands)
        G.verify("fog", abs(fc.get_editor_property("fog_density") - f["density"]) < 1e-6,
                 "density %.3f falloff %.2f volumetric %s" % (f["density"], f["falloff"], f["volumetric"]))

        # ---------------------------------------------------------------- post process
        pp = cfg["post_process"]
        ppv = G.spawn_by_class(unreal.PostProcessVolume, (cx, cy, zt + 1000.0), (0, 0, 0), "PPV_Global", PHASE)
        _set(ppv, "unbound", bool(pp["unbound"]), "ppv")
        st = ppv.get_editor_property("settings")
        if pp["exposure_method"] == "manual":
            _set(st, "override_auto_exposure_method", True, "pp")
            _set(st, "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL, "pp")
        else:
            _set(st, "override_auto_exposure_method", True, "pp")
            _set(st, "auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM, "pp")
            _set(st, "override_auto_exposure_min_brightness", True, "pp")
            _set(st, "auto_exposure_min_brightness", float(pp.get("auto_min_brightness", 0.5)), "pp")
            _set(st, "override_auto_exposure_max_brightness", True, "pp")
            _set(st, "auto_exposure_max_brightness", float(pp.get("auto_max_brightness", 6.0)), "pp")
        _set(st, "override_auto_exposure_bias", True, "pp")
        _set(st, "auto_exposure_bias", float(pp["exposure_compensation"]), "pp")
        _set(st, "override_bloom_intensity", True, "pp")
        _set(st, "bloom_intensity", float(pp["bloom_intensity"]), "pp")
        if pp.get("color_gain"):
            g = pp["color_gain"]
            _set(st, "override_color_gain", True, "pp")
            _set(st, "color_gain", unreal.Vector4(g[0], g[1], g[2], g[3]), "pp")
        if pp.get("saturation"):
            v = float(pp["saturation"])
            _set(st, "override_color_saturation", True, "pp")
            _set(st, "color_saturation", unreal.Vector4(v, v, v, 1.0), "pp")
        if pp.get("contrast"):
            v = float(pp["contrast"])
            _set(st, "override_color_contrast", True, "pp")
            _set(st, "color_contrast", unreal.Vector4(v, v, v, 1.0), "pp")
        if pp.get("lumen_gi"):
            _set(st, "override_dynamic_global_illumination_method", True, "pp")
            _set(st, "dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN, "pp")
        if pp.get("lumen_reflections"):
            _set(st, "override_reflection_method", True, "pp")
            _set(st, "reflection_method", unreal.ReflectionMethod.LUMEN, "pp")
        ppv.set_editor_property("settings", st)
        got = ppv.get_editor_property("unbound")
        G.verify("post_process", bool(got) == bool(pp["unbound"]),
                 "unbound=%s, %s exposure, bloom %.1f, Lumen GI/reflections" % (got, pp["exposure_method"], pp["bloom_intensity"]))

        # ---------------------------------------------------------------- interior lights
        il = cfg["interior_lights"]
        palette = {"amber": (il["amber_rgb"], il["amber_intensity_cd"]),
                   "blue": (il["blue_rgb"], il["blue_intensity_cd"]),
                   "white": (WHITE, il["amber_intensity_cd"]),
                   "red": (RED, il["blue_intensity_cd"])}
        expected, placed, outside = 0, 0, 0
        counts = {}
        for st_ in layout["structures"]:
            entry = assets["buildings"][st_["asset"]]
            jpath = os.path.join(G.project_dir(), entry["door_json"].replace("/", os.sep))
            with open(jpath, "r", encoding="utf-8") as fh:
                lights = json.load(fh).get("lights", [])
            wx, wy = G.plan_to_world(level, st_["pos"][0], st_["pos"][1])
            yaw = G.facing_to_yaw(layout, st_["facing"], st_["yaw_offset_deg"], level["mesh_native_front_yaw_deg"])
            for i, (kind, pos) in enumerate(lights):
                expected += 1
                rgb, cd = palette.get(kind, palette["white"])
                lx, ly, lz = pos[0] * 100.0, -pos[1] * 100.0, pos[2] * 100.0
                rx, ry = _rot(lx, ly, yaw)
                x, y, z = wx + rx, wy + ry, zt + lz
                if not (b["min"][0] <= x <= b["max"][0] and b["min"][1] <= y <= b["max"][1]):
                    outside += 1
                a = G.spawn_by_class(unreal.PointLight, (x, y, z), (0, 0, 0), "LIGHT_%s_%02d_%s" % (st_["label"], i, kind), PHASE)
                c = a.get_component_by_class(unreal.PointLightComponent)
                _set(c, "intensity_units", unreal.LightUnits.CANDELAS, "light")
                _set(c, "intensity", float(cd), "light")
                _set(c, "light_color", unreal.Color(r=int(rgb[0] * 255), g=int(rgb[1] * 255), b=int(rgb[2] * 255), a=255), "light")
                _set(c, "attenuation_radius", float(il["attenuation_cm"]), "light")
                _set(c, "cast_shadows", bool(il.get("all_cast_shadows", False)) or kind in ("amber", "red"), "light")   # shadows stop interior light leaking through walls
                placed += 1
                counts[kind] = counts.get(kind, 0) + 1
        G.log("Interior lights by colour: %s" % counts)
        G.verify("interior_lights", placed == expected and expected > 0 and outside == 0,
                 "%d lights (expected %d), %d outside bounds" % (placed, expected, outside))

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p06_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p06_unexpected", False, repr(e))
    G.summary()


main()
