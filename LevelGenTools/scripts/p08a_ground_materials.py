"""p08a_ground_materials.py - Phase 8a: real ground / road / apron materials, extended outer ground, landscape API probe.

Run:   py "X:/IronBreach/LevelGenTools/scripts/p08a_ground_materials.py"

 * Builds world-aligned M_Ground (MossEarth), M_Dirt (MossEarth, warm tint, roads) and M_Apron (FloorConcrete).
 * Applies them to the Phase-2 slab / road strips / apron, and the perimeter marker walls get M_ConcreteDark.
 * Adds a big outer ground plane (Ground_Outer) around the base so the forest ring does not float in the void.
 * Logs which Landscape APIs this UE build exposes to Python (so a heightmap landscape can be attempted next).

Look for:
  [Thornfield] VERIFY: ground_materials PASS
  [Thornfield] VERIFY: ground_applied PASS (...)
  [Thornfield] VERIFY: outer_ground PASS
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)

MEL = unreal.MaterialEditingLibrary
MP = unreal.MaterialProperty
CUBE = "/Engine/BasicShapes/Cube"
PHASE = 8


def _mat(dest, name):
    path = "%s/%s" % (dest, name)
    m = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if m is None:
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, dest, unreal.Material, unreal.MaterialFactoryNew())
    else:
        MEL.delete_all_material_expressions(m)
    if m is None:
        raise G.GenError("Cannot create %s" % path)
    return m


def _world_aligned(name, dest, tex_dir, base, tile_cm, tint=None):
    m = _mat(dest, name)
    wp = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1400, 0)
    mask = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1150, 0)
    mask.set_editor_property("r", True)
    mask.set_editor_property("g", True)
    mask.set_editor_property("b", False)
    mask.set_editor_property("a", False)
    MEL.connect_material_expressions(wp, "", mask, "")
    div = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -950, 0)
    k = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -1150, 150)
    k.set_editor_property("r", 1.0 / float(tile_cm))
    MEL.connect_material_expressions(mask, "", div, "A")
    MEL.connect_material_expressions(k, "", div, "B")

    def sample(suffix, y):
        t = unreal.EditorAssetLibrary.load_asset("%s/T_%s_%s" % (tex_dir, base, suffix))
        if t is None:
            raise G.GenError("Texture missing: T_%s_%s" % (base, suffix))
        n = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSample, -650, y)
        n.set_editor_property("texture", t)
        MEL.connect_material_expressions(div, "", n, "UVs")
        return n

    bc = sample("BC", -300)
    if tint:
        mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, -300)
        tv = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -650, -450)
        tv.set_editor_property("constant", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
        MEL.connect_material_expressions(bc, "RGB", mul, "A")
        MEL.connect_material_expressions(tv, "", mul, "B")
        MEL.connect_material_property(mul, "", MP.MP_BASE_COLOR)
    else:
        MEL.connect_material_property(bc, "RGB", MP.MP_BASE_COLOR)
    MEL.connect_material_property(sample("N", 0), "RGB", MP.MP_NORMAL)
    orm = sample("ORM", 300)
    MEL.connect_material_property(orm, "R", MP.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(orm, "G", MP.MP_ROUGHNESS)
    MEL.connect_material_property(orm, "B", MP.MP_METALLIC)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def _set_mat(actor, mat):
    actor.static_mesh_component.set_material(0, mat)


def main():
    G.init_log("p08a_ground_materials")
    try:
        level = G.load_json("level.json")
        mcfg = G.load_json("materials.json")
        env = G.load_json("environment.json")
        dest, tex_dir = mcfg["dest"], mcfg["texture_dir"]
        b = level["bounds_cm"]

        ground = _world_aligned("M_Ground", dest, tex_dir, "MossEarth", env["ground"]["tile_cm"])
        dirt = _world_aligned("M_Dirt", dest, tex_dir, "MossEarth", env["ground"]["tile_cm"] * 0.5, env["road_dirt_tint"])
        apron = _world_aligned("M_Apron", dest, tex_dir, "FloorConcrete", env["apron_tile_cm"])
        G.verify("ground_materials", all(x is not None for x in (ground, dirt, apron)), "M_Ground, M_Dirt, M_Apron")

        wall_mat = unreal.EditorAssetLibrary.load_asset("%s/M_ConcreteDark" % dest)
        counts = {"ground": 0, "road": 0, "apron": 0, "wall": 0}
        for a in G.actors_with_tag("GEN_Phase2"):
            n = a.get_actor_label()
            if not isinstance(a, unreal.StaticMeshActor):
                continue
            if n == "GB_Ground":
                _set_mat(a, ground); counts["ground"] += 1
            elif n.startswith("GB_Road_HangarApron"):
                _set_mat(a, apron); counts["apron"] += 1
            elif n.startswith("GB_Road_"):
                _set_mat(a, dirt); counts["road"] += 1
            elif n.startswith("GB_Perimeter_") and wall_mat is not None:
                _set_mat(a, wall_mat); counts["wall"] += 1
        G.verify("ground_applied", counts["ground"] == 1 and counts["road"] > 0 and counts["apron"] > 0, str(counts))

        # outer ground plane (rebuilt each run)
        for a in G.actors_with_tag("GEN_Phase8"):
            if a.get_actor_label() == "Ground_Outer":
                G.actor_subsystem().destroy_actor(a)
        m = env["ground"]["outer_margin_cm"]
        w = (b["max"][0] - b["min"][0]) + 2 * m
        h = (b["max"][1] - b["min"][1]) + 2 * m
        cx, cy = (b["min"][0] + b["max"][0]) / 2.0, (b["min"][1] + b["max"][1]) / 2.0
        og = G.spawn_static_mesh(CUBE, (cx, cy, env["ground"]["outer_z"] - 50.0), (0, 0, 0), (w / 100.0, h / 100.0, 1.0), "Ground_Outer", PHASE)
        _set_mat(og, ground)
        og.static_mesh_component.set_collision_profile_name("BlockAll")
        G.verify("outer_ground", og is not None, "%.0f x %.0f m" % (w / 100.0, h / 100.0))

        # landscape API probe (for the heightmap landscape attempt)
        names = [n for n in dir(unreal) if "andscape" in n]
        G.log("Landscape classes in unreal module: %s" % names)
        try:
            cls = unreal.Landscape
            G.log("unreal.Landscape methods: %s" % [n for n in dir(cls) if any(k in n for k in ("import", "heightmap", "create", "component", "layer"))])
        except Exception as e:
            G.log("unreal.Landscape unavailable: %r" % e)
        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True)
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p08a_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p08a_unexpected", False, repr(e))
    G.summary()


main()
