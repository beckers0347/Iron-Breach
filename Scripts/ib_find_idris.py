"""
IBPY: ib_find_idris.py

Quick read-only search for wherever the Ms. Idris skeletal mesh actually
lives now -- my guessed path (/Game/Characters/NPCs/MsIdris/Ms_Idris) came
back "Failed to find object", so either she landed somewhere else or under
a different asset name.

Searches the whole /Game/ tree for any asset with "idris" in its name
(case-insensitive) and prints the exact asset path + class for each hit,
plus does the same for any actor in the currently open level with "idris"
in its label, so we can see exactly what's placed and what it's using.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_find_idris.py"
Paste back the full output.
"""

import unreal

registry = unreal.AssetRegistryHelpers.get_asset_registry()


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== FIND IDRIS ====")

    log("---- Asset registry search (/Game, name contains 'idris') ----")
    all_assets = registry.get_assets_by_path("/Game", recursive=True)
    hits = [a for a in all_assets if "idris" in str(a.asset_name).lower()]
    if not hits:
        log("No assets anywhere under /Game with 'idris' in the name.")
    for a in hits:
        log(f"  {a.get_full_name()}  (package: {a.package_name})")

    log("---- Level actors with 'idris' in the label ----")
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()
    actor_hits = [a for a in all_actors if "idris" in a.get_actor_label().lower()]
    if not actor_hits:
        log("No placed actor in this level has 'idris' in its label.")
    for a in actor_hits:
        log(f"  Actor '{a.get_actor_label()}' ({a.get_class().get_name()}) at {a.get_actor_location()}")
        if isinstance(a, unreal.SkeletalMeshActor):
            mesh = a.skeletal_mesh_component.get_skeletal_mesh_asset() if hasattr(
                a.skeletal_mesh_component, "get_skeletal_mesh_asset"
            ) else a.skeletal_mesh_component.skeletal_mesh
            if mesh:
                log(f"      -> using mesh asset: {mesh.get_path_name()}")
            else:
                log("      -> no mesh assigned on this actor")

    log("==== DONE ====")


main()
