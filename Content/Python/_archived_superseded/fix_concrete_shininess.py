"""
FIX: fix_concrete_tile_scale.py made the concrete shiny -- undo that side
effect, keep the tile-size fix
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT WENT WRONG
----------------
The tile-scale fix found EVERY Constant node on M_AI_Ground with a value
between 0.00005 and 1.0 and treated all of them as if they were the
tile-size constant. That range is broad enough to also catch a Roughness
(or Metallic/Specular) constant if the material has one sitting in that
same 0-1 range -- which apparently it does, and setting a Roughness
constant to something like 1/8000 (~0.0001) means "almost perfectly
smooth," i.e. shiny/mirror-like. That's the "shiny" result.

THE FIX
-------
This time it identifies nodes by what they're actually WIRED to instead of
just their value range:
  - Finds the real tile-scale node by tracing which Constant feeds into a
    Multiply that's also fed by WorldPosition (the actual triplanar UV
    chain, same pattern fix_cobblestone_tile_scale.py used) -- leaves that
    one alone, it's correct.
  - Reads whatever Constant node is wired directly into the material's
    Roughness input and sets it back to 0.85 (a normal rough concrete
    value, not shiny). Same for Metallic (-> 0.0, concrete isn't
    metallic) and Specular (-> 0.5, the engine default) if those are also
    wired to plain Constant nodes.

Doesn't touch the tile size itself -- that part of the last fix was
correct, this just undoes the accidental roughness/metallic change.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_concrete_shininess.py"
"""

import unreal

CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary


def log(msg):
    print("[FixConcreteShininess] %s" % msg)


def find_tile_scale_node(material, exprs):
    """The correct tile-scale Constant: feeds a Multiply whose other input
    is a WorldPosition node."""
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


def reset_property_constant(material, prop_name, new_value, label):
    try:
        prop_input = material.get_editor_property(prop_name)
    except Exception as e:
        log("  Could not read '%s' input: %s" % (prop_name, e))
        return
    expr = prop_input.expression if prop_input else None
    if expr is None:
        log("  %s: not wired to a node (uses the material's plain default) -- nothing to fix." % label)
        return
    if isinstance(expr, unreal.MaterialExpressionConstant):
        old = expr.get_editor_property("R")
        expr.set_editor_property("R", new_value)
        log("  %s: Constant node %.5f -> %.2f." % (label, old, new_value))
    else:
        log("  %s: wired to a %s node, not a plain Constant -- leaving it alone, tell me if it "
            "still looks shiny." % (label, type(expr).__name__))


def run():
    material = AL.load_asset(CONCRETE_MATERIAL_PATH)
    if material is None:
        log("ABORTED -- %s not found." % CONCRETE_MATERIAL_PATH)
        return

    exprs = MEL.get_material_expressions(material)

    tile_node = find_tile_scale_node(material, exprs)
    if tile_node is not None:
        log("Confirmed real tile-scale node (feeds WorldPosition * Constant): R=%.6f (tile=%.0fcm) -- left alone." % (
            tile_node.get_editor_property("R"), 1.0 / tile_node.get_editor_property("R")))
    else:
        log("Could not re-locate the tile-scale node via its wiring -- tile size left untouched either way.")

    reset_property_constant(material, "roughness", 0.85, "Roughness")
    reset_property_constant(material, "metallic", 0.0, "Metallic")
    reset_property_constant(material, "specular", 0.5, "Specular")

    MEL.recompile_material(material)
    log("Done. Save and take a look -- should be back to a normal matte concrete look with the "
        "bigger tile size kept.")


run()
