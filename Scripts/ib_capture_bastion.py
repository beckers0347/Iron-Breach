"""Settled editor screenshots of fortress, quay and water. Never saves the level.
Run with -ExecutePythonScript. Optional IB_BASTION_CAPTURE_DIR selects output folder.
"""
import unreal, time, traceback, os
from pathlib import Path
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT = Path(os.environ.get("IB_BASTION_CAPTURE_DIR", str(Path(unreal.Paths.project_saved_dir()) / "BastionPolish/after")))
OUT.mkdir(parents=True, exist_ok=True)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/LevelPrototyping/CarrowGateGarrison")
SHOTS = [
    ("fortress", (-5000,-5800,3000), (-500,600,650)),
    ("yard", (6500,-6500,2600), (10500,-800,350)),
    ("water", (5200,-7800,480), (1700,-11000,-35)),
    ("player", (7000,7862,555), (7000,-5000,555)),
]
state = {"i": 0, "phase": "camera", "due": time.monotonic()+3, "cam": None, "busy": False}
def finish():
    unreal.unregister_slate_post_tick_callback(state["handle"])
    unreal.log("BASTION CAPTURE COMPLETE; no level saved")
    unreal.SystemLibrary.quit_editor()
def tick(dt):
    if state["busy"] or time.monotonic() < state["due"]: return
    state["busy"] = True
    try:
        if state["i"] >= len(SHOTS): finish(); return
        name, eye, target = SHOTS[state["i"]]
        if state["phase"] == "camera":
            rot = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*eye), unreal.Vector(*target))
            cam = EAS.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*eye), rot)
            cam.get_component_by_class(unreal.CameraComponent).set_editor_property("field_of_view",70.0)
            state["cam"] = cam
            LES.set_level_viewport_camera_info(unreal.Vector(*eye), rot, LES.get_active_viewport_config_key())
            LES.editor_set_game_view(True)
            state["phase"] = "capture"; state["due"] = time.monotonic()+18
        elif state["phase"] == "capture":
            state["task"] = unreal.AutomationLibrary.take_high_res_screenshot(1280,720,str(OUT/(name+".png")),state["cam"])
            unreal.log("BASTION CAPTURE: " + name)
            state["phase"] = "next"; state["due"] = time.monotonic()+4
        else:
            EAS.destroy_actor(state["cam"]); state["cam"] = None
            state["i"] += 1; state["phase"] = "camera"
    except Exception:
        unreal.log_error(traceback.format_exc()); finish()
    finally: state["busy"] = False
state["handle"] = unreal.register_slate_post_tick_callback(tick)
