"""
IBPY: ib_hangar_lights.py -- interior + exterior lighting for the Hangar_04 (run AFTER ib_place_hangar.py).

  py "X:/IronBreach/Scripts/ib_hangar_lights.py"

Interior: 12 emissive ceiling panels (matching the mesh's light panels) + 6 point lights (high ceiling, 14 m,
so a few strong lights read better than twelve weak ones). Exterior: lamp lights at the front/side/rear lamps.
Everything is tagged IB_Hangar04 + IB_Hangar04_Light, attached to the building, and replaced on re-run.
Nothing is saved. Too dark/bright: LIGHT_LUMENS / EXT_LUMENS. Too slow: CAST_SHADOWS = False.
"""
import unreal

TAG, LIGHT_TAG = "IB_Hangar04", "IB_Hangar04_Light"
BUILDING_MESH_NAME = "SM_Hangar_04"
FOLDER = "Carrowgate Garrison/Hangar Lights"
WARM = unreal.Color(255, 222, 168, 255)      # LightColor is an FColor, not a LinearColor
LIGHT_LUMENS = 9000.0
ATTENUATION = 2200.0
CAST_SHADOWS = True
EXT_LUMENS, EXT_ATTENUATION = 1500.0, 900.0
POINT_Z = 11.2
PANELS = [(x, y, 12.8) for x in (-8.0, -3.0, 2.0, 7.0) for y in (-5.5, 0.0, 5.5)]       # Blender metres
POINT_LIGHTS = [(x, y, POINT_Z) for x in (-6.0, 3.0, 8.0) for y in (-6.0, 6.0)]
EXT = [(-14.4, -5.0, 10.4), (-14.4, 5.0, 10.4), (-10.0, -15.4, 2.9), (-10.0, 15.4, 2.9), (-6.0, -15.4, 2.9),
       (-6.0, 15.4, 2.9), (3.0, -15.0, 4.0), (3.0, 15.0, 4.0), (14.1, -9.6, 2.9), (14.1, 0.0, 3.4), (14.1, 9.6, 2.9)]


def log(m): unreal.log(f"IBPY: {m}")
def warn(m): unreal.log_warning(f"IBPY: WARNING -- {m}")
def bl(p): return unreal.Vector(p[0] * 100.0, -p[1] * 100.0, p[2] * 100.0)


def tag_attach(a, b):
    a.set_editor_property("tags", [unreal.Name(TAG), unreal.Name(LIGHT_TAG)])
    try:
        a.set_folder_path(FOLDER)
    except Exception:
        pass
    a.attach_to_actor(b, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                      unreal.AttachmentRule.KEEP_WORLD, False)


def setp(o, k, v):
    try:
        o.set_editor_property(k, v)
    except Exception as e:
        warn(f"could not set {k}: {e}")


def point(sub, b, p, lumens, atten, shadows, label):
    w = b.get_actor_transform().transform_location(bl(p))
    a = sub.spawn_actor_from_class(unreal.PointLight, w, unreal.Rotator(0, 0, 0))
    if not a:
        warn(f"could not spawn {label}")
        return None
    c = a.get_editor_property("light_component")
    try:
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
    except Exception as e:
        warn(f"mobility: {e}")
    setp(c, "intensity_units", unreal.LightUnits.LUMENS)
    setp(c, "intensity", lumens)
    setp(c, "light_color", WARM)
    setp(c, "attenuation_radius", atten)
    setp(c, "source_radius", 40.0 if shadows else 4.0)
    setp(c, "cast_shadows", shadows)
    a.set_actor_label(label)
    tag_attach(a, b)
    return a


def main():
    log("=== ib_hangar_lights START ===")
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()
    b = next((a for a in actors if isinstance(a, unreal.StaticMeshActor) and TAG in [str(t) for t in a.tags]
              and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name() == BUILDING_MESH_NAME), None)
    if not b:
        warn("hangar (tag IB_Hangar04, mesh SM_Hangar_04) not found -- run ib_place_hangar.py first.")
        return
    n = 0
    for a in actors:
        if LIGHT_TAG in [str(t) for t in a.tags]:
            sub.destroy_actor(a)
            n += 1
    log(f"removed {n} previous light actor(s)")
    # The mesh already contains the emissive panels (Light_Strip material); these are only the light sources.
    k = 0
    for p in POINT_LIGHTS:
        if point(sub, b, p, LIGHT_LUMENS, ATTENUATION, CAST_SHADOWS, f"Hangar_Light_{k:02d}"):
            k += 1
    e = 0
    for p in EXT:
        if point(sub, b, p, EXT_LUMENS, EXT_ATTENUATION, False, f"Hangar_LampLight_{e:02d}"):
            e += 1
    log(f"=== DONE: {k} interior point lights, {e} exterior lamp lights. Nothing saved. ===")


main()
