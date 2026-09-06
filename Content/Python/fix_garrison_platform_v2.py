"""
GARRISON RECOVERY v2 -- restore every building group to its documented
original position using CURRENT measured positions, not assumed history
================================================================
IRON BREACH / Unreal Engine 5.8

WHY v2
------
The first fix script assumed nothing had moved except by its own earlier
math, and reconstructed a delta from that assumption -- but the platform
(and maybe other things) got manually nudged/rotated in between, so that
reconstruction was working from the wrong starting point and made it
worse.

This version doesn't try to reconstruct any history at all. For every area
folder, it measures where its actors ACTUALLY are right now (the real
bounding-box centroid of everything under that folder), compares that to
the documented original design position (straight from
build_carrowgate_garrison.py's AREAS list), and moves the whole folder by
the exact difference. It doesn't matter how many times something got
shifted since -- this always corrects from wherever things actually are
now.

Also resets GarrisonPlatform_New itself: rotation back to (0,0,0), X/Y back
to the garrison's original centroid, Z re-grounded so its top sits at 0 --
its scale (1500/1500/1500) is left alone since that's a separate question
(how big it actually reads once everything else is back in place) that's
easiest to judge visually once this run is done.

SAFE TO RE-RUN. Every correction is measured fresh from current positions,
so running it again after things are already correct just computes a
near-zero delta and does nothing.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_garrison_platform_v2.py"
"""

import unreal

M = 100.0
ROOT_FOLDER = "Carrowgate Garrison"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Documented original design centers (meters, X/Y), straight from
# build_carrowgate_garrison.py's AREAS list.
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
    print("[GarrisonRecoveryV2] %s" % msg)


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
    """Real bounding-box centroid (meters) of every actor in the list, unioned."""
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
    # -- 1. Restore every building group to its documented position ---------
    for area_name, (target_x, target_y) in OLD_AREA_POS.items():
        folder_path = f"{ROOT_FOLDER}/{area_name}"
        actors = folder_actors(folder_path)
        if not actors:
            log("'%s': no actors found under that folder -- skipped." % area_name)
            continue
        centroid = folder_centroid_xy(actors)
        cur_x, cur_y = centroid
        dx, dy = target_x - cur_x, target_y - cur_y
        if abs(dx) < 0.05 and abs(dy) < 0.05:
            log("'%s': already at its correct position (within 5cm) -- left alone." % area_name)
            continue
        offset = unreal.Vector(dx * M, dy * M, 0.0)
        for a in actors:
            a.add_actor_world_offset(offset, False, False)
        log("'%s': measured centroid was (%.1f, %.1f)m, moved %d actor(s) by (%.1f, %.1f)m to "
            "land on its documented position (%.1f, %.1f)m." % (
                area_name, cur_x, cur_y, len(actors), dx, dy, target_x, target_y))

    # -- 2. Reset the platform itself: rotation to 0, X/Y to the garrison's --
    #    original centroid, Z re-grounded. Scale left untouched.
    platform = None
    for a in get_all_actors():
        if a.get_actor_label() == "GarrisonPlatform_New":
            platform = a
            break

    if platform is None:
        log("GarrisonPlatform_New not found -- skipping platform reset.")
    else:
        old_xs = [p[0] for p in OLD_AREA_POS.values()]
        old_ys = [p[1] for p in OLD_AREA_POS.values()]
        centroid_x = (min(old_xs) + max(old_xs)) / 2.0
        centroid_y = (min(old_ys) + max(old_ys)) / 2.0

        platform.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
        platform.set_actor_location(unreal.Vector(centroid_x * M, centroid_y * M, 0.0), False, False)

        origin, extent = platform.get_actor_bounds(False)
        top_z = origin.z + extent.z
        platform.add_actor_world_offset(unreal.Vector(0.0, 0.0, -top_z), False, False)

        origin, extent = platform.get_actor_bounds(False)
        pmin_x, pmax_x = (origin.x - extent.x) / M, (origin.x + extent.x) / M
        pmin_y, pmax_y = (origin.y - extent.y) / M, (origin.y + extent.y) / M
        pmin_z, pmax_z = (origin.z - extent.z) / M, (origin.z + extent.z) / M
        log("GarrisonPlatform_New reset: rotation=(0,0,0), centered at (%.1f, %.1f)m, "
            "re-grounded. Real footprint now: X=[%.1f, %.1f]  Y=[%.1f, %.1f]  Z=[%.1f, %.1f] "
            "(meters, scale still %s)." % (
                centroid_x, centroid_y, pmin_x, pmax_x, pmin_y, pmax_y, pmin_z, pmax_z,
                str(platform.static_mesh_component.get_editor_property("relative_scale3d"))))

    log("Done. Save and take a look. Everything should be back in the garrison's original "
        "footprint now, platform included. If the platform still reads way too big or small "
        "next to the restored buildings, tell me the scale you actually want and I'll change "
        "just that -- buildings won't move again.")


run()
