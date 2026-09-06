"""
DIAGNOSE M_AI_GROUND'S CURRENT GRAPH (v2) -- read-only, changes nothing
================================================================
IRON BREACH / Unreal Engine 5.8

The graph had 24 nodes right after the from-scratch rebuild; it now has
45. Something (an Apply/compile cycle in the Material Editor, or manual
node creation while poking at this) added more nodes since. Rather than
guess at the new structure, this lists every node with an index, and for
every Multiply node it tries to identify BOTH inputs (so we can find every
WorldPosition*Constant pair now, not just assume there's still only one).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/diagnose_ground_v2.py"
"""

import unreal

CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary


def log(msg):
    print("[DiagnoseGroundV2] %s" % msg)


def run():
    material = AL.load_asset(CONCRETE_MATERIAL_PATH)
    if material is None:
        log("ABORTED -- %s not found." % CONCRETE_MATERIAL_PATH)
        return

    exprs = MEL.get_material_expressions(material)

    def idx_of(e):
        return exprs.index(e) if e in exprs else -1

    def short(e):
        if e is None:
            return "None"
        return "[%d] %s" % (idx_of(e), type(e).__name__)

    log("Total nodes: %d" % len(exprs))

    log("--- All Constant nodes (possible tile-scale candidates) ---")
    for i, e in enumerate(exprs):
        if isinstance(e, unreal.MaterialExpressionConstant):
            r = e.get_editor_property("R")
            tile = (1.0 / r) if r else 0.0
            log("  [%d] Constant  R=%.8f  (tile=%.1fcm if this is a tile-scale node)" % (i, r, tile))

    log("--- All WorldPosition nodes ---")
    for i, e in enumerate(exprs):
        if isinstance(e, unreal.MaterialExpressionWorldPosition):
            log("  [%d] WorldPosition" % i)

    log("--- All Multiply nodes and both their inputs ---")
    for i, e in enumerate(exprs):
        if isinstance(e, unreal.MaterialExpressionMultiply):
            try:
                a_conn = e.get_editor_property("a")
                b_conn = e.get_editor_property("b")
                a_expr = a_conn.expression if a_conn else None
                b_expr = b_conn.expression if b_conn else None
                log("  [%d] Multiply   A=%s   B=%s" % (i, short(a_expr), short(b_expr)))
            except Exception as ex:
                log("  [%d] Multiply   (could not read inputs: %s)" % (i, ex))

    log("--- What actually feeds Base Color right now ---")
    try:
        bc = material.get_editor_property("base_color")
        expr = bc.expression if bc else None
        log("  base_color -> %s" % short(expr))
    except Exception as ex:
        log("  base_color -> (couldn't read: %s)" % ex)

    log("Done. Nothing was changed.")


run()
