"""
CONNECT ORPHAN BUILDINGS TO THE ROAD NETWORK
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
"add road around all the building that are currently missing it" -- Downtown
buildings sit right against their street grid so they're basically always
touching a road already, but a lot of Outskirt_* buildings (organic
scatter, independent of the road random-walk) end up sitting some distance
from the nearest road piece with nothing connecting them to it.

THE FIX
-------
For every Downtown_*/Outskirt_* building: find the nearest road/path actor
(matched by material, same as the overlap-fix scripts -- covers
M_AI_CobblestonePath and, for safety, MI_Landmass_Road too in case this is
run before retexture_all_roads.py) by real bounding-box gap distance. If
that gap exceeds CONNECT_THRESHOLD_M, spawn a straight cobblestone
connector strip (BuildingLink_<label>) running from the building's nearest
edge point to the road's nearest edge point, width CONNECTOR_WIDTH_M,
laid flat at ground level and oriented to point straight at the road.

Buildings already close enough to a road (touching or within the
threshold) are left alone -- this only fills in genuine gaps.

Safe to re-run -- clears any previously-spawned BuildingLink_* actors
first, so it won't pile up duplicates.

RUN THIS AFTER retexture_all_roads.py so the new connectors match the
road material that's actually textured.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/connect_buildings_to_roads.py"
"""

import math
import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary

PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
FLAT_ROAD_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_Road"
CUBE_MESH_PATH = "/Engine/BasicShapes/Cube.Cube"

CONNECT_THRESHOLD_M = 3.0     # gaps smaller than this count as "already connected"
CONNECTOR_WIDTH_M = 3.0
CONNECTOR_HEIGHT_M = 0.22
ROOT_FOLDER = "IronBreach/City/RoadLinks"


def log(msg):
    print("[ConnectBuildingsToRoads] %s" % msg)


def is_road_actor(actor):
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        mat = comp.get_material(0)
        if mat:
            p = mat.get_path_name()
            if p.startswith(PATH_MATERIAL_PATH) or p.startswith(FLAT_ROAD_MATERIAL_PATH):
                return True
    return False


def get_aabb_xy(actor):
    origin, extent = actor.get_actor_bounds(False)
    return (origin.x - extent.x, origin.y - extent.y, origin.x + extent.x, origin.y + extent.y)


def closest_point_on_box(box, px, py):
    x0, y0, x1, y1 = box
    return (max(x0, min(px, x1)), max(y0, min(py, y1)))


def box_gap_and_points(box_a, box_b):
    """Returns (gap_distance_cm, point_on_a, point_on_b) between two AABBs."""
    ax0, ay0, ax1, ay1 = box_a
    bx0, by0, bx1, by1 = box_b
    a_cx, a_cy = (ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0
    b_cx, b_cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0

    pa = closest_point_on_box(box_a, b_cx, b_cy)
    pb = closest_point_on_box(box_b, a_cx, a_cy)
    # Refine once more now that we have better target points
    pa = closest_point_on_box(box_a, pb[0], pb[1])
    pb = closest_point_on_box(box_b, pa[0], pa[1])

    dist = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
    return dist, pa, pb


def clear_previous_links(all_actors):
    removed = 0
    for a in list(all_actors):
        if a.get_actor_label().startswith("BuildingLink_"):
            actor_subsystem.destroy_actor(a)
            removed += 1
    if removed:
        log("Removed %d previously-spawned BuildingLink_* actor(s)." % removed)


def run():
    if not AL.does_asset_exist(PATH_MATERIAL_PATH):
        log("ABORTED -- %s doesn't exist." % PATH_MATERIAL_PATH)
        return
    cobblestone = AL.load_asset(PATH_MATERIAL_PATH)
    cube_mesh = AL.load_asset(CUBE_MESH_PATH)

    all_actors = actor_subsystem.get_all_level_actors()
    clear_previous_links(all_actors)
    all_actors = actor_subsystem.get_all_level_actors()

    buildings = [a for a in all_actors if a.get_actor_label().startswith(("Outskirt_", "Downtown_"))]
    roads = [a for a in all_actors if is_road_actor(a)]

    if not roads:
        log("ABORTED -- no road/path actors found in the level.")
        return

    road_boxes = [(r, get_aabb_xy(r)) for r in roads]
    threshold_cm = CONNECT_THRESHOLD_M * 100.0

    connected = 0
    already_ok = 0

    for b in buildings:
        b_box = get_aabb_xy(b)
        best = None
        for road, r_box in road_boxes:
            dist, pa, pb = box_gap_and_points(b_box, r_box)
            if best is None or dist < best[0]:
                best = (dist, pa, pb, road)

        dist, pa, pb, road = best
        if dist <= threshold_cm:
            already_ok += 1
            continue

        mid_x = (pa[0] + pb[0]) / 2.0
        mid_y = (pa[1] + pb[1]) / 2.0
        length_cm = max(dist, 10.0)
        yaw = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))

        label = "BuildingLink_%s" % b.get_actor_label()
        location = unreal.Vector(mid_x, mid_y, 2.0)
        rotation = unreal.Rotator(0.0, 0.0, yaw)
        actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
        actor.set_actor_label(label)
        actor.set_folder_path(ROOT_FOLDER)
        mesh_comp = actor.static_mesh_component
        mesh_comp.set_static_mesh(cube_mesh)
        # Engine cube is 100x100x100cm native -> scale IS size in cm/100.
        mesh_comp.set_world_scale3d(unreal.Vector(
            length_cm / 100.0, (CONNECTOR_WIDTH_M * 100.0) / 100.0, (CONNECTOR_HEIGHT_M * 100.0) / 100.0))
        mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
        mesh_comp.set_material(0, cobblestone)
        connected += 1
        log("  %s -> nearest road %s, gap %.1fm, connector length %.1fm" % (
            b.get_actor_label(), road.get_actor_label(), dist / 100.0, length_cm / 100.0))

    log("Connected %d building(s) that were missing a road link (%d were already within %.1fm of a road)." % (
        connected, already_ok, CONNECT_THRESHOLD_M))
    log("Save and check the viewport / re-run PIE.")


run()
