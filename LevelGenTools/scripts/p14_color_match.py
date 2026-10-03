"""p14_color_match.py - warm, desaturated olive-brown palette so mountains, rocks and ground match the reference photo.

Run:   py "X:/IronBreach/LevelGenTools/scripts/p14_color_match.py"
Safe to re-run. Tunables in config/environment.json (scatter): rock_tint, rock_desaturate, ground_tint.

 * Builds M_Warm_<mesh> for each mountain/rock mesh: its own texture -> desaturate -> warm tint, and assigns it to the
   MOUNTAIN_ / ROCK_ / SEAMROCK_ actors.
 * Rebuilds M_Ground with a warm olive tint (actors already using it update automatically).

Look for:
  [Thornfield] VERIFY: warm_materials PASS
  [Thornfield] VERIFY: ground_tinted PASS
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


def _tint_chain(m, color_node, color_pin, tint, desat):
    src, pin = color_node, color_pin
    if desat > 0.0:
        d = MEL.create_material_expression(m, unreal.MaterialExpressionDesaturation, -500, -300)
        MEL.connect_material_expressions(src, pin, d, "")
        d.set_editor_property("luminance_factors", unreal.LinearColor(0.3, 0.59, 0.11, 0.0))
        f = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -700, -200)
        f.set_editor_property("r", float(desat))
        MEL.connect_material_expressions(f, "", d, "Fraction")
        src, pin = d, ""
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, -300)
    tv = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -500, -450)
    tv.set_editor_property("constant", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
    MEL.connect_material_expressions(src, pin, mul, "A")
    MEL.connect_material_expressions(tv, "", mul, "B")
    MEL.connect_material_property(mul, "", MP.MP_BASE_COLOR)


def _collect_textures(mat):
    """Textures used by a Material or MaterialInstance (instance overrides first, then the parent chain)."""
    texs = []
    cur = mat
    for _ in range(6):
        if cur is None:
            break
        if isinstance(cur, unreal.MaterialInstanceConstant):
            try:
                for tp in cur.get_editor_property("texture_parameter_values"):
                    t = tp.get_editor_property("parameter_value")
                    if t is not None and t not in texs:
                        texs.append(t)
            except Exception as e:
                G.warn("texture_parameter_values: %r" % e)
            try:
                cur = cur.get_editor_property("parent")
            except Exception:
                cur = None
            continue
        try:
            for t in MEL.get_used_textures(cur):
                if t not in texs:
                    texs.append(t)
        except Exception as e:
            G.warn("get_used_textures: %r" % e)
        break
    return texs


def _pick_base_texture(mat):
    texs = _collect_textures(mat)
    G.log("  candidate textures: %s" % [t.get_name() for t in texs])
    if not texs:
        return None
    for t in texs:
        n = t.get_name().lower()
        if any(k in n for k in ("basecolor", "base_color", "_bc", "diffuse", "albedo", "color")):
            return t
    return texs[0]


def main():
    G.init_log("p14_color_match")
    try:
        assets = G.load_json("assets.json")
        mcfg = G.load_json("materials.json")
        env = G.load_json("environment.json")
        sc = env["scatter"]
        dest, tex_dir = mcfg["dest"], mcfg["texture_dir"]
        tint = sc.get("rock_tint", [1.25, 1.0, 0.7])
        desat = float(sc.get("rock_desaturate", 0.65))

        # ---- warm materials per mountain / rock mesh
        keys = [k for k in assets["nature"] if k.startswith(("Mountain_", "Rock_"))]
        new_mats = {}
        for k in keys:
            e = assets["nature"][k]
            mesh = G.assert_asset_exists(e["ue_path"])
            base = mesh.get_material(0)
            if base is None:
                G.warn("%s has no material" % k)
                continue
            tex = _pick_base_texture(base)
            if tex is None:
                G.warn("%s: no texture found in %s" % (k, base.get_name()))
                continue
            m = _mat(dest, "M_Warm_%s" % k)
            ts = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSample, -900, -300)
            ts.set_editor_property("texture", tex)
            _tint_chain(m, ts, "RGB", tint, desat)
            r = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 0)
            r.set_editor_property("r", 0.9)
            MEL.connect_material_property(r, "", MP.MP_ROUGHNESS)
            MEL.recompile_material(m)
            unreal.EditorAssetLibrary.save_loaded_asset(m)
            new_mats[k] = m
            G.log("M_Warm_%s from texture %s" % (k, tex.get_name()))
        applied = 0
        for a in G.actor_subsystem().get_all_level_actors():
            lab = a.get_actor_label()
            if not lab.startswith(("MOUNTAIN_", "ROCK_", "SEAMROCK_")):
                continue
            try:
                comp = a.static_mesh_component
                path = comp.static_mesh.get_path_name()
            except Exception:
                continue
            for k, m in new_mats.items():
                if assets["nature"][k]["ue_path"].split("/")[-1] in path:
                    for i in range(comp.get_num_materials()):
                        comp.set_material(i, m)
                    applied += 1
                    break
        G.log("Warm material applied to %d actors" % applied)
        G.verify("warm_materials", len(new_mats) > 0 and applied > 0, "%d materials, %d actors" % (len(new_mats), applied))

        # ---- warm ground
        gt = sc.get("ground_tint", env.get("ground_tint", [1.2, 0.98, 0.72]))
        gm = _mat(dest, "M_Ground")
        wp = MEL.create_material_expression(gm, unreal.MaterialExpressionWorldPosition, -1400, 0)
        mask = MEL.create_material_expression(gm, unreal.MaterialExpressionComponentMask, -1150, 0)
        for ch, v in (("r", True), ("g", True), ("b", False), ("a", False)):
            mask.set_editor_property(ch, v)
        MEL.connect_material_expressions(wp, "", mask, "")
        div = MEL.create_material_expression(gm, unreal.MaterialExpressionMultiply, -950, 0)
        kk = MEL.create_material_expression(gm, unreal.MaterialExpressionConstant, -1150, 150)
        kk.set_editor_property("r", 1.0 / float(env["ground"]["tile_cm"]))
        MEL.connect_material_expressions(mask, "", div, "A")
        MEL.connect_material_expressions(kk, "", div, "B")

        def smp(suffix, y):
            t = unreal.EditorAssetLibrary.load_asset("%s/T_MossEarth_%s" % (tex_dir, suffix))
            n = MEL.create_material_expression(gm, unreal.MaterialExpressionTextureSample, -650, y)
            n.set_editor_property("texture", t)
            MEL.connect_material_expressions(div, "", n, "UVs")
            return n

        bc = smp("BC", -300)
        _tint_chain(gm, bc, "RGB", gt, 0.25)
        MEL.connect_material_property(smp("N", 0), "RGB", MP.MP_NORMAL)
        orm = smp("ORM", 300)
        MEL.connect_material_property(orm, "R", MP.MP_AMBIENT_OCCLUSION)
        MEL.connect_material_property(orm, "G", MP.MP_ROUGHNESS)
        MEL.connect_material_property(orm, "B", MP.MP_METALLIC)
        MEL.recompile_material(gm)
        unreal.EditorAssetLibrary.save_loaded_asset(gm)
        G.verify("ground_tinted", True, "M_Ground tint %s" % gt)

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, "saved")
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e)); G.verify("p14_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e); G.verify("p14_unexpected", False, repr(e))
    G.summary()


main()
