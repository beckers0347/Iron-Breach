"""
ADD TRUNKS UNDER THE SHRUB "TREES" -- CG Mainland
================================================================
IRON BREACH / Unreal Engine 5.8

WHY THIS IS NEEDED
-------------------
build_carrowgate_mainland.py's own TREE_ASSET_KIT comment explains this
directly: real Tripo3D tree generations don't exist yet, so every "tree" in
the forest is actually one of the Iceland pack's shrub meshes
(GV_Vol7_Shrub_*_full_type*) used as an interim stand-in. Shrubs don't have a
trunk modeled in at all -- that's not a bug, it's the documented placeholder
state -- but it reads as "floating bush with no trunk," which is what you're
seeing.

WHAT THIS SCRIPT DOES
----------------------
Doesn't touch the shrub meshes themselves. Instead, for every actor under
"CG Mainland/Trees" (any of the Causeway/Outskirts/Fringe/Belt/Understory
subfolders -- whatever survived the earlier thinning pass) whose mesh is one
of the known shrub assets, it spawns a simple cylinder trunk underneath it:
positioned at the shrub's own base, sized to roughly half the shrub's own
height, with a proper bark texture (T_Bark_A -- diffuse/normal/roughness,
already in the Landscaping/Shrubs pack, just never wired to anything) instead
of a flat color, so it actually reads as wood.

Each trunk is parented to its shrub actor (so moving/deleting the shrub later
takes the trunk with it) and placed in a "Trunks" subfolder alongside the
tree it belongs to.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/add_tree_trunks.py"

Safe to re-run IF you haven't run it before -- it does NOT check for an
existing trunk on a given shrub, so running it twice will double up trunks.
If you need to re-run after an interrupted first pass, delete everything
under the "CG Mainland/Trees/.../Trunks" folders first.
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

TREES_ROOT = "CG Mainland/Trees"
CYLINDER_MESH_PATH = "/Engine/BasicShapes/Cylinder.Cylinder"

TRUNK_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_TreeTrunk"
BARK_DIFFUSE = "/Game/Landscaping/Shrubs/Textures/Shrubs/Bark_A/T_Bark_A_diffuse"
BARK_NORMAL = "/Game/Landscaping/Shrubs/Textures/Shrubs/Bark_A/T_Bark_A_normal"
BARK_ROUGH = "/Game/Landscaping/Shrubs/Textures/Shrubs/Bark_A/T_Bark_A_rough"

SHRUB_MESH_NAMES = {
    "GV_Vol7_Shrub_A_full_type1", "GV_Vol7_Shrub_B_full_type1", "GV_Vol7_Shrub_C_full_type1",
    "GV_Vol7_Shrub_D_full_type1", "GV_Vol7_Shrub_E_full_type1_A", "GV_Vol7_Shrub_F_full_type1_B",
    "GV_Vol7_Shrub_G_full_type1_C", "GV_Vol7_Shrub_H_full_type1_D", "GV_Vol7_Shrub_I_full_type1",
}

TRUNK_HEIGHT_FRACTION = 0.5   # trunk height as a fraction of the shrub's own live height
TRUNK_RADIUS_M = 0.18         # trunk radius in meters


def log(msg):
    print("[AddTrunks] %s" % msg)


def is_under_folder(actor, root):
    folder = str(actor.get_folder_path())
    return folder == root or folder.startswith(root + "/")


def build_trunk_material():
    if AL.does_asset_exist(TRUNK_MATERIAL_PATH):
        mat = AL.load_asset(TRUNK_MATERIAL_PATH)
    else:
        package_path, name = TRUNK_MATERIAL_PATH.rsplit("/", 1)
        factory = unreal.MaterialFactoryNew()
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        mat = asset_tools.create_asset(name, package_path, unreal.Material, factory)

    diffuse = AL.load_asset(BARK_DIFFUSE)
    normal = AL.load_asset(BARK_NORMAL)
    rough = AL.load_asset(BARK_ROUGH)
    if not diffuse:
        log("WARNING: could not load %s -- trunk material will be untextured." % BARK_DIFFUSE)
        return mat

    MEL.delete_all_material_expressions(mat)
    uv = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -600, 0)
    uv.set_editor_property("u_tiling", 1.0)
    uv.set_editor_property("v_tiling", 3.0)  # trunk is tall/thin -- stretch V so bark doesn't look squashed

    tex_diffuse = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -300, -150)
    tex_diffuse.set_editor_property("texture", diffuse)
    MEL.connect_material_expressions(uv, "", tex_diffuse, "Coordinates")
    MEL.connect_material_property(tex_diffuse, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    if normal:
        tex_normal = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -300, 100)
        tex_normal.set_editor_property("texture", normal)
        tex_normal.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        MEL.connect_material_expressions(uv, "", tex_normal, "Coordinates")
        MEL.connect_material_property(tex_normal, "RGB", unreal.MaterialProperty.MP_NORMAL)

    if rough:
        tex_rough = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -300, 300)
        tex_rough.set_editor_property("texture", rough)
        MEL.connect_material_expressions(uv, "", tex_rough, "Coordinates")
        MEL.connect_material_property(tex_rough, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    else:
        rough_const = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 300)
        rough_const.set_editor_property("R", 0.85)
        MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

    MEL.recompile_material(mat)
    log("Built trunk material %s from T_Bark_A." % mat.get_name())
    return mat


def run():
    trunk_mat = build_trunk_material()
    cylinder_mesh = AL.load_asset(CYLINDER_MESH_PATH)
    if not cylinder_mesh:
        log("SKIPPED -- could not load engine cylinder mesh at %s" % CYLINDER_MESH_PATH)
        return

    all_actors = actor_subsystem.get_all_level_actors()
    shrub_actors = []
    for a in all_actors:
        if not (isinstance(a, unreal.StaticMeshActor) and is_under_folder(a, TREES_ROOT)):
            continue
        comp = a.static_mesh_component
        mesh = comp.static_mesh if comp else None
        if mesh and mesh.get_name() in SHRUB_MESH_NAMES:
            shrub_actors.append(a)

    log("Found %d shrub/tree actor(s) under '%s' needing a trunk." % (len(shrub_actors), TREES_ROOT))

    added = 0
    for shrub in shrub_actors:
        origin, extent = shrub.get_actor_bounds(False)
        base_z = origin.z - extent.z          # world Z of the shrub's own base
        shrub_height_cm = extent.z * 2.0
        trunk_height_cm = max(30.0, shrub_height_cm * TRUNK_HEIGHT_FRACTION)

        trunk_loc = unreal.Vector(origin.x, origin.y, base_z + trunk_height_cm / 2.0)
        trunk = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, trunk_loc, unreal.Rotator(0, 0, 0))
        trunk.set_actor_label(f"{shrub.get_actor_label()}_Trunk")
        trunk.set_folder_path(f"{str(shrub.get_folder_path())}/Trunks")

        tcomp = trunk.static_mesh_component
        tcomp.set_static_mesh(cylinder_mesh)
        # Engine BasicShapes/Cylinder is 100cm diameter x 100cm tall at scale 1,1,1.
        diameter_cm = TRUNK_RADIUS_M * 2.0 * 100.0
        tcomp.set_world_scale3d(unreal.Vector(diameter_cm / 100.0, diameter_cm / 100.0, trunk_height_cm / 100.0))
        tcomp.set_material(0, trunk_mat)
        tcomp.set_mobility(unreal.ComponentMobility.STATIC)

        try:
            trunk.attach_to_actor(shrub, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD)
        except Exception:
            pass  # attachment is cosmetic/organizational only -- not fatal if it fails on a given actor

        added += 1

    log("Added %d trunk(s). Save the level (Ctrl+S) and check the viewport / re-run PIE." % added)


run()
