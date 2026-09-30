"""
IBPY: ib_diag_command_door.py

READ-ONLY. The door-carving script's boolean subtract for Command & Comms
resulted in an IDENTICAL triangle count before and after (1936862 both
times) -- meaning the cutter box didn't actually touch the mesh. This
checks:
  1. Every level actor whose label is exactly "08_Command & Comms_DoorFrame"
     (in case there's more than one, which would explain get_actor_by_label
     picking an unexpected one).
  2. SM_Command_Tripo's current transform.
  3. The door's position relative to the building, both in world space and
     unrotated into the building's local frame, to compare against the
     apothem (756.5cm) and the earlier-established facet direction.

Touches nothing.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_diag_command_door.py"
"""

import math
import unreal


def log(msg):
    unreal.log(f"IBPY: {msg}")


def unrotate_vector_yaw(x, y, yaw_degrees):
    rad = math.radians(-yaw_degrees)
    c = math.cos(rad)
    s = math.sin(rad)
    return (x * c - y * s, x * s + y * c)


def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()

    log("---- All actors labeled '08_Command & Comms_DoorFrame' ----")
    door_matches = []
    for a in all_actors:
        if a.get_actor_label() == "08_Command & Comms_DoorFrame":
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            folder = str(a.get_folder_path())
            log(f"  [{a.get_class().get_name()}] loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) rot_yaw={rot.yaw:.1f} folder='{folder}'")
            door_matches.append(a)
    log(f"Total matches: {len(door_matches)}")

    log("---- SM_Command_Tripo current transform ----")
    command = None
    for a in all_actors:
        if a.get_actor_label() == "SM_Command_Tripo":
            command = a
            break
    if not command:
        log("SM_Command_Tripo NOT FOUND.")
        log("Done.")
        return

    actor_loc = command.get_actor_location()
    actor_rot = command.get_actor_rotation()
    actor_scale = command.get_actor_scale3d()
    log(f"  loc=({actor_loc.x:.1f},{actor_loc.y:.1f},{actor_loc.z:.1f}) yaw={actor_rot.yaw:.1f} scale=({actor_scale.x:.1f},{actor_scale.y:.1f},{actor_scale.z:.1f})")

    log("---- Each door match's position relative to SM_Command_Tripo ----")
    for d in door_matches:
        door_loc = d.get_actor_location()
        rel_x = door_loc.x - actor_loc.x
        rel_y = door_loc.y - actor_loc.y
        local_x, local_y = unrotate_vector_yaw(rel_x, rel_y, actor_rot.yaw)
        dist_from_center = math.sqrt(local_x * local_x + local_y * local_y)
        log(f"  door_loc=({door_loc.x:.1f},{door_loc.y:.1f},{door_loc.z:.1f}) -> local=({local_x:.1f},{local_y:.1f}) dist_from_center={dist_from_center:.1f} (apothem=756.5)")

    log("Done.")


main()
