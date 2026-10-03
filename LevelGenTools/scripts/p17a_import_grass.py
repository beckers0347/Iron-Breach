"""p17a_import_grass.py - build M_Grass and import the 4 grass patch meshes (real blade geometry, Nanite).

Run:   py "X:/IronBreach/LevelGenTools/scripts/p17a_import_grass.py"
Needs SourceArt/Thornfield/Grass/SM_GrassPatch_0..3.fbx on disk.

Look for:
  [Thornfield] VERIFY: grass_material PASS
  [Thornfield] VERIFY: grass_imported PASS (4 of 4)
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


def build_material(dest, cfg):
    path = dest + "/M_Grass"
    m = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if m is None:
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_Grass", dest, unreal.Material, unreal.MaterialFactoryNew())
    else:
        MEL.delete_all_material_expressions(m)
    m.set_editor_property("two_sided", True)

    tc = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -1400, -300)
    mk = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1200, -300)
    for ch, v in (("r", False), ("g", True), ("b", False), ("a", False)):
        mk.set_editor_property(ch, v)
    MEL.connect_material_expressions(tc, "", mk, "")
    one = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -1000, -300)   # FBX import flips V: height = 1 - V
    MEL.connect_material_expressions(mk, "", one, "")
    pw = MEL.create_material_expression(m, unreal.MaterialExpressionPower, -800, -300)
    ex = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -1000, -200)
    ex.set_editor_property("r", 1.4)
    MEL.connect_material_expressions(one, "", pw, "Base")
    MEL.connect_material_expressions(ex, "", pw, "Exponent")

    def col(rgb, y):
        c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -800, y)
        c.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        return c

    root, green, dry = col(cfg["root_rgb"], -100), col(cfg["tip_green_rgb"], 0), col(cfg["tip_dry_rgb"], 100)
    l1 = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -550, -150)
    MEL.connect_material_expressions(root, "", l1, "A")
    MEL.connect_material_expressions(green, "", l1, "B")
    MEL.connect_material_expressions(pw, "", l1, "Alpha")
    l2 = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -550, 50)
    MEL.connect_material_expressions(root, "", l2, "A")
    MEL.connect_material_expressions(dry, "", l2, "B")
    MEL.connect_material_expressions(pw, "", l2, "Alpha")

    alpha = None
    try:
        wp = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1200, 200)
        nz = MEL.create_material_expression(m, unreal.MaterialExpressionNoise, -1000, 200)
        for prop, val in (("scale", float(cfg["noise_scale"])), ("quality", 1), ("levels", 3), ("turbulence", True),
                          ("output_min", 0.0), ("output_max", 1.0)):
            try:
                nz.set_editor_property(prop, val)
            except Exception as e:
                G.warn("noise.%s: %r" % (prop, e))
        MEL.connect_material_expressions(wp, "", nz, "Position")
        alpha = nz
    except Exception as e:
        G.warn("Noise node unavailable: %r" % e)
    if alpha is None:
        alpha = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -800, 250)
        alpha.set_editor_property("r", 0.3)
    l3 = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -300, -50)
    MEL.connect_material_expressions(l1, "", l3, "A")
    MEL.connect_material_expressions(l2, "", l3, "B")
    MEL.connect_material_expressions(alpha, "", l3, "Alpha")
    MEL.connect_material_property(l3, "", MP.MP_BASE_COLOR)
    r = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 250)
    r.set_editor_property("r", 0.75)
    MEL.connect_material_property(r, "", MP.MP_ROUGHNESS)
    sp = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 350)
    sp.set_editor_property("r", 0.2)
    MEL.connect_material_property(sp, "", MP.MP_SPECULAR)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def _options():
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    sm = ui.static_mesh_import_data
    sm.set_editor_property("combine_meshes", True)
    sm.set_editor_property("auto_generate_collision", False)
    sm.set_editor_property("generate_lightmap_u_vs", False)
    try:
        sm.set_editor_property("build_nanite", True)
    except Exception as e:
        G.warn("build_nanite: %r" % e)
    return ui


def main():
    G.init_log("p17a_import_grass")
    try:
        try:
            unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
        except Exception as e:
            G.warn("console command failed: %r" % e)
        assets = G.load_json("assets.json")
        mcfg = G.load_json("materials.json")
        gcfg = G.load_json("environment.json")["scatter"]["grass"]
        g = assets["grass"]
        mat = build_material(mcfg["dest"], gcfg)
        G.verify("grass_material", mat is not None, "M_Grass (two-sided, root-to-tip gradient)")
        ok = 0
        for i in range(int(g["variants"])):
            name = "SM_GrassPatch_%d" % i
            src = os.path.join(G.project_dir(), g["source_dir"].replace("/", os.sep), name + ".fbx")
            if not os.path.isfile(src):
                G.err("Grass FBX missing: %s" % src)
                continue
            t = unreal.AssetImportTask()
            t.set_editor_property("filename", src)
            t.set_editor_property("destination_path", g["dest"])
            t.set_editor_property("destination_name", name)
            t.set_editor_property("replace_existing", True)
            t.set_editor_property("automated", True)
            t.set_editor_property("save", False)
            t.set_editor_property("options", _options())
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
            mesh = unreal.EditorAssetLibrary.load_asset("%s/%s" % (g["dest"], name))
            if mesh is None:
                G.err("Import failed: %s" % name)
                continue
            for k in range(len(mesh.static_materials)):
                mesh.set_material(k, mat)
            mesh.modify()
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
            size, origin = G.get_bounds(mesh)
            G.log("%s: bounds %s" % (name, G.fmt_size(size)))
            ok += 1
        G.verify("grass_imported", ok == int(g["variants"]), "%d of %d" % (ok, int(g["variants"])))
    except G.GenError as e:
        G.err(str(e)); G.verify("p17a_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e); G.verify("p17a_unexpected", False, repr(e))
    G.summary()


main()
