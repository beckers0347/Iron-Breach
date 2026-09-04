"""
ALIGN BUILDINGS TO THE ROAD NETWORK -- rotate to run parallel with the
nearest street, pull them in to a tight 2-4m setback from the road edge
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
relayout_town.py placed every fill building with a random yaw and a loose
rejection-sampled position, so nothing lines up with the streets that
build_town_roads.py laid down afterward. Shane wants buildings rotated so
their walls run parallel to whichever road they're closest to, and pulled
in so there's only a 2-4m gap between the road's edge and the building's
edge -- a real street-front layout instead of a scatter.

HOW IT WORKS
------------
  1. Recomputes the same backbone road segments build_town_roads.py builds
     (perimeter loop connecting the 4 towers, main spine through the
     square/spire, cross spine through the spire) directly from the actual
     Spire_TownCenter / TownSquare / CornerTower_* actors in the level --
     not the spawned road meshes -- so it always matches what's really
     there.
  2. For every Rowhouse/Warehouse/Apartment/Cottage/Shopfront/Garage/
     EdgeRuin actor, finds the closest point on the closest backbone
     segment.
  3. Every building type relayout_town.py placed has an ISOTROPIC target
     size (Shopfront 7x7x7, Rowhouse 50x50x50, etc -- literal world-space
     cube envelopes), so half that size is the building's true edge
     distance from its own pivot regardless of rotation. That, plus the
     road's own half-width, is used to solve for a pivot position that
     lands the building's edge exactly `gap` meters (2-4m, varied
     per-building) from the road's edge.
  4. Rotates the building's yaw to match the road segment's direction (so
     its walls run parallel to the street) and keeps it on the same side
     of the road it was already on, so buildings don't jump across the
     street from where Shane last saw them.
  5. Leaves the Spire, Town Square and the 4 corner Towers untouched --
     those actors ARE what defines the road network, so moving them would
     invalidate the road layout.

Safe to re-run -- it always recomputes from each building's *current*
position, so running it twice just re-snaps everything again.

Buildings will move. Re-run build_town_roads.py afterward to rebuild the
spurs against the new positions (most spurs should shrink to nothing now
that buildings sit right up against the backbone streets).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/align_buildings_to_roads.py"
"""

import unreal
import math

M = 100.0

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

CITY_X_START = -40.0

# Isotropic target size (meters) relayout_town.py fit each building type to
# -- half of this is the true edge-distance from the actor's own pivot,
# regardless of yaw, since the fit made the native bounding box a literal
# cube of this size before any extra rotation was applied on top.
SIZE_BY_PREFIX = {
    "Rowhouse_": 50.0,
    "Warehouse_": 25.0,
    "Apartment_": 30.0,
    "Cottage_": 10.0,
    "Shopfront_": 7.0,
    "Garage_": 8.0,
    "EdgeRuin_": 20.0,
}

# Backbone road widths (meters) -- must match build_town_roads.py.
LOOP_WIDTH = 6.0
MAIN_WIDTH = 9.0
CROSS_WIDTH = MAIN_WIDTH * 0.75

MIN_GAP = 2.0
MAX_GAP = 4.0


def log(msg):
    print("[AlignBuildingsToRoads] %s" % msg)


def prand(seed):
    """Deterministic pseudo-random float in [0,1) from an integer/string seed."""
    h = 2166136261
    for ch in str(seed):
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    h ^= (h >> 15)
    h = (h * 2246822519) & 0xFFFFFFFF
    h ^= (h >> 13)
    return (h % 1000000) / 1000000.0


def closest_point_on_seg(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq < 1e-6:
        return x0, y0, ((px - x0) ** 2 + (py - y0) ** 2) ** 0.5, 0.0, 0.0
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / seg_len_sq))
    cx, cy = x0 + t * dx, y0 + t * dy
    dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
    length = seg_len_sq ** 0.5
    return cx, cy, dist, dx / length, dy / length


def run():
    all_actors = actor_subsystem.get_all_level_actors()

    def find_one(prefix):
        for a in all_actors:
            if a.get_actor_label().startswith(prefix):
                return a
        return None

    def find_all(prefixes):
        out = []
        for a in all_actors:
            label = a.get_actor_label()
            if any(label.startswith(p) for p in prefixes):
                out.append(a)
        return out

    spire = find_one("Spire_TownCenter")
    square = find_one("TownSquare")
    towers = find_all(["CornerTower_"])

    if spire is None or square is None or len(towers) != 4:
        log("ABORTED -- expected Spire_TownCenter, TownSquare and 4 CornerTower_* actors "
            "(run relayout_town.py first, then build_town_roads.py). Found spire=%s square=%s towers=%d" % (
                spire is not None, square is not None, len(towers)))
        return

    def loc_xy(actor):
        l = actor.get_actor_location()
        return l.x / M, l.y / M

    spire_x, spire_y = loc_xy(spire)
    square_x, square_y = loc_xy(square)
    tower_pts = [loc_xy(t) for t in towers]

    near = sorted([p for p in tower_pts if p[0] > (CITY_X_START - 130.0)], key=lambda p: -p[1])
    far = sorted([p for p in tower_pts if p not in near], key=lambda p: -p[1])
    if len(near) != 2 or len(far) != 2:
        near = sorted(tower_pts, key=lambda p: -p[0])[:2]
        far = sorted(tower_pts, key=lambda p: -p[0])[2:]
    loop = [near[0], far[0], far[1], near[1]]

    segments = []  # (x0,y0,x1,y1,width)
    for i in range(4):
        x0, y0 = loop[i]
        x1, y1 = loop[(i + 1) % 4]
        segments.append((x0, y0, x1, y1, LOOP_WIDTH))

    entrance_x, entrance_y = CITY_X_START, 0.0
    back_x = (loop[1][0] + loop[2][0]) / 2.0
    back_y = (loop[1][1] + loop[2][1]) / 2.0
    spine_pts = [(entrance_x, entrance_y), (square_x, square_y), (spire_x, spire_y), (back_x, back_y)]
    for i in range(len(spine_pts) - 1):
        x0, y0 = spine_pts[i]
        x1, y1 = spine_pts[i + 1]
        segments.append((x0, y0, x1, y1, MAIN_WIDTH))

    side_a = min(loop, key=lambda p: abs(p[0] - spire_x) + (0 if p[1] > 0 else 1000))
    side_b = min(loop, key=lambda p: abs(p[0] - spire_x) + (0 if p[1] < 0 else 1000))
    cross_pts = [(side_a[0], side_a[1]), (spire_x, spire_y), (side_b[0], side_b[1])]
    for i in range(len(cross_pts) - 1):
        x0, y0 = cross_pts[i]
        x1, y1 = cross_pts[i + 1]
        segments.append((x0, y0, x1, y1, CROSS_WIDTH))

    log("Recomputed %d backbone road segment(s)." % len(segments))

    buildings = find_all(list(SIZE_BY_PREFIX.keys()))
    moved = 0
    skipped = 0

    for b in buildings:
        label = b.get_actor_label()
        prefix = next((p for p in SIZE_BY_PREFIX if label.startswith(p)), None)
        if prefix is None:
            skipped += 1
            continue

        bx, by = loc_xy(b)

        best = None
        for (x0, y0, x1, y1, w) in segments:
            cx, cy, dist, dirx, diry = closest_point_on_seg(bx, by, x0, y0, x1, y1)
            if best is None or dist < best[2]:
                best = (cx, cy, dist, dirx, diry, w)
        if best is None:
            skipped += 1
            continue

        cx, cy, dist, dirx, diry, width = best
        nx, ny = -diry, dirx  # road normal (perpendicular to travel direction)

        # Which side of the road is this building currently on?
        side_dot = (bx - cx) * nx + (by - cy) * ny
        side = 1.0 if side_dot >= 0 else -1.0

        half = SIZE_BY_PREFIX[prefix] / 2.0
        gap = MIN_GAP + (MAX_GAP - MIN_GAP) * prand(label)
        offset = (width / 2.0) + gap + half

        new_x = cx + side * nx * offset
        new_y = cy + side * ny * offset

        yaw = math.degrees(math.atan2(diry, dirx))

        loc = b.get_actor_location()
        b.set_actor_location(unreal.Vector(new_x * M, new_y * M, loc.z), False, False)
        b.set_actor_rotation(unreal.Rotator(0.0, 0.0, yaw), False)
        moved += 1

    log("Aligned %d building(s) to their nearest road, parallel with a %.0f-%.0fm edge gap; skipped %d." % (
        moved, MIN_GAP, MAX_GAP, skipped))
    log("Done. Save, take a look, then re-run build_town_roads.py to rebuild the spurs against the new positions.")


run()
