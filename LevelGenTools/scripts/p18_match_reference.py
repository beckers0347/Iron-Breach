"""p18_match_reference.py - tweaks the existing level to match Reference/Thornfield (golden-hour forest garrison).
Edits actors in place (found by class / label prefix), then saves. Stages via env IB_P18_STAGES (default: all).
NOTE: unreal.Color positional args are (b, g, r, a) - always use keywords.
"""
import os, math, random
import unreal

LEVEL = "/Game/IronBreach/Thornfield/Levels/L_ThornfieldGarrison"
STAGES = [s for s in os.environ.get("IB_P18_STAGES", "light,hide,ground,rocks,trees,fog,slabs,props").split(",") if s]
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(m):
    unreal.log("[Thornfield] p18: " + m)


def col(r, g, b):
    return unreal.Color(r=int(r * 255), g=int(g * 255), b=int(b * 255), a=255)


def lin(r, g, b):
    return unreal.LinearColor(r, g, b, 1.0)


def setp(o, n, v):
    try:
        o.set_editor_property(n, v); return True
    except Exception as e:
        log("could not set %s: %r" % (n, e)); return False


def actors(cls):
    return [a for a in EAS.get_all_level_actors() if a.get_class().get_name() == cls]


def dedupe():
    for cls in ("DirectionalLight", "SkyLight", "SkyAtmosphere", "ExponentialHeightFog", "PostProcessVolume"):
        al = actors(cls)
        for a in al[1:]:
            log("deleting duplicate %s %s" % (cls, a.get_actor_label()))
            EAS.destroy_actor(a)


def stage_light():
    dedupe()
    for a in actors("DirectionalLight"):
        c = a.get_component_by_class(unreal.DirectionalLightComponent)
        setp(c, "light_color", col(1.0, 0.84, 0.64))
        setp(c, "intensity", 22.0)
        setp(c, "light_source_angle", 2.5)
        a.set_actor_rotation(unreal.Rotator(roll=0, pitch=-20.0, yaw=-22.5), False)
        log("sun set")
    for a in actors("SkyLight"):
        c = a.get_component_by_class(unreal.SkyLightComponent)
        setp(c, "light_color", col(0.82, 0.88, 1.0))
        setp(c, "intensity", 1.3)
    for a in actors("ExponentialHeightFog"):
        c = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
        setp(c, "fog_inscattering_luminance", lin(0.50, 0.52, 0.48))
        setp(c, "directional_inscattering_luminance", lin(0.55, 0.40, 0.25))
        setp(c, "fog_density", 0.010)
    for a in EAS.get_all_level_actors():
        if a.get_actor_label().startswith("POLELIGHT_"):
            c = a.get_component_by_class(unreal.PointLightComponent)
            setp(c, "light_color", col(1.0, 0.82, 0.55))
    for a in actors("PostProcessVolume"):
        s = a.get_editor_property("settings")
        setp(s, "color_gain", unreal.Vector4(1.0, 1.0, 0.97, 1.0))
        setp(s, "override_color_gain", True)
        setp(s, "override_color_saturation", True)
        setp(s, "color_saturation", unreal.Vector4(0.92, 0.92, 0.92, 1.0))
        a.set_editor_property("settings", s)


import sys, importlib
sys.path.insert(0, "X:/IronBreach/LevelGenTools/scripts")
import p18_stages
importlib.reload(p18_stages)
for st in STAGES:
    log("stage " + st)
    (globals().get("stage_" + st) or getattr(p18_stages, "stage_" + st))()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "ThornfieldGarrison" in world.get_path_name(), "wrong world loaded: " + world.get_path_name()
r1 = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
log("save_current_level -> %s (%s)" % (r1, world.get_path_name()))
