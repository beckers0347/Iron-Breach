import unreal
import json
import os

# =============================================================================
# LEVEL MANAGEMENT
# =============================================================================

def load_or_create_level(level_path, force_new=False):
    """
    Loads an existing level, or creates a new one if it doesn't exist
    (or if force_new is True). Returns True on success.
    """
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    exists = unreal.EditorAssetLibrary.does_asset_exist(level_path)

    if exists and not force_new:
        unreal.log(f"Loading existing level: {level_path}")
        return level_subsystem.load_level(level_path)

    unreal.log(f"Creating new level: {level_path}")
    return level_subsystem.new_level(level_path)


def save_current_level():
    """Saves the currently open level."""
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    saved = level_subsystem.save_current_level()
    if saved:
        unreal.log("Level saved successfully.")
    else:
        unreal.log_error("Failed to save level.")
    return saved


# =============================================================================
# BATCH ACTOR PLACEMENT
# =============================================================================

def spawn_actors_from_layout(layout_entries):
    """
    Spawns a batch of actors from a list of layout entries. Each entry is a dict:
    {
        "asset_path": "/Game/IronBreach/Kaiju/Alpha/BP_Kaiju_Alpha.BP_Kaiju_Alpha",
        "location": [500.0, 0.0, 100.0],
        "rotation": [0.0, -90.0, 0.0],   # optional, defaults to (0,0,0)
        "label": "Kaiju_Spawn_01",       # optional, sets actor label
        "scale": [1.0, 1.0, 1.0]         # optional, defaults to (1,1,1)
    }
    Returns a list of successfully spawned actors.
    """
    spawned_actors = []

    for i, entry in enumerate(layout_entries):
        asset_path = entry.get("asset_path")
        if not asset_path:
            unreal.log_error(f"Layout entry {i} missing 'asset_path', skipping.")
            continue

        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not asset:
            unreal.log_error(f"Could not load asset at {asset_path}, skipping entry {i}.")
            continue

        loc = entry.get("location", [0.0, 0.0, 0.0])
        rot = entry.get("rotation", [0.0, 0.0, 0.0])
        scale = entry.get("scale", [1.0, 1.0, 1.0])

        spawn_location = unreal.Vector(*loc)
        spawn_rotation = unreal.Rotator(*rot)

        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        spawned = actor_subsystem.spawn_actor_from_object(asset, spawn_location, spawn_rotation)

        if not spawned:
            unreal.log_error(f"Failed to spawn actor for entry {i} ({asset_path}).")
            continue

        spawned.set_actor_scale3d(unreal.Vector(*scale))

        label = entry.get("label")
        if label:
            spawned.set_actor_label(label)

        spawned_actors.append(spawned)
        unreal.log(f"Spawned: {spawned.get_actor_label()} at {loc}")

    unreal.log(f"Batch placement complete. {len(spawned_actors)}/{len(layout_entries)} actors spawned.")
    return spawned_actors


def load_layout_from_json(json_path):
    """
    Loads a layout definition from a JSON file on disk.
    Expected format: {"actors": [ {...}, {...}, ... ]}
    """
    if not os.path.exists(json_path):
        unreal.log_error(f"Layout file not found: {json_path}")
        return []

    with open(json_path, "r") as f:
        data = json.load(f)

    return data.get("actors", [])


# =============================================================================
# IRON BREACH ENCOUNTER BUILD PIPELINE
# =============================================================================

def build_encounter_from_layout(level_path, layout_json_path, force_new_level=False):
    """
    Full pipeline: load/create a level, populate it from a JSON layout file,
    and save the result. This is the entry point for procedural encounter builds.
    """
    unreal.log("--- Building Iron Breach Encounter ---")

    if not load_or_create_level(level_path, force_new=force_new_level):
        unreal.log_error("Aborting: level load/create failed.")
        return

    layout_entries = load_layout_from_json(layout_json_path)
    if not layout_entries:
        unreal.log_error("No layout entries found, aborting.")
        return

    spawn_actors_from_layout(layout_entries)
    save_current_level()

    unreal.log("--- Encounter Build Complete ---")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
# Example layout JSON (save as e.g. C:/Assets/Layouts/kaiju_raid_01.json):
#
# {
#   "actors": [
#     {
#       "asset_path": "/Game/IronBreach/Kaiju/Alpha/BP_Kaiju_Alpha.BP_Kaiju_Alpha",
#       "location": [500.0, 0.0, 100.0],
#       "rotation": [0.0, -90.0, 0.0],
#       "label": "Kaiju_Spawn_01"
#     },
#     {
#       "asset_path": "/Game/IronBreach/Mech/BP_Mech_Base.BP_Mech_Base",
#       "location": [-800.0, 200.0, 100.0],
#       "rotation": [0.0, 90.0, 0.0],
#       "label": "Mech_Drop_01"
#     }
#   ]
# }
#
# Then run:
# build_encounter_from_layout(
#     level_path="/Game/IronBreach/Maps/Raid_01",
#     layout_json_path="C:/Assets/Layouts/kaiju_raid_01.json",
#     force_new_level=False
# )
