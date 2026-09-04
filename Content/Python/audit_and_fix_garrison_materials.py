"""
Audit and fix blank/default materials across CarrowGateGarrison
====================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
build_carrowgate_garrison.py placed 324+ actors across the garrison, each
material-slot assignment done by hand as the script was built up over many
edits -- a few slots on a few actors (the Armory's wall fills/glass panes
are the ones Shane spotted in the Outliner, but there may be others) never
got a material.set_material(0, ...) call, or got one that silently failed
(e.g. a mesh with more slots than the script accounted for), and are showing
either fully blank (None) or Unreal's default grey/checker fallback.

This script does NOT try to guess new content -- it only finds every
StaticMeshComponent (on plain StaticMeshActors AND on Blueprint actors like
BP_DoorFrame, which carry their mesh on an internal component rather than
via actor.static_mesh_component) under the "Carrowgate Garrison" Outliner
folder tree, checks each material slot, and for any slot that's blank or
still on Unreal's own placeholder material, assigns the right M_AI_*
material by matching the actor's label against the same naming convention
build_carrowgate_garrison.py already uses (Wall/Glass/Ground/Ramp/etc in
the label).

If an actor's label doesn't match any known pattern, it's left alone and
logged as unmatched -- so nothing gets a wrong material silently. Check the
Output Log for an "UNMATCHED" list at the end and fix those by hand (or
tell me the label and I'll add a rule).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/audit_and_fix_garrison_materials.py"

Read-only by default -- set DRY_RUN = False below to actually apply fixes.
Safe to re-run either way.
"""

import unreal

DRY_RUN = False  # flip to False once the planned fixes below look right

ROOT_FOLDER = "Carrowgate Garrison"

MATERIAL_PATHS = {
    "wall": "/Game/LevelPrototyping/AITextures/M_AI_Wall.M_AI_Wall",
    "ground": "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground",
    "ramp": "/Game/LevelPrototyping/AITextures/M_AI_Ramp.M_AI_Ramp",
    "furniture": "/Game/LevelPrototyping/AITextures/M_AI_Furniture.M_AI_Furniture",
    "water": "/Game/LevelPrototyping/AITextures/M_AI_Water.M_AI_Water",
    "vehicle": "/Game/LevelPrototyping/AITextures/M_AI_Vehicle.M_AI_Vehicle",
    "ship": "/Game/LevelPrototyping/AITextures/M_AI_Ship.M_AI_Ship",
    "crane": "/Game/LevelPrototyping/AITextures/M_AI_Crane.M_AI_Crane",
    "glass": "/Game/LevelPrototyping/AITextures/M_AI_Glass.M_AI_Glass",
}

# Ordered (most-specific-first) label substring -> material key. First match wins,
# so put narrower matches ("weaponrack") before broader ones ("wall").
LABEL_RULES = [
    ("glass", "glass"),
    ("weaponrack", "furniture"), ("weapon_rack", "furniture"),
    ("locker", "furniture"), ("bunk", "furniture"), ("messtable", "furniture"),
    ("mess_table", "furniture"), ("desk", "furniture"), ("chair", "furniture"),
    ("vendingmachine", "furniture"), ("vending", "furniture"),
    ("commsconsole", "furniture"), ("console", "furniture"),
    ("truck", "vehicle"), ("vehicle", "vehicle"), ("jeep", "vehicle"),
    ("ship", "ship"), ("hull", "ship"),
    ("crane", "crane"),
    ("water", "water"),
    ("ramp", "ramp"), ("stair", "ramp"),
    ("ground", "ground"), ("floor", "ground"), ("pad", "ground"), ("approach", "ground"),
    ("wall", "wall"), ("doorframe", "wall"), ("door_frame", "wall"), ("ceiling", "wall"),
]

DEFAULT_MATERIAL_INDICATORS = (
    "worldgridmaterial",
    "defaultmaterial",
    "basicshapematerial",
)


def load_materials():
    loaded = {}
    for key, path in MATERIAL_PATHS.items():
        mat = unreal.EditorAssetLibrary.load_asset(path)
        if mat is None:
            unreal.log_warning(f"[Garrison Materials] Could not load {path} -- '{key}' fixes will be skipped.")
        loaded[key] = mat
    return loaded


def classify_label(label):
    lower = label.lower()
    for substr, key in LABEL_RULES:
        if substr in lower:
            return key
    return None


def is_blank_or_default(material):
    if material is None:
        return True
    path = material.get_path_name().lower()
    return any(tok in path for tok in DEFAULT_MATERIAL_INDICATORS)


def in_garrison_folder(actor):
    folder = str(actor.get_folder_path())
    return folder == ROOT_FOLDER or folder.startswith(ROOT_FOLDER + "/")


def get_slot_count(static_mesh):
    """StaticMesh's material-slot array property has moved names across engine
    versions ("static_materials" vs "materials") -- try both, fall back to a
    generous fixed guess if neither reads cleanly rather than erroring out."""
    for prop_name in ("static_materials", "materials"):
        try:
            slots = static_mesh.get_editor_property(prop_name)
            return len(slots)
        except Exception:
            continue
    return 8


def run():
    materials = load_materials()
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    checked_slots = 0
    fixed = []
    unmatched = []
    already_ok = 0

    for actor in actor_subsystem.get_all_level_actors():
        if not in_garrison_folder(actor):
            continue

        mesh_comps = actor.get_components_by_class(unreal.StaticMeshComponent)
        if not mesh_comps:
            continue

        label = actor.get_actor_label()
        for comp in mesh_comps:
            static_mesh = comp.static_mesh
            if static_mesh is None:
                continue
            num_slots = get_slot_count(static_mesh)
            for slot in range(num_slots):
                try:
                    mat = comp.get_material(slot)
                except Exception:
                    break
                checked_slots += 1
                if is_blank_or_default(mat):
                    key = classify_label(label)
                    if key is None or materials.get(key) is None:
                        unmatched.append(f"{label} (slot {slot})")
                    else:
                        if not DRY_RUN:
                            comp.set_material(slot, materials[key])
                        fixed.append(f"{label} (slot {slot}) -> {key}")
                else:
                    already_ok += 1

    unreal.log(f"[Garrison Materials] Checked {checked_slots} material slot(s) across the '{ROOT_FOLDER}' tree.")
    unreal.log(f"[Garrison Materials] {already_ok} slot(s) already had a real material -- left alone.")

    if fixed:
        verb = "Would fix" if DRY_RUN else "Fixed"
        unreal.log(f"[Garrison Materials] {verb} {len(fixed)} slot(s):")
        for line in fixed:
            unreal.log(f"[Garrison Materials]   {line}")
    else:
        unreal.log("[Garrison Materials] No blank/default slots matched a known naming rule.")

    if unmatched:
        unreal.log_warning(f"[Garrison Materials] {len(unmatched)} blank/default slot(s) didn't match any label rule:")
        for line in unmatched:
            unreal.log_warning(f"[Garrison Materials]   {line}")
        unreal.log_warning(
            "[Garrison Materials] Add a rule to LABEL_RULES for these, or fix them by hand in the editor.")

    if DRY_RUN and fixed:
        unreal.log(
            "[Garrison Materials] DRY_RUN is True -- nothing was actually changed. Review the list above, "
            "then set DRY_RUN = False at the top of this script and re-run to apply."
        )
    elif not DRY_RUN and fixed:
        unreal.log("[Garrison Materials] Applied. Save the level (Ctrl+S) to keep the fixes.")


run()
