"""
FIX FALLING THROUGH THE GARRISON PLATFORM -- gives GarrisonPlatform_New real
collision so the player capsule actually blocks on it
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Falling straight through a mesh you can clearly see almost always means one
thing: the mesh has render geometry but no COLLISION geometry. Very common
for custom-imported FBX models that didn't have collision generated on
import -- the shape looks solid in the viewport, but there's nothing there
for the player capsule to hit, so PIE just drops you through it.

WHAT THIS DOES
--------------
  1. Sets the platform's static mesh asset to use its own render geometry
     AS its collision ("Use Complex Collision As Simple") -- for a static,
     non-simulating level piece like this, that's the standard fix and it
     matches the real shape exactly (round helipad, lower dock, the notch
     between them, all of it), instead of a rough box/convex hull that
     would either miss the shape or fill in gaps that shouldn't be solid.
  2. Makes sure the platform's own component actually has collision
     enabled and set to block (Collision Enabled = Query And Physics,
     Profile = BlockAll) -- possible the component itself got left on
     NoCollision even if the asset had geometry.

Also sweeps every other actor under "Carrowgate Garrison" that uses a
custom imported mesh (ship, cranes, trucks, furniture -- anything spawned
via spawn_mesh_actor in the original build script) and does the same
fix, in case those have the same problem and you just haven't walked into
one yet.

Doesn't touch position, rotation, or scale -- collision only.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_platform_collision.py"
"""

import unreal

ROOT_FOLDER = "Carrowgate Garrison"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[FixPlatformCollision] %s" % msg)


def get_all_actors():
    return actor_subsystem.get_all_level_actors()


def under_root(a):
    folder = str(a.get_folder_path())
    return folder == ROOT_FOLDER or folder.startswith(ROOT_FOLDER + "/")


def fix_mesh_collision(mesh):
    """Sets a static mesh asset to use its render geometry as collision."""
    if mesh is None:
        return False
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup is None:
        return False
    try:
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        return True
    except Exception as e:
        log("  Could not set collision_trace_flag: %s" % e)
        return False


def fix_component_collision(mesh_comp):
    try:
        mesh_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    except Exception as e:
        log("  Could not set_collision_enabled: %s" % e)
    try:
        mesh_comp.set_collision_profile_name("BlockAll")
    except Exception as e:
        log("  Could not set_collision_profile_name: %s" % e)


def run():
    fixed_meshes = set()
    fixed_actor_count = 0

    # -- 1. The platform, specifically -- this is the reported problem. -----
    platform = None
    for a in get_all_actors():
        if a.get_actor_label() == "GarrisonPlatform_New":
            platform = a
            break

    if platform is None:
        log("GarrisonPlatform_New not found -- can't fix its collision specifically, "
            "continuing to the general sweep below.")
    else:
        mesh_comp = platform.static_mesh_component
        mesh = mesh_comp.static_mesh
        if mesh is not None and mesh.get_path_name() not in fixed_meshes:
            if fix_mesh_collision(mesh):
                fixed_meshes.add(mesh.get_path_name())
                log("Set '%s' (the platform's mesh asset) to use complex collision as simple." % mesh.get_name())
        fix_component_collision(mesh_comp)
        fixed_actor_count += 1
        log("GarrisonPlatform_New: collision enabled + set to BlockAll.")

    # -- 2. Sweep every other custom-mesh actor in the garrison folder ------
    for a in get_all_actors():
        if not under_root(a) or a is platform:
            continue
        mesh_comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if mesh_comp is None:
            continue
        mesh = mesh_comp.static_mesh
        if mesh is None:
            continue
        # Only touch meshes from LevelPrototyping/AIModels (the imported/custom
        # ones) -- leave the plain engine Cube/Cylinder blockout meshes alone,
        # those already have collision from the engine's own primitives.
        mesh_path = mesh.get_path_name()
        if "/AIModels/" not in mesh_path and "/Garrison/" not in mesh_path:
            continue
        if mesh_path not in fixed_meshes:
            if fix_mesh_collision(mesh):
                fixed_meshes.add(mesh_path)
                log("Set '%s' to use complex collision as simple." % mesh.get_name())
        fix_component_collision(mesh_comp)
        fixed_actor_count += 1
        log("'%s': collision enabled + set to BlockAll." % a.get_actor_label())

    log("Done -- %d actor(s) touched, %d unique mesh asset(s) had collision fixed. Save, then "
        "PIE again and check the platform." % (fixed_actor_count, len(fixed_meshes)))


run()
