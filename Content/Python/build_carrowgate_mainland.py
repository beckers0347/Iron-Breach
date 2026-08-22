"""
Connect the Main Gate to a mainland: causeway, small city, mountains, trees
============================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
CarrowGateGarrison currently sits on an isolated platform -- the Main Gate
(world origin, arch at (0,0,3m), open edge facing -X per the garrison's own
layout: everything else -- Vehicle Bay, Parade Yard, Docks/Harbor -- extends
+X from the gate) opens onto nothing. This script builds the missing "other
side": a causeway leading west from the gate into a mainland blockout with

  1. An approach causeway/road from the gate (X=0) out to the mainland edge.
  2. A small city -- a grid of placeholder buildings with streets between --
     matching the concept doc's "all exits lead toward civilian districts"
     note.
  3. A mountain backdrop further out (cone blockouts, arc across the horizon).
  4. Scattered trees along the road, between city blocks, and at the city's
     edge where it meets the foothills.

This is a BLOCKOUT pass, matching how Shane wants this done: simple shapes
now, in the right scale and layout, so real Tripo3D-generated buildings/
mountains/trees can be swapped in later without re-doing the layout work.
Every spawned actor lives under a unique Outliner root folder ("CG Mainland")
so cleanup_previous_run() here can never touch (or collide with) anything
build_carrowgate_garrison.py or build_m1_district.py already placed, and
vice versa -- same collision-safety pattern as everything else in this repo.

COORDINATE FRAME
-----------------
Reuses CarrowGateGarrison's own world space (this script does NOT call
load_level -- run it with CarrowGateGarrison already open, same as the
garrison/armory scripts). +X is into the garrison (Vehicle Bay, Docks);
this script only ever places things at X <= -15m, i.e. west of the gate,
so it can never overlap the existing GateApproach/WestConnector pads that
already occupy roughly X = -10..+55.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/build_carrowgate_mainland.py"

Safe to re-run: deletes and rebuilds everything under "CG Mainland" first,
so tweaking constants below and re-running always converges cleanly.
Doesn't call save_level() -- save manually (Ctrl+S / File > Save Current
Level) once you're happy with the result, same as the other build scripts.
"""

import unreal
import math

M = 100.0  # meters -> Unreal units (cm)
ROOT_FOLDER = "CG Mainland"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

CUBE_MESH = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
CONE_MESH = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cone.Cone")
CYLINDER_MESH = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")

FLAT_COL_PARENT = unreal.EditorAssetLibrary.load_asset("/Game/LevelPrototyping/Materials/M_FlatCol.M_FlatCol")
FALLBACK_GROUND = unreal.EditorAssetLibrary.load_asset("/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground")
FALLBACK_WALL = unreal.EditorAssetLibrary.load_asset("/Game/LevelPrototyping/AITextures/M_AI_Wall.M_AI_Wall")

MATERIAL_DIR = "/Game/LevelPrototyping/AITextures/Landmass"
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

# ---------------------------------------------------------------------------
# Real-model kit -- once these are generated (Tripo3D) and imported under
# ASSET_ROOT with these exact names, re-running this script swaps every
# matching placeholder over automatically (real_or_* helpers below check
# EditorAssetLibrary.load_asset() and fall back to the blockout shape if an
# asset isn't there yet). No per-instance code changes needed as the kit
# fills in -- that's the whole point of building the layout this way.
# ---------------------------------------------------------------------------
ASSET_ROOT = "/Game/Environment/CGMainland/AIModels"

BUILDING_ASSET_KIT = [
    f"{ASSET_ROOT}/SM_Building_Cottage",
    f"{ASSET_ROOT}/SM_Building_Apartment",
    f"{ASSET_ROOT}/SM_Building_Warehouse",
    f"{ASSET_ROOT}/SM_Building_Tower",
    f"{ASSET_ROOT}/SM_Building_Shopfront",
    f"{ASSET_ROOT}/SM_Building_Rowhouse",
    f"{ASSET_ROOT}/SM_Building_Spire",
    f"{ASSET_ROOT}/SM_Building_Garage",
    f"{ASSET_ROOT}/SM_Building_Ruin",
]
# Still awaiting real Tripo3D tree generations (same pipeline as the 9
# buildings) -- these paths don't exist yet, so trees keep falling back to
# the cylinder+cone placeholders until SM_Tree_* assets land here.
#
# scan_tree_mountain_assets.py found existing "tree" meshes in the project's
# Landscaping pack (Tree_Black_Alder / Tree_Hornbeam), but those are all
# modular branch/leaf/decoration pieces meant to be assembled by a
# tree-builder Blueprint, not single drop-in meshes -- not usable here as-is.
# The pack's shrub set DOES include one pre-assembled "full" mesh per shrub
# type though (GV_Vol7_Shrub_*_full_type*), so those are wired in below as an
# interim stand-in for roadside/foothill greenery -- shrubs, not full-canopy
# trees. Swap SM_Tree_* in once real trees are generated.
#
# NOTE: the SM_Tree_Pine/Oak/Dead/Birch/Shrub placeholder paths used to be
# listed first in this kit "for when they land" -- but since real_or_placeholder
# picks a kit slot by hashing the label and none of those 5 paths have ever
# resolved to a real asset, ~36% of trees permanently fell back to the
# cylinder+cone blockout every run even after the shrub stand-ins were wired
# in below (Shane: "some of the old trees are still there, the ones you
# modeled"). Dropping the 5 dead entries so every slot in this kit resolves
# to a real shrub mesh -- add SM_Tree_* back in once actual tree generations
# exist under ASSET_ROOT.
TREE_ASSET_KIT = [
    "/Game/Landscaping/Shrubs/Meshes/Shrubs/Wind/Shrub_A/GV_Vol7_Shrub_A_full_type1",
    "/Game/Landscaping/Shrubs/Meshes/Shrubs/Wind/Shrub_B/GV_Vol7_Shrub_B_full_type1",
    "/Game/Landscaping/Shrubs/Meshes/Shrubs/Wind/Shrub_C/GV_Vol7_Shrub_C_full_type1",
    "/Game/Landscaping/Shrubs/Meshes/Shrubs/Wind/Shrub_D/GV_Vol7_Shrub_D_full_type1",
    "/Game/Landscaping/Shrubs/Meshes/Shrubs/Wind/Shrub_E/GV_Vol7_Shrub_E_full_type1_A",
    "/Game/Landscaping/Shrubs/Meshes/Shrubs/Wind/Shrub_F/GV_Vol7_Shrub_F_full_type1_B",
    "/Game/Landscaping/Shrubs/Meshes/Shrubs/Wind/Shrub_G/GV_Vol7_Shrub_G_full_type1_C",
    "/Game/Landscaping/Shrubs/Meshes/Shrubs/Wind/Shrub_H/GV_Vol7_Shrub_H_full_type1_D",
    "/Game/Landscaping/Shrubs/Meshes/Shrubs/Wind/Shrub_I/GV_Vol7_Shrub_I_full_type1",
]
# Real single-mesh mountains found by scan_tree_mountain_assets.py under the
# project's Iceland landscaping pack. The [MtnDiag] log (see spawn_mountain's
# MOUNTAIN_NATIVE_HEIGHT_M below) showed this kit actually mixes two
# incompatible asset families: SM_Iceland_Eroded_Mountain, SM_Iceland_Mountain_02,
# and (surprise -- looked like a small rock by its name, isn't one) SM_Mountain_01
# are genuine full mountain-range meshes, natively ~350-400m tall with believable
# tall-peak proportions. SM_Mountain_02 through _09 and _Plateu_01 are small
# individual rock/outcrop meshes, natively only ~2-5m tall AND much wider than
# they are tall (a squat mesa/outcrop shape, not a peak) -- scaling one of
# those up to a full mountain's HEIGHT (uniform XYZ scale, since there's no
# reliable native footprint to fit separately) also blows its WIDTH out to
# hundreds of meters, which is what caused Peak_28 (SM_Mountain_01, before its
# real ~400m native height was known) to swallow the whole town, and made
# every other SM_Mountain_0X instance render as an oddly wide, flat-looking
# shelf rather than a peak. Restricting the kit to just the three confirmed,
# precisely-measured full-mountain meshes fixes both: no more guessing at an
# unmeasured mesh's scale, and every kit entry actually looks like a mountain.
MOUNTAIN_ASSET_KIT = [
    "/Game/Landscaping/IcelandEnviroment/Static_Meshes/SM_Iceland_Eroded_Mountain",
    "/Game/Landscaping/IcelandEnviroment/Static_Meshes/SM_Iceland_Mountain_02",
    "/Game/Landscaping/IcelandEnviroment/Static_Meshes/SM_Mountain_01",
]


def _pick_kit_asset(kit, seed):
    if not kit:
        return None
    idx = int(prand(str(seed) + "kit") * len(kit)) % len(kit)
    return unreal.EditorAssetLibrary.load_asset(kit[idx])

# Common vector-parameter names across different flat-color master material setups --
# tried in order, first one that doesn't throw wins. Logged once so re-runs are silent.
_COLOR_PARAM_CANDIDATES = ["Color", "BaseColor", "Base Color", "Tint", "Albedo"]
_resolved_color_param = [None]


def _tint_instance(instance, color):
    if _resolved_color_param[0] is not None:
        try:
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
                instance, _resolved_color_param[0], color)
            return True
        except Exception:
            pass
    for name in _COLOR_PARAM_CANDIDATES:
        try:
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance, name, color)
            _resolved_color_param[0] = name
            unreal.log(f"[CG Mainland] Flat-color parameter resolved to '{name}'.")
            return True
        except Exception:
            continue
    return False


def get_or_make_flat_material(name, rgb):
    """rgb = (r,g,b) 0..1. Reuses an existing MI if this script already made it."""
    path = f"{MATERIAL_DIR}/{name}"
    existing = unreal.EditorAssetLibrary.load_asset(path)
    if existing is not None:
        return existing
    if FLAT_COL_PARENT is None:
        unreal.log_warning(f"[CG Mainland] M_FlatCol not found -- '{name}' will fall back to M_AI_Wall (untinted).")
        return FALLBACK_WALL
    factory = unreal.MaterialInstanceConstantFactoryNew()
    instance = asset_tools.create_asset(name, MATERIAL_DIR, unreal.MaterialInstanceConstant, factory)
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, FLAT_COL_PARENT)
    color = unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0)
    if not _tint_instance(instance, color):
        unreal.log_warning(
            f"[CG Mainland] Could not find a color parameter on M_FlatCol for '{name}' -- "
            f"it'll render as M_FlatCol's own default color instead of {rgb}. Tint it by hand if needed.")
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    return instance


# ---------------------------------------------------------------------------
# Palette -- built lazily on first run() so asset creation only happens once.
# ---------------------------------------------------------------------------
PALETTE = {}


# Built by build_grass_material.py (run separately -- it wires up the Iceland
# pack's grass textures into a plain Material a StaticMeshComponent can use;
# see that script for why this couldn't just be another get_or_make_flat_material
# tint). Loaded here rather than at import time so this script still runs fine
# (falling back to the flat ground color) if that script hasn't been run yet.
GRASS_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Grass.M_AI_Grass"
# Built into M_AI_Water (see build_water_material.py) -- reused here for the
# shoreline beyond the mountains, same asset the garrison's own water plane uses.
WATER_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Water.M_AI_Water"
# Lighter, more turquoise near-shore variant -- build_water_material.py builds
# this from the same graph as M_AI_Water, just with a different tint (real
# water reads lighter close to the beach where light bounces off the sand).
WATER_SHALLOW_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Water_Shallow.M_AI_Water_Shallow"
# Built by build_foam_material.py -- animated, pulsing whitewater. Used as the
# parent for a few phase-offset Material Instance Constants (see
# get_or_make_foam_instance() below) rather than assigned directly, so
# build_shoreline()'s surf strips don't all surge in perfect unison.
FOAM_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Foam.M_AI_Foam"


def get_or_make_foam_instance(phase_seconds):
    """A Material Instance Constant off M_AI_Foam with its own PhaseOffset,
    so multiple surf strips built from the same parent surge at different
    moments instead of in lockstep. Returns None (blockout callers should
    fall back to PALETTE["water"]) if M_AI_Foam hasn't been built yet."""
    foam_parent = unreal.EditorAssetLibrary.load_asset(FOAM_MATERIAL_PATH)
    if foam_parent is None:
        return None
    name = f"MI_AI_Foam_P{int(phase_seconds * 10):03d}"
    path = f"{MATERIAL_DIR}/{name}"
    existing = unreal.EditorAssetLibrary.load_asset(path)
    if existing is not None:
        unreal.MaterialEditingLibrary.set_material_instance_parent(existing, foam_parent)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(existing, "PhaseOffset", phase_seconds)
        unreal.EditorAssetLibrary.save_loaded_asset(existing)
        return existing
    factory = unreal.MaterialInstanceConstantFactoryNew()
    instance = asset_tools.create_asset(name, MATERIAL_DIR, unreal.MaterialInstanceConstant, factory)
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, foam_parent)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "PhaseOffset", phase_seconds)
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    return instance


def build_palette():
    PALETTE["road"] = get_or_make_flat_material("MI_Landmass_Road", (0.10, 0.10, 0.11))
    PALETTE["ground"] = FALLBACK_GROUND or get_or_make_flat_material("MI_Landmass_Ground", (0.28, 0.24, 0.16))
    grass = unreal.EditorAssetLibrary.load_asset(GRASS_MATERIAL_PATH)
    if grass is None:
        unreal.log_warning(
            f"[CG Mainland] {GRASS_MATERIAL_PATH} not found -- run build_grass_material.py first for a "
            "textured mountain ground; falling back to the flat ground color for now.")
    PALETTE["mountain_ground"] = grass or PALETTE["ground"]
    water = unreal.EditorAssetLibrary.load_asset(WATER_MATERIAL_PATH)
    if water is None:
        unreal.log_warning(f"[CG Mainland] {WATER_MATERIAL_PATH} not found -- run build_water_material.py first for a real shoreline material.")
    PALETTE["water"] = water or PALETTE["ground"]
    water_shallow = unreal.EditorAssetLibrary.load_asset(WATER_SHALLOW_MATERIAL_PATH)
    if water_shallow is None:
        unreal.log_warning(f"[CG Mainland] {WATER_SHALLOW_MATERIAL_PATH} not found -- run build_water_material.py "
                            "(rebuilt to also produce this) for a lighter near-shore band.")
    PALETTE["water_shallow"] = water_shallow or PALETTE["water"]
    if unreal.EditorAssetLibrary.load_asset(FOAM_MATERIAL_PATH) is None:
        unreal.log_warning(f"[CG Mainland] {FOAM_MATERIAL_PATH} not found -- run build_foam_material.py first for "
                            "animated surf/foam; the shoreline will fall back to plain water there for now.")
    PALETTE["beach"] = get_or_make_flat_material("MI_Landmass_Beach", (0.76, 0.68, 0.52))
    PALETTE["helipad"] = get_or_make_flat_material("MI_Landmass_Helipad", (0.42, 0.43, 0.45))
    PALETTE["helipad_marking"] = get_or_make_flat_material("MI_Landmass_HelipadMarking", (0.95, 0.82, 0.15))
    PALETTE["helipad_light"] = get_or_make_flat_material("MI_Landmass_HelipadLight", (1.0, 0.32, 0.08))
    PALETTE["helipad_broken"] = get_or_make_flat_material("MI_Landmass_HelipadBroken", (0.16, 0.15, 0.14))
    PALETTE["helipad_rust"] = get_or_make_flat_material("MI_Landmass_HelipadRust", (0.32, 0.17, 0.08))
    PALETTE["debris"] = get_or_make_flat_material("MI_Landmass_Debris", (0.24, 0.23, 0.21))
    PALETTE["mountain"] = get_or_make_flat_material("MI_Landmass_Mountain", (0.35, 0.36, 0.38))
    PALETTE["mountain_far"] = get_or_make_flat_material("MI_Landmass_MountainFar", (0.55, 0.58, 0.62))
    PALETTE["trunk"] = get_or_make_flat_material("MI_Landmass_TreeTrunk", (0.22, 0.15, 0.09))
    PALETTE["canopy"] = get_or_make_flat_material("MI_Landmass_TreeCanopy", (0.14, 0.32, 0.13))
    PALETTE["building_a"] = get_or_make_flat_material("MI_Landmass_Building_A", (0.55, 0.52, 0.47))
    PALETTE["building_b"] = get_or_make_flat_material("MI_Landmass_Building_B", (0.42, 0.40, 0.38))
    PALETTE["building_c"] = get_or_make_flat_material("MI_Landmass_Building_C", (0.61, 0.44, 0.32))
    PALETTE["building_d"] = get_or_make_flat_material("MI_Landmass_Building_D", (0.33, 0.35, 0.40))


def prand(seed):
    """Deterministic pseudo-random float in [0,1) from an int/str seed -- no `random`
    module, so re-running with the same constants always produces the same layout
    (same convention as add_rubble_cluster in the other build scripts)."""
    h = hash(seed) & 0xFFFFFFFF
    h = (h * 9301 + 49297) % 233280
    return h / 233280.0


# ---------------------------------------------------------------------------
# Spawn helpers -- same shape as spawn_block() in build_carrowgate_garrison.py
# ---------------------------------------------------------------------------
def _spawn(label, folder, mesh, loc_m, size_m, rotation_deg=(0, 0, 0), material=None):
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    rotation = unreal.Rotator(rotation_deg[0], rotation_deg[1], rotation_deg[2])
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(mesh)
    mesh_comp.set_world_scale3d(unreal.Vector(size_m[0], size_m[1], size_m[2]))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    return actor


def spawn_block(label, folder, loc_m, size_m, rotation_deg=(0, 0, 0), material=None):
    return _spawn(label, folder, CUBE_MESH, loc_m, size_m, rotation_deg, material)


def spawn_cone(label, folder, loc_m, size_m, rotation_deg=(0, 0, 0), material=None):
    return _spawn(label, folder, CONE_MESH, loc_m, size_m, rotation_deg, material)


def spawn_cylinder(label, folder, loc_m, size_m, rotation_deg=(0, 0, 0), material=None):
    return _spawn(label, folder, CYLINDER_MESH, loc_m, size_m, rotation_deg, material)


def _mesh_bounds_m(mesh):
    """Local-space (unscaled) bounds of a static mesh, in meters: returns
    (min_z_m, native_size_m_xyz). Tries EditorStaticMeshLibrary's bounding
    box call first (this is what the original grounding fix used, and it's
    confirmed working for the imported Tripo3D buildings); falls back to the
    mesh's own 'extended_bounds' editor property (doesn't need an editor
    subsystem context, more reliable for assets loaded outside a running
    build like the asset-scan script); falls back to treating the mesh as
    already normalized to 1m native size with its pivot at the base if
    neither works, which reproduces the old "size_m IS the world scale"
    behavior rather than crashing or mis-scaling.

    Needed for TWO things: (1) grounding -- see _spawn_grounded -- and
    (2) correct scaling of any real mesh kit whose *native* size isn't
    already ~1m, e.g. a licensed landscaping-pack mountain mesh that's
    already dozens of meters across at scale 1,1,1, vs. a Tripo3D export
    which comes out close to 1m. Without native-size normalization, a kit
    asset from a pack like that would get scaled by desired-size-in-meters
    directly (as if it were already 1m) and come out enormous."""
    try:
        box = unreal.EditorStaticMeshLibrary.get_static_mesh_bounding_box(mesh)
        size = box.max - box.min
        if size.x > 1.0 and size.y > 1.0 and size.z > 1.0:
            return box.min.z / 100.0, (size.x / 100.0, size.y / 100.0, size.z / 100.0)
    except Exception:
        pass
    try:
        bounds = mesh.get_editor_property("extended_bounds")
        ext = bounds.box_extent
        origin = bounds.origin
        size_cm = (ext.x * 2.0, ext.y * 2.0, ext.z * 2.0)
        if size_cm[0] > 1.0 and size_cm[1] > 1.0 and size_cm[2] > 1.0:
            return (origin.z - ext.z) / 100.0, (size_cm[0] / 100.0, size_cm[1] / 100.0, size_cm[2] / 100.0)
    except Exception:
        pass
    return 0.0, (1.0, 1.0, 1.0)


def _spawn_grounded(label, folder, mesh, loc_m, size_m, rotation_deg=(0, 0, 0), ground_z_m=None, manual_scale=None):
    """Spawns `mesh`, rotated by rotation_deg, then corrects its Z so the
    mesh's own bounding-box BASE sits at ground level, not wherever its pivot
    happens to be. ground_z_m defaults to loc_m[2] - size_m[2]/2.0 (i.e.
    "loc_m[2] was a CENTER height, same convention every placeholder call
    site already uses"); pass ground_z_m explicitly for callers (like trees)
    that already pass true ground level.

    Scale: by default, fits the mesh's NATIVE bounding box to size_m meters
    (not size_m used as a raw scale factor -- see _mesh_bounds_m). Pass
    manual_scale=(sx,sy,sz) to use a fixed scale instead and skip that
    native-size fit entirely -- needed for the /Game/Landscaping/* pack (see
    spawn_mountain), where scan_tree_mountain_assets.py confirmed every
    single asset in that pack comes back with size_m_xyz=None: BOTH bounds
    reads in _mesh_bounds_m fail/return nothing for these meshes (unclear why
    -- possibly a Nanite or World-Partition-proxy quirk of this asset pack --
    but it means neither computing a fit-to-size_m scale NOR the old grounding
    correction (which used that same broken read for the mesh's local min-Z)
    ever had real numbers to work with for this pack. That's why mountains
    kept "floating" no matter how the burial margin was tuned: the correction
    was silently operating on a fallback 0.0, not a measurement.

    Grounding itself no longer depends on that read at all -- it queries the
    already-spawned, already-scaled ACTOR's live world-space bounds
    (AActor.get_actor_bounds), which UE computes from the actual render data
    regardless of whether EditorStaticMeshLibrary's asset-level bounding-box
    call works for a given mesh. Robust for every kit (buildings/trees/
    mountains alike), so it replaces the old min-Z-based offset everywhere."""
    if ground_z_m is None:
        ground_z_m = loc_m[2] - size_m[2] / 2.0
    if manual_scale is not None:
        scale = manual_scale
    else:
        _, native_size_m = _mesh_bounds_m(mesh)
        scale = tuple(
            (size_m[i] / native_size_m[i]) if native_size_m[i] > 1e-6 else size_m[i]
            for i in range(3)
        )
    actor = _spawn(label, folder, mesh, (loc_m[0], loc_m[1], ground_z_m), scale, rotation_deg)
    origin, extent = actor.get_actor_bounds(False)
    current_bottom_cm = origin.z - extent.z
    target_bottom_cm = ground_z_m * M
    if folder == "Mountains":
        # Extra insurance margin on top of the exact correction below: a
        # mountain reading as slightly SUNK into the ground hides any leftover
        # measurement error in a shadow; the same error on the float-above
        # side reads as an obvious gap. Bias the target down by a small cut of
        # the mountain's own height (floor 1m) so any residual error lands on
        # the safe side.
        target_bottom_cm -= max(100.0, extent.z * 0.03)
        unreal.log(f"[CG Mainland][MtnDiag] {label}: mesh={mesh.get_name()} scale={tuple(round(v, 3) for v in scale)} "
                   f"world_size_m={tuple(round(v * 2 / M, 1) for v in (extent.x, extent.y, extent.z))} "
                   f"corrected_bottom_by_m={round((target_bottom_cm - current_bottom_cm) / M, 2)}")
    if abs(target_bottom_cm - current_bottom_cm) > 0.01:
        actor.add_actor_world_offset(unreal.Vector(0.0, 0.0, target_bottom_cm - current_bottom_cm), False, False)
    return actor


def spawn_tree(label, folder, loc_m, trunk_h=3.0, canopy_h=4.0, canopy_r=1.8):
    real_mesh = _pick_kit_asset(TREE_ASSET_KIT, label)
    if real_mesh is not None:
        # The real kit entries are pre-assembled Landscaping-pack SHRUB meshes
        # (see TREE_ASSET_KIT comment) -- squat and bushy, not trunk+canopy
        # trees. Feeding them trunk_h+canopy_h (up to ~10m) stretched them
        # into giants (Shane: "trees are a bit too big" -- one instance came
        # out at world scale Z=6.4). Remap the same per-instance variance
        # (canopy_h/canopy_r, already seeded per-tree upstream) into a modest
        # shrub-appropriate size instead of just adding the placeholder's
        # trunk height on top.
        shrub_h = 1.1 + (canopy_h - 3.0) / 2.5 * 0.9      # placeholder canopy_h range 3.0-5.5 -> ~1.1-2.0m
        shrub_r = 0.6 + (canopy_r - 1.3) / 1.2 * 0.6      # placeholder canopy_r range 1.3-2.5 -> ~0.6-1.2m
        _spawn_grounded(label, folder, real_mesh, (loc_m[0], loc_m[1], loc_m[2]),
                         (shrub_r, shrub_r, shrub_h), ground_z_m=loc_m[2])
        return
    spawn_cylinder(f"{label}_Trunk", folder, (loc_m[0], loc_m[1], loc_m[2] + trunk_h / 2.0),
                    (0.5, 0.5, trunk_h), material=PALETTE["trunk"])
    spawn_cone(f"{label}_Canopy", folder, (loc_m[0], loc_m[1], loc_m[2] + trunk_h + canopy_h / 2.0),
               (canopy_r, canopy_r, canopy_h), material=PALETTE["canopy"])


def spawn_building(label, folder, loc_m, size_m, rotation_deg=(0, 0, 0), material=None):
    real_mesh = _pick_kit_asset(BUILDING_ASSET_KIT, label)
    if real_mesh is not None:
        return _spawn_grounded(label, folder, real_mesh, loc_m, size_m, rotation_deg)
    return spawn_block(label, folder, loc_m, size_m, rotation_deg, material=material)


# scan_tree_mountain_assets.py's mesh_scan_results.json came back with
# size_m_xyz=None for every single /Game/Landscaping/* asset -- both bounds
# reads in _mesh_bounds_m fail/return nothing for this pack, so there's no
# runtime way to measure native size before scaling. Backing out native
# height per mesh from the [MtnDiag] log instead (native_height_m = logged
# world_size_m.z / logged scale -- world_size_m is measured AFTER spawn via
# get_actor_bounds, see _spawn_grounded, so it's real regardless of the
# broken asset-level bounds read) gives real, per-mesh numbers, averaged
# across every instance of each mesh seen across two runs (7, 1, and 1
# measurements respectively):
MOUNTAIN_NATIVE_HEIGHT_M = {
    "SM_Iceland_Eroded_Mountain": 353.4,  # avg of 7 measured instances
    "SM_Iceland_Mountain_02": 376.8,      # avg of 2 measured instances
    "SM_Mountain_01": 401.5,              # 1 measured instance (Peak_28 -- the one that swallowed the town before this was known)
}
MOUNTAIN_NATIVE_HEIGHT_FALLBACK_M = 380.0  # any future kit addition not yet in the table above -- default to "large" (the kit is now Iceland-mountain-only) rather than the old "assume ~1m" fallback that caused all of this


def spawn_mountain(label, folder, loc_m, size_m, rotation_deg=(0, 0, 0), material=None):
    real_mesh = _pick_kit_asset(MOUNTAIN_ASSET_KIT, label)
    if real_mesh is not None:
        native_h = MOUNTAIN_NATIVE_HEIGHT_M.get(real_mesh.get_name(), MOUNTAIN_NATIVE_HEIGHT_FALLBACK_M)
        s = max(0.01, size_m[2] / native_h)
        return _spawn_grounded(label, folder, real_mesh, loc_m, size_m, rotation_deg, manual_scale=(s, s, s))
    return spawn_cone(label, folder, loc_m, size_m, rotation_deg, material=material)


def add_tree_cluster(label, folder, center_m, count, spread_m, ground_z=0.0):
    for i in range(count):
        seed = f"{label}_{i}"
        ang = prand(seed + "a") * math.tau
        r = spread_m * (0.25 + 0.75 * prand(seed + "r"))
        dx, dy = math.cos(ang) * r, math.sin(ang) * r
        trunk_h = 2.5 + prand(seed + "t") * 2.0
        canopy_h = 3.0 + prand(seed + "c") * 2.5
        canopy_r = 1.3 + prand(seed + "w") * 1.2
        spawn_tree(f"{label}_{i:02d}", folder,
                   (center_m[0] + dx, center_m[1] + dy, ground_z),
                   trunk_h=trunk_h, canopy_h=canopy_h, canopy_r=canopy_r)


def cleanup_previous_run():
    removed = 0
    for a in actor_subsystem.get_all_level_actors():
        folder = str(a.get_folder_path())
        if folder == ROOT_FOLDER or folder.startswith(ROOT_FOLDER + "/"):
            actor_subsystem.destroy_actor(a)
            removed += 1
    if removed:
        unreal.log(f"[CG Mainland] Cleared {removed} actor(s) from a previous run.")


# ---------------------------------------------------------------------------
# 1. Approach causeway -- gate (X=0) out to the mainland edge (X=-30)
# ---------------------------------------------------------------------------
def build_causeway():
    folder = "Causeway"
    # Widens as it leaves the gate: 16m at the gate, 60m by the time it meets the mainland.
    segments = [
        (-2, -10, 16, 18),
        (-10, -20, 18, 32),
        (-20, -32, 32, 60),
    ]
    for i, (x0, x1, w0, w1) in enumerate(segments):
        length = x0 - x1
        cx = (x0 + x1) / 2.0
        width = (w0 + w1) / 2.0
        spawn_block(f"Causeway_{i:02d}", folder, (cx, 0.0, -0.15), (length, width, 0.3), material=PALETTE["road"])
    # Guard rail blockouts along both edges, cosmetic scale marker more than a real rail.
    for i, x in enumerate(range(-4, -30, -4)):
        for side, y in (("N", 8.0), ("S", -8.0)):
            spawn_block(f"Rail_{side}_{i:02d}", f"{folder}/Rails", (x, y, 0.6), (0.3, 0.3, 1.2), material=PALETTE["road"])


# ---------------------------------------------------------------------------
# 2. Small city -- an organic settlement between the mainland edge and the
#    foothills. A dense street-grid "downtown" right where the causeway
#    lands, then it thins out into a scattered, irregular-edged outskirts
#    that fades in both density and building height as it climbs into the
#    mountain fringe -- no hard rectangle anywhere.
# ---------------------------------------------------------------------------
CITY_X_START = -40.0     # where downtown starts (causeway mouth)
CITY_X_END = -300.0      # far edge of the outskirts scatter -- overlaps the
                          # near mountain layer on purpose so city and peaks blend
DOWNTOWN_DEPTH = 70.0     # how far the dense grid core extends
CITY_Y_HALF_WIDTH = 130.0  # widest extent, right at the causeway mouth
STREET_WIDTH = 8.0  # narrowed from 10 -- frees up more of each city-block cell for
                     # the building footprint itself (Shane: "the buildings look
                     # really thin" -- streets were eating too much of the block)

DOWNTOWN_ROWS = 3
DOWNTOWN_COLS = 6

BUILDING_MATS = ["building_a", "building_b", "building_c", "building_d"]


def city_depth_t(x):
    """0.0 at the causeway mouth, 1.0 at the far edge of the outskirts."""
    return max(0.0, min(1.0, (CITY_X_START - x) / (CITY_X_START - CITY_X_END)))


def city_boundary_y(x):
    """Max |y| the city is allowed to reach at this x. Tapers from the full
    width at the mouth down to a narrow trailing edge in the foothills, with
    a wobble on top so the silhouette is ragged rather than a straight taper."""
    t = city_depth_t(x)
    taper = CITY_Y_HALF_WIDTH * (1.0 - 0.55 * t)
    wobble = 22.0 * math.sin(t * 7.3 + 1.7) + 12.0 * math.sin(t * 13.1 + 4.2) + 8.0 * math.sin(t * 21.0 + 0.4)
    return max(18.0, taper + wobble)


def build_city_ground():
    """Follows city_boundary_y(x) in slices instead of one big rectangle, so
    the ground footprint itself reads as an organic, ragged shape instead of
    a hard-edged square (Shane: "the town base to be less square...flow and
    fade into the mountains and the grass"). Past ~55% depth it starts
    dappling grass patches into the dirt instead of swapping material in one
    hard-edged slice, so the boundary against MountainGroundPad's grass reads
    as a gradient rather than a seam."""
    folder = "City/Ground"
    SLICES = 44
    x0, x1 = CITY_X_START + 8.0, CITY_X_END - 6.0  # slight overrun both ends -- laps under downtown's streets and the fringe trees
    step = (x0 - x1) / SLICES
    for i in range(SLICES):
        cx = x0 - (i + 0.5) * step
        t = city_depth_t(cx)
        half_w = city_boundary_y(cx) + 6.0 + prand(f"cg_{i}_w") * 6.0  # small overrun so buildings/trees never poke past the ground's own edge
        use_grass = t > 0.55 and prand(f"cg_{i}_mat") < (t - 0.55) / 0.45 * 0.7
        mat = PALETTE["mountain_ground"] if use_grass else PALETTE["ground"]
        spawn_block(f"CityGround_{i:02d}", folder, (cx, 0.0, -0.2 - prand(f"cg_{i}_z") * 0.05),
                    (step + 1.5, half_w * 2.0, 0.3), material=mat)


def build_outskirt_roads():
    """Organic winding dirt roads through the outskirts, branching off
    downtown's own street grid -- until now the outskirts had buildings and
    trees but nothing connecting them (Shane: "can we make the town have
    roads?"). Each one is a short random walk (turn a little each step)
    starting along downtown's edge and wandering outward until it nears the
    city's own ragged boundary, so they read as country roads winding out to
    the edge of town rather than another rigid grid."""
    folder = "City/Outskirts/Roads"
    ROAD_WIDTH = 6.0
    STEP = 9.0
    ROAD_COUNT = 6
    for r in range(ROAD_COUNT):
        seed = f"road_{r}"
        x = CITY_X_START - DOWNTOWN_DEPTH
        y = -CITY_Y_HALF_WIDTH + (r + 0.5) / ROAD_COUNT * (CITY_Y_HALF_WIDTH * 2.0)
        heading = 180.0 + (prand(seed + "h0") - 0.5) * 50.0
        steps = int(24 + prand(seed + "len") * 14)
        for i in range(steps):
            if abs(y) > city_boundary_y(x) - 6.0 or x < CITY_X_END + 10.0:
                break
            heading += (prand(f"{seed}_{i}_turn") - 0.5) * 32.0
            rad = math.radians(heading)
            nx = x + math.cos(rad) * STEP
            ny = y + math.sin(rad) * STEP
            mid_x, mid_y = (x + nx) / 2.0, (y + ny) / 2.0
            spawn_block(f"Road_{r:02d}_{i:03d}", folder, (mid_x, mid_y, -0.05),
                        (STEP + 2.0, ROAD_WIDTH, 0.25), rotation_deg=(0, 0, heading), material=PALETTE["road"])
            x, y = nx, ny


def build_mountain_ground():
    # The mountain backdrop (build_mountains, below) sits way outside the
    # city ground pad's footprint -- it was floating over open water before
    # this. This pad picks up well east of where CityGroundPad ends (all the
    # way to WRAP_END_X's neighborhood, so build_mountains()'s horseshoe wrap
    # -- whose two ends curl in to X=-60 -- always has solid ground under it,
    # not just the straight backdrop wall at the arc's middle) and runs out
    # past the farthest peak (near_x/far_x/radius/far-layer-shift below all
    # match build_mountains()'s own constants, plus a margin). Sits slightly
    # lower than CityGroundPad so the overlap never z-fights.
    mountain_far_edge = -560.0 - 80.0 - 140.0  # far_x - far-layer x-shift - max radius
    x0 = -40.0   # east of build_mountains()'s WRAP_END_X=-60 with margin; overlaps CityGroundPad too
    x1 = mountain_far_edge - 40.0
    length = x0 - x1
    cx = (x0 + x1) / 2.0
    half_width = MOUNTAIN_Y_HALF_SPAN + 40.0  # margin past build_mountains()'s own y-spread + jitter/radius
    spawn_block("MountainGroundPad", "Mountains/Ground", (cx, 0.0, -0.25),
                (length, half_width * 2.0, 0.3), material=PALETTE["mountain_ground"])
    return x1  # far edge -- build_shoreline() picks up right past here


# ---------------------------------------------------------------------------
# Shoreline -- a stretch of sand then open water past the far edge of the
# mountain backdrop (Shane: "can we also add a shoreline"), so the mainland
# doesn't just stop dead at the last row of peaks. Sits below MountainGroundPad
# so the beach reads as sloping down to the waterline rather than z-fighting.
#
# Shane: "make the water look more realistic and maybe crash up on shore."
# The water itself is now split into a lighter SHALLOW band right along the
# beach and a darker DEEP band further out (build_water_material.py builds
# both from the same animated-ripple graph, just retinted) -- real water
# reads lighter close to shore where light bounces off the sand below. Right
# on top of the beach/water line, a handful of overlapping strips using
# M_AI_Foam (build_foam_material.py) -- an animated, pulsing whitewater
# material -- stand in for a breaking wave: no real wave sim, but the
# pan+pulse animation reads as surf rolling in and receding, not a static
# foam decal.
# ---------------------------------------------------------------------------
def build_shoreline(mountain_far_x):
    folder = "Shoreline"
    half_width = MOUNTAIN_Y_HALF_SPAN + 40.0  # matches MountainGroundPad's y-coverage
    beach_depth = 60.0
    beach_x0 = mountain_far_x
    beach_x1 = mountain_far_x - beach_depth
    beach_cx = (beach_x0 + beach_x1) / 2.0
    spawn_block("Beach", f"{folder}/Beach", (beach_cx, 0.0, -0.6),
                (beach_depth, half_width * 2.0, 0.4), material=PALETTE["beach"])

    # beach_x1 is the exact waterline -- where the beach block ends and the
    # water begins. Shallow band hugs it; the deep band picks up past that.
    shoreline_x = beach_x1

    shallow_depth = 130.0
    shallow_x0 = shoreline_x
    shallow_x1 = shoreline_x - shallow_depth
    shallow_cx = (shallow_x0 + shallow_x1) / 2.0
    spawn_block("Water_Shallow", f"{folder}/Water", (shallow_cx, 0.0, -1.2),
                (shallow_depth, half_width * 2.0 + 40.0, 0.4), material=PALETTE["water_shallow"])

    deep_depth = 400.0
    deep_x0 = shallow_x1
    deep_x1 = shallow_x1 - deep_depth
    deep_cx = (deep_x0 + deep_x1) / 2.0
    spawn_block("Water_Deep", f"{folder}/Water", (deep_cx, 0.0, -1.25),
                (deep_depth, half_width * 2.0 + 40.0, 0.4), material=PALETTE["water"])

    # Surf strips -- a few overlapping bands straddling the waterline: some
    # sitting on the wet sand, some out over the shallow water, each on its
    # own Material Instance (see get_or_make_foam_instance()) so they pulse
    # out of sync with each other instead of surging in unison. Positioned
    # just above both the beach's and water's top surfaces so they read as a
    # thin floating layer of whitewater rather than fighting either mesh for
    # the same Z.
    surf_z = -0.32
    surf_y = half_width * 2.0 + 10.0
    surf_strips = [
        ("Surf_A", shoreline_x + 9.0, 16.0, 0.0),   # furthest onto the wet sand
        ("Surf_B", shoreline_x + 1.0, 14.0, 1.7),   # right on the waterline
        ("Surf_C", shoreline_x - 10.0, 18.0, 3.4),  # receding out over the shallows
    ]
    for label, cx, depth, phase in surf_strips:
        foam_mat = get_or_make_foam_instance(phase) or PALETTE["water_shallow"]
        spawn_block(label, f"{folder}/Surf", (cx, 0.0, surf_z), (depth, surf_y, 0.12), material=foam_mat)

    unreal.log(f"[CG Mainland] Shoreline: beach + shallow/deep water bands + {len(surf_strips)} pulsing surf "
               f"strip(s) crashing at the X={shoreline_x:.0f} waterline.")


def build_downtown():
    """Dense street grid right at the causeway mouth -- the one part of the
    city allowed to look planned/rectilinear, since real downtowns do."""
    folder = "City/Downtown"
    row_step = DOWNTOWN_DEPTH / DOWNTOWN_ROWS
    col_step = (CITY_Y_HALF_WIDTH * 2.0) / DOWNTOWN_COLS
    x_start = CITY_X_START

    for r in range(DOWNTOWN_ROWS + 1):
        x = x_start - r * row_step
        spawn_block(f"Street_X_{r:02d}", f"{folder}/Streets", (x, 0.0, -0.05),
                    (STREET_WIDTH, CITY_Y_HALF_WIDTH * 2.0, 0.25), material=PALETTE["road"])
    dt_cx = x_start - DOWNTOWN_DEPTH / 2.0
    for c in range(DOWNTOWN_COLS + 1):
        y = -CITY_Y_HALF_WIDTH + c * col_step
        spawn_block(f"Street_Y_{c:02d}", f"{folder}/Streets", (dt_cx, y, -0.05),
                    (DOWNTOWN_DEPTH, STREET_WIDTH, 0.25), material=PALETTE["road"])

    placed = 0
    for r in range(DOWNTOWN_ROWS):
        row_x = x_start - (r + 0.5) * row_step
        for c in range(DOWNTOWN_COLS):
            col_y = -CITY_Y_HALF_WIDTH + (c + 0.5) * col_step
            seed = f"dt_{r}_{c}"
            if prand(seed + "skip") < 0.10:
                continue
            # Margin shrunk from (2.0 + prand*3.0) -- was eating nearly half of an
            # already-narrow row cell, which combined with heights up to ~78m made
            # every building read as a paper-thin slab (Shane: "the buildings look
            # really thin").
            footprint_x = row_step - STREET_WIDTH - (1.0 + prand(seed + "fx") * 2.0)
            footprint_y = col_step - STREET_WIDTH - (1.0 + prand(seed + "fy") * 2.0)
            footprint_x = max(footprint_x, 4.0)
            footprint_y = max(footprint_y, 4.0)
            height = 14.0 + prand(seed + "h") * 40.0  # downtown skews taller than the outskirts
            if prand(seed + "tower") > 0.82:
                height += 24.0
            # Hard cap tied to the narrow (row_step-limited) footprint dimension --
            # without this a handful of buildings still came out as tall, skinny
            # needles no matter how much footprint margin was freed up above.
            height = min(height, footprint_x * 4.5)
            jitter_x = (prand(seed + "jx") - 0.5) * 3.0
            jitter_y = (prand(seed + "jy") - 0.5) * 3.0
            mat = PALETTE[BUILDING_MATS[int(prand(seed + "mat") * len(BUILDING_MATS)) % len(BUILDING_MATS)]]
            spawn_building(f"Downtown_{r:02d}_{c:02d}", f"{folder}/Buildings",
                            (row_x + jitter_x, col_y + jitter_y, height / 2.0),
                            (footprint_x, footprint_y, height), material=mat)
            placed += 1
    unreal.log(f"[CG Mainland] Downtown: {placed} building(s) on a real street grid.")
    return placed


def build_outskirts():
    """Organic scatter from the edge of downtown out to the foothills.
    Density AND building height fall off with depth, and every candidate
    site is rejected if it falls outside the ragged city_boundary_y() edge
    -- that's what keeps the silhouette from reading as a rectangle and
    what makes it thin out into the mountain fringe instead of stopping dead."""
    folder = "City/Outskirts"
    outskirt_x0 = CITY_X_START - DOWNTOWN_DEPTH
    outskirt_x1 = CITY_X_END
    attempts = 260
    placed = 0
    min_spacing = 13.0  # widened alongside the bigger footprints below
    placed_positions = []

    for i in range(attempts):
        seed = f"osk_{i}"
        x = outskirt_x0 + prand(seed + "x") * (outskirt_x1 - outskirt_x0)
        t = city_depth_t(x)
        max_y = city_boundary_y(x)
        y = (prand(seed + "y") * 2.0 - 1.0) * max_y

        # Density fades from ~95% near downtown to ~5% at the far edge.
        density = 0.95 * (1.0 - t) ** 1.4 + 0.05
        if prand(seed + "keep") > density:
            continue

        too_close = False
        for (px, py) in placed_positions:
            if (px - x) ** 2 + (py - y) ** 2 < min_spacing ** 2:
                too_close = True
                break
        if too_close:
            continue
        placed_positions.append((x, y))

        # Widened base range (was 5.0 + prand*6.0, i.e. 5-11m) -- too narrow against
        # heights up to ~40m, same "thin slab" problem as downtown (Shane: "the
        # buildings look really thin").
        footprint = 9.0 + prand(seed + "fp") * 9.0
        aspect = 0.7 + prand(seed + "asp") * 0.6
        height = (18.0 * (1.0 - t) + 5.0) + prand(seed + "h") * (14.0 * (1.0 - t) + 4.0)
        height = min(height, footprint * min(1.0, aspect) * 4.0)  # cap tied to the narrower footprint axis
        rot = prand(seed + "rot") * 90.0
        mat = PALETTE[BUILDING_MATS[int(prand(seed + "mat") * len(BUILDING_MATS)) % len(BUILDING_MATS)]]
        spawn_building(f"Outskirt_{i:03d}", folder, (x, y, height / 2.0),
                        (footprint, footprint * aspect, height),
                        rotation_deg=(0, 0, rot), material=mat)
        placed += 1

    unreal.log(f"[CG Mainland] Outskirts: {placed} building(s) scattered across a ragged, thinning edge.")
    return placed_positions


# ---------------------------------------------------------------------------
# 3. Mountain backdrop -- arc of peaks beyond the city. Stays a straight
#    north-south wall directly west of downtown at its middle (t=0.5), same
#    as before, but the two ends (t near 0 or 1) curl forward toward +X
#    (WRAP_END_X) instead of continuing straight north/south -- a horseshoe
#    that wraps around the city's flanks and reaches back alongside
#    CarrowGateGarrison to the north and south (Shane: "move the mountains so
#    it partially wraps around the city and the Carrowgate Garrison").
#    WRAP_END_X stays comfortably west of X=-15 -- the boundary the rest of
#    this script (and the coordinate-frame note at the top of the file) relies
#    on to guarantee nothing here ever collides with the garrison's own
#    GateApproach/WestConnector pads at X=-10..+55.
# ---------------------------------------------------------------------------
# Shared with build_mountain_wall() below, so the invisible blocker follows
# exactly the same curve as the visible peaks instead of a second hand-tuned
# approximation that could drift out of alignment with it.
MOUNTAIN_NEAR_X = -280.0
MOUNTAIN_FAR_X = -560.0
MOUNTAIN_WRAP_END_X = -60.0    # how far forward (east, toward the garrison) the two arc ends curl
MOUNTAIN_Y_HALF_SPAN = 900.0   # widened again (Shane: "add more all the way to the edge on either side") -- pushed out to the edges of the mainland's own ground pad so there's no open flank a player could walk around the range through


def _mountain_arc_xy(t):
    """The horseshoe centerline build_mountains() and build_mountain_wall()
    both place things along: 0.0 at the south end, 1.0 at the north end."""
    x_wall = MOUNTAIN_NEAR_X + (MOUNTAIN_FAR_X - MOUNTAIN_NEAR_X) * t
    curl_t = abs(2.0 * t - 1.0) ** 2  # 0 at the middle (t=0.5), 1 at the two far ends (t=0 or 1)
    x = x_wall + curl_t * (MOUNTAIN_WRAP_END_X - x_wall)
    y = -MOUNTAIN_Y_HALF_SPAN + t * (2.0 * MOUNTAIN_Y_HALF_SPAN)
    return x, y


def build_mountains():
    # count=30 across a 1120m arc spaces peak CENTERS ~38.6m apart, but radius
    # (8-25m, so footprint diameter only 16-50m) plus up to +-35m of y jitter
    # meant neighboring peaks' visible silhouettes often didn't overlap at all
    # -- open sky between them (Shane: "still some large gaps can we fill
    # those" -- the collision wall was already closing them to a player, but
    # the visible peaks themselves had real holes). Denser peaks (count
    # roughly doubled, spacing ~19m), a bigger radius floor so a peak's own
    # footprint diameter comfortably exceeds that spacing even at minimum
    # roll, and less y jitter (kept below half the new spacing so it staggers
    # peaks without reopening the gap it's meant to close) -- now neighboring
    # footprints overlap by construction instead of by luck.
    folder = "Mountains"
    count = 145  # scaled up with MOUNTAIN_Y_HALF_SPAN's widened span so spacing stays ~12.5m, same density as before
    for i in range(count):
        seed = f"mtn_{i}"
        t = i / float(count - 1)
        # Small per-peak jitter on top of the shared centerline -- x gets its own
        # jitter (perpendicular-ish to the arc, deepens/shallows individual peaks),
        # y gets a smaller one (staggers peaks along the arc) -- same visual
        # variety the old single-formula version had.
        x, y = _mountain_arc_xy(t)
        x += (prand(seed + "xz") - 0.5) * 0.15 * (MOUNTAIN_FAR_X - MOUNTAIN_NEAR_X)
        y += (prand(seed + "y") - 0.5) * 10.0  # scaled down from the count=58 pass -- stays under half the new, tighter spacing
        height = 15.0 + prand(seed + "h") * 30.0
        radius = 16.0 + prand(seed + "r") * 24.0
        rot = prand(seed + "rot") * 360.0
        far_layer = prand(seed + "far") > 0.5
        mat = PALETTE["mountain_far"] if far_layer else PALETTE["mountain"]
        if far_layer:
            height *= 1.3
            x -= 80.0
        spawn_mountain(f"Peak_{i:02d}", folder, (x, y, height / 2.0), (radius, radius, height),
                        rotation_deg=(0, 0, rot), material=mat)


# ---------------------------------------------------------------------------
# Invisible blocking wall along the same horseshoe -- the visible peaks above
# are individual meshes with gaps between them (Shane: "fill in the gaps
# between the mountains, I dont want players to be able to walk past the
# mountain range"). Rather than trying to pack meshes tightly enough to
# guarantee no seam ever lines up, this drops a continuous chain of plain,
# invisible collision blocks along the exact same centerline, dense enough
# that consecutive blocks always overlap -- the visible peaks stay purely
# decorative, this is what actually stops a player from walking through.
# ---------------------------------------------------------------------------
def build_mountain_wall():
    folder = "Mountains/Wall"
    segments = 145  # scaled up with MOUNTAIN_Y_HALF_SPAN alongside the visible peak count above -- comfortably overlapping given each block's own width below
    seg_width = (2.0 * MOUNTAIN_Y_HALF_SPAN) / (segments - 1)
    wall_height = 260.0
    wall_depth = 70.0
    for i in range(segments):
        t = i / float(segments - 1)
        x, y = _mountain_arc_xy(t)
        actor = spawn_block(f"Wall_{i:03d}", folder, (x, y, wall_height / 2.0 - 20.0),
                             (wall_depth, seg_width * 1.4, wall_height))
        actor.static_mesh_component.set_visibility(False)
    unreal.log(f"[CG Mainland] Mountain wall: {segments} invisible blocking segment(s) closing the gaps between peaks.")


# ---------------------------------------------------------------------------
# 4. Trees -- along the causeway, filling the gaps the outskirts scatter
#    left behind, and a dense foothill fringe that follows the SAME ragged
#    boundary as the city so the treeline reads as one continuous edge with
#    the buildings, not a separate rectangle of its own.
# ---------------------------------------------------------------------------
def build_trees(outskirt_positions, keepout=None):
    """keepout: optional list of (x, y, radius) -- ground the Belt pass below
    should leave alone (e.g. build_helipads()'s pads, so trees don't spawn
    on top of an extraction LZ)."""
    keepout = keepout or []
    folder = "Trees"
    # Causeway edges
    for i, x in enumerate(range(-8, -30, -6)):
        add_tree_cluster(f"Causeway_{i:02d}_N", f"{folder}/Causeway", (x, 14.0, 0.0), count=3, spread_m=4.0)
        add_tree_cluster(f"Causeway_{i:02d}_S", f"{folder}/Causeway", (x, -14.0, 0.0), count=3, spread_m=4.0)

    # Small clusters scattered through the outskirts wherever a candidate site
    # WASN'T claimed by a building -- reuses the same site-sampling pass so
    # trees naturally fill the gaps between houses instead of a separate grid.
    # Shane: "make the forest significantly thicker" -- more candidate sites,
    # a much higher keep-rate at every depth, and bigger clusters per site.
    outskirt_x0 = CITY_X_START - DOWNTOWN_DEPTH
    outskirt_x1 = CITY_X_END
    gap_count = 0
    for i in range(220):
        seed = f"gap_{i}"
        x = outskirt_x0 + prand(seed + "x") * (outskirt_x1 - outskirt_x0)
        t = city_depth_t(x)
        max_y = city_boundary_y(x)
        y = (prand(seed + "y") * 2.0 - 1.0) * max_y
        too_close = any((px - x) ** 2 + (py - y) ** 2 < 8.0 ** 2 for (px, py) in outskirt_positions)
        if too_close:
            continue
        # Trees get MORE likely as depth increases -- inverse of the building density
        # falloff -- so the far edge of the city is mostly trees with a few houses,
        # which is what actually reads as "fading into the mountains." Base rate
        # and slope both raised so even the shallow (near-downtown) end reads as
        # forest, not scattered saplings.
        if prand(seed + "keep") > (0.35 + 0.85 * t):
            continue
        add_tree_cluster(f"Gap_{i:03d}", f"{folder}/Outskirts", (x, y, 0.0),
                          count=int(5 + prand(seed + "cnt") * 7), spread_m=6.0 + 6.0 * t)
        gap_count += 1

    # Foothill fringe -- extends past the city's far edge, following the same
    # ragged city_boundary_y() shape (scaled up a bit) so trees and mountains
    # interleave instead of meeting at a hard line. More, bigger, tighter-
    # packed clusters for a proper wall of foliage against the foothills.
    fringe_x0, fringe_x1 = CITY_X_END - 30.0, -300.0
    fringe_count = 30
    for i in range(fringe_count):
        seed = f"fringe_{i}"
        x = fringe_x0 + prand(seed + "x") * (fringe_x1 - fringe_x0)
        spread_y = city_boundary_y(min(x, CITY_X_END)) * 1.6 + 60.0
        y = (prand(seed + "y") * 2.0 - 1.0) * spread_y
        add_tree_cluster(f"Fringe_{i:02d}", f"{folder}/Fringe", (x, y, 0.0), count=14, spread_m=18.0)

    # Belt fill -- Shane: "more trees...in the empty area between the town and
    # the mountains." build_mountains()'s horseshoe wrap pulls its two arc
    # ends in toward the garrison, which opened up flat ground north and south
    # of downtown that the fringe pass above never reaches (it's scoped to the
    # city's own ragged city_boundary_y() edge). This pass ignores that
    # boundary entirely and just scatters across the same wide Y range the
    # mountain wrap uses, skipping only ground already inside downtown/
    # outskirts' own footprint and each keepout's own radius (see build_helipads()
    # -- the working helipad carries a wide clearing margin here, the broken one
    # doesn't, so the forest is free to crowd right up against it).
    belt_x0, belt_x1 = CITY_X_START - 20.0, -290.0
    belt_count = 0
    for i in range(220):
        seed = f"belt_{i}"
        x = belt_x0 + prand(seed + "x") * (belt_x1 - belt_x0)
        y = (prand(seed + "y") * 2.0 - 1.0) * MOUNTAIN_Y_HALF_SPAN
        if abs(y) < city_boundary_y(x) + 15.0:
            continue  # inside (or right at the edge of) downtown/outskirts -- leave it to those passes
        if any((x - kx) ** 2 + (y - ky) ** 2 < (kr + 10.0) ** 2 for (kx, ky, kr) in keepout):
            continue  # clear of a helipad's own footprint + approach margin
        add_tree_cluster(f"Belt_{i:03d}", f"{folder}/Belt", (x, y, 0.0),
                          count=int(6 + prand(seed + "cnt") * 9), spread_m=10.0 + prand(seed + "sp") * 10.0)
        belt_count += 1

    # Understory -- a second, denser layer interleaved between the passes
    # above using its own independent sampling, so the canopy reads as
    # continuous forest instead of visibly-separate clusters with sky showing
    # between them. Smaller, tighter clusters filling whatever gaps are left.
    under_count = 0
    for i in range(200):
        seed = f"under_{i}"
        x = belt_x0 + prand(seed + "x") * (belt_x1 - belt_x0)
        y = (prand(seed + "y") * 2.0 - 1.0) * MOUNTAIN_Y_HALF_SPAN
        if abs(y) < city_boundary_y(x) + 10.0:
            continue
        if any((x - kx) ** 2 + (y - ky) ** 2 < (kr + 10.0) ** 2 for (kx, ky, kr) in keepout):
            continue
        add_tree_cluster(f"Understory_{i:03d}", f"{folder}/Understory", (x, y, 0.0),
                          count=int(3 + prand(seed + "cnt") * 4), spread_m=5.0 + prand(seed + "sp") * 5.0)
        under_count += 1

    unreal.log(f"[CG Mainland] Trees: causeway + {gap_count} outskirt gap cluster(s) + {fringe_count} fringe cluster(s) "
               f"+ {belt_count} belt cluster(s) + {under_count} understory cluster(s) -- significantly thicker forest, "
               f"with a clearing kept around the working helipad.")


# ---------------------------------------------------------------------------
# Helipad(s) -- Shane: "add a helipad in some of the empty space on either
# side of the town...for the end of the first mission for extraction." Then:
# "put the helipads deeper in the forest and make them bigger, also make one
# of them old and broken so its unusable."
#
# Pushed well past downtown/the outskirts scatter into the tree belt (still
# comfortably short of the mountain wall -- see build_helipads()'s hp_x
# comment for the margin math), and made larger. One of the two (south) is
# now built "broken": cracked/tilted pad surface, a faded and partially
# missing H, most of the corner lights knocked out, tumbled debris chunks,
# and scrub breaking up through the concrete -- reads as abandoned/unusable
# without needing a placed prop to explain it.
#
# NOTE ON THE MODEL: Shane authorized generating a real damaged-helipad mesh
# via Tripo3D for this if needed (same generate -> download -> FBX-import ->
# auto-swap pattern as import_mainland_buildings.py). The Chrome browser
# bridge wasn't connected when this pass ran, so the broken look below is
# built from the same primitive kit as everything else in this script
# instead. If/when Tripo3D is reachable, generate SM_Helipad_Broken, write an
# import script following import_mainland_buildings.py's pattern, and this
# can wire it in through the usual ASSET_ROOT kit-swap so a real mesh
# replaces the primitive version automatically on the next run.
# ---------------------------------------------------------------------------
def build_helipad(label, folder, center_m, radius=13.0, broken=False):
    cx, cy = center_m[0], center_m[1]
    pad_h = 0.3
    pad_mat = PALETTE["helipad_broken"] if broken else PALETTE["helipad"]
    # Slight warp on the broken pad -- a sunken/heaved foundation rather than
    # a flat maintained slab.
    pad_rot = (3.5, -2.5, 0) if broken else (0, 0, 0)
    spawn_cylinder(f"{label}_Pad", folder, (cx, cy, pad_h / 2.0), (radius, radius, pad_h),
                   rotation_deg=pad_rot, material=pad_mat)

    top_z = pad_h + 0.03
    bar_w = radius * 0.22
    bar_len = radius * 1.2
    gap = radius * 0.7
    marking_mat = PALETTE["helipad_rust"] if broken else PALETTE["helipad_marking"]
    if broken:
        # Faded H, one leg gone entirely and the survivors knocked askew.
        spawn_block(f"{label}_H_L", folder, (cx - gap / 2.0, cy, top_z), (bar_w, bar_len * 0.55, 0.05),
                    rotation_deg=(0, 0, 9.0), material=marking_mat)
        spawn_block(f"{label}_H_Bar", folder, (cx, cy, top_z), (gap + bar_w, bar_w, 0.05),
                    rotation_deg=(0, 0, -5.0), material=marking_mat)
    else:
        spawn_block(f"{label}_H_L", folder, (cx - gap / 2.0, cy, top_z), (bar_w, bar_len, 0.05), material=marking_mat)
        spawn_block(f"{label}_H_R", folder, (cx + gap / 2.0, cy, top_z), (bar_w, bar_len, 0.05), material=marking_mat)
        spawn_block(f"{label}_H_Bar", folder, (cx, cy, top_z), (gap + bar_w, bar_w, 0.05), material=marking_mat)

    light_mat = PALETTE["helipad_rust"] if broken else PALETTE["helipad_light"]
    for i, ang in enumerate((45.0, 135.0, 225.0, 315.0)):
        if broken and prand(f"{label}_lightgone_{i}") > 0.35:
            continue  # most corner lights long dead or knocked off entirely
        rad = math.radians(ang)
        lx = cx + math.cos(rad) * radius * 0.85
        ly = cy + math.sin(rad) * radius * 0.85
        spawn_block(f"{label}_Light_{i}", folder, (lx, ly, pad_h + 0.15), (0.6, 0.6, 0.3), material=light_mat)

    if not broken:
        return

    # Crack lines -- thin dark slabs raking across the pad at random angles.
    for i in range(5):
        seed = f"{label}_crack_{i}"
        ang = prand(seed + "a") * 360.0
        offset = (prand(seed + "o") - 0.5) * radius * 1.1
        length = radius * (0.7 + prand(seed + "l") * 0.6)
        rad = math.radians(ang)
        ox, oy = math.cos(rad) * offset, math.sin(rad) * offset
        spawn_block(f"{label}_Crack_{i}", folder, (cx + ox, cy + oy, pad_h + 0.02), (0.15, length, 0.04),
                    rotation_deg=(0, 0, ang), material=PALETTE["helipad_broken"])

    # Tumbled debris chunks scattered around the rim, each at its own tilt.
    for i in range(7):
        seed = f"{label}_debris_{i}"
        ang = prand(seed + "a") * 360.0
        dist = radius * (0.75 + prand(seed + "d") * 0.5)
        rad = math.radians(ang)
        dx, dy = math.cos(rad) * dist, math.sin(rad) * dist
        size = 0.8 + prand(seed + "s") * 1.4
        spawn_block(f"{label}_Debris_{i}", folder, (cx + dx, cy + dy, size / 2.0),
                    (size, size * (0.6 + prand(seed + "s2") * 0.8), size * 0.5),
                    rotation_deg=(prand(seed + "rx") * 40.0 - 20.0, prand(seed + "ry") * 40.0 - 20.0, prand(seed + "rz") * 360.0),
                    material=PALETTE["debris"])

    # Scrub breaking up through the cracked concrete -- the clearest "nobody's
    # flown here in years" cue, reusing the same tree-cluster helper as
    # everywhere else in this script.
    add_tree_cluster(f"{label}_Overgrowth", folder, (cx, cy, pad_h), count=6, spread_m=radius * 0.9)


def build_helipads():
    folder = "Helipads"
    # Pulled deep into the tree belt/forest (Shane: "put the helipads deeper
    # in the forest") -- well past the outskirts scatter (which ends around
    # CITY_X_END) and downtown's own ragged edge, but still with a wide
    # margin of open forest floor before the mountain wall: at this Y, the
    # horseshoe's near edge sits roughly 190m further west, so there's no
    # risk of clipping the collision wall or spawning inside a peak.
    hp_x = CITY_X_START - DOWNTOWN_DEPTH - 130.0
    radius = 22.0  # bigger landing footprint (Shane: "make them bigger")
    # Shane: "leave a clearing around the working helipad" -- now that the
    # forest pass is much denser, the working pad needs an explicit wide
    # keepout or the Belt/Understory passes would happily grow right up to
    # (and onto) its edge. The broken pad gets none of that extra margin --
    # only its own footprint is kept clear (see build_helipad's own
    # overgrowth cluster) -- so the thicker forest is left free to crowd in
    # and swallow it, reinforcing that it's abandoned.
    CLEARING_MARGIN = 45.0
    pads = [
        ("Helipad_North", (hp_x, CITY_Y_HALF_WIDTH + 90.0), False),
        # Shane: "make one of them old and broken so its unusable."
        ("Helipad_South", (hp_x, -(CITY_Y_HALF_WIDTH + 90.0)), True),
    ]
    for label, center, broken in pads:
        build_helipad(label, folder, center, radius=radius, broken=broken)
    unreal.log(f"[CG Mainland] Helipads: {len(pads)} extraction pad(s) deep in the tree belt north and south of "
               f"downtown (south pad built broken/unusable, cleared only to its own footprint; north pad kept a "
               f"{CLEARING_MARGIN:.0f}m clearing).")
    return [(c[0], c[1], radius if broken else radius + CLEARING_MARGIN) for _, c, broken in pads]


def run():
    cleanup_previous_run()
    build_palette()
    build_causeway()
    build_city_ground()
    mountain_far_x = build_mountain_ground()
    build_downtown()
    outskirt_positions = build_outskirts()
    build_outskirt_roads()
    build_mountains()
    build_mountain_wall()
    helipad_keepouts = build_helipads()
    build_trees(outskirt_positions, keepout=helipad_keepouts)
    build_shoreline(mountain_far_x)
    unreal.log(
        "[CG Mainland] Done. Causeway + downtown grid + an organic, ragged-edged outskirts scatter that "
        "thins into the foothill treeline + mountain backdrop, all west of the Main Gate under the "
        "'CG Mainland' Outliner folder. Placeholders auto-swap to real meshes the moment matching assets "
        f"exist under {ASSET_ROOT} (see BUILDING_ASSET_KIT / TREE_ASSET_KIT / MOUNTAIN_ASSET_KIT at the top "
        "of this script) -- just re-run after importing each one. Remember to save the level (Ctrl+S) once "
        "you're happy with the layout."
    )


run()
