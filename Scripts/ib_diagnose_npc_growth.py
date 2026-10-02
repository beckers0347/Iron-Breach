"""
IBPY: ib_diagnose_npc_growth.py

Diagnoses why NPC_* placeholder actors grow huge / lie down when PIE starts.

Suspected cause: the NPCs wear the Ms_Idris_wSkeleton mesh, but
ABP_NPC_Locomotion and its Loco_* animations were built for
Base_Character_Mesh_Skeleton (the JumpSuit skeleton). Different skeleton =
the animation drives the wrong bones / a root bone with scale or rotation.

What it does (read-only unless APPLY_SAFE_FIX is True):
  1. Compares each NPC mesh's skeleton with the ABP's target skeleton.
  2. Compares mesh bounds (size) of the NPC mesh vs the JumpSuit mesh.
  3. Compares bone names between the two skeletons.
  4. Samples the root-bone pose of Loco_Idle/Walking/Running at t=0.
  5. Logs each NPC actor's anim mode / anim class / scale.
  6. APPLY_SAFE_FIX=True: on mismatched NPCs, removes the ABP so they stay in
     their normal reference pose in PIE (no growth). Rescales nothing.

What it CANNOT do: edit ABP_NPC_Locomotion's EventGraph nodes (Unreal's
Python API doesn't expose Blueprint graph editing). The Set Speed fix
(Get Owning Actor -> Is Valid -> Get Velocity -> Vector Length -> Set Speed)
has to be wired by hand.

HOW TO RUN (editor open, NOT in PIE):
    py "X:/IronBreach/Scripts/ib_diagnose_npc_growth.py"
Paste back the full output (filter the Output Log by "IBPY").
"""

import unreal

# ----------------------------- CONFIG --------------------------------------
APPLY_SAFE_FIX = False   # set True to strip the mismatched ABP from NPCs

ABP_PATH = "/Game/Characters/NPCs/Shared/ABP_NPC_Locomotion"
ABP_CLASS_PATH = ABP_PATH  # load_blueprint_class takes the same path
REFERENCE_MESH_PATH = "/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh"
IDRIS_MESH_PATH = "/Game/Characters/NPCs/MsIdris/Ms_Idris_Infantry"
ANIM_PATHS = [
    "/Game/Characters/Infantry/Animations/Locomotion_Unarmed/Loco_Idle",
    "/Game/Characters/Infantry/Animations/Locomotion_Unarmed/Loco_Walking",
    "/Game/Characters/Infantry/Animations/Locomotion_Unarmed/Loco_Running",
]
NPC_PREFIX = "NPC_"
# ---------------------------------------------------------------------------


def log(msg):
    unreal.log(f"IBPY: {msg}")


def warn(msg):
    unreal.log_warning(f"IBPY: {msg}")


def err(msg):
    unreal.log_error(f"IBPY: {msg}")


def name_of(obj):
    return obj.get_path_name() if obj else "None"


def safe_prop(obj, prop, default=None):
    try:
        return obj.get_editor_property(prop)
    except Exception as ex:
        warn(f"  could not read '{prop}': {ex}")
        return default


def mesh_extent(mesh):
    try:
        b = mesh.get_bounds()
        e = b.box_extent
        return (e.x, e.y, e.z)
    except Exception as ex:
        warn(f"  could not read bounds: {ex}")
        return None


def bone_names_for_mesh(mesh):
    """Spawn a throwaway SkeletalMeshActor to read bone names, then delete it."""
    names = []
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    tmp = None
    try:
        tmp = actor_subsystem.spawn_actor_from_class(
            unreal.SkeletalMeshActor, unreal.Vector(0, 0, -100000))
        comp = tmp.skeletal_mesh_component
        comp.set_skinned_asset_and_update(mesh)
        for i in range(comp.get_num_bones()):
            names.append(str(comp.get_bone_name(i)))
    except Exception as ex:
        warn(f"  could not read bone names: {ex}")
    finally:
        if tmp is not None:
            actor_subsystem.destroy_actor(tmp)
    return names


def sample_root_pose(anim, bone_name):
    """Try the known Python entry points for reading a bone pose from a sequence."""
    for lib_name in ("AnimationLibrary", "AnimPoseExtensions"):
        lib = getattr(unreal, lib_name, None)
        if lib is None:
            continue
        fn = getattr(lib, "get_bone_pose_for_time", None)
        if fn is None:
            continue
        try:
            return fn(anim, bone_name, 0.0, False)
        except Exception:
            continue
    return None


def step1_abp():
    log("---- STEP 1: ABP target skeleton ----")
    abp = unreal.load_asset(ABP_PATH)
    if abp is None:
        err(f"could not load {ABP_PATH}")
        return None
    skel = None
    try:
        skel = abp.get_editor_property("target_skeleton")
    except Exception as ex:
        warn(f"could not read target_skeleton: {ex}")
    log(f"ABP target skeleton: {name_of(skel)}")
    return skel


def step2_reference_mesh():
    log("---- STEP 2: reference (JumpSuit) mesh ----")
    mesh = unreal.load_asset(REFERENCE_MESH_PATH)
    if mesh is None:
        err(f"could not load {REFERENCE_MESH_PATH}")
        return None, [], None
    ext = mesh_extent(mesh)
    bones = bone_names_for_mesh(mesh)
    log(f"JumpSuit mesh skeleton: {name_of(mesh.skeleton)}")
    log(f"JumpSuit bounds extent (cm): {ext}")
    log(f"JumpSuit bone count: {len(bones)}; first 5: {bones[:5]}")
    return mesh, bones, ext


def step3_anims(abp_skel):
    log("---- STEP 3: locomotion animation assets ----")
    for p in ANIM_PATHS:
        anim = unreal.load_asset(p)
        if anim is None:
            warn(f"  could not load {p}")
            continue
        skel = None
        try:
            skel = anim.get_editor_property("skeleton")
        except Exception:
            pass
        same = (skel == abp_skel) if (skel and abp_skel) else None
        log(f"  {anim.get_name()}: skeleton={name_of(skel)} matches ABP skeleton={same}")
        pose = None
        for bn in ("Hips", "root", "Root"):  # JumpSuit skeleton's top bone is Hips
            pose = sample_root_pose(anim, bn)
            if pose is not None:
                log(f"    sampled bone '{bn}'")
                break
        if pose is not None:
            r = pose.rotation.rotator()
            s = pose.scale3d
            log(f"    root pose @t=0: scale=({s.x:.3f},{s.y:.3f},{s.z:.3f}) "
                f"rot(P,Y,R)=({r.pitch:.1f},{r.yaw:.1f},{r.roll:.1f})")
            if max(abs(s.x), abs(s.y), abs(s.z)) > 2.0 or min(abs(s.x), abs(s.y), abs(s.z)) < 0.5:
                warn("    ^ root scale is far from 1.0 -- candidate for the growth")
        else:
            log("    (root pose not readable via Python; open the asset and check the root track by hand)")


def step4_npcs(abp_skel, ref_bones, ref_ext, anim_class):
    log("---- STEP 4: NPC actors in the level ----")
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mismatched = []
    found = 0
    for a in actor_subsystem.get_all_level_actors():
        label = a.get_actor_label()
        if not label.startswith(NPC_PREFIX) or not isinstance(a, unreal.SkeletalMeshActor):
            continue
        found += 1
        comp = a.skeletal_mesh_component
        mesh = comp.get_editor_property("skeletal_mesh_asset") \
            if hasattr(comp, "skeletal_mesh_asset") else comp.skeletal_mesh
        skel = mesh.skeleton if mesh else None
        sc = a.get_actor_scale3d()
        csc = safe_prop(comp, "relative_scale3d", unreal.Vector(1, 1, 1))
        log(f"'{label}':")
        log(f"  mesh={name_of(mesh)}")
        log(f"  mesh skeleton={name_of(skel)}")
        log(f"  actor scale=({sc.x},{sc.y},{sc.z}) component scale=({csc.x},{csc.y},{csc.z})")
        try:
            mode = comp.get_animation_mode()
        except Exception as ex:
            mode = f"<unreadable: {ex}>"
        try:
            acls = name_of(comp.get_editor_property("anim_class"))
        except Exception as ex:
            acls = f"<unreadable: {ex}>"
        log(f"  anim mode={mode} anim class={acls}")
        ext = mesh_extent(mesh) if mesh else None
        log(f"  mesh bounds extent (cm)={ext}")
        if skel is not None and abp_skel is not None and skel != abp_skel:
            warn(f"  MISMATCH: mesh skeleton != ABP skeleton. This is the likely growth cause.")
            mismatched.append((a, mesh))
        elif skel == abp_skel:
            log("  skeleton matches ABP skeleton (not the cause for this actor)")
    log(f"NPC actors found: {found}; mismatched: {len(mismatched)}")

    if mismatched:
        npc_bones = bone_names_for_mesh(mismatched[0][1])
        shared = set(npc_bones) & set(ref_bones)
        log(f"Bone compare: NPC mesh has {len(npc_bones)} bones, JumpSuit has "
            f"{len(ref_bones)}, shared names: {len(shared)}")
        log(f"  NPC first 8 bones: {npc_bones[:8]}")
        if ref_ext and mismatched[0][1]:
            n_ext = mesh_extent(mismatched[0][1])
            if n_ext and ref_ext[2]:
                log(f"  height ratio NPC/JumpSuit (Z extent): {n_ext[2] / ref_ext[2]:.3f}")
    return mismatched


def step5_fix(mismatched):
    log("---- STEP 5: safe fix ----")
    if not mismatched:
        log("nothing to fix.")
        return
    if not APPLY_SAFE_FIX:
        log("APPLY_SAFE_FIX is False -> no changes made. Set it to True and re-run to "
            "strip the ABP from the mismatched NPCs.")
        return
    for a, _ in mismatched:
        comp = a.skeletal_mesh_component
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        comp.set_animation(None)
        log(f"  '{a.get_actor_label()}': ABP removed, back to reference pose.")
    log("Save the level, then hit Play. NPCs should stay normal size. "
        "Real fix: build/retarget animations for the Ms_Idris skeleton "
        "(IK Retargeter from Base_Character_Mesh_Skeleton), then re-run "
        "ib_assign_npc_animbp.py with an ABP that targets it.")


def hips_ref_pose(mesh, bone="Hips"):
    """Reference-pose transform of a bone (component space) via a throwaway actor."""
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    tmp = None
    try:
        tmp = actor_subsystem.spawn_actor_from_class(
            unreal.SkeletalMeshActor, unreal.Vector(0, 0, -100000))
        comp = tmp.skeletal_mesh_component
        comp.set_skinned_asset_and_update(mesh)
        return comp.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_COMPONENT)
    except Exception as ex:
        warn(f"  could not read ref pose of '{bone}': {ex}")
        return None
    finally:
        if tmp is not None:
            actor_subsystem.destroy_actor(tmp)


def fmt_xform(t):
    if t is None:
        return "n/a"
    r = t.rotation.rotator()
    s = t.scale3d
    l = t.translation
    return (f"loc=({l.x:.1f},{l.y:.1f},{l.z:.1f}) rot(P,Y,R)=({r.pitch:.1f},{r.yaw:.1f},{r.roll:.1f}) "
            f"scale=({s.x:.3f},{s.y:.3f},{s.z:.3f})")


def step6_hips_compare():
    log("---- STEP 6: Hips reference pose, JumpSuit mesh vs Idris mesh vs animation ----")
    jump = unreal.load_asset(REFERENCE_MESH_PATH)
    idris = unreal.load_asset(IDRIS_MESH_PATH)
    for label, m in (("JumpSuit mesh", jump), ("Idris mesh", idris)):
        if m is None:
            warn(f"  could not load {label}")
            continue
        log(f"  {label} Hips ref pose: {fmt_xform(hips_ref_pose(m))}")
        log(f"  {label} Spine ref pose: {fmt_xform(hips_ref_pose(m, 'Spine'))}")
    anim = unreal.load_asset(ANIM_PATHS[0])
    if anim is not None:
        log(f"  Loco_Idle Hips track @t=0: {fmt_xform(sample_root_pose(anim, 'Hips'))}")
    log("  READ: if JumpSuit ref Hips ~ the animation's Hips (scale 1000, ~90 roll) and "
        "Idris ref Hips is different (scale 1, rot 0), the Idris mesh has a different "
        "bind pose than the animations expect -> re-import/fix the Idris mesh's Hips.")


def main():
    log("==== NPC GROWTH DIAGNOSTIC ====")
    abp_skel = step1_abp()
    _, ref_bones, ref_ext = step2_reference_mesh()
    step3_anims(abp_skel)
    anim_class = unreal.EditorAssetLibrary.load_blueprint_class(ABP_CLASS_PATH)
    mismatched = step4_npcs(abp_skel, ref_bones, ref_ext, anim_class)
    step5_fix(mismatched)
    step6_hips_compare()
    log("==== DONE. Paste the IBPY lines back. ====")


main()
