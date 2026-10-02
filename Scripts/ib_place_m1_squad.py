"""
IBPY: ib_place_m1_squad.py

Places the Mission 1 / Act I squad NPCs in the open level.

Why outside the Barracks: the inventory (ib_inventory_mission1_spots.py)
showed the Barracks is a solid mesh with no interior/collision shell in this
level, so there is no watch room to stand in yet. Until one exists, the squad
musters on the forecourt just outside the Barracks door, facing the player's
approach (PlayerStart). All spots are derived from the level's own actors:

  door      = 'Barracks_DoorFrame'
  outward   = direction from the door to 'IBGC_FF_Fore_DoorBar_Barracks'
  facing    = toward the first PlayerStart
  ground Z  = 384 (HUB_Z, the garrison's flat road height)

Placement (outward = out of the door, side = perpendicular):
  Rhodes (Lt.)      centre,  MUSTER_DISTANCE cm out
  Okafor (Bricks)   left,    MUSTER_DISTANCE cm out, SIDE_SPACING to the side
  Yun (Static)      right,   MUSTER_DISTANCE cm out, SIDE_SPACING to the side
Ms. Idris is NOT in Act I: she is hidden in game and parked at the Medical
muster (outside Medical_DoorFrame), where the Act V naming beat happens.

Only moves/rotates these four actors (roll 0, pitch 0). Mesh, scale, and the
Act1BarracksDirector / Act2EscalationDirector references are untouched.
Previous transforms are logged so anything can be reverted by hand.

HOW TO RUN (editor, not PIE):
    py "X:/IronBreach/Scripts/ib_place_m1_squad.py"
Then Play and check them. Adjust constants below and re-run as needed; save the
level when you're happy.
"""

import math
import unreal

# ----------------------------- CONFIG --------------------------------------
GROUND_Z = 384.0
MUSTER_DISTANCE = 650.0     # cm out from the door along "outward"
SIDE_SPACING = 220.0        # cm between squad members
FACING_YAW_OFFSET = 0.0     # add/subtract if the mesh's "forward" isn't +X after PIE test
IDRIS_PARK_BACKOFF = 500.0  # cm out from the Medical door for Idris

DOOR_LABEL = "Barracks_DoorFrame"
DOORBAR_LABEL = "IBGC_FF_Fore_DoorBar_Barracks"
MEDICAL_DOOR_LABEL = "Medical_DoorFrame"
MEDICAL_BAR_LABEL = "IBGC_FF_Fore_DoorBar_Medical"
BARRACKS_LABEL = "Barracks"

FALLBACK_DOOR = (2764.0, -1147.0)
FALLBACK_OUTWARD = (0.0, 1.0)
FALLBACK_FACE_TARGET = (4690.0, 4024.0)

NPC_SLOTS = [
    # label, side multiplier (0 centre, -1 left, +1 right)
    ("NPC_Rhodes_PLACEHOLDER", 0.0),
    ("NPC_Okafor_Bricks_PLACEHOLDER", -1.0),
    ("NPC_Yun_Static_PLACEHOLDER", 1.0),
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


def xy(a):
    l = a.get_actor_location()
    return (l.x, l.y)


def norm(v):
    m = math.hypot(v[0], v[1])
    return (v[0] / m, v[1] / m) if m > 1e-6 else (0.0, 1.0)


def yaw_to(src, dst):
    return math.degrees(math.atan2(dst[1] - src[1], dst[0] - src[0]))


def place(actor, x, y, yaw, hidden=None):
    before = actor.get_actor_location()
    brot = actor.get_actor_rotation()
    actor.set_actor_location(unreal.Vector(x, y, GROUND_Z), False, False)
    actor.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), False)
    if hidden is not None:
        try:
            actor.set_actor_hidden_in_game(hidden)
        except Exception as ex:
            log(f"  could not set hidden-in-game on '{actor.get_actor_label()}': {ex} "
                "(set 'Actor Hidden In Game' in Details by hand)")
    log(f"'{actor.get_actor_label()}': ({before.x:.0f},{before.y:.0f},{before.z:.0f}) "
        f"rot(P,Y,R)=({brot.pitch:.0f},{brot.yaw:.0f},{brot.roll:.0f})  ->  "
        f"({x:.0f},{y:.0f},{GROUND_Z:.0f}) yaw={yaw:.0f}")


def main():
    log("==== PLACE M1 ACT I SQUAD ====")
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()

    door = find(actors, DOOR_LABEL)
    bar = find(actors, DOORBAR_LABEL)
    door_xy = xy(door) if door else FALLBACK_DOOR
    if door is None:
        log(f"WARNING: '{DOOR_LABEL}' not found; using fallback {FALLBACK_DOOR}")
    if door and bar:
        outward = norm((xy(bar)[0] - door_xy[0], xy(bar)[1] - door_xy[1]))
    else:
        outward = FALLBACK_OUTWARD
        log("WARNING: door bar not found; assuming outward = +Y")
    side = (-outward[1], outward[0])   # perpendicular, to the left looking outward

    face_target = FALLBACK_FACE_TARGET
    for a in actors:
        if isinstance(a, unreal.PlayerStart):
            face_target = xy(a)
            break
    log(f"door={door_xy} outward=({outward[0]:.2f},{outward[1]:.2f}) face target={face_target}")

    # --- safety: stay clear of the Barracks mesh bounds ---
    barracks = find(actors, BARRACKS_LABEL)
    bb = None
    if barracks:
        o, e = barracks.get_actor_bounds(False)
        bb = (o.x - e.x, o.x + e.x, o.y - e.y, o.y + e.y)
        log(f"Barracks bounds X[{bb[0]:.0f},{bb[1]:.0f}] Y[{bb[2]:.0f},{bb[3]:.0f}]")

    for label, s in NPC_SLOTS:
        a = find(actors, label)
        if a is None:
            log(f"ERROR: '{label}' not found in this level - skipped")
            continue
        x = door_xy[0] + outward[0] * MUSTER_DISTANCE + side[0] * SIDE_SPACING * s
        y = door_xy[1] + outward[1] * MUSTER_DISTANCE + side[1] * SIDE_SPACING * s
        yaw = yaw_to((x, y), face_target) + FACING_YAW_OFFSET
        if bb and bb[0] <= x <= bb[1] and bb[2] <= y <= bb[3]:
            log(f"  WARNING: '{label}' target ({x:.0f},{y:.0f}) is inside the Barracks bounds - "
                "increase MUSTER_DISTANCE")
        place(a, x, y, yaw, hidden=False)

    idris = find(actors, IDRIS_LABEL)
    if idris is not None:
        md = find(actors, MEDICAL_DOOR_LABEL)
        mb = find(actors, MEDICAL_BAR_LABEL)
        if md and mb:
            m = xy(md)
            out = norm((xy(mb)[0] - m[0], xy(mb)[1] - m[1]))
            px, py = m[0] + out[0] * IDRIS_PARK_BACKOFF, m[1] + out[1] * IDRIS_PARK_BACKOFF
            place(idris, px, py, yaw_to((px, py), m), hidden=True)
            log("  Idris hidden in game and parked at the Medical muster for the Act V beat.")
        else:
            log("WARNING: Medical door/bar not found; Idris left where she is (not moved).")

    log("==== DONE. Press Play and check the squad; save the level if good. ====")


main()
