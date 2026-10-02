"""
IBPY: ib_find_barracks.py -- read-only unless FIX = True.
Lists every Barracks-related actor in the open level (new IB_Barracks02 building, sensor doors,
old parked Tripo Barracks): location, hidden flags, folder.
FIX = True un-hides the new building + doors and re-enables collision.
Run:  py "X:/IronBreach/Scripts/ib_find_barracks.py"
"""
import unreal

FIX = False

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
unreal.log("IBPY: ib_find_barracks v1 level=" + unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_name())

hits = []
for a in eas.get_all_level_actors():
    try:
        tags = [str(t) for t in a.tags]
        blob = (a.get_name() + " " + a.get_actor_label() + " " + " ".join(tags) + " " + str(a.get_folder_path())).lower()
    except Exception:
        continue
    if "barrack" in blob or "sensordoor" in blob:
        hits.append(a)

unreal.log("IBPY: found %d barracks-related actor(s)" % len(hits))
for a in hits:
    loc = a.get_actor_location()
    try:
        hg = a.get_editor_property("hidden")
    except Exception:
        hg = "?"
    unreal.log("IBPY:  %s [%s] loc=(%.0f,%.0f,%.0f) hidden_ed=%s hidden_game=%s folder=%s tags=%s" % (
        a.get_actor_label(), a.get_class().get_name(), loc.x, loc.y, loc.z,
        a.is_temporarily_hidden_in_editor(), hg, a.get_folder_path(), [str(t) for t in a.tags]))
    if FIX and "IB_Barracks02" in [str(t) for t in a.tags]:
        a.set_is_temporarily_hidden_in_editor(False)
        a.set_actor_hidden_in_game(False)
        a.set_actor_enable_collision(True)
        unreal.log("IBPY:    -> unhidden + collision on")
