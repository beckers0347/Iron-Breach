"""
IBPY: ib_reimport_loco_anims.py

ROOT CAUSE of NPCs (and any actor using ABP_NPC_Locomotion) growing to ~900 m
in PIE: the Loco_* animations were imported with Import Uniform Scale = 1000
(Hips track measured at scale 1000, Z ~55,424). The JumpSuit mesh was imported
at 1.8 and the Idris mesh at 1.7, and the animation overwrites the Hips
transform, so the whole skeleton is inflated ~555x.

FIX: re-import the animations from their Mixamo FBX sources with Import
Uniform Scale = 1.8 (matches Base_Character_Mesh's 1.8), bound to the Infantry
skeleton, replacing the existing assets in place (same paths, so
BS_NPC_Unarmed_Locomotion / ABP references stay intact).

STEP-BY-STEP (default): only Loco_Idle is re-imported, then its Hips track is
sampled to verify the scale. If it reads ~1.8, set ONLY_IDLE_FIRST = False and
re-run to do the other 11 (or just the 3 NPC ones, see NPC_THREE_ONLY).

Backup of the original .uasset files:
  X:/IronBreach/Claude outputs/backup_Loco_Unarmed_2026-10-02/

HOW TO RUN (editor open, NOT in PIE):
    py "X:/IronBreach/Scripts/ib_reimport_loco_anims.py"
Paste back the IBPY lines.
"""

import os
import unreal

# ----------------------------- CONFIG --------------------------------------
IMPORT_SCALE = 1.8
ONLY_IDLE_FIRST = False     # True: just Loco_Idle. False: do the rest too.
NPC_THREE_ONLY = False      # when ONLY_IDLE_FIRST is False: True = Idle/Walking/Running only

SOURCE_DIR = r"X:\Downloads\Jump+Suit\Animations\Locomotion_Unarmed"
DEST_PATH = "/Game/Characters/Infantry/Animations/Locomotion_Unarmed"
SKELETON_PATH = "/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton"

ALL_ANIMS = [
    "Loco_Idle", "Loco_Walking", "Loco_Running", "Loco_Jump",
    "Loco_Left_Strafe", "Loco_Left_Strafe_Walking",
    "Loco_Right_Strafe", "Loco_Right_Strafe_Walking",
    "Loco_Left_Turn", "Loco_Left_Turn_90",
    "Loco_Right_Turn", "Loco_Right_Turn_90",
]
NPC_THREE = ["Loco_Idle", "Loco_Walking", "Loco_Running"]
# ---------------------------------------------------------------------------


def log(msg):
    unreal.log(f"IBPY: {msg}")


def hips_pose(anim):
    for lib_name in ("AnimationLibrary", "AnimPoseExtensions"):
        lib = getattr(unreal, lib_name, None)
        fn = getattr(lib, "get_bone_pose_for_time", None) if lib else None
        if fn is None:
            continue
        try:
            return fn(anim, "Hips", 0.0, False)
        except Exception:
            continue
    return None


def verify(name):
    anim = unreal.load_asset(f"{DEST_PATH}/{name}")
    if anim is None:
        log(f"  VERIFY: could not load {name}")
        return False
    pose = hips_pose(anim)
    if pose is None:
        log(f"  VERIFY: could not read Hips pose for {name}; check it by hand.")
        return False
    s = pose.scale3d
    l = pose.translation
    log(f"  VERIFY {name}: Hips scale=({s.x:.3f},{s.y:.3f},{s.z:.3f}) "
        f"loc=({l.x:.1f},{l.y:.1f},{l.z:.1f})")
    ok = abs(s.x - IMPORT_SCALE) < 0.5
    log("  -> scale looks right." if ok else
        "  -> scale is STILL wrong; the import options were probably ignored "
        "(Interchange). Fall back to the manual reimport described at the bottom.")
    return ok


def import_one(name, skeleton):
    src = os.path.join(SOURCE_DIR, f"{name}.fbx")
    if not os.path.isfile(src):
        log(f"  ERROR: source not found: {src}")
        return False
    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = DEST_PATH
    task.destination_name = name
    task.automated = True
    task.save = True
    task.replace_existing = True

    opts = unreal.FbxImportUI()
    opts.import_mesh = False
    opts.import_as_skeletal = True
    opts.import_animations = True
    opts.import_materials = False
    opts.import_textures = False
    opts.create_physics_asset = False
    opts.automated_import_should_detect_type = False
    opts.mesh_type_to_import = unreal.FBXImportType.FBXIT_ANIMATION
    opts.skeleton = skeleton
    opts.anim_sequence_import_data.set_editor_property("import_uniform_scale", IMPORT_SCALE)
    task.options = opts

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths"))
    if not imported:
        log(f"  ERROR: import of {name} produced no assets (see log above).")
        return False
    log(f"  imported: {imported[0]}")
    return True


def main():
    log("==== REIMPORT Loco_* ANIMATIONS @ scale %.2f ====" % IMPORT_SCALE)
    skeleton = unreal.load_asset(SKELETON_PATH)
    if skeleton is None:
        log(f"ERROR: could not load skeleton {SKELETON_PATH}")
        return

    if ONLY_IDLE_FIRST:
        names = ["Loco_Idle"]
    elif NPC_THREE_ONLY:
        names = NPC_THREE
    else:
        names = ALL_ANIMS
    log(f"animations to reimport: {names}")

    good = 0
    for n in names:
        log(f"---- {n} ----")
        if import_one(n, skeleton) and verify(n):
            good += 1
    log(f"==== DONE. {good}/{len(names)} verified. ====")
    if ONLY_IDLE_FIRST:
        log("If Loco_Idle verified (scale ~1.8): set ONLY_IDLE_FIRST=False and re-run, "
            "then press Play and check the NPCs/test actor.")
    log("Manual fallback if options are ignored: Content Browser -> right-click Loco_Idle -> "
        "Reimport With New File -> in the Interchange dialog set Import Uniform Scale to 1.8.")


main()
