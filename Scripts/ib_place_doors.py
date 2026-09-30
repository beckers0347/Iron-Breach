"""
IBPY: ib_place_doors.py

Places one BP_DoorFrame instance per Garrison building, on the side of
each building facing the shared courtyard (the centroid of all 5
building locations) -- per your call to face doors inward toward a
common center rather than a per-building compass direction.

PLACEMENT-ONLY: does NOT touch collision, does NOT carve anything. Per
your request, this stops here so you can review door positions/rotations
in the editor (or via another survey script) before we run the
carving/collision pass. Nothing destructive happens in this script --
worst case if a placement looks wrong, just delete the actor and re-run
after I adjust the math.

ALGORITHM (per building):
  1. Take the centroid (average X/Y) of all 5 buildings' locations as the
     shared "courtyard center."
  2. direction_world = normalized vector from this building's location
     toward the centroid (the wall the door should sit on, and the
     direction the doorway should open toward).
  3. Un-rotate that direction into the building's own local space (undo
     its actor yaw) to figure out whether the courtyard-facing wall is
     more "along local X" or "along local Y" for this building's mesh.
  4. Use the world-space half-extent along whichever local axis is
     dominant (local_bounds_extent * actor_scale on that axis) as the
     approximate distance from the building's pivot to that wall's
     surface, from the last survey's numbers -- hardcoded below since
     re-deriving them live risks operating on stale actors if anything
     shifted.
  5. Door location = building location + direction_world * that
     distance, at the building's own Z (assumes pivot sits at floor
     level, consistent with how BP_DoorFrame was used previously).
  6. Door yaw = the angle of direction_world, so the door frame's own
     forward axis points toward the courtyard center.

This is a geometric approximation, not a guarantee -- these are organic
Tripo3D shapes (Command's mesh isn't a simple box, for instance), so a
placement can land slightly inside or outside the real wall surface.
That's fine for review purposes; nudge it in the editor (or tell me the
offset and I'll adjust the script) before we carve.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_place_doors.py"
Then look at each new "<Building>_DoorFrame" actor in the editor (or run
a survey script) and tell me if any need repositioning before we carve.
"""

import math
import unreal

DOORFRAME_BP_PATH = "/Game/LevelPrototyping/Interactable/Door/BP_DoorFrame"

# From the latest ib_survey_garrison.py run -- (location, yaw, scale, local_bounds_extent)
BUILDINGS = [
    {
        "name": "Medical",
        "loc": (9397.6, 6241.2, 380.0),
        "yaw": -90.0,
        "scale": (25.0, 25.0, 25.0),
        "bounds_extent": (49.1, 29.5, 37.0),
    },
    {
        "name": "Barracks",
        "loc": (3310.0, -1604.0, 380.0),
        "yaw": 90.0,
        "scale": (25.0, 25.0, 25.0),
        "bounds_extent": (23.2, 49.2, 31.5),
    },
    {
        "name": "Armory",
        "loc": (6893.0, 8733.0, 380.0),
        "yaw": 180.0,
        "scale": (25.0, 25.0, 25.0),
        "bounds_extent": (49.0, 44.0, 33.8),
    },
    {
        "name": "Command",
        "loc": (518.0, 5770.0, 380.0),
        "yaw": -90.0,
        "scale": (25.0, 25.0, 25.0),
        "bounds_extent": (48.8, 28.8, 48.8),
    },
    {
        "name": "Mess_Hall",
        "loc": (318.0, 2854.0, 380.0),
        "yaw": -90.0,
        "scale": (25.0, 25.0, 25.0),
        "bounds_extent": (49.0, 24.2, 21.9),
    },
]

DOOR_FOLDER = "Carrowgate Garrison/Doors"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def unrotate_vector_yaw(x, y, yaw_degrees):
    rad = math.radians(-yaw_degrees)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


def main():
    centroid_x = sum(b["loc"][0] for b in BUILDINGS) / len(BUILDINGS)
    centroid_y = sum(b["loc"][1] for b in BUILDINGS) / len(BUILDINGS)
    log(f"Courtyard centroid (avg of all 5 building locations): ({centroid_x:.1f}, {centroid_y:.1f})")

    door_class = unreal.EditorAssetLibrary.load_blueprint_class(DOORFRAME_BP_PATH)
    if not door_class:
        log(f"FAILED -- could not load Blueprint class at '{DOORFRAME_BP_PATH}'. Nothing placed.")
        return

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    results = []
    for b in BUILDINGS:
        name = b["name"]
        bx, by, bz = b["loc"]
        yaw = b["yaw"]
        sx, sy, sz = b["scale"]
        ex, ey, ez = b["bounds_extent"]

        dir_x = centroid_x - bx
        dir_y = centroid_y - by
        mag = math.sqrt(dir_x * dir_x + dir_y * dir_y)
        if mag < 1.0:
            log(f"[{name}] SKIPPED -- building location is essentially at the centroid, no clear direction.")
            continue
        dir_x /= mag
        dir_y /= mag

        local_dir_x, local_dir_y = unrotate_vector_yaw(dir_x, dir_y, yaw)

        if abs(local_dir_x) >= abs(local_dir_y):
            world_extent_along_axis = ex * sx
            dominant_axis = "local X"
        else:
            world_extent_along_axis = ey * sy
            dominant_axis = "local Y"

        door_x = bx + dir_x * world_extent_along_axis
        door_y = by + dir_y * world_extent_along_axis
        door_z = bz

        door_yaw = math.degrees(math.atan2(dir_y, dir_x))

        label = f"{name}_DoorFrame"
        spawn_location = unreal.Vector(door_x, door_y, door_z)
        spawn_rotation = unreal.Rotator(0.0, 0.0, door_yaw)
        # spawn_actor_from_class wants a Rotator here, NOT the .rotation of an
        # unreal.Transform (that's internally a Quat and fails to nativize) --
        # build and pass the Rotator directly.
        door_actor = actor_subsystem.spawn_actor_from_class(door_class, spawn_location, spawn_rotation)
        if not door_actor:
            log(f"[{name}] FAILED -- spawn_actor_from_class returned None.")
            results.append((name, False))
            continue

        door_actor.set_actor_label(label)
        try:
            door_actor.set_folder_path(DOOR_FOLDER)
        except Exception as e:
            log(f"[{name}] Note: could not set folder path ({e}), actor still placed fine.")

        log(f"[{name}] Placed '{label}' at ({door_x:.1f},{door_y:.1f},{door_z:.1f}) yaw={door_yaw:.1f} "
            f"(dominant axis for this building: {dominant_axis}, offset distance={world_extent_along_axis:.1f}).")
        results.append((name, True))

    log("---- SUMMARY ----")
    for name, ok in results:
        log(f"{name}: {'PLACED' if ok else 'FAILED'}")
    log("Nothing else was touched -- no collision/carving changes. Review positions/rotations before we carve.")


main()
