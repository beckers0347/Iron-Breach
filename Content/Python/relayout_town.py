"""
RELAYOUT THE CG MAINLAND TOWN -- delete every existing building, rebuild
from scratch with explicit sizes and a real town layout
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Shane: scale each building type to a specific size (Shop Front 7/7/7,
Spire 30/30/30, Apartment 30/30/30, Rowhouse 50/50/50, Warehouse 25/25/25,
Cottage 10/10/10, Tower 20/20/20, Ruin 20/20/20, Garage 8/8/8), keep only
ONE Spire as the literal center of town with a town square in front of it,
keep only 4 Towers -- one at each corner of the outskirts -- and push the
Ruins out toward the edge of town. Rather than try to rescale/reshuffle the
existing randomly-scattered Downtown_*/Outskirt_* actors in place (which
were sized by the OLD footprint/height formula, not these fixed sizes, and
would just overlap everywhere), Shane asked to delete all of them and
re-place buildings fresh -- his call, and the cleaner path given how much
the sizes changed.

THE PLAN
--------
Reuses CG Mainland's existing coordinate frame (build_carrowgate_mainland.py):
the same CITY_X_START/CITY_X_END/CITY_Y_HALF_WIDTH bounds and the same
city_boundary_y() ragged-taper function, so the new buildings still sit
inside the ground/road footprint that script already built. Within those
bounds:
  - The one Spire sits at the town's literal center (depth t=0.5).
  - A cobblestone town square sits just in front of it (toward the
    causeway/entrance, t=0.35), so arriving from the gate you reach the
    square first and the spire rises up beyond it.
  - 4 Towers sit at the 4 corners of the town's bounding shape (near
    entrance / far edge x, at the widest +Y/-Y each x allows).
  - A handful of Ruins scatter along the FAR edge of town (deep in the
    outskirts, near the foothills), reading as the town's crumbling fringe.
  - Everything else (Shop Front, Apartment, Rowhouse, Warehouse, Cottage,
    Garage) fills the remaining space via rejection-sampled scatter, each
    new building checked against every already-placed building (specials
    included) so nothing overlaps, at the counts below.

Safe to re-run -- clears every actor this script has ever placed (folder
"CG Mainland/City/TownBuildings") AND the old Downtown_*/Outskirt_* actors
from build_carrowgate_mainland.py's original layout before placing anything.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/relayout_town.py"
"""

import unreal
import math

M = 100.0
ROOT_FOLDER = "CG Mainland"
NEW_FOLDER = f"{ROOT_FOLDER}/City/TownBuildings"
OLD_DOWNTOWN_BUILDINGS_FOLDER = f"{ROOT_FOLDER}/City/Downtown/Buildings"
OLD_OUTSKIRTS_FOLDER = f"{ROOT_FOLDER}/City/Outskirts"

ASSET_ROOT = "/Game/Environment/CGMainland/AIModels"
COBBLE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary
CUBE_MESH = AL.load_asset("/Engine/BasicShapes/Cube.Cube")

# Same bounds/taper as build_carrowgate_mainland.py so this drops into the
# ground/road footprint already built there.
CITY_X_START = -40.0
CITY_X_END = -300.0
CITY_Y_HALF_WIDTH = 130.0


def city_depth_t(x):
    return max(0.0, min(1.0, (CITY_X_START - x) / (CITY_X_START - CITY_X_END)))


def city_boundary_y(x):
    t = city_depth_t(x)
    taper = CITY_Y_HALF_WIDTH * (1.0 - 0.55 * t)
    wobble = 22.0 * math.sin(t * 7.3 + 1.7) + 12.0 * math.sin(t * 13.1 + 4.2) + 8.0 * math.sin(t * 21.0 + 0.4)
    return max(18.0, taper + wobble)


def x_at_t(t):
    return CITY_X_START - t * (CITY_X_START - CITY_X_END)


def prand(seed):
    h = hash(seed) & 0xFFFFFFFF
    h = (h * 9301 + 49297) % 233280
    return h / 233280.0


def log(msg):
    print("[RelayoutTown] %s" % msg)


# ---------------------------------------------------------------------------
# Spawn helpers
# ---------------------------------------------------------------------------
def _mesh_bounds_m(mesh):
    try:
        box = unreal.EditorStaticMeshLibrary.get_static_mesh_bounding_box(mesh)
        size = box.max - box.min
        if size.x > 1.0 and size.y > 1.0 and size.z > 1.0:
            return box.min.z / 100.0, (size.x / 100.0, size.y / 100.0, size.z / 100.0)
    except Exception:
        pass
    try:
        bounds = mesh.get_editor_property("extended_bounds")
        ext = bounds.box_extent
        origin = bounds.origin
        size_cm = (ext.x * 2.0, ext.y * 2.0, ext.z * 2.0)
        if size_cm[0] > 1.0 and size_cm[1] > 1.0 and size_cm[2] > 1.0:
            return (origin.z - ext.z) / 100.0, (size_cm[0] / 100.0, size_cm[1] / 100.0, size_cm[2] / 100.0)
    except Exception:
        pass
    return 0.0, (1.0, 1.0, 1.0)


def spawn_building(label, folder, mesh, loc_m, size_m, rotation_deg=(0, 0, 0)):
    """Fits mesh's native bounding box to size_m (meters) -- size_m IS the
    building's real world dimensions, matching how Shane means "scale to
    N N N" -- then grounds it so its base sits at loc_m's Z (default 0)."""
    _, native_size_m = _mesh_bounds_m(mesh)
    scale = tuple(
        (size_m[i] / native_size_m[i]) if native_size_m[i] > 1e-6 else size_m[i]
        for i in range(3)
    )
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    rotation = unreal.Rotator(rotation_deg[0], rotation_deg[1], rotation_deg[2])
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.set_folder_path(f"{NEW_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(mesh)
    mesh_comp.set_world_scale3d(unreal.Vector(*scale))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    # Ground it: base of the actor's real bounds should sit at loc_m[2].
    origin, extent = actor.get_actor_bounds(False)
    current_bottom_cm = origin.z - extent.z
    target_bottom_cm = loc_m[2] * M
    if abs(target_bottom_cm - current_bottom_cm) > 0.01:
        actor.add_actor_world_offset(unreal.Vector(0.0, 0.0, target_bottom_cm - current_bottom_cm), False, False)
    return actor


def spawn_plaza(label, folder, loc_m, size_m, material, rotation_deg=(0, 0, 0)):
    location = unreal.Vector(loc_m[0] * M, loc_m[1] * M, loc_m[2] * M)
    rotation = unreal.Rotator(rotation_deg[0], rotation_deg[1], rotation_deg[2])
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    actor.set_actor_label(label)
    actor.set_folder_path(f"{NEW_FOLDER}/{folder}")
    mesh_comp = actor.static_mesh_component
    mesh_comp.set_static_mesh(CUBE_MESH)
    mesh_comp.set_world_scale3d(unreal.Vector(size_m[0], size_m[1], size_m[2]))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)
    if material is not None:
        mesh_comp.set_material(0, material)
    return actor


def clear_previous():
    removed = 0
    for a in list(actor_subsystem.get_all_level_actors()):
        folder = str(a.get_folder_path())
        if (folder == NEW_FOLDER or folder.startswith(NEW_FOLDER + "/")
                or folder == OLD_DOWNTOWN_BUILDINGS_FOLDER or folder.startswith(OLD_DOWNTOWN_BUILDINGS_FOLDER + "/")
                or folder == OLD_OUTSKIRTS_FOLDER or folder.startswith(OLD_OUTSKIRTS_FOLDER + "/")):
            # Don't eat the outskirts' own Roads subfolder if it still has
            # anything in it -- buildings-only cleanup.
            if folder == OLD_OUTSKIRTS_FOLDER + "/Roads" or folder.startswith(OLD_OUTSKIRTS_FOLDER + "/Roads/"):
                continue
            actor_subsystem.destroy_actor(a)
            removed += 1
    if removed:
        log("Cleared %d old building actor(s)." % removed)


# ---------------------------------------------------------------------------
# Building kit -- one real mesh per type, target world size (meters) per
# Shane's numbers.
# ---------------------------------------------------------------------------
KIT = {
    "Shopfront":  (f"{ASSET_ROOT}/SM_Building_Shopfront",  (7.0, 7.0, 7.0)),
    "Spire":      (f"{ASSET_ROOT}/SM_Building_Spire",      (30.0, 30.0, 30.0)),
    "Apartment":  (f"{ASSET_ROOT}/SM_Building_Apartment",  (30.0, 30.0, 30.0)),
    "Rowhouse":   (f"{ASSET_ROOT}/SM_Building_Rowhouse",   (50.0, 50.0, 50.0)),
    "Warehouse":  (f"{ASSET_ROOT}/SM_Building_Warehouse",  (25.0, 25.0, 25.0)),
    "Cottage":    (f"{ASSET_ROOT}/SM_Building_Cottage",    (10.0, 10.0, 10.0)),
    "Tower":      (f"{ASSET_ROOT}/SM_Building_Tower",      (20.0, 20.0, 20.0)),
    "Ruin":       (f"{ASSET_ROOT}/SM_Building_Ruin",       (20.0, 20.0, 20.0)),
    "Garage":     (f"{ASSET_ROOT}/SM_Building_Garage",     (8.0, 8.0, 8.0)),
}

# How many of the general-fill types to scatter through town (the big ones
# get fewer instances -- they're 4-7x the footprint of the small ones).
FILL_COUNTS = {
    "Rowhouse": 3,
    "Warehouse": 3,
    "Apartment": 4,
    "Cottage": 10,
    "Shopfront": 10,
    "Garage": 4,
}

RUIN_COUNT = 4


def footprint_radius(size_m):
    # size_m is uniform (N,N,N) for every type Shane gave -- half-width plus
    # a flat clearance margin so buildings read as separated, not touching.
    return size_m[0] * 0.62 + 3.0


def fits(x, y, r, placed):
    if abs(y) > city_boundary_y(x) - 8.0:
        return False
    for (px, py, pr) in placed:
        dx, dy = x - px, y - py
        if (dx * dx + dy * dy) ** 0.5 < (r + pr):
            return False
    return True


def run():
    for name, (path, _) in KIT.items():
        if AL.load_asset(path) is None:
            log("ABORTED -- missing mesh asset %s (run import_mainland_buildings.py first)." % path)
            return

    clear_previous()
    placed = []  # (x, y, radius) for every building spawned this run

    # -- 1. Spire at the literal center of town -----------------------------
    spire_mesh = AL.load_asset(KIT["Spire"][0])
    spire_size = KIT["Spire"][1]
    spire_x, spire_y = x_at_t(0.5), 0.0
    spawn_building("Spire_TownCenter", "Center", spire_mesh, (spire_x, spire_y, 0.0), spire_size)
    placed.append((spire_x, spire_y, footprint_radius(spire_size)))
    log("Spire placed at town center (%.0f, %.0f)." % (spire_x, spire_y))

    # -- 2. Town square in front of it (toward the causeway/entrance) -------
    square_x, square_y = x_at_t(0.36), 0.0
    cobble_mat = AL.load_asset(COBBLE_MATERIAL_PATH)
    spawn_plaza("TownSquare", "Center", (square_x, square_y, 0.02), (46.0, 46.0, 0.06), cobble_mat)
    placed.append((square_x, square_y, 28.0))
    log("Town square placed in front of the spire at (%.0f, %.0f)." % (square_x, square_y))

    # -- 3. 4 Towers, one at each corner of the town's bounding shape -------
    tower_mesh = AL.load_asset(KIT["Tower"][0])
    tower_size = KIT["Tower"][1]
    tower_r = footprint_radius(tower_size)
    for i, (t, side) in enumerate([(0.06, "NearEntrance"), (0.94, "FarEdge")]):
        cx = x_at_t(t)
        max_y = city_boundary_y(cx) - tower_r - 4.0
        for sign, label in [(1, "Pos"), (-1, "Neg")]:
            cy = sign * max_y
            spawn_building(f"CornerTower_{side}_{label}", "Corners", tower_mesh, (cx, cy, 0.0), tower_size)
            placed.append((cx, cy, tower_r))
    log("4 Towers placed at the town's corners.")

    # -- 4. Ruins scattered along the far edge of town -----------------------
    ruin_mesh = AL.load_asset(KIT["Ruin"][0])
    ruin_size = KIT["Ruin"][1]
    ruin_r = footprint_radius(ruin_size)
    ruin_placed = 0
    attempt = 0
    while ruin_placed < RUIN_COUNT and attempt < 400:
        attempt += 1
        seed = f"ruin_{attempt}"
        t = 0.78 + prand(seed + "t") * 0.16  # deep in the outskirts, short of the very back corners
        x = x_at_t(t)
        max_y = city_boundary_y(x) - ruin_r - 4.0
        y = (prand(seed + "y") * 2.0 - 1.0) * max_y
        if fits(x, y, ruin_r, placed):
            spawn_building(f"EdgeRuin_{ruin_placed:02d}", "Edge", ruin_mesh, (x, y, 0.0), ruin_size)
            placed.append((x, y, ruin_r))
            ruin_placed += 1
    log("Placed %d/%d Ruins along the far edge of town." % (ruin_placed, RUIN_COUNT))

    # -- 5. Fill the rest of town with the remaining building types ---------
    # Biggest footprints first so they get first pick of open ground.
    fill_order = sorted(FILL_COUNTS.keys(), key=lambda k: -KIT[k][1][0])
    for type_name in fill_order:
        mesh = AL.load_asset(KIT[type_name][0])
        size_m = KIT[type_name][1]
        r = footprint_radius(size_m)
        target = FILL_COUNTS[type_name]
        done = 0
        attempt = 0
        while done < target and attempt < 600:
            attempt += 1
            seed = f"{type_name}_{attempt}"
            t = 0.08 + prand(seed + "t") * 0.84
            x = x_at_t(t)
            max_y = city_boundary_y(x) - r - 4.0
            if max_y <= 0:
                continue
            y = (prand(seed + "y") * 2.0 - 1.0) * max_y
            if fits(x, y, r, placed):
                yaw = prand(seed + "r") * 360.0
                spawn_building(f"{type_name}_{done:02d}", "Fill", mesh, (x, y, 0.0), size_m, (0, 0, yaw))
                placed.append((x, y, r))
                done += 1
        log("%s: placed %d/%d." % (type_name, done, target))

    log("Done. %d buildings total. Save and check the viewport / re-run PIE." % len(placed))


run()
