"""
BUILD A BEACH/SHORELINE RING AROUND THE GARRISON'S WATER EDGE
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Water_Placeholder (build_carrowgate_garrison.py) is one giant flat ocean
plane sitting under the whole complex -- every ground segment currently
just drops straight down into it, a sheer ~4.4m cliff on every side, no
beach, no surf. Shane: "make it so where the water meets the land [is] a
beach with water flowing up and down shore."

The mainland's west shoreline (build_shoreline() in this same file)
already solved this exact problem with a proven recipe: a sand beach band,
a lighter shallow-water band, a darker deep-water band further out, and a
few overlapping M_AI_Foam strips (each its own phase-offset Material
Instance via get_or_make_foam_instance so they pulse out of sync) sitting
right at the waterline to read as surf rolling in and out. All of those
materials (M_AI_Water, M_AI_Water_Shallow, M_AI_Foam, MI_Landmass_Beach)
already exist on disk -- this reuses them as-is, no new material work.

THE FIX
-------
The garrison's landmass isn't one rectangle, it's 9 overlapping ground
segments tracing an irregular arrow shape (GROUND_SEGMENTS, same list as
build_carrowgate_garrison.py). Rather than compute an exact outward-offset
polygon, this uses the same trick that list already relies on: expand each
segment's own footprint outward by a margin and let the expanded boxes
overlap each other and the ground segments themselves -- any part of an
expanded box that lands under solid ground (Z=0 down to -6) is simply
hidden by it, no visual artifact, so approximate per-segment rings still
add up to a continuous ring around the whole irregular coastline.

Per segment:
  - Beach ring: sand box (MI_Landmass_Beach), expanded by BEACH_MARGIN_M,
    given real depth (top just under the ground's own edge, bottom reaching
    down near the waterline) so it reads as a sloped bank, not a floating
    sliver over a void.
  - Shallow-water ring: thin band (M_AI_Water_Shallow) expanded further out,
    sitting just above Water_Placeholder's own surface so the existing deep
    ocean shows through everywhere past it.
  - Surf ring: a thin M_AI_Foam strip over the shallow band, alternating
    phase offsets per segment so neighboring stretches of coast don't pulse
    in lockstep -- reads as water lapping the shore instead of a static
    decal.

Safe to re-run -- clears any previously-spawned GarrisonBeach_*/
GarrisonShallow_*/GarrisonSurf_* actors first.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/build_garrison_shoreline.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

M = 100.0
ROOT_FOLDER = "IronBreach/Shoreline"
MATERIAL_DIR = "/Game/LevelPrototyping/AITextures/Landmass"

CUBE_MESH = AL.load_asset("/Engine/BasicShapes/Cube.Cube")
CHAMFER_MESH = AL.load_asset("/Game/LevelPrototyping/Meshes/SM_ChamferCube.SM_ChamferCube") or CUBE_MESH

BEACH_MATERIAL_PATH = f"{MATERIAL_DIR}/MI_Landmass_Beach"
SHALLOW_WATER_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Water_Shallow.M_AI_Water_Shallow"
FOAM_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Foam.M_AI_Foam"

# Same list as GROUND_SEGMENTS in build_carrowgate_garrison.py.
GROUND_SEGMENTS = [
    ("GateApproach", (2.5, 0.0), (25, 20)),
    ("WestConnector", (25.0, 2.0), (30, 20)),
    ("NW_Yard", (47.5, -2.5), (55, 35)),
    ("NorthSpur_WatchTower", (57.5, 33.5), (35, 43)),
    ("CentralBody_Barracks", (65.0, -15.0), (50, 60)),
    ("EastWing_MessHallArmory", (100.0, -2.5), (50, 55)),
    ("SouthWing_Command", (72.5, -57.5), (35, 35)),
    ("SE_CoastalReach_Helipad", (125.0, -37.5), (50, 45)),
    ("SouthTaper_CivicRoute", (95.0, -77.5), (40, 35)),
]

BEACH_MARGIN_M = 12.0
SHALLOW_MARGIN_M = 18.0

BEACH_TOP_Z = -0.5
BEACH_BOTTOM_Z = -4.35
SHALLOW_TOP_Z = -4.3
SHALLOW_BOTTOM_Z = -4.5
SURF_Z = -4.25
SURF_HEIGHT_M = 0.12
SURF_INSET_M = 3.0   # keep the foam strip inside the shallow ring's own edge


def log(msg):
    print("[GarrisonShoreline] %s" % msg)


def clear_previous(all_actors):
    removed = 0
    for a in list(all_actors):
        label = a.get_actor_label()
        if label.startswith(("GarrisonBeach_", "GarrisonShallow_", "GarrisonSurf_")):
            actor_subsystem.destroy_actor(a)
            removed += 1
    if removed:
        log("Removed %d previously-spawned shoreline actor(s)." % removed)


def spawn_box(label, folder, loc_m, size_m, material, mesh):
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(0, 0, 0))
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(mesh)
    mesh_comp.set_world_scale3d(unreal.Vector(size_m[0], size_m[1], size_m[2]))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    return actor


def get_or_make_foam_instance(phase_seconds, foam_parent):
    name = "MI_AI_Foam_P%03d" % int(phase_seconds * 10)
    path = f"{MATERIAL_DIR}/{name}"
    existing = AL.load_asset(path)
    if existing is not None:
        return existing
    factory = unreal.MaterialInstanceConstantFactoryNew()
    instance = asset_tools.create_asset(name, MATERIAL_DIR, unreal.MaterialInstanceConstant, factory)
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, foam_parent)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "PhaseOffset", phase_seconds)
    AL.save_asset(path)
    return instance


def run():
    beach_mat = AL.load_asset(BEACH_MATERIAL_PATH)
    shallow_mat = AL.load_asset(SHALLOW_WATER_MATERIAL_PATH)
    foam_parent = AL.load_asset(FOAM_MATERIAL_PATH)

    if beach_mat is None or shallow_mat is None:
        log("ABORTED -- beach or shallow-water material missing (%s / %s)." % (
            BEACH_MATERIAL_PATH, SHALLOW_WATER_MATERIAL_PATH))
        return
    if foam_parent is None:
        log("WARNING -- %s not found, surf strips will fall back to plain shallow water." % FOAM_MATERIAL_PATH)

    all_actors = actor_subsystem.get_all_level_actors()
    clear_previous(all_actors)

    beach_h = BEACH_TOP_Z - BEACH_BOTTOM_Z
    beach_cz = (BEACH_TOP_Z + BEACH_BOTTOM_Z) / 2.0
    shallow_h = SHALLOW_TOP_Z - SHALLOW_BOTTOM_Z
    shallow_cz = (SHALLOW_TOP_Z + SHALLOW_BOTTOM_Z) / 2.0

    for i, (seg_name, (gx, gy), (gsx, gsy)) in enumerate(GROUND_SEGMENTS):
        spawn_box(f"GarrisonBeach_{seg_name}", "Beach",
                  (gx, gy, beach_cz),
                  (gsx + 2.0 * BEACH_MARGIN_M, gsy + 2.0 * BEACH_MARGIN_M, beach_h),
                  beach_mat, CHAMFER_MESH)

        shallow_sx = gsx + 2.0 * (BEACH_MARGIN_M + SHALLOW_MARGIN_M)
        shallow_sy = gsy + 2.0 * (BEACH_MARGIN_M + SHALLOW_MARGIN_M)
        spawn_box(f"GarrisonShallow_{seg_name}", "Water",
                  (gx, gy, shallow_cz),
                  (shallow_sx, shallow_sy, shallow_h),
                  shallow_mat, CUBE_MESH)

        phase = float((i * 7) % 40) * 0.5  # spread phases 0..~19.5s so rings don't sync
        foam_mat = get_or_make_foam_instance(phase, foam_parent) if foam_parent else None
        surf_sx = shallow_sx - 2.0 * SURF_INSET_M
        surf_sy = shallow_sy - 2.0 * SURF_INSET_M
        spawn_box(f"GarrisonSurf_{seg_name}", "Surf",
                  (gx, gy, SURF_Z),
                  (max(surf_sx, gsx + 2.0), max(surf_sy, gsy + 2.0), SURF_HEIGHT_M),
                  foam_mat or shallow_mat, CUBE_MESH)

    log("Built shoreline ring (beach + shallow water + pulsing surf) around %d ground segment(s). "
        "Save and check the viewport / re-run PIE." % len(GROUND_SEGMENTS))


run()
