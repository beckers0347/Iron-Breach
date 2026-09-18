"""
IBPY: ib_fit_blockout_to_tripo.py

Reuses the existing blockout wall/ceiling pieces (already correctly laid
out with door and window gaps) as the interior collision boundary for a
building, instead of deleting them or spawning new BlockingVolumes.

For each building, it:
  1. Computes the OLD blockout's combined bounds (from its wall/ceiling
     StaticMeshActors, excluding the door frame and the Tripo mesh).
  2. Computes the NEW Tripo3D exterior mesh's bounds, inset by a wall
     thickness so the old pieces sit just inside the visible shell.
  3. Scales + repositions EACH old wall/ceiling actor by the ratio
     between old and new bounds, preserving their relative layout
     (door gap, window gaps) -- just fit to the new footprint.
  4. Hides each repositioned actor visually (Actor Hidden In Game),
     leaving its collision intact, so the player collides with it but
     never sees it -- the Tripo mesh is the only visible geometry.

The door frame actor itself is left untouched (it's already correctly
positioned/working). The Tripo mesh is left untouched.

HOW TO RUN:
  py "X:\\IronBreach\\Scripts\\ib_fit_blockout_to_tripo.py"

Nothing is saved automatically -- review in the viewport, then save
the level yourself once you're happy.
"""

import unreal
import re

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
BUILDINGS = [
    {
        "outliner_folder": "Barracks",
        "tripo_actor": "SM_Barracks_Tripo",
        "door_actor": "05_Barracks_DoorFrame",
        "wall_inset": 30.0,   # how far inside the Tripo mesh's outer face the old walls should sit
    },
    # {
    #     "outliner_folder": "Armory",
    #     "tripo_actor": "SM_Armory_Tripo",
    #     "door_actor": "07_Armory_DoorFrame",
    #     "wall_inset": 30.0,
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


def get_blockout_pieces(folder_name, door_actor, tripo_actor):
    """All StaticMeshActors in this building's Outliner folder, excluding the door frame and Tripo mesh."""
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    pieces = []
    for a in subsystem.get_all_level_actors():
        path = str(a.get_folder_path())
        segments = path.split("/")
        if folder_name not in segments:
            continue
        if a == door_actor or a == tripo_actor:
            continue
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        pieces.append(a)
    return pieces


def compute_bounds(actors):
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
    center = unreal.Vector((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, (min_z + max_z) / 2.0)
    extent = unreal.Vector((max_x - min_x) / 2.0, (max_y - min_y) / 2.0, (max_z - min_z) / 2.0)
    return center, extent


def fit_building(building):
    folder = building["outliner_folder"]
    tripo = get_actor_by_label(building["tripo_actor"])
    door = get_actor_by_label(building["door_actor"])
    inset = building.get("wall_inset", 30.0)

    if not tripo:
        log(f"[{folder}] SKIPPED -- Tripo mesh actor '{building['tripo_actor']}' not found.")
        return False
    if not door:
        log(f"[{folder}] SKIPPED -- door actor '{building['door_actor']}' not found.")
        return False

    pieces = get_blockout_pieces(folder, door, tripo)
    if not pieces:
        log(f"[{folder}] SKIPPED -- no blockout wall/ceiling pieces found.")
        return False

    old_center, old_extent = compute_bounds(pieces)

    tripo_origin, tripo_extent = tripo.get_actor_bounds(only_colliding_components=False)
    new_extent = unreal.Vector(
        max(tripo_extent.x - inset, 50.0),
        max(tripo_extent.y - inset, 50.0),
        max(tripo_extent.z - inset, 50.0),
    )
    new_center = tripo_origin

    scale_x = new_extent.x / old_extent.x if old_extent.x > 0 else 1.0
    scale_y = new_extent.y / old_extent.y if old_extent.y > 0 else 1.0
    scale_z = new_extent.z / old_extent.z if old_extent.z > 0 else 1.0

    log(f"[{folder}] Old blockout bounds: center={old_center} extent={old_extent}")
    log(f"[{folder}] New target bounds (from Tripo mesh, inset {inset}cm): center={new_center} extent={new_extent}")
    log(f"[{folder}] Scale factors: x={scale_x:.3f} y={scale_y:.3f} z={scale_z:.3f}")
    log(f"[{folder}] Refitting {len(pieces)} blockout piece(s)...")

    for a in pieces:
        loc = a.get_actor_location()
        cur_scale = a.get_actor_scale3d()

        rel_x = (loc.x - old_center.x) * scale_x
        rel_y = (loc.y - old_center.y) * scale_y
        rel_z = (loc.z - old_center.z) * scale_z

        new_loc = unreal.Vector(new_center.x + rel_x, new_center.y + rel_y, new_center.z + rel_z)
        new_scale = unreal.Vector(cur_scale.x * scale_x, cur_scale.y * scale_y, cur_scale.z * scale_z)

        a.set_actor_location(new_loc, False, False)
        a.set_actor_scale3d(new_scale)
        a.set_actor_hidden_in_game(True)

        log(f"  {a.get_actor_label()}: loc {loc} -> {new_loc}, scale {cur_scale} -> {new_scale}, hidden=True")

    log(f"[{folder}] Done. {len(pieces)} piece(s) refit to the Tripo mesh footprint and hidden.")
    return True


def main():
    log(f"Fitting blockout collision to Tripo3D mesh for {len(BUILDINGS)} building(s).")
    results = []
    for building in BUILDINGS:
        ok = fit_building(building)
        results.append((building["outliner_folder"], ok))

    log("---- SUMMARY ----")
    for folder, ok in results:
        log(f"{folder}: {'FIT' if ok else 'SKIPPED/FAILED'}")
    log("Review in viewport (collision should still block movement even though pieces are hidden). Nothing saved automatically.")


main()
