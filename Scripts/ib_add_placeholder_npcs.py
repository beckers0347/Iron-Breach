"""
IBPY: ib_add_placeholder_npcs.py

Shane's call: Ms. Idris is in the game now, and her mesh stands in as a
placeholder body for ALL the human NPCs until each gets real art. Skipping
the Dog for now.

What this does:
  1. Loads the Ms_Idris skeletal mesh from /Game/Characters/NPCs/MsIdris/Ms_Idris
     (the one you confirmed is correct and already in the game).
  2. Spawns THREE more SkeletalMeshActor instances in the currently open
     level, all wearing that same mesh, labeled clearly as placeholders:
       - NPC_Rhodes_PLACEHOLDER
       - NPC_Okafor_Bricks_PLACEHOLDER
       - NPC_Yun_Static_PLACEHOLDER
     (lined up a few meters apart so they don't overlap -- move them
     wherever they actually belong once you see them.)
  3. Finds the Act1BarracksDirector and Act2EscalationDirector instances
     already placed in this level and wires these three into their NPC
     arrays:
       - Act1BarracksDirector.SquadNPCs      <- Rhodes, Okafor, Yun
       - Act2EscalationDirector.DistrictNPCs <- Rhodes, Okafor, Yun
     (same three in both -- they're squadmates who carry through from the
     barracks into the district escort. Easy to change later once real
     models exist and you want different folks in each array.)

Does NOT touch Ms. Idris herself, does NOT import the Dog, does NOT save
the level for you -- check the World Outliner, move the three placeholders
to sensible spots, then save the level yourself (File > Save Current Level)
once it looks right.

HOW TO RUN
----------
Open CarrowGateGarrison as your current level, then:
    py "X:/IronBreach/Scripts/ib_add_placeholder_npcs.py"
Paste back the full output.
"""

import unreal

IDRIS_MESH_PATH = "/Game/Characters/NPCs/MsIdris/Ms_Idris_wSkeleton"

PLACEHOLDERS = [
    {"label": "NPC_Rhodes_PLACEHOLDER", "offset_x": 300.0},
    {"label": "NPC_Okafor_Bricks_PLACEHOLDER", "offset_x": 600.0},
    {"label": "NPC_Yun_Static_PLACEHOLDER", "offset_x": 900.0},
]

DIRECTOR_WIRING = [
    ("Act1BarracksDirector", "SquadNPCs"),
    ("Act2EscalationDirector", "DistrictNPCs"),
]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def find_base_location(all_actors):
    # Park the placeholders near wherever Ms. Idris already is, if we can
    # find her placed in the level; otherwise just use the world origin.
    for a in all_actors:
        if "Idris" in a.get_actor_label():
            loc = a.get_actor_location()
            log(f"Found Idris actor '{a.get_actor_label()}' at {loc} -- placeholders will line up near her.")
            return loc
    log("Could not find a placed Idris actor to anchor to -- using world origin instead.")
    return unreal.Vector(x=0.0, y=0.0, z=0.0)


def main():
    log("==== PLACEHOLDER NPCs (Idris mesh standing in for Rhodes/Okafor/Yun) ====")

    mesh = unreal.load_asset(IDRIS_MESH_PATH)
    if mesh is None:
        log(f"ERROR: could not load {IDRIS_MESH_PATH} -- is Ms. Idris actually imported under that path?")
        return

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()
    base_loc = find_base_location(all_actors)

    spawned = {}
    for p in PLACEHOLDERS:
        spawn_loc = unreal.Vector(x=base_loc.x + p["offset_x"], y=base_loc.y, z=base_loc.z)
        actor = actor_subsystem.spawn_actor_from_class(
            unreal.SkeletalMeshActor, spawn_loc, unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0)
        )
        if actor is None:
            log(f"ERROR: failed to spawn {p['label']}")
            continue
        actor.set_actor_label(p["label"])
        actor.skeletal_mesh_component.set_skeletal_mesh(mesh)
        spawned[p["label"]] = actor
        log(f"  Placed '{p['label']}' at {spawn_loc}")

    if len(spawned) < len(PLACEHOLDERS):
        log("WARNING: not all placeholders spawned -- skipping director wiring to avoid a half-populated array.")
        return

    npc_list = [spawned[p["label"]] for p in PLACEHOLDERS]

    log("---- Wiring into Act directors ----")
    all_actors = actor_subsystem.get_all_level_actors()  # refresh, now includes the new placeholders
    for cls_name, prop_name in DIRECTOR_WIRING:
        matches = [a for a in all_actors if a.get_class().get_name() == cls_name]
        if not matches:
            log(f"  {cls_name} not found in this level -- skipped.")
            continue
        director = matches[0]
        try:
            director.set_editor_property(prop_name, npc_list)
            confirm = director.get_editor_property(prop_name)
            log(f"  {cls_name}.{prop_name} set to {len(confirm)} entr(y/ies): "
                f"{[a.get_actor_label() for a in confirm]}")
        except Exception as e:
            log(f"  ERROR setting {cls_name}.{prop_name}: {e}")

    log("==== DONE. Review placement in the World Outliner, move the three "
        "placeholders to where they should actually stand, then save the "
        "level yourself. ====")


main()
