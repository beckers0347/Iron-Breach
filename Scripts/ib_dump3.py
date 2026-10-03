import unreal, collections
unreal.EditorLoadingAndSavingUtils.load_map("/Game/IronBreach/Thornfield/Levels/L_ThornfieldGarrison")
P = lambda s: unreal.log("TFDUMP " + s)
d = collections.defaultdict(lambda: [0, set(), None])
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    l = a.get_actor_label()
    k = ''.join(ch for ch in l if not ch.isdigit()).rstrip('_')
    k = k.split('_')[0] if k.startswith(("ROAD","GRASS","TREE","FILLTREE","LIGHT","ROCK","SEAMROCK","MOUNTAIN","CLIFF","WP")) else k
    e = d[k]; e[0] += 1
    if a.get_class().get_name() == "StaticMeshActor":
        c = a.static_mesh_component
        m = c.static_mesh
        if m: e[1].add(m.get_name())
        if e[2] is None:
            e[2] = (a.get_actor_location(), a.get_actor_scale3d(), [x.get_name() if x else None for x in c.get_materials()][:3], m.get_bounds().box_extent if m else None)
for k, (n, ms, s) in sorted(d.items(), key=lambda kv: -kv[1][0]):
    P("%s n=%d meshes=%s sample=%s" % (k, n, sorted(ms)[:4], s))
open("X:/IronBreach/Saved/tf_dump_done.txt","w").write("ok")
unreal.SystemLibrary.quit_editor()
