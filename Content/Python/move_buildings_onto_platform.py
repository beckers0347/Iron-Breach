"""
MOVE THE BUILDINGS ONTO THE PLATFORM -- reads GarrisonPlatform_New's
CURRENT real position/size (wherever you've since placed it by hand) and
fits every building group into its footprint. Does NOT touch the platform.
================================================================
IRON BREACH / Unreal Engine 5.8

Doesn't touch GarrisonPlatform_New's position, rotation, or scale at all --
just measures its real current world footprint (get_actor_bounds, so this
is live geometry, not a remembered number) and uses that as the target
area. Same idea as the original rebuild pass (proportionally remap each
building's documented original position into the platform's footprint,
inset by a margin so nothing hangs off an edge), but this time it's safe
because the platform is the one YOU sized and placed, not a runaway 1500x
scale.

Every building group is moved from wherever it ACTUALLY is right now
(measured bounding-box centroid, same as the last fix pass) to its new
target -- so it doesn't matter if some are already close and some are still
way off, this corrects all of them from their real current spot.

Can't tell which part of your mesh is the helipad vs. the dock vs. the
ramp, so it can't specifically dodge those -- if something lands on the
round helipad or the lower dock, that's a manual nudge afterward.

SAFE TO RE-RUN -- everything is measured fresh from current positions each
time.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/move_buildings_onto_platform.py"
"""

import unreal

M = 100.0
ROOT_FOLDER = "Carrowgate Garrison"
MARGIN = 0.15

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
    print("[MoveBuildingsOntoPlatform] %s" % msg)


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
    log("Platform's current real footprint: X=[%.1f, %.1f]  Y=[%.1f, %.1f] (meters)." % (
        plat_min_x, plat_max_x, plat_min_y, plat_max_y))

    old_xs = [p[0] for p in OLD_AREA_POS.values()]
    old_ys = [p[1] for p in OLD_AREA_POS.values()]
    old_min_x, old_max_x = min(old_xs), max(old_xs)
    old_min_y, old_max_y = min(old_ys), max(old_ys)

    span_x = plat_max_x - plat_min_x
    span_y = plat_max_y - plat_min_y
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

    log("Done. Save and take a look. Anything that landed on the round helipad or the lower "
        "dock is a manual drag from here -- this script can't see those sub-shapes inside "
        "your mesh.")


run()
