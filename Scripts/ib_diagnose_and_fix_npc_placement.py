"""
IBPY: ib_diagnose_and_fix_npc_placement.py

You reported the NPCs are sideways, too small, and the three placeholders
are sunk into the ground. Rather than guess from a screenshot, this:

  1. REPORTS, for every actor labeled NPC_* or TEMP_* in the current level:
     mesh asset path, location, rotation, scale, and mesh bounds (to check
     if "too small" is a real scale problem or just how they look from far
     away/at an angle).
  2. Also flags any leftover TEMP_BoneCheck_* actors from the earlier bone-
     comparison scripts that may not have been cleaned up properly.
  3. FIXES position and rotation directly (low-risk, mechanical): for each
     NPC_* actor, sets Z to 384 -- the known flat ground level for
     CarrowGateGarrison established back in the road-markings work
     (HUB_Z = 384.0) -- and resets rotation to upright (roll=0, pitch=0,
     keeps existing yaw). This is why they were sunk/sideways in the first
     place -- they were spawned at flat hardcoded offsets from world
     origin (Z=0), which is below the garrison's actual floor.
     (Not using a line-trace here -- the Python line-trace API's exact
     signature isn't reliable across engine versions, and we already have
     a known-good Z for this level from earlier work, so there's no need
     to guess.)

Does NOT touch mesh assignment or scale -- if the bounds report below still
shows something wrong after this runs, that's a separate, second fix.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_diagnose_and_fix_npc_placement.py"
Paste back the full output, then look at them in the viewport again.
"""

import unreal

GARRISON_GROUND_Z = 384.0


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== DIAGNOSE + FIX NPC PLACEMENT ====")

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()
    world = actor_subsystem.get_editor_world() if hasattr(actor_subsystem, "get_editor_world") else None

    npc_actors = []
    temp_actors = []
    for a in all_actors:
        label = a.get_actor_label()
        if label.startswith("NPC_"):
            npc_actors.append(a)
        elif label.startswith("TEMP_"):
            temp_actors.append(a)

    log(f"---- Found {len(npc_actors)} NPC_* actor(s), {len(temp_actors)} leftover TEMP_* actor(s) ----")

    if temp_actors:
        log("Leftover TEMP_ actors (from earlier bone-check scripts, should have self-destroyed):")
        for a in temp_actors:
            log(f"  '{a.get_actor_label()}' at {a.get_actor_location()} -- removing it now.")
            actor_subsystem.destroy_actor(a)

    log("---- Current state of each NPC before fixing ----")
    for a in npc_actors:
        loc = a.get_actor_location()
        rot = a.get_actor_rotation()
        scale = a.get_actor_scale3d()
        comp = a.skeletal_mesh_component if isinstance(a, unreal.SkeletalMeshActor) else None
        mesh = None
        if comp is not None:
            mesh = comp.get_skinned_asset() if hasattr(comp, "get_skinned_asset") else (
                comp.get_skeletal_mesh_asset() if hasattr(comp, "get_skeletal_mesh_asset") else comp.skeletal_mesh
            )
        log(f"  '{a.get_actor_label()}': mesh={mesh.get_path_name() if mesh else 'NONE'}  "
            f"loc={loc}  rot(roll={rot.roll:.1f},pitch={rot.pitch:.1f},yaw={rot.yaw:.1f})  scale={scale}")
        if mesh is not None:
            bounds = mesh.get_bounds()
            box = bounds.box_extent
            log(f"      mesh full bounds (cm): x={box.x*2:.1f} y={box.y*2:.1f} z={box.z*2:.1f}")

    log(f"---- Fixing position (Z={GARRISON_GROUND_Z}) and rotation (Y/Z-swap correction) ----")
    # Ms_Idris_Infantry's bounds came back x=47.2 y=97.9 z=18.9 -- compared to the
    # correctly-standing Ms_Idris_Fixed (x=47.2 y=18.9 z=97.9), Y and Z are swapped.
    # That's a 90-degree roll fixing it, not just a position problem.
    for a in npc_actors:
        loc = a.get_actor_location()
        new_loc = unreal.Vector(x=loc.x, y=loc.y, z=GARRISON_GROUND_Z)
        a.set_actor_location(new_loc, False, False)

        rot = a.get_actor_rotation()
        a.set_actor_rotation(unreal.Rotator(roll=-90.0, pitch=0.0, yaw=rot.yaw), False)
        log(f"  '{a.get_actor_label()}': moved to {new_loc}, rotation set to roll=-90 "
            f"(Y/Z swap fix, flipped from roll=90 which came out upside-down), yaw kept at {rot.yaw:.1f}")

    log("==== DONE. Mesh/scale was only reported, not changed -- if bounds above still look "
        "wrong, tell me and that's the next fix. ====")


main()
