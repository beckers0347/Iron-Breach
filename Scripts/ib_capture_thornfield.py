"""Thornfield comparison captures. Changes nothing, never saves.
Run: UnrealEditor.exe IronBreach.uproject -ExecutePythonScript="Scripts/ib_capture_thornfield.py"
Env: IB_TF_TAG (output subfolder, default 'cur')
"""
import unreal, time, os, traceback
from pathlib import Path

LEVEL = "/Game/IronBreach/Thornfield/Levels/L_ThornfieldGarrison"
TAG = os.environ.get("IB_TF_TAG", "cur")
OUT = Path(unreal.Paths.project_saved_dir()) / "ThornfieldShots" / TAG
OUT.mkdir(parents=True, exist_ok=True)
H = 19200.0


def w(px, py, z=0.0):
    return (px, H - py, z)


SHOTS = [
    ("ref_view", w(-4500, -7000, 9500), w(17500, 9500, 0), 60),
    ("aerial_south", w(17000, -9000, 9000), w(17000, 9500, 0), 60),
    ("aerial_east", w(42000, 9500, 8000), w(17000, 9500, 0), 60),
    ("topdown", w(17200, 9600, 42000), w(17200, 9601, 0), 70),
    ("gate_ground", w(16750, -1500, 350), w(16750, 3500, 400), 75),
    ("yard_hangars", w(22500, 6500, 500), w(27750, 11000, 500), 75),
]

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
state = {"i": 0, "phase": "camera", "due": time.monotonic() + 8, "cam": None, "busy": False}


def finish():
    unreal.unregister_slate_post_tick_callback(state["handle"])
    unreal.log("THORNFIELD CAPTURE COMPLETE -> " + str(OUT))
    unreal.SystemLibrary.quit_editor()


def tick(dt):
    if state["busy"] or time.monotonic() < state["due"]:
        return
    state["busy"] = True
    try:
        if state["i"] >= len(SHOTS):
            finish(); return
        name, eye, tgt, fov = SHOTS[state["i"]]
        if state["phase"] == "camera":
            rot = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*eye), unreal.Vector(*tgt))
            cam = EAS.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*eye), rot)
            cam.get_component_by_class(unreal.CameraComponent).set_editor_property("field_of_view", float(fov))
            state["cam"] = cam
            LES.set_level_viewport_camera_info(unreal.Vector(*eye), rot, LES.get_active_viewport_config_key())
            LES.editor_set_game_view(True)
            state["phase"] = "capture"; state["due"] = time.monotonic() + 15
        elif state["phase"] == "capture":
            state["task"] = unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, str(OUT / (name + ".png")), state["cam"])
            unreal.log("THORNFIELD CAPTURE: " + name)
            state["phase"] = "next"; state["due"] = time.monotonic() + 4
        else:
            EAS.destroy_actor(state["cam"]); state["cam"] = None
            state["i"] += 1; state["phase"] = "camera"
    except Exception:
        unreal.log_error(traceback.format_exc()); finish()
    finally:
        state["busy"] = False


state["handle"] = unreal.register_slate_post_tick_callback(tick)
