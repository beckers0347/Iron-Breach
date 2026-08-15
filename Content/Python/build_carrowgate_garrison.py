"""
Carrowgate Garrison -- Mission 01 "Landfall" blockout generator
=================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
A one-shot Editor Python script that grey-boxes the Carrowgate Garrison
starting area from the Mission 01 level sheet: 13 numbered zones, a
PlayerStart in the Barracks, a NavMeshBoundsVolume over the footprint, and
a rough pre-dawn/overcast lighting rig.

The 6 actual buildings (Watch Tower, Barracks, Mess Hall, Armory, Command &
Comms, Sensor Array) are hollow, walkable rooms -- 4 walls + a ceiling with a
doorway gap, built from cubes -- not solid blocks, so you can walk inside
them. Main Gate is a pass-through checkpoint arch (two pylons + a lintel),
not an enclosed room. The open yards (Vehicle Bay, Parade Yard, Helipad, Sea
Wall, Civic Route, Docks/Harbor) stay solid flat pads since they're not
buildings. See spawn_room()/spawn_gate_arch() below, and each area's `kind`
in AREAS, if you want to change which areas are enterable or where their
doors face.

Each of the 6 buildings also gets basic interior furniture (bunks, lockers,
tables, weapon racks, desks, sensor consoles, etc.) via add_furniture() near
the bottom -- see FURNITURE comments there to add/move/reskin pieces.

HOW TO RUN IT
-------------
1. In the Unreal Editor: File > New Level > Empty Level, then Save As
   something like Content/LevelPrototyping/Lvl_Mission01_CarrowgateGarrison
   (or open whatever level you want this dropped into -- the script doesn't
   care, it just spawns actors into whatever level is currently open).
2. Run it from one of two consoles at the bottom of the editor -- they take
   different syntax, don't mix them up:
     - General Cmd / Output Log console (opened with ~): prefix with "py":
           py "X:/IronBreach/Content/Python/build_carrowgate_garrison.py"
     - Dedicated Python console tab: it already evaluates raw Python, so do
       NOT prefix with "py" -- either paste the bare path, or run:
           exec(open("X:/IronBreach/Content/Python/build_carrowgate_garrison.py").read())
   (This requires the Python Editor Script Plugin, which has been enabled
   in IronBreach.uproject -- if the editor was already open, close and
   reopen it, or "Yes" the regenerate-modules prompt, so the plugin loads.)
3. Check the Output Log for the summary line and any [Carrowgate Blockout]
   warnings, then press P to preview navigation and Build > Build Paths.
4. Save the level.

Re-running is safe: the script clears out anything under the "Carrowgate
Garrison" outliner folder from a previous run before rebuilding, so you can
tweak AREAS below and re-run instead of hand-deleting actors each time.

If the viewport looks empty/black after running: nothing moves your camera
for you. Select the "Carrowgate Garrison" folder in the Outliner (or any one
actor, e.g. 05_Barracks), then press F with the viewport focused to frame it.

LAYOUT NOTES
------------
+X = toward the coast / Docks & Harbor. +Y = north (Watch Tower / Sensor
Array side). Z=0 is the main garrison platform; the Docks/Harbor sit ~4m
lower, reached by a ramp, matching the sheet's "multiple vertical layers"
note. Every position/size below is a reasonable starting guess read off the
area map and the scale reference (1.8m human, 8.5m vehicle, 22m ship) --
nudge things once you can walk the space, nothing here is precious.

ON THE KAIJU
------------
The sheet lists "Threat: Class C Kaiju (Palawan)" but also "Role: Player
Spawn / Intro / Tutorial" and a camera note that kaiju scale should be
introduced "through destruction, not direct confrontation." The M1
"Landfall" beat in the narrative bible has PALAWAN un-engaged, folding down
and calcifying on its own a couple blocks from the hospital -- it's a
skybox/atmosphere beat here, not a fight. So this script does NOT place an
active AIBKaijuSpawner in the garrison. If BP_Kaiju_Palawan exists in your
content (per Docs/HANDOFF_PROMPT.md it may not be persisted to every
checkout yet), the optional last section will place a distant, non-combat
silhouette of it for atmosphere; otherwise it logs a warning and skips.
"""

import unreal

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

M = 100.0  # meters -> Unreal units (cm)
ROOT_FOLDER = "Carrowgate Garrison"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CUBE_MESH = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")

if CUBE_MESH is None:
    unreal.log_error("[Carrowgate Blockout] Could not load /Engine/BasicShapes/Cube.Cube -- aborting.")
    raise SystemExit

# Bevelled-edge cube from the same LevelPrototyping pack as the grid materials
# below -- used for ground plates so the footprint's top edges read as chamfered
# instead of razor-sharp 90-degree cube corners. Loaded defensively: if it's
# ever missing, ground plates just fall back to the sharp engine cube instead of
# the script aborting.
CHAMFER_MESH = unreal.EditorAssetLibrary.load_asset("/Game/LevelPrototyping/Meshes/SM_ChamferCube.SM_ChamferCube")
if CHAMFER_MESH is None:
    unreal.log_warning("[Carrowgate Blockout] SM_ChamferCube not found -- ground plates will keep sharp cube edges.")


# ---------------------------------------------------------------------------
# Materials. Real-texture pass: these now load the AI-generated (Meshy)
# materials built by import_ai_textures.py -- concrete wall, wet concrete
# ground, diamond-plate steel ramp, wood/metal furniture -- instead of the
# flat prototype-grid colorways from the earlier pass. Still one colorway per
# function so walls/floor/ramp/furniture read apart from each other at a
# glance. Loaded with a fallback: if import_ai_textures.py hasn't been run
# yet (or a texture failed to import), each one falls back to its old
# prototype-grid material instead of the engine's flat default grey, so this
# script still works standalone -- just less pretty -- if run out of order.
# ---------------------------------------------------------------------------

def load_mat(path):
    mat = unreal.EditorAssetLibrary.load_asset(path)
    if mat is None:
        unreal.log_warning(f"[Carrowgate Blockout] Material not found at '{path}' -- affected meshes will keep the engine default grey.")
    return mat


def load_mat_with_fallback(primary_path, fallback_path, label):
    """fallback_path may be None -- callers that already have a fallback material
    loaded elsewhere (e.g. MAT_FLATCOL_BASE, MAT_FURNITURE) pass None here and
    `or` in their own fallback afterward instead of loading a second asset."""
    mat = unreal.EditorAssetLibrary.load_asset(primary_path)
    if mat is not None:
        return mat
    unreal.log_warning(f"[Carrowgate Blockout] {label} not found at '{primary_path}' -- run import_ai_textures.py first. Falling back to the previous material for now.")
    return load_mat(fallback_path) if fallback_path else None


MAT_WALL = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Wall.M_AI_Wall",
    "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray.MI_PrototypeGrid_Gray", "M_AI_Wall")
MAT_GROUND = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground",
    "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_TopDark.MI_PrototypeGrid_TopDark", "M_AI_Ground")
MAT_RAMP = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Ramp.M_AI_Ramp",
    "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray_02.MI_PrototypeGrid_Gray_02", "M_AI_Ramp")
MAT_FURNITURE = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Furniture.M_AI_Furniture",
    "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray_Round.MI_PrototypeGrid_Gray_Round", "M_AI_Furniture")
MAT_FLATCOL_BASE = load_mat("/Game/LevelPrototyping/Materials/M_FlatCol.M_FlatCol")

# Round 2 of the AI texture pass: water + the Vehicle Bay/Docks/Harbor props,
# which were all still riding on MAT_FURNITURE or a flat dynamic tint.
# Fallback for these is MAT_FURNITURE/MAT_FLATCOL_BASE -- what they were using
# before this pass -- so a script run before import_ai_textures.py has picked
# these up just looks like the previous pass instead of erroring.
MAT_WATER = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Water.M_AI_Water", None, "M_AI_Water") or MAT_FLATCOL_BASE
MAT_VEHICLE = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Vehicle.M_AI_Vehicle", None, "M_AI_Vehicle") or MAT_FURNITURE
MAT_SHIP = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Ship.M_AI_Ship", None, "M_AI_Ship") or MAT_FURNITURE
MAT_CRANE = load_mat_with_fallback(
    "/Game/LevelPrototyping/AITextures/M_AI_Crane.M_AI_Crane", None, "M_AI_Crane") or MAT_FURNITURE

# Real door prop. Doorway gaps used to be bare cutouts in the walls -- this is
# an existing, unused Blueprint in the project (frame + door leaf) placed at
# each room's doorway instead. Rotation/fit is a first guess (matches this
# script's usual "verify by hand once you can walk it" approach for anything
# placed without being able to see it) -- door_width/door_height above are
# 1.6m/2.4m, whatever BP_DoorFrame's own authored size is may not match
# exactly; nudge it in the editor if the gap and the frame don't line up.
_DOOR_FRAME_PATH = "/Game/LevelPrototyping/Interactable/Door/BP_DoorFrame"
DOOR_FRAME_CLASS = None
if unreal.EditorAssetLibrary.does_asset_exist(_DOOR_FRAME_PATH):
    # load_blueprint_class appends "_C" itself -- passing the plain Blueprint
    # asset path (not a manually-suffixed ".BP_DoorFrame_C" object path) is what
    # it expects. The manual suffix was what made this fail last run (log showed
    # LoadBlueprintClass failed: AssetData '...BP_DoorFrame.BP_DoorFrame_C' could
    # not be found in the Asset Registry).
    DOOR_FRAME_CLASS = unreal.EditorAssetLibrary.load_blueprint_class(_DOOR_FRAME_PATH)
if DOOR_FRAME_CLASS is None:
    unreal.log_warning("[Carrowgate Blockout] BP_DoorFrame not found/loadable -- doorways will stay bare cutouts, no frame prop placed.")


def safe(fn, label):
    """Runs fn(), logging a warning and continuing instead of aborting the whole script on failure."""
    try:
        fn()
    except Exception as e:  # noqa: BLE001 -- deliberately broad, this is a one-shot editor tool
        unreal.log_warning(f"[Carrowgate Blockout] Skipped '{label}': {e}")


def cleanup_previous_run():
    """Deletes anything left over from an earlier run of this script so re-running it is safe
    (idempotent) instead of stacking duplicate cubes on top of each other."""
    removed = 0
    for a in actor_subsystem.get_all_level_actors():
        try:
            folder = str(a.get_folder_path())
        except Exception:
            continue
        if folder == ROOT_FOLDER or folder.startswith(ROOT_FOLDER + "/"):
            actor_subsystem.destroy_actor(a)
            removed += 1
    if removed:
        unreal.log(f"[Carrowgate Blockout] Cleared {removed} actor(s) from a previous run before rebuilding.")


safe(cleanup_previous_run, "Cleanup previous run")


def spawn_block(label, folder, location_m, size_m, rotation_deg=(0.0, 0.0, 0.0), material=MAT_WALL, mesh=None, base_pivot=False):
    """Spawns a StaticMeshActor cube blockout. location_m is the box CENTER in meters.
    material defaults to the prototype-grid wall material (MAT_WALL) -- pass material=
    MAT_GROUND / MAT_RAMP / MAT_FURNITURE / None explicitly for anything that isn't a
    wall/ceiling/gate pylon (None leaves the engine's flat-grey default untouched).
    mesh defaults to the sharp-edged engine cube; pass mesh=CHAMFER_MESH for a
    bevelled-edge block instead (used for ground plates so the footprint reads less
    blocky up close). base_pivot=True means the mesh's pivot sits at its base rather
    than its center -- true of most LevelPrototyping kit meshes, unlike the engine
    cube's center pivot -- and the actor gets nudged down by half its height so
    location_m still means "box center" at every call site regardless of which mesh
    is used. UPDATE: first guess was base_pivot=True for SM_ChamferCube -- wrong. It's
    center-pivoted just like the engine cube, same as everything else in this script.
    That guess sank every ground/pad/ramp surface down by half its own thickness while
    the buildings (still on the plain cube) stayed put, which is what read as "all the
    buildings floating." All call sites below now pass base_pivot=False -- left as a
    parameter in case a future mesh actually needs it, but don't default any new call
    site to True without confirming the mesh's pivot first."""
    location = unreal.Vector(location_m[0] * M, location_m[1] * M, location_m[2] * M)
    rotation = unreal.Rotator(rotation_deg[0], rotation_deg[1], rotation_deg[2])
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/{folder}")

    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(mesh if mesh is not None else CUBE_MESH)
    # The engine cube (and this pack's kit meshes, same authoring convention) is
    # 100x100x100uu (1m^3), so world scale == desired size in meters.
    mesh_comp.set_world_scale3d(unreal.Vector(size_m[0], size_m[1], size_m[2]))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    if base_pivot:
        actor.set_actor_location(unreal.Vector(location.x, location.y, location.z - (size_m[2] * M) / 2.0), False, False)
    return actor


def spawn_mesh_actor(label, folder, asset_path, loc_m, rotation_deg=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0), material=None):
    """Spawns a StaticMeshActor using a real imported mesh asset (e.g. a Meshy-generated
    model via import_ai_models.py) instead of a scaled unit cube. loc_m is the actor's
    world location in meters -- NOT a box center like spawn_block/prop_block use, since a
    real mesh carries its own pivot. Meshy exports downloaded with Origin=Bottom sit flush
    on their base at loc_m's Z with no half-height offset needed. Returns None (no actor
    spawned) if asset_path doesn't exist yet, so callers can fall back to a placeholder
    prop_block() cleanly instead of erroring out."""
    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    if mesh is None:
        return None
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    rotation = unreal.Rotator(rotation_deg[0], rotation_deg[1], rotation_deg[2])
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(mesh)
    mesh_comp.set_world_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    return actor


def spawn_door_frame(label, folder, loc_m, yaw_deg):
    """Places the real BP_DoorFrame prop at a doorway gap instead of leaving it a bare
    cutout. yaw_deg is a first guess (0 for a gap in a north/south wall running along X,
    90 for a gap in an east/west wall running along Y) -- verify/rotate by hand once it's
    visible, same as this script's other placed-blind guesses (ramp roll, sea wall, etc.)."""
    if DOOR_FRAME_CLASS is None:
        return
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    rotation = unreal.Rotator(0.0, 0.0, yaw_deg)
    door = actor_subsystem.spawn_actor_from_class(DOOR_FRAME_CLASS, location, rotation)
    door.set_actor_label(f"{label}_DoorFrame")
    door.set_folder_path(f"{ROOT_FOLDER}/{folder}")


def spawn_room(area_id, name, folder, loc_m, size_m, door_side="south",
                wall_thickness=0.3, door_width=1.6, door_height=2.4):
    """Builds a hollow, ENTERABLE room out of wall/ceiling cubes, with a doorway gap
    on door_side ('north'/'south'/'east'/'west'). No dedicated floor slab -- the
    shared Ground segments underneath already serve as the floor, same as they do for
    every solid pad, so this drops straight into the existing footprint. loc_m/size_m
    use the exact same center/size convention as spawn_block, so swapping an area from
    a solid pad to a room doesn't move or resize it."""
    cx, cy, cz = loc_m
    sx, sy, sz = size_m
    base_z = cz - sz / 2.0
    ceiling_t = wall_thickness
    wall_h = sz - ceiling_t
    wall_cz = base_z + wall_h / 2.0
    label = f"{area_id:02d}_{name}"

    def solid_wall(suffix, center, size):
        spawn_block(f"{label}_{suffix}", folder, center, size)

    def doored_wall_x(suffix, wall_y):
        """North/south wall: runs along X, split around a door gap centered on X."""
        side_len = (sx - door_width) / 2.0
        if side_len > 0.05:
            solid_wall(f"{suffix}_L", (cx - (door_width / 2.0 + side_len / 2.0), wall_y, wall_cz), (side_len, wall_thickness, wall_h))
            solid_wall(f"{suffix}_R", (cx + (door_width / 2.0 + side_len / 2.0), wall_y, wall_cz), (side_len, wall_thickness, wall_h))
        lintel_h = wall_h - door_height
        if lintel_h > 0.05:
            solid_wall(f"{suffix}_Lintel", (cx, wall_y, base_z + door_height + lintel_h / 2.0), (door_width, wall_thickness, lintel_h))

    def doored_wall_y(suffix, wall_x):
        """East/west wall: runs along Y, split around a door gap centered on Y."""
        side_len = (sy - door_width) / 2.0
        if side_len > 0.05:
            solid_wall(f"{suffix}_L", (wall_x, cy - (door_width / 2.0 + side_len / 2.0), wall_cz), (wall_thickness, side_len, wall_h))
            solid_wall(f"{suffix}_R", (wall_x, cy + (door_width / 2.0 + side_len / 2.0), wall_cz), (wall_thickness, side_len, wall_h))
        lintel_h = wall_h - door_height
        if lintel_h > 0.05:
            solid_wall(f"{suffix}_Lintel", (wall_x, cy, base_z + door_height + lintel_h / 2.0), (wall_thickness, door_width, lintel_h))

    north_y, south_y = cy + sy / 2.0, cy - sy / 2.0
    east_x, west_x = cx + sx / 2.0, cx - sx / 2.0

    if door_side == "north":
        doored_wall_x("Wall_N", north_y)
        solid_wall("Wall_S", (cx, south_y, wall_cz), (sx, wall_thickness, wall_h))
    elif door_side == "south":
        solid_wall("Wall_N", (cx, north_y, wall_cz), (sx, wall_thickness, wall_h))
        doored_wall_x("Wall_S", south_y)
    else:
        solid_wall("Wall_N", (cx, north_y, wall_cz), (sx, wall_thickness, wall_h))
        solid_wall("Wall_S", (cx, south_y, wall_cz), (sx, wall_thickness, wall_h))

    if door_side == "east":
        doored_wall_y("Wall_E", east_x)
        solid_wall("Wall_W", (west_x, cy, wall_cz), (wall_thickness, sy, wall_h))
    elif door_side == "west":
        solid_wall("Wall_E", (east_x, cy, wall_cz), (wall_thickness, sy, wall_h))
        doored_wall_y("Wall_W", west_x)
    else:
        solid_wall("Wall_E", (east_x, cy, wall_cz), (wall_thickness, sy, wall_h))
        solid_wall("Wall_W", (west_x, cy, wall_cz), (wall_thickness, sy, wall_h))

    spawn_block(f"{label}_Ceiling", folder, (cx, cy, base_z + sz - ceiling_t / 2.0), (sx, sy, ceiling_t))

    door_gap_positions = {
        "north": ((cx, north_y, base_z), 0.0),
        "south": ((cx, south_y, base_z), 0.0),
        "east": ((east_x, cy, base_z), 90.0),
        "west": ((west_x, cy, base_z), 90.0),
    }
    if door_side in door_gap_positions:
        door_loc, door_yaw = door_gap_positions[door_side]
        safe(lambda: spawn_door_frame(label, folder, door_loc, door_yaw), f"{label} door frame")


def spawn_gate_arch(area_id, name, folder, loc_m, size_m, gate_width=4.0, gate_height=4.5):
    """A standalone checkpoint wall you walk/drive straight through -- two pylons
    flanking an opening, with a lintel above -- rather than a fully enclosed room.
    Used for Main Gate, since the 'building' there is a threshold, not a space you
    stop and stand in."""
    cx, cy, cz = loc_m
    sx, sy, sz = size_m  # sx = gate depth (X, the thin "through" axis), sy = width, sz = height
    base_z = cz - sz / 2.0
    label = f"{area_id:02d}_{name}"
    side_len = (sy - gate_width) / 2.0
    if side_len > 0.05:
        spawn_block(f"{label}_Pylon_L", folder, (cx, cy - (gate_width / 2.0 + side_len / 2.0), cz), (sx, side_len, sz))
        spawn_block(f"{label}_Pylon_R", folder, (cx, cy + (gate_width / 2.0 + side_len / 2.0), cz), (sx, side_len, sz))
    lintel_h = sz - gate_height
    if lintel_h > 0.05:
        spawn_block(f"{label}_Lintel", folder, (cx, cy, base_z + gate_height + lintel_h / 2.0), (sx, gate_width, lintel_h))


# ---------------------------------------------------------------------------
# Area data: id, display name, outliner folder, center location (m), size (m),
# a note carried over from the sheet's callouts, and how to build it:
#   kind="room" -> hollow, enterable (spawn_room), door faces `door`
#   kind="gate" -> pass-through checkpoint arch (spawn_gate_arch)
#   kind="pad"  -> solid flat slab (spawn_block), the default -- for open yards,
#                  not buildings (Vehicle Bay, Parade Yard, Helipad, Sea Wall,
#                  Civic Route, Docks/Harbor). These are thin (5cm) marker slabs
#                  sitting flush on TOP of the shared Ground segments (top surface at
#                  Z=0, matching every room's floor) -- NOT tall extruded blocks.
#                  An earlier version made them tall (Parade Yard's top sat at
#                  0.5m, Vehicle Bay's at 3m), which poked up through the walls
#                  of any adjacent room built at floor level -- that's what was
#                  clipping into the Mess Hall. Sea Wall is the deliberate
#                  exception: it's supposed to stick up as an actual barrier.
#                  Docks/Harbor is also exempt: it's intentionally a full lower
#                  deck, not a thin overlay, since it sits ~4m below Z=0.
# `door` faces roughly toward the cluster's centroid (~66, ~-2).
#
# POSITIONS BELOW were re-derived directly from the reference sheet's area map
# (the numbered pin diagram), not eyeballed: pin pixel coordinates were read
# off the source image and converted to world meters (same origin/scale as
# before -- Main Gate stays at world (0,0)). The real shape is NOT a neat grid:
# Watch Tower + Sensor Array sit on a narrow spur at the NORTH tip, Main Gate
# is an isolated point at the WEST tip, and Docks/Harbor sits well south and
# east of the main cluster, reached by a long ramp/causeway -- not just
# offset a few meters from Command & Comms like the first pass had it. A few
# pins (Vehicle Bay, Parade Yard, Barracks, Helipad, Sea Wall, Civic Route)
# were harder to read at source resolution -- if any of those look off once
# you can walk it, they're the ones to double check first.
# ---------------------------------------------------------------------------

AREAS = [
    dict(id=1, name="Main Gate", loc=(0, 0, 3), size=(4, 12, 6), kind="gate",
         note="Fortified entry, ID scanning. Outer road continues west, off-map. "
              "Isolated at the west tip of the complex, per the area map."),
    dict(id=2, name="Vehicle Bay", loc=(35, -3, 0.025), size=(25, 18, 0.05), kind="pad",
         note="Open yard -- add 2-3 vehicle boxes (~8.5x3x3m) once real trucks exist."),
    dict(id=3, name="Parade Yard", loc=(46, 16, 0.025), size=(40, 32, 0.05), kind="pad",
         note="Open flat staging ground for formation / briefings. Central hub where "
              "the map's main paths converge."),
    dict(id=4, name="Watch Tower", loc=(56, 44, 11), size=(7, 7, 22), kind="room", door="south",
         note="Tall thin tower, overlooks coast/harbor. Vertical traversal beat. On its "
              "own spur at the NORTH tip of the complex, per the area map. Blockout is "
              "one hollow shaft top-to-bottom -- worth manually adding an intermediate "
              "floor + ladder gap and opening the top into a railed observation deck "
              "once you're past greybox."),
    dict(id=5, name="Barracks", loc=(55, -32, 3), size=(20, 12, 6), kind="room", door="south",
         note="Player starts here. Living quarters, spartan/functional. Door faces the "
              "PlayerStart just south of it, so they land looking straight at it. (Door "
              "side kept as-is from the previous pass -- only its world position moved "
              "-- so the existing furniture layout, which assumes this door side, "
              "didn't need to be redone.)"),
    dict(id=6, name="Mess Hall", loc=(96, 8, 2.5), size=(18, 15, 5), kind="room", door="south",
         note="Vending, seating, info boards, passive NPCs."),
    dict(id=7, name="Armory", loc=(112, -15, 2.5), size=(12, 12, 5), kind="room", door="north",
         note="Reinforced walls, equipment checks. Door faces back toward the main cluster."),
    dict(id=8, name="Command & Comms", loc=(73, -61, 4), size=(15, 12, 8), kind="room", door="west",
         note="Taller building, roof antenna array. South of Barracks."),
    dict(id=9, name="Sensor Array", loc=(59, 30, 5), size=(8, 8, 10), kind="room", door="south",
         note="Raised platform w/ dish; radio/sensor tutorial beat immediately south of "
              "Watch Tower on the same north spur."),
    dict(id=10, name="Helipad", loc=(136, -36, 0.025), size=(20, 20, 0.05), kind="pad",
         note="Flat pad, civilian evac + resupply. East coastal edge, near Docks/Harbor."),
    dict(id=11, name="Sea Wall", loc=(145, -40, 1.5), size=(2, 35, 3), kind="pad",
         note="Long barrier along the coast edge. Kept axis-aligned and inside the "
              "SE_CoastalReach_Helipad ground segment's bounds -- an earlier angled "
              "version (rotated -60 deg, 90m long, centered further south than any "
              "ground segment reached) had most of its length hanging unsupported "
              "over open water, reading as a big diagonal floating sheet. Unlike the "
              "other pads, this one is meant to stick up as an actual barrier, not "
              "sit flush with the ground."),
    dict(id=12, name="Civic Route (Streets)", loc=(95, -77.5, 0.025), size=(10, 30, 0.05), kind="pad",
         note="Evac road toward Docks/Harbor and the civilian district beyond it, "
              "off-map. Shortened + de-rotated to fit inside the SouthTaper_CivicRoute "
              "ground segment -- same floating-sheet problem as Sea Wall: it was 60m "
              "long and rotated, but the ground under it only covered ~35m."),
    dict(id=13, name="Docks / Harbor", loc=(116, -126, -3.85), size=(45, 65, 0.3), kind="pad",
         note="Lower pier, ~4m drop from the main platform, and well south/east of the "
              "main cluster -- a separate landmass on the area map reached by a long "
              "causeway, not just a short hop from Command & Comms. Add ship/crane "
              "blockouts."),
]

for area in AREAS:
    label = f"{area['id']:02d}_{area['name']}"
    kind = area.get("kind", "pad")
    if kind == "room":
        spawn_room(area["id"], area["name"], area["name"], area["loc"], area["size"], door_side=area.get("door", "south"))
    elif kind == "gate":
        spawn_gate_arch(area["id"], area["name"], area["name"], area["loc"], area["size"])
    else:
        spawn_block(label, area["name"], area["loc"], area["size"], rotation_deg=area.get("rot", (0.0, 0.0, 0.0)), material=MAT_GROUND, mesh=CHAMFER_MESH, base_pivot=False)

# ---------------------------------------------------------------------------
# Placeholder props for the two pads whose AREAS notes explicitly call for
# them -- Vehicle Bay ("add 2-3 vehicle boxes") and Docks/Harbor ("Add
# ship/crane blockouts"). Simple boxes, same fidelity as everything else in
# this pass -- not real vehicle/ship/crane meshes, just enough shape and scale
# to read as "there's stuff here" instead of a bare pad. Uses the file's own
# scale reference from the header (8.5m vehicle, 22m ship). MAT_FURNITURE
# (same colorway used for interior furniture) so these read as placed objects
# rather than structure, consistent with the rest of the material pass.
# ---------------------------------------------------------------------------

def prop_block(label, folder, loc_m, size_m, rot_z=0.0, material=MAT_FURNITURE):
    """Places one placeholder prop. loc_m is the box CENTER in meters, same convention
    as spawn_block/furn() elsewhere in this script."""
    spawn_block(label, folder, loc_m, size_m, rotation_deg=(0.0, 0.0, rot_z), material=material)


def add_vehicle_bay_props():
    # Vehicle Bay pad: loc=(35,-3,0.025), size=(25,18,0.05) -> top at Z=0.05,
    # spans X=[22.5,47.5] Y=[-12,6]. Three ~8.5x3x3m vehicle boxes parked in a
    # row, long axis along X (the pad's long axis), staggered slightly in X so
    # they don't read as three identical boxes in a perfect line.
    top_z = 0.05
    veh_size = (8.5, 3.0, 3.0)
    cz = top_z + veh_size[2] / 2.0

    # Pilot: Truck_01 uses the real Meshy-generated mesh (import_ai_models.py) if it's
    # been imported yet; otherwise falls back to the same placeholder box as 02/03. Only
    # one truck is swapped for now -- see if this looks right before doing the rest.
    real_truck = spawn_mesh_actor(
        "VehicleBay_Truck_01", "Vehicle Bay",
        "/Game/LevelPrototyping/AIModels/SM_Truck_Cargo.SM_Truck_Cargo",
        (32.0, -8.0, top_z), material=MAT_VEHICLE)
    if real_truck is None:
        unreal.log_warning("[Carrowgate Blockout] SM_Truck_Cargo not found -- run import_ai_models.py first (after moving the downloaded FBX into Content/LevelPrototyping/AIModels/). Using placeholder box for Truck_01 for now.")
        prop_block("VehicleBay_Truck_01", "Vehicle Bay", (32.0, -8.0, cz), veh_size, material=MAT_VEHICLE)

    prop_block("VehicleBay_Truck_02", "Vehicle Bay", (36.5, -3.0, cz), veh_size, material=MAT_VEHICLE)
    prop_block("VehicleBay_Truck_03", "Vehicle Bay", (33.5, 2.0, cz), veh_size, material=MAT_VEHICLE)


safe(add_vehicle_bay_props, "Vehicle Bay placeholder props")


def add_docks_harbor_props():
    # Docks/Harbor pad: loc=(116,-126,-3.85), size=(45,65,0.3) -> top at
    # Z=-3.7, spans X=[93.5,138.5] Y=[-158.5,-93.5]. One ~22m ship blockout
    # (hull + a smaller deckhouse box near the stern) docked along the pad's
    # long (Y) axis, plus two simple cranes (mast + jib) near its bow for
    # loading. All well clear of the ramp's footprint (centered X=107,
    # Y=-107..-120) and the Sea Wall/Helipad area further north.
    dock_top = -3.7

    hull_size = (7.0, 22.0, 5.0)
    hull_cz = dock_top + hull_size[2] / 2.0
    hull_loc = (104.0, -145.0, hull_cz)
    prop_block("Docks_Ship_Hull", "Docks / Harbor", hull_loc, hull_size, material=MAT_SHIP)

    deckhouse_size = (6.0, 6.0, 3.0)
    deckhouse_loc = (104.0, -153.0, dock_top + hull_size[2] + deckhouse_size[2] / 2.0)
    prop_block("Docks_Ship_Deckhouse", "Docks / Harbor", deckhouse_loc, deckhouse_size, material=MAT_SHIP)

    def crane(label, loc_xy):
        cx, cy = loc_xy
        mast_size = (1.5, 1.5, 10.0)
        mast_cz = dock_top + mast_size[2] / 2.0
        prop_block(f"{label}_Mast", "Docks / Harbor", (cx, cy, mast_cz), mast_size, material=MAT_CRANE)
        jib_size = (1.0, 12.0, 1.0)
        jib_cz = dock_top + mast_size[2] + jib_size[2] / 2.0
        # Jib overhangs from the mast toward the ship (offset half its own
        # length along Y) rather than being centered on the mast, like a real
        # crane arm swung out over the water/hull instead of straight up.
        prop_block(f"{label}_Jib", "Docks / Harbor", (cx, cy - jib_size[1] / 2.0, jib_cz), jib_size, material=MAT_CRANE)

    # Both kept south of Y=-120 -- the ramp's footprint now runs roughly
    # X=[99,115] Y=[-120,-94] (see the ramp block below), so anything north of
    # -120 in that X band risks clipping through it.
    crane("Docks_Crane_01", (110.0, -132.0))
    crane("Docks_Crane_02", (110.0, -126.0))


safe(add_docks_harbor_props, "Docks / Harbor placeholder props")

# Ramp connecting the main platform (near Civic Route) down to the Docks/Harbor
# causeway -- the sheet's "multiple vertical layers for traversal" note made
# concrete.
#
# Fixed along the way: unreal.Rotator's Python constructor takes (roll, pitch,
# yaw) -- roll spins around local X (tilts a Y-long box along its length), so
# the slope needed to be in the roll slot, not pitch. Also: LightColor-style
# mismatches aside, when the length got stretched from 55m to 70m for more
# overlap, the roll angle didn't get re-solved for the new half-length, so it
# swung the platform end up past Z=0 -- fixed by re-deriving the angle from
# whatever half-length is actually in play, which is what the point below is
# for.
#
# Re-derived properly this time instead of eyeballing another stretch, since
# stretching it symmetrically last time was itself the bug that caused "too
# large a gap": extending both ends equally moves the platform end TOWARD
# SouthTaper_CivicRoute's far edge (its Y-span is [-95, -60]), not deeper into
# it -- 70m long centered at Y=-101 put that end at Y=-66, just 6m shy of
# falling off the far edge entirely once yaw and the tilt's real footprint are
# factored in. That thin margin is the gap in the screenshot.
#
# That 20m-deep overlap into the platform (previous version) turned out to be
# its own new bug, found by actually walking it in PIE: GROUND_SEGMENTS slabs
# are a CONSTANT 1m thick (top=0, bottom=-1.0) across their whole footprint --
# they don't taper down to meet a ramp. With the ramp still well below Z=-1.0
# for a long stretch while already horizontally under the platform's overlap
# zone, the platform's solid underside was a literal ceiling blocking the
# climb -- "the platform in the way," exactly as reported, not a slope or
# collision-snag problem.
#
# Fix: the ramp needs to clear Z=-1.0 (platform's underside) BEFORE it enters
# the platform's Y-footprint (Y=-95), not gradually while already buried under
# it. That means less overlap on the platform end AND a steeper angle so it
# climbs fast enough to clear the underside in the shorter distance it now has
# before reaching the edge -- still nowhere near the ~44 degree walkable
# limit, so steeper is fine here.
#   - North/platform end targeted at Y=-94 (1m past SouthTaper_CivicRoute's
#     south edge at Y=-95 -- just enough overlap for a clean seam, not a deep
#     tunnel under the slab), top=0.
#   - South/Docks end kept at Y=-120 (26.5m inside the Docks/Harbor pad,
#     Y=[-158.5,-93.5]) -- that end wasn't the one reported as blocked, and
#     the Docks pad is only 0.3m thick so the same problem is far less likely
#     there regardless.
#   Center Y = (-94 + -120) / 2 = -107. Length = -94 - (-120) = 26m
#   (half-length 13m).
# Z: same top targets as before (0 at the platform end, -3.7 at the Docks
#   end -- Docks/Harbor pad: loc.z=-3.85 + half its 0.3 thickness). Centerline
#   targets (top minus the ramp's own half-thickness, 0.2m): -0.2 at the
#   platform end, -3.9 at the Docks end -> center Z=-2.0, half-swing 1.85m
#   over the new 13m half-length: asin(1.85 / 13) =~ 8.2 degrees. At that
#   angle the ramp clears Z=-1.0 by Y=-99.7, about 5m before it ever reaches
#   the platform's Y=-95 edge, so there's no stretch left where it's both
#   below the underside AND under the slab.
# Yaw keeps the small plan-view alignment nudge from before. Roll's sign is
# still a first guess at which end dips -- flip to +8.2 if the platform end
# sinks instead of the Docks end.
spawn_block("Platform-to-Docks Ramp", "Docks / Harbor", (107, -107, -2.0), (16, 26, 0.4), (-8.2, 0.0, -4.0), material=MAT_RAMP, mesh=CHAMFER_MESH, base_pivot=False)

# ---------------------------------------------------------------------------
# Ground. NOT a single rectangle -- the reference area map's landmass is an
# irregular arrow/star shape, not a square: a narrow north spur for Watch
# Tower/Sensor Array, a thin west arm out to the isolated Main Gate, a wide
# central body, and a south/east reach toward Command & Comms and Helipad.
# So the ground is built from several overlapping slabs that trace that
# outline (a "staircase" approximation using axis-aligned boxes, each
# generously overlapping its neighbors so there's no seam/gap), instead of
# one big rectangle covering the whole bounding box. Every segment still
# sits with its top surface at Z=0, same convention as before -- swapping
# the single slab for several didn't change floor height anywhere.
# ---------------------------------------------------------------------------
GROUND_SEGMENTS = [
    # name,                      (center X, center Y), (size X, size Y)
    ("GateApproach", (2.5, 0.0), (25, 20)),           # around Main Gate's isolated tip
    ("WestConnector", (25.0, 2.0), (30, 20)),         # thin arm bridging gate to the main body
    ("NW_Yard", (47.5, -2.5), (55, 35)),              # Vehicle Bay / lower Parade Yard
    ("NorthSpur_WatchTower", (57.5, 33.5), (35, 43)),  # narrower spur: Watch Tower + Sensor Array
    ("CentralBody_Barracks", (65.0, -15.0), (50, 60)),  # Barracks / core
    ("EastWing_MessHallArmory", (100.0, -2.5), (50, 55)),  # Mess Hall + Armory
    ("SouthWing_Command", (72.5, -57.5), (35, 35)),    # Command & Comms
    ("SE_CoastalReach_Helipad", (125.0, -37.5), (50, 45)),  # toward Helipad/Sea Wall
    ("SouthTaper_CivicRoute", (95.0, -77.5), (40, 35)),  # Civic Route, tapering toward the causeway
]
for seg_name, (gx, gy), (gsx, gsy) in GROUND_SEGMENTS:
    spawn_block(f"Ground_{seg_name}", "Ground", (gx, gy, -0.5), (gsx, gsy, 1.0), material=MAT_GROUND, mesh=CHAMFER_MESH, base_pivot=False)

# ---------------------------------------------------------------------------
# Corner fillets -- tried twice, pulled both times (SM_QuarterCylinderOuter:
# thin shell, floating slivers; SM_QuarterCylinder: same underlying problem).
# The real issue isn't the mesh choice: every ground segment is still a full,
# sharp-cornered box. Placing a curved piece next to or on top of that corner
# doesn't cut the box's own corner away -- it's still there at full size
# underneath, so the square shape keeps showing through no matter what gets
# added alongside it. This is different from the chamfered top edges above,
# which work because that swaps the segment's OWN mesh for one bevelled from
# the start -- there's no separate box to hide there.
#
# Actual corner rounding needs the segment's corner physically cut away (split
# into an L-shape with a real notch) with a curved piece filling that notch --
# a geometry rewrite, not a mesh swap. Not attempting that blind a third time;
# flag if you want that done properly and it's a bigger, separate pass.
# ---------------------------------------------------------------------------

# Water. One big placeholder ocean plane, centered under the whole complex and
# sized way past every edge, so the garrison + docks read as rising out of
# water on all sides rather than water only existing on the Docks/Sea Wall
# side. Sits well below Z=0 (the platform's floor level) and just under the
# Docks/Harbor deck (top at -3.7m), same water-level logic as before.
#
# Now uses MAT_WATER -- the AI-generated ocean texture from import_ai_textures.py
# -- instead of a flat tinted color. Still just a base-color image on a flat
# plane, not an actual water shader (no waves/refraction/depth-based color);
# swap in a proper water body (Water plugin) once past greybox.
_water_actor = spawn_block("Water_Placeholder", "Ground", (100, -40, -4.6), (3000, 3000, 0.3), material=MAT_WATER)


def tint_water():
    """Only matters if MAT_WATER fell back to MAT_FLATCOL_BASE (AI water texture
    not imported yet, per the fallback in load_mat_with_fallback above) -- tints
    that flat placeholder blue-teal so it still reads as water instead of
    whatever M_FlatCol's raw default color is. Skipped once the real AI ocean
    texture is in place; tinting a photo would just wash it out, not help it."""
    if _water_actor is None or MAT_WATER is not MAT_FLATCOL_BASE:
        return
    mid = _water_actor.static_mesh_component.create_dynamic_material_instance(0, MAT_FLATCOL_BASE)
    for param_name in ("Color", "BaseColor", "Base Color", "Tint"):
        try:
            mid.set_vector_parameter_value(param_name, unreal.LinearColor(0.05, 0.18, 0.28, 1.0))
            return
        except Exception:
            continue
    unreal.log_warning("[Carrowgate Blockout] Could not find a color parameter on M_FlatCol -- water left at its default color.")


safe(tint_water, "Water tint (fallback-only)")


# ---------------------------------------------------------------------------
# PlayerStart -- Barracks ("Player starts here" on the sheet). Barracks' door
# is on its SOUTH wall, so the PlayerStart sits just south of it, facing
# north back toward the doorway.
# ---------------------------------------------------------------------------

def add_player_start():
    ps = actor_subsystem.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(55 * M, -41 * M, 1 * M), unreal.Rotator(0, 90, 0)
    )
    ps.set_actor_label("PS_Barracks_MissionStart")
    ps.set_folder_path(f"{ROOT_FOLDER}/Barracks")


safe(add_player_start, "PlayerStart")


# ---------------------------------------------------------------------------
# NavMeshBoundsVolume over the whole footprint (needed for AIBKaijuSpawner's
# ground-projection spawn logic, and for any patrol/AI later). Widened south
# to reach the now much-further-away Docks/Harbor causeway.
# NOTE: a freshly spawned volume's default brush is a small (~2m) cube, so the
# scale below is an approximation to roughly cover the garrison -- verify by
# pressing P after running this and resize the volume by hand if the green
# nav mesh doesn't reach every walkable area.
# ---------------------------------------------------------------------------

def add_nav_volume():
    vol = actor_subsystem.spawn_actor_from_class(
        unreal.NavMeshBoundsVolume, unreal.Vector(100 * M, -42.5 * M, 7.5 * M), unreal.Rotator(0, 0, 0)
    )
    vol.set_actor_label("NavMeshBounds_CarrowgateGarrison")
    vol.set_folder_path(ROOT_FOLDER)
    vol.set_actor_scale3d(unreal.Vector(120, 97.5, 22.5))  # roughly 240m x 195m x 45m


safe(add_nav_volume, "NavMeshBoundsVolume")


# ---------------------------------------------------------------------------
# Rough pre-dawn / overcast lighting rig, per the sheet's Lighting/Time notes:
# "Pre-dawn, overcast. Sparse artificial lights. Emphasis on silhouettes and
# wet reflections." This is a base to dress with point lights later, not a
# finished pass.
# ---------------------------------------------------------------------------

def try_set(obj, prop, value):
    """Sets one editor property without letting a wrong/renamed property name in this
    engine version take down every property set after it (each call is independent)."""
    try:
        obj.set_editor_property(prop, value)
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[Carrowgate Blockout] Could not set '{prop}' on {obj}: {e}")


def add_lighting():
    sun = actor_subsystem.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 50 * M), unreal.Rotator(-8, 200, 0)
    )
    sun.set_actor_label("DirLight_PreDawn")
    sun.set_folder_path(f"{ROOT_FOLDER}/Lighting")
    sun_comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    # IMPORTANT: UE5 Lumen directional lights are physically based -- "Intensity" is in
    # LUX, not the old arbitrary 1-10 scale. 3.5 lux (near-moonlight) crushed the
    # viewport to black; 1500 lux then blew it out fully white once the camera was
    # actually framed on the scene. The real fix is below in the PostProcessVolume:
    # switch to MANUAL exposure so brightness stops depending on getting lux exactly
    # right against Lumen's auto-metering. These values just need to be "plausible
    # overcast," not tuned to hit a magic exposure number anymore.
    try_set(sun_comp, "intensity", 400.0)
    # Fixed: LightColor on a light component is an FColor (0-255 bytes), not an
    # FLinearColor (0-1 floats) -- same mismatch already fixed on the interior
    # point lights below (see WARM_INTERIOR's comment). This was silently
    # failing every run ("Could not set 'light_color' on
    # DirectionalLightComponent..." in the Output Log) and leaving the sun at
    # default white. 0.55/0.6/0.7 converted to bytes: ~140/153/179.
    try_set(sun_comp, "light_color", unreal.Color(140, 153, 179, 255))
    try_set(sun_comp, "atmosphere_sun_light", True)

    atmo = actor_subsystem.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    atmo.set_folder_path(f"{ROOT_FOLDER}/Lighting")

    sky = actor_subsystem.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    sky.set_folder_path(f"{ROOT_FOLDER}/Lighting")
    sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
    try_set(sky_comp, "intensity", 0.3)
    try_set(sky_comp, "real_time_capture", True)

    fog = actor_subsystem.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    fog.set_folder_path(f"{ROOT_FOLDER}/Lighting")
    fog_comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    try_set(fog_comp, "fog_density", 0.012)
    # Fixed: this property was renamed between engine versions -- UE5.8's
    # ExponentialHeightFogComponent has fog_inscattering_luminance, not
    # fog_inscattering_color (that name is gone; this was logging "Could not
    # find property 'fog_inscattering_color'" every run). Same LinearColor
    # type as before, just the new name.
    try_set(fog_comp, "fog_inscattering_luminance", unreal.LinearColor(0.35, 0.38, 0.45))

    # Unbound post-process volume: forces MANUAL exposure instead of leaving Lumen's
    # auto-exposure to meter the scene. Auto-exposure is what caused the black/white
    # whiplash -- it reacts to average scene luminance, which swings wildly in an
    # empty blockout depending on what's in frame. Manual mode makes brightness a
    # single predictable dial (auto_exposure_bias below) independent of scene content.
    ppv = actor_subsystem.spawn_actor_from_class(
        unreal.PostProcessVolume, unreal.Vector(50 * M, -7.5 * M, 10 * M), unreal.Rotator(0, 0, 0)
    )
    ppv.set_actor_label("PPV_Unbound_ManualExposure")
    ppv.set_folder_path(f"{ROOT_FOLDER}/Lighting")
    try_set(ppv, "unbound", True)
    try:
        settings = ppv.settings
        try_set(settings, "override_auto_exposure_method", True)
        try_set(settings, "auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
        try_set(settings, "override_auto_exposure_bias", True)
        # Walking this in from both ends: 6.0 overexposed, 0.0 and 3.0 were
        # both "way too dark," 5.0 was "too dark" but notably less severe --
        # the correct value sits in a fairly narrow band close to 6, not
        # spread evenly across the 0-6 range (consistent with each unit being
        # a full stop/2x -- most of the range is very dark and it brightens
        # fast right near the top). Nudging 5.0 -> 5.5, half a stop closer to
        # the overexposed value. If 5.5 overshoots back to washed-out, the
        # answer is between 5.0 and 5.5; if it's still dark, it's between 5.5
        # and 6.0 -- either way we're now bracketing a ~1-stop window instead
        # of guessing across the full range.
        try_set(settings, "auto_exposure_bias", 5.5)  # brightness dial: negative = darker, positive = brighter
        ppv.set_editor_property("settings", settings)
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[Carrowgate Blockout] Could not touch PostProcessVolume settings struct: {e}")


safe(add_lighting, "Lighting rig")


# ---------------------------------------------------------------------------
# OPTIONAL: distant, non-combat Kaiju silhouette for atmosphere only.
# Only runs if BP_Kaiju_Palawan already exists in this checkout.
# ---------------------------------------------------------------------------

def add_distant_palawan():
    bp_asset_path = "/Game/Kaiju/BP_Kaiju_Palawan"
    if not unreal.EditorAssetLibrary.does_asset_exist(bp_asset_path):
        unreal.log_warning(
            "[Carrowgate Blockout] BP_Kaiju_Palawan not found at /Game/Kaiju/ -- skipping distant "
            "silhouette (per Docs/HANDOFF_PROMPT.md this asset may not be persisted to every checkout "
            "yet). Create DA_Kaiju_Palawan (Class C, ~60m) + a BP_Kaiju_Palawan child of "
            "AIBCharacter_Kaiju, then re-run this function by hand once it exists."
        )
        return

    palawan_class = unreal.EditorAssetLibrary.load_blueprint_class(bp_asset_path + "." + bp_asset_path.split("/")[-1] + "_C")
    if palawan_class is None:
        unreal.log_warning(f"[Carrowgate Blockout] Found {bp_asset_path} but could not load it as a class -- skipping.")
        return

    silhouette = actor_subsystem.spawn_actor_from_class(
        palawan_class, unreal.Vector(400 * M, -20 * M, -5 * M), unreal.Rotator(0, 160, 0)
    )
    silhouette.set_actor_label("PALAWAN_DistantSilhouette")
    silhouette.set_folder_path(f"{ROOT_FOLDER}/Atmosphere")
    unreal.log(
        "[Carrowgate Blockout] Placed distant PALAWAN silhouette -- it scales up at BeginPlay "
        "(ApplySpecies), so verify its size/position in PIE, not just the editor viewport."
    )


safe(add_distant_palawan, "Distant Palawan silhouette")


# ---------------------------------------------------------------------------
# Furniture. Basic interior props for the 6 enterable buildings, sized off
# common real-world dimensions (bunk ~2.0x0.9x0.5m, locker ~0.5x0.5x2.0m,
# table ~1.5x0.8x0.75m, etc.) and placed relative to each building's own
# (cx, cy) center from AREAS, at its floor (Z=0, same as every room). If you
# move a building in AREAS, update its origin tuple below to match, or the
# furniture will spawn at the building's OLD position.
# ---------------------------------------------------------------------------

def furn(folder, prefix, name, origin_xy, base_z, dx, dy, dz, size_m, rot_z=0.0):
    """Places one furniture cube at (origin_xy + dx/dy, base_z + dz), sized size_m."""
    cx, cy = origin_xy
    sx, sy, sz = size_m
    center = (cx + dx, cy + dy, base_z + dz + sz / 2.0)
    spawn_block(f"{prefix}_{name}", folder, center, size_m, rotation_deg=(0.0, 0.0, rot_z), material=MAT_FURNITURE)


def add_furniture():
    BASE_Z = 0.0  # every furnished building's floor sits at Z=0, same as the Ground segments' top
    # Must match each building's (loc[0], loc[1]) in AREAS above -- these were
    # updated when the layout was corrected to match the reference area map.
    WATCH_TOWER = (56, 44)
    BARRACKS = (55, -32)
    MESS_HALL = (96, 8)
    ARMORY = (112, -15)
    COMMAND = (73, -61)
    SENSOR_ARRAY = (59, 30)

    # -- Watch Tower: overlook post, minimal furniture, a marker for the climb up. --
    furn("Watch Tower", "04", "SensorConsole", WATCH_TOWER, BASE_Z, 0.0, 2.6, 0.0, (1.4, 0.6, 1.2))
    furn("Watch Tower", "04", "Chair", WATCH_TOWER, BASE_Z, 0.0, 1.7, 0.0, (0.5, 0.5, 0.9))
    furn("Watch Tower", "04", "LadderMarker", WATCH_TOWER, BASE_Z, -2.4, -2.4, 0.0, (0.15, 0.6, 3.0))

    # -- Barracks: 4 bunks along the back wall, lockers flanking the door, a
    # notice board (per the M1 design doc's QUIET beat -- "the notice board"). --
    for i, dx in enumerate((-7.5, -2.5, 2.5, 7.5)):
        furn("Barracks", "05", f"Bunk_{i + 1:02d}", BARRACKS, BASE_Z, dx, 5.0, 0.0, (2.0, 0.9, 0.5))
    furn("Barracks", "05", "Locker_L", BARRACKS, BASE_Z, -7.0, -5.3, 0.0, (0.5, 0.5, 2.0))
    furn("Barracks", "05", "Locker_R", BARRACKS, BASE_Z, 7.0, -5.3, 0.0, (0.5, 0.5, 2.0))
    furn("Barracks", "05", "NoticeBoard", BARRACKS, BASE_Z, 9.6, 0.0, 1.0, (0.1, 1.5, 1.2))

    # -- Mess Hall: 3 tables + 6 benches down the middle, a vending machine, a
    # serving counter along the back wall. --
    for i, dx in enumerate((-5.0, 0.0, 5.0)):
        furn("Mess Hall", "06", f"Table_{i + 1:02d}", MESS_HALL, BASE_Z, dx, 0.5, 0.0, (1.5, 0.8, 0.75))
        furn("Mess Hall", "06", f"Bench_{i + 1:02d}A", MESS_HALL, BASE_Z, dx, -0.2, 0.0, (1.2, 0.35, 0.45))
        furn("Mess Hall", "06", f"Bench_{i + 1:02d}B", MESS_HALL, BASE_Z, dx, 1.2, 0.0, (1.2, 0.35, 0.45))
    furn("Mess Hall", "06", "VendingMachine", MESS_HALL, BASE_Z, -8.0, -5.0, 0.0, (0.9, 0.8, 1.9))
    furn("Mess Hall", "06", "ServingCounter", MESS_HALL, BASE_Z, 0.0, 6.5, 0.0, (6.0, 0.8, 1.1))

    # -- Armory: weapon racks along the back wall, lockers along both side
    # walls, a checkout counter near the door. --
    for i, dx in enumerate((-3.0, 0.0, 3.0)):
        furn("Armory", "07", f"WeaponRack_{i + 1:02d}", ARMORY, BASE_Z, dx, -5.0, 0.0, (1.2, 0.3, 2.0))
    for i, dy in enumerate((-3.0, 0.0, 3.0)):
        furn("Armory", "07", f"Locker_E{i + 1:02d}", ARMORY, BASE_Z, 5.0, dy, 0.0, (0.3, 0.5, 2.0))
        furn("Armory", "07", f"Locker_W{i + 1:02d}", ARMORY, BASE_Z, -5.0, dy, 0.0, (0.3, 0.5, 2.0))
    furn("Armory", "07", "CheckoutCounter", ARMORY, BASE_Z, -3.5, 4.5, 0.0, (1.5, 0.6, 1.0))

    # -- Command & Comms: a comms console opposite the door, desks along the
    # north/south walls, a map table (offset from the doorway's direct line so
    # you don't spawn nose-to-nose with it). --
    furn("Command & Comms", "08", "CommsConsole", COMMAND, BASE_Z, 6.0, 0.0, 0.0, (1.6, 0.6, 1.3))
    for i, dx in enumerate((-3.0, 3.0)):
        furn("Command & Comms", "08", f"Desk_N{i + 1:02d}", COMMAND, BASE_Z, dx, 5.0, 0.0, (1.2, 0.6, 0.9))
        furn("Command & Comms", "08", f"Desk_S{i + 1:02d}", COMMAND, BASE_Z, dx, -5.0, 0.0, (1.2, 0.6, 0.9))
    furn("Command & Comms", "08", "MapTable", COMMAND, BASE_Z, 1.5, 0.0, 0.0, (1.8, 1.0, 0.9))

    # -- Sensor Array: the "pour coffee for the sensor post, sign the log" beat
    # from the M1 design doc -- console, chair, log stand, equipment rack. --
    furn("Sensor Array", "09", "SensorConsole", SENSOR_ARRAY, BASE_Z, 0.0, 2.6, 0.0, (1.4, 0.6, 1.2))
    furn("Sensor Array", "09", "Chair", SENSOR_ARRAY, BASE_Z, 0.0, 1.8, 0.0, (0.5, 0.5, 0.9))
    furn("Sensor Array", "09", "EquipmentRack", SENSOR_ARRAY, BASE_Z, -2.6, 1.5, 0.0, (0.6, 0.5, 1.8))
    furn("Sensor Array", "09", "LogStand", SENSOR_ARRAY, BASE_Z, 1.0, 2.6, 0.0, (0.3, 0.3, 0.9))


safe(add_furniture, "Furniture")


# ---------------------------------------------------------------------------
# Interior lighting. One warm point light per building (three for Watch Tower,
# since it's a 22m vertical shaft and one light at the bottom wouldn't reach the
# top), positioned near the ceiling so they clear the furniture below. Matches
# the sheet's "sparse artificial lights" note -- functional room fill, not a
# lit pass. Intensity is in LUMENS (UE5 point lights default to inverse-square
# falloff, same physically-based units as the directional light's lux), sized
# roughly to each room's floor area so small rooms don't blow out and the tower
# doesn't stay dark top-to-bottom.
#
# NOTE: LightColor on a light component is an FColor (0-255 bytes), not an
# FLinearColor (0-1 floats) -- passing LinearColor here is exactly what's been
# silently failing on the sun (see "[Carrowgate Blockout] Could not set
# 'light_color' on DirectionalLightComponent..." in the Output Log every run).
# unreal.Color is used below so these actually take the warm tint instead of
# falling back to default white and logging a warning like that one does.
# ---------------------------------------------------------------------------

WARM_INTERIOR = unreal.Color(255, 217, 166, 255)


def add_interior_lighting():
    # Must match each building's (loc[0], loc[1]) in AREAS above, same as add_furniture().
    WATCH_TOWER = (56, 44)
    BARRACKS = (55, -32)
    MESS_HALL = (96, 8)
    ARMORY = (112, -15)
    COMMAND = (73, -61)
    SENSOR_ARRAY = (59, 30)

    def point_light(folder, name, origin_xy, z_m, intensity, radius_m, color=WARM_INTERIOR):
        cx, cy = origin_xy
        light = actor_subsystem.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(cx * M, cy * M, z_m * M), unreal.Rotator(0, 0, 0)
        )
        light.set_actor_label(name)
        light.set_folder_path(f"{ROOT_FOLDER}/{folder}/Lighting")
        light_comp = light.get_component_by_class(unreal.PointLightComponent)
        try_set(light_comp, "intensity", intensity)
        try_set(light_comp, "light_color", color)
        try_set(light_comp, "attenuation_radius", radius_m * M)
        try_set(light_comp, "source_radius", 4.0)
        try_set(light_comp, "cast_shadows", True)
        light_comp.set_mobility(unreal.ComponentMobility.STATIC)
        return light

    # Watch Tower: 22m shaft, stacked low/mid/top so the climb isn't dark partway up.
    point_light("Watch Tower", "PL_WatchTower_Low", WATCH_TOWER, 3.0, 3000.0, 6.0)
    point_light("Watch Tower", "PL_WatchTower_Mid", WATCH_TOWER, 11.0, 3000.0, 6.0)
    point_light("Watch Tower", "PL_WatchTower_Top", WATCH_TOWER, 19.0, 3000.0, 6.0)

    # Barracks: 20m x 12m -- two lights down the long axis over the bunks.
    point_light("Barracks", "PL_Barracks_A", (BARRACKS[0] - 5.0, BARRACKS[1]), 5.3, 3500.0, 8.0)
    point_light("Barracks", "PL_Barracks_B", (BARRACKS[0] + 5.0, BARRACKS[1]), 5.3, 3500.0, 8.0)

    # Mess Hall: 18m x 15m -- centered over the tables.
    point_light("Mess Hall", "PL_MessHall", MESS_HALL, 4.5, 5000.0, 10.0)

    # Armory: 12m x 12m -- centered.
    point_light("Armory", "PL_Armory", ARMORY, 4.5, 3500.0, 8.0)

    # Command & Comms: taller room (8m) -- centered near the ceiling.
    point_light("Command & Comms", "PL_Command", COMMAND, 7.0, 4000.0, 9.0)

    # Sensor Array: 8m x 8m, 10m tall -- centered.
    point_light("Sensor Array", "PL_SensorArray", SENSOR_ARRAY, 9.0, 3000.0, 7.0)


safe(add_interior_lighting, "Interior lighting")


# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

unreal.log(
    f"[Carrowgate Blockout] Placed {len(AREAS)} areas + ramp + furniture + interior lighting "
    f"under outliner folder '{ROOT_FOLDER}'. Next: press P to preview nav mesh / Build Paths, "
    f"verify the NavMeshBoundsVolume covers the walkable footprint, then Save Current Level."
)
