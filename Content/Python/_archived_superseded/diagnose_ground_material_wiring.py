"""
DIAGNOSE M_AI_GROUND'S ACTUAL WIRING -- read-only, changes nothing
================================================================
IRON BREACH / Unreal Engine 5.8

The node-list diagnostic showed 41 nodes but not how they connect to each
other. This traces the actual A/B/Input connections on every Multiply,
Add, Divide, ComponentMask, Power, Abs, and TextureSample node, printing
each one as "[index] NodeType  input_name -> [other_index] OtherNodeType"
so the real tiling chain(s) can be read off directly instead of guessed
at a third time.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/diagnose_ground_material_wiring.py"
"""

import unreal

CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary


def log(msg):
    print("[DiagnoseGroundMaterialWiring] %s" % msg)


def run():
    material = AL.load_asset(CONCRETE_MATERIAL_PATH)
    if material is None:
        log("ABORTED -- %s not found." % CONCRETE_MATERIAL_PATH)
        return

    exprs = MEL.get_material_expressions(material)

    def idx_of(e):
        return exprs.index(e) if e in exprs else -1

    def short(e):
        if isinstance(e, str):
            return e
        if e is None:
            return "None"
        return "[%d] %s" % (idx_of(e), type(e).__name__)

    def conn_expr(node, pin_prop):
        try:
            conn = node.get_editor_property(pin_prop)
        except Exception as ex:
            return "ERR(get '%s': %s)" % (pin_prop, ex)
        if conn is None:
            return "None(prop itself is None)"
        try:
            expr = conn.expression
        except Exception as ex:
            return "ERR(.expression on '%s': %s | conn type=%s)" % (pin_prop, ex, type(conn).__name__)
        if expr is None:
            return "unconnected(.expression is None, conn type=%s)" % type(conn).__name__
        return expr

    # Candidate input-pin property names per node type -- Unreal's Python
    # exposes these as ExpressionInput-typed properties named after the pin.
    PIN_NAMES_BY_TYPE = {
        unreal.MaterialExpressionMultiply: ["a", "b"],
        unreal.MaterialExpressionAdd: ["a", "b"],
        unreal.MaterialExpressionDivide: ["a", "b"],
        unreal.MaterialExpressionPower: ["base", "exponent"],
        unreal.MaterialExpressionAbs: ["input"],
        unreal.MaterialExpressionComponentMask: ["input"],
        unreal.MaterialExpressionTextureSample: ["coordinates", "texture_object"],
    }

    log("Total nodes: %d" % len(exprs))
    for i, e in enumerate(exprs):
        matched = False
        for cls, pins in PIN_NAMES_BY_TYPE.items():
            if isinstance(e, cls):
                matched = True
                parts = []
                for pin in pins:
                    target = conn_expr(e, pin)
                    parts.append("%s->%s" % (pin, short(target)))
                extra = ""
                if isinstance(e, unreal.MaterialExpressionTextureSample):
                    tex = e.get_editor_property("texture")
                    extra = " texture='%s'" % (tex.get_name() if tex else "None")
                log("  [%d] %-30s %s%s" % (i, type(e).__name__, "  ".join(parts), extra))
                break
        if not matched and isinstance(e, unreal.MaterialExpressionConstant):
            log("  [%d] %-30s R=%.6f (tile=%.0fcm if this is a tile-scale node)" % (
                i, type(e).__name__, e.get_editor_property("R"), 1.0 / e.get_editor_property("R") if e.get_editor_property("R") else 0))

    log("Done. Nothing was changed.")


run()
