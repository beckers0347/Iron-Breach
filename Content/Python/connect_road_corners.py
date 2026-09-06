"""
FILL THE GAPS AT OUTSKIRT ROAD TURNS -- square joint patches at every bend
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
build_outskirt_roads() (in build_carrowgate_mainland.py) lays each winding
outskirt road down as a chain of straight rotated box segments -- a random
walk that turns up to +/-16 degrees per 9m step. Each segment overruns its
own step length a bit (STEP+2.0 instead of STEP) so segments overlap along
their length, but that overrun doesn't fix the OUTSIDE of a turn: two
straight-edged boxes meeting at an angle always leave a wedge-shaped gap of
bare ground showing through on the outer edge of the bend, and the new
cobblestone grid on the road material actually makes this more obvious than
the old flat gray road did, since the grid pattern now visibly stops short
of the corner instead of blending into a uniform gray.

THE FIX
-------
This does NOT touch or respawn the existing road segments (avoids re-running
the whole mainland build and risking duplicate buildings/trees/etc). It just
re-derives the exact same random-walk waypoints that build_outskirt_roads()
already used -- identical seed/prand/heading logic, copy-pasted from that
function -- and drops one small square joint patch (ROAD_WIDTH x ROAD_WIDTH,
axis-aligned, not rotated) centered on every waypoint where one placed
segment ends and the next begins. A square that size fully covers the
outside wedge at any turn angle the random walk can produce, regardless of
which way the road bends.

Safe to re-run -- it deletes any joints it placed on a previous run first
(RoadJoint_* labels), so re-running with the same layout doesn't stack
duplicates.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/connect_road_corners.py"
"""

import unreal
import math

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary

M = 100.0  # meters -> unreal units, matches build_carrowgate_mainland.py's M
ROOT_FOLDER = "CG Mainland"
CUBE_MESH = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
ROAD_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_Road"

# ---- copied verbatim from build_carrowgate_mainland.py so the waypoints match exactly ----
CITY_X_START = -40.0
CITY_X_END = -300.0
DOWNTOWN_DEPTH = 70.0
CITY_Y_HALF_WIDTH = 130.0
ROAD_WIDTH = 6.0
STEP = 9.0
ROAD_COUNT = 6


def log(msg):
    print("[ConnectRoadCorners] %s" % msg)


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


def spawn_joint(label, loc_m, size_m, material):
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    rotation = unreal.Rotator(0, 0, 0)
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/City/Outskirts/Roads")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(CUBE_MESH)
    mesh_comp.set_world_scale3d(unreal.Vector(size_m[0], size_m[1], size_m[2]))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    return actor


def delete_existing_joints():
    all_actors = actor_subsystem.get_all_level_actors()
    existing = [a for a in all_actors if a.get_actor_label().startswith("RoadJoint_")]
    for a in existing:
        actor_subsystem.destroy_actor(a)
    if existing:
        log("Removed %d joint(s) from a previous run before re-placing." % len(existing))


def run():
    if not AL.does_asset_exist(ROAD_MATERIAL_PATH):
        log("SKIPPED -- %s doesn't exist." % ROAD_MATERIAL_PATH)
        return
    road_mat = AL.load_asset(ROAD_MATERIAL_PATH)

    delete_existing_joints()

    placed = 0
    for r in range(ROAD_COUNT):
        seed = f"road_{r}"
        x = CITY_X_START - DOWNTOWN_DEPTH
        y = -CITY_Y_HALF_WIDTH + (r + 0.5) / ROAD_COUNT * (CITY_Y_HALF_WIDTH * 2.0)
        heading = 180.0 + (prand(seed + "h0") - 0.5) * 50.0
        steps = int(24 + prand(seed + "len") * 14)

        prev_placed = False
        for i in range(steps):
            if abs(y) > city_boundary_y(x) - 6.0 or x < CITY_X_END + 10.0:
                break
            heading += (prand(f"{seed}_{i}_turn") - 0.5) * 32.0
            rad = math.radians(heading)
            nx = x + math.cos(rad) * STEP
            ny = y + math.sin(rad) * STEP

            # a joint at (x, y) covers the seam between the PREVIOUS segment
            # (which ended here) and this one (which starts here).
            if prev_placed:
                spawn_joint(f"RoadJoint_{r:02d}_{i:03d}", (x, y, -0.05),
                            (ROAD_WIDTH, ROAD_WIDTH, 0.25), road_mat)
                placed += 1

            x, y = nx, ny
            prev_placed = True

    log("Placed %d corner joint(s) across %d outskirt road(s)." % (placed, ROAD_COUNT))
    log("Save and check the viewport / re-run PIE.")


run()
