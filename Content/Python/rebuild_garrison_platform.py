"""
REPLACE THE GARRISON'S GROUND WITH SHANE'S CUSTOM PLATFORM MODEL
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT SHANE ASKED FOR
---------------------
Shane built a real platform model for Carrowgate Garrison (imported under
/Game/LevelPrototyping/Garrison) -- a round helipad with a lower dock pad
(where the boat + cranes go) coming off it, and a small ramp at the far end
that's how it connects to the mainland. It replaces every ground element
currently in the level. He wants:
  - It scaled up 1500/1500/1500.
  - The old Sea Wall placeholder pad DELETED outright -- he made a separate
    3D sea wall model that gets imported later, not part of this pass.
  - Every other existing building (Main Gate, Vehicle Bay, Parade Yard,
    Watch Tower, Barracks, Mess Hall, Armory, Command & Comms, Sensor
    Array, plus the Docks/Harbor ship + cranes) repositioned onto the new
    platform -- his exact words: "you can position the rest of the
    buildings however you want on it."

HOW THIS SCRIPT PLACES THINGS
------------------------------
It does NOT know the new mesh's internal layout (where exactly the round
helipad or the lower dock sit inside it, which side the mainland ramp faces)
-- that only exists inside the model itself, not in anything this script can
read ahead of time. So instead of guessing at that, it:
  1. Finds the new platform mesh under /Game/LevelPrototyping/Garrison
     automatically (whatever it's actually named).
  2. Deletes every old Ground_* landmass slab, the old Sea Wall pad, the old
     flat Helipad pad, the old flat Docks/Harbor pad, and the old
     mainland-to-docks ramp block -- everything the new model replaces.
  3. Spawns the new mesh at 1500/1500/1500 scale, centered where the old
     ground used to be, and nudges it in Z so its top surface sits at the
     same Z=0 floor level every room in this level already assumes.
  4. Reads the new mesh's ACTUAL world-space footprint back (get_actor_bounds
     -- this is real geometry, not a guess) and uses it to proportionally
     remap every other building's old position into the new platform's
     real footprint (with a inset margin so nothing hangs off an edge),
     preserving their old relative arrangement (Main Gate near one edge,
     Watch Tower/Sensor Array as a pair, Barracks central, etc.) just
     rescaled to fit whatever size platform Shane actually built.
  5. Moves each building as a WHOLE outliner-folder group (every wall,
     door, furniture piece, light) by one uniform X/Y offset, so nothing
     about how those rooms were built gets touched or re-derived -- they
     just slide to a new spot, fully intact.

Since this can't see where the helipad/dock actually are inside the mesh,
the Docks/Harbor group (ship + cranes) gets remapped the same proportional
way as everything else, but its Z height (previously keyed to the old
dock's -3.7m deck) is left as-is -- check that against where your model's
real lower dock pad sits and nudge Z if it's floating or buried.

NOT SAFE TO RE-RUN. It deletes ground/sea wall/helipad/dock placeholders
and shifts buildings by a one-time delta -- running it twice would delete
nothing new (fine) but double-shift every building (not fine). It refuses
to run a second time (checks for a GarrisonPlatform_New actor first).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/rebuild_garrison_platform.py"
"""

import unreal

M = 100.0
ROOT_FOLDER = "Carrowgate Garrison"
PLATFORM_ASSET_DIR = "/Game/LevelPrototyping/Garrison"
PLATFORM_SCALE = (1500.0, 1500.0, 1500.0)
MARGIN = 0.15  # inset fraction so remapped buildings don't hang off the new platform's edge

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary

# Old area positions (meters, X/Y only) -- straight from build_carrowgate_garrison.py's
# AREAS list. Used only as the remap SOURCE domain; each area's actors get moved as a
# whole folder group, so nothing here needs to match current in-level positions exactly.
OLD_AREA_POS = {
    "Main Gate": (0.0, 0.0),
    "Vehicle Bay": (35.0, -3.0),
    "Parade Yard": (46.0, 16.0),
    "Watch Tower": (56.0, 44.0),
    "Barracks": (55.0, -32.0),
    "Mess Hall": (96.0, 8.0),
    "Armory": (112.0, -15.0),
    "Command & Comms": (73.0, -61.0),
    "Sensor Array": (59.0, 30.0),
    "Civic Route (Streets)": (95.0, -77.5),
    "Docks / Harbor": (116.0, -126.0),
}


def log(msg):
    print("[RebuildGarrisonPlatform] %s" % msg)


def get_all_actors():
    return actor_subsystem.get_all_level_actors()


def find_platform_mesh():
    if not AL.does_directory_exist(PLATFORM_ASSET_DIR):
        return None, []
    paths = AL.list_assets(PLATFORM_ASSET_DIR, recursive=True, include_folder=False)
    meshes = []
    for p in paths:
        asset = AL.load_asset(p)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append((p, asset))
    if not meshes:
        return None, []
    return meshes[0][1], meshes


def delete_by_label_prefix(prefix):
    removed = 0
    for a in list(get_all_actors()):
        if a.get_actor_label().startswith(prefix):
            actor_subsystem.destroy_actor(a)
            removed += 1
    return removed


def delete_by_label_exact(label):
    for a in list(get_all_actors()):
        if a.get_actor_label() == label:
            actor_subsystem.destroy_actor(a)
            return True
    return False


def delete_folder(folder_path):
    removed = 0
    for a in list(get_all_actors()):
        folder = str(a.get_folder_path())
        if folder == folder_path or folder.startswith(folder_path + "/"):
            actor_subsystem.destroy_actor(a)
            removed += 1
    return removed


def move_folder(folder_path, dx_m, dy_m, dz_m=0.0):
    offset = unreal.Vector(dx_m * M, dy_m * M, dz_m * M)
    moved = 0
    for a in get_all_actors():
        folder = str(a.get_folder_path())
        if folder == folder_path or folder.startswith(folder_path + "/"):
            a.add_actor_world_offset(offset, False, False)
            moved += 1
    return moved


def run():
    # -- 0. Refuse to re-run -------------------------------------------------
    if any(a.get_actor_label() == "GarrisonPlatform_New" for a in get_all_actors()):
        log("ABORTED -- GarrisonPlatform_New already exists. This script isn't safe to "
            "re-run (it shifts buildings by a one-time delta). Undo/reload the level first "
            "if you need to redo this pass.")
        return

    # -- 1. Find the platform mesh -------------------------------------------
    mesh, all_found = find_platform_mesh()
    if mesh is None:
        log("ABORTED -- no StaticMesh found under %s. Import/save your platform model there "
            "first, then re-run this script. (Checked the directory exists: %s)" % (
                PLATFORM_ASSET_DIR, AL.does_directory_exist(PLATFORM_ASSET_DIR)))
        return
    if len(all_found) > 1:
        log("Found %d static meshes under %s -- using the first one: %s. Tell me if that's "
            "the wrong one." % (len(all_found), PLATFORM_ASSET_DIR, all_found[0][0]))
    else:
        log("Using platform mesh: %s" % all_found[0][0])

    # -- 2. Delete everything the new model replaces -------------------------
    n_ground = delete_by_label_prefix("Ground_")
    log("Deleted %d old Ground_* landmass slab(s)." % n_ground)

    n_seawall = delete_folder(f"{ROOT_FOLDER}/Sea Wall")
    log("Deleted Sea Wall folder entirely (%d actor(s)) -- your separate sea wall model "
        "goes back in later." % n_seawall)

    if delete_by_label_exact("10_Helipad"):
        log("Deleted old flat Helipad placeholder pad.")
    else:
        log("Old Helipad placeholder pad (10_Helipad) not found -- skipped.")

    if delete_by_label_exact("13_Docks / Harbor"):
        log("Deleted old flat Docks/Harbor placeholder pad.")
    else:
        log("Old Docks/Harbor placeholder pad (13_Docks / Harbor) not found -- skipped.")

    if delete_by_label_exact("Platform-to-Docks Ramp"):
        log("Deleted old mainland-to-docks ramp block.")
    else:
        log("Old ramp block not found -- skipped.")

    # -- 3. Spawn the new platform --------------------------------------------
    old_xs = [p[0] for p in OLD_AREA_POS.values()]
    old_ys = [p[1] for p in OLD_AREA_POS.values()]
    old_min_x, old_max_x = min(old_xs), max(old_xs)
    old_min_y, old_max_y = min(old_ys), max(old_ys)
    centroid_x = (old_min_x + old_max_x) / 2.0
    centroid_y = (old_min_y + old_max_y) / 2.0

    location = unreal.Vector(centroid_x * M, centroid_y * M, 0.0)
    platform = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(0, 0, 0))
    platform.set_actor_label("GarrisonPlatform_New")
    platform.set_folder_path(f"{ROOT_FOLDER}/Ground")
    mesh_comp = platform.static_mesh_component
    mesh_comp.set_static_mesh(mesh)
    mesh_comp.set_world_scale3d(unreal.Vector(*PLATFORM_SCALE))
    mesh_comp.set_mobility(unreal.ComponentMobility.STATIC)

    # Ground it: nudge Z so the mesh's own top surface lands at Z=0, matching
    # every room/floor in this level's existing convention.
    origin, extent = platform.get_actor_bounds(False)
    top_z = origin.z + extent.z
    platform.add_actor_world_offset(unreal.Vector(0.0, 0.0, -top_z), False, False)

    # Re-query the REAL world footprint now that it's placed and grounded.
    origin, extent = platform.get_actor_bounds(False)
    plat_min_x, plat_max_x = (origin.x - extent.x) / M, (origin.x + extent.x) / M
    plat_min_y, plat_max_y = (origin.y - extent.y) / M, (origin.y + extent.y) / M
    plat_min_z, plat_max_z = (origin.z - extent.z) / M, (origin.z + extent.z) / M
    log("Spawned GarrisonPlatform_New at %.1fx scale. Real world footprint: "
        "X=[%.1f, %.1f]  Y=[%.1f, %.1f]  Z=[%.1f, %.1f] (meters)." % (
            PLATFORM_SCALE[0], plat_min_x, plat_max_x, plat_min_y, plat_max_y, plat_min_z, plat_max_z))

    # -- 4. Remap every other area's position into the new footprint ---------
    span_x = plat_max_x - plat_min_x
    span_y = plat_max_y - plat_min_y
    new_min_x = plat_min_x + MARGIN * span_x
    new_max_x = plat_max_x - MARGIN * span_x
    new_min_y = plat_min_y + MARGIN * span_y
    new_max_y = plat_max_y - MARGIN * span_y

    def remap(old_x, old_y):
        tx = 0.5 if old_max_x == old_min_x else (old_x - old_min_x) / (old_max_x - old_min_x)
        ty = 0.5 if old_max_y == old_min_y else (old_y - old_min_y) / (old_max_y - old_min_y)
        return new_min_x + tx * (new_max_x - new_min_x), new_min_y + ty * (new_max_y - new_min_y)

    for area_name, (ox, oy) in OLD_AREA_POS.items():
        nx, ny = remap(ox, oy)
        dx, dy = nx - ox, ny - oy
        moved = move_folder(f"{ROOT_FOLDER}/{area_name}", dx, dy, 0.0)
        if moved:
            log("Moved '%s': %d actor(s), delta=(%.1f, %.1f)m -> now centered near (%.1f, %.1f)." % (
                area_name, moved, dx, dy, nx, ny))
        else:
            log("'%s': no actors found under that folder -- nothing to move." % area_name)

    log("Done. Save and take a look. The new platform's real bounds are logged above -- if "
        "any building landed on top of the round helipad or the lower dock, just drag it in "
        "the viewport; this script has no way to know where those sub-shapes sit inside your "
        "mesh. Docks/Harbor's ship + cranes moved with the rest of that group but kept their "
        "old Z height -- check that against where the new dock deck actually sits and nudge "
        "Z if needed.")


run()
