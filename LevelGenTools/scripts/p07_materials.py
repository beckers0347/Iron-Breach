"""p07_materials.py - Phase 7: build the UE materials and assign them to every building and door mesh.

Run (level does not need to be open):   py "X:/IronBreach/LevelGenTools/scripts/p07_materials.py"

 1. Builds M_<slot> materials from config/materials.json (re-runs rebuild the nodes of existing ones).
 2. Walks every building + door mesh in assets.json, and points each material slot at M_<slot name>.
 3. Verifies nothing is left on a default / missing material.

Look for:
  [Thornfield] VERIFY: materials_built PASS (<n> materials)
  [Thornfield] VERIFY: textures_found PASS
  [Thornfield] VERIFY: slots_assigned PASS (<n> slots on <m> meshes)
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


def _get_or_create(dest, name):
    path = "%s/%s" % (dest, name)
    mat = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if mat is None:
        mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, dest, unreal.Material, unreal.MaterialFactoryNew())
    else:
        MEL.delete_all_material_expressions(mat)
    if mat is None:
        raise G.GenError("Could not create material %s" % path)
    return mat


def _node(mat, cls, x, y):
    return MEL.create_material_expression(mat, cls, x, y)


def _vec(mat, rgb, x, y):
    n = _node(mat, unreal.MaterialExpressionConstant3Vector, x, y)
    n.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    return n


def _scalar(mat, v, x, y):
    n = _node(mat, unreal.MaterialExpressionConstant, x, y)
    n.set_editor_property("r", float(v))
    return n


def _tex(mat, tex, x, y):
    n = _node(mat, unreal.MaterialExpressionTextureSample, x, y)
    n.set_editor_property("texture", tex)
    return n


def _textured(mat, tex_dir, base, tint=None, missing=None):
    bc = unreal.EditorAssetLibrary.load_asset("%s/T_%s_BC" % (tex_dir, base))
    nm = unreal.EditorAssetLibrary.load_asset("%s/T_%s_N" % (tex_dir, base))
    orm = unreal.EditorAssetLibrary.load_asset("%s/T_%s_ORM" % (tex_dir, base))
    for k, t in (("BC", bc), ("N", nm), ("ORM", orm)):
        if t is None and missing is not None:
            missing.append("T_%s_%s" % (base, k))
    if bc is None or nm is None or orm is None:
        return
    n_bc = _tex(mat, bc, -800, -300)
    if tint:
        mul = _node(mat, unreal.MaterialExpressionMultiply, -500, -300)
        MEL.connect_material_expressions(n_bc, "RGB", mul, "A")
        MEL.connect_material_expressions(_vec(mat, tint, -800, -100), "", mul, "B")
        MEL.connect_material_property(mul, "", MP.MP_BASE_COLOR)
    else:
        MEL.connect_material_property(n_bc, "RGB", MP.MP_BASE_COLOR)
    n_n = _tex(mat, nm, -800, 0)
    MEL.connect_material_property(n_n, "RGB", MP.MP_NORMAL)
    n_o = _tex(mat, orm, -800, 300)
    MEL.connect_material_property(n_o, "R", MP.MP_AMBIENT_OCCLUSION)
    MEL.connect_material_property(n_o, "G", MP.MP_ROUGHNESS)
    MEL.connect_material_property(n_o, "B", MP.MP_METALLIC)


def _emissive(mat, rgb, intensity):
    mul = _node(mat, unreal.MaterialExpressionMultiply, -300, 0)
    MEL.connect_material_expressions(_vec(mat, rgb, -600, 0), "", mul, "A")
    MEL.connect_material_expressions(_scalar(mat, intensity, -600, 150), "", mul, "B")
    MEL.connect_material_property(mul, "", MP.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(_vec(mat, [0, 0, 0], -300, -200), "", MP.MP_BASE_COLOR)


def _glass(mat, rgb, opacity):
    # Nanite meshes only accept opaque/masked materials, so "glass" is a dark, glossy, metallic masked surface.
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    MEL.connect_material_property(_vec(mat, [c * 0.5 for c in rgb], -500, 0), "", MP.MP_BASE_COLOR)
    MEL.connect_material_property(_scalar(mat, 1.0, -500, 150), "", MP.MP_OPACITY_MASK)
    MEL.connect_material_property(_scalar(mat, 0.05, -500, 300), "", MP.MP_ROUGHNESS)
    MEL.connect_material_property(_scalar(mat, 0.9, -500, 450), "", MP.MP_METALLIC)


def _plain(mat, rgb, roughness, metallic):
    MEL.connect_material_property(_vec(mat, rgb, -500, 0), "", MP.MP_BASE_COLOR)
    MEL.connect_material_property(_scalar(mat, roughness, -500, 150), "", MP.MP_ROUGHNESS)
    MEL.connect_material_property(_scalar(mat, metallic, -500, 300), "", MP.MP_METALLIC)


def main():
    G.init_log("p07_materials")
    try:
        cfg = G.load_json("materials.json")
        assets = G.load_json("assets.json")
        dest, tex_dir = cfg["dest"], cfg["texture_dir"]
        unreal.EditorAssetLibrary.make_directory(dest)

        built, missing_tex = {}, []

        for name in cfg["textured"]:
            m = _get_or_create(dest, "M_%s" % name)
            _textured(m, tex_dir, name, None, missing_tex)
            built[name] = m
        for name, d in cfg["tinted"].items():
            m = _get_or_create(dest, "M_%s" % name)
            _textured(m, tex_dir, d["base"], d["tint"], missing_tex)
            built[name] = m
        for name, d in cfg["emissive"].items():
            m = _get_or_create(dest, "M_%s" % name)
            _emissive(m, d["rgb"], d["intensity"])
            built[name] = m
        for name, d in cfg["glass"].items():
            m = _get_or_create(dest, "M_%s" % name)
            _glass(m, d["rgb"], d["opacity"])
            built[name] = m
        for name, d in cfg["plain"].items():
            m = _get_or_create(dest, "M_%s" % name)
            _plain(m, d["rgb"], d["roughness"], d["metallic"])
            built[name] = m

        for name, m in built.items():
            MEL.recompile_material(m)
            unreal.EditorAssetLibrary.save_loaded_asset(m)
            G.log("Built M_%s" % name)
        G.verify("textures_found", not missing_tex, "all texture sets present" if not missing_tex else "missing %s" % sorted(set(missing_tex)))
        expected_n = len(cfg["textured"]) + len(cfg["tinted"]) + len(cfg["emissive"]) + len(cfg["glass"]) + len(cfg["plain"])
        G.verify("materials_built", len(built) == expected_n, "%d materials" % len(built))

        # ---------------------------------------------------------------- assign
        meshes, slots_total, unknown, unassigned = 0, 0, [], []
        for key, entry in assets["buildings"].items():
            for p in sorted(unreal.EditorAssetLibrary.list_assets(entry["dest"], recursive=False, include_folder=False)):
                mesh = unreal.EditorAssetLibrary.load_asset(p)
                if not isinstance(mesh, unreal.StaticMesh):
                    continue
                meshes += 1
                for i, sm in enumerate(mesh.static_materials):
                    slot = str(sm.material_slot_name)
                    base = slot[2:] if slot.startswith("M_") else slot
                    slots_total += 1
                    mat = built.get(base)
                    if mat is None:
                        unknown.append("%s:%s" % (mesh.get_name(), slot))
                        continue
                    mesh.set_material(i, mat)
                mesh.modify()
                unreal.EditorAssetLibrary.save_loaded_asset(mesh)
                # re-read and confirm
                for i, sm in enumerate(mesh.static_materials):
                    mi = sm.material_interface
                    if mi is None or not mi.get_path_name().startswith(dest):
                        unassigned.append("%s:%s" % (mesh.get_name(), str(sm.material_slot_name)))
        if unknown:
            G.warn("Slots with no material definition: %s" % sorted(set(unknown)))
        G.verify("slots_assigned", not unknown and not unassigned and slots_total > 0,
                 "%d slots on %d meshes" % (slots_total, meshes) if not (unknown or unassigned)
                 else "unknown=%s unassigned=%s" % (sorted(set(unknown))[:6], unassigned[:6]))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p07_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p07_unexpected", False, repr(e))
    G.summary()


main()
