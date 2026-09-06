"""
MOVE THE BUILDINGS ONTO THE PLATFORM v2 -- same as before, now dodges the
round helipad lobe (Mess Hall is confirmed sitting on it right now, so
that's used as the reference point to define the no-build zone)
================================================================
IRON BREACH / Unreal Engine 5.8

Same live-measured approach as move_buildings_onto_platform.py -- reads
GarrisonPlatform_New's real current footprint, doesn't touch the platform
itself, remaps every building group's documented original position into
that footprint, moves each group from wherever it ACTUALLY is right now.

NEW: Shane confirmed the round lobe is the helipad and nothing should be on
it -- and that Mess Hall is the building currently sitting there, which
means Mess Hall's CURRENT position is a real, measured point inside the
helipad. This script uses that as the center of a no-build circle (radius
guessed from the platform's overall size -- logged clearly below so it can
be tuned) and pushes any building's target position that would land inside
that circle radially outward until it clears it, before moving anything.
That includes Mess Hall itself, which is exactly what needs to move off
the helipad this run.

This still can't see the mesh's actual geometry -- the circle is a guess
anchored to one real data point (Mess Hall's current spot). If the guessed
radius is too small (something still clips the helipad's edge) or too big
(it's eating into usable main-body space), say so and I'll adjust
HELIPAD_RADIUS_FRACTION directly.

SAFE TO RE-RUN.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/move_buildings_onto_platform_v2.py"
"""

import unreal
import math

M = 100.0
ROOT_FOLDER = "Carrowgate Garrison"
MARGIN = 0.15
HELIPAD_RADIUS_FRACTION = 0.22  # of the platform's larger span -- tune this if the circle's wrong
HELIPAD_BUFFER_M = 4.0  # extra clearance past the guessed radius

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
    print("[MoveBuildingsOntoPlatformV2] %s" % msg)


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

    # -- Establish the helipad no-build circle from Mess Hall's CURRENT (on
    #    the helipad, per Shane) position, measured before anything moves. --
    mess_hall_actors = folder_actors(f"{ROOT_FOLDER}/Mess Hall")
    helipad_center = folder_centroid_xy(mess_hall_actors) if mess_hall_actors else None
    helipad_radius = HELIPAD_RADIUS_FRACTION * max(span_x, span_y)
    if helipad_center is not None:
        log("Helipad no-build zone: center=(%.1f, %.1f)m [Mess Hall's current spot], "
            "radius=%.1fm (%.0f%% of platform span + %.1fm buffer)." % (
                helipad_center[0], helipad_center[1], helipad_radius + HELIPAD_BUFFER_M,
                HELIPAD_RADIUS_FRACTION * 100, HELIPAD_BUFFER_M))
    else:
        log("Mess Hall folder not found -- can't establish the helipad no-build zone, "
            "proceeding without it.")

    def push_outside_helipad(x, y):
        if helipad_center is None:
            return x, y
        hx, hy = helipad_center
        dx, dy = x - hx, y - hy
        dist = math.sqrt(dx * dx + dy * dy)
        min_dist = helipad_radius + HELIPAD_BUFFER_M
        if dist >= min_dist:
            return x, y
        if dist < 1e-4:
            # Target landed dead-on the helipad center -- push toward the platform's
            # overall centroid direction as a sane default.
            dx, dy = (plat_min_x + plat_max_x) / 2.0 - hx, (plat_min_y + plat_max_y) / 2.0 - hy
            dist = math.sqrt(dx * dx + dy * dy) or 1.0
        scale = min_dist / dist
        return hx + dx * scale, hy + dy * scale

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

    for area_name, (ox, oy) in OLD_AREA_POS.items():
        folder_path = f"{ROOT_FOLDER}/{area_name}"
        actors = folder_actors(folder_path)
        if not actors:
            log("'%s': no actors found -- skipped." % area_name)
            continue

        target_x, target_y = remap(ox, oy)
        target_x, target_y = push_outside_helipad(target_x, target_y)

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

    log("Done. Save and take a look. If anything's still on the round helipad, or the "
        "no-build circle is eating too much of the main body, tell me and I'll adjust "
        "HELIPAD_RADIUS_FRACTION directly.")


run()
