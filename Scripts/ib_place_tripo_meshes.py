"""
IBPY: ib_place_tripo_meshes.py

Places each building's imported Tripo3D static mesh into the
CarrowGateGarrison level, positioned/rotated to roughly match the
existing blockout footprint, at a configurable scale (default 30x,
since Tripo3D exports typically need a big scale-up to read as
real-world building size in UE's cm units).

This does NOT delete or hide the existing blockout -- it just adds the
new mesh alongside it so you can compare/adjust before removing the
old boxes yourself. Collision on the spawned mesh is left at engine
defaults; run ib_auto_interior_collision.py afterward for the actual
walkable interior shell.

HOW TO RUN:
  1. Fill in / confirm the BUILDINGS list below -- each needs:
       - outliner_folder: the building's folder name in the Outliner
         (e.g. "Barracks", as seen under "Carrowgate Garrison/Barracks")
       - tripo_content_folder: the Content Browser path holding the
         imported Tripo3D mesh (e.g. "/Game/TripoModels/Barracks")
       - door_actor: the existing *_DoorFrame actor label, used to
         determine which way the building should face
       - scale: uniform scale to apply (defaults to 30.0)
  2. In the Unreal Editor Python console, run:
       exec(open(r"X:\IronBreach\Scripts\ib_place_tripo_meshes.py").read())
  3. Check the Output Log for a per-building report, then eyeball the
     placement in the viewport and nudge as needed.
  4. Nothing is saved automatically.
"""

import unreal

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BUILDINGS = [
    {
        "outliner_folder": "Barracks",
        "tripo_content_folder": "/Game/TripoModels/Barracks",
        "door_actor": "05_Barracks_DoorFrame",
        "scale": 30.0,
    },
    {
        "outliner_folder": "Armory",
        "tripo_content_folder": "/Game/TripoModels/Armory",
        "door_actor": "07_Armory_DoorFrame",   # confirm this matches your current level
        "scale": 30.0,
    },
    # {
    #     "outliner_folder": "Command",
    #     "tripo_content_folder": "/Game/TripoModels/Command",
    #     "door_actor": "08_Command_DoorFrame",   # confirm actual label
    #     "scale": 30.0,
    # },
    # {
    #     "outliner_folder": "MainGate",
    #     "tripo_content_folder": "/Game/TripoModels/MainGate",
    #     "door_actor": "01_Main Gate_DoorFrame",   # confirm actual label
    #     "scale": 30.0,
    # },
    # {
    #     "outliner_folder": "Medical",
    #     "tripo_content_folder": "/Game/TripoModels/Medical",
    #     "door_actor": "PLACEHOLDER_Medical_DoorFrame",   # new building, no existing blockout yet
    #     "scale": 30.0,
    # },
    # {
    #     "outliner_folder": "Mess_Hall",
    #     "tripo_content_folder": "/Game/TripoModels/Mess_Hall",
    #     "door_actor": "06_Mess Hall_DoorFrame",   # confirm actual label
    #     "scale": 30.0,
    # },
]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_actor_by_label(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsystem.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def get_actors_in_outliner_folder(folder_name):
    """Return all level actors whose folder path contains folder_name as a path segment."""
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    matches = []
    for a in subsystem.get_all_level_actors():
        path = str(a.get_folder_path())
        segments = path.split("/")
        if folder_name in segments:
            matches.append(a)
    return matches


def find_tripo_static_mesh(content_folder):
    """Find the first StaticMesh asset under a given Content Browser folder."""
    asset_paths = unreal.EditorAssetLibrary.list_assets(content_folder, recursive=True, include_folder=False)
    for path in asset_paths:
        asset_data = unreal.EditorAssetLibrary.find_asset_data(path)
        if asset_data and asset_data.asset_class_path.asset_name == "StaticMesh":
            return unreal.EditorAssetLibrary.load_asset(path)
    return None


def compute_footprint(actors):
    """Combine bounds of a list of actors into an overall (center, min_z)."""
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


def place_building(building):
    folder = building["outliner_folder"]
    door = get_actor_by_label(building["door_actor"])
    mesh = find_tripo_static_mesh(building["tripo_content_folder"])
    scale = building.get("scale", 30.0)

    if not door:
        log(f"[{folder}] SKIPPED -- door actor '{building['door_actor']}' not found. "
            f"For a brand-new building with no existing blockout, place a temporary "
            f"door frame first so this script has an anchor point.")
        return False

    if not mesh:
        log(f"[{folder}] SKIPPED -- no StaticMesh asset found under '{building['tripo_content_folder']}'.")
        return False

    blockout_actors = get_actors_in_outliner_folder(folder)
    # Exclude the door frame itself and any prior Tripo placements from the footprint calc
    blockout_actors = [a for a in blockout_actors if a != door and "Tripo" not in a.get_actor_label()]

    if blockout_actors:
        center_x, center_y, floor_z = compute_footprint(blockout_actors)
        log(f"[{folder}] Footprint computed from {len(blockout_actors)} blockout actor(s): "
            f"center=({center_x:.1f}, {center_y:.1f}), floor_z={floor_z:.1f}")
    else:
        door_loc = door.get_actor_location()
        center_x, center_y, floor_z = door_loc.x, door_loc.y, door_loc.z
        log(f"[{folder}] No blockout actors found in Outliner folder -- falling back to door location "
            f"({center_x:.1f}, {center_y:.1f}, {floor_z:.1f}). Placement will likely need manual adjustment.")

    door_yaw = door.get_actor_rotation().yaw

    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    spawn_loc = unreal.Vector(center_x, center_y, floor_z)
    spawn_rot = unreal.Rotator(0, 0, door_yaw)

    actor = subsystem.spawn_actor_from_object(mesh, spawn_loc, spawn_rot)
    label = f"SM_{folder}_Tripo"
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    actor.set_folder_path(f"Carrowgate Garrison/{folder}")

    # No collision -- this is a visual-only exterior shell, per the two-layer approach.
    mesh_comp = actor.static_mesh_component
    if mesh_comp:
        mesh_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

    log(f"[{folder}] Placed '{label}' at {spawn_loc}, yaw={door_yaw:.1f}, scale={scale}x. "
        f"Collision set to None (visual-only exterior).")
    return True


def main():
    log(f"Placing Tripo3D meshes for {len(BUILDINGS)} building(s).")
    results = []
    for building in BUILDINGS:
        ok = place_building(building)
        results.append((building["outliner_folder"], ok))

    log("---- SUMMARY ----")
    for folder, ok in results:
        log(f"{folder}: {'PLACED' if ok else 'SKIPPED/FAILED'}")
    log("Review placement in viewport and adjust as needed. Nothing saved automatically.")
    log("Once placement looks right, run ib_auto_interior_collision.py for the walkable interior shell.")


main()
