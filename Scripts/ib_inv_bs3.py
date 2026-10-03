"""Read-only inventory of the Carrowgate garrison buildings in BoulderShore3. Saves nothing."""
import unreal, json, collections
LEVEL = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3"
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
rows = []
folders = collections.Counter()
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    f = str(a.get_folder_path())
    folders[f] += 1
    if not f.startswith("Carrowgate Garrison") or "Rock" in f or "Boulder" in f:
        continue
    o, e = a.get_actor_bounds(False)
    mesh = None
    try:
        mesh = a.static_mesh_component.static_mesh.get_path_name()
    except Exception:
        pass
    r = a.get_actor_rotation()
    rows.append(dict(label=a.get_actor_label(), cls=a.get_class().get_name(), folder=f, mesh=mesh,
                     loc=[round(o.x), round(o.y), round(o.z)], ext=[round(e.x), round(e.y), round(e.z)],
                     yaw=round(r.yaw, 1), tags=[str(t) for t in a.tags]))
json.dump({"folders": folders, "rows": rows}, open("X:/IronBreach/Saved/bs3_inventory.json", "w"), indent=1)
unreal.log("BS3INV rows=%d" % len(rows))
open("X:/IronBreach/Saved/bs3_inv_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
