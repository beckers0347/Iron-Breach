"""
IBPY: ib_inventory_mission1_spots.py   (READ-ONLY - changes nothing)

Dumps the actors needed to place the M1 Act I squad NPCs (Rhodes, Okafor,
Yun) in the Carrowgate barracks/watch room, from whichever level is open:
  - current level name (so we know if this is the real mission level or the
    _GarrisonPreview_Disposable copy)
  - PlayerStart(s), Act*Director actors
  - anything labeled like Barracks / WeaponRack / Door / Radio / Comms /
    Console / Desk / Table / Locker / Bunk / Medical / Hospital / Muster
  - the current transform of every NPC_* actor
For each: label, class, location, bounds center + full size.

HOW TO RUN (editor, not PIE):
    py "X:/IronBreach/Scripts/ib_inventory_mission1_spots.py"
Paste back the IBPY lines.
"""

import unreal

KEYWORDS = ("barracks", "weaponrack", "weapon_rack", "door", "radio", "comms",
            "console", "desk", "table", "locker", "bunk", "medical", "hospital",
            "muster", "director", "playerstart", "ps_", "watch", "terminal")
MAX_LINES = 160


def log(msg):
    unreal.log(f"IBPY: {msg}")


def fmt(a):
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    try:
        o, e = a.get_actor_bounds(False)
        b = (f"bounds center=({o.x:.0f},{o.y:.0f},{o.z:.0f}) "
             f"size=({e.x * 2:.0f},{e.y * 2:.0f},{e.z * 2:.0f})")
    except Exception:
        b = "bounds n/a"
    return (f"'{a.get_actor_label()}' [{a.get_class().get_name()}] "
            f"loc=({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}) yaw={rot.yaw:.0f} {b}")


def main():
    log("==== MISSION 1 SPOT INVENTORY ====")
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        log(f"Level: {world.get_path_name()}")
    except Exception as ex:
        log(f"could not read level name: {ex}")

    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()
    log(f"total actors: {len(actors)}")

    npcs, starts, directors, hits = [], [], [], []
    for a in actors:
        lbl = a.get_actor_label()
        low = lbl.lower()
        cls = a.get_class().get_name().lower()
        if lbl.startswith("NPC_"):
            npcs.append(a)
        elif isinstance(a, unreal.PlayerStart):
            starts.append(a)
        elif "director" in low or "director" in cls:
            directors.append(a)
        elif any(k in low for k in KEYWORDS):
            hits.append(a)

    log(f"---- NPC actors ({len(npcs)}) ----")
    for a in npcs:
        log("  " + fmt(a))
    log(f"---- PlayerStart ({len(starts)}) ----")
    for a in starts:
        log("  " + fmt(a))
    log(f"---- Directors ({len(directors)}) ----")
    for a in directors:
        log("  " + fmt(a))
    log(f"---- Candidate props/buildings ({len(hits)}; showing up to {MAX_LINES}) ----")
    for a in sorted(hits, key=lambda x: x.get_actor_label())[:MAX_LINES]:
        log("  " + fmt(a))
    log("==== DONE ====")


main()
