"""
IBPY: ib_inspect_buildings.py

Read-only inspection: lists every level actor whose Outliner folder path
or label mentions one of the target building names, grouping them and
flagging anything that looks like a door frame, so we can confirm exact
actor labels before writing placement/collision/cleanup scripts.

HOW TO RUN:
  py "X:\IronBreach\Scripts\ib_inspect_buildings.py"
"""

import unreal

TARGETS = ["Command", "MainGate", "Main Gate", "Medical", "Mess_Hall", "Mess Hall", "MechHangar", "Mech Hangar"]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()

    grouped = {}
    for a in all_actors:
        label = a.get_actor_label()
        folder = str(a.get_folder_path())
        haystack = f"{label} {folder}"
        for target in TARGETS:
            if target.lower() in haystack.lower():
                grouped.setdefault(target, []).append((label, folder, a.get_class().get_name()))
                break

    for target in TARGETS:
        actors = grouped.get(target, [])
        log(f"---- {target}: {len(actors)} actor(s) ----")
        for label, folder, cls in actors:
            tag = " <-- DOORFRAME?" if "door" in label.lower() else ""
            log(f"    [{cls}] {label}  (folder: {folder}){tag}")

    log("Done.")


main()
