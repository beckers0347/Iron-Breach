"""
IBPY: ib_dump_npcs.py -- read-only. Lists every NPC-ish SkeletalMeshActor and the guide route's
references so we can see why placeholders are duplicated / facing the wrong way.
Run: py "X:/IronBreach/Scripts/ib_dump_npcs.py"
"""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.log("IBPY: ib_dump_npcs v2")
for a in eas.get_all_level_actors():
    if not isinstance(a, unreal.SkeletalMeshActor):
        continue
    c = a.skeletal_mesh_component
    loc = a.get_actor_location(); rot = a.get_actor_rotation()
    rr = c.get_editor_property("relative_rotation"); rl = c.get_editor_property("relative_location")
    try:
        mesh = c.get_editor_property("skinned_asset").get_name()
    except Exception:
        mesh = "?"
    unreal.log("IBPY: %s / %s loc=(%.0f,%.0f,%.0f) actorRot=(p%.0f,y%.0f,r%.0f) compRelRot=(p%.0f,y%.0f,r%.0f) compRelLoc=(%.0f,%.0f,%.0f) hidden_game=%s tags=%s mesh=%s" % (
        a.get_name(), a.get_actor_label(), loc.x, loc.y, loc.z, rot.pitch, rot.yaw, rot.roll,
        rr.pitch, rr.yaw, rr.roll, rl.x, rl.y, rl.z, a.get_editor_property("hidden"), [str(t) for t in a.tags], mesh))
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "M1_GuideRoute":
        g = a.get_editor_property("guide_actor"); f = a.get_editor_property("followers")
        unreal.log("IBPY: route guide=%s followers=%s facing_yaw_offset=%s" % (
            g.get_path_name() if g else None, [x.get_path_name() if x else None for x in f], a.get_editor_property("facing_yaw_offset")))
