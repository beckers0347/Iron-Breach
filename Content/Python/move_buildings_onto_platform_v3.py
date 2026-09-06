"""
MOVE THE BUILDINGS ONTO THE PLATFORM v3 -- fixes v2's self-reference bug:
the helipad center is now a fixed computed point, not "wherever Mess Hall
currently is" (which stops being true the moment Mess Hall gets moved off
the helipad by this same script).
================================================================
IRON BREACH / Unreal Engine 5.8

v2 measured Mess Hall's CURRENT position and called that the helipad
center -- true the first time (Shane confirmed Mess Hall was sitting on
the helipad), but false on every run after that, since the whole point of
the script is to move Mess Hall away from there. Re-running it kept
re-deriving the "helipad center" from Mess Hall's new (already-pushed)
position, which drifts the no-build zone a little further off target each
time instead of using one stable point.

Fixed properly this time: since GarrisonPlatform_New's position isn't
touched by this script and Shane isn't moving it either, the RAW remap of
Mess Hall's documented original position (before any push-out) lands on
the exact same point every single run -- that point IS a stable, reliable
stand-in for "a point on the helipad" (confirmed by Shane), independent of
where Mess Hall actually is right now. That's what's used as the no-build
circle's center this time, computed fresh each run but always the same
value as long as the platform doesn't move.

Also widened the circle (0.22 -> 0.32 of platform span, buffer 4m -> 10m)
since the last screenshot still showed one thing clipping the helipad's
edge.

SAFE TO RE-RUN -- and this time actually converges instead of drifting,
since the no-build center no longer depends on anything this script itself
moves.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/move_buildings_onto_platform_v3.py"
"""

import unreal
import math

M = 100.0
ROOT_FOLDER = "Carrowgate Garrison"
MARGIN = 0.15
HELIPAD_RADIUS_FRACTION = 0.32
HELIPAD_BUFFER_M = 10.0
HELIPAD_REFERENCE_AREA = "Mess Hall"  # Shane confirmed this one lands on the helipad

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

OLD_AREA_POS = {
    "Main Gate": (0.0, 0.0),
    "Vehicle Bay": (35.0, -3.0),
    "Parade Yard": (46.0, 16.0),
    "Watch Tower": (56.0, 44.0),
    "Barracks": (55.0, -32.0),
    "Mess Hall": (96.0, 8.0),
    "Armory": (112.0, -15.0),
    "Command & Comms": (73.0, -61.0),
    "Sensor Array": (59.0, 30.0),
    "Civic Route (Streets)": (95.0, -77.5),
    "Docks / Harbor": (116.0, -126.0),
}


def log(msg):
    print("[MoveBuildingsOntoPlatformV3] %s" % msg)


def get_all_actors():
    return actor_subsystem.get_all_level_actors()


def folder_actors(folder_path):
    out = []
    for a in get_all_actors():
        folder = str(a.get_folder_path())
        if folder == folder_path or folder.startswith(folder_path + "/"):
            out.append(a)
    return out


def folder_centroid_xy(actors):
    min_x = min_y = None
    max_x = max_y = None
    for a in actors:
        origin, extent = a.get_actor_bounds(False)
        ax0, ax1 = origin.x - extent.x, origin.x + extent.x
        ay0, ay1 = origin.y - extent.y, origin.y + extent.y
        min_x = ax0 if min_x is None else min(min_x, ax0)
        max_x = ax1 if max_x is None else max(max_x, ax1)
        min_y = ay0 if min_y is None else min(min_y, ay0)
        max_y = ay1 if max_y is None else max(max_y, ay1)
    if min_x is None:
        return None
    return ((min_x + max_x) / 2.0 / M, (min_y + max_y) / 2.0 / M)


def run():
    platform = None
    for a in get_all_actors():
        if a.get_actor_label() == "GarrisonPlatform_New":
            platform = a
            break
    if platform is None:
        log("ABORTED -- GarrisonPlatform_New not found.")
        return

    origin, extent = platform.get_actor_bounds(False)
    plat_min_x, plat_max_x = (origin.x - extent.x) / M, (origin.x + extent.x) / M
    plat_min_y, plat_max_y = (origin.y - extent.y) / M, (origin.y + extent.y) / M
    span_x = plat_max_x - plat_min_x
    span_y = plat_max_y - plat_min_y
    log("Platform's current real footprint: X=[%.1f, %.1f]  Y=[%.1f, %.1f] (meters)." % (
        plat_min_x, plat_max_x, plat_min_y, plat_max_y))

    old_xs = [p[0] for p in OLD_AREA_POS.values()]
    old_ys = [p[1] for p in OLD_AREA_POS.values()]
    old_min_x, old_max_x = min(old_xs), max(old_xs)
    old_min_y, old_max_y = min(old_ys), max(old_ys)

    new_min_x = plat_min_x + MARGIN * span_x
    new_max_x = plat_max_x - MARGIN * span_x
    new_min_y = plat_min_y + MARGIN * span_y
    new_max_y = plat_max_y - MARGIN * span_y

    def remap(old_x, old_y):
        tx = 0.5 if old_max_x == old_min_x else (old_x - old_min_x) / (old_max_x - old_min_x)
        ty = 0.5 if old_max_y == old_min_y else (old_y - old_min_y) / (old_max_y - old_min_y)
        return new_min_x + tx * (new_max_x - new_min_x), new_min_y + ty * (new_max_y - new_min_y)

    # Stable helipad reference point: the RAW remap of Mess Hall's documented
    # position, recomputed fresh but always the same value run to run (as
    # long as the platform itself doesn't move) -- NOT wherever Mess Hall
    # currently sits, which changes once this script moves it.
    helipad_center = remap(*OLD_AREA_POS[HELIPAD_REFERENCE_AREA])
    helipad_radius = HELIPAD_RADIUS_FRACTION * max(span_x, span_y)
    min_dist = helipad_radius + HELIPAD_BUFFER_M
    log("Helipad no-build zone (fixed): center=(%.1f, %.1f)m, radius=%.1fm." % (
        helipad_center[0], helipad_center[1], min_dist))

    def push_outside_helipad(x, y):
        hx, hy = helipad_center
        dx, dy = x - hx, y - hy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist >= min_dist:
            return x, y
        if dist < 1e-4:
            dx, dy = (plat_min_x + plat_max_x) / 2.0 - hx, (plat_min_y + plat_max_y) / 2.0 - hy
            dist = math.sqrt(dx * dx + dy * dy) or 1.0
        scale = min_dist / dist
        return hx + dx * scale, hy + dy * scale

    for area_name, (ox, oy) in OLD_AREA_POS.items():
        folder_path = f"{ROOT_FOLDER}/{area_name}"
        actors = folder_actors(folder_path)
        if not actors:
            log("'%s': no actors found -- skipped." % area_name)
            continue

        raw_x, raw_y = remap(ox, oy)
        target_x, target_y = push_outside_helipad(raw_x, raw_y)

        centroid = folder_centroid_xy(actors)
        cur_x, cur_y = centroid
        dx, dy = target_x - cur_x, target_y - cur_y
        if abs(dx) < 0.05 and abs(dy) < 0.05:
            log("'%s': already on target -- left alone." % area_name)
            continue

        offset = unreal.Vector(dx * M, dy * M, 0.0)
        for a in actors:
            a.add_actor_world_offset(offset, False, False)
        log("'%s': %d actor(s) moved by (%.1f, %.1f)m -> now centered near (%.1f, %.1f)m." % (
            area_name, len(actors), dx, dy, target_x, target_y))

    log("Done. Save and take a look. Still tunable -- HELIPAD_RADIUS_FRACTION/HELIPAD_BUFFER_M "
        "at the top of this file if the circle's still off, and this time it'll actually hold "
        "steady across re-runs instead of drifting.")


run()
