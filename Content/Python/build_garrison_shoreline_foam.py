"""
Carrowgate Garrison -- coastline foam pass
=================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Adds crashing-surf foam strips all the way around the Garrison platform's
irregular footprint, the same idea as build_carrowgate_mainland.py's
build_shoreline() surf strips, but computed for a shape that isn't a single
straight coastline -- the Garrison sits on a "staircase" union of 9
overlapping axis-aligned ground slabs (see GROUND_SEGMENTS below, copied
verbatim from build_carrowgate_garrison.py so this script's outline always
matches the real platform), so there's no single X value to hang foam off
of like the mainland script could.

Instead this rasterizes the footprint onto a 1m grid, walks every occupied
cell's 4 neighbors to find which cell edges border open water (occupied
cell, unoccupied neighbor), and merges contiguous same-facing edges into
long straight runs before spawning geometry -- so a ~160m x 150m footprint
turns into a few dozen foam strips, not thousands of 1m actors.

WHY A SEPARATE SCRIPT instead of editing build_carrowgate_garrison.py
directly: this needs its own Outliner root folder and its own
cleanup-before-rebuild step (see cleanup_previous_run() below) so it
doesn't collide with that script's own ROOT_FOLDER ("Carrowgate Garrison")
cleanup scope -- re-running the base script would otherwise sweep this
script's foam actors away too. Keeping the roots distinct means either
script can be re-run independently.

ONE THING THIS SCRIPT DELIBERATELY SKIPS: the GateApproach segment's west
edge (around X=-10m) -- that's not open coastline, it's where the Main Gate
opens and (per build_carrowgate_mainland.py's own convention of never
placing anything past X=-15m) the CG-Mainland causeway connects. Foam there
would read as surf crashing across the road into the base.

HOW TO RUN IT
-------------
Run build_carrowgate_garrison.py first (this script reads its
GROUND_SEGMENTS layout but doesn't require its actors to exist -- it
recomputes the footprint from the same coordinate data independently).
Then:
    py "X:/IronBreach/Content/Python/build_garrison_shoreline_foam.py"

Needs M_AI_Foam built first (build_foam_material.py) for the actual
pulsing whitewater look -- falls back to plain water-colored strips with a
warning if that hasn't been run yet, same fallback style as everywhere else
in this project's build scripts.

Safe to re-run (clears its own root folder first).
"""

import unreal

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

M = 100.0  # meters -> Unreal units (cm)
ROOT_FOLDER = "Carrowgate Garrison Foam"  # deliberately NOT nested under
# "Carrowgate Garrison" -- see header comment on why this needs its own root.

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

CUBE_MESH = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
if CUBE_MESH is None:
    unreal.log_error("[Garrison Foam] Could not load /Engine/BasicShapes/Cube.Cube -- aborting.")
    raise SystemExit


def cleanup_previous_run():
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
        unreal.log(f"[Garrison Foam] Cleared {removed} actor(s) from a previous run before rebuilding.")


try:
    cleanup_previous_run()
except Exception as e:  # noqa: BLE001
    unreal.log_warning(f"[Garrison Foam] Cleanup failed, continuing anyway: {e}")


def spawn_block(label, folder, loc_m, size_m, material=None):
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(0, 0, 0))
    actor.set_actor_label(label)
    actor.set_folder_path(f"{ROOT_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(CUBE_MESH)
    mesh_comp.set_world_scale3d(unreal.Vector(size_m[0], size_m[1], size_m[2]))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    return actor


# ---------------------------------------------------------------------------
# Materials -- same MI_AI_Foam_P### phase-instance convention and same
# MATERIAL_DIR as build_carrowgate_mainland.py's get_or_make_foam_instance(),
# so if that script already made these instances this one reuses them
# instead of creating duplicates.
# ---------------------------------------------------------------------------
MATERIAL_DIR = "/Game/LevelPrototyping/AITextures/Landmass"
FOAM_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Foam.M_AI_Foam"
WATER_SHALLOW_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Water_Shallow.M_AI_Water_Shallow"
WATER_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Water.M_AI_Water"

_FOAM_PARENT = unreal.EditorAssetLibrary.load_asset(FOAM_MATERIAL_PATH)
if _FOAM_PARENT is None:
    unreal.log_warning(f"[Garrison Foam] {FOAM_MATERIAL_PATH} not found -- run build_foam_material.py first for "
                        "animated whitewater. Falling back to a plain water-colored strip for now.")
_FALLBACK_MAT = (unreal.EditorAssetLibrary.load_asset(WATER_SHALLOW_MATERIAL_PATH)
                  or unreal.EditorAssetLibrary.load_asset(WATER_MATERIAL_PATH))


def get_or_make_foam_instance(phase_seconds):
    """Same convention as build_carrowgate_mainland.py's helper of the same name --
    a Material Instance Constant off M_AI_Foam with its own PhaseOffset so
    different strips surge out of sync. Returns None if M_AI_Foam isn't built yet."""
    if _FOAM_PARENT is None:
        return None
    name = f"MI_AI_Foam_P{int(phase_seconds * 10):03d}"
    path = f"{MATERIAL_DIR}/{name}"
    existing = unreal.EditorAssetLibrary.load_asset(path)
    if existing is not None:
        unreal.MaterialEditingLibrary.set_material_instance_parent(existing, _FOAM_PARENT)
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(existing, "PhaseOffset", phase_seconds)
        unreal.EditorAssetLibrary.save_loaded_asset(existing)
        return existing
    factory = unreal.MaterialInstanceConstantFactoryNew()
    instance = asset_tools.create_asset(name, MATERIAL_DIR, unreal.MaterialInstanceConstant, factory)
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, _FOAM_PARENT)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "PhaseOffset", phase_seconds)
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    return instance


# ---------------------------------------------------------------------------
# Footprint -- copied verbatim from build_carrowgate_garrison.py's
# GROUND_SEGMENTS. Keep these two lists in sync if that script's layout ever
# changes; this script recomputes its own boundary from this data rather
# than depending on the other script's live actors.
# ---------------------------------------------------------------------------
GROUND_SEGMENTS = [
    # name,                      (center X, center Y), (size X, size Y)
    ("GateApproach", (2.5, 0.0), (25, 20)),
    ("WestConnector", (25.0, 2.0), (30, 20)),
    ("NW_Yard", (47.5, -2.5), (55, 35)),
    ("NorthSpur_WatchTower", (57.5, 33.5), (35, 43)),
    ("CentralBody_Barracks", (65.0, -15.0), (50, 60)),
    ("EastWing_MessHallArmory", (100.0, -2.5), (50, 55)),
    ("SouthWing_Command", (72.5, -57.5), (35, 35)),
    ("SE_CoastalReach_Helipad", (125.0, -37.5), (50, 45)),
    ("SouthTaper_CivicRoute", (95.0, -77.5), (40, 35)),
]

# GateApproach is the only segment that reaches this far west (every other
# segment starts at X >= 10) -- so any west-facing boundary edge out here is
# the gate/causeway side, not open coastline. Excluded below.
GATE_WEST_EXCLUDE_X = -8.0


def in_any_segment(px, py):
    for _, (cx, cy), (sx, sy) in GROUND_SEGMENTS:
        if (cx - sx / 2.0) <= px <= (cx + sx / 2.0) and (cy - sy / 2.0) <= py <= (cy + sy / 2.0):
            return True
    return False


# Bounding box, with a 1-cell margin so edge cells always have a real
# (unoccupied) neighbor to compare against instead of falling off the grid.
_all_x = [cx - sx / 2.0 for _, (cx, cy), (sx, sy) in GROUND_SEGMENTS] + \
         [cx + sx / 2.0 for _, (cx, cy), (sx, sy) in GROUND_SEGMENTS]
_all_y = [cy - sy / 2.0 for _, (cx, cy), (sx, sy) in GROUND_SEGMENTS] + \
         [cy + sy / 2.0 for _, (cx, cy), (sx, sy) in GROUND_SEGMENTS]
XMIN, XMAX = int(min(_all_x)) - 1, int(max(_all_x)) + 1
YMIN, YMAX = int(min(_all_y)) - 1, int(max(_all_y)) + 1

# occupied[(ix, iy)] -- cell spans world X in [ix, ix+1], Y in [iy, iy+1]
# (1m grid, so the integer index doubles as the world coordinate).
occupied = set()
for ix in range(XMIN, XMAX):
    for iy in range(YMIN, YMAX):
        if in_any_segment(ix + 0.5, iy + 0.5):
            occupied.add((ix, iy))

unreal.log(f"[Garrison Foam] Rasterized footprint: {len(occupied)} occupied 1m cell(s) "
           f"over a {XMAX - XMIN}m x {YMAX - YMIN}m bounding box.")

# Collect raw unit-length boundary edges, grouped for merging:
#   vertical edges (W/E, constant X) grouped by (direction, x) -> set of y indices
#   horizontal edges (N/S, constant Y) grouped by (direction, y) -> set of x indices
_vert = {}   # (dir, x) -> set(iy)
_horiz = {}  # (dir, y) -> set(ix)

for (ix, iy) in occupied:
    if (ix - 1, iy) not in occupied:
        _vert.setdefault(("W", ix), set()).add(iy)
    if (ix + 1, iy) not in occupied:
        _vert.setdefault(("E", ix + 1), set()).add(iy)
    if (ix, iy - 1) not in occupied:
        _horiz.setdefault(("S", iy), set()).add(ix)
    if (ix, iy + 1) not in occupied:
        _horiz.setdefault(("N", iy + 1), set()).add(ix)


def merge_indices(indices):
    """Sorted unique ints -> list of (run_start, run_end) merging consecutive runs."""
    runs = []
    for i in sorted(indices):
        if runs and i == runs[-1][1]:
            runs[-1] = (runs[-1][0], i + 1)
        else:
            runs.append((i, i + 1))
    return runs


# Final edge list: (direction, fixed_coord, run_start, run_end) in world meters.
edges = []
for (direction, fixed), idxs in _vert.items():
    if direction == "W" and fixed <= GATE_WEST_EXCLUDE_X:
        continue
    for start, end in merge_indices(idxs):
        edges.append((direction, fixed, start, end))
for (direction, fixed), idxs in _horiz.items():
    for start, end in merge_indices(idxs):
        edges.append((direction, fixed, start, end))

unreal.log(f"[Garrison Foam] Found {len(edges)} merged boundary run(s) after excluding the gate/causeway side.")

# ---------------------------------------------------------------------------
# Spawn foam strips along each run.
# ---------------------------------------------------------------------------
# Water_Placeholder in build_carrowgate_garrison.py sits at Z=-4.6 with 0.3m
# height (world scale), so its top surface is -4.6 + 0.15 = -4.45m. Ground
# segments' top is Z=0 with a 6m-deep underside (GROUND_DEPTH), so the
# platform edge is a ~4.45m vertical drop into the water, not a gentle beach
# like the mainland shoreline -- foam here should hug the cliff base near
# the waterline, not sit up at platform level.
FOAM_Z = -4.30
STRIP_THICKNESS = 0.15
STRIP_WIDTH = 4.0     # extent in the outward (cliff-to-water) direction
RUN_MARGIN = 2.0      # extra length so adjoining runs' strips overlap at corners, no gaps
OUTWARD_OFFSET = 1.5  # how far the strip's center sits out past the platform edge

# A handful of phases so neighboring strips don't pulse in lockstep -- cycled
# by index, same spirit as build_carrowgate_mainland.py's 3 hand-picked phases.
PHASES = [0.0, 1.3, 2.6, 3.9, 5.2, 0.7, 2.0]

spawned = 0
for i, (direction, fixed, start, end) in enumerate(edges):
    run_len = (end - start) + RUN_MARGIN
    mid = (start + end) / 2.0
    phase = PHASES[i % len(PHASES)]
    foam_mat = get_or_make_foam_instance(phase) or _FALLBACK_MAT

    if direction == "W":
        loc = (fixed - OUTWARD_OFFSET, mid, FOAM_Z)
        size = (STRIP_WIDTH, run_len, STRIP_THICKNESS)
    elif direction == "E":
        loc = (fixed + OUTWARD_OFFSET, mid, FOAM_Z)
        size = (STRIP_WIDTH, run_len, STRIP_THICKNESS)
    elif direction == "S":
        loc = (mid, fixed - OUTWARD_OFFSET, FOAM_Z)
        size = (run_len, STRIP_WIDTH, STRIP_THICKNESS)
    else:  # "N"
        loc = (mid, fixed + OUTWARD_OFFSET, FOAM_Z)
        size = (run_len, STRIP_WIDTH, STRIP_THICKNESS)

    spawn_block(f"Surf_{direction}_{i:03d}", "Foam", loc, size, material=foam_mat)
    spawned += 1

unreal.log(f"[Garrison Foam] Spawned {spawned} foam strip(s) around the Garrison platform's coastline "
           f"(gate/causeway side at X<={GATE_WEST_EXCLUDE_X:.0f} left clear).")
