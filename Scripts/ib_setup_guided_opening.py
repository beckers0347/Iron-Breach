"""
IBPY: ib_setup_guided_opening.py

Run AFTER the C++ is compiled (IBGuideRoute + IBDialogueVoice). Sets up:

  1. VO speaker tags on the NPC actors, so voiced lines play from the right NPC in 3D:
        Rhodes -> VO_Rhodes   Okafor/Bricks -> VO_Bricks   Yun/Static -> VO_Static
     (Act I originals and the *_ACT5 copies both get tagged; the one nearest the
     player is the one that speaks.)
  2. One AIBGuideRoute actor ("M1_GuideRoute") at the world origin:
        guide      = NPC_Rhodes_PLACEHOLDER
        followers  = Okafor, Yun (placeholders)
        waypoint 0 = approach to the Medical muster (derived from Medical_DoorFrame)
        starts when Act1BarracksDirector finishes (StartAfterAct1)
        debug draw ON so you can see the path while testing
     Safe to re-run: if M1_GuideRoute exists it is just re-configured.

Edit the route afterwards in Details (add waypoints with the diamond widgets, change
speed, leash, call-out lines, turn bDebugDraw off).

HOW TO RUN (editor, not PIE):
    py "X:/IronBreach/Scripts/ib_setup_guided_opening.py"
"""

import unreal

ROUTE_LABEL = "M1_GuideRoute"
GUIDE_LABEL = "NPC_Rhodes_PLACEHOLDER"
FOLLOWER_LABELS = ["NPC_Okafor_Bricks_PLACEHOLDER", "NPC_Yun_Static_PLACEHOLDER"]
ACT1_LABEL = "Act1BarracksDirector"

MEDICAL_DOOR_LABEL = "Medical_DoorFrame"
MEDICAL_BAR_LABEL = "IBGC_FF_Fore_DoorBar_Medical"
MUSTER_STOP_DISTANCE = 1100.0   # cm out from the Medical door (beyond the Act V ring)
GROUND_Z = 384.0
FALLBACK_STOP = (7717.0, 6454.0)

TAG_RULES = [   # (label contains, tag)
    ("Rhodes", "VO_Rhodes"),
    ("Okafor", "VO_Bricks"),
    ("Bricks", "VO_Bricks"),
    ("Yun", "VO_Static"),
    ("Static", "VO_Static"),
]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def find(actors, label):
    for a in actors:
        if a.get_actor_label() == label:
            return a
    return None


def tag_npcs(actors):
    log("---- 1. VO speaker tags ----")
    for a in actors:
        lbl = a.get_actor_label()
        if not lbl.startswith("NPC_"):
            continue
        for key, tag in TAG_RULES:
            if key in lbl:
                existing = [str(t) for t in a.get_editor_property("tags")]
                if tag not in existing:
                    a.set_editor_property("tags", [unreal.Name(t) for t in existing + [tag]])
                log(f"  '{lbl}' tagged {tag}")
                break


def medical_stop(actors):
    door = find(actors, MEDICAL_DOOR_LABEL)
    bar = find(actors, MEDICAL_BAR_LABEL)
    if not (door and bar):
        log("  WARNING: Medical door/bar not found; using fallback stop position.")
        return unreal.Vector(FALLBACK_STOP[0], FALLBACK_STOP[1], GROUND_Z)
    d, b = door.get_actor_location(), bar.get_actor_location()
    dx, dy = b.x - d.x, b.y - d.y
    m = (dx * dx + dy * dy) ** 0.5 or 1.0
    return unreal.Vector(d.x + dx / m * MUSTER_STOP_DISTANCE, d.y + dy / m * MUSTER_STOP_DISTANCE, GROUND_Z)


def main():
    log("==== SETUP GUIDED OPENING ====")
    route_cls = getattr(unreal, "IBGuideRoute", None)
    if route_cls is None:
        unreal.log_error("IBPY: unreal.IBGuideRoute not found -- compile the C++ (IBGuideRoute.h/.cpp) "
                         "and restart/reload the editor first.")
        return

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()

    tag_npcs(actors)

    log("---- 2. Guide route ----")
    guide = find(actors, GUIDE_LABEL)
    followers = [a for a in (find(actors, l) for l in FOLLOWER_LABELS) if a is not None]
    if guide is None:
        unreal.log_error(f"IBPY: guide '{GUIDE_LABEL}' not found in this level.")
        return

    route = find(actors, ROUTE_LABEL)
    if route is None:
        route = sub.spawn_actor_from_class(route_cls, unreal.Vector(0.0, 0.0, 0.0))
        route.set_actor_label(ROUTE_LABEL)
        log(f"  spawned '{ROUTE_LABEL}' at the world origin")
    else:
        log(f"  '{ROUTE_LABEL}' already exists; re-configuring")

    route.set_editor_property("guide_actor", guide)
    route.set_editor_property("followers", followers)

    stop = medical_stop(actors)
    wp = unreal.IBGuideWaypoint()
    wp.set_editor_property("location", stop)           # route is at the origin: local == world
    wp.set_editor_property("wait_for_player_radius", 700.0)
    wp.set_editor_property("pause_seconds", 1.0)
    wp.set_editor_property("arrival_event_tag", "ArrivedMuster")
    route.set_editor_property("waypoints", [wp])

    act1 = find(actors, ACT1_LABEL)
    if act1 is not None:
        route.set_editor_property("start_after_act1", act1)
        log(f"  starts when '{ACT1_LABEL}' completes")
    else:
        log(f"  WARNING: '{ACT1_LABEL}' not found; set bAutoStart or StartAfterAct1 by hand.")

    route.set_editor_property("debug_draw", True)

    # Confirm what stuck
    log(f"  guide_actor   = {route.get_editor_property('guide_actor')}")
    log(f"  followers     = {[f.get_actor_label() for f in route.get_editor_property('followers')]}")
    log(f"  waypoints     = {len(route.get_editor_property('waypoints'))} (stop at "
        f"({stop.x:.0f},{stop.y:.0f},{stop.z:.0f}))")
    log(f"  walk speed    = {route.get_editor_property('walk_speed')}  "
        f"leash = {route.get_editor_property('leash_distance_cm')}")
    log("==== DONE. Save the level. Press Play: after Act I's stand-to line the squad should "
        "walk to the Medical muster and wait whenever you fall behind. ====")


main()
