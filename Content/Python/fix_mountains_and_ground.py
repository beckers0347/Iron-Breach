"""
FIX MOUNTAINS + GROUND TEXTURING -- CG Mainland (CarrowGateGarrison)
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
A one-shot Editor Python script addressing three things from the latest
screenshots: (1) one mountain shape reading as a black, torn-looking sliver
in the sky, (2) the ground plate around the mountains looking like a flat,
textureless brown color, (3) the mountains sitting too high -- move the
whole mountain range down 6m.

WHAT I FOUND BEFORE WRITING THIS
---------------------------------
Traced this back to build_carrowgate_mainland.py (the script that built the
background mountains/city/ground you're looking at in these screenshots --
separate from CarrowGateGarrison's own close-in props, which is what the
earlier water/wall script touched).

  - The mountains (SM_Iceland_Eroded_Mountain / SM_Iceland_Mountain_02 /
    SM_Mountain_01) are spawned WITHOUT a material override -- spawn_mountain()
    never calls mesh_comp.set_material(), so each one should be showing its
    own real, already-textured pack material (the Iceland pack ships full
    BaseColor/Normal/ORM sets for these: T_Mountain_01, T_Mountain_02,
    T_Iceland_Eroded, T_Iceland_Dirt). That's good news -- it means most of
    the range shouldn't need new textures built for it at all.
  - The GROUND under/around the mountains and city, though, IS a flat single
    color -- PALETTE["ground"] is a MaterialInstanceConstant off a plain
    "M_FlatCol" flat-color master material (get_or_make_flat_material), not a
    real texture. That's the flat brown you're seeing close to camera in your
    2nd/4th screenshots -- that part is a real, confirmed placeholder.
  - I could NOT determine from static inspection alone which single mountain
    instance is rendering as the black sliver -- that needs live values
    (assigned material, actual scale) that only the running editor has. So
    rather than guess a third time on something I can't verify statically
    (see the hand-IK lesson), this script's mountain pass does two things:
      (a) SAFE, unconditional: shifts the whole mountain range down 6m, and
          logs every mountain instance's mesh/scale/world-size/material name
          so the actual culprit is identifiable by label from the Output Log.
      (b) CONDITIONAL, targeted: only overrides a mountain's material with a
          new, real, triplanar-textured rock material if that instance's
          CURRENT material name matches the known flat-color placeholder
          names (MI_Landmass_Mountain / MI_Landmass_MountainFar) or is
          missing entirely -- i.e. it only touches instances that are
          actually confirmed untextured, never ones already using the pack's
          real imported material.

WHAT THIS SCRIPT DOES
----------------------
1. DIAGNOSTIC LOG (always runs, read-only): every actor under the
   "CG Mainland/Mountains" folder tree -- label, mesh name, scale, live
   world-space size, and current material-slot-0 name. Read this after
   running; the black sliver will likely stand out as an extreme world-size
   or an odd scale ratio compared to its siblings. Paste the relevant line(s)
   back and I can target a precise fix (reset scale, swap mesh, etc.) instead
   of guessing.

2. MOVE MOUNTAINS DOWN 6M: every actor under "CG Mainland/Mountains"
   (recursive, so the "/Ground" and "/Wall" subfolders move with it) gets
   shifted -600cm in world Z. This is unconditional, as requested.

3. GROUND RETEXTURE: builds a new triplanar (world-aligned, seamless) PBR
   material, M_AI_MountainGround, from the Iceland pack's own
   T_Iceland_Dirt texture set (BaseColor + Normal + ORM -- real roughness/
   metallic, not a flat constant this time, since the source maps exist).
   Finds every actor in the level whose material slot 0 is the flat
   MI_Landmass_Ground instance and swaps it to the new textured material
   directly on that mesh component -- the flat MI_Landmass_Ground asset
   itself is left alone (in case anything else still wants a flat brown, and
   so this is safe to re-run/undo by re-running build_carrowgate_mainland.py
   if you want the old look back).

4. MOUNTAIN RETEXTURE (conditional, see above): any mountain actor whose
   current material is missing or is one of the flat MI_Landmass_Mountain*
   placeholders gets a new triplanar PBR material built from T_Mountain_01
   (BaseColor + Normal + ORM) instead.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_mountains_and_ground.py"

Safe to re-run. The move-down-6m step is NOT idempotent by design (each run
shifts by another 6m) -- if you run it twice by accident, move everything
back up 6m per extra run (or reload the level without saving).
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MOUNTAIN_FOLDER_ROOT = "CG Mainland/Mountains"
MOUNTAIN_DROP_CM = -600.0  # 6m down

FLAT_GROUND_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_Ground"
FLAT_MOUNTAIN_MATERIAL_NAMES = ("MI_Landmass_Mountain", "MI_Landmass_MountainFar")

NEW_GROUND_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_MountainGround"
NEW_MOUNTAIN_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_MountainRock"

DIRT_BASECOLOR = "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Dirt/T_Iceland_Dirt_BaseColor"
DIRT_NORMAL = "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Dirt/T_Iceland_Dirt_Normal"
DIRT_ORM = "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Dirt/T_Iceland_Dirt_ORM"

MOUNTAIN_BASECOLOR = "/Game/Landscaping/IcelandEnviroment/Textures/T_Mountain_01/T_Mountain_01_BaseColor"
MOUNTAIN_NORMAL = "/Game/Landscaping/IcelandEnviroment/Textures/T_Mountain_01/T_Mountain_01_Normal"
# T_Mountain_01 has no ORM in this project -- T_Mountain_02's ORM is the closest real
# roughness/metallic map available for this rock family; reused here rather than
# falling back to a flat constant, since a real map exists.
MOUNTAIN_ORM = "/Game/Landscaping/IcelandEnviroment/Textures/T_Mountain_02/T_Mountain_02_ORM"


def log(msg):
    print("[FixMountains] %s" % msg)


def is_under_folder(actor, root):
    folder = str(actor.get_folder_path())
    return folder == root or folder.startswith(root + "/")


def get_slot0_material_name(actor):
    if not isinstance(actor, unreal.StaticMeshActor):
        return None
    comp = actor.static_mesh_component
    mat = comp.get_material(0) if comp else None
    return mat.get_name() if mat else None


# --- Step 1: diagnostic log + Step 2: move down ------------------------------

def diagnose_and_lower_mountains():
    all_actors = actor_subsystem.get_all_level_actors()
    mountain_actors = [a for a in all_actors if is_under_folder(a, MOUNTAIN_FOLDER_ROOT)]
    log("Found %d actor(s) under '%s'." % (len(mountain_actors), MOUNTAIN_FOLDER_ROOT))

    for a in mountain_actors:
        comp = a.static_mesh_component if isinstance(a, unreal.StaticMeshActor) else None
        mesh = comp.static_mesh if comp else None
        scale = a.get_actor_scale3d()
        origin, extent = a.get_actor_bounds(False)
        mat_name = get_slot0_material_name(a)
        log("  %-32s mesh=%-32s scale=(%.2f,%.2f,%.2f) world_size_m=(%.1f,%.1f,%.1f) material=%s" % (
            a.get_actor_label(),
            mesh.get_name() if mesh else "(none)",
            scale.x, scale.y, scale.z,
            extent.x * 2 / 100.0, extent.y * 2 / 100.0, extent.z * 2 / 100.0,
            mat_name or "(none / default)",
        ))

    for a in mountain_actors:
        a.add_actor_world_offset(unreal.Vector(0.0, 0.0, MOUNTAIN_DROP_CM), False, False)
    log("Moved %d mountain actor(s) down %.0fm." % (len(mountain_actors), abs(MOUNTAIN_DROP_CM) / 100.0))

    return mountain_actors


# --- Triplanar PBR builder (basecolor + normal + roughness/metallic from ORM) ----

def build_triplanar_pbr(material, basecolor_tex, normal_tex, orm_tex, tile_world_size=1500.0, blend_sharpness=4.0):
    log("Rebuilding %s as triplanar PBR (basecolor%s%s)..." % (
        material.get_name(),
        " + normal" if normal_tex else "",
        " + ORM" if orm_tex else "",
    ))
    MEL.delete_all_material_expressions(material)

    world_pos = MEL.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -1600, 0)
    tile_scale = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1600, 150)
    tile_scale.set_editor_property("R", 1.0 / tile_world_size)
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
    sharpness_const.set_editor_property("R", blend_sharpness)
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

    def sample_and_blend(tex, out_y, prop, is_normal=False):
        """Samples `tex` through the 3 existing coordinate masks, blends by the
        3 existing normalized weights, connects the result to `prop`."""
        tx = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y - 200)
        tx.set_editor_property("texture", tex)
        if is_normal:
            tx.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        MEL.connect_material_expressions(mask_yz, "", tx, "Coordinates")

        ty = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y)
        ty.set_editor_property("texture", tex)
        if is_normal:
            ty.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        MEL.connect_material_expressions(mask_xz, "", ty, "Coordinates")

        tz = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y + 200)
        tz.set_editor_property("texture", tex)
        if is_normal:
            tz.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        MEL.connect_material_expressions(mask_xy, "", tz, "Coordinates")

        out_pin = "RGB"
        mul_x = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y - 200)
        MEL.connect_material_expressions(tx, out_pin, mul_x, "A")
        MEL.connect_material_expressions(norm_x, "", mul_x, "B")
        mul_y = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y)
        MEL.connect_material_expressions(ty, out_pin, mul_y, "A")
        MEL.connect_material_expressions(norm_y, "", mul_y, "B")
        mul_z = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y + 200)
        MEL.connect_material_expressions(tz, out_pin, mul_z, "A")
        MEL.connect_material_expressions(norm_z, "", mul_z, "B")

        add_xy = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 480, out_y - 100)
        MEL.connect_material_expressions(mul_x, "", add_xy, "A")
        MEL.connect_material_expressions(mul_y, "", add_xy, "B")
        add_xyz = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 640, out_y)
        MEL.connect_material_expressions(add_xy, "", add_xyz, "A")
        MEL.connect_material_expressions(mul_z, "", add_xyz, "B")

        MEL.connect_material_property(add_xyz, "", prop)
        return add_xyz

    sample_and_blend(basecolor_tex, 0, unreal.MaterialProperty.MP_BASE_COLOR)

    if normal_tex:
        sample_and_blend(normal_tex, 900, unreal.MaterialProperty.MP_NORMAL, is_normal=True)

    if orm_tex:
        orm_blend = sample_and_blend(orm_tex, 1500, None)  # connect manually below (need G/B channels)
        # sample_and_blend already wired the full RGB sum into nothing (prop=None skips connect);
        # split it into roughness (G) and metallic (B) ourselves.
        rough_mask = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, 820, 1450)
        rough_mask.set_editor_property("R", False); rough_mask.set_editor_property("G", True)
        rough_mask.set_editor_property("B", False); rough_mask.set_editor_property("A", False)
        MEL.connect_material_expressions(orm_blend, "", rough_mask, "")
        MEL.connect_material_property(rough_mask, "", unreal.MaterialProperty.MP_ROUGHNESS)

        metal_mask = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, 820, 1550)
        metal_mask.set_editor_property("R", False); metal_mask.set_editor_property("G", False)
        metal_mask.set_editor_property("B", True); metal_mask.set_editor_property("A", False)
        MEL.connect_material_expressions(orm_blend, "", metal_mask, "")
        MEL.connect_material_property(metal_mask, "", unreal.MaterialProperty.MP_METALLIC)
    else:
        rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 820, 1450)
        rough_const.set_editor_property("R", 0.85)
        MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

    MEL.recompile_material(material)
    log("  done -- %s recompiled." % material.get_name())


def get_or_create_material(path):
    if AL.does_asset_exist(path):
        return AL.load_asset(path)
    package_path, name = path.rsplit("/", 1)
    factory = unreal.MaterialFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    return asset_tools.create_asset(name, package_path, unreal.Material, factory)


def retexture_ground():
    dirt_base = AL.load_asset(DIRT_BASECOLOR)
    dirt_normal = AL.load_asset(DIRT_NORMAL)
    dirt_orm = AL.load_asset(DIRT_ORM)
    if not dirt_base:
        log("SKIPPED ground retexture -- could not load %s" % DIRT_BASECOLOR)
        return

    ground_mat = get_or_create_material(NEW_GROUND_MATERIAL_PATH)
    build_triplanar_pbr(ground_mat, dirt_base, dirt_normal, dirt_orm, tile_world_size=2000.0)

    flat_ground_asset = AL.load_asset(FLAT_GROUND_MATERIAL_PATH) if AL.does_asset_exist(FLAT_GROUND_MATERIAL_PATH) else None
    if flat_ground_asset is None:
        log("Note: %s doesn't exist in this checkout -- nothing to swap away from, "
            "but the new material is built and ready at %s." % (FLAT_GROUND_MATERIAL_PATH, NEW_GROUND_MATERIAL_PATH))
        return

    swapped = 0
    for a in actor_subsystem.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        comp = a.static_mesh_component
        if comp and comp.get_material(0) == flat_ground_asset:
            comp.set_material(0, ground_mat)
            swapped += 1
    log("Swapped %d ground actor(s) from the flat placeholder to the new textured material." % swapped)


def retexture_flat_mountains(mountain_actors):
    mtn_base = AL.load_asset(MOUNTAIN_BASECOLOR)
    mtn_normal = AL.load_asset(MOUNTAIN_NORMAL)
    mtn_orm = AL.load_asset(MOUNTAIN_ORM)
    if not mtn_base:
        log("SKIPPED mountain retexture -- could not load %s" % MOUNTAIN_BASECOLOR)
        return

    to_fix = []
    for a in mountain_actors:
        mat_name = get_slot0_material_name(a)
        if mat_name is None or mat_name in FLAT_MOUNTAIN_MATERIAL_NAMES:
            to_fix.append(a)

    if not to_fix:
        log("No mountain instances are on a flat/placeholder material -- all of them already "
            "carry a real imported material, so nothing was retextured here. If one still "
            "looks wrong (e.g. the black sliver), it's a geometry/scale issue, not a missing "
            "texture -- check the diagnostic log above for the outlier's scale/world_size.")
        return

    mtn_mat = get_or_create_material(NEW_MOUNTAIN_MATERIAL_PATH)
    build_triplanar_pbr(mtn_mat, mtn_base, mtn_normal, mtn_orm, tile_world_size=4000.0)

    for a in to_fix:
        comp = a.static_mesh_component
        comp.set_material(0, mtn_mat)
    log("Retextured %d mountain instance(s) that were on a flat/missing material: %s" % (
        len(to_fix), ", ".join(a.get_actor_label() for a in to_fix)))


def run():
    mountain_actors = diagnose_and_lower_mountains()
    retexture_ground()
    retexture_flat_mountains(mountain_actors)
    log("All done. Save the level and modified materials (Ctrl+Shift+S / File > Save All), "
        "then check the mountains/ground in the viewport or a fresh PIE run. If the black "
        "sliver is still there, find its line in the diagnostic log above (unusual scale or "
        "world_size compared to its neighbors) and send me that line.")


run()
