"""
FIX ALL CITY BUILDING OVERLAPS -- Downtown AND Outskirts, both movable
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
fix_outskirt_overlaps.py only ever moved Outskirt_* buildings, treating
Downtown_* as a fixed obstacle. Shane's newest ask is broader: "adjust the
building in the city so they arent overlapping" -- covers the whole city,
Downtown included, not just the outskirts.

Downtown buildings are placed on a real grid so they mostly don't overlap
each other by construction, but they CAN still overlap:
  - a road/street piece (grid math + per-building jitter can push a corner
    over a street edge)
  - an Outskirt_* building near the downtown/outskirt seam

THE FIX
-------
Same real-bounding-box relaxation approach as fix_outskirt_overlaps.py, but
now BOTH Downtown_* and Outskirt_* buildings are movable, and they push off
each other, off roads, and off CityGround_* alike. Buildings that aren't
overlapping anything are left completely untouched.

Safe to re-run -- if nothing overlaps, it does nothing. Run this INSTEAD of
fix_outskirt_overlaps.py from here on (it's a superset).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_all_city_overlaps.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
FLAT_ROAD_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_Road"
MARGIN_M = 4.0
PASSES = 50
DAMPING = 0.6


def log(msg):
    print("[FixAllCityOverlaps] %s" % msg)


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
    return (origin.x - extent.x, origin.y - extent.y, origin.x + extent.x, origin.y + extent.y, origin)


def overlap_mtv(box_a, box_b, margin_cm):
    ax0, ay0, ax1, ay1, ao = box_a
    bx0, by0, bx1, by1, bo = box_b
    ox = min(ax1, bx1) - max(ax0, bx0) + margin_cm
    oy = min(ay1, by1) - max(ay0, by0) + margin_cm
    if ox <= 0 or oy <= 0:
        return None
    dx = ao.x - bo.x
    dy = ao.y - bo.y
    if ox < oy:
        push = ox
        vx = 1.0 if dx >= 0 else -1.0
        return (push * vx, 0.0)
    else:
        push = oy
        vy = 1.0 if dy >= 0 else -1.0
        return (0.0, push * vy)


def run():
    all_actors = actor_subsystem.get_all_level_actors()
    buildings = [a for a in all_actors
                 if a.get_actor_label().startswith(("Outskirt_", "Downtown_"))]
    roads = [a for a in all_actors if is_road_actor(a)]
    other_static = [a for a in all_actors
                     if a not in buildings and a not in roads
                     and a.get_actor_label().startswith("CityGround_")]

    log("Movable: %d city building(s) (Downtown + Outskirts). Fixed obstacles: %d road piece(s), %d ground piece(s)." % (
        len(buildings), len(roads), len(other_static)))

    margin_cm = MARGIN_M * 100.0
    moved_total = set()

    for p in range(PASSES):
        any_overlap = False
        boxes = {a: get_aabb_xy(a) for a in buildings}
        obstacle_boxes = [get_aabb_xy(a) for a in roads + other_static]

        pushes = {a: [0.0, 0.0] for a in buildings}

        for i, a in enumerate(buildings):
            box_a = boxes[a]
            for ob in obstacle_boxes:
                mtv = overlap_mtv(box_a, ob, margin_cm)
                if mtv:
                    pushes[a][0] += mtv[0]
                    pushes[a][1] += mtv[1]
                    any_overlap = True
            for j in range(i + 1, len(buildings)):
                b = buildings[j]
                mtv = overlap_mtv(box_a, boxes[b], margin_cm)
                if mtv:
                    pushes[a][0] += mtv[0] * 0.5
                    pushes[a][1] += mtv[1] * 0.5
                    pushes[b][0] -= mtv[0] * 0.5
                    pushes[b][1] -= mtv[1] * 0.5
                    any_overlap = True

        if not any_overlap:
            log("No overlaps remaining after %d pass(es)." % p)
            break

        for a, (px, py) in pushes.items():
            if px == 0.0 and py == 0.0:
                continue
            loc = a.get_actor_location()
            a.set_actor_location(unreal.Vector(loc.x + px * DAMPING, loc.y + py * DAMPING, loc.z), False, False)
            moved_total.add(a)

    log("Moved %d building(s) total to clear overlaps:" % len(moved_total))
    for a in sorted(moved_total, key=lambda x: x.get_actor_label()):
        loc = a.get_actor_location()
        log("  %s -> (%.0f, %.0f)" % (a.get_actor_label(), loc.x, loc.y))

    log("Save and check the viewport / re-run PIE.")


run()
