"""
REBUILD THE TOWN ROAD NETWORK -- flat blockout, real connectivity, rounded
corners -- NO cobblestone yet (Shane: confirm the flow first)
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Every road/path actor in the level got deleted a while back (660 actors --
Causeway, Downtown Streets, Outskirt Roads, PathGapFills, RoadLinks -- all
gone). Then the whole building layout changed too (relayout_town.py): one
Spire at the literal town center with a square in front of it, 4 Towers at
the town's corners, Ruins out along the far edge, everything else scattered
through the middle. The old street grid wouldn't have matched any of that
even if it still existed.

Shane wants the path NETWORK rebuilt first, and wants to see it flows
correctly -- real connections, not another random scatter -- before any
cobblestone goes back on. So this uses a plain flat placeholder material
(MI_Landmass_Road, same "untextured gray" placeholder every road in this
project has used at blockout stage) and focuses entirely on layout:

  - A perimeter loop connecting all 4 Towers (queried from their actual
    spawned locations, not recomputed math -- whatever's really in the
    level right now), forming the town's outer ring road.
  - A main spine from the causeway/gate entrance, through the Town Square,
    past the Spire, back to where it meets the perimeter loop's far edge.
  - A cross spine through the Spire, perpendicular to the main spine,
    connecting out to the loop's left and right sides.
  - A short straight spur from every other building (every Rowhouse/
    Warehouse/Apartment/Cottage/Shopfront/Garage/Ruin relayout_town.py
    placed) to the closest point on the road network above -- same
    closest-point-on-segment technique proven out in
    connect_buildings_to_roads.py last session.
  - A cylinder "corner pad" at every turn (all 4 perimeter-loop corners,
    plus the square/spire/back-edge and cross-spine junctions) so turns
    read as rounded curves instead of hard right-angle miters -- exactly
    what Shane asked for.

Once this is confirmed to flow the way Shane wants, swap MI_Landmass_Road
for M_AI_CobblestonePath the same way retexture_all_roads.py did before
(or just re-run that idea against the "IronBreach/City/Roads" folder this
script uses).

Safe to re-run -- clears everything under "IronBreach/City/Roads" first.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/build_town_roads.py"
"""

import unreal

M = 100.0
ROOT_FOLDER = "IronBreach/City/Roads"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary
CUBE_MESH = AL.load_asset("/Engine/BasicShapes/Cube.Cube")
CYLINDER_MESH = AL.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
FLAT_ROAD_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_Road"

MAIN_WIDTH = 9.0       # spine through the square/spire -- the town's primary street
LOOP_WIDTH = 6.0        # perimeter ring connecting the 4 towers
SPUR_WIDTH = 4.0        # short connectors from individual buildings to the network
ROAD_THICKNESS = 0.3
ROAD_Z = 0.05           # sits a hair above ground level, matches old road convention

CITY_X_START = -40.0    # where the causeway meets the city -- entrance end of the main spine


def log(msg):
    print("[BuildTownRoads] %s" % msg)


def clear_previous():
    removed = 0
    for a in list(actor_subsystem.get_all_level_actors()):
        folder = str(a.get_folder_path())
        if folder == ROOT_FOLDER or folder.startswith(ROOT_FOLDER + "/"):
            actor_subsystem.destroy_actor(a)
            removed += 1
    if removed:
        log("Cleared %d previous road actor(s)." % removed)


def spawn_segment(label, folder, x0, y0, x1, y1, width, material):
    """Straight road segment (as a cube) spanning (x0,y0)->(x1,y1)."""
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    if length < 0.05:
        return None
    import math
    yaw = math.degrees(math.atan2(y1 - y0, x1 - x0))
    location = unreal.Vector(cx * M, cy * M, ROAD_Z * M)
    rotation = unreal.Rotator(0.0, 0.0, yaw)
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(CUBE_MESH)
    mesh_comp.set_world_scale3d(unreal.Vector(length, width, ROAD_THICKNESS))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    return actor


def spawn_corner(label, folder, x, y, width, material, radius_mult=1.35):
    """Cylinder corner pad -- rounds off a turn/junction so it reads as a
    curve instead of a sharp miter."""
    diameter = width * radius_mult
    location = unreal.Vector(x * M, y * M, ROAD_Z * M)
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(0, 0, 0))
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(CYLINDER_MESH)
    mesh_comp.set_world_scale3d(unreal.Vector(diameter, diameter, ROAD_THICKNESS))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    return actor


def closest_point_on_seg(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq < 1e-6:
        return x0, y0, ((px - x0) ** 2 + (py - y0) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / seg_len_sq))
    cx, cy = x0 + t * dx, y0 + t * dy
    return cx, cy, ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5


def run():
    flat_mat = AL.load_asset(FLAT_ROAD_MATERIAL_PATH)
    if flat_mat is None:
        log("ABORTED -- %s not found." % FLAT_ROAD_MATERIAL_PATH)
        return

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
            "(run relayout_town.py first). Found spire=%s square=%s towers=%d" % (
                spire is not None, square is not None, len(towers)))
        return

    clear_previous()

    def loc_xy(actor):
        l = actor.get_actor_location()
        return l.x / M, l.y / M

    spire_x, spire_y = loc_xy(spire)
    square_x, square_y = loc_xy(square)
    tower_pts = [loc_xy(t) for t in towers]

    # Sort the 4 towers into NE/SE/SW/NW loop order (x descending = nearer
    # entrance first, matching CornerTower_NearEntrance_*/FarEdge_* naming,
    # then split each pair by y sign).
    near = sorted([p for p in tower_pts if p[0] > (CITY_X_START - 130.0)], key=lambda p: -p[1])
    far = sorted([p for p in tower_pts if p not in near], key=lambda p: -p[1])
    if len(near) != 2 or len(far) != 2:
        # fallback: just sort all 4 by x then y so the loop still closes sanely
        near = sorted(tower_pts, key=lambda p: -p[0])[:2]
        far = sorted(tower_pts, key=lambda p: -p[0])[2:]
    loop = [near[0], far[0], far[1], near[1]]  # NE, FE(+y), FE(-y), NE(-y) -> closed rectangle order

    segments = []  # (x0,y0,x1,y1,width) for spur closest-point checks

    # -- 1. Perimeter loop connecting all 4 towers, rounded corners --------
    for i in range(4):
        x0, y0 = loop[i]
        x1, y1 = loop[(i + 1) % 4]
        spawn_segment(f"Loop_{i:02d}", "Loop", x0, y0, x1, y1, LOOP_WIDTH, flat_mat)
        segments.append((x0, y0, x1, y1, LOOP_WIDTH))
    for i, (x, y) in enumerate(loop):
        spawn_corner(f"LoopCorner_{i:02d}", "Loop", x, y, LOOP_WIDTH, flat_mat)
    log("Perimeter loop: 4 segments connecting the towers, 4 rounded corners.")

    # -- 2. Main spine: entrance -> square -> spire -> back edge -----------
    entrance_x, entrance_y = CITY_X_START, 0.0
    # Back edge target: midpoint of whichever loop edge is "behind" the spire
    # (the far edge segment, i.e. the loop edge connecting the two far
    # towers) -- that's loop[1]->loop[2].
    back_x = (loop[1][0] + loop[2][0]) / 2.0
    back_y = (loop[1][1] + loop[2][1]) / 2.0

    spine_pts = [(entrance_x, entrance_y), (square_x, square_y), (spire_x, spire_y), (back_x, back_y)]
    for i in range(len(spine_pts) - 1):
        x0, y0 = spine_pts[i]
        x1, y1 = spine_pts[i + 1]
        spawn_segment(f"MainSpine_{i:02d}", "MainSpine", x0, y0, x1, y1, MAIN_WIDTH, flat_mat)
        segments.append((x0, y0, x1, y1, MAIN_WIDTH))
    for i, (x, y) in enumerate(spine_pts[1:-1], start=1):
        spawn_corner(f"MainSpineJoint_{i:02d}", "MainSpine", x, y, MAIN_WIDTH, flat_mat)
    log("Main spine: entrance -> square -> spire -> back edge, %d segment(s)." % (len(spine_pts) - 1))

    # -- 3. Cross spine through the spire, out to the loop's left/right ----
    left_x = (loop[0][0] + loop[3][0]) / 2.0   # near-entrance side, -y tower... use loop[3]/loop[0] pairing
    left_y = (loop[0][1] + loop[3][1]) / 2.0
    # Simpler + more robust: aim the cross spine straight out along +Y/-Y
    # from the spire to whichever loop edge it actually crosses -- just
    # target the two SIDE loop corners nearest the spire's own depth so the
    # cross street reads as a real perpendicular street, not a diagonal.
    side_a = min(loop, key=lambda p: abs(p[0] - spire_x) + (0 if p[1] > 0 else 1000))
    side_b = min(loop, key=lambda p: abs(p[0] - spire_x) + (0 if p[1] < 0 else 1000))
    cross_pts = [(side_a[0], side_a[1]), (spire_x, spire_y), (side_b[0], side_b[1])]
    for i in range(len(cross_pts) - 1):
        x0, y0 = cross_pts[i]
        x1, y1 = cross_pts[i + 1]
        spawn_segment(f"CrossSpine_{i:02d}", "CrossSpine", x0, y0, x1, y1, MAIN_WIDTH * 0.75, flat_mat)
        segments.append((x0, y0, x1, y1, MAIN_WIDTH * 0.75))
    spawn_corner("CrossSpineJoint", "CrossSpine", spire_x, spire_y, MAIN_WIDTH, flat_mat)
    log("Cross spine through the spire out to both sides of the loop.")

    # -- 4. Spurs: every other building gets a short connector to the -------
    #    nearest point on the road network built so far.
    building_actors = find_all(["Rowhouse_", "Warehouse_", "Apartment_", "Cottage_",
                                 "Shopfront_", "Garage_", "EdgeRuin_"])
    spur_count = 0
    for b in building_actors:
        bx, by = loc_xy(b)
        best = None
        for (x0, y0, x1, y1, w) in segments:
            cx, cy, dist = closest_point_on_seg(bx, by, x0, y0, x1, y1)
            if best is None or dist < best[2]:
                best = (cx, cy, dist)
        if best is None:
            continue
        cx, cy, dist = best
        if dist < 3.0:
            continue  # already basically touching the network
        spawn_segment(f"Spur_{b.get_actor_label()}", "Spurs", bx, by, cx, cy, SPUR_WIDTH, flat_mat)
        spur_count += 1

    log("Spurs: connected %d/%d buildings to the road network." % (spur_count, len(building_actors)))
    log("Done -- flat placeholder material (MI_Landmass_Road) on purpose, no cobblestone yet. "
        "Save, check the viewport / PIE, and once the flow looks right say the word and I'll "
        "swap this over to M_AI_CobblestonePath.")


run()
