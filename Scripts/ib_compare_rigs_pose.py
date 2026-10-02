"""
IBPY: ib_compare_rigs_pose.py

Read-only. In Play, NPCs using ABP_NPC_Locomotion come out giant and lying
down, so the Infantry animations disagree with Ms_Idris_Infantry's rig.
Compares Ms_Idris_Infantry against the player's Base_Character_Mesh:
  1. bone count, how many bone NAMES match, names unique to each side
  2. reference-pose transform (component space) of the first bones + any
     root/hips bone: location, rotation, scale -- this is where an extra
     -90 rotation or a 100x scale would show up
  3. Loco_Idle's own pose for the root/hips bone at t=0
Changes nothing (temp actors are spawned far below the map and destroyed).

HOW TO RUN
    py "X:/IronBreach/Scripts/ib_compare_rigs_pose.py"
Paste back the full output.
"""
import unreal

BASE_MESH = "/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh"
IDRIS_MESH = "/Game/Characters/NPCs/MsIdris/Ms_Idris_Infantry"
IDLE_ANIM = "/Game/Characters/Infantry/Animations/Locomotion_Unarmed/Loco_Idle"


def log(m):
    unreal.log(f"IBPY: {m}")


def fmt_t(t):
    l, r, s = t.translation, t.rotation.rotator(), t.scale3d
    return (f"loc=({l.x:.2f},{l.y:.2f},{l.z:.2f}) "
            f"rot(r={r.roll:.1f},p={r.pitch:.1f},y={r.yaw:.1f}) "
            f"scale=({s.x:.3f},{s.y:.3f},{s.z:.3f})")


def inspect(mesh, label):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = sub.spawn_actor_from_class(unreal.SkeletalMeshActor,
                                   unreal.Vector(x=0, y=0, z=-50000),
                                   unreal.Rotator(roll=0, pitch=0, yaw=0))
    names, poses = [], {}
    try:
        a.set_actor_label(f"TEMP_PoseCheck_{label}")
        c = a.skeletal_mesh_component
        c.set_skinned_asset_and_update(mesh)
        n = c.get_num_bones()
        names = [str(c.get_bone_name(i)) for i in range(n)]
        pick = names[:6] + [x for x in names if x.lower().endswith(("hips", "root", "pelvis"))]
        for nm in dict.fromkeys(pick):
            poses[nm] = c.get_socket_transform(nm, unreal.RelativeTransformSpace.RTS_COMPONENT)
    except Exception as e:
        log(f"  [{label}] error: {e}")
    finally:
        sub.destroy_actor(a)
    return names, poses


def main():
    log("==== COMPARE RIGS (Infantry base vs Idris) ====")
    base = unreal.load_asset(BASE_MESH)
    idris = unreal.load_asset(IDRIS_MESH)
    if not base or not idris:
        log("ERROR: could not load one of the meshes."); return

    bn, bp = inspect(base, "Base")
    inn, ip = inspect(idris, "Idris")
    log(f"Base mesh: {len(bn)} bones. First 8: {bn[:8]}")
    log(f"Idris mesh: {len(inn)} bones. First 8: {inn[:8]}")
    common = set(bn) & set(inn)
    log(f"Matching bone names: {len(common)} (Base-only {len(set(bn)-set(inn))}, Idris-only {len(set(inn)-set(bn))})")
    log(f"Base-only sample: {sorted(set(bn)-set(inn))[:10]}")
    log(f"Idris-only sample: {sorted(set(inn)-set(bn))[:10]}")

    log("---- Reference pose, component space ----")
    for lbl, poses in (("BASE", bp), ("IDRIS", ip)):
        for nm, t in poses.items():
            log(f"  {lbl} {nm}: {fmt_t(t)}")

    log("---- Loco_Idle t=0 pose on root/hips ----")
    anim = unreal.load_asset(IDLE_ANIM)
    for nm in [x for x in bn if x.lower().endswith(("hips", "root", "pelvis"))][:3] + bn[:1]:
        try:
            t = unreal.AnimationLibrary.get_bone_pose_for_time(anim, nm, 0.0, False)
            log(f"  Loco_Idle {nm}: {fmt_t(t)}")
        except Exception as e:
            log(f"  could not read Loco_Idle pose for {nm}: {e}")
            break
    log("==== DONE ====")


main()
