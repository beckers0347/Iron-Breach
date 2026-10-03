import unreal, json, traceback
LEVEL = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3"
out = []
try:
    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        c = a.get_class().get_name(); l = a.get_actor_label()
        key = any(k in (c + l).lower() for k in ("npc", "director", "idris", "rhodes", "bricks", "static", "okafor", "yun", "squad", "temp_", "dialog", "guide"))
        if not key: continue
        row = dict(label=l, cls=c, loc=[round(v) for v in a.get_actor_location().to_tuple()], rot=[round(v) for v in a.get_actor_rotation().to_tuple()],
                   scale=[round(v, 2) for v in a.get_actor_scale3d().to_tuple()], folder=str(a.get_folder_path()))
        try:
            sk = a.get_component_by_class(unreal.SkeletalMeshComponent)
            if sk:
                row["skmesh"] = sk.skeletal_mesh.get_path_name() if sk.skeletal_mesh else None
                row["anim_mode"] = str(sk.get_editor_property("animation_mode"))
                ac = sk.get_editor_property("anim_class")
                row["anim_class"] = ac.get_path_name() if ac else None
                row["bounds"] = [round(v) for v in a.get_actor_bounds(False)[1].to_tuple()]
        except Exception as e:
            row["err"] = repr(e)
        out.append(row)
except BaseException:
    out.append({"ERR": traceback.format_exc()})
json.dump(out, open("X:/IronBreach/Saved/campaign_npcs.json", "w"), indent=1)
open("X:/IronBreach/Saved/campaign_npcs_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
