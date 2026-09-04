"""
DIAGNOSE M_AI_GROUND'S ACTUAL NODE GRAPH -- read-only, changes nothing
================================================================
IRON BREACH / Unreal Engine 5.8

The last two fix scripts assumed M_AI_Ground tiles the same way
M_AI_CobblestonePath does (a plain Constant -> Multiply -> WorldPosition
chain), but it doesn't -- fix_concrete_solid.py couldn't find that pattern
at all. Rather than guess again, this just lists every node in the
material's graph (type, key properties, what it's connected to) so we can
see how it ACTUALLY controls tiling before touching it again.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/diagnose_ground_material_graph.py"
"""

import unreal

CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary


def log(msg):
    print("[DiagnoseGroundMaterialGraph] %s" % msg)


def describe_expr(e):
    t = type(e).__name__
    extra = ""
    try:
        if isinstance(e, unreal.MaterialExpressionConstant):
            extra = "R=%.6f" % e.get_editor_property("R")
        elif isinstance(e, unreal.MaterialExpressionConstant2Vector):
            extra = "R=%.4f G=%.4f" % (e.get_editor_property("R"), e.get_editor_property("G"))
        elif isinstance(e, unreal.MaterialExpressionScalarParameter):
            extra = "name='%s' default=%.4f" % (e.get_editor_property("parameter_name"), e.get_editor_property("default_value"))
        elif isinstance(e, unreal.MaterialExpressionVectorParameter):
            extra = "name='%s'" % e.get_editor_property("parameter_name")
        elif isinstance(e, unreal.MaterialExpressionTextureSample):
            tex = e.get_editor_property("texture")
            extra = "texture='%s'" % (tex.get_name() if tex else "None")
        elif isinstance(e, unreal.MaterialExpressionTextureSampleParameter2D):
            tex = e.get_editor_property("texture")
            extra = "param='%s' texture='%s'" % (e.get_editor_property("parameter_name"), tex.get_name() if tex else "None")
        elif isinstance(e, unreal.MaterialExpressionMaterialFunctionCall):
            fn = e.get_editor_property("material_function")
            extra = "function='%s'" % (fn.get_name() if fn else "None")
        elif isinstance(e, unreal.MaterialExpressionPanner):
            extra = "(panner)"
        elif isinstance(e, unreal.MaterialExpressionMultiply):
            extra = "(multiply)"
        elif isinstance(e, unreal.MaterialExpressionComponentMask):
            extra = "R=%s G=%s B=%s A=%s" % (e.get_editor_property("R"), e.get_editor_property("G"),
                                              e.get_editor_property("B"), e.get_editor_property("A"))
    except Exception as ex:
        extra = "(couldn't read props: %s)" % ex
    return "%s  %s" % (t, extra)


def run():
    material = AL.load_asset(CONCRETE_MATERIAL_PATH)
    if material is None:
        log("ABORTED -- %s not found." % CONCRETE_MATERIAL_PATH)
        return

    exprs = MEL.get_material_expressions(material)
    log("M_AI_Ground has %d expression node(s):" % len(exprs))
    for i, e in enumerate(exprs):
        log("  [%d] %s  (obj name: %s)" % (i, describe_expr(e), e.get_name()))

    log("--- What feeds the material's main property inputs ---")
    for prop in ("base_color", "metallic", "specular", "roughness", "normal", "world_position_offset"):
        try:
            inp = material.get_editor_property(prop)
            expr = inp.expression if inp else None
            if expr is not None:
                idx = exprs.index(expr) if expr in exprs else -1
                log("  %-22s -> node [%d] %s" % (prop, idx, describe_expr(expr)))
            else:
                log("  %-22s -> (not connected / plain default)" % prop)
        except Exception as ex:
            log("  %-22s -> (couldn't read: %s)" % (prop, ex))

    log("--- Any MaterialFunctionCall nodes: their inputs (often where tiling params live) ---")
    for i, e in enumerate(exprs):
        if isinstance(e, unreal.MaterialExpressionMaterialFunctionCall):
            fn = e.get_editor_property("material_function")
            log("  Node [%d] calls function '%s'" % (i, fn.get_name() if fn else "None"))
            try:
                fn_inputs = e.get_editor_property("function_inputs")
                for fi in fn_inputs:
                    fi_name = fi.get_editor_property("input") if hasattr(fi, "get_editor_property") else fi
                    log("    input: %s" % fi_name)
            except Exception as ex:
                log("    (couldn't enumerate function inputs: %s)" % ex)

    log("Done. Nothing was changed.")


run()
