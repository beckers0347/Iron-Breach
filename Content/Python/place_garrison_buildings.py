"""
MANUAL PLACEMENT TABLE -- edit the X/Y/Z numbers below, run, done.
================================================================
IRON BREACH / Unreal Engine 5.8

No auto-layout, no remapping, no guessing at the mesh's geometry -- just a
plain table of "this building group goes here." Edit a number, run the
script, that whole building (every wall/door/furniture/light in its
outliner folder) moves there. Leave an entry as None and it's left alone,
but its CURRENT position gets logged so you can see what to type in.

HOW TO USE IT
-------------
1. First run: leave everything as None. It won't move anything -- it just
   logs each building's current X/Y/Z (meters) to the Output Log.
2. Copy those numbers into BUILDING_TARGETS / ACTOR_TARGETS below, tweak
   the ones you want to change, leave the rest as-is (or None to skip).
3. Re-run. Only entries with real numbers move; the rest are left alone
   and re-logged so you always have current values to copy from.

WHAT "X/Y/Z" MEANS FOR EACH KIND OF ENTRY
-------------------------------------------
  - BUILDING_TARGETS (whole outliner folders -- Main Gate, Barracks, etc):
    X/Y move the group's horizontal CENTER (bounding-box centroid) there.
    Z moves the group's FLOOR (the bottom of its bounding box) there --
    not its centroid -- since that's what actually needs to sit on the
    platform's surface. Every actor in the folder (walls, furniture,
    lights, doors -- everything) moves together by the same offset, so
    the room stays exactly as built, just relocated.
  - ACTOR_TARGETS (single actors -- the dock cranes, the ship): X/Y/Z set
    that actor's own location directly, same convention
    build_carrowgate_garrison.py used when it first placed them.

All position values are in METERS, world space (same numbers you'd read
off the Details panel's Location field, divided by 100).

ROTATION -- BUILDING_ROTATIONS / ACTOR_ROTATIONS
-------------------------------------------------
These are DEGREES, and unlike position they're a ONE-TIME DELTA applied
THIS run, not an absolute target -- there's no single "current rotation"
for a whole building (every wall already faces a different direction even
when the room is at its original 0-rotation), so there's nothing stable to
log and re-type like there is for position. Positive = counterclockwise
(standard UE yaw), looking down from above.
  - BUILDING_ROTATIONS: spins the WHOLE folder group as one rigid piece
    around its own current horizontal center -- every actor's position
    gets rotated around that shared pivot AND its own facing rotates by
    the same amount, so the room turns in place without deforming.
  - ACTOR_ROTATIONS: spins that single actor in place (around its own
    location) by that many degrees.
IMPORTANT: set an entry back to 0 (or None) after it runs once, or the
next run will rotate it AGAIN by that same amount -- these do not
self-correct to a target the way position entries do.

SAFE TO RE-RUN for position -- every move is computed fresh from wherever
things currently are to wherever you just typed. Rotation entries are the
one exception (see above) -- reset them to 0/None between runs.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/place_garrison_buildings.py"
"""

import unreal
import math

M = 1.0
ROOT_FOLDER = "Carrowgate Garrison"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# ===========================================================================
# EDIT THESE. (x, y, z) in meters, or None to leave that one alone.
# ===========================================================================

BUILDING_TARGETS = {
    "Main Gate": None,
    "Vehicle Bay": None,
    "Parade Yard": None,
    "Watch Tower": None,
    "Barracks": (7000, 8500, 250),
    "Mess Hall": (3000, 8500, 250),
    "Armory": (9000, -3000, -50),
    "Command & Comms": (4000, -1500, 250),
    "Sensor Array": (10500, -5000, -50),
    "Civic Route (Streets)": None,
}

ACTOR_TARGETS = {
    "Docks_Crane_01": (13500, -3500, 20),
    "Docks_Crane_02":(13500, -4500, 0),
    "Docks_Ship_Hull": (13200, -4000, 0),
}

# Degrees, one-time delta applied THIS run -- see the ROTATION note above.
# Reset to 0 (or None) after running once.
BUILDING_ROTATIONS = {
    "Main Gate": None,
    "Vehicle Bay": None,
    "Parade Yard": None,
    "Watch Tower": None,
    "Barracks": None,
    "Mess Hall": None,
    "Armory": None,
    "Command & Comms": None,
    "Sensor Array": None,
    "Civic Route (Streets)": None,
}

ACTOR_ROTATIONS = {
    "Docks_Crane_01": None,
    "Docks_Crane_02": None,
    "Docks_Ship_Hull": None,
}

# ===========================================================================


def log(msg):
    print("[PlaceGarrisonBuildings] %s" % msg)


def get_all_actors():
    return actor_subsystem.get_all_level_actors()


def folder_actors(folder_path):
    out = []
    for a in get_all_actors():
        folder = str(a.get_folder_path())
        if folder == folder_path or folder.startswith(folder_path + "/"):
            out.append(a)
    return out


def folder_bounds_m(actors):
    """Real bounding box (meters) of every actor in the list, unioned."""
    min_x = min_y = min_z = None
    max_x = max_y = max_z = None
    for a in actors:
        origin, extent = a.get_actor_bounds(False)
        ax0, ax1 = origin.x - extent.x, origin.x + extent.x
        ay0, ay1 = origin.y - extent.y, origin.y + extent.y
        az0, az1 = origin.z - extent.z, origin.z + extent.z
        min_x = ax0 if min_x is None else min(min_x, ax0)
        max_x = ax1 if max_x is None else max(max_x, ax1)
        min_y = ay0 if min_y is None else min(min_y, ay0)
        max_y = ay1 if max_y is None else max(max_y, ay1)
        min_z = az0 if min_z is None else min(min_z, az0)
        max_z = az1 if max_z is None else max(max_z, az1)
    if min_x is None:
        return None
    return (min_x / M, max_x / M, min_y / M, max_y / M, min_z / M, max_z / M)


def rotate_folder_group(folder_path, actors, degrees):
    """Spins every actor in the group around the group's own current
    horizontal (X/Y) center by `degrees` -- rigid rotation, positions AND
    facings both turn together, so the room doesn't deform."""
    bounds = folder_bounds_m(actors)
    min_x, max_x, min_y, max_y, _, _ = bounds
    px, py = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0  # pivot, meters
    rad = math.radians(degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    for a in actors:
        loc = a.get_actor_location()
        lx, ly = loc.x / M, loc.y / M
        rx, ry = lx - px, ly - py
        nx = px + (rx * cos_a - ry * sin_a)
        ny = py + (rx * sin_a + ry * cos_a)
        a.set_actor_location(unreal.Vector(nx * M, ny * M, loc.z), False, False)

        rot = a.get_actor_rotation()
        a.set_actor_rotation(unreal.Rotator(rot.roll, rot.pitch, rot.yaw + degrees), False)


def run():
    log("--- Building rotations (one-time deltas) ---")
    for name, degrees in BUILDING_ROTATIONS.items():
        if not degrees:
            continue
        folder_path = f"{ROOT_FOLDER}/{name}"
        actors = folder_actors(folder_path)
        if not actors:
            log("'%s': no actors found -- skipped rotation." % name)
            continue
        rotate_folder_group(folder_path, actors, degrees)
        log("'%s': rotated %d actor(s) by %.1f degrees around its own center. Set this back to "
            "0/None before the next run." % (name, len(actors), degrees))

    log("--- Actor rotations (one-time deltas) ---")
    all_actors_for_rot = get_all_actors()
    for label, degrees in ACTOR_ROTATIONS.items():
        if not degrees:
            continue
        actor = next((a for a in all_actors_for_rot if a.get_actor_label() == label), None)
        if actor is None:
            log("'%s': actor not found -- skipped rotation." % label)
            continue
        rot = actor.get_actor_rotation()
        actor.set_actor_rotation(unreal.Rotator(rot.roll, rot.pitch, rot.yaw + degrees), False)
        log("'%s': rotated by %.1f degrees. Set this back to 0/None before the next run." % (label, degrees))

    log("--- Building groups ---")
    for name, target in BUILDING_TARGETS.items():
        folder_path = f"{ROOT_FOLDER}/{name}"
        actors = folder_actors(folder_path)
        if not actors:
            log("'%s': no actors found under that folder -- skipped." % name)
            continue

        bounds = folder_bounds_m(actors)
        min_x, max_x, min_y, max_y, min_z, max_z = bounds
        cur_cx, cur_cy, cur_floor_z = (min_x + max_x) / 2.0, (min_y + max_y) / 2.0, min_z

        if target is None:
            log("'%s': currently at center=(%.1f, %.1f)  floor_z=%.1f  (%d actors) -- copy these "
                "into BUILDING_TARGETS to edit." % (name, cur_cx, cur_cy, cur_floor_z, len(actors)))
            continue

        tx, ty, tz = target
        dx, dy, dz = tx - cur_cx, ty - cur_cy, tz - cur_floor_z
        if abs(dx) < 0.05 and abs(dy) < 0.05 and abs(dz) < 0.05:
            log("'%s': already at target -- left alone." % name)
            continue

        offset = unreal.Vector(dx * M, dy * M, dz * M)
        for a in actors:
            a.add_actor_world_offset(offset, False, False)
        log("'%s': %d actor(s) moved by (%.1f, %.1f, %.1f)m -> center now (%.1f, %.1f), floor now %.1f." % (
            name, len(actors), dx, dy, dz, tx, ty, tz))

    log("--- Individual actors ---")
    all_actors = get_all_actors()
    for label, target in ACTOR_TARGETS.items():
        actor = next((a for a in all_actors if a.get_actor_label() == label), None)
        if actor is None:
            log("'%s': actor not found -- skipped." % label)
            continue

        loc = actor.get_actor_location()
        cur_x, cur_y, cur_z = loc.x / M, loc.y / M, loc.z / M

        if target is None:
            log("'%s': currently at (%.1f, %.1f, %.1f) -- copy this into ACTOR_TARGETS to edit." % (
                label, cur_x, cur_y, cur_z))
            continue

        tx, ty, tz = target
        if abs(tx - cur_x) < 0.05 and abs(ty - cur_y) < 0.05 and abs(tz - cur_z) < 0.05:
            log("'%s': already at target -- left alone." % label)
            continue

        actor.set_actor_location(unreal.Vector(tx * M, ty * M, tz * M), False, False)
        log("'%s': moved to (%.1f, %.1f, %.1f)." % (label, tx, ty, tz))

    log("Done. Save and take a look. Anything left as None above just got logged, not moved -- "
        "edit the numbers and re-run for those. Any rotation you just used: reset it to 0/None "
        "now, or it'll rotate again next run.")


run()
