"""
IBPY: ib_restore_squad_hide_act5.py
 1) Re-runs ib_place_m1_squad.py (the Act I squad had snapped back to the default
    (300/600/900, 0) spots, and Idris was visible again).
 2) Hides the three *_ACT5 muster NPCs in game, so the medical muster isn't pre-populated with
    extra placeholders while the guide squad walks there. (Unhide later: set HIDE = False.)
Then SAVE THE LEVEL (Ctrl+S) -- unsaved placement is what got lost in the crash.
Run: py "X:/IronBreach/Scripts/ib_restore_squad_hide_act5.py"
"""
import unreal
HIDE = True

exec(compile(open("X:/IronBreach/Scripts/ib_place_m1_squad.py", encoding="utf-8").read(),
             "ib_place_m1_squad.py", "exec"))

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label().endswith("_ACT5"):
        a.set_actor_hidden_in_game(HIDE)
        unreal.log("IBPY: %s hidden_in_game=%s" % (a.get_actor_label(), HIDE))
unreal.log("IBPY: ib_restore_squad_hide_act5 done -- now press Ctrl+S to save the level")
