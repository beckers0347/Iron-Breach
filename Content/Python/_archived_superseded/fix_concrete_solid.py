"""
CONCRETE AS ONE SOLID PIECE -- tile size big enough that only ~1 repeat
spans the whole platform, so there's no visible seam/grid anywhere
================================================================
IRON BREACH / Unreal Engine 5.8

The last pass (fix_concrete_tile_scale.py) aimed for ~12 repeats across
the platform's long side -- enough to avoid a tight paver grid, but still
enough repeats that the seams were visible. This goes further: sizes the
tile so roughly ONE repeat covers the platform's entire longer dimension,
so there's nothing left to repeat and it reads as one continuous slab.

Trade-off, worth knowing up front: at this scale the source photo texture
gets stretched a lot, so up close (standing on it, not looking across the
whole platform) it'll look softer/blurrier than a normal-scale concrete
texture would -- that's an inherent trade-off of "no visible tiling" on
something this large with a single tileable photo texture, not a bug.
Say so if that's too soft and we can find a middle ground (fewer repeats,
i.e. some seams, in exchange for sharper close-up detail), or look at a
different approach (a macro-variation/detail-blend texture instead of one
flat tile) if you want both.

Same identification logic as the last two fixes -- only touches the real
tile-scale node (the one wired into the WorldPosition multiply), leaves
Roughness/Metallic/Specular alone this time since those are already fixed.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_concrete_solid.py"
"""

import unreal

M = 100.0
CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"
TARGET_REPEATS_ACROSS_LONG_SIDE = 1.0

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[FixConcreteSolid] %s" % msg)


def find_tile_scale_node(exprs):
    multiplies = [e for e in exprs if isinstance(e, unreal.MaterialExpressionMultiply)]
    for mul in multiplies:
        try:
            a_conn = mul.get_editor_property("a")
            b_conn = mul.get_editor_property("b")
        except Exception:
            continue
        a_expr = a_conn.expression if a_conn else None
        b_expr = b_conn.expression if b_conn else None
        for x, y in ((a_expr, b_expr), (b_expr, a_expr)):
            if isinstance(x, unreal.MaterialExpressionWorldPosition) and isinstance(y, unreal.MaterialExpressionConstant):
                return y
    return None


def run():
    material = AL.load_asset(CONCRETE_MATERIAL_PATH)
    if material is None:
        log("ABORTED -- %s not found." % CONCRETE_MATERIAL_PATH)
        return

    exprs = MEL.get_material_expressions(material)
    tile_node = find_tile_scale_node(exprs)
    if tile_node is None:
        log("ABORTED -- couldn't find the tile-scale node via its wiring.")
        return

    platform = None
    for a in actor_subsystem.get_all_level_actors():
        if a.get_actor_label() == "GarrisonPlatform_New":
            platform = a
            break
    if platform is None:
        log("ABORTED -- GarrisonPlatform_New not found, can't measure it to size the tile.")
        return

    origin, extent = platform.get_actor_bounds(False)
    span_x, span_y = extent.x * 2.0, extent.y * 2.0
    long_side_cm = max(span_x, span_y)
    log("Platform's real footprint: %.0fm x %.0fm." % (span_x / M, span_y / M))

    old_tile = 1.0 / tile_node.get_editor_property("R")
    new_tile = long_side_cm / TARGET_REPEATS_ACROSS_LONG_SIDE
    tile_node.set_editor_property("R", 1.0 / new_tile)
    log("Tile size: %.0fcm -> %.0fcm (%.0fm) -- ~%.1f repeat(s) across the platform's long side." % (
        old_tile, new_tile, new_tile / M, TARGET_REPEATS_ACROSS_LONG_SIDE))

    MEL.recompile_material(material)
    log("Done. Save and take a look. If it's too soft/blurry up close, tell me and we'll dial "
        "back toward a few repeats instead of exactly one.")


run()
