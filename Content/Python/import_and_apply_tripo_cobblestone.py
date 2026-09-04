"""
IMPORT THE TRIPO3D-GENERATED STONE TEXTURE AND APPLY IT TO THE PATH MATERIAL
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS DOES
----------------
1. Imports X:/IronBreach/SourceArt/T_TripoCobblestone_A.png (the seamless
   grey cobblestone image generated with Tripo3D's image tool) as a real
   Texture2D asset at
   /Game/Landscaping/IcelandEnviroment/Textures/T_TripoCobblestone/T_TripoCobblestone_A
   -- safe to re-run, re-imports over itself rather than duplicating.
2. Rebuilds M_AI_CobblestonePath as a plain triplanar sample of that
   texture -- basecolor only, flat constant roughness, no normal map (the
   no-normal approach already proven not to streak), and NO procedural
   grid overlay this time, because the irregular stone/grout pattern is
   now baked directly into the generated image itself rather than being
   faked with math -- so the "not a perfect grid" problem is solved at
   the source instead of patched after the fact.

TILE_WORLD_SIZE is a guess at how large a real-world area the generated
image should represent (2m) based on the apparent paver size in the
image -- tell me if the scale reads too big or small once you see it in
the viewport and I'll adjust and re-run.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/import_and_apply_tripo_cobblestone.py"
"""

import unreal
import os

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()

SOURCE_PNG = "X:/IronBreach/SourceArt/T_TripoCobblestone_A.png"
DEST_PACKAGE = "/Game/Landscaping/IcelandEnviroment/Textures/T_TripoCobblestone"
DEST_NAME = "T_TripoCobblestone_A"
DEST_PATH = f"{DEST_PACKAGE}/{DEST_NAME}"

PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
TILE_WORLD_SIZE = 200.0   # cm -- best guess at the real-world span of the generated image
ROUGHNESS = 0.85


def log(msg):
    print("[ImportTripoCobblestone] %s" % msg)


def import_texture():
    if not os.path.exists(SOURCE_PNG.replace("/", os.sep)):
        # also try as-is in case the OS handles the mixed separators fine
        if not os.path.exists(SOURCE_PNG):
            log("SOURCE PNG NOT FOUND at %s -- did the file land somewhere else?" % SOURCE_PNG)
            return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", SOURCE_PNG)
    task.set_editor_property("destination_path", DEST_PACKAGE)
    task.set_editor_property("destination_name", DEST_NAME)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    AT.import_asset_tasks([task])

    tex = AL.load_asset(DEST_PATH)
    if not tex:
        log("Import ran but %s wasn't found afterward -- check the Output Log above for import errors." % DEST_PATH)
        return None

    tex.set_editor_property("srgb", True)
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
    AL.save_asset(DEST_PATH)
    log("Imported %s" % DEST_PATH)
    return tex


def build_triplanar_basecolor_only(material, basecolor_tex):
    log("Rebuilding %s -- plain triplanar sample of the Tripo texture (tile=%.0fcm)..." % (
        material.get_name(), TILE_WORLD_SIZE))
    MEL.delete_all_material_expressions(material)

    world_pos = MEL.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -1600, 0)
    tile_scale = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1600, 150)
    tile_scale.set_editor_property("R", 1.0 / TILE_WORLD_SIZE)
    scaled_pos = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, -1400, 0)
    MEL.connect_material_expressions(world_pos, "", scaled_pos, "A")
    MEL.connect_material_expressions(tile_scale, "", scaled_pos, "B")

    mask_yz = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1200, -300)
    mask_yz.set_editor_property("R", False); mask_yz.set_editor_property("G", True)
    mask_yz.set_editor_property("B", True);  mask_yz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_yz, "")

    mask_xz = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1200, 0)
    mask_xz.set_editor_property("R", True);  mask_xz.set_editor_property("G", False)
    mask_xz.set_editor_property("B", True);  mask_xz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xz, "")

    mask_xy = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1200, 300)
    mask_xy.set_editor_property("R", True);  mask_xy.set_editor_property("G", True)
    mask_xy.set_editor_property("B", False); mask_xy.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xy, "")

    world_normal = MEL.create_material_expression(material, unreal.MaterialExpressionVertexNormalWS, -1200, 600)
    abs_normal = MEL.create_material_expression(material, unreal.MaterialExpressionAbs, -1000, 600)
    MEL.connect_material_expressions(world_normal, "", abs_normal, "")
    sharpness_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1000, 750)
    sharpness_const.set_editor_property("R", 4.0)
    weight_pow = MEL.create_material_expression(material, unreal.MaterialExpressionPower, -800, 600)
    MEL.connect_material_expressions(abs_normal, "", weight_pow, "Base")
    MEL.connect_material_expressions(sharpness_const, "", weight_pow, "Exp")

    w_x = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -600, 520)
    w_x.set_editor_property("R", True); w_x.set_editor_property("G", False)
    w_x.set_editor_property("B", False); w_x.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_x, "")
    w_y = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -600, 600)
    w_y.set_editor_property("R", False); w_y.set_editor_property("G", True)
    w_y.set_editor_property("B", False); w_y.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_y, "")
    w_z = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -600, 680)
    w_z.set_editor_property("R", False); w_z.set_editor_property("G", False)
    w_z.set_editor_property("B", True); w_z.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_z, "")

    sum_xy = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, -420, 560)
    MEL.connect_material_expressions(w_x, "", sum_xy, "A")
    MEL.connect_material_expressions(w_y, "", sum_xy, "B")
    sum_xyz = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, -280, 600)
    MEL.connect_material_expressions(sum_xy, "", sum_xyz, "A")
    MEL.connect_material_expressions(w_z, "", sum_xyz, "B")

    norm_x = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, -120, 480)
    MEL.connect_material_expressions(w_x, "", norm_x, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_x, "B")
    norm_y = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, -120, 600)
    MEL.connect_material_expressions(w_y, "", norm_y, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_y, "B")
    norm_z = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, -120, 720)
    MEL.connect_material_expressions(w_z, "", norm_z, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_z, "B")

    def sample_and_blend(tex, out_y, prop):
        tx = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y - 200)
        tx.set_editor_property("texture", tex)
        MEL.connect_material_expressions(mask_yz, "", tx, "Coordinates")

        ty = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y)
        ty.set_editor_property("texture", tex)
        MEL.connect_material_expressions(mask_xz, "", ty, "Coordinates")

        tz = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y + 200)
        tz.set_editor_property("texture", tex)
        MEL.connect_material_expressions(mask_xy, "", tz, "Coordinates")

        mul_x = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y - 200)
        MEL.connect_material_expressions(tx, "RGB", mul_x, "A")
        MEL.connect_material_expressions(norm_x, "", mul_x, "B")
        mul_y = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y)
        MEL.connect_material_expressions(ty, "RGB", mul_y, "A")
        MEL.connect_material_expressions(norm_y, "", mul_y, "B")
        mul_z = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y + 200)
        MEL.connect_material_expressions(tz, "RGB", mul_z, "A")
        MEL.connect_material_expressions(norm_z, "", mul_z, "B")

        add_xy = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 480, out_y - 100)
        MEL.connect_material_expressions(mul_x, "", add_xy, "A")
        MEL.connect_material_expressions(mul_y, "", add_xy, "B")
        add_xyz = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 640, out_y)
        MEL.connect_material_expressions(add_xy, "", add_xyz, "A")
        MEL.connect_material_expressions(mul_z, "", add_xyz, "B")

        MEL.connect_material_property(add_xyz, "", prop)

    sample_and_blend(basecolor_tex, 0, unreal.MaterialProperty.MP_BASE_COLOR)

    rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 260, 1400)
    rough_const.set_editor_property("R", ROUGHNESS)
    MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

    MEL.recompile_material(material)
    log("  done -- %s recompiled." % material.get_name())


def run():
    tex = import_texture()
    if not tex:
        return
    if not AL.does_asset_exist(PATH_MATERIAL_PATH):
        log("SKIPPED material rebuild -- %s doesn't exist." % PATH_MATERIAL_PATH)
        return
    mat = AL.load_asset(PATH_MATERIAL_PATH)
    build_triplanar_basecolor_only(mat, tex)
    log("Path actors already point at this material -- no re-assignment needed. "
        "Save and check the viewport / re-run PIE.")


run()
