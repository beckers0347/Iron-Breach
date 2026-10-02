"""
IBPY: ib_add_markings.py  (v8 -- 2x wider lanes, flat Z=384)

v8: lane width doubled (LANE_HALF_WIDTH_CM, EDGE_LINE_WIDTH_CM,
CENTER_DASH_WIDTH_CM all 2x) and every road waypoint's Z set to a flat
384 (was 382 hub-side / 380 door-side) at your request.

v7: per your sketch, the road to the helipad (and eventually the boat/crane
parking area) is a separate north-south trunk road that runs independently
of the Parade Square loop and forks at a branch point, rather than being
just another spur off the loop's west edge like it was in v6. The trunk's
X position (TRUNK_X_OFFSET_FROM_LOOP) is a guess placed east of the loop,
roughly under the Armory/crossroads area -- nudge that constant if it
doesn't land where the real crossroads structure is once you see it.

v6 replaces the hub-and-spoke diagonal roads with a proper square road
network per your sketch: a rectangular "Parade Square" loop (4 straight,
axis-aligned edges) centered on the hub, with each building connected to
the loop by a right-angle spur (one straight segment, or a single 90-deg
bend when needed) instead of a diagonal line straight to the hub. The
helipad approach is now the same right-angle-spur style off the loop.
World X/Y axes were used for the grid -- the door yaws surveyed earlier
for every building came out within ~10 degrees of 0/90/180/270, so the
buildings themselves are already very close to axis-aligned; a rotated
camera in some of your screenshots made the platform look diagonal on
screen even though it isn't in world space.

NOT done yet: your sketch also shows a road branch to a "Parking" area
near the boat/crane on the east side of the platform. I don't have real
coordinates for that spot -- same as the slope waypoints, if you place a
reference actor there and give me its Location, I'll add that branch too.

v3 fixed two bugs seen in the v2 screenshot: (1) the helipad "H" was
rendering as a "+" cross because both legs were offset along the same axis
as their own length, landing them on top of the crossbar -- legs are now
offset apart along X instead, so it reads as an actual H; (2) the road
approaching the helipad ran all the way to dead-center of the pad, cutting
a visible line straight across the ring -- it now stops at the ring's edge
on the hub-facing side instead.

v4 fixed why only the dashed centerline was showing up and the two solid
edge lines were invisible in the v3 screenshot: offset_point_perpendicular()
always offset its first argument, but the per-waypoint list comprehension
called it inconsistently, so for a straight 2-point road the first and
last "edge" points came out identical -- a zero-length degenerate segment
that never actually rendered. Replaced with a proper offset_waypoints()
helper that offsets every waypoint correctly regardless of its position
in the list.

v5 fixes the real cause of the "climbing into the sky" look you confirmed
by selecting a road and testing rotation (0,0,0): positional
unreal.Rotator(pitch, yaw, 0.0) was NOT filling (Pitch, Yaw, Roll) the way
the keyword names suggest -- our yaw value (a real compass bearing, e.g.
23.48 deg for the Medical road) was landing in the Pitch slot, physically
tilting every box up at that angle, while our near-zero computed pitch
landed in Roll and did nothing useful, and our literal roll=0.0 ended up
in the actual Yaw slot -- so every road box pointed due "north" (yaw 0)
but pitched up by its own bearing angle instead. Fixed by constructing
the Rotator with explicit keywords (roll=, pitch=, yaw=) so there's no
positional ambiguity, and removed the old "-pitch" negation that was
compensating for the wrong slot in the wrong way.

v1 confirmed working (yellow tint material works, hub-and-spoke roads and
door caution stripes all placed correctly -- just weren't all visible in
the first screenshot's framing). This version replaces the single solid
center line per road with a real 2-lane road marking: a solid yellow
line down each outer edge, and a dashed yellow line down the middle.
Helipad ring/H and door caution stripes are unchanged from v1.

DELETES v1's road markings first (anything labeled "Marking_Road_*")
before rebuilding, so re-running this is safe and won't leave old
single-line roads behind. Helipad ring/H and caution stripes are left
alone (rebuilt fresh too, safe to re-run).

SLOPE: you mentioned the Garrison platform has a slope and want the
roads to follow it. I don't have real elevation data for that yet --
our earlier attempt to sample ground height via line traces from the
editor console was a dead end (the same broken trace pipeline that
returned zero hits on known-solid ground, unrelated to this project's
geometry). Each road below is built as a per-waypoint polyline in 3D
(not just flat XY), so once you give me real (x, y, z) waypoints along
whichever road segment(s) cross the slope, I can drop them straight
into ROAD_WAYPOINT_OVERRIDES below and every line (edges + dashes)
will tilt to match, because each sub-segment already computes its own
pitch from its start/end Z. Until then, every road is flat at Z=384
(HUB_Z) -- correct everywhere except wherever the real slope is.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_add_markings.py"
"""

import math
import unreal

# ---- Known coordinates ----
HELIPAD_CENTER = unreal.Vector(14362.0, 4533.0, 307.0)
HELIPAD_RADIUS = 3000.0
HELIPAD_TOP_Z = HELIPAD_CENTER.z + 51.0

BUILDINGS = [
    {"name": "Medical", "center": (9397.6, 6241.2), "door": (8816.8, 6453.5, 384.0)},
    {"name": "Barracks", "center": (3310.0, -1604.0), "door": (2764.5, -1147.0, 384.0)},
    {"name": "Armory", "center": (6893.0, 8733.0), "door": (6895.2, 8102.6, 384.0)},
    {"name": "Command", "center": (518.0, 5770.0), "door": (875.1, 5934.8, 384.0)},
    {"name": "Mess_Hall", "center": (318.0, 2854.0), "door": (870.8, 2890.4, 384.0)},
]

HUB_Z = 384.0  # flat road height -- was 382 (hub) / 380 (door), now uniform at your request

# name -> list of (x, y, z) waypoints overriding the default straight
# hub->door line. Leave empty for now; fill in once you give me real
# elevation samples along the sloped section(s).
ROAD_WAYPOINT_OVERRIDES = {
    # "Medical": [(4087.3, 4398.8, 384.0), (6500.0, 5300.0, 340.0), (8816.8, 6453.5, 384.0)],
}

# ---- Lane marking geometry ----
LANE_HALF_WIDTH_CM = 320.0   # centerline to each edge line -- doubled from 160
EDGE_LINE_WIDTH_CM = 32.0    # doubled from 16
CENTER_DASH_WIDTH_CM = 28.0  # doubled from 14
CENTER_DASH_LENGTH_CM = 70.0
CENTER_DASH_GAP_CM = 70.0
ROAD_THICKNESS_CM = 3.0

RING_WIDTH_CM = 40.0
RING_SEGMENTS = 32
RING_THICKNESS_CM = 2.0

H_HEIGHT_CM = 1600.0
H_BAR_WIDTH_CM = 200.0
H_THICKNESS_CM = 2.0

CAUTION_ZONE_WIDTH_CM = 320.0
CAUTION_ZONE_DEPTH_CM = 200.0
CAUTION_ZONE_OFFSET_CM = 150.0
CAUTION_BAR_SPACING_CM = 45.0
CAUTION_BAR_THICKNESS_CM = 35.0
CAUTION_Z = 383.0

MARKING_FOLDER = "Carrowgate Garrison/Markings"
COLOR_SOURCE_ACTOR_LABEL = "MechHanger_Placeholder"

YELLOW = unreal.LinearColor(1.0, 0.82, 0.0, 1.0)
BLACK = unreal.LinearColor(0.02, 0.02, 0.02, 1.0)

_material_cache = {}


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_actor_by_label(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsystem.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def delete_actors_with_label_prefix(prefix):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    to_delete = [a for a in subsystem.get_all_level_actors() if a.get_actor_label().startswith(prefix)]
    for a in to_delete:
        subsystem.destroy_actor(a)
    if to_delete:
        log(f"Removed {len(to_delete)} stale actor(s) labeled '{prefix}*' from a previous run.")


def get_source_material():
    actor = get_actor_by_label(COLOR_SOURCE_ACTOR_LABEL)
    if not actor:
        log(f"WARNING: couldn't find '{COLOR_SOURCE_ACTOR_LABEL}' -- falling back to the engine default basic shape material.")
        return unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
    mesh_comp = getattr(actor, "static_mesh_component", None) or actor.get_component_by_class(unreal.StaticMeshComponent)
    return mesh_comp.get_material(0)


def get_or_create_color_material(name, color):
    if name in _material_cache:
        return _material_cache[name]
    dest_path = f"/Game/LevelPrototyping/Garrison/Materials/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(dest_path):
        mi = unreal.load_asset(dest_path)
        _material_cache[name] = mi
        return mi

    source_mat = get_source_material()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = asset_tools.create_asset(name, "/Game/LevelPrototyping/Garrison/Materials", unreal.MaterialInstanceConstant, factory)
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, source_mat)

    succeeded = None
    for param_name in ["Color", "BaseColor", "Tint", "TintColor", "Base Color"]:
        try:
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, param_name, color)
            succeeded = param_name
            break
        except Exception:
            continue

    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    log(f"Material '{dest_path}': tint param {'set via ' + succeeded if succeeded else 'NOT SET (no matching parameter name found)'}.")
    _material_cache[name] = mi
    return mi


def spawn_box_3d(label, center3, yaw, pitch, dim_x, dim_y, dim_z, material):
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    location = unreal.Vector(center3[0], center3[1], center3[2])
    # Confirmed by you selecting a road in-editor: positional unreal.Rotator(pitch, yaw, 0.0)
    # was NOT landing our yaw value in the Yaw slot -- it landed in Pitch (23.48 deg for the
    # Medical road, which is exactly atan2(dy,dx) for hub->door, i.e. our *yaw*), while our
    # near-zero computed pitch landed in Roll, and our literal roll=0.0 landed in Yaw. That's
    # why resetting rotation to (0,0,0) made it lie flat -- it was zeroing out a real (wrong)
    # 23-degree pitch. Using explicit keywords removes the ambiguity.
    rotation = unreal.Rotator(roll=0.0, pitch=pitch, yaw=yaw)
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    if not actor:
        log(f"  FAILED to spawn '{label}'.")
        return None
    actor.set_actor_label(label)
    try:
        actor.set_folder_path(MARKING_FOLDER)
    except Exception:
        pass
    mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh_comp.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
    actor.set_actor_scale3d(unreal.Vector(dim_x / 100.0, dim_y / 100.0, dim_z / 100.0))
    if material:
        mesh_comp.set_material(0, material)
    return actor


def segment_yaw_pitch(p0, p1):
    dx, dy, dz = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
    horiz = math.sqrt(dx * dx + dy * dy)
    yaw = math.degrees(math.atan2(dy, dx))
    pitch = math.degrees(math.atan2(dz, horiz)) if horiz > 0.0001 else 0.0
    length3d = math.sqrt(dx * dx + dy * dy + dz * dz)
    return yaw, pitch, length3d


def offset_point_perpendicular(p0, p1, offset_cm):
    """Offsets p0 sideways (in the horizontal plane) relative to the p0->p1
    direction -- used to generate the two edge lines either side of a
    road's centerline."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    mag = math.sqrt(dx * dx + dy * dy)
    if mag < 0.0001:
        return p0
    perp_x, perp_y = -dy / mag, dx / mag
    return (p0[0] + perp_x * offset_cm, p0[1] + perp_y * offset_cm, p0[2])


def offset_waypoints(waypoints, offset_cm):
    """Offsets every waypoint in a polyline sideways by offset_cm, using the
    direction to its neighbor to pick which way is 'sideways'. The old
    version always offset waypoints[0] regardless of which index it was
    building, so for a straight 2-point road the first and last offset
    points came out identical -- a zero-length degenerate edge line that
    never actually rendered (only the dashed centerline did)."""
    n = len(waypoints)
    pts = []
    for i in range(n):
        p_this = waypoints[i]
        p_ref = waypoints[i + 1] if i < n - 1 else waypoints[i - 1]
        offset = offset_point_perpendicular(p_this, p_ref, offset_cm if i < n - 1 else -offset_cm)
        pts.append(offset)
    return pts


def spawn_polyline_solid(label_prefix, waypoints, width_cm, material):
    count = 0
    for i in range(len(waypoints) - 1):
        p0, p1 = waypoints[i], waypoints[i + 1]
        yaw, pitch, length3d = segment_yaw_pitch(p0, p1)
        mid = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0, (p0[2] + p1[2]) / 2.0)
        spawn_box_3d(f"{label_prefix}_{i:02d}", mid, yaw, pitch, length3d, width_cm, ROAD_THICKNESS_CM, material)
        count += 1
    return count


def spawn_polyline_dashed(label_prefix, waypoints, width_cm, dash_len, gap_len, material):
    count = 0
    leftover = 0.0  # carries partial dash/gap phase across waypoint segments so dashes look continuous
    on_dash = True
    for i in range(len(waypoints) - 1):
        p0, p1 = waypoints[i], waypoints[i + 1]
        yaw, pitch, length3d = segment_yaw_pitch(p0, p1)
        if length3d < 0.0001:
            continue
        dir3 = ((p1[0] - p0[0]) / length3d, (p1[1] - p0[1]) / length3d, (p1[2] - p0[2]) / length3d)

        pos = 0.0
        remaining = length3d - leftover if on_dash else length3d
        # Simplify: just restart dash phase cleanly at each waypoint (visually fine, avoids fiddly cross-segment math)
        pos = 0.0
        while pos < length3d:
            seg_len = min(dash_len, length3d - pos)
            if seg_len > 1.0:
                start_t = pos
                end_t = pos + seg_len
                start_pt = (p0[0] + dir3[0] * start_t, p0[1] + dir3[1] * start_t, p0[2] + dir3[2] * start_t)
                end_pt = (p0[0] + dir3[0] * end_t, p0[1] + dir3[1] * end_t, p0[2] + dir3[2] * end_t)
                mid = ((start_pt[0] + end_pt[0]) / 2.0, (start_pt[1] + end_pt[1]) / 2.0, (start_pt[2] + end_pt[2]) / 2.0)
                spawn_box_3d(f"{label_prefix}_{i:02d}_{count:03d}", mid, yaw, pitch, seg_len, width_cm, ROAD_THICKNESS_CM, material)
                count += 1
            pos += dash_len + gap_len
    return count


def build_lane_road(name, waypoints, yellow_mat):
    delete_actors_with_label_prefix(f"Marking_Road_{name}")
    left_pts = offset_waypoints(waypoints, -LANE_HALF_WIDTH_CM)
    right_pts = offset_waypoints(waypoints, LANE_HALF_WIDTH_CM)

    n_left = spawn_polyline_solid(f"Marking_Road_{name}_EdgeL", left_pts, EDGE_LINE_WIDTH_CM, yellow_mat)
    n_right = spawn_polyline_solid(f"Marking_Road_{name}_EdgeR", right_pts, EDGE_LINE_WIDTH_CM, yellow_mat)
    n_dash = spawn_polyline_dashed(f"Marking_Road_{name}_Center", waypoints, CENTER_DASH_WIDTH_CM,
                                    CENTER_DASH_LENGTH_CM, CENTER_DASH_GAP_CM, yellow_mat)
    log(f"  [{name}] road: {n_left} left-edge + {n_right} right-edge + {n_dash} center-dash segment(s).")


# Half-size of the "Parade Square" loop, centered on the hub. Buildings are
# nearly always farther from the hub than this in at least one axis, so
# every building connects to the loop via a right-angle spur rather than
# sitting on the loop itself -- matches your sketch (a compact square with
# spurs reaching out to each building) rather than one huge loop stretched
# out to touch every door.
LOOP_HALF_X = 1600.0
LOOP_HALF_Y = 1300.0


def compute_loop_corners(hub):
    min_x, max_x = hub[0] - LOOP_HALF_X, hub[0] + LOOP_HALF_X
    min_y, max_y = hub[1] - LOOP_HALF_Y, hub[1] + LOOP_HALF_Y
    z = hub[2]
    return {
        "min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y,
        "NW": (min_x, max_y, z), "NE": (max_x, max_y, z),
        "SE": (max_x, min_y, z), "SW": (min_x, min_y, z),
    }


def compute_spur_waypoints(target_point, loop, hub):
    """Builds a right-angle (Manhattan) path from a point outside the loop
    to the loop's boundary, always axis-aligned -- either one straight
    segment (when the point's cross-axis coordinate already falls within
    the loop's range on the near edge) or a single 90-degree bend (when it
    doesn't)."""
    tx, ty, tz = target_point
    dx = tx - hub[0]
    dy = ty - hub[1]

    if abs(dx) >= abs(dy):
        edge_x = loop["max_x"] if dx >= 0 else loop["min_x"]
        if loop["min_y"] <= ty <= loop["max_y"]:
            return [target_point, (edge_x, ty, tz)]
        attach_y = loop["max_y"] if ty > hub[1] else loop["min_y"]
        return [target_point, (tx, attach_y, tz), (edge_x, attach_y, tz)]
    else:
        edge_y = loop["max_y"] if dy >= 0 else loop["min_y"]
        if loop["min_x"] <= tx <= loop["max_x"]:
            return [target_point, (tx, edge_y, tz)]
        attach_x = loop["max_x"] if tx > hub[0] else loop["min_x"]
        return [target_point, (attach_x, ty, tz), (attach_x, edge_y, tz)]


def build_roads(yellow_mat):
    log("---- Roads (orthogonal Parade Square + right-angle spurs) ----")
    centroid_x = sum(b["center"][0] for b in BUILDINGS) / len(BUILDINGS)
    centroid_y = sum(b["center"][1] for b in BUILDINGS) / len(BUILDINGS)
    hub = (centroid_x, centroid_y, HUB_Z)
    loop = compute_loop_corners(hub)
    log(f"Hub point: ({hub[0]:.1f}, {hub[1]:.1f}, {hub[2]:.1f})  "
        f"Loop: X[{loop['min_x']:.0f},{loop['max_x']:.0f}] Y[{loop['min_y']:.0f},{loop['max_y']:.0f}]")

    # The loop itself, as 4 independent straight edges (each is its own
    # clean 2-point lane road -- simpler and more robust than trying to
    # offset one closed 5-point polyline, which would need special-casing
    # the shared start/end corner).
    build_lane_road("LoopNorth", [loop["NW"], loop["NE"]], yellow_mat)
    build_lane_road("LoopEast", [loop["NE"], loop["SE"]], yellow_mat)
    build_lane_road("LoopSouth", [loop["SE"], loop["SW"]], yellow_mat)
    build_lane_road("LoopWest", [loop["SW"], loop["NW"]], yellow_mat)

    # Each building connects to the loop with a right-angle spur.
    for b in BUILDINGS:
        default_waypoints = compute_spur_waypoints(b["door"], loop, hub)
        waypoints = ROAD_WAYPOINT_OVERRIDES.get(b["name"], default_waypoints)
        build_lane_road(b["name"], waypoints, yellow_mat)

    build_trunk_spine(yellow_mat, hub, loop)


# The main north-south trunk road, per your sketch: a separate through-road
# (not connected to the Parade Square loop) that comes down from the
# platform's north side and forks -- one branch to the helipad, one
# (not built yet, see note below) toward the boat/crane parking area.
# TRUNK_X sits east of the loop, roughly under the Armory/crossroads area
# based on the building survey -- adjust here if it doesn't line up with
# where the real crossroads structure is once you see it rendered.
TRUNK_X_OFFSET_FROM_LOOP = 1500.0
TRUNK_NORTH_OFFSET = 3000.0   # how far north of the branch point the trunk starts
TRUNK_BRANCH_Y_OFFSET = 0.0   # branch point's Y relative to hub; 0 = level with hub


def build_trunk_spine(yellow_mat, hub, loop):
    log("---- Trunk spine (separate from the loop) + helipad branch ----")
    trunk_x = loop["max_x"] + TRUNK_X_OFFSET_FROM_LOOP
    branch_y = hub[1] + TRUNK_BRANCH_Y_OFFSET
    trunk_north_y = branch_y + TRUNK_NORTH_OFFSET
    branch_point = (trunk_x, branch_y, hub[2])
    trunk_start = (trunk_x, trunk_north_y, hub[2])

    trunk_waypoints = ROAD_WAYPOINT_OVERRIDES.get("Trunk", [trunk_start, branch_point])
    build_lane_road("Trunk", trunk_waypoints, yellow_mat)

    # Helipad branch off the trunk's branch point -- a right-angle path,
    # independent of the loop entirely.
    dir_x = HELIPAD_CENTER.x - branch_point[0]
    dir_y = HELIPAD_CENTER.y - branch_point[1]
    dir_mag = math.sqrt(dir_x * dir_x + dir_y * dir_y)
    if dir_mag > 0.0001:
        ring_edge = (HELIPAD_CENTER.x - (dir_x / dir_mag) * HELIPAD_RADIUS,
                     HELIPAD_CENTER.y - (dir_y / dir_mag) * HELIPAD_RADIUS,
                     hub[2])
    else:
        ring_edge = (HELIPAD_CENTER.x, HELIPAD_CENTER.y, hub[2])
    heli_default = [branch_point, (ring_edge[0], branch_point[1], hub[2]), ring_edge]
    heli_waypoints = ROAD_WAYPOINT_OVERRIDES.get("Helipad", heli_default)
    build_lane_road("Helipad", heli_waypoints, yellow_mat)

    # Parking branch (toward the boat/crane) -- not built yet, no real
    # coordinates for that spot. Once you drop a reference actor there and
    # give me its Location, add a "Parking" entry to ROAD_WAYPOINT_OVERRIDES
    # (or tell me the numbers) and I'll branch it off branch_point the same
    # way as the helipad branch above.
    log(f"  Trunk branch point: ({branch_point[0]:.1f}, {branch_point[1]:.1f}, {branch_point[2]:.1f}) -- "
        f"Parking branch not built yet, still need real coordinates for that spot.")


def build_helipad(yellow_mat):
    log("---- Helipad ring + H ----")
    delete_actors_with_label_prefix("Marking_HelipadRing_")
    delete_actors_with_label_prefix("Marking_Helipad_H_")

    for i in range(RING_SEGMENTS):
        a0 = (2.0 * math.pi * i) / RING_SEGMENTS
        a1 = (2.0 * math.pi * (i + 1)) / RING_SEGMENTS
        p0 = (HELIPAD_CENTER.x + HELIPAD_RADIUS * math.cos(a0), HELIPAD_CENTER.y + HELIPAD_RADIUS * math.sin(a0))
        p1 = (HELIPAD_CENTER.x + HELIPAD_RADIUS * math.cos(a1), HELIPAD_CENTER.y + HELIPAD_RADIUS * math.sin(a1))
        mid = ((p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        seg_len = math.sqrt(dx * dx + dy * dy) * 1.15
        yaw = math.degrees(math.atan2(dy, dx))
        spawn_box_3d(f"Marking_HelipadRing_{i:02d}", (mid[0], mid[1], HELIPAD_TOP_Z), yaw, 0.0, seg_len, RING_WIDTH_CM, RING_THICKNESS_CM, yellow_mat)
    log(f"  Ring: {RING_SEGMENTS} segments placed.")

    # Each leg runs along Y (vertical stroke, length H_HEIGHT_CM) and the two
    # legs sit apart along X. The old version offset both legs along Y --
    # the same axis as their own length -- so they landed on top of the
    # crossbar in the middle and rendered as a "+", not an "H".
    H_STROKE_WIDTH_CM = 60.0
    H_LEG_GAP_CM = 500.0
    leg_offset_x = H_LEG_GAP_CM / 2.0
    spawn_box_3d("Marking_Helipad_H_Left", (HELIPAD_CENTER.x - leg_offset_x, HELIPAD_CENTER.y, HELIPAD_TOP_Z), 0.0, 0.0,
                 H_STROKE_WIDTH_CM, H_HEIGHT_CM, H_THICKNESS_CM, yellow_mat)
    spawn_box_3d("Marking_Helipad_H_Right", (HELIPAD_CENTER.x + leg_offset_x, HELIPAD_CENTER.y, HELIPAD_TOP_Z), 0.0, 0.0,
                 H_STROKE_WIDTH_CM, H_HEIGHT_CM, H_THICKNESS_CM, yellow_mat)
    spawn_box_3d("Marking_Helipad_H_Bar", (HELIPAD_CENTER.x, HELIPAD_CENTER.y, HELIPAD_TOP_Z), 0.0, 0.0,
                 H_LEG_GAP_CM + H_STROKE_WIDTH_CM, H_STROKE_WIDTH_CM, H_THICKNESS_CM, yellow_mat)
    log("  'H' placed.")


def build_caution_stripes(yellow_mat, black_mat):
    log("---- Door caution stripes ----")
    for b in BUILDINGS:
        name = b["name"]
        delete_actors_with_label_prefix(f"Marking_Caution_{name}_")
        cx, cy = b["center"]
        dx_door, dy_door, dz_door = b["door"]

        dir_x = dx_door - cx
        dir_y = dy_door - cy
        mag = math.sqrt(dir_x * dir_x + dir_y * dir_y)
        if mag < 1.0:
            log(f"  [{name}] SKIPPED -- door essentially at building center.")
            continue
        dir_x /= mag
        dir_y /= mag
        facing_yaw = math.degrees(math.atan2(dir_y, dir_x))

        zone_center_x = dx_door + dir_x * (CAUTION_ZONE_OFFSET_CM + CAUTION_ZONE_DEPTH_CM / 2.0)
        zone_center_y = dy_door + dir_y * (CAUTION_ZONE_OFFSET_CM + CAUTION_ZONE_DEPTH_CM / 2.0)

        num_bars = int(CAUTION_ZONE_DEPTH_CM // CAUTION_BAR_SPACING_CM) + 2
        bar_yaw = facing_yaw + 45.0
        bar_length = CAUTION_ZONE_WIDTH_CM * 1.6

        for i in range(num_bars):
            offset = -CAUTION_ZONE_DEPTH_CM / 2.0 + i * CAUTION_BAR_SPACING_CM
            bar_x = zone_center_x + dir_x * offset
            bar_y = zone_center_y + dir_y * offset
            mat = yellow_mat if i % 2 == 0 else black_mat
            color_name = "Y" if i % 2 == 0 else "B"
            spawn_box_3d(f"Marking_Caution_{name}_{i:02d}{color_name}", (bar_x, bar_y, CAUTION_Z), bar_yaw, 0.0,
                         bar_length, CAUTION_BAR_THICKNESS_CM, ROAD_THICKNESS_CM, mat)

        log(f"  [{name}] {num_bars} caution bars placed.")


def main():
    yellow_mat = get_or_create_color_material("MI_Marking_Yellow", YELLOW)
    black_mat = get_or_create_color_material("MI_Marking_Black", BLACK)

    build_roads(yellow_mat)
    build_helipad(yellow_mat)
    build_caution_stripes(yellow_mat, black_mat)

    log("Done. Everything is under the 'Carrowgate Garrison/Markings' Outliner folder, prefixed 'Marking_'. "
        "Roads are still flat (no real slope data yet) except wherever you've added entries to "
        "ROAD_WAYPOINT_OVERRIDES. Review in the editor, then save the level (Ctrl+S).")


main()
