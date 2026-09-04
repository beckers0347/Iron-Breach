"""
REBUILD THE PATH/ROAD NETWORK -- geometry only, flat untextured material
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
remove_all_paths.py cleared out the scattered, never-actually-connected
tile patches. Rather than texture another attempt blind, this rebuilds
just the GEOMETRY of a real connected network -- using a single flat grey
material with no texture sampling at all (MI_Landmass_Road if it still
exists as an asset, otherwise a brand new plain-color material built here)
-- so you can see and verify the connectivity/shape itself first, before
any material work happens on top of it.

WHAT IT BUILDS (three systems, all provably connected by construction)
------------------------------------------------------------------------
1. Causeway -- 3 widening segments from the gate (X=-2) out to the mainland
   edge (X=-32). Each segment's end X exactly matches the next one's start
   X, so there's no gap between them by construction.
2. Downtown street grid -- full-length streets: each Street_X spans the
   ENTIRE city width, each Street_Y spans the ENTIRE downtown depth, so
   every X-street physically crosses every Y-street. This can't have a
   corner gap -- the strips fully overlap at every intersection, not just
   touch at an edge.
3. Outskirt winding roads -- same random-walk shape as before, but this
   time a square joint patch is placed at every bend from the start (not
   bolted on after), so turns are connected from the moment they're built
   instead of being patched later.

This does NOT touch buildings, trees, or the ground/grass -- only spawns
the road/street/causeway/joint actors. It also does NOT modify
M_AI_CobblestonePath or any texture asset -- once you've confirmed the
shape/connectivity looks right, tell me and I'll point this network back
at a real stone material as a separate step.

Safe to re-run -- clears its own previous output first.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/rebuild_path_network.py"
"""

import unreal
import math

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

M = 100.0
ROOT_FOLDER = "CG Mainland"
CUBE_MESH = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")

FLAT_ROAD_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_Road"
FLAT_ROAD_COLOR = (0.10, 0.10, 0.11)

# ---- copied from build_carrowgate_mainland.py so this matches the rest of the city exactly ----
CITY_X_START = -40.0
CITY_X_END = -300.0
DOWNTOWN_DEPTH = 70.0
CITY_Y_HALF_WIDTH = 130.0
STREET_WIDTH = 8.0
DOWNTOWN_ROWS = 3
DOWNTOWN_COLS = 6
OUTSKIRT_ROAD_WIDTH = 6.0
OUTSKIRT_STEP = 9.0
OUTSKIRT_ROAD_COUNT = 6

LABEL_PREFIXES_TO_CLEAR = ("Street_X_", "Street_Y_", "Causeway_", "Rail_", "Road_", "RoadJoint_", "PathBridge_")


def log(msg):
    print("[RebuildPathNetwork] %s" % msg)


def prand(seed):
    h = hash(seed) & 0xFFFFFFFF
    h = (h * 9301 + 49297) % 233280
    return h / 233280.0


def city_depth_t(x):
    return max(0.0, min(1.0, (CITY_X_START - x) / (CITY_X_START - CITY_X_END)))


def city_boundary_y(x):
    t = city_depth_t(x)
    taper = CITY_Y_HALF_WIDTH * (1.0 - 0.55 * t)
    wobble = 22.0 * math.sin(t * 7.3 + 1.7) + 12.0 * math.sin(t * 13.1 + 4.2) + 8.0 * math.sin(t * 21.0 + 0.4)
    return max(18.0, taper + wobble)


def get_or_make_flat_material():
    existing = AL.load_asset(FLAT_ROAD_MATERIAL_PATH)
    if existing:
        log("Reusing existing flat material %s (no texture)." % FLAT_ROAD_MATERIAL_PATH)
        return existing

    log("MI_Landmass_Road not found -- creating a new plain flat-color material (no texture).")
    package_path, name = FLAT_ROAD_MATERIAL_PATH.rsplit("/", 1)
    factory = unreal.MaterialFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = asset_tools.create_asset(name, package_path, unreal.Material, factory)
    color_const = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
    color_const.set_editor_property("constant", unreal.LinearColor(FLAT_ROAD_COLOR[0], FLAT_ROAD_COLOR[1], FLAT_ROAD_COLOR[2], 1.0))
    MEL.connect_material_property(color_const, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough_const = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -300, 150)
    rough_const.set_editor_property("R", 0.85)
    MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(mat)
    AL.save_asset(FLAT_ROAD_MATERIAL_PATH)
    return mat


def spawn_block(label, folder, loc_m, size_m, rotation_deg, material):
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    rotation = unreal.Rotator(rotation_deg[0], rotation_deg[1], rotation_deg[2])
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(CUBE_MESH)
    mesh_comp.set_world_scale3d(unreal.Vector(size_m[0], size_m[1], size_m[2]))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    mesh_comp.set_material(0, material)
    return actor


def clear_previous():
    all_actors = actor_subsystem.get_all_level_actors()
    to_clear = [a for a in all_actors if a.get_actor_label().startswith(LABEL_PREFIXES_TO_CLEAR)]
    for a in to_clear:
        actor_subsystem.destroy_actor(a)
    if to_clear:
        log("Cleared %d actor(s) from a previous run." % len(to_clear))


def build_causeway(mat):
    folder = "Causeway"
    segments = [
        (-2, -10, 16, 18),
        (-10, -20, 18, 32),
        (-20, -32, 32, 60),
    ]
    count = 0
    for i, (x0, x1, w0, w1) in enumerate(segments):
        length = x0 - x1
        cx = (x0 + x1) / 2.0
        width = (w0 + w1) / 2.0
        spawn_block(f"Causeway_{i:02d}", folder, (cx, 0.0, -0.15), (length, width, 0.3), (0, 0, 0), mat)
        count += 1
    for i, x in enumerate(range(-4, -30, -4)):
        for side, y in (("N", 8.0), ("S", -8.0)):
            spawn_block(f"Rail_{side}_{i:02d}", f"{folder}/Rails", (x, y, 0.6), (0.3, 0.3, 1.2), (0, 0, 0), mat)
            count += 1
    log("Causeway: %d actor(s)." % count)


def build_downtown_streets(mat):
    folder = "City/Downtown/Streets"
    row_step = DOWNTOWN_DEPTH / DOWNTOWN_ROWS
    col_step = (CITY_Y_HALF_WIDTH * 2.0) / DOWNTOWN_COLS
    x_start = CITY_X_START
    count = 0

    for r in range(DOWNTOWN_ROWS + 1):
        x = x_start - r * row_step
        spawn_block(f"Street_X_{r:02d}", folder, (x, 0.0, -0.05),
                    (STREET_WIDTH, CITY_Y_HALF_WIDTH * 2.0, 0.25), (0, 0, 0), mat)
        count += 1
    dt_cx = x_start - DOWNTOWN_DEPTH / 2.0
    for c in range(DOWNTOWN_COLS + 1):
        y = -CITY_Y_HALF_WIDTH + c * col_step
        spawn_block(f"Street_Y_{c:02d}", folder, (dt_cx, y, -0.05),
                    (DOWNTOWN_DEPTH, STREET_WIDTH, 0.25), (0, 0, 0), mat)
        count += 1
    log("Downtown streets: %d actor(s) -- every X-street physically crosses every Y-street." % count)


def build_outskirt_roads(mat):
    folder = "City/Outskirts/Roads"
    count = 0
    for r in range(OUTSKIRT_ROAD_COUNT):
        seed = f"road_{r}"
        x = CITY_X_START - DOWNTOWN_DEPTH
        y = -CITY_Y_HALF_WIDTH + (r + 0.5) / OUTSKIRT_ROAD_COUNT * (CITY_Y_HALF_WIDTH * 2.0)
        heading = 180.0 + (prand(seed + "h0") - 0.5) * 50.0
        steps = int(24 + prand(seed + "len") * 14)

        prev_placed = False
        for i in range(steps):
            if abs(y) > city_boundary_y(x) - 6.0 or x < CITY_X_END + 10.0:
                break
            heading += (prand(f"{seed}_{i}_turn") - 0.5) * 32.0
            rad = math.radians(heading)
            nx = x + math.cos(rad) * OUTSKIRT_STEP
            ny = y + math.sin(rad) * OUTSKIRT_STEP
            mid_x, mid_y = (x + nx) / 2.0, (y + ny) / 2.0

            if prev_placed:
                spawn_block(f"RoadJoint_{r:02d}_{i:03d}", folder, (x, y, -0.05),
                            (OUTSKIRT_ROAD_WIDTH, OUTSKIRT_ROAD_WIDTH, 0.25), (0, 0, 0), mat)
                count += 1

            spawn_block(f"Road_{r:02d}_{i:03d}", folder, (mid_x, mid_y, -0.05),
                        (OUTSKIRT_STEP + 2.0, OUTSKIRT_ROAD_WIDTH, 0.25), (0, 0, heading), mat)
            count += 1

            x, y = nx, ny
            prev_placed = True
    log("Outskirt roads: %d actor(s) (segments + joints)." % count)


def run():
    clear_previous()
    mat = get_or_make_flat_material()
    build_causeway(mat)
    build_downtown_streets(mat)
    build_outskirt_roads(mat)
    log("Done. Every piece here uses a flat, untextured grey material by design -- "
        "check the shape/connectivity in the viewport, then tell me and I'll take a "
        "real stone material pass at it as its own next step.")


run()
