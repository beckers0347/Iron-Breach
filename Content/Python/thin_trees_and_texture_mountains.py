"""
THIN CG MAINLAND TREES + TEXTURE THE MOUNTAINS
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Two independent passes in one script, both against the "CG Mainland"
background set built by build_carrowgate_mainland.py (the mountains/city/
forest around CarrowGateGarrison -- different from the garrison's own close-in
props).

A NOTE ON TRIPO3D
------------------
I don't have a way to call out to Tripo3D or generate new textures from this
session -- no image/3D-generation tool is wired up here, so I can't produce
new mountain rock textures the way the project's Tripo3D pipeline normally
does. What I *can* do is put the REAL texture sets already sitting unused in
the Iceland landscaping pack onto the mountains -- T_Mountain_01,
T_Mountain_02, and T_Iceland_Eroded all have proper BaseColor + Normal maps
already imported under Content/Landscaping/IcelandEnviroment/Textures/, they
just weren't reaching the mountain meshes with enough visible surface detail.
That's what this script's mountain pass does. If that still doesn't read as
textured enough once you look at it, the next step really would be
generating dedicated Tripo3D mountain textures -- that has to happen through
whatever normally drives that pipeline for this project (the same one that
made the SM_Building_* / BUILDING_ASSET_KIT models), not from here.

PASS 1 -- THIN THE TREES
--------------------------
build_carrowgate_mainland.py scatters trees into 5 separate folders under
"CG Mainland/Trees": Causeway, Outskirts, Fringe, Belt, Understory.
"Outskirts" is the one that fills gaps directly between the town's own
buildings -- that's almost certainly what's reading as overgrown in your
screenshots -- so it gets cut hardest. Fringe/Belt/Understory are the outer
forest wall against the foothills (meant to read as a distant treeline); cut
less hard by default so it doesn't go bald, but still thinned since you asked
for "way more" overall. Tune the KEEP_RATIOS dict below per-folder if any of
these numbers over/undershoot once you see it.

Deterministic seeded shuffle per folder, same pattern as the earlier
thin_garrison_trees.py -- re-running at the same ratios won't re-roll which
instances survive.

PASS 2 -- TEXTURE THE MOUNTAINS
---------------------------------
Unconditionally (not gated on "is it already textured" this time, since the
conditional pass in fix_mountains_and_ground.py apparently didn't produce a
visible change) rebuilds a triplanar (world-aligned, seamless) material per
mountain mesh type, using that mesh's own matching real texture from the
Iceland pack, and assigns it directly:
    SM_Mountain_01            -> T_Mountain_01
    SM_Iceland_Mountain_02    -> T_Mountain_02
    SM_Iceland_Eroded_Mountain -> T_Iceland_Eroded
BaseColor + Normal only (no ORM/metallic sampling this time -- that's what
caused the ground-turned-water bug last time; roughness is a fixed matte
constant instead).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/thin_trees_and_texture_mountains.py"

The tree deletion is NOT reversible (it destroys actors) -- lower the keep
ratios and re-run for more thinning, but there's no "undo" short of a level
reload without saving. The mountain retexture is safe to re-run any time.
"""

import random
import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# ---------------------------------------------------------------------------
# PASS 1 config
# ---------------------------------------------------------------------------
TREES_ROOT = "CG Mainland/Trees"
RANDOM_SEED = 4242

# Fraction of each folder's actors to KEEP (rest are deleted). Outskirts (the
# clusters filling gaps between town buildings) cut hardest.
KEEP_RATIOS = {
    "CG Mainland/Trees/Outskirts": 0.12,
    "CG Mainland/Trees/Causeway": 0.25,
    "CG Mainland/Trees/Fringe": 0.45,
    "CG Mainland/Trees/Belt": 0.40,
    "CG Mainland/Trees/Understory": 0.25,
}

# ---------------------------------------------------------------------------
# PASS 2 config
# ---------------------------------------------------------------------------
MOUNTAIN_FOLDER_ROOT = "CG Mainland/Mountains"
MATERIAL_DIR = "/Game/LevelPrototyping/AITextures/Landmass"

MOUNTAIN_TEXTURE_SETS = {
    "SM_Mountain_01": {
        "basecolor": "/Game/Landscaping/IcelandEnviroment/Textures/T_Mountain_01/T_Mountain_01_BaseColor",
        "normal": "/Game/Landscaping/IcelandEnviroment/Textures/T_Mountain_01/T_Mountain_01_Normal",
        "material_name": "M_AI_MountainRock_01",
    },
    "SM_Iceland_Mountain_02": {
        "basecolor": "/Game/Landscaping/IcelandEnviroment/Textures/T_Mountain_02/T_Mountain_02_BaseColor",
        "normal": "/Game/Landscaping/IcelandEnviroment/Textures/T_Mountain_02/T_Mountain_02_Normal",
        "material_name": "M_AI_MountainRock_02",
    },
    "SM_Iceland_Eroded_Mountain": {
        "basecolor": "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Eroded/T_Iceland_Eroded_BaseColor",
        "normal": "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Eroded/Iceland_Eroded_Normal",
        "material_name": "M_AI_MountainRock_Eroded",
    },
}


def log(msg):
    print("[ThinAndTexture] %s" % msg)


# --- Pass 1 --------------------------------------------------------------

def thin_trees():
    all_actors = actor_subsystem.get_all_level_actors()
    by_folder = {}
    for a in all_actors:
        folder = str(a.get_folder_path())
        if folder in KEEP_RATIOS:
            by_folder.setdefault(folder, []).append(a)

    total_before = sum(len(v) for v in by_folder.values())
    total_deleted = 0
    for folder, keep_ratio in KEEP_RATIOS.items():
        actors = by_folder.get(folder, [])
        if not actors:
            log("  %-38s 0 actors found (folder empty or not present)" % folder)
            continue
        actors_sorted = sorted(actors, key=lambda a: a.get_actor_label())
        rng = random.Random(RANDOM_SEED ^ hash(folder) & 0xFFFFFFFF)
        rng.shuffle(actors_sorted)
        keep_count = int(round(len(actors_sorted) * keep_ratio))
        to_delete = actors_sorted[keep_count:]
        for a in to_delete:
            actor_subsystem.destroy_actor(a)
        total_deleted += len(to_delete)
        log("  %-38s %5d -> %5d (kept %.0f%%, deleted %d)" % (
            folder, len(actors_sorted), keep_count, keep_ratio * 100.0, len(to_delete)))

    log("Tree thinning done: %d -> %d actors across %d folder(s)." % (
        total_before, total_before - total_deleted, len(KEEP_RATIOS)))


# --- Pass 2 ----------------------------------------------------------------

def build_triplanar_basecolor_normal(material, basecolor_tex, normal_tex, tile_world_size=4000.0, blend_sharpness=4.0, roughness=0.95):
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
    if normal_tex:
        sample_and_blend(normal_tex, 900, unreal.MaterialProperty.MP_NORMAL, is_normal=True)

    rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 260, 1400)
    rough_const.set_editor_property("R", roughness)
    MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)
    # No metallic connection -- defaults to 0. Learned that lesson on the ground pass.

    MEL.recompile_material(material)


def get_or_create_material(path):
    if AL.does_asset_exist(path):
        return AL.load_asset(path)
    package_path, name = path.rsplit("/", 1)
    factory = unreal.MaterialFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    return asset_tools.create_asset(name, package_path, unreal.Material, factory)


def is_under_folder(actor, root):
    folder = str(actor.get_folder_path())
    return folder == root or folder.startswith(root + "/")


def texture_mountains():
    built = {}
    for mesh_name, cfg in MOUNTAIN_TEXTURE_SETS.items():
        basecolor = AL.load_asset(cfg["basecolor"])
        normal = AL.load_asset(cfg["normal"])
        if not basecolor:
            log("  SKIPPED %s -- could not load %s" % (mesh_name, cfg["basecolor"]))
            continue
        mat_path = f"{MATERIAL_DIR}/{cfg['material_name']}"
        mat = get_or_create_material(mat_path)
        build_triplanar_basecolor_normal(mat, basecolor, normal)
        built[mesh_name] = mat
        log("  built %s for mesh %s" % (cfg["material_name"], mesh_name))

    all_actors = actor_subsystem.get_all_level_actors()
    mountain_actors = [a for a in all_actors if is_under_folder(a, MOUNTAIN_FOLDER_ROOT)
                        and isinstance(a, unreal.StaticMeshActor)]

    assigned = 0
    unmatched = 0
    for a in mountain_actors:
        comp = a.static_mesh_component
        mesh = comp.static_mesh if comp else None
        mesh_name = mesh.get_name() if mesh else None
        mat = built.get(mesh_name)
        if mat is None:
            unmatched += 1
            continue
        comp.set_material(0, mat)
        assigned += 1

    log("Assigned real triplanar rock materials to %d mountain actor(s) (%d had no matching mesh entry)." % (
        assigned, unmatched))


def run():
    log("=== Pass 1: thinning CG Mainland trees ===")
    thin_trees()
    log("=== Pass 2: texturing mountains ===")
    texture_mountains()
    log("All done. Save the level and modified materials (Ctrl+Shift+S / File > Save All), "
        "then check the viewport or a fresh PIE run.")


run()
