"""
FIX THE TILED-LOOKING CONCRETE ON THE GARRISON PLATFORM -- bigger tile
repeat size so it reads as one continuous slab instead of a paver grid
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
M_AI_Ground is triplanar (world-position based, same pattern as
M_AI_CobblestonePath and the mountain/ground materials -- a Constant node
sets how many world-space centimeters one texture repeat covers). That
tile size was fine for the pads/yards it was originally tuned against
(Vehicle Bay ~25m, Parade Yard ~40m), but the new garrison platform is
enormous by comparison -- at that same small tile size, the concrete
texture repeats dozens of times across it, which is exactly the "added in
tiles" grid Shane's screenshot shows.

THE FIX
-------
Same technique as fix_cobblestone_tile_scale.py from earlier this
session: find M_AI_Ground's tile-size Constant node, measure the
platform's REAL current footprint (get_actor_bounds, live geometry not a
guess), and size the tile so roughly a dozen repeats span the platform's
longer dimension -- enough repeats to still show natural concrete
variation up close, but few enough that it doesn't read as a tile grid
from a normal viewing distance. Floored so it's always a real increase
over whatever the current tile size is, capped so it doesn't get so huge
the texture looks like a blurry smear.

M_AI_Ground is shared by other pads (Vehicle Bay, Parade Yard, etc.) --
this changes their tiling too, but a LARGER tile size only ever means
FEWER repeats, so smaller pads that already showed less than one full
tile will just keep looking the same (still no visible seams there).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_concrete_tile_scale.py"
"""

import unreal

M = 100.0
CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"
TARGET_REPEATS_ACROSS_LONG_SIDE = 12.0
MIN_MULTIPLIER_OVER_CURRENT = 3.0   # always at least a 3x bigger tile than whatever it is now
MAX_TILE_SIZE_CM = 8000.0           # 80m cap so it doesn't turn into a blurry smear

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[FixConcreteTileScale] %s" % msg)


def run():
    material = AL.load_asset(CONCRETE_MATERIAL_PATH)
    if material is None:
        log("ABORTED -- %s not found." % CONCRETE_MATERIAL_PATH)
        return

    exprs = MEL.get_material_expressions(material)
    tile_nodes = []
    for e in exprs:
        if isinstance(e, unreal.MaterialExpressionConstant):
            try:
                r = e.get_editor_property("R")
                if 0.00005 < r < 1.0:
                    tile_nodes.append((e, r))
            except Exception:
                pass

    if not tile_nodes:
        log("ABORTED -- couldn't find a tile-size Constant node on M_AI_Ground. It may not use "
            "the same triplanar/Constant-R pattern as the other ground materials -- tell me and "
            "I'll look at its graph a different way.")
        return

    # Measure the platform's real current footprint.
    platform = None
    for a in actor_subsystem.get_all_level_actors():
        if a.get_actor_label() == "GarrisonPlatform_New":
            platform = a
            break

    if platform is not None:
        origin, extent = platform.get_actor_bounds(False)
        span_x, span_y = extent.x * 2.0, extent.y * 2.0
        long_side_cm = max(span_x, span_y)
        log("Platform's real footprint: %.0fm x %.0fm." % (span_x / M, span_y / M))
    else:
        long_side_cm = None
        log("GarrisonPlatform_New not found -- can't measure it, falling back to a flat "
            "multiplier of the current tile size instead.")

    for node, r in tile_nodes:
        current_tile = 1.0 / r
        by_platform = (long_side_cm / TARGET_REPEATS_ACROSS_LONG_SIDE) if long_side_cm else 0.0
        by_multiplier = current_tile * MIN_MULTIPLIER_OVER_CURRENT
        new_tile = min(max(by_platform, by_multiplier), MAX_TILE_SIZE_CM)
        node.set_editor_property("R", 1.0 / new_tile)
        log("M_AI_Ground tile size: %.0fcm -> %.0fcm (%.1fm)." % (current_tile, new_tile, new_tile / M))

    MEL.recompile_material(material)
    log("Done. Save and take a look -- the platform's concrete should read as one continuous "
        "slab now instead of a tight paver grid.")


run()
