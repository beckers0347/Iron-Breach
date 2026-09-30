"""
IBPY: ib_revert_complex_collision.py

Quick undo for ib_complex_collision.py. Diagnosis: these Tripo3D meshes are
solid, CLOSED shells -- the door you see is decoration (a separate door
mesh/frame sitting in front of a wall), not an actual cut hole through the
building's own geometry. So "Use Complex Collision As Simple" made the
entire shell solid everywhere, doorway included, which is why none of the
three buildings could be walked into at all.

This just flips collision back off on the three exterior mesh COMPONENTS
(NoCollision, same as before ib_complex_collision.py ran) so you can walk
around again immediately while we pick the next approach. It leaves the
StaticMesh ASSETS' collision_trace_flag as CTF_USE_COMPLEX_AS_SIMPLE --
harmless to leave set, since a component with NoCollision never queries it
-- but flip that back too if you'd rather have it fully back to original.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_revert_complex_collision.py"
"""

import unreal

BUILDINGS = [
    {"prefix": "07_Armory", "exterior_actor": "SM_Armory_Tripo"},
    {"prefix": "08_Command & Comms", "exterior_actor": "SM_Command_Tripo"},
    {"prefix": "06_Mess Hall", "exterior_actor": "SM_MessHall_Tripo"},
]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_actor_by_label(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsystem.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def main():
    log("Reverting exterior mesh collision back to NoCollision on 3 building(s).")
    for building in BUILDINGS:
        prefix = building["prefix"]
        label = building["exterior_actor"]
        actor = get_actor_by_label(label)
        if not actor:
            log(f"[{prefix}] SKIPPED -- exterior actor '{label}' not found.")
            continue
        mesh_comp = getattr(actor, "static_mesh_component", None) or actor.get_component_by_class(unreal.StaticMeshComponent)
        if not mesh_comp:
            log(f"[{prefix}] SKIPPED -- exterior actor has no static mesh component.")
            continue
        mesh_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        log(f"[{prefix}] '{label}' collision_enabled -> NoCollision.")
    log("Done. Buildings are walk-through again (no collision at all right now) until we pick the next approach.")


main()
