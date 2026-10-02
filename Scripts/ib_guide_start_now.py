"""
IBPY: ib_guide_start_now.py -- makes M1_GuideRoute start right when PIE begins
(instead of after Act I finishes), so the squad pulls the player along from the start.
Set START_DELAY / BACK_TO_AFTER_ACT1 below. Save the level afterwards (Ctrl+S).
Run: py "X:/IronBreach/Scripts/ib_guide_start_now.py"
"""
import unreal
START_DELAY = 2.0
BACK_TO_AFTER_ACT1 = False

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
found = False
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "M1_GuideRoute":
        found = True
        if BACK_TO_AFTER_ACT1:
            a.set_editor_property("auto_start", False)
        else:
            a.set_editor_property("auto_start", True)
            a.set_editor_property("start_delay_seconds", START_DELAY)
        unreal.log("IBPY: M1_GuideRoute auto_start=%s delay=%s pull_player=%s grace=%s speed=%s" % (
            a.get_editor_property("auto_start"), a.get_editor_property("start_delay_seconds"),
            a.get_editor_property("pull_player"), a.get_editor_property("pull_grace_seconds"),
            a.get_editor_property("pull_speed_cm")))
if not found:
    unreal.log_error("IBPY: M1_GuideRoute not found in this level")
