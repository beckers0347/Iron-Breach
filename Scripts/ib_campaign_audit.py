"""
IBPY: ib_campaign_audit.py

Read-only recon for the M1 LANDFALL campaign work. Doesn't change or save
anything. Answers three questions I can't get reliably from grepping .umap
files on disk (class names show up in every map's dependency table whether
or not an actor is actually placed, so that check was a dead end):

  1. Which of the five Act directors (Act1BarracksDirector ... Act5RetreatDirector)
     are actually PLACED as live actor instances in the currently-OPEN level,
     and what their SquadNPCs / DistrictNPCs arrays currently hold (empty or not).
  2. Whether an AIBKaijuSpawner exists anywhere in the open level.
  3. Whether the named NPC assets (Ms. Idris, Rhodes, Okafor/Bricks, Yun/Static)
     actually still exist as loadable assets under /Game/Characters/NPCs/ --
     the folder looked empty on disk, which could mean the work was never saved.

HOW TO RUN
----------
Open CarrowGateGarrison (the real one, not a _GarrisonPreview_Disposable
variant) as your current level, then:
    py "X:/IronBreach/Scripts/ib_campaign_audit.py"
Paste back the full output.
"""

import unreal

DIRECTOR_CLASSES = [
    "Act1BarracksDirector",
    "Act2EscalationDirector",
    "Act3ContactDirector",
    "Act4DeepWaterDirector",
    "Act5RetreatDirector",
]

NPC_ASSET_CANDIDATES = [
    "/Game/Characters/NPCs/MsIdris/Ms_Idris",
    "/Game/Characters/NPCs/MsIdris/Ms_Idris_Skeleton",
    "/Game/Characters/NPCs/Rhodes/Rhodes",
    "/Game/Characters/NPCs/Okafor/Okafor",
    "/Game/Characters/NPCs/Bricks/Bricks",
    "/Game/Characters/NPCs/Yun/Yun",
    "/Game/Characters/NPCs/Static/Static",
]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== CAMPAIGN AUDIT ====")

    world = unreal.EditorLevelLibrary.get_editor_world() if hasattr(unreal, "EditorLevelLibrary") else None
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()
    log(f"Currently open level has {len(all_actors)} total actors.")

    log("---- Act Directors ----")
    for cls_name in DIRECTOR_CLASSES:
        matches = [a for a in all_actors if a.get_class().get_name() == cls_name]
        if not matches:
            log(f"{cls_name}: NOT PLACED in this level.")
            continue
        for a in matches:
            log(f"{cls_name}: PLACED as '{a.get_name()}' at {a.get_actor_location()}")
            for prop_name in ("SquadNPCs", "DistrictNPCs"):
                try:
                    val = a.get_editor_property(prop_name)
                    log(f"    {prop_name}: {len(val)} entr(y/ies) -> {list(val)}")
                except Exception:
                    pass  # property doesn't exist on this class, that's fine

    log("---- Kaiju Spawners ----")
    spawner_matches = [a for a in all_actors if "KaijuSpawner" in a.get_class().get_name()]
    if not spawner_matches:
        log("No AIBKaijuSpawner (or similarly named) actor found in this level.")
    else:
        for a in spawner_matches:
            log(f"Spawner: '{a.get_name()}' ({a.get_class().get_name()}) at {a.get_actor_location()}")

    log("---- Containment / blocking volumes ----")
    vol_matches = [a for a in all_actors if "Volume" in a.get_class().get_name()]
    log(f"{len(vol_matches)} Volume-class actor(s) in this level (includes lighting/ambient volumes, not just blocking):")
    for a in vol_matches:
        log(f"    {a.get_name()} ({a.get_class().get_name()})")

    log("---- Named NPC assets on disk ----")
    for path in NPC_ASSET_CANDIDATES:
        exists = unreal.EditorAssetLibrary.does_asset_exist(path)
        log(f"{path}: {'EXISTS' if exists else 'missing'}")

    log("---- Player start / game mode sanity ----")
    starts = [a for a in all_actors if isinstance(a, unreal.PlayerStart)]
    log(f"{len(starts)} PlayerStart(s) in this level.")

    log("==== DONE ====")


main()
