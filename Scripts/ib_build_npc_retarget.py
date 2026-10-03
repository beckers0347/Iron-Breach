"""
IBPY: ib_build_npc_retarget.py

Builds every campaign NPC on its OWN skeleton (from the *wSkeleton.fbx files in Downloads\\NPCs) and bakes the
Infantry locomotion (idle / walk / run) onto each one with an IK Retargeter.

Why the first attempt produced frozen animations: UE 5.8's retargeter runs an OP STACK (pelvis motion, FK chains,
IK, ...). A retargeter created from Python has an empty stack, so nothing was transferred and every baked clip was
just the rest pose. This version calls add_default_ops(), assigns the target rig to the ops, maps the chains and
auto-aligns the bind poses (T-pose vs the Infantry A-pose), then verifies the baked clips actually move.

Safe to re-run. Output: /Game/Characters/NPCs/<Name>/SK_<Name> + Retargeted/Loco_*_<Name>.
"""
import traceback
import unreal

DL = "X:/Downloads/NPCs/"
CHARACTERS = {
    # name: (fbx, target height cm)
    "Idris":   ("MsIdris_Source/Ms_Idris_wSkeleton.fbx", 160.0),
    "Rhodes":  ("Lt.+Imani+Rhodes/Lt._Imani_Rhodes wSkeleton.fbx", 172.0),
    "Bricks":  ("Sgt.+Adaeze+Okafor+aka.+Bricks/Sgt._Adaeze_Okafor_aka.Bricks wSkeleton.fbx", 175.0),
    "Static":  ("Spc.+Theo+Yun+aka.+Static/Spc._Theo_Yun_aka.Static wSkeleton.fbx", 170.0),
}
RIG_DIR = "/Game/Characters/NPCs/Shared/Retarget"
# The meshes keep the Mannequin's facing (+Y): rotating them +X made the foot chains retarget 90 degrees off
# (twisted bodies). Fresh asset names (SKN_) so no stale skeleton/import settings are reused.
MESH_PREFIX = "SKN_"
RIG_TAG = "3"       # fresh IK rigs / retargeters bound to the new meshes
# The Infantry (JumpSuit) skeleton is unusable as a retarget source (ref pose scaled 100x, animations compensate),
# so the clips come from the standard UE5 Mannequin instead: sane skeleton, standard A-pose.
INF_MESH = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
ANIM_DIR = "/Game/Characters/Mannequins/Anims/Unarmed"
ANIMS = {"MM_Idle": "Loco_Idle", "Walk/MF_Unarmed_Walk_Fwd": "Loco_Walking"}
SRC_CHAINS = [("Spine", "spine_01", "spine_05"), ("Neck", "neck_01", "neck_02"), ("Head", "head", "head"),
              ("LeftArm", "clavicle_l", "hand_l"), ("RightArm", "clavicle_r", "hand_r"),
              ("LeftLeg", "thigh_l", "ball_l"), ("RightLeg", "thigh_r", "ball_r")]
SRC_ROOT = "pelvis"
CHAINS = [("Spine", "Spine", "Spine2"), ("Neck", "Neck", "Neck"), ("Head", "Head", "HeadTop_End"),
          ("LeftArm", "LeftShoulder", "LeftHand"), ("RightArm", "RightShoulder", "RightHand"),
          ("LeftLeg", "LeftUpLeg", "LeftToeBase"), ("RightLeg", "RightUpLeg", "RightToeBase")]
AT = unreal.AssetToolsHelpers.get_asset_tools()
FAILED = []


def log(m):
    unreal.log("IBPY: " + m)


def step(label, fn):
    try:
        r = fn()
        log("OK   " + label)
        return r
    except Exception:
        FAILED.append(label)
        unreal.log_error("IBPY: FAIL " + label + "\n" + traceback.format_exc())
        return None


def import_mesh(name, fbx, scale):
    dest = "/Game/Characters/NPCs/" + name
    t = unreal.AssetImportTask()
    t.filename = DL + fbx
    t.destination_path = dest
    t.destination_name = MESH_PREFIX + name
    t.automated = True
    t.save = True
    t.replace_existing = True
    o = unreal.FbxImportUI()
    o.import_mesh = True
    o.import_as_skeletal = True
    o.import_animations = False
    o.import_materials = True
    o.import_textures = True
    o.create_physics_asset = False
    d = o.skeletal_mesh_import_data
    d.set_editor_property("import_uniform_scale", scale)
    d.set_editor_property("import_rotation", unreal.Rotator(roll=-90, pitch=0, yaw=0))
    t.options = o
    AT.import_asset_tasks([t])
    m = unreal.load_asset("%s/%s%s" % (dest, MESH_PREFIX, name))
    b = m.get_bounds()
    log("  " + MESH_PREFIX + "%s: height %.0f cm, extent %s, skeleton %s" % (name, b.box_extent.z * 2, b.box_extent, m.skeleton.get_name()))
    return m


def height_of(name, fbx):
    """Import at scale 1 to measure, so the final scale gives the target height."""
    return import_mesh(name, fbx, 1.0).get_bounds().box_extent.z * 2


def get_or_make(name, factory, cls):
    path = "%s/%s" % (RIG_DIR, name)
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    return AT.create_asset(name, RIG_DIR, cls, factory)


def make_rig(name, mesh, chains=None, root="Hips"):
    rig = get_or_make(name, unreal.IKRigDefinitionFactory(), unreal.IKRigDefinition)
    c = unreal.IKRigController.get_controller(rig)
    c.set_skeletal_mesh(mesh)
    c.set_retarget_root(root)
    for ch in list(c.get_retarget_chains()):
        c.remove_retarget_chain(ch.get_editor_property("chain_name"))
    for n, s, e in (chains or CHAINS):
        c.add_retarget_chain(unreal.Name(n), unreal.Name(s), unreal.Name(e), unreal.Name(""))
    unreal.EditorAssetLibrary.save_loaded_asset(rig)
    return rig


def make_retargeter(name, src_rig, dst_rig):
    rt = get_or_make(name, unreal.IKRetargetFactory(), unreal.IKRetargeter)
    c = unreal.IKRetargeterController.get_controller(rt)
    c.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig)
    c.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, dst_rig)
    n0 = c.get_num_retarget_ops()
    if n0 == 0:
        c.add_default_ops()
    c.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig)
    c.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, dst_rig)
    log("  retarget ops in stack: %d (was %d): %s" % (c.get_num_retarget_ops(), n0, [str(c.get_op_name(i)) for i in range(c.get_num_retarget_ops())]))
    # The guide route moves the body, so the clip must not carry the Mannequin's root travel: switch that op off.
    for i in range(c.get_num_retarget_ops()):
        if str(c.get_op_name(i)) == "Root Motion":
            c.set_retarget_op_enabled(i, False)
            log("  Root Motion op disabled (enabled now: %s)" % c.get_retarget_op_enabled(i))
    c.auto_map_chains(unreal.AutoMapChainType.EXACT, True)
    for side in (unreal.RetargetSourceOrTarget.SOURCE, unreal.RetargetSourceOrTarget.TARGET):
        try:
            c.auto_align_all_bones(side)
        except Exception as e:
            log("  align %s: %r" % (side, e))
    unreal.EditorAssetLibrary.save_loaded_asset(rt)
    return rt


def bake(name, rt, src_mesh, dst_mesh):
    out_dir = "/Game/Characters/NPCs/%s/Retargeted" % name
    anims = [unreal.EditorAssetLibrary.find_asset_data("%s/%s" % (ANIM_DIR, a)) for a in ANIMS]
    inp = unreal.IKRetargetBatchOperationInputs()
    inp.set_editor_property("assets_to_retarget", anims)
    inp.set_editor_property("source_mesh", src_mesh)
    inp.set_editor_property("target_mesh", dst_mesh)
    inp.set_editor_property("ik_retarget_asset", rt)
    inp.set_editor_property("suffix", "_" + name)
    inp.set_editor_property("use_source_path", False)
    inp.set_editor_property("target_path", out_dir)
    inp.set_editor_property("overwrite_existing_files", True)
    inp.set_editor_property("include_referenced_assets", False)
    res = unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
    for a, friendly in ANIMS.items():
        base = a.split("/")[-1]
        src_path = "%s/%s_%s" % (out_dir, base, name)
        dst_path = "%s/%s_%s" % (out_dir, friendly, name)
        if unreal.EditorAssetLibrary.does_asset_exist(dst_path):
            unreal.EditorAssetLibrary.delete_asset(dst_path)
        if unreal.EditorAssetLibrary.does_asset_exist(src_path):
            unreal.EditorAssetLibrary.rename_asset(src_path, dst_path)
        clip = unreal.load_asset(dst_path)
        if clip:
            # Hips IS the root bone here: root lock would pin the pelvis to the origin and flatten the body.
            clip.set_editor_property("force_root_lock", False)
            clip.set_editor_property("enable_root_motion", False)
            unreal.EditorAssetLibrary.save_loaded_asset(clip)
    unreal.EditorAssetLibrary.save_directory(out_dir, True, True)
    return res


def verify(name):
    opts = unreal.AnimPoseEvaluationOptions()
    ok = True
    for n in ("Loco_Idle_" + name, "Loco_Walking_" + name):
        a = unreal.load_asset("/Game/Characters/NPCs/%s/Retargeted/%s" % (name, n))
        L = a.get_editor_property("sequence_length")
        pts = []
        for t in (0.0, L * 0.25, L * 0.5, L * 0.75):
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, t, opts)
            f = unreal.AnimPoseExtensions.get_bone_pose(pose, "LeftFoot", unreal.AnimPoseSpaces.WORLD).translation
            h = unreal.AnimPoseExtensions.get_bone_pose(pose, "RightHand", unreal.AnimPoseSpaces.WORLD).translation
            pts.append((f.x, f.y, f.z, h.x, h.y, h.z))
        spread = max(max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(6))
        log("  verify %s: motion spread %.1f cm %s" % (n, spread, "MOVES" if spread > 1.0 else "FROZEN"))
        ok = ok and spread > 1.0
    return ok


def main():
    log("=== ib_build_npc_retarget ===")
    src = unreal.load_asset(INF_MESH)
    src_rig = step("source IK rig (Mannequin)", lambda: make_rig("IK_Manny", src, SRC_CHAINS, SRC_ROOT))
    for name, (fbx, target_h) in CHARACTERS.items():
        log("---- %s ----" % name)
        raw_h = step("%s: measure" % name, lambda: height_of(name, fbx))
        if not raw_h:
            continue
        scale = target_h / raw_h
        log("  raw height %.1f cm -> scale %.3f for %.0f cm" % (raw_h, scale, target_h))
        dst = step("%s: import" % name, lambda: import_mesh(name, fbx, scale))
        if not dst:
            continue
        dst_rig = step("%s: IK rig" % name, lambda: make_rig("IK%s_%s" % (RIG_TAG, name), dst))
        rt = step("%s: retargeter" % name, lambda: make_retargeter("RTG%s_Infantry_to_%s" % (RIG_TAG, name), src_rig, dst_rig))
        if rt:
            step("%s: bake" % name, lambda: bake(name, rt, src, dst))
            if not verify(name):
                FAILED.append(name + ": animation is frozen")
    log("=== done. failures: %s ===" % (FAILED or "none"))


main()
