"""
IBPY: ib_place_remaining_meshes.py

Phase A of finishing the remaining garrison buildings (Command & Comms,
Mess Hall, Main Gate). This step only places/repositions each building's
Tripo3D exterior mesh -- it does NOT touch interior collision and does NOT
delete any old blockout geometry. Review the result before moving on.

- Command & Comms already has its Tripo mesh dropped into the level
  (label "command tower 3d model", no folder) -- this script RENAMES and
  REPOSITIONS that existing actor rather than spawning a duplicate.
- Mess Hall has no Tripo mesh placed yet -- this script spawns one fresh
  from /Game/TripoModels/Mess_Hall.
- Main Gate has no Tripo mesh placed yet -- this script spawns one fresh
  from /Game/TripoModels/MainGate. NOTE: Main Gate is a drive-through
  checkpoint, not an enclosed room, so this is a VISUAL OVERLAY ONLY --
  the existing Pylon_L/Pylon_R/Lintel actors are left in place as the
  real collision (they are not old "hollow box" blockout like the other
  buildings, they're the actual gate structure).

HOW TO RUN:
  py "X:\IronBreach\Scripts\ib_place_remaining_meshes.py"

Nothing is saved automatically -- review in the viewport, then save the
level yourself once you're happy with it.
"""

import unreal

SCALE = 30.0


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_actor_by_label(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsystem.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def get_actors_by_labels(labels):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    wanted = set(labels)
    found = {}
    for a in subsystem.get_all_level_actors():
        lbl = a.get_actor_label()
        if lbl in wanted:
            found[lbl] = a
    return found


def compute_footprint(actors):
    min_x = min_y = min_z = None
    max_x = max_y = max_z = None
    for a in actors:
        origin, extent = a.get_actor_bounds(only_colliding_components=False)
        ax0, ax1 = origin.x - extent.x, origin.x + extent.x
        ay0, ay1 = origin.y - extent.y, origin.y + extent.y
        az0, az1 = origin.z - extent.z, origin.z + extent.z
        min_x = ax0 if min_x is None else min(min_x, ax0)
        max_x = ax1 if max_x is None else max(max_x, ax1)
        min_y = ay0 if min_y is None else min(min_y, ay0)
        max_y = ay1 if max_y is None else max(max_y, ay1)
        min_z = az0 if min_z is None else min(min_z, az0)
        max_z = az1 if max_z is None else max(max_z, az1)
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    return center_x, center_y, min_z


def find_tripo_static_mesh(content_folder):
    asset_paths = unreal.EditorAssetLibrary.list_assets(content_folder, recursive=True, include_folder=False)
    for path in asset_paths:
        asset_data = unreal.EditorAssetLibrary.find_asset_data(path)
        if asset_data and asset_data.asset_class_path.asset_name == "StaticMesh":
            return unreal.EditorAssetLibrary.load_asset(path)
    return None


def set_no_collision(actor):
    mesh_comp = getattr(actor, "static_mesh_component", None)
    if mesh_comp:
        mesh_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)


# ---------------------------------------------------------------------------
# Command & Comms -- reuse the already-placed "command tower 3d model" actor.
# ---------------------------------------------------------------------------
def do_command():
    prefix = "08_Command & Comms"
    folder = "Carrowgate Garrison/Command & Comms"

    existing = get_actor_by_label("command tower 3d model")
    door = get_actor_by_label(f"{prefix}_DoorFrame")

    if not existing:
        log("[Command] SKIPPED -- couldn't find the existing 'command tower 3d model' actor.")
        return False
    if not door:
        log("[Command] SKIPPED -- door actor not found.")
        return False

    wall_labels = [
        f"{prefix}_Wall_N_L", f"{prefix}_Wall_N_R", f"{prefix}_Wall_N_Fill0",
        f"{prefix}_Wall_N_Glass0", f"{prefix}_Wall_N_FillTop",
        f"{prefix}_Wall_S_L", f"{prefix}_Wall_S_R", f"{prefix}_Wall_S_Fill0",
        f"{prefix}_Wall_S_Glass0", f"{prefix}_Wall_S_FillTop",
        f"{prefix}_Wall_E_L", f"{prefix}_Wall_E_R", f"{prefix}_Wall_E_Fill0",
        f"{prefix}_Wall_E_Glass0", f"{prefix}_Wall_E_FillTop",
        f"{prefix}_Wall_W_L", f"{prefix}_Wall_W_R", f"{prefix}_Wall_W_Lintel",
    ]
    found = get_actors_by_labels(wall_labels)
    missing = [l for l in wall_labels if l not in found]
    if missing:
        log(f"[Command] WARNING -- {len(missing)} expected wall actor(s) not found: {missing}")
    wall_actors = list(found.values())
    if not wall_actors:
        log("[Command] SKIPPED -- no blockout wall actors found to compute a footprint from.")
        return False

    center_x, center_y, floor_z = compute_footprint(wall_actors)
    door_yaw = door.get_actor_rotation().yaw

    log(f"[Command] Footprint from {len(wall_actors)} wall actor(s): center=({center_x:.1f}, {center_y:.1f}), floor_z={floor_z:.1f}, door_yaw={door_yaw:.1f}")
    log(f"[Command] Existing tripo actor current loc={existing.get_actor_location()} scale={existing.get_actor_scale3d()}")

    existing.set_actor_label(f"SM_Command_Tripo")
    existing.set_folder_path(folder)
    existing.set_actor_location(unreal.Vector(center_x, center_y, floor_z), False, False)
    existing.set_actor_rotation(unreal.Rotator(0, 0, door_yaw), False)
    existing.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
    set_no_collision(existing)

    log(f"[Command] Placed 'SM_Command_Tripo' at ({center_x:.1f}, {center_y:.1f}, {floor_z:.1f}), yaw={door_yaw:.1f}, scale={SCALE}x. Collision set to None.")
    return True


# ---------------------------------------------------------------------------
# Mess Hall -- spawn fresh from the Content Browser asset.
# ---------------------------------------------------------------------------
def do_mess_hall():
    prefix = "06_Mess Hall"
    folder = "Carrowgate Garrison/Mess Hall"

    door = get_actor_by_label(f"{prefix}_DoorFrame")
    mesh = find_tripo_static_mesh("/Game/TripoModels/Mess_Hall")

    if not door:
        log("[Mess Hall] SKIPPED -- door actor not found.")
        return False
    if not mesh:
        log("[Mess Hall] SKIPPED -- no StaticMesh asset found under /Game/TripoModels/Mess_Hall.")
        return False

    wall_labels = [
        f"{prefix}_Wall_N_L", f"{prefix}_Wall_N_R", f"{prefix}_Wall_N_Fill0",
        f"{prefix}_Wall_N_Glass0", f"{prefix}_Wall_N_FillTop",
        f"{prefix}_Wall_S_L", f"{prefix}_Wall_S_R", f"{prefix}_Wall_S_Lintel",
        f"{prefix}_Wall_E_L", f"{prefix}_Wall_E_R", f"{prefix}_Wall_E_Fill0",
        f"{prefix}_Wall_E_Glass0", f"{prefix}_Wall_E_FillTop",
        f"{prefix}_Wall_W_L", f"{prefix}_Wall_W_R", f"{prefix}_Wall_W_Fill0",
        f"{prefix}_Wall_W_Glass0", f"{prefix}_Wall_W_FillTop",
    ]
    found = get_actors_by_labels(wall_labels)
    missing = [l for l in wall_labels if l not in found]
    if missing:
        log(f"[Mess Hall] WARNING -- {len(missing)} expected wall actor(s) not found: {missing}")
    wall_actors = list(found.values())
    if not wall_actors:
        log("[Mess Hall] SKIPPED -- no blockout wall actors found to compute a footprint from.")
        return False

    center_x, center_y, floor_z = compute_footprint(wall_actors)
    door_yaw = door.get_actor_rotation().yaw

    log(f"[Mess Hall] Footprint from {len(wall_actors)} wall actor(s): center=({center_x:.1f}, {center_y:.1f}), floor_z={floor_z:.1f}, door_yaw={door_yaw:.1f}")

    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    spawn_loc = unreal.Vector(center_x, center_y, floor_z)
    spawn_rot = unreal.Rotator(0, 0, door_yaw)
    actor = subsystem.spawn_actor_from_object(mesh, spawn_loc, spawn_rot)
    actor.set_actor_label("SM_MessHall_Tripo")
    actor.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
    actor.set_folder_path(folder)
    set_no_collision(actor)

    log(f"[Mess Hall] Placed 'SM_MessHall_Tripo' at {spawn_loc}, yaw={door_yaw:.1f}, scale={SCALE}x. Collision set to None.")
    return True


# ---------------------------------------------------------------------------
# Main Gate -- spawn fresh, VISUAL OVERLAY ONLY. Pylon_L/Pylon_R/Lintel stay
# exactly as they are (they're the real collision at a drive-through
# checkpoint, not hollow-box blockout like the other buildings).
# ---------------------------------------------------------------------------
def do_main_gate():
    folder = "Carrowgate Garrison/Main Gate"

    door = get_actor_by_label("BP_MainGateDoor")
    mesh = find_tripo_static_mesh("/Game/TripoModels/MainGate")

    if not door:
        log("[Main Gate] SKIPPED -- door actor 'BP_MainGateDoor' not found.")
        return False
    if not mesh:
        log("[Main Gate] SKIPPED -- no StaticMesh asset found under /Game/TripoModels/MainGate.")
        return False

    structure_labels = ["01_Main Gate_Pylon_L", "01_Main Gate_Pylon_R", "01_Main Gate_Lintel"]
    found = get_actors_by_labels(structure_labels)
    missing = [l for l in structure_labels if l not in found]
    if missing:
        log(f"[Main Gate] WARNING -- {len(missing)} expected structure actor(s) not found: {missing}")
    structure_actors = list(found.values())
    if not structure_actors:
        log("[Main Gate] SKIPPED -- no Pylon/Lintel actors found to compute a footprint from.")
        return False

    center_x, center_y, floor_z = compute_footprint(structure_actors)
    door_yaw = door.get_actor_rotation().yaw

    log(f"[Main Gate] Footprint from {len(structure_actors)} structure actor(s): center=({center_x:.1f}, {center_y:.1f}), floor_z={floor_z:.1f}, door_yaw={door_yaw:.1f}")

    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    spawn_loc = unreal.Vector(center_x, center_y, floor_z)
    spawn_rot = unreal.Rotator(0, 0, door_yaw)
    actor = subsystem.spawn_actor_from_object(mesh, spawn_loc, spawn_rot)
    actor.set_actor_label("SM_MainGate_Tripo")
    actor.set_actor_scale3d(unreal.Vector(SCALE, SCALE, SCALE))
    actor.set_folder_path(folder)
    set_no_collision(actor)

    log(f"[Main Gate] Placed 'SM_MainGate_Tripo' (visual overlay only) at {spawn_loc}, yaw={door_yaw:.1f}, scale={SCALE}x. Collision set to None. Pylon_L/Pylon_R/Lintel left untouched as the real collision.")
    return True


def report_blocked():
    medical = get_actor_by_label("medical building 3d model")
    if medical:
        log(f"[Medical] Tripo mesh IS in the level ('medical building 3d model') but there's no blockout or door frame actor to anchor placement/rotation/interior collision to. loc={medical.get_actor_location()} scale={medical.get_actor_scale3d()}. Left untouched -- needs a placeholder door frame + footprint before this can be finished the same way as the others.")
    else:
        log("[Medical] No existing Tripo mesh actor found either.")
    log("[Mech Hangar] No Tripo mesh asset in Content Browser (Content/TripoModels has no Mech Hangar folder) and no blockout/door frame in the level. Fully blocked until a mesh is generated/imported and a placeholder door frame is placed.")


def main():
    log("---- Phase A: placing/repositioning exterior meshes ----")
    results = []
    results.append(("Command", do_command()))
    results.append(("Mess Hall", do_mess_hall()))
    results.append(("Main Gate", do_main_gate()))
    report_blocked()

    log("---- SUMMARY ----")
    for name, ok in results:
        log(f"{name}: {'OK' if ok else 'SKIPPED/FAILED'}")
    log("Review placement in viewport. Nothing saved automatically.")


main()
