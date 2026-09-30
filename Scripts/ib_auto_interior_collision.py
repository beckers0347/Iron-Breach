"""
IBPY: ib_auto_interior_collision.py  (v3 -- trace-based)

Auto-generates a simple interior collision shell (walls, floor, ceiling) for
a garrison building, using LINE TRACES against the actual imported Tripo3D
exterior mesh geometry to find each wall's real surface distance, instead of
trusting the mesh's full bounding box.

WHY: the full bounding box approach (v1/v2) kept producing shells that were
either offset/rotated relative to the mesh (fixed by using local, not world,
bounds) or just loose/oversized on one or more sides, because these Tripo3D
meshes have external decoration (antennas, dishes, vents) that skews the
naive bounding box well past the actual walkable wall surface -- sometimes
by a meter or more, which is exactly why a player couldn't walk up to a
door. Bounding-box math can't tell a real wall from a decorative antenna
sticking out sideways; a physical trace against the mesh can.

HOW IT WORKS:
  1. Temporarily enables collision (QUERY_ONLY) on the exterior mesh so we
     can trace against it, and restores NO_COLLISION when done -- the
     visual mesh is never left with gameplay collision.
  2. For each of the 4 local cardinal directions (+X/-X/+Y/-Y in the
     building's own unrotated frame), fires several parallel rays at a
     human-height sample line and takes the MEDIAN hit distance. Median
     (not min/max) is what makes this robust to a single antenna, vent, or
     dish throwing off one or two rays -- most rays hit the real flat wall.
  3. Finds which wall the door is actually embedded in by tracing short
     rays outward from the DOOR'S OWN location in all 4 local directions --
     whichever direction hits almost immediately is the wall the door sits
     in. (Earlier versions tried to infer this from the door actor's own
     rotation, then from its position ratio to the bounding box -- both
     turned out unreliable; a direct trace from the door itself is not.)
  4. Builds the shell (floor/ceiling/4 walls, one split around the door
     gap) from these measured, possibly-asymmetric distances rather than a
     single symmetric extent.

This does NOT touch the visual exterior mesh at all -- it only adds
invisible BlockingVolume collision so the player can walk inside without
clipping through the solid Tripo3D shell. Run once per building.

HOW TO RUN:
  1. Edit the BUILDINGS list below -- one entry per building you've
     already imported a Tripo3D mesh for.
  2. In the Unreal Editor Python console (the "Cmd" input bar at the
     bottom of the editor), run:
       py "X:\IronBreach\Scripts\ib_auto_interior_collision.py"
  3. Check the log (search "IBPY:" in Output Log or Saved/Logs) for a
     per-building report, then look at the result in the viewport.
  4. Nothing is saved automatically -- review first, then save the level
     yourself once you're happy with it.
"""

import unreal
import math
import statistics

BUILDINGS = [
    {
        "prefix": "07_Armory",
        "exterior_actor": "SM_Armory_Tripo",
        "door_actor": "07_Armory_DoorFrame",
        # Armory has a deep open archway/breezeway at its front, with a
        # raised step/platform sitting right inside it. Wall-distance
        # tracing at door height consistently clips that step from most
        # sample angles, collapsing that whole side of the shell down to
        # ~65cm regardless of the archway-vs-real-wall sanity check. This
        # building's actual mesh bounding box (used successfully earlier)
        # is the safer source of truth for sizing here; only the new
        # trace-from-the-door method (used for every building, below) is
        # needed to fix its door-wall selection reliability.
        "sizing_method": "bbox",
    },
    {
        "prefix": "08_Command & Comms",
        "exterior_actor": "SM_Command_Tripo",
        "door_actor": "08_Command & Comms_DoorFrame",
        # Command's interior is an octagonal room (clear from directly
        # above), plus a radar dish and equipment pod mounted on the
        # OUTSIDE of the tower. Axis-aligned tracing only lines up with the
        # door-facing facet (-X); the other 3 directions graze past the
        # octagon's angled walls at every height tried and fall back to the
        # decoration-inflated mesh bbox, producing the oversized cage
        # reported by screenshot. Live tracing for this building also
        # proved flaky run-to-run (editor physics-scene timing right after
        # toggling collision on), so rather than depend on that, this uses
        # -X's distance -- reproduced identically across 6+ separate runs
        # before tracing got flaky -- as a fixed, verified value applied
        # symmetrically to all four sides -- but the room is a regular
        # OCTAGON (confirmed by the top-down screenshot), not a square, so
        # a single symmetric box still clips through the angled walls /
        # leaves gaps at the corners depending on how it's sized. Reported
        # by screenshot as "too square". sizing_method=octagon builds 8
        # correctly-angled wall segments (one per facet) instead of 4,
        # using this same verified 756.5cm apothem.
        "sizing_method": "octagon",
        "uniform_distance_cm": 756.5,
        # The octagon shell above only covers the walkable room itself. The
        # radar dish and equipment pod are mounted OUTSIDE that octagon,
        # further out than its ~756cm apothem but still well within the
        # mesh's own raw bounding box (~1460cm x ~860cm) -- confirmed by a
        # top-down screenshot showing the collision wireframe stopping well
        # short of both the dish cluster and the side pod. Since the
        # exterior mesh has NO_COLLISION everywhere, that whole outer
        # margin was completely walk/see-through despite looking solid.
        # outer_cap=True adds a second, separate ring of thin walls at the
        # mesh's TRUE bbox surface (build_outer_cap_shell) without touching
        # the octagon shell at all, so the room a player actually walks
        # through still follows the real octagon shape -- this only plugs
        # the gap so nothing solid-looking is left uncollided.
        "outer_cap": True,
    },
    {
        "prefix": "06_Mess Hall",
        "exterior_actor": "SM_MessHall_Tripo",
        "door_actor": "06_Mess Hall_DoorFrame",
        # Mess Hall's shell was built with an earlier, cruder version of
        # this script (oversized/offset relative to the mesh, reported by
        # screenshot). First rebuild attempt here with trace-based sizing
        # showed a NEW failure mode: the +X trace found some opening/gap in
        # the mesh and sailed clean through to hit something ~3015cm away
        # (vs. the mesh's own bbox half-extent of only ~1471cm) -- the
        # existing archway sanity check only guards against traces coming
        # back TOO SHORT, not too long, so this overshoot slipped through
        # and produced exactly the oversized cage reported. Falling back to
        # plain bbox sizing here too, same as Armory.
        "sizing_method": "bbox",
    },
    # Barracks already has a shell built with this trace-based version's
    # predecessor and isn't reported as broken -- leave commented out so
    # re-running this script doesn't spawn duplicate, overlapping
    # BlockingVolumes for it. Uncomment if it turns out to need the same
    # tightening treatment.
    # {
    #     "prefix": "05_Barracks",
    #     "exterior_actor": "SM_Barracks_Tripo",
    #     "door_actor": "05_Barracks_DoorFrame",
    # },
    # Main Gate is a drive-through checkpoint, not an enclosed room -- the
    # existing Pylon_L/Pylon_R/Lintel actors are the real collision there,
    # so it intentionally does NOT get an interior BlockingVolume shell.
    # {
    #     "prefix": "01_Main Gate",
    #     "exterior_actor": "SM_Checkpoint_Tripo",
    #     "door_actor": "01_Main Gate_DoorFrame",
    # },
]

WALL_THICKNESS_CM = 30.0
FLOOR_THICKNESS_CM = 20.0
CEILING_THICKNESS_CM = 20.0
DOOR_GAP_WIDTH_CM = 220.0
DOOR_GAP_HEIGHT_CM = 280.0

# How far in from the traced wall surface to place the actual collision
# wall's centerline -- just enough for the wall's own half-thickness plus a
# small buffer so it doesn't visually poke through the real mesh surface.
WALL_BUFFER_CM = 25.0

TRACE_START_DIST_CM = 4000.0   # comfortably outside any building
TRACE_SAMPLE_COUNT = 9         # parallel rays per wall direction
TRACE_HEIGHT_ABOVE_FLOOR_CM = 150.0  # roughly door/chest height -- used for the door probe
TRACE_HEIGHT_CANDIDATES_CM = [150.0, 350.0, 600.0, 900.0, 1300.0, 1800.0]  # tried in order for wall-distance tracing
TRACE_PERP_HALF_SPAN_RATIO = 0.7    # sample width as a fraction of the mesh's own half-extent on that axis, so samples stay within the wall and don't wrap around a corner

TRACE_CHANNEL = unreal.TraceTypeQuery.TRACE_TYPE_QUERY1


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_actor_by_label(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsystem.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def rotate_vector_yaw(v, yaw_degrees):
    rad = math.radians(yaw_degrees)
    c = math.cos(rad)
    s = math.sin(rad)
    return unreal.Vector(v.x * c - v.y * s, v.x * s + v.y * c, v.z)


def unrotate_vector_yaw(v, yaw_degrees):
    return rotate_vector_yaw(v, -yaw_degrees)


def spawn_blocking_volume(name, location, rotation, box_extent, folder):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    volume = subsystem.spawn_actor_from_class(unreal.BlockingVolume, location, rotation)
    volume.set_actor_label(name)
    volume.set_folder_path(folder)
    scale = unreal.Vector(box_extent.x / 100.0, box_extent.y / 100.0, box_extent.z / 100.0)
    volume.set_actor_scale3d(scale)
    return volume


def line_trace(world, start, end, ignore_actors):
    hit = unreal.SystemLibrary.line_trace_single(
        world, start, end, TRACE_CHANNEL, True, ignore_actors,
        unreal.DrawDebugTrace.NONE, True,
    )
    if hit and hit.to_dict().get("blocking_hit"):
        return hit.to_dict()
    return None


def trace_wall_distance(world, actor_loc, actor_yaw, local_dir, local_perp, perp_half_span, height_world_z, ignore_actors):
    """Fire TRACE_SAMPLE_COUNT parallel rays along local_dir (a unit vector
    in the building's local XY frame) at height_world_z, spread across
    perp_half_span along local_perp, and return the MEDIAN distance (in
    local space, from the actor's own origin) to whatever they hit."""
    hits = []
    for i in range(TRACE_SAMPLE_COUNT):
        t = -1.0 + 2.0 * i / (TRACE_SAMPLE_COUNT - 1)
        perp_offset = t * perp_half_span
        start_local = unreal.Vector(
            local_dir.x * TRACE_START_DIST_CM + local_perp.x * perp_offset,
            local_dir.y * TRACE_START_DIST_CM + local_perp.y * perp_offset,
            0.0,
        )
        end_local = unreal.Vector(
            local_perp.x * perp_offset,
            local_perp.y * perp_offset,
            0.0,
        )
        start_world = actor_loc + rotate_vector_yaw(start_local, actor_yaw)
        start_world.z = height_world_z
        end_world = actor_loc + rotate_vector_yaw(end_local, actor_yaw)
        end_world.z = height_world_z

        hit = line_trace(world, start_world, end_world, ignore_actors)
        if hit:
            # distance along local_dir from actor origin to the hit point
            hit_local = unrotate_vector_yaw(hit["location"] - actor_loc, actor_yaw)
            dist = hit_local.x * local_dir.x + hit_local.y * local_dir.y
            if dist > 10.0:
                hits.append(dist)

    if not hits:
        return None, 0, 0
    return statistics.median(hits), len(hits), max(hits)


def trace_wall_distance_multi_height(world, actor_loc, actor_yaw, local_dir, local_perp, perp_half_span, floor_z_world, ignore_actors):
    """Some buildings (Command & Comms, notably) have geometry that isn't
    uniform with height on every side -- a radar dish or equipment pod
    attached partway up a tower shaft, for instance, doesn't necessarily
    have anything solid at door height (150cm) directly beneath it, so a
    single-height trace sails clean through to nothing and falls back to
    the full decorative bounding box (which is how the dish/pod tip ends
    up dictating the wall position instead of the tower's real wall).
    Try several heights up the building and use whichever one actually
    finds a wall with the most confidence (most rays hitting something),
    preferring the lowest such height since that's most likely the real,
    continuous wall rather than a stray higher-up piece of geometry."""
    best = (None, 0, 0)
    for height_offset in TRACE_HEIGHT_CANDIDATES_CM:
        height_world_z = floor_z_world + height_offset
        result = trace_wall_distance(world, actor_loc, actor_yaw, local_dir, local_perp, perp_half_span, height_world_z, ignore_actors)
        median, count, mx = result
        if median is not None and count >= TRACE_SAMPLE_COUNT * 0.5:
            return result
        if count > best[1]:
            best = result
    return best


def trace_door_wall(world, actor_loc, actor_yaw, door_loc, height_world_z, ignore_actors, probe_dist=600.0):
    """Fire a short trace outward from the DOOR'S OWN location in each of
    the 4 local cardinal directions. Whichever direction hits almost
    immediately is the wall the door is actually embedded in -- this is
    far more reliable than inferring it from the door actor's own rotation
    (inconsistent across placed doors) or its position ratio to the
    bounding box (fails when a door happens to sit close to local center,
    as seen on Armory)."""
    directions = [
        ("X", 1, unreal.Vector(1, 0, 0)),
        ("X", -1, unreal.Vector(-1, 0, 0)),
        ("Y", 1, unreal.Vector(0, 1, 0)),
        ("Y", -1, unreal.Vector(0, -1, 0)),
    ]
    best = None
    results = []
    for axis, sign, local_dir in directions:
        start_local = unreal.Vector(0, 0, 0)
        end_local = unreal.Vector(local_dir.x * probe_dist, local_dir.y * probe_dist, 0)
        start_world = unreal.Vector(door_loc.x, door_loc.y, height_world_z)
        end_world = actor_loc + rotate_vector_yaw(
            unrotate_vector_yaw(door_loc - actor_loc, actor_yaw) + end_local, actor_yaw
        )
        end_world.z = height_world_z
        hit = line_trace(world, start_world, end_world, ignore_actors)
        dist = hit["distance"] if hit else None
        results.append((axis, sign, dist))
        if dist is not None and (best is None or dist < best[2]):
            best = (axis, sign, dist)

    log(f"    Door probe results: {results}")
    if best is None:
        return None
    return (best[0], best[1])


def build_outer_cap_shell(building, door, actor_loc, actor_rot, actor_yaw, floor_z_world, ceiling_z_world,
                           dist_pos_x, dist_neg_x, dist_pos_y, dist_neg_y, door_axis, door_sign):
    """Adds a SECOND, separate ring of thin walls at the mesh's true raw
    bounding-box surface, in addition to (not replacing) a tighter interior
    shell already built for this building (e.g. the octagon room). Some
    buildings have decoration -- a radar dish, an equipment pod -- mounted
    OUTSIDE the walkable room but still solidly part of the visual mesh;
    since the exterior mesh has NO_COLLISION everywhere, any part of it not
    covered by SOME BlockingVolume is fully walk/see-through no matter how
    solid it looks. This doesn't need a tight fit or to match the room's
    real shape -- it's not walkable space, there's no door into it
    specifically -- it only needs to exist so nothing solid-looking is left
    uncollided. The one thing it does need to get right is the door gap:
    it's split around the SAME door actor's position as the interior shell,
    on the same wall axis/sign already determined for that shell, so the
    real doorway stays open all the way through both layers rather than
    trapping the player between them."""
    prefix = building["prefix"]
    folder = f"CarrowGateGarrison/{prefix}/InteriorCollision"

    door_loc = door.get_actor_location()
    local_door = unrotate_vector_yaw(door_loc - actor_loc, actor_yaw)

    outer_buffer = 5.0  # just enough that this ring doesn't z-fight the true mesh surface
    in_pos_x = max(dist_pos_x - outer_buffer, 50.0)
    in_neg_x = max(dist_neg_x - outer_buffer, 50.0)
    in_pos_y = max(dist_pos_y - outer_buffer, 50.0)
    in_neg_y = max(dist_neg_y - outer_buffer, 50.0)

    local_center_x = (in_pos_x - in_neg_x) / 2.0
    local_center_y = (in_pos_y - in_neg_y) / 2.0
    in_extent_x = (in_pos_x + in_neg_x) / 2.0
    in_extent_y = (in_pos_y + in_neg_y) / 2.0

    full_height = max(ceiling_z_world - floor_z_world, 100.0)
    center_z_local = (floor_z_world - actor_loc.z) + (full_height / 2.0)

    def spawn_local(name, local_pos, local_half_extent):
        world_pos = actor_loc + rotate_vector_yaw(local_pos, actor_yaw)
        spawn_blocking_volume(name, world_pos, actor_rot, local_half_extent, folder)

    walls = [
        ("N", "Y", 1, in_pos_y),
        ("S", "Y", -1, in_neg_y),
        ("E", "X", 1, in_pos_x),
        ("W", "X", -1, in_neg_x),
    ]

    for wall_name, axis, sign, wall_dist in walls:
        is_door_wall = (axis == door_axis and sign == door_sign)

        if axis == "X":
            wall_center_local = unreal.Vector(local_center_x + sign * (wall_dist - WALL_THICKNESS_CM / 2.0), local_center_y, center_z_local)
            wall_extent = unreal.Vector(WALL_THICKNESS_CM / 2.0, in_extent_y, full_height / 2.0)
        else:
            wall_center_local = unreal.Vector(local_center_x, local_center_y + sign * (wall_dist - WALL_THICKNESS_CM / 2.0), center_z_local)
            wall_extent = unreal.Vector(in_extent_x, WALL_THICKNESS_CM / 2.0, full_height / 2.0)

        if not is_door_wall:
            spawn_local(f"{prefix}_Collision_Outer_{wall_name}", wall_center_local, wall_extent)
            continue

        log(f"[{prefix}] Outer wall {wall_name} faces the door -- splitting with a {DOOR_GAP_WIDTH_CM}cm gap.")

        if axis == "X":
            gap_center = local_door.y
            seg_len_a = max((gap_center - (local_center_y - in_extent_y)) - (DOOR_GAP_WIDTH_CM / 2.0), 0.0)
            seg_len_b = max(((local_center_y + in_extent_y) - gap_center) - (DOOR_GAP_WIDTH_CM / 2.0), 0.0)
            if seg_len_a > 10.0:
                seg_a_center_y = (local_center_y - in_extent_y) + (seg_len_a / 2.0)
                spawn_local(
                    f"{prefix}_Collision_Outer_{wall_name}_A",
                    unreal.Vector(wall_center_local.x, seg_a_center_y, center_z_local),
                    unreal.Vector(WALL_THICKNESS_CM / 2.0, seg_len_a / 2.0, full_height / 2.0),
                )
            if seg_len_b > 10.0:
                seg_b_center_y = (local_center_y + in_extent_y) - (seg_len_b / 2.0)
                spawn_local(
                    f"{prefix}_Collision_Outer_{wall_name}_B",
                    unreal.Vector(wall_center_local.x, seg_b_center_y, center_z_local),
                    unreal.Vector(WALL_THICKNESS_CM / 2.0, seg_len_b / 2.0, full_height / 2.0),
                )
            header_z = center_z_local + (full_height / 2.0) - ((full_height - DOOR_GAP_HEIGHT_CM) / 2.0) / 2.0
            spawn_local(
                f"{prefix}_Collision_Outer_{wall_name}_Header",
                unreal.Vector(wall_center_local.x, gap_center, header_z),
                unreal.Vector(WALL_THICKNESS_CM / 2.0, DOOR_GAP_WIDTH_CM / 2.0, (full_height - DOOR_GAP_HEIGHT_CM) / 4.0),
            )
        else:
            gap_center = local_door.x
            seg_len_a = max((gap_center - (local_center_x - in_extent_x)) - (DOOR_GAP_WIDTH_CM / 2.0), 0.0)
            seg_len_b = max(((local_center_x + in_extent_x) - gap_center) - (DOOR_GAP_WIDTH_CM / 2.0), 0.0)
            if seg_len_a > 10.0:
                seg_a_center_x = (local_center_x - in_extent_x) + (seg_len_a / 2.0)
                spawn_local(
                    f"{prefix}_Collision_Outer_{wall_name}_A",
                    unreal.Vector(seg_a_center_x, wall_center_local.y, center_z_local),
                    unreal.Vector(seg_len_a / 2.0, WALL_THICKNESS_CM / 2.0, full_height / 2.0),
                )
            if seg_len_b > 10.0:
                seg_b_center_x = (local_center_x + in_extent_x) - (seg_len_b / 2.0)
                spawn_local(
                    f"{prefix}_Collision_Outer_{wall_name}_B",
                    unreal.Vector(seg_b_center_x, wall_center_local.y, center_z_local),
                    unreal.Vector(seg_len_b / 2.0, WALL_THICKNESS_CM / 2.0, full_height / 2.0),
                )
            header_z = center_z_local + (full_height / 2.0) - ((full_height - DOOR_GAP_HEIGHT_CM) / 2.0) / 2.0
            spawn_local(
                f"{prefix}_Collision_Outer_{wall_name}_Header",
                unreal.Vector(gap_center, wall_center_local.y, header_z),
                unreal.Vector(DOOR_GAP_WIDTH_CM / 2.0, WALL_THICKNESS_CM / 2.0, (full_height - DOOR_GAP_HEIGHT_CM) / 4.0),
            )

    log(f"[{prefix}] Outer cap shell built at true mesh bbox (+X={dist_pos_x:.1f} -X={dist_neg_x:.1f} +Y={dist_pos_y:.1f} -Y={dist_neg_y:.1f}).")


def build_octagon_shell(building, exterior, door, mesh_comp, actor_loc, actor_rot, actor_yaw, floor_z_world, ceiling_z_world,
                         bbox_dist_pos_x=None, bbox_dist_neg_x=None, bbox_dist_pos_y=None, bbox_dist_neg_y=None):
    """Builds an 8-sided (regular octagon) interior collision shell instead
    of the usual 4-wall box -- for a room like Command & Comms' that is
    visibly octagonal from directly above, a rectangular box either clips
    through the angled walls (if sized tight) or leaves big triangular gaps
    at the corners (if sized to circumscribe it), which is exactly the
    "too square" complaint. This uses building["uniform_distance_cm"] as
    the apothem (perpendicular distance from center to every facet, since
    a REGULAR octagon has all 8 faces equidistant from its center) and
    builds one thin, correctly-angled wall segment per facet, splitting
    whichever one faces the door around a gap the same way the rectangular
    path splits its door wall."""
    prefix = building["prefix"]
    apothem = building["uniform_distance_cm"]

    world = unreal.EditorLevelLibrary.get_editor_world()
    orig_collision = mesh_comp.get_collision_enabled()
    mesh_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    ignore_actors = [exterior]
    try:
        trace_height_world_z = floor_z_world + TRACE_HEIGHT_ABOVE_FLOOR_CM
        door_loc = door.get_actor_location()
        door_result = trace_door_wall(world, actor_loc, actor_yaw, door_loc, trace_height_world_z, ignore_actors)
    finally:
        mesh_comp.set_collision_enabled(orig_collision)

    local_door = unrotate_vector_yaw(door_loc - actor_loc, actor_yaw)

    # Map a cardinal axis/sign result (or, failing that, the door's own
    # local position) to the nearest octagon facet angle theta0 (degrees,
    # measured from the actor's own local +X axis).
    axis_sign_to_theta = {("X", 1): 0.0, ("Y", 1): 90.0, ("X", -1): 180.0, ("Y", -1): 270.0}
    if door_result is not None:
        door_axis, door_sign = door_result
        theta0 = axis_sign_to_theta[(door_axis, door_sign)]
        log(f"[{prefix}] Door probe -> wall axis={door_axis} sign={door_sign} (facet angle {theta0:.0f} deg).")
    else:
        if abs(local_door.x) >= abs(local_door.y):
            door_axis, door_sign = ("X", 1 if local_door.x >= 0 else -1)
        else:
            door_axis, door_sign = ("Y", 1 if local_door.y >= 0 else -1)
        theta0 = axis_sign_to_theta[(door_axis, door_sign)]
        log(f"[{prefix}] Door probe found nothing -- falling back to the door's own local position "
            f"({local_door.x:.1f}, {local_door.y:.1f}) -> facet angle {theta0:.0f} deg.")

    in_apothem = max(apothem - WALL_BUFFER_CM, 50.0)
    center_apothem = in_apothem - (WALL_THICKNESS_CM / 2.0)
    face_half_width = in_apothem * math.tan(math.pi / 8.0)

    interior_height = max((ceiling_z_world - floor_z_world) - FLOOR_THICKNESS_CM - CEILING_THICKNESS_CM, 100.0)
    interior_center_z_local = (floor_z_world - actor_loc.z) + FLOOR_THICKNESS_CM + (interior_height / 2.0)

    folder = f"CarrowGateGarrison/{prefix}/InteriorCollision"

    def spawn_local(name, local_pos, local_half_extent):
        world_pos = actor_loc + rotate_vector_yaw(local_pos, actor_yaw)
        spawn_blocking_volume(name, world_pos, actor_rot, local_half_extent, folder)

    def spawn_facet(name, theta_deg, tangent_offset, half_len_tangent, center_z_local, half_height_z):
        rad = math.radians(theta_deg)
        normal_dir = unreal.Vector(math.cos(rad), math.sin(rad), 0.0)
        tangent_dir = unreal.Vector(-math.sin(rad), math.cos(rad), 0.0)
        local_pos = unreal.Vector(
            normal_dir.x * center_apothem + tangent_dir.x * tangent_offset,
            normal_dir.y * center_apothem + tangent_dir.y * tangent_offset,
            center_z_local,
        )
        world_pos = actor_loc + rotate_vector_yaw(local_pos, actor_yaw)
        rotation = unreal.Rotator(actor_rot.roll, actor_rot.pitch, actor_yaw + theta_deg)
        spawn_blocking_volume(name, world_pos, rotation, unreal.Vector(WALL_THICKNESS_CM / 2.0, half_len_tangent, half_height_z), folder)

    # Floor/Ceiling: a simple square inscribed to the apothem. Its corners
    # sit slightly outside the true octagon, under the angled walls, but
    # that's invisible to the player (floor/ceiling aren't things anyone
    # sees past) and far simpler than an 8-sided prism.
    spawn_local(
        f"{prefix}_Collision_Floor",
        unreal.Vector(0.0, 0.0, (floor_z_world - actor_loc.z) + (FLOOR_THICKNESS_CM / 2.0)),
        unreal.Vector(in_apothem, in_apothem, FLOOR_THICKNESS_CM / 2.0),
    )
    spawn_local(
        f"{prefix}_Collision_Ceiling",
        unreal.Vector(0.0, 0.0, (ceiling_z_world - actor_loc.z) - (CEILING_THICKNESS_CM / 2.0)),
        unreal.Vector(in_apothem, in_apothem, CEILING_THICKNESS_CM / 2.0),
    )

    face_names = ["E", "NE", "N", "NW", "W", "SW", "S", "SE"]
    for k in range(8):
        theta = k * 45.0
        face_name = face_names[k]
        is_door_face = abs(((theta - theta0 + 180.0) % 360.0) - 180.0) < 1.0

        if not is_door_face:
            spawn_facet(f"{prefix}_Collision_Wall_{face_name}", theta, 0.0, face_half_width, interior_center_z_local, interior_height / 2.0)
            continue

        log(f"[{prefix}] Facet {face_name} (angle {theta:.0f} deg) faces the door -- splitting with a {DOOR_GAP_WIDTH_CM}cm gap.")

        rad = math.radians(theta)
        tangent_dir = unreal.Vector(-math.sin(rad), math.cos(rad), 0.0)
        gap_center = local_door.x * tangent_dir.x + local_door.y * tangent_dir.y
        clamp = face_half_width - (DOOR_GAP_WIDTH_CM / 2.0) - 10.0
        gap_center = max(-clamp, min(clamp, gap_center)) if clamp > 0 else 0.0

        seg_len_a = max((gap_center - (-face_half_width)) - (DOOR_GAP_WIDTH_CM / 2.0), 0.0)
        seg_len_b = max((face_half_width - gap_center) - (DOOR_GAP_WIDTH_CM / 2.0), 0.0)

        if seg_len_a > 10.0:
            seg_a_center = -face_half_width + (seg_len_a / 2.0)
            spawn_facet(f"{prefix}_Collision_Wall_{face_name}_A", theta, seg_a_center, seg_len_a / 2.0, interior_center_z_local, interior_height / 2.0)
        if seg_len_b > 10.0:
            seg_b_center = face_half_width - (seg_len_b / 2.0)
            spawn_facet(f"{prefix}_Collision_Wall_{face_name}_B", theta, seg_b_center, seg_len_b / 2.0, interior_center_z_local, interior_height / 2.0)

        header_half_height = (interior_height - DOOR_GAP_HEIGHT_CM) / 4.0
        header_z = interior_center_z_local + (interior_height / 2.0) - header_half_height
        spawn_facet(f"{prefix}_Collision_Wall_{face_name}_Header", theta, gap_center, DOOR_GAP_WIDTH_CM / 2.0, header_z, header_half_height)

    log(f"[{prefix}] Octagonal interior collision shell built (apothem={apothem:.1f}cm, facet width={face_half_width * 2:.1f}cm).")

    if building.get("outer_cap") and None not in (bbox_dist_pos_x, bbox_dist_neg_x, bbox_dist_pos_y, bbox_dist_neg_y):
        build_outer_cap_shell(
            building, door, actor_loc, actor_rot, actor_yaw, floor_z_world, ceiling_z_world,
            bbox_dist_pos_x, bbox_dist_neg_x, bbox_dist_pos_y, bbox_dist_neg_y,
            door_axis, door_sign,
        )

    return True


def build_interior_shell(building):
    prefix = building["prefix"]
    exterior = get_actor_by_label(building["exterior_actor"])
    door = get_actor_by_label(building["door_actor"])

    if not exterior:
        log(f"[{prefix}] SKIPPED -- exterior actor '{building['exterior_actor']}' not found.")
        return False
    if not door:
        log(f"[{prefix}] SKIPPED -- door actor '{building['door_actor']}' not found.")
        return False

    mesh_comp = getattr(exterior, "static_mesh_component", None)
    if not mesh_comp:
        mesh_comp = exterior.get_component_by_class(unreal.StaticMeshComponent)
    if not mesh_comp:
        log(f"[{prefix}] SKIPPED -- exterior actor has no static mesh component.")
        return False

    actor_loc = exterior.get_actor_location()
    actor_rot = exterior.get_actor_rotation()
    actor_scale = exterior.get_actor_scale3d()
    actor_yaw = actor_rot.yaw

    local_min, local_max = mesh_comp.get_local_bounds()
    scaled_min = unreal.Vector(local_min.x * actor_scale.x, local_min.y * actor_scale.y, local_min.z * actor_scale.z)
    scaled_max = unreal.Vector(local_max.x * actor_scale.x, local_max.y * actor_scale.y, local_max.z * actor_scale.z)
    bbox_extent_x = (scaled_max.x - scaled_min.x) / 2.0
    bbox_extent_y = (scaled_max.y - scaled_min.y) / 2.0
    floor_z_world = actor_loc.z + scaled_min.z
    ceiling_z_world = actor_loc.z + scaled_max.z

    # Per-direction distances from the actor's own origin to each face of the
    # mesh's bounding box. These are NOT symmetric in general -- a Tripo3D
    # mesh's pivot is rarely centered on its own footprint, so scaled_min.x
    # and scaled_max.x can differ by a wide margin (Command & Comms' radar
    # dish and side pod, for instance, pull scaled_max.x well past
    # -scaled_min.x). Using a single symmetric "bbox_extent" for both faces
    # of an axis -- which earlier revisions of this script did, in both the
    # sizing_method="bbox" branch and the trace-fallback path below -- was
    # exactly why Command's east wall (fell back to the loose symmetric
    # extent because tracing found no hits) ended up so much farther out
    # than its west wall (which traced tight): the fallback number itself
    # was wrong, not just the trace. These four per-face values are the
    # correct fallback/bbox distances to use instead.
    bbox_dist_pos_x = scaled_max.x
    bbox_dist_neg_x = -scaled_min.x
    bbox_dist_pos_y = scaled_max.y
    bbox_dist_neg_y = -scaled_min.y

    log(f"[{prefix}] Actor loc={actor_loc} yaw={actor_yaw:.1f} scale={actor_scale}")
    log(f"[{prefix}] Raw mesh bbox half-extent: x={bbox_extent_x:.1f} y={bbox_extent_y:.1f}, floor_z={floor_z_world:.1f} ceiling_z={ceiling_z_world:.1f}")
    log(f"[{prefix}] Raw mesh per-face distances from origin: +X={bbox_dist_pos_x:.1f} -X={bbox_dist_neg_x:.1f} +Y={bbox_dist_pos_y:.1f} -Y={bbox_dist_neg_y:.1f}")

    sizing_method = building.get("sizing_method", "trace")

    if sizing_method == "octagon":
        return build_octagon_shell(
            building, exterior, door, mesh_comp, actor_loc, actor_rot, actor_yaw, floor_z_world, ceiling_z_world,
            bbox_dist_pos_x, bbox_dist_neg_x, bbox_dist_pos_y, bbox_dist_neg_y,
        )

    world = unreal.EditorLevelLibrary.get_editor_world()
    orig_collision = mesh_comp.get_collision_enabled()
    mesh_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)

    try:
        trace_height_world_z = floor_z_world + TRACE_HEIGHT_ABOVE_FLOOR_CM
        ignore_actors = [exterior]

        if sizing_method == "bbox":
            # Skip wall-distance tracing entirely for this building -- its
            # geometry (an archway with a step/platform right inside it)
            # defeats the trace at every sample height we've tried. Use the
            # full mesh bounding box, same as the original approach that
            # was already confirmed tight and aligned for this specific
            # building's shape.
            log(f"[{prefix}] sizing_method=bbox -- skipping wall-distance tracing, using mesh bbox per-face distances directly.")
            dist_pos_x = bbox_dist_pos_x
            dist_neg_x = bbox_dist_neg_x
            dist_pos_y = bbox_dist_pos_y
            dist_neg_y = bbox_dist_neg_y
        elif sizing_method == "uniform_fixed":
            # Tracing against this building's geometry turned out to be
            # flaky run-to-run (line traces fired immediately after
            # toggling QUERY_ONLY collision on don't always see updated
            # collision state on the very next frame -- an editor physics
            # scene timing issue, not a geometry problem), so a distance
            # that traced successfully on one run could silently fail on
            # the next. Rather than depend on that, this uses a distance
            # value that DID reproduce identically across 6+ separate runs
            # (756.5cm, the door-facing wall) as a fixed, verified number,
            # applied symmetrically to all four sides since the room is a
            # regular octagon (confirmed by the top-down screenshot).
            uniform_dist = building["uniform_distance_cm"]
            log(f"[{prefix}] sizing_method=uniform_fixed -- using a manually-verified distance ({uniform_dist:.1f}) symmetrically on all sides.")
            dist_pos_x = dist_neg_x = dist_pos_y = dist_neg_y = uniform_dist
        elif sizing_method == "uniform_trace":
            # For a round/octagonal room (Command & Comms' interior is an
            # octagon, not a rectangle -- visible clearly from directly
            # above), axis-aligned cardinal-direction tracing is the wrong
            # tool on 3 of 4 sides: rays fired straight along +X/+Y/-Y
            # graze past the octagon's angled facets instead of hitting
            # them square-on, at EVERY height tried, so they fall back to
            # the raw mesh bbox -- which is inflated further still by the
            # radar dish and equipment pod mounted on the outside of the
            # tower (decoration, not interior space). Only -X (facing the
            # door) happens to line up with a flat facet and traces cleanly.
            # Since the room is roughly regular, the fix is to trust
            # whichever direction(s) DID trace successfully and apply that
            # distance -- conservatively, the smallest one -- symmetrically
            # to all four sides, rather than let the 3 failed directions
            # fall back to the decoration-inflated bbox.
            uniform_raw = [
                trace_wall_distance_multi_height(world, actor_loc, actor_yaw, unreal.Vector(1, 0, 0), unreal.Vector(0, 1, 0), bbox_extent_y * TRACE_PERP_HALF_SPAN_RATIO, floor_z_world, ignore_actors),
                trace_wall_distance_multi_height(world, actor_loc, actor_yaw, unreal.Vector(-1, 0, 0), unreal.Vector(0, 1, 0), bbox_extent_y * TRACE_PERP_HALF_SPAN_RATIO, floor_z_world, ignore_actors),
                trace_wall_distance_multi_height(world, actor_loc, actor_yaw, unreal.Vector(0, 1, 0), unreal.Vector(1, 0, 0), bbox_extent_x * TRACE_PERP_HALF_SPAN_RATIO, floor_z_world, ignore_actors),
                trace_wall_distance_multi_height(world, actor_loc, actor_yaw, unreal.Vector(0, -1, 0), unreal.Vector(1, 0, 0), bbox_extent_x * TRACE_PERP_HALF_SPAN_RATIO, floor_z_world, ignore_actors),
            ]
            successful = [median for median, count, mx in uniform_raw if median is not None and count >= TRACE_SAMPLE_COUNT * 0.5]
            if successful:
                uniform_dist = min(successful)
                log(f"[{prefix}] sizing_method=uniform_trace -- {len(successful)}/4 direction(s) traced successfully "
                    f"({[f'{d:.1f}' for d in successful]}), using the smallest ({uniform_dist:.1f}) symmetrically on all sides.")
            else:
                uniform_dist = min(bbox_dist_pos_x, bbox_dist_neg_x, bbox_dist_pos_y, bbox_dist_neg_y)
                log(f"[{prefix}] sizing_method=uniform_trace -- no direction traced successfully, "
                    f"falling back to the smallest raw bbox face distance ({uniform_dist:.1f}) symmetrically on all sides.")
            dist_pos_x = dist_neg_x = dist_pos_y = dist_neg_y = uniform_dist
        else:
            raw_pos_x = trace_wall_distance_multi_height(world, actor_loc, actor_yaw, unreal.Vector(1, 0, 0), unreal.Vector(0, 1, 0), bbox_extent_y * TRACE_PERP_HALF_SPAN_RATIO, floor_z_world, ignore_actors)
            raw_neg_x = trace_wall_distance_multi_height(world, actor_loc, actor_yaw, unreal.Vector(-1, 0, 0), unreal.Vector(0, 1, 0), bbox_extent_y * TRACE_PERP_HALF_SPAN_RATIO, floor_z_world, ignore_actors)
            raw_pos_y = trace_wall_distance_multi_height(world, actor_loc, actor_yaw, unreal.Vector(0, 1, 0), unreal.Vector(1, 0, 0), bbox_extent_x * TRACE_PERP_HALF_SPAN_RATIO, floor_z_world, ignore_actors)
            raw_neg_y = trace_wall_distance_multi_height(world, actor_loc, actor_yaw, unreal.Vector(0, -1, 0), unreal.Vector(1, 0, 0), bbox_extent_x * TRACE_PERP_HALF_SPAN_RATIO, floor_z_world, ignore_actors)

            # Each entry is (median_distance, hit_count, max_distance). A wall
            # direction with either no hits at all, or a suspiciously small
            # median relative to that face's own bbox distance (fewer than
            # 35% of it) with most rays finding nothing, almost always means
            # the rays sailed through an open archway/recess and only
            # clipped a nearby alcove corner rather than hitting a real
            # outer wall -- the mesh's own per-face bbox distance is the
            # safer number to fall back to there than trusting a handful of
            # stray close hits. Falling back to a single symmetric
            # bbox_extent (as earlier revisions did) was itself a bug: a
            # failed trace on one side would fall back to the AVERAGE of
            # both faces' distances rather than that face's own, which is
            # exactly what put Command & Comms' east wall out past where
            # its own mesh geometry actually ends.
            def resolve(raw, bbox_dist, label):
                median, count, mx = raw
                if median is None:
                    log(f"[{prefix}] WARNING: no trace hits in {label}, falling back to bbox distance ({bbox_dist:.1f}).")
                    return bbox_dist
                if median < 0.35 * bbox_dist and count < TRACE_SAMPLE_COUNT * 0.5:
                    log(f"[{prefix}] WARNING: {label} trace median ({median:.1f}) looks like an archway/recess, "
                        f"not a real wall (only {count}/{TRACE_SAMPLE_COUNT} rays hit anything) -- falling back to bbox distance ({bbox_dist:.1f}).")
                    return bbox_dist
                return median

            dist_pos_x = resolve(raw_pos_x, bbox_dist_pos_x, "+X")
            dist_neg_x = resolve(raw_neg_x, bbox_dist_neg_x, "-X")
            dist_pos_y = resolve(raw_pos_y, bbox_dist_pos_y, "+Y")
            dist_neg_y = resolve(raw_neg_y, bbox_dist_neg_y, "-Y")

        log(f"[{prefix}] Wall distances used (from actor origin): +X={dist_pos_x:.1f} -X={dist_neg_x:.1f} +Y={dist_pos_y:.1f} -Y={dist_neg_y:.1f}")

        door_loc = door.get_actor_location()
        door_result = trace_door_wall(world, actor_loc, actor_yaw, door_loc, trace_height_world_z, ignore_actors)
    finally:
        mesh_comp.set_collision_enabled(orig_collision)

    local_door = unrotate_vector_yaw(door_loc - actor_loc, actor_yaw)

    if door_result is None:
        # Fallback: pick whichever traced wall the door is numerically
        # closest to (comparing the door's local coordinate on each axis to
        # that axis's measured wall distance), rather than failing outright.
        candidates = [
            ("X", 1, abs(local_door.x - dist_pos_x)),
            ("X", -1, abs(-local_door.x - dist_neg_x)),
            ("Y", 1, abs(local_door.y - dist_pos_y)),
            ("Y", -1, abs(-local_door.y - dist_neg_y)),
        ]
        candidates.sort(key=lambda c: c[2])
        door_axis, door_sign, best_gap = candidates[0]
        log(f"[{prefix}] Door probe found nothing -- falling back to nearest-traced-wall comparison: "
            f"axis={door_axis} sign={door_sign} (gap={best_gap:.1f}cm). All candidates: {candidates}")
    else:
        door_axis, door_sign = door_result

    log(f"[{prefix}] Door local={local_door} -> determined wall axis={door_axis} sign={door_sign}")

    # Interior half-extents after pulling each wall in from its traced
    # surface by the buffer, and the (possibly off-center) interior center.
    in_pos_x = max(dist_pos_x - WALL_BUFFER_CM, 50.0)
    in_neg_x = max(dist_neg_x - WALL_BUFFER_CM, 50.0)
    in_pos_y = max(dist_pos_y - WALL_BUFFER_CM, 50.0)
    in_neg_y = max(dist_neg_y - WALL_BUFFER_CM, 50.0)

    local_center_x = (in_pos_x - in_neg_x) / 2.0
    local_center_y = (in_pos_y - in_neg_y) / 2.0
    in_extent_x = (in_pos_x + in_neg_x) / 2.0
    in_extent_y = (in_pos_y + in_neg_y) / 2.0

    interior_height = max((ceiling_z_world - floor_z_world) - FLOOR_THICKNESS_CM - CEILING_THICKNESS_CM, 100.0)
    interior_center_z_local = (floor_z_world - actor_loc.z) + FLOOR_THICKNESS_CM + (interior_height / 2.0)

    folder = f"CarrowGateGarrison/{prefix}/InteriorCollision"

    def spawn_local(name, local_pos, local_half_extent):
        world_pos = actor_loc + rotate_vector_yaw(local_pos, actor_yaw)
        spawn_blocking_volume(name, world_pos, actor_rot, local_half_extent, folder)

    # Floor
    spawn_local(
        f"{prefix}_Collision_Floor",
        unreal.Vector(local_center_x, local_center_y, (floor_z_world - actor_loc.z) + (FLOOR_THICKNESS_CM / 2.0)),
        unreal.Vector(in_extent_x, in_extent_y, FLOOR_THICKNESS_CM / 2.0),
    )
    # Ceiling
    spawn_local(
        f"{prefix}_Collision_Ceiling",
        unreal.Vector(local_center_x, local_center_y, (ceiling_z_world - actor_loc.z) - (CEILING_THICKNESS_CM / 2.0)),
        unreal.Vector(in_extent_x, in_extent_y, CEILING_THICKNESS_CM / 2.0),
    )

    walls = [
        ("N", "Y", 1, in_pos_y),
        ("S", "Y", -1, in_neg_y),
        ("E", "X", 1, in_pos_x),
        ("W", "X", -1, in_neg_x),
    ]

    for wall_name, axis, sign, wall_dist in walls:
        is_door_wall = (axis == door_axis and sign == door_sign)

        if axis == "X":
            wall_center_local = unreal.Vector(
                local_center_x + sign * (wall_dist - WALL_THICKNESS_CM / 2.0),
                local_center_y,
                interior_center_z_local,
            )
            wall_extent = unreal.Vector(WALL_THICKNESS_CM / 2.0, in_extent_y, interior_height / 2.0)
        else:
            wall_center_local = unreal.Vector(
                local_center_x,
                local_center_y + sign * (wall_dist - WALL_THICKNESS_CM / 2.0),
                interior_center_z_local,
            )
            wall_extent = unreal.Vector(in_extent_x, WALL_THICKNESS_CM / 2.0, interior_height / 2.0)

        if not is_door_wall:
            spawn_local(f"{prefix}_Collision_Wall_{wall_name}", wall_center_local, wall_extent)
            continue

        log(f"[{prefix}] Wall {wall_name} faces the door -- splitting with a {DOOR_GAP_WIDTH_CM}cm gap.")

        if axis == "X":
            gap_center = local_door.y
            seg_len_a = max((gap_center - (local_center_y - in_extent_y)) - (DOOR_GAP_WIDTH_CM / 2.0), 0.0)
            seg_len_b = max(((local_center_y + in_extent_y) - gap_center) - (DOOR_GAP_WIDTH_CM / 2.0), 0.0)

            if seg_len_a > 10.0:
                seg_a_center_y = (local_center_y - in_extent_y) + (seg_len_a / 2.0)
                spawn_local(
                    f"{prefix}_Collision_Wall_{wall_name}_A",
                    unreal.Vector(wall_center_local.x, seg_a_center_y, interior_center_z_local),
                    unreal.Vector(WALL_THICKNESS_CM / 2.0, seg_len_a / 2.0, interior_height / 2.0),
                )
            if seg_len_b > 10.0:
                seg_b_center_y = (local_center_y + in_extent_y) - (seg_len_b / 2.0)
                spawn_local(
                    f"{prefix}_Collision_Wall_{wall_name}_B",
                    unreal.Vector(wall_center_local.x, seg_b_center_y, interior_center_z_local),
                    unreal.Vector(WALL_THICKNESS_CM / 2.0, seg_len_b / 2.0, interior_height / 2.0),
                )
            header_z = interior_center_z_local + (interior_height / 2.0) - ((interior_height - DOOR_GAP_HEIGHT_CM) / 2.0) / 2.0
            spawn_local(
                f"{prefix}_Collision_Wall_{wall_name}_Header",
                unreal.Vector(wall_center_local.x, gap_center, header_z),
                unreal.Vector(WALL_THICKNESS_CM / 2.0, DOOR_GAP_WIDTH_CM / 2.0, (interior_height - DOOR_GAP_HEIGHT_CM) / 4.0),
            )
        else:
            gap_center = local_door.x
            seg_len_a = max((gap_center - (local_center_x - in_extent_x)) - (DOOR_GAP_WIDTH_CM / 2.0), 0.0)
            seg_len_b = max(((local_center_x + in_extent_x) - gap_center) - (DOOR_GAP_WIDTH_CM / 2.0), 0.0)

            if seg_len_a > 10.0:
                seg_a_center_x = (local_center_x - in_extent_x) + (seg_len_a / 2.0)
                spawn_local(
                    f"{prefix}_Collision_Wall_{wall_name}_A",
                    unreal.Vector(seg_a_center_x, wall_center_local.y, interior_center_z_local),
                    unreal.Vector(seg_len_a / 2.0, WALL_THICKNESS_CM / 2.0, interior_height / 2.0),
                )
            if seg_len_b > 10.0:
                seg_b_center_x = (local_center_x + in_extent_x) - (seg_len_b / 2.0)
                spawn_local(
                    f"{prefix}_Collision_Wall_{wall_name}_B",
                    unreal.Vector(seg_b_center_x, wall_center_local.y, interior_center_z_local),
                    unreal.Vector(seg_len_b / 2.0, WALL_THICKNESS_CM / 2.0, interior_height / 2.0),
                )
            header_z = interior_center_z_local + (interior_height / 2.0) - ((interior_height - DOOR_GAP_HEIGHT_CM) / 2.0) / 2.0
            spawn_local(
                f"{prefix}_Collision_Wall_{wall_name}_Header",
                unreal.Vector(gap_center, wall_center_local.y, header_z),
                unreal.Vector(DOOR_GAP_WIDTH_CM / 2.0, WALL_THICKNESS_CM / 2.0, (interior_height - DOOR_GAP_HEIGHT_CM) / 4.0),
            )

    log(f"[{prefix}] Interior collision shell built.")
    return True


def main():
    log(f"Starting trace-based interior collision generation for {len(BUILDINGS)} building(s).")
    results = []
    for building in BUILDINGS:
        ok = build_interior_shell(building)
        results.append((building["prefix"], ok))

    log("---- SUMMARY ----")
    for prefix, ok in results:
        log(f"{prefix}: {'OK' if ok else 'SKIPPED/FAILED'}")
    log("Review in viewport, then save the level yourself when ready.")


main()
