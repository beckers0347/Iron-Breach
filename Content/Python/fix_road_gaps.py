"""
FIX GAPS BETWEEN PATH PIECES -- bridge any road segments that don't quite touch
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Even with the rebuilt road network (contiguous causeway segments, full-span
downtown streets, outskirt roads with joints baked in from the start),
real-world placement math can still leave a hairline or few-meter gap
between two road pieces that were meant to meet -- easy to miss until
you're looking straight down at the path and see a sliver of bare ground
between two cobblestone segments.

THE FIX
-------
Finds every actor wearing M_AI_CobblestonePath, computes real bounding
boxes, and for any two pieces whose boxes are close (within
GAP_THRESHOLD_M) but not actually touching (beyond TOUCH_MARGIN_M), spawns
a small square PathGapFill_<n> patch at their midpoint sized to cover the
gap plus a margin -- same technique proven out earlier for building/road
connectors. Pieces that are already touching, or are far apart (different
parts of the network, not meant to connect), are left alone.

Safe to re-run -- clears any previously-spawned PathGapFill_* actors first.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_road_gaps.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary

PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
CUBE_MESH_PATH = "/Engine/BasicShapes/Cube.Cube"

GAP_THRESHOLD_M = 6.0     # only bridge gaps smaller than this -- bigger gaps are unrelated pieces
TOUCH_MARGIN_M = 0.3      # boxes within this are already considered touching
PATCH_MARGIN_M = 1.5      # extra size added around the bridging patch
PATCH_HEIGHT_M = 0.28
ROOT_FOLDER = "IronBreach/City/PathGapFills"


def log(msg):
    print("[FixRoadGaps] %s" % msg)


def is_path_actor(actor):
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        mat = comp.get_material(0)
        if mat and mat.get_path_name().startswith(PATH_MATERIAL_PATH):
            return True
    return False


def get_aabb_xy(actor):
    origin, extent = actor.get_actor_bounds(False)
    return (origin.x - extent.x, origin.y - extent.y, origin.x + extent.x, origin.y + extent.y)


def closest_point_on_box(box, px, py):
    x0, y0, x1, y1 = box
    return (max(x0, min(px, x1)), max(y0, min(py, y1)))


def box_gap_and_points(box_a, box_b):
    """Returns (gap_distance_cm, midpoint) between two AABBs."""
    ax0, ay0, ax1, ay1 = box_a
    bx0, by0, bx1, by1 = box_b
    a_cx, a_cy = (ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0
    b_cx, b_cy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0

    pa = closest_point_on_box(box_a, b_cx, b_cy)
    pb = closest_point_on_box(box_b, a_cx, a_cy)
    pa = closest_point_on_box(box_a, pb[0], pb[1])
    pb = closest_point_on_box(box_b, pa[0], pa[1])

    dist = ((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2) ** 0.5
    mid = ((pa[0] + pb[0]) / 2.0, (pa[1] + pb[1]) / 2.0)
    return dist, mid


def clear_previous(all_actors):
    removed = 0
    for a in list(all_actors):
        if a.get_actor_label().startswith("PathGapFill_"):
            actor_subsystem.destroy_actor(a)
            removed += 1
    if removed:
        log("Removed %d previously-spawned PathGapFill_* actor(s)." % removed)


def run():
    if not AL.does_asset_exist(PATH_MATERIAL_PATH):
        log("ABORTED -- %s doesn't exist." % PATH_MATERIAL_PATH)
        return
    cobblestone = AL.load_asset(PATH_MATERIAL_PATH)
    cube_mesh = AL.load_asset(CUBE_MESH_PATH)

    all_actors = actor_subsystem.get_all_level_actors()
    clear_previous(all_actors)
    all_actors = actor_subsystem.get_all_level_actors()

    paths = [a for a in all_actors if is_path_actor(a)]
    boxes = [(a, get_aabb_xy(a)) for a in paths]
    log("Checking %d path piece(s) for gaps..." % len(paths))

    touch_cm = TOUCH_MARGIN_M * 100.0
    gap_threshold_cm = GAP_THRESHOLD_M * 100.0
    patch_margin_cm = PATCH_MARGIN_M * 100.0

    filled = 0
    seen_pairs = set()

    for i in range(len(boxes)):
        a, box_a = boxes[i]
        ax0, ay0, ax1, ay1 = box_a
        acx, acy = (ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0
        for j in range(i + 1, len(boxes)):
            b, box_b = boxes[j]
            bx0, by0, bx1, by1 = box_b

            # quick reject if centers are way too far apart to be neighbors
            bcx, bcy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
            if abs(acx - bcx) > 4000.0 or abs(acy - bcy) > 4000.0:
                continue

            gap, (mid_x, mid_y) = box_gap_and_points(box_a, box_b)
            if gap <= touch_cm or gap > gap_threshold_cm:
                continue

            pair_key = (a.get_actor_label(), b.get_actor_label())
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            patch_size_cm = gap + patch_margin_cm * 2.0
            patch_size_cm = max(patch_size_cm, 100.0)

            label = "PathGapFill_%04d" % filled
            location = unreal.Vector(mid_x, mid_y, 1.5)
            actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(0, 0, 0))
            actor.set_actor_label(label)
            actor.set_folder_path(ROOT_FOLDER)
            mesh_comp = actor.static_mesh_component
            mesh_comp.set_static_mesh(cube_mesh)
            mesh_comp.set_world_scale3d(unreal.Vector(
                patch_size_cm / 100.0, patch_size_cm / 100.0, (PATCH_HEIGHT_M * 100.0) / 100.0))
            mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
            mesh_comp.set_material(0, cobblestone)
            filled += 1
            log("  gap %.2fm between %s and %s -> filled at (%.0f, %.0f)" % (
                gap / 100.0, a.get_actor_label(), b.get_actor_label(), mid_x, mid_y))

    log("Filled %d gap(s) between path pieces. Save and check the viewport / re-run PIE." % filled)


run()
