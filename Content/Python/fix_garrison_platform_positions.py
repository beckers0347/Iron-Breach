"""
UNDO THE BUILDING SHIFT FROM rebuild_garrison_platform.py -- moves every
repositioned area back to its original spot, leaves the new platform alone
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT WENT WRONG
----------------
rebuild_garrison_platform.py proportionally remapped every building's old
position into the new platform's ACTUAL measured footprint. That worked
fine as an idea, but the platform at 1500/1500/1500 scale turned out to be
enormous (its real measured bounds are logged below) -- and remapping into
a footprint that big, with an inset margin, threw every building's target
position way off to one side, far enough to land in the middle of the town
instead of anywhere near the garrison. Nothing was deleted or lost -- it's
all still there, just relocated.

WHAT THIS SCRIPT DOES
-----------------------
Re-finds GarrisonPlatform_New, reads its CURRENT real-world bounds (same
query the original script used), reconstructs the EXACT SAME remap that
script computed (same OLD_AREA_POS constants, same 0.15 margin), and moves
every area folder back by the exact inverse of the delta that was applied
-- putting every building back to its original position, byte for byte.
It does NOT touch the platform itself (position, scale, or rotation) --
that's left for a separate, deliberate pass once we agree on the right
scale for it.

IMPORTANT: only run this ONCE, and only if you haven't manually moved
GarrisonPlatform_New or any of the buildings since the bad run -- it
recomputes the same math from the platform's current bounds, so if the
platform moved since then, the inverse won't line up.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_garrison_platform_positions.py"
"""

import unreal

M = 100.0
ROOT_FOLDER = "Carrowgate Garrison"
MARGIN = 0.15  # must match rebuild_garrison_platform.py exactly

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
    print("[FixGarrisonPlatformPositions] %s" % msg)


def get_all_actors():
    return actor_subsystem.get_all_level_actors()


def move_folder(folder_path, dx_m, dy_m, dz_m=0.0):
    offset = unreal.Vector(dx_m * M, dy_m * M, dz_m * M)
    moved = 0
    for a in get_all_actors():
        folder = str(a.get_folder_path())
        if folder == folder_path or folder.startswith(folder_path + "/"):
            a.add_actor_world_offset(offset, False, False)
            moved += 1
    return moved


def run():
    platform = None
    for a in get_all_actors():
        if a.get_actor_label() == "GarrisonPlatform_New":
            platform = a
            break
    if platform is None:
        log("ABORTED -- no GarrisonPlatform_New actor found. Nothing to undo, or it's "
            "already been renamed/removed.")
        return

    origin, extent = platform.get_actor_bounds(False)
    plat_min_x, plat_max_x = (origin.x - extent.x) / M, (origin.x + extent.x) / M
    plat_min_y, plat_max_y = (origin.y - extent.y) / M, (origin.y + extent.y) / M
    log("Platform's current real footprint: X=[%.1f, %.1f]  Y=[%.1f, %.1f] (meters) -- "
        "reconstructing the same remap from this." % (plat_min_x, plat_max_x, plat_min_y, plat_max_y))

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
        nx, ny = remap(ox, oy)
        dx, dy = nx - ox, ny - oy  # the delta the bad run applied
        # Apply the inverse to put it back.
        moved = move_folder(f"{ROOT_FOLDER}/{area_name}", -dx, -dy, 0.0)
        if moved:
            log("Restored '%s': %d actor(s) moved back by (%.1f, %.1f)m." % (area_name, moved, -dx, -dy))
        else:
            log("'%s': no actors found under that folder -- nothing to restore." % area_name)

    log("Done. Every building should be back at its original position. The platform itself "
        "was left untouched -- take a look at its size next to the restored buildings and "
        "tell me what scale actually looks right (1500 was clearly too big); I'll adjust just "
        "the platform from there without touching the buildings again.")


run()
