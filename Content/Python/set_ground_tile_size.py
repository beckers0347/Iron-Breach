"""
SET GROUND TILE SIZE -- edit TILE_SIZE_METERS below and rerun any time you
want to change it. No more fiddling with the confusing 1/size R value by
hand in the Material Editor.
================================================================
IRON BREACH / Unreal Engine 5.8

The manual edits to R=1 and R=100 in the Material Editor put the tile
size at 1cm and 0.01cm -- both WAY too small to render correctly, which
is why it turned into a diamond/argyle-looking noise pattern (texture
aliasing/moire from a repeat rate way higher than the screen can resolve
-- not an actual tiling problem). The tile size needs to be in the
THOUSANDS of cm (tens of meters) range for something this large, same as
right after the original rebuild (which looked correct -- real concrete
slab joints, no artifact pattern).

Just change TILE_SIZE_METERS below to whatever you want and rerun this --
it finds the tile-scale node (identified as the Constant that ISN'T the
roughness constant [0.85] or the blend-sharpness constant [4.0], so it's
safe even though the graph's node ordering has shifted around) and sets
it directly, no manual node-clicking needed.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/set_ground_tile_size.py"
"""

import unreal

CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"

# ---- EDIT THIS AND RERUN TO CHANGE THE TILE SIZE ----
TILE_SIZE_METERS = 40.0
# -------------------------------------------------------

KNOWN_OTHER_CONSTANTS = (0.85, 4.0)  # roughness, blend-sharpness -- never touch these
TOLERANCE = 0.01

M = 100.0
MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary


def log(msg):
    print("[SetGroundTileSize] %s" % msg)


def run():
    material = AL.load_asset(CONCRETE_MATERIAL_PATH)
    if material is None:
        log("ABORTED -- %s not found." % CONCRETE_MATERIAL_PATH)
        return

    exprs = MEL.get_material_expressions(material)
    candidates = []
    for i, e in enumerate(exprs):
        if isinstance(e, unreal.MaterialExpressionConstant):
            r = e.get_editor_property("R")
            is_known = any(abs(r - k) < TOLERANCE for k in KNOWN_OTHER_CONSTANTS)
            if not is_known:
                candidates.append((i, e, r))

    if len(candidates) == 0:
        log("ABORTED -- no candidate tile-scale Constant found (only roughness/sharpness constants "
            "exist). Tell me and we'll re-diagnose.")
        return
    if len(candidates) > 1:
        log("ABORTED -- found %d candidates, not sure which is the tile-scale node:" % len(candidates))
        for i, e, r in candidates:
            log("  [%d] R=%.8f" % (i, r))
        log("Tell me which index looks right (or paste this) and I'll target it directly.")
        return

    idx, node, old_r = candidates[0]
    old_tile_cm = (1.0 / old_r) if old_r else 0.0
    new_tile_cm = TILE_SIZE_METERS * M
    new_r = 1.0 / new_tile_cm
    node.set_editor_property("R", new_r)
    log("Tile-scale node [%d]: R %.8f (%.1fm) -> R %.8f (%.1fm)" % (
        idx, old_r, old_tile_cm / M, new_r, TILE_SIZE_METERS))

    MEL.recompile_material(material)
    log("Recompiled. Save and take a look.")


run()
