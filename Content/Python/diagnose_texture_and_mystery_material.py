"""
DIAGNOSE: why the path still looks flat grey, and what "tripo_mat_..." is
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Two things to sort out before touching anything else:

1. The path is still flat matte grey after import_and_apply_tripo_cobblestone.py
   supposedly ran -- this checks whether the texture actually imported,
   whether M_AI_CobblestonePath's base color is actually wired to it, and
   re-does the wiring if not (read-only checks first, then a safe re-apply
   using the exact same texture asset if it exists).

2. Your selected building (Outskirt_166, SM_Building_Cottage) is wearing a
   material called "tripo_mat_395a4bc8" -- that name pattern is NOT
   anything either of my scripts created (mine only ever touched
   M_AI_CobblestonePath and imported a texture named T_TripoCobblestone_A).
   "tripo_mat_<hash>" is the kind of auto-generated name Unreal gives
   materials that come bundled inside an imported 3D model file (glTF/OBJ/
   FBX) -- so something imported an actual 3D model with its own materials
   into the project, and it (or its material) ended up assigned to this
   building. This is read-only: it just finds every actor wearing ANY
   material whose name starts with "tripo_mat_" and logs them, so we can
   see the scope (one building or many) before deciding what "fix" means
   here -- reverting it to its original material, or something else.

Purely diagnostic + one narrowly-scoped safe re-apply (item 1 only). Does
NOT touch the mystery material or any building.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/diagnose_texture_and_mystery_material.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

TEXTURE_PATH = "/Game/Landscaping/IcelandEnviroment/Textures/T_TripoCobblestone/T_TripoCobblestone_A"
PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
TILE_WORLD_SIZE = 200.0
ROUGHNESS = 0.85


def log(msg):
    print("[Diagnose] %s" % msg)


def check_texture():
    if not AL.does_asset_exist(TEXTURE_PATH):
        log("PROBLEM FOUND: %s does NOT exist -- the import never actually created the asset. "
            "Check the Output Log from when you ran import_and_apply_tripo_cobblestone.py for an "
            "import error/warning above the [ImportTripoCobblestone] lines." % TEXTURE_PATH)
        return None
    tex = AL.load_asset(TEXTURE_PATH)
    log("Texture OK: %s exists, size=%dx%d" % (TEXTURE_PATH, tex.blueprint_get_size_x(), tex.blueprint_get_size_y()))
    return tex


def check_material_wiring(tex):
    if not AL.does_asset_exist(PATH_MATERIAL_PATH):
        log("PROBLEM: %s doesn't exist at all." % PATH_MATERIAL_PATH)
        return False
    mat = AL.load_asset(PATH_MATERIAL_PATH)

    # Walk the graph for any TextureSample node and report which texture(s) it references.
    all_exprs = MEL.get_material_expressions(mat)
    found_textures = []
    for e in all_exprs:
        if isinstance(e, unreal.MaterialExpressionTextureSample):
            t = e.get_editor_property("texture")
            found_textures.append(t.get_name() if t else "(none)")
    log("TextureSample nodes in the graph reference: %s" % (found_textures if found_textures else "NONE FOUND"))
    if tex and tex.get_name() not in found_textures:
        log("PROBLEM FOUND: the Tripo texture is NOT referenced anywhere in this material's graph.")
        return False
    return True


def reapply(tex):
    log("Re-applying the triplanar basecolor build with %s..." % tex.get_name())
    mat = AL.load_asset(PATH_MATERIAL_PATH)
    MEL.delete_all_material_expressions(mat)

    world_pos = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1600, 0)
    tile_scale = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -1600, 150)
    tile_scale.set_editor_property("R", 1.0 / TILE_WORLD_SIZE)
    scaled_pos = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -1400, 0)
    MEL.connect_material_expressions(world_pos, "", scaled_pos, "A")
    MEL.connect_material_expressions(tile_scale, "", scaled_pos, "B")

    mask_yz = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -1200, -300)
    mask_yz.set_editor_property("R", False); mask_yz.set_editor_property("G", True)
    mask_yz.set_editor_property("B", True);  mask_yz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_yz, "")

    mask_xz = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -1200, 0)
    mask_xz.set_editor_property("R", True);  mask_xz.set_editor_property("G", False)
    mask_xz.set_editor_property("B", True);  mask_xz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xz, "")

    mask_xy = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -1200, 300)
    mask_xy.set_editor_property("R", True);  mask_xy.set_editor_property("G", True)
    mask_xy.set_editor_property("B", False); mask_xy.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xy, "")

    world_normal = MEL.create_material_expression(mat, unreal.MaterialExpressionVertexNormalWS, -1200, 600)
    abs_normal = MEL.create_material_expression(mat, unreal.MaterialExpressionAbs, -1000, 600)
    MEL.connect_material_expressions(world_normal, "", abs_normal, "")
    sharpness_const = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -1000, 750)
    sharpness_const.set_editor_property("R", 4.0)
    weight_pow = MEL.create_material_expression(mat, unreal.MaterialExpressionPower, -800, 600)
    MEL.connect_material_expressions(abs_normal, "", weight_pow, "Base")
    MEL.connect_material_expressions(sharpness_const, "", weight_pow, "Exp")

    w_x = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -600, 520)
    w_x.set_editor_property("R", True); w_x.set_editor_property("G", False)
    w_x.set_editor_property("B", False); w_x.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_x, "")
    w_y = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -600, 600)
    w_y.set_editor_property("R", False); w_y.set_editor_property("G", True)
    w_y.set_editor_property("B", False); w_y.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_y, "")
    w_z = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -600, 680)
    w_z.set_editor_property("R", False); w_z.set_editor_property("G", False)
    w_z.set_editor_property("B", True); w_z.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_z, "")

    sum_xy = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, -420, 560)
    MEL.connect_material_expressions(w_x, "", sum_xy, "A")
    MEL.connect_material_expressions(w_y, "", sum_xy, "B")
    sum_xyz = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, -280, 600)
    MEL.connect_material_expressions(sum_xy, "", sum_xyz, "A")
    MEL.connect_material_expressions(w_z, "", sum_xyz, "B")

    norm_x = MEL.create_material_expression(mat, unreal.MaterialExpressionDivide, -120, 480)
    MEL.connect_material_expressions(w_x, "", norm_x, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_x, "B")
    norm_y = MEL.create_material_expression(mat, unreal.MaterialExpressionDivide, -120, 600)
    MEL.connect_material_expressions(w_y, "", norm_y, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_y, "B")
    norm_z = MEL.create_material_expression(mat, unreal.MaterialExpressionDivide, -120, 720)
    MEL.connect_material_expressions(w_z, "", norm_z, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_z, "B")

    def sample_and_blend(t, out_y, prop):
        tx = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, 0, out_y - 200)
        tx.set_editor_property("texture", t)
        MEL.connect_material_expressions(mask_yz, "", tx, "Coordinates")
        ty = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, 0, out_y)
        ty.set_editor_property("texture", t)
        MEL.connect_material_expressions(mask_xz, "", ty, "Coordinates")
        tz = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, 0, out_y + 200)
        tz.set_editor_property("texture", t)
        MEL.connect_material_expressions(mask_xy, "", tz, "Coordinates")

        mul_x = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, 260, out_y - 200)
        MEL.connect_material_expressions(tx, "RGB", mul_x, "A")
        MEL.connect_material_expressions(norm_x, "", mul_x, "B")
        mul_y = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, 260, out_y)
        MEL.connect_material_expressions(ty, "RGB", mul_y, "A")
        MEL.connect_material_expressions(norm_y, "", mul_y, "B")
        mul_z = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, 260, out_y + 200)
        MEL.connect_material_expressions(tz, "RGB", mul_z, "A")
        MEL.connect_material_expressions(norm_z, "", mul_z, "B")

        add_xy = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, 480, out_y - 100)
        MEL.connect_material_expressions(mul_x, "", add_xy, "A")
        MEL.connect_material_expressions(mul_y, "", add_xy, "B")
        add_xyz = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, 640, out_y)
        MEL.connect_material_expressions(add_xy, "", add_xyz, "A")
        MEL.connect_material_expressions(mul_z, "", add_xyz, "B")
        MEL.connect_material_property(add_xyz, "", prop)

    sample_and_blend(tex, 0, unreal.MaterialProperty.MP_BASE_COLOR)
    rough_const = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, 260, 1400)
    rough_const.set_editor_property("R", ROUGHNESS)
    MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(mat)
    AL.save_asset(PATH_MATERIAL_PATH)
    log("Re-applied and saved.")


def scan_for_mystery_material():
    all_actors = actor_subsystem.get_all_level_actors()
    hits = []
    for a in all_actors:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            mat = comp.get_material(0)
            if mat and mat.get_name().startswith("tripo_mat_"):
                hits.append((a, mat))
                break
    log("Found %d actor(s) wearing a 'tripo_mat_*' material." % len(hits))
    for a, mat in hits:
        mesh_comp = a.get_components_by_class(unreal.StaticMeshComponent)[0]
        mesh = mesh_comp.static_mesh
        log("  label='%s'  folder='%s'  mesh=%s  material=%s  material_asset_path=%s" % (
            a.get_actor_label(), str(a.get_folder_path()),
            mesh.get_name() if mesh else "(none)",
            mat.get_name(), mat.get_path_name()))
    if hits:
        log("These weren't created by any of my scripts -- their material's asset path above should say "
            "what package/folder it lives in, which tells us where it actually came from.")


def run():
    tex = check_texture()
    if tex:
        ok = check_material_wiring(tex)
        if not ok:
            reapply(tex)
        else:
            log("Material graph looks correctly wired to the texture already -- if it still reads flat "
                "grey in the viewport, it may just need a viewport refresh/PIE restart, or the actors "
                "might not actually be pointed at M_AI_CobblestonePath any more (worth a quick "
                "diag_selected_material.py check on one of the path pieces).")
    scan_for_mystery_material()


run()
