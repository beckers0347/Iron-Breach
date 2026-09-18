"""
IBPY: ib_complex_collision.py

Replaces the earlier approach -- invisible BlockingVolume shells trying to
approximate each building's interior/exterior with boxes, octagons, outer
caps, etc. -- with a much simpler one: turn on REAL collision on the
Tripo3D exterior mesh itself, set to "Use Complex Collision As Simple".
This makes the player collide with the mesh's own actual triangles, so
every dish, pod, antenna, and the room's real (possibly non-rectangular)
shape is automatically solid exactly where it visually is, and open
exactly where the mesh itself has an opening (the modeled doorway) -- no
more manual box/octagon math trying to approximate a shape that was never
a box to begin with.

This does NOT touch the meshes' geometry, and does NOT spawn or delete any
actors -- it only flips a collision setting on each building's StaticMesh
ASSET (collision_trace_flag = CTF_USE_COMPLEX_AS_SIMPLE, which affects
every placed instance of that mesh) and enables blocking query collision
on each building's exterior mesh COMPONENT (previously NO_COLLISION).

CAVEATS TO WATCH FOR WHEN YOU TEST:
  - If a Tripo mesh isn't a clean, reasonably watertight shell (stray
    disconnected geometry, inverted normals, self-intersections), complex
    collision can behave oddly in spots -- inspect each building in PIE
    rather than assuming it's perfect everywhere.
  - If these meshes are Nanite-enabled, complex collision uses the
    auto-generated Nanite fallback mesh -- should just work, but is worth
    knowing if something looks off.
  - Complex collision is a bit more expensive per-query than simple
    primitives, but for a handful of static, non-moving buildings a player
    walks around, this is a total non-issue.

HOW TO RUN:
  In the Unreal Editor Python console (the "Cmd" bar at the bottom):
    py "X:/IronBreach/Scripts/ib_complex_collision.py"
  Then walk into each building in PIE and check that walls/dish/pod block
  you and the doorway itself is open. This script saves the modified
  StaticMesh assets itself -- you only need to save the level (Ctrl+S)
  once you're happy.
"""

import unreal

BUILDINGS = [
    {"prefix": "07_Armory", "exterior_actor": "SM_Armory_Tripo"},
    {"prefix": "08_Command & Comms", "exterior_actor": "SM_Command_Tripo"},
    {"prefix": "06_Mess Hall", "exterior_actor": "SM_MessHall_Tripo"},
]

COLLISION_PROFILE = "BlockAll"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_actor_by_label(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsystem.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def main():
    log(f"Switching {len(BUILDINGS)} building(s) to complex-collision-as-simple.")
    dirty_packages = []
    results = []

    for building in BUILDINGS:
        prefix = building["prefix"]
        label = building["exterior_actor"]
        actor = get_actor_by_label(label)
        if not actor:
            log(f"[{prefix}] SKIPPED -- exterior actor '{label}' not found.")
            results.append((prefix, False))
            continue

        mesh_comp = getattr(actor, "static_mesh_component", None) or actor.get_component_by_class(unreal.StaticMeshComponent)
        if not mesh_comp:
            log(f"[{prefix}] SKIPPED -- exterior actor has no static mesh component.")
            results.append((prefix, False))
            continue

        static_mesh = mesh_comp.get_editor_property("static_mesh")
        if not static_mesh:
            log(f"[{prefix}] SKIPPED -- static mesh component has no assigned mesh.")
            results.append((prefix, False))
            continue

        body_setup = static_mesh.get_editor_property("body_setup")
        if body_setup:
            before = body_setup.get_editor_property("collision_trace_flag")
            static_mesh.modify()
            body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            saved = unreal.EditorAssetLibrary.save_loaded_asset(static_mesh)
            dirty_packages.append((static_mesh.get_path_name(), saved))
            log(f"[{prefix}] StaticMesh '{static_mesh.get_name()}' collision_trace_flag: {before} -> CTF_USE_COMPLEX_AS_SIMPLE (saved={saved})")
        else:
            log(f"[{prefix}] WARNING -- StaticMesh '{static_mesh.get_name()}' has no BodySetup; couldn't set collision_trace_flag.")

        mesh_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        mesh_comp.set_collision_profile_name(COLLISION_PROFILE)
        # Note: no explicit "recreate physics state" call here -- that method
        # isn't exposed to Python on this component type, but set_collision_*
        # already triggers the engine's own component re-registration under
        # the hood, so the change takes effect immediately without it.

        log(f"[{prefix}] '{label}' collision_enabled=QueryOnly profile='{COLLISION_PROFILE}'.")
        results.append((prefix, True))

    log("---- SUMMARY ----")
    for prefix, ok in results:
        log(f"{prefix}: {'OK' if ok else 'SKIPPED/FAILED'}")
    for path, saved in dirty_packages:
        log(f"StaticMesh asset {'saved' if saved else 'FAILED TO SAVE'}: {path}")
    log("Test by walking into each building in PIE, then save the level (Ctrl+S) -- the mesh assets above were already saved by this script.")


main()
