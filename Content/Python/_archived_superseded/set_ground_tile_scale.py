"""
SET THE GROUND TILE SCALE DIRECTLY -- bypasses manual node editing to rule
out user-side mistakes (wrong node, missed Apply, stale viewport)
================================================================
IRON BREACH / Unreal Engine 5.8

Manual edits in the Material Editor (setting the tile-scale Constant to 1,
then 100) produced no visible change on the platform, even though the
platform's mesh slot is confirmed to be the live M_AI_Ground material
(not a baked instance). A change that large should be unmistakable, so
before chasing anything else, this sets the SAME node directly via
Python and recompiles -- if the platform visibly changes after this runs,
the material pipeline is fine and the problem was something in the manual
edit (wrong node selected, Apply not clicked, etc). If it STILL doesn't
change, the problem is downstream of the material entirely (e.g. Nanite
mesh distance field / Lumen surface cache needs a hard refresh, or the
viewport needs to actually move/rebuild).

Sets tile size to 800cm (8m) -- deliberately different enough from the
105m tile currently set that it cannot be missed if it takes effect.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/set_ground_tile_scale.py"
"""

import unreal

CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"
NEW_TILE_WORLD_SIZE_CM = 800.0

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary


def log(msg):
    print("[SetGroundTileScale] %s" % msg)


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
    log("M_AI_Ground currently has %d expression node(s)." % len(exprs))

    tile_node = find_tile_scale_node(exprs)
    if tile_node is None:
        log("ABORTED -- couldn't find the tile-scale node via its wiring. The graph may have "
            "changed since the rebuild -- tell me and I'll add a diagnostic to relocate it.")
        return

    old_r = tile_node.get_editor_property("R")
    old_tile = (1.0 / old_r) if old_r else 0.0
    new_r = 1.0 / NEW_TILE_WORLD_SIZE_CM
    tile_node.set_editor_property("R", new_r)
    log("Tile-scale Constant: R %.8f (tile=%.0fcm) -> R %.8f (tile=%.0fcm)" % (
        old_r, old_tile, new_r, NEW_TILE_WORLD_SIZE_CM))

    MEL.recompile_material(material)
    log("Recompiled. Save, then LOOK at the platform without touching anything else -- if it's "
        "still identical to before, the problem isn't the material node, tell me and we'll dig into "
        "the viewport/render side instead.")


run()
