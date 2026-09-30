"""
IBPY: ib_delete_old_blockout.py

Deletes the OLD placeholder blockout wall/ceiling pieces for buildings whose
new Tripo3D exterior mesh + interior BlockingVolume collision shell has
already been placed and verified. Furniture, fixtures, lights, door frames,
the new Tripo mesh, the new collision volumes, and any unrelated actors
(e.g. shoreline geometry) are explicitly NOT touched -- only the exact
labels listed below are deleted.

HOW TO RUN:
  py "X:\\IronBreach\\Scripts\\ib_delete_old_blockout.py"
"""

import unreal

# Exact old blockout actor labels to delete, per building. Compiled from the
# ib_inspect_buildings.py inventory. Doors, furniture, lights, the new
# SM_*_Tripo mesh, and the new *_Collision_* BlockingVolumes are deliberately
# excluded from these lists.
DELETE_LABELS = {
    "Command & Comms": [
        "08_Command & Comms_Wall_N_L",
        "08_Command & Comms_Wall_N_R",
        "08_Command & Comms_Wall_N_Fill0",
        "08_Command & Comms_Wall_N_Glass0",
        "08_Command & Comms_Wall_N_FillTop",
        "08_Command & Comms_Wall_S_L",
        "08_Command & Comms_Wall_S_R",
        "08_Command & Comms_Wall_S_Fill0",
        "08_Command & Comms_Wall_S_Glass0",
        "08_Command & Comms_Wall_S_FillTop",
        "08_Command & Comms_Wall_E_L",
        "08_Command & Comms_Wall_E_R",
        "08_Command & Comms_Wall_E_Fill0",
        "08_Command & Comms_Wall_E_Glass0",
        "08_Command & Comms_Wall_E_FillTop",
        "08_Command & Comms_Wall_W_L",
        "08_Command & Comms_Wall_W_R",
        "08_Command & Comms_Wall_W_Lintel",
        "08_Command & Comms_Ceiling",
    ],
    "Mess Hall": [
        "06_Mess Hall_Wall_N_L",
        "06_Mess Hall_Wall_N_R",
        "06_Mess Hall_Wall_N_Fill0",
        "06_Mess Hall_Wall_N_Glass0",
        "06_Mess Hall_Wall_N_FillTop",
        "06_Mess Hall_Wall_S_L",
        "06_Mess Hall_Wall_S_R",
        "06_Mess Hall_Wall_S_Lintel",
        "06_Mess Hall_Wall_E_L",
        "06_Mess Hall_Wall_E_R",
        "06_Mess Hall_Wall_E_Fill0",
        "06_Mess Hall_Wall_E_Glass0",
        "06_Mess Hall_Wall_E_FillTop",
        "06_Mess Hall_Wall_W_L",
        "06_Mess Hall_Wall_W_R",
        "06_Mess Hall_Wall_W_Fill0",
        "06_Mess Hall_Wall_W_Glass0",
        "06_Mess Hall_Wall_W_FillTop",
        "06_Mess Hall_Ceiling",
    ],
}


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()
    by_label = {}
    for a in all_actors:
        by_label.setdefault(a.get_actor_label(), []).append(a)

    total_deleted = 0
    total_missing = 0

    for building, labels in DELETE_LABELS.items():
        log(f"---- {building}: deleting {len(labels)} old blockout actor(s) ----")
        deleted_here = 0
        for label in labels:
            matches = by_label.get(label, [])
            if not matches:
                log(f"    MISSING (already gone?): {label}")
                total_missing += 1
                continue
            for actor in matches:
                ok = subsystem.destroy_actor(actor)
                if ok:
                    deleted_here += 1
                    total_deleted += 1
                else:
                    log(f"    FAILED to delete: {label}")
        log(f"    Deleted {deleted_here}/{len(labels)} for {building}.")

    log("---- SUMMARY ----")
    log(f"Total deleted: {total_deleted}")
    log(f"Total missing (not found): {total_missing}")
    log("Review in viewport, then save the level yourself when ready.")


main()
