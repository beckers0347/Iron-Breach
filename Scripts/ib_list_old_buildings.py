"""
IBPY: ib_list_old_buildings.py

READ-ONLY. Lists every actor in the current level (CarrowGateGarrison) so
you can review which ones are the old pre-Tripo3D placeholder blockouts
(buildings + their props) before anything gets deleted. Deletes nothing --
this is step 1 of 2. Once you've reviewed the output and told me which
actors/folders/patterns to actually remove, I'll write a second script
that deletes exactly those and nothing else.

It groups actors two ways to make review easier:
  1. By World Outliner folder path (often the fastest way to spot an
     "OldBuildings" / "Blockout" / "Placeholder" folder at a glance).
  2. A "likely placeholder" flag per actor, based on soft signals:
       - Label contains any of: old, placeholder, blockout, block_out,
         temp, bsp, wip, deprecated, unused
       - It's a BSP brush actor (common for early blockout geometry)
       - Its static mesh (if any) comes from /Engine/BasicShapes (Cube,
         Sphere, Cylinder, Cone -- classic placeholder primitives) rather
         than /Game/...
  These are just hints, not a decision -- nothing is auto-selected for
  deletion. The known-good Tripo3D buildings and their DoorFrame actors
  are explicitly excluded from the "likely placeholder" flag (listed
  under KNOWN_KEEP below) so they don't show up as false positives, even
  if their names happen to loosely match a pattern.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_list_old_buildings.py"
Paste the full output back and tell me which folders/patterns/actors are
actually the old stuff to remove -- I'll turn that into a precise,
reviewed deletion script next.
"""

import unreal

# Actors we already know are current/good -- never flag these even if a
# name pattern below would otherwise loosely match them.
KNOWN_KEEP_SUBSTRINGS = [
    "sm_armory_tripo",
    "sm_command_tripo",
    "sm_messhall_tripo",
    "_doorframe",
]

PLACEHOLDER_NAME_HINTS = [
    "old", "placeholder", "blockout", "block_out", "block out",
    "temp", "bsp", "wip", "deprecated", "unused", "delete",
]

BASIC_SHAPE_HINTS = ["basicshapes", "/engine/"]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def is_known_keep(label_lower):
    return any(s in label_lower for s in KNOWN_KEEP_SUBSTRINGS)


def get_static_mesh_path(actor):
    mesh_comp = getattr(actor, "static_mesh_component", None) or actor.get_component_by_class(unreal.StaticMeshComponent)
    if not mesh_comp:
        return None
    static_mesh = mesh_comp.get_editor_property("static_mesh")
    if not static_mesh:
        return None
    try:
        return static_mesh.get_path_name()
    except Exception:
        return None


def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()
    log(f"Total actors in level: {len(all_actors)}")

    by_folder = {}
    flagged = []
    unflagged = []

    for a in all_actors:
        label = a.get_actor_label()
        label_lower = label.lower()
        class_name = a.get_class().get_name()
        folder = str(a.get_folder_path()) or "(root)"
        mesh_path = get_static_mesh_path(a)
        loc = a.get_actor_location()

        by_folder.setdefault(folder, []).append(label)

        keep = is_known_keep(label_lower)
        reasons = []
        if not keep:
            for hint in PLACEHOLDER_NAME_HINTS:
                if hint in label_lower:
                    reasons.append(f"name contains '{hint}'")
                    break
            if "bsp" in class_name.lower() or class_name in ("Brush",):
                reasons.append(f"class={class_name} (BSP brush)")
            if mesh_path:
                mp_lower = mesh_path.lower()
                for hint in BASIC_SHAPE_HINTS:
                    if hint in mp_lower:
                        reasons.append(f"mesh under engine content: {mesh_path}")
                        break

        entry = {
            "label": label,
            "class": class_name,
            "folder": folder,
            "mesh_path": mesh_path,
            "loc": (round(loc.x, 1), round(loc.y, 1), round(loc.z, 1)),
            "reasons": reasons,
        }

        if reasons and not keep:
            flagged.append(entry)
        else:
            unflagged.append(entry)

    log("==== ACTORS BY FOLDER PATH ====")
    for folder in sorted(by_folder.keys()):
        labels = by_folder[folder]
        log(f"  [{folder}] ({len(labels)} actor(s)):")
        for lbl in sorted(labels):
            log(f"      {lbl}")

    log("==== LIKELY-PLACEHOLDER CANDIDATES (soft heuristic, review before deleting) ====")
    if not flagged:
        log("  (none matched the naming/class/mesh-source hints)")
    for e in flagged:
        log(f"  [{e['class']}] '{e['label']}' folder='{e['folder']}' loc={e['loc']} "
            f"mesh='{e['mesh_path']}' reasons={e['reasons']}")

    log("==== EVERYTHING ELSE (not flagged -- includes all current Tripo3D buildings/doors/props) ====")
    for e in unflagged:
        log(f"  [{e['class']}] '{e['label']}' folder='{e['folder']}' loc={e['loc']} mesh='{e['mesh_path']}'")

    log("Done. Nothing was modified or deleted -- this is a listing only.")


main()
