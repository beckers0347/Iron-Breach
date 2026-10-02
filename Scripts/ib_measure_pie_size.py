"""
IBPY: ib_measure_pie_size.py  (v2)

Run WHILE PIE IS RUNNING (type into the Cmd box at the bottom of the editor).

v1 used actor bounds, which are STATIC mesh bounds and ignore animation, so it
proved nothing. v2 reads the animated world-space position of every bone and
reports the bounding box of the skeleton plus where the Hips and Head are.
A normal human skeleton is roughly 160-180 cm tall (Z) and upright.

    py "X:/IronBreach/Scripts/ib_measure_pie_size.py"
"""

import unreal


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_pie_world():
    try:
        subsys = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        return subsys.get_game_world()
    except Exception as ex:
        log(f"get_game_world failed: {ex}")
        return None


def main():
    log("==== PIE BONE-SPACE SIZE MEASURE (v2) ====")
    world = get_pie_world()
    if world is None:
        log("ERROR: no PIE world. Press Play first, then run this from the Cmd box.")
        return
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SkeletalMeshActor)
    log(f"SkeletalMeshActors in PIE world: {len(actors)}")
    for a in actors:
        comp = a.skeletal_mesh_component
        n = comp.get_num_bones()
        pts = {}
        for i in range(n):
            name = comp.get_bone_name(i)
            pts[str(name)] = comp.get_socket_location(name)
        if not pts:
            log(f"'{a.get_actor_label()}': no bones read")
            continue
        xs = [p.x for p in pts.values()]
        ys = [p.y for p in pts.values()]
        zs = [p.z for p in pts.values()]
        loc = a.get_actor_location()
        hips = pts.get("Hips")
        head = pts.get("Head")
        log(f"'{a.get_actor_label()}': {n} bones, skeleton size (X,Y,Z) cm = "
            f"({max(xs) - min(xs):.0f}, {max(ys) - min(ys):.0f}, {max(zs) - min(zs):.0f}); "
            f"actor loc=({loc.x:.0f},{loc.y:.0f},{loc.z:.0f})")
        if hips is not None:
            log(f"    Hips world=({hips.x:.0f},{hips.y:.0f},{hips.z:.0f})"
                + (f"  Head world=({head.x:.0f},{head.y:.0f},{head.z:.0f})" if head is not None else ""))
    log("==== DONE ====")


main()
