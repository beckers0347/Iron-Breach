"""
IBPY: ib_place_m1_act5_muster.py

Adds the Act V "hospital muster" squad: copies of Rhodes, Okafor and Yun
standing around the spot where Ms. Idris is handed over (outside
Medical_DoorFrame), all facing that spot. Mission doc: "at the hospital
muster, the squad takes her weight onto a stretcher. Rhodes asks who brought
her in. Bricks coins it ... Static repeats it once."

How: duplicates the existing Act I squad actors (so mesh, anim class, scale and
the orientation you already fixed all carry over) and labels them
  NPC_Rhodes_ACT5, NPC_Okafor_Bricks_ACT5, NPC_Yun_Static_ACT5
Safe to re-run: if a copy already exists it is just re-placed, not duplicated.
The Act I actors (and the directors' SquadNPCs/DistrictNPCs wiring) are not
touched. NPC_Idris stays hidden at the muster centre; the Act V carry/naming
logic should unhide her when she arrives.

Spots derived from the level:
  Medical_DoorFrame, outward = toward IBGC_FF_Fore_DoorBar_Medical,
  centre = MUSTER_DISTANCE out from the door (same spot Idris is parked at).

HOW TO RUN (editor, not PIE):
    py "X:/IronBreach/Scripts/ib_place_m1_act5_muster.py"
"""

import math
import unreal

# ----------------------------- CONFIG --------------------------------------
GROUND_Z = 384.0
MUSTER_DISTANCE = 500.0      # centre of the muster, cm out from Medical door
RING_RADIUS = 220.0          # squad distance from the centre
FACING_YAW_OFFSET = 0.0      # same meaning as in ib_place_m1_squad.py

DOOR_LABEL = "Medical_DoorFrame"
BAR_LABEL = "IBGC_FF_Fore_DoorBar_Medical"
FALLBACK_DOOR = (8817.0, 6453.0)
FALLBACK_OUTWARD = (-1.0, 0.0)

# source label, copy label, angle (deg) around the centre, measured from "outward"
SLOTS = [
    ("NPC_Rhodes_PLACEHOLDER", "NPC_Rhodes_ACT5", 90.0),
    ("NPC_Okafor_Bricks_PLACEHOLDER", "NPC_Okafor_Bricks_ACT5", -90.0),
    ("NPC_Yun_Static_PLACEHOLDER", "NPC_Yun_Static_ACT5", 0.0),
]
IDRIS_LABEL = "NPC_Idris"
# ---------------------------------------------------------------------------


def log(msg):
    unreal.log(f"IBPY: {msg}")


def find(actors, label):
    for a in actors:
        if a.get_actor_label() == label:
            return a
    return None


def norm(v):
    m = math.hypot(v[0], v[1])
    return (v[0] / m, v[1] / m) if m > 1e-6 else (1.0, 0.0)


def rot2(v, deg):
    r = math.radians(deg)
    return (v[0] * math.cos(r) - v[1] * math.sin(r), v[0] * math.sin(r) + v[1] * math.cos(r))


def main():
    log("==== PLACE M1 ACT V MUSTER SQUAD ====")
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()

    door = find(actors, DOOR_LABEL)
    bar = find(actors, BAR_LABEL)
    if door and bar:
        d = (door.get_actor_location().x, door.get_actor_location().y)
        b = (bar.get_actor_location().x, bar.get_actor_location().y)
        outward = norm((b[0] - d[0], b[1] - d[1]))
    else:
        d, outward = FALLBACK_DOOR, FALLBACK_OUTWARD
        log("WARNING: Medical door/bar not found; using fallback position")
    centre = (d[0] + outward[0] * MUSTER_DISTANCE, d[1] + outward[1] * MUSTER_DISTANCE)
    log(f"Medical door={d} outward=({outward[0]:.2f},{outward[1]:.2f}) muster centre=({centre[0]:.0f},{centre[1]:.0f})")

    for src_label, new_label, ang in SLOTS:
        copy = find(actors, new_label)
        if copy is None:
            src = find(actors, src_label)
            if src is None:
                log(f"ERROR: source '{src_label}' not found - skipped")
                continue
            copy = sub.duplicate_actor(src)
            if copy is None:
                log(f"ERROR: could not duplicate '{src_label}'")
                continue
            copy.set_actor_label(new_label)
            log(f"  created '{new_label}' from '{src_label}'")
        off = rot2(outward, ang)
        x, y = centre[0] + off[0] * RING_RADIUS, centre[1] + off[1] * RING_RADIUS
        yaw = math.degrees(math.atan2(centre[1] - y, centre[0] - x)) + FACING_YAW_OFFSET
        copy.set_actor_location(unreal.Vector(x, y, GROUND_Z), False, False)
        copy.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), False)
        try:
            copy.set_actor_hidden_in_game(False)
        except Exception:
            pass
        log(f"  '{new_label}' -> ({x:.0f},{y:.0f},{GROUND_Z:.0f}) yaw={yaw:.0f}")

    idris = find(actors, IDRIS_LABEL)
    if idris is not None:
        idris.set_actor_location(unreal.Vector(centre[0], centre[1], GROUND_Z), False, False)
        log(f"  '{IDRIS_LABEL}' parked (still hidden in game) at muster centre ({centre[0]:.0f},{centre[1]:.0f})")

    log("==== DONE. Press Play, walk to the Medical muster, check them; save the level if good. ====")


main()
