import unreal
for n in ("IKRigController", "IKRetargeterController", "IKRetargetBatchOperation", "IKRigDefinition", "IKRetargeter", "IKRigSkeletalMeshController", "IKRigFKChainsController" ):
    unreal.log("RTAPI %s %s" % (n, hasattr(unreal, n)))
for n in dir(unreal):
    if "IKRetarget" in n or "IKRigDef" in n or "IKRigController" in n: unreal.log("RTAPI name " + n)
m = unreal.load_asset("/Game/Characters/NPCs/MsIdris/Ms_Idris_Fixed")
unreal.log("RTAPI fixed bounds %s skel %s" % (m.get_bounds().box_extent, m.skeleton.get_path_name()))
pose = unreal.AnimPoseExtensions.get_reference_pose(m.skeleton)
unreal.log("RTAPI fixed bones: %s" % [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(pose)][:12])
open("X:/IronBreach/Saved/rt_done.txt","w").write("ok")
unreal.SystemLibrary.quit_editor()
