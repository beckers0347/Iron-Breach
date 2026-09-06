"""
SET UP WATER_PLACEHOLDER'S COLLISION FOR THE DROWN/RESPAWN MECHANIC
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Water_Placeholder is a plain StaticMeshActor, almost certainly still on
whatever the engine cube's default collision preset is (BlockAll) --
meaning the player currently just stands on top of the water like solid
ground instead of falling into it, and there's no overlap event to hook a
"you're now in the water" Blueprint check to at all.

THE FIX
-------
1. Sets Water_Placeholder's collision so Pawns specifically OVERLAP it
   (everything else keeps blocking, so it still reads as a solid volume to
   projectiles/props) -- this is what lets the player actually sink into
   the water instead of standing on it.
2. Enables "Generate Overlap Events" on it so a Level Blueprint "On Actor
   Begin/End Overlap (Water_Placeholder)" event can actually fire -- this
   is the hook the drown/respawn logic (built next, in the Level Blueprint
   via the editor UI since Blueprint graphs aren't Python-scriptable) needs
   to exist.
3. Lowers World Settings' Kill Z to effectively "off" (-100000) -- with
   Pawn collision now set to Overlap, a player who doesn't get pulled back
   out in time would otherwise free-fall forever under the water and could
   hit the level's default Kill Z and get destroyed before the 4-second
   drown timer ever gets a chance to respawn them.

Safe to re-run -- idempotent, just re-applies the same settings.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/setup_water_collision.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[SetupWaterCollision] %s" % msg)


def run():
    all_actors = actor_subsystem.get_all_level_actors()
    water_actors = [a for a in all_actors if a.get_actor_label() == "Water_Placeholder"]
    if not water_actors:
        log("ABORTED -- no actor labeled 'Water_Placeholder' found in the level.")
        return

    for water in water_actors:
        for comp in water.get_components_by_class(unreal.StaticMeshComponent):
            try:
                comp.set_generate_overlap_events(True)
            except AttributeError:
                comp.set_editor_property("generate_overlap_events", True)
            try:
                comp.set_collision_response_to_channel(
                    unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponse.ECR_OVERLAP)
                log("  %s: Pawn channel set to Overlap, overlap events enabled." % water.get_actor_label())
            except Exception as e:
                log("  %s: couldn't set the Pawn channel response directly (%s) -- falling back to the "
                    "OverlapAllDynamic collision profile instead." % (water.get_actor_label(), e))
                comp.set_collision_profile_name("OverlapAllDynamic")

    # Lower Kill Z so a sinking player doesn't get destroyed by falling out of the
    # world before the drown timer respawns them.
    world = unreal.EditorLevelLibrary.get_editor_world() if hasattr(unreal, "EditorLevelLibrary") else None
    world_settings = None
    for a in all_actors:
        if isinstance(a, unreal.WorldSettings):
            world_settings = a
            break
    if world_settings is not None:
        try:
            world_settings.set_editor_property("kill_z", -100000.0)
            log("World Settings Kill Z set to -100000 (effectively disabled).")
        except Exception as e:
            log("Couldn't set Kill Z (%s) -- check World Settings > Kill Z manually if players get "
                "destroyed before the drown timer fires." % e)
    else:
        log("Couldn't find a WorldSettings actor to lower Kill Z -- check it manually if needed.")

    log("Done. Save. Next: wire the drown/respawn logic into the Level Blueprint (Begin/End Actor Overlap "
        "on Water_Placeholder), which has to be done in the Blueprint editor UI.")


run()
