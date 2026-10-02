"""
IBPY: ib_preview_idris_fixed.py

Places ONE instance of the newly fixed Ms_Idris_Fixed mesh in the current
level so you can actually look at her -- her fixed bounds came back
97.9 cm tall, which is about half a typical adult, and I'd rather you
eyeball her in the viewport than have me guess whether that's a real
proportions issue or just how this particular model came out.

Spawns her at world origin as 'NPC_Idris_FIXED_PREVIEW', standing upright
(identity rotation). Doesn't touch anything else, doesn't wire her into
any director yet.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_preview_idris_fixed.py"
Then look at her in the viewport (search 'NPC_Idris_FIXED_PREVIEW' in the
World Outliner and focus on her with F) and tell me what you see --
proportioned correctly but just short, or still looks wrong/tiny/distorted.
"""

import unreal

MESH_PATH = "/Game/Characters/NPCs/MsIdris/Ms_Idris_Fixed"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== PREVIEW FIXED IDRIS ====")

    mesh = unreal.load_asset(MESH_PATH)
    if mesh is None:
        log(f"ERROR: could not load {MESH_PATH}")
        return

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = actor_subsystem.spawn_actor_from_class(
        unreal.SkeletalMeshActor, unreal.Vector(x=0.0, y=0.0, z=0.0),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0)
    )
    if actor is None:
        log("ERROR: failed to spawn preview actor")
        return
    actor.set_actor_label("NPC_Idris_FIXED_PREVIEW")
    actor.skeletal_mesh_component.set_skeletal_mesh(mesh)

    loc = actor.get_actor_location()
    log(f"Placed 'NPC_Idris_FIXED_PREVIEW' at {loc}. Find her in the World Outliner, "
        f"select her, press F to focus the viewport, and tell me what she actually looks like.")
    log("==== DONE ====")


main()
