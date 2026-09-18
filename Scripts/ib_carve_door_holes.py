"""
IBPY: ib_carve_door_holes.py  (v3 -- empirical cutter-orientation search)

Physically carves a doorway-shaped hole through each building's exterior
Tripo3D mesh, so "Use Complex Collision As Simple" (already enabled, see
ib_complex_collision.py) can give exact, shape-accurate collision AND a
walkable doorway.

SAFE BY CONSTRUCTION: this NEVER edits your original visual StaticMesh
assets. For each building it:
  1. Duplicates the original mesh asset to a new "<Name>_Collision" asset
     (deleting any stale one from a previous run first, so it always
     starts from clean, uncarved geometry).
  2. Searches for a cutter orientation (and, if needed, a larger cutter
     size) that actually intersects the mesh -- see "WHY A SEARCH" below.
  3. Writes ONLY the winning result back into the DUPLICATE asset.
  4. Points the ORIGINAL asset's "complex_collision_mesh" property at the
     duplicate -- so the original render mesh is 100% untouched, but
     complex collision now has a real doorway.
  5. Re-enables collision on the exterior mesh component (BlockAll).

WHY A SEARCH (v1/v2 history, kept for context):
  v1 hardcoded a per-building wall direction -- wrong for Command (stale
  data from an old script). v2 trusted each DoorFrame actor's own
  get_actor_rotation() directly -- that happened to be correct for Armory
  but STILL produced a silent 0-triangle-change no-op for Command, and
  even REGRESSED Mess Hall (which had worked in v1). Two different single-
  guess strategies each failed for at least one of the three doors, which
  means no cheap heuristic here is trustworthy across all three -- the
  door actors' placement/rotation just wasn't applied consistently when
  this level was built. So v3 stops guessing and instead VERIFIES:

  For each building, it tries candidate cutter yaws (starting with the
  door's own rotation, since that's right at least once, then sweeping
  every 15 degrees around the full circle) against a scratch copy of the
  mesh, and only accepts a candidate if the boolean subtract actually
  changes the triangle count by a real amount (>= MIN_TRIANGLE_DELTA --
  filters out near-miss grazing hits, not just exact zero). Each
  candidate test uses a FRESH copy of the duplicate's geometry (so a
  failed attempt never contaminates the next one) and nothing is written
  back to any asset until a winning candidate is found. If every yaw at
  the normal cutter size fails, it retries the same yaw sweep with an
  enlarged cutter (bigger depth/width/height) in case the miss was really
  a positioning/reach problem rather than a pure orientation problem.

  This does mean more boolean-subtract calls per building than before
  (up to ~24 candidates x up to 2 size tiers), but each one is a cheap
  in-memory op with NO asset write and NO Nanite rebuild -- only the
  final winning candidate gets written back and rebuilt. Expect this
  script to take noticeably longer to run than v1/v2, especially for
  Command and Mess Hall, since it has to search this time. That's normal.

DOOR CUTTER SIZING (tune these if the carved opening looks off after your
first look in PIE):
  DOOR_CUT_WIDTH_CM / DOOR_CUT_HEIGHT_CM match the DOOR_GAP_WIDTH_CM /
  DOOR_GAP_HEIGHT_CM constants from the earlier BlockingVolume script.
  DOOR_CUT_DEPTH_CM is generous so it reliably punches through the wall's
  actual thickness regardless of what that turns out to be.
  ENLARGED_* are the fallback size used only if every yaw candidate fails
  at normal size -- bigger so it can reach a wall even if the door
  actor's position is a bit off from where the real wall surface is.

Assumes each DoorFrame actor's pivot sits at floor level (so the cutter's
vertical span starts at the door actor's own Z and extends upward by the
cutter height) -- if a carved hole comes out shifted up/down, that's the
thing to adjust first.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_carve_door_holes.py"
Then check each building in PIE: the doorway should now be a real, open
gap you can walk through, and everything else should still block you
(complex-as-simple collision, via the un-holed exterior shape). Save the
level once happy -- the mesh assets are saved by this script already.
"""

import unreal

BUILDINGS = [
    {"prefix": "Medical", "exterior_actor": "Medical", "door_actor": "Medical_DoorFrame"},
    {"prefix": "Barracks", "exterior_actor": "Barracks", "door_actor": "Barracks_DoorFrame"},
    {"prefix": "Armory", "exterior_actor": "Armory", "door_actor": "Armory_DoorFrame"},
    {"prefix": "Command", "exterior_actor": "Command", "door_actor": "Command_DoorFrame"},
    {"prefix": "Mess_Hall", "exterior_actor": "Mess_Hall", "door_actor": "Mess_Hall_DoorFrame"},
]
# NOTE: after the Garrison rebuild, actors are labeled just "Medical" /
# "Armory" / etc. (no "07_" prefix, no "SM_..._Tripo" suffix) -- confirmed
# via ib_survey_garrison.py. Door actors are "<Building>_DoorFrame",
# matching what ib_place_doors.py spawned (you then manually repositioned
# them, without renaming). If a run below says a door/exterior actor
# wasn't found, the actual current label differs from this guess --
# paste back an ib_survey_garrison.py run and I'll fix these strings.

DOOR_CUT_WIDTH_CM = 220.0
DOOR_CUT_HEIGHT_CM = 280.0
DOOR_CUT_DEPTH_CM = 600.0

# Fallback size, tried only if every yaw candidate misses at normal size.
ENLARGED_CUT_WIDTH_CM = 340.0
ENLARGED_CUT_HEIGHT_CM = 380.0
ENLARGED_CUT_DEPTH_CM = 1200.0

YAW_SWEEP_STEP_DEG = 15.0
MIN_TRIANGLE_DELTA = 50  # a real cut; filters out near-miss/grazing noise

COLLISION_PROFILE = "BlockAll"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_actor_by_label(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsystem.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def build_candidate_yaws(door_yaw):
    """Door's own rotation first (cheap, sometimes already right), then a
    full sweep every YAW_SWEEP_STEP_DEG degrees, skipping near-duplicates
    of the door yaw so we don't waste a test re-trying basically the same
    angle."""
    candidates = [door_yaw]
    yaw = 0.0
    while yaw < 360.0:
        if abs(((yaw - door_yaw + 180.0) % 360.0) - 180.0) > 1.0:
            candidates.append(yaw)
        yaw += YAW_SWEEP_STEP_DEG
    return candidates


def fresh_copy(duplicate_asset):
    mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(
        duplicate_asset,
        unreal.DynamicMesh(),
        unreal.GeometryScriptCopyMeshFromAssetOptions(),
        unreal.GeometryScriptMeshReadLOD(lod_type=unreal.GeometryScriptLODType.SOURCE_MODEL, lod_index=0),
    )
    return mesh, outcome


def try_candidate(duplicate_asset, target_transform, door_loc, yaw, width, height, depth, boolean_options):
    """Tests one (yaw, size) candidate against a FRESH copy of the
    duplicate's current geometry. Returns (mesh, before_count, after_count)
    -- caller decides pass/fail from the count delta. Never writes
    anything to any asset."""
    mesh, _copy_outcome = fresh_copy(duplicate_asset)
    before_count = mesh.get_triangle_count()

    cutter_center = unreal.Vector(door_loc.x, door_loc.y, door_loc.z + (height / 2.0))
    cutter_transform = unreal.Transform(
        location=cutter_center,
        rotation=unreal.Rotator(0.0, 0.0, yaw),
        scale=unreal.Vector(1.0, 1.0, 1.0),
    )
    cutter_mesh = unreal.DynamicMesh()
    cutter_mesh.append_box(
        unreal.GeometryScriptPrimitiveOptions(),
        cutter_transform,
        dimension_x=depth,
        dimension_y=width,
        dimension_z=height,
        steps_x=0, steps_y=0, steps_z=0,
        origin=unreal.GeometryScriptPrimitiveOriginMode.CENTER,
    )

    mesh.apply_mesh_boolean(
        target_transform,
        cutter_mesh,
        unreal.Transform(),
        unreal.GeometryScriptBooleanOperation.SUBTRACT,
        boolean_options,
    )
    after_count = mesh.get_triangle_count()
    return mesh, before_count, after_count


def find_working_cut(prefix, duplicate_asset, target_transform, door_loc, door_yaw):
    boolean_options = unreal.GeometryScriptMeshBooleanOptions(
        output_transform_space=unreal.GeometryScriptBooleanOutputSpace.TARGET_TRANSFORM_SPACE,
        fill_holes=True,
        allow_empty_result=False,
    )

    size_tiers = [
        ("normal", DOOR_CUT_WIDTH_CM, DOOR_CUT_HEIGHT_CM, DOOR_CUT_DEPTH_CM),
        ("enlarged", ENLARGED_CUT_WIDTH_CM, ENLARGED_CUT_HEIGHT_CM, ENLARGED_CUT_DEPTH_CM),
    ]

    for tier_name, width, height, depth in size_tiers:
        candidates = build_candidate_yaws(door_yaw)
        log(f"[{prefix}] Searching {len(candidates)} yaw candidate(s) at '{tier_name}' cutter size "
            f"({depth}x{width}x{height})...")
        for yaw in candidates:
            mesh, before_count, after_count = try_candidate(
                duplicate_asset, target_transform, door_loc, yaw, width, height, depth, boolean_options
            )
            delta = abs(after_count - before_count)
            if delta >= MIN_TRIANGLE_DELTA:
                log(f"[{prefix}] HIT at yaw={yaw:.1f} size='{tier_name}': triangles {before_count} -> "
                    f"{after_count} (delta={delta}).")
                return mesh, tier_name, yaw, width, height, depth
        log(f"[{prefix}] No candidate at '{tier_name}' size produced a real cut (all deltas < {MIN_TRIANGLE_DELTA}).")

    return None, None, None, None, None, None


def carve_building(building):
    prefix = building["prefix"]
    exterior = get_actor_by_label(building["exterior_actor"])
    door = get_actor_by_label(building["door_actor"])

    if not exterior:
        log(f"[{prefix}] SKIPPED -- exterior actor '{building['exterior_actor']}' not found.")
        return False
    if not door:
        log(f"[{prefix}] SKIPPED -- door actor '{building['door_actor']}' not found.")
        return False

    mesh_comp = getattr(exterior, "static_mesh_component", None) or exterior.get_component_by_class(unreal.StaticMeshComponent)
    if not mesh_comp:
        log(f"[{prefix}] SKIPPED -- exterior actor has no static mesh component.")
        return False

    static_mesh = mesh_comp.get_editor_property("static_mesh")
    if not static_mesh:
        log(f"[{prefix}] SKIPPED -- static mesh component has no assigned mesh.")
        return False

    actor_loc = exterior.get_actor_location()
    actor_rot = exterior.get_actor_rotation()
    actor_scale = exterior.get_actor_scale3d()
    door_loc = door.get_actor_location()
    door_rot = door.get_actor_rotation()

    # ---- 1. Duplicate the original asset (always fresh from the original) ----
    package_path = static_mesh.get_outermost().get_name()
    new_asset_name = static_mesh.get_name() + "_Collision"
    new_package_dir = "/".join(package_path.split("/")[:-1])
    new_full_path = f"{new_package_dir}/{new_asset_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(new_full_path):
        unreal.EditorAssetLibrary.delete_asset(new_full_path)
        log(f"[{prefix}] Removed stale '{new_full_path}' from a previous run.")

    duplicate_asset = unreal.EditorAssetLibrary.duplicate_asset(package_path, new_full_path)
    if not duplicate_asset:
        log(f"[{prefix}] SKIPPED -- failed to duplicate '{package_path}' to '{new_full_path}'.")
        return False
    log(f"[{prefix}] Duplicated '{package_path}' -> '{new_full_path}'.")

    # ---- 2. Search for a cutter orientation/size that actually cuts something ----
    target_transform = unreal.Transform(location=actor_loc, rotation=actor_rot, scale=actor_scale)
    winning_mesh, tier_name, yaw, width, height, depth = find_working_cut(
        prefix, duplicate_asset, target_transform, door_loc, door_rot.yaw
    )

    if winning_mesh is None:
        log(f"[{prefix}] FAILED -- no cutter orientation/size produced a real cut. Nothing written; "
            f"duplicate asset left as an unmodified copy. This building's door position/rotation likely "
            f"needs to be checked by hand in the editor.")
        return False

    winning_mesh.recompute_normals(unreal.GeometryScriptCalculateNormalsOptions(angle_weighted=True, area_weighted=True))

    # ---- 3. Write ONLY the winning result back into the DUPLICATE ----
    _, write_outcome = unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(
        winning_mesh,
        duplicate_asset,
        unreal.GeometryScriptCopyMeshToAssetOptions(enable_recompute_normals=False, enable_recompute_tangents=True),
        unreal.GeometryScriptMeshWriteLOD(lod_index=0, write_hi_res_source=False),
        use_section_materials=True,
    )
    log(f"[{prefix}] copy_mesh_to_static_mesh outcome={write_outcome} (winning yaw={yaw:.1f}, size='{tier_name}').")

    dup_body_setup = duplicate_asset.get_editor_property("body_setup")
    if dup_body_setup:
        duplicate_asset.modify()
        dup_body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    dup_saved = unreal.EditorAssetLibrary.save_loaded_asset(duplicate_asset)
    log(f"[{prefix}] Duplicate collision asset saved={dup_saved}.")

    # ---- 4. Point the ORIGINAL asset's complex collision at the duplicate ----
    static_mesh.modify()
    static_mesh.set_editor_property("complex_collision_mesh", duplicate_asset)
    body_setup = static_mesh.get_editor_property("body_setup")
    if body_setup:
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    orig_saved = unreal.EditorAssetLibrary.save_loaded_asset(static_mesh)
    log(f"[{prefix}] Original visual mesh untouched, now points complex_collision_mesh -> '{new_full_path}' (saved={orig_saved}).")

    # ---- 5. Re-enable collision on the level actor's component ----
    mesh_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    mesh_comp.set_collision_profile_name(COLLISION_PROFILE)
    log(f"[{prefix}] '{building['exterior_actor']}' collision_enabled=QueryOnly profile='{COLLISION_PROFILE}'.")

    return True


def main():
    log(f"Carving doorway holes for {len(BUILDINGS)} building(s) into non-destructive collision-only mesh copies "
        f"(v3 -- empirical search, may take a while per building).")
    results = []
    for building in BUILDINGS:
        try:
            ok = carve_building(building)
        except Exception as e:
            log(f"[{building['prefix']}] FAILED with exception: {e}")
            ok = False
        results.append((building["prefix"], ok))

    log("---- SUMMARY ----")
    for prefix, ok in results:
        log(f"{prefix}: {'OK' if ok else 'SKIPPED/FAILED'}")
    log("Test by walking into each building's doorway in PIE, then save the level (Ctrl+S) when happy. "
        "Any building marked SKIPPED/FAILED still has NoCollision-safe fallback from earlier and needs "
        "its door position/rotation checked by hand.")


main()
