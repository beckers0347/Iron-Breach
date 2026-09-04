"""
BRIDGE EVERY GAP BETWEEN COBBLESTONE PATH PIECES -- wherever they are
================================================================
IRON BREACH / Unreal Engine 5.8

WHY THIS IS DIFFERENT FROM THE LAST CORNER FIX
------------------------------------------------
connect_road_corners.py only re-derived waypoints for ONE specific system
(CG Mainland's outskirt winding roads) and it turned out that wasn't even
the right corner -- the reddish patch you kept pointing at never got
confirmed by the selection diagnostic, so guessing which hand-authored
system it belongs to again risks being wrong a third time.

Instead of guessing which script generated a given path piece, this reads
the ACTUAL PLACED GEOMETRY straight out of the level: every actor currently
wearing M_AI_CobblestonePath (that's now the one shared material for every
walking path/street/road in the project, garrison and mainland both), gets
its real world bounding box. Any two path pieces that are close to each
other (within GAP_THRESHOLD_M) but whose bounding boxes DON'T actually
touch get a bridging patch spawned between their centers, wide enough to
fully cover the gap. This doesn't care which build script made either
piece, or what angle they meet at -- it works off where things actually
are right now, so it should catch corners regardless of which system
they came from.

Safe to re-run -- clears any bridges it placed on a previous run first
(PathBridge_* labels).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/connect_all_path_corners.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary

PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
CUBE_MESH = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")

GAP_THRESHOLD_M = 14.0    # only bridge path pieces closer than this (center to center)
TOUCH_MARGIN_M = 0.5      # bounding boxes within this of touching count as "already connected"
BRIDGE_MARGIN_M = 5.0     # extra width/depth added to each bridge so it fully covers the gap
BRIDGE_HEIGHT_M = 0.3


def log(msg):
    print("[ConnectAllPathCorners] %s" % msg)


def get_path_actors(path_mat):
    all_actors = actor_subsystem.get_all_level_actors()
    result = []
    for a in all_actors:
        for comp in a.get_components_by_class(unreal.StaticMeshComponent):
            mat = comp.get_material(0)
            if mat and mat.get_path_name().startswith(PATH_MATERIAL_PATH):
                origin, extent = a.get_actor_bounds(False)
                result.append((a, origin, extent))
                break
    return result


def boxes_touch(o1, e1, o2, e2, margin_cm):
    # Axis-aligned overlap test (with a margin) in X and Y only -- these are
    # all thin ground-level slabs, Z doesn't matter for "does the path connect".
    dx = abs(o1.x - o2.x) - (e1.x + e2.x + margin_cm)
    dy = abs(o1.y - o2.y) - (e1.y + e2.y + margin_cm)
    return dx <= 0 and dy <= 0


def delete_existing_bridges():
    all_actors = actor_subsystem.get_all_level_actors()
    existing = [a for a in all_actors if a.get_actor_label().startswith("PathBridge_")]
    for a in existing:
        actor_subsystem.destroy_actor(a)
    if existing:
        log("Removed %d bridge(s) from a previous run before re-placing." % len(existing))


def spawn_bridge(index, o1, o2, mat):
    cx = (o1.x + o2.x) / 2.0
    cy = (o1.y + o2.y) / 2.0
    cz = min(o1.z, o2.z)
    dist_cm = ((o1.x - o2.x) ** 2 + (o1.y - o2.y) ** 2) ** 0.5
    size_cm = dist_cm + BRIDGE_MARGIN_M * 100.0

    location = unreal.Vector(cx, cy, cz)
    rotation = unreal.Rotator(0, 0, 0)
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(f"PathBridge_{index:04d}")
    actor.set_folder_path("PathBridges")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(CUBE_MESH)
    # Cube is 100uu(=1m) native -- scale in "meters" directly, matching every other spawn helper in this project.
    mesh_comp.set_world_scale3d(unreal.Vector(size_cm / 100.0, size_cm / 100.0, BRIDGE_HEIGHT_M))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    mesh_comp.set_material(0, mat)
    return actor


def run():
    if not AL.does_asset_exist(PATH_MATERIAL_PATH):
        log("SKIPPED -- %s doesn't exist." % PATH_MATERIAL_PATH)
        return
    path_mat = AL.load_asset(PATH_MATERIAL_PATH)

    delete_existing_bridges()

    pieces = get_path_actors(path_mat)
    log("Found %d actor(s) wearing M_AI_CobblestonePath." % len(pieces))
    if len(pieces) < 2:
        log("Not enough path pieces to bridge anything.")
        return

    gap_threshold_cm = GAP_THRESHOLD_M * 100.0
    touch_margin_cm = TOUCH_MARGIN_M * 100.0

    bridged = 0
    n = len(pieces)
    for i in range(n):
        a1, o1, e1 = pieces[i]
        for j in range(i + 1, n):
            a2, o2, e2 = pieces[j]
            dist_cm = ((o1.x - o2.x) ** 2 + (o1.y - o2.y) ** 2) ** 0.5
            if dist_cm > gap_threshold_cm:
                continue
            if boxes_touch(o1, e1, o2, e2, touch_margin_cm):
                continue  # already connected, nothing to bridge
            spawn_bridge(bridged, o1, o2, path_mat)
            bridged += 1
            log("  bridged '%s' <-> '%s' (gap ~%.1fm)" % (
                a1.get_actor_label(), a2.get_actor_label(), dist_cm / 100.0))

    log("Placed %d bridge patch(es)." % bridged)
    log("Save and check the viewport / re-run PIE.")


run()
