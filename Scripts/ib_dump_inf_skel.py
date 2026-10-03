import unreal, json
sk = unreal.load_asset("/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton")
pose = unreal.AnimPoseExtensions.get_reference_pose(sk)
names = unreal.AnimPoseExtensions.get_bone_names(pose)
out = []
for n in names:
    w = unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD)
    l = unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.LOCAL)
    t, q = w.translation, w.rotation
    lt, lq = l.translation, l.rotation
    out.append(dict(name=str(n), world_t=[t.x, t.y, t.z], world_q=[q.x, q.y, q.z, q.w], local_t=[lt.x, lt.y, lt.z], local_q=[lq.x, lq.y, lq.z, lq.w],
                    parent=str(sk.get_reference_skeleton().get_parent_index(sk.get_reference_skeleton().find_bone_index(n))) if False else None))
json.dump(out, open("X:/IronBreach/Saved/inf_skel.json", "w"), indent=1)
unreal.log("INFSKEL bones=%d" % len(out))
open("X:/IronBreach/Saved/infskel_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
