"""
IBPY: ib_sync_npcs_to_infantry_skeleton.py

Now that Ms_Idris_Infantry is confirmed bound to the real Infantry skeleton
(Base_Character_Mesh_Skeleton) at the right scale, this switches everything
currently using an older Idris mesh over to it, so the whole NPC set is
consistent and animation-ready:

  - NPC_Rhodes_PLACEHOLDER
  - NPC_Okafor_Bricks_PLACEHOLDER
  - NPC_Yun_Static_PLACEHOLDER
  - NPC_Idris_FIXED_PREVIEW  -> relabeled to NPC_Idris (she's no longer a
    scale-check preview, she's the real placeholder now)

Only swaps the mesh each actor's component points at -- doesn't move,
rescale, or re-spawn any of them, so their current positions and the
Act1BarracksDirector.SquadNPCs / Act2EscalationDirector.DistrictNPCs wiring
(which references the actor objects themselves, not their meshes) stay
intact. Confirms that wiring is still correct at the end as a sanity check.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_sync_npcs_to_infantry_skeleton.py"
Paste back the full output.
"""

import unreal

NEW_MESH_PATH = "/Game/Characters/NPCs/MsIdris/Ms_Idris_Infantry"

ACTOR_LABELS = [
    "NPC_Rhodes_PLACEHOLDER",
    "NPC_Okafor_Bricks_PLACEHOLDER",
    "NPC_Yun_Static_PLACEHOLDER",
    "NPC_Idris_FIXED_PREVIEW",
]

DIRECTOR_WIRING = [
    ("Act1BarracksDirector", "SquadNPCs"),
    ("Act2EscalationDirector", "DistrictNPCs"),
]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== SYNC ALL NPC PLACEHOLDERS TO Ms_Idris_Infantry ====")

    new_mesh = unreal.load_asset(NEW_MESH_PATH)
    if new_mesh is None:
        log(f"ERROR: could not load {NEW_MESH_PATH}")
        return

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()
    by_label = {a.get_actor_label(): a for a in all_actors}

    updated = []
    for label in ACTOR_LABELS:
        actor = by_label.get(label)
        if actor is None:
            log(f"  '{label}' not found in this level -- skipped.")
            continue
        actor.skeletal_mesh_component.set_skinned_asset_and_update(new_mesh)
        if label == "NPC_Idris_FIXED_PREVIEW":
            actor.set_actor_label("NPC_Idris")
            log(f"  Updated '{label}' -> mesh swapped, relabeled to 'NPC_Idris'")
        else:
            log(f"  Updated '{label}' -> mesh swapped to Ms_Idris_Infantry")
        updated.append(label)

    log(f"---- {len(updated)}/{len(ACTOR_LABELS)} actors updated ----")

    log("---- Confirming director wiring is still intact ----")
    all_actors = actor_subsystem.get_all_level_actors()
    for cls_name, prop_name in DIRECTOR_WIRING:
        matches = [a for a in all_actors if a.get_class().get_name() == cls_name]
        if not matches:
            log(f"  {cls_name} not found in this level.")
            continue
        director = matches[0]
        try:
            val = director.get_editor_property(prop_name)
            log(f"  {cls_name}.{prop_name}: {len(val)} entr(y/ies) -> {[a.get_actor_label() for a in val]}")
        except Exception as e:
            log(f"  ERROR reading {cls_name}.{prop_name}: {e}")

    log("==== DONE. Save the level once this looks right. ====")


main()
