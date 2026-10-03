"""Generic captures: reads X:/IronBreach/Saved/capture_job.json {level, out, shots:[[name, eye, target, fov],...]}. Never saves."""
import unreal, time, json, traceback
from pathlib import Path
job = json.load(open("X:/IronBreach/Saved/capture_job.json"))
OUT = Path(job["out"]); OUT.mkdir(parents=True, exist_ok=True)
SHOTS = job["shots"]
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map(job["level"])
if job.get("run_script"):
    import runpy
    try:
        runpy.run_path(job["run_script"], run_name="__main__")
    except BaseException:
        import traceback
        unreal.log_error("RUN_SCRIPT FAIL " + traceback.format_exc())
state = {"i": 0, "phase": "camera", "due": time.monotonic() + 10, "cam": None, "busy": False}
def finish():
    unreal.unregister_slate_post_tick_callback(state["handle"])
    open("X:/IronBreach/Saved/capture_done.txt", "w").write("ok")
    unreal.SystemLibrary.quit_editor()
def tick(dt):
    if state["busy"] or time.monotonic() < state["due"]: return
    state["busy"] = True
    try:
        if state["i"] >= len(SHOTS): finish(); return
        name, eye, tgt, fov = SHOTS[state["i"]]
        if state["phase"] == "camera":
            rot = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*eye), unreal.Vector(*tgt))
            cam = EAS.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*eye), rot)
            cam.get_component_by_class(unreal.CameraComponent).set_editor_property("field_of_view", float(fov))
            state["cam"] = cam
            LES.set_level_viewport_camera_info(unreal.Vector(*eye), rot, LES.get_active_viewport_config_key())
            LES.editor_set_game_view(True)
            state["phase"] = "capture"; state["due"] = time.monotonic() + 14
        elif state["phase"] == "capture":
            state["task"] = unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, str(OUT / (name + ".png")), state["cam"])
            state["phase"] = "next"; state["due"] = time.monotonic() + 4
        else:
            EAS.destroy_actor(state["cam"]); state["cam"] = None
            state["i"] += 1; state["phase"] = "camera"
    except Exception:
        unreal.log_error(traceback.format_exc()); finish()
    finally:
        state["busy"] = False
state["handle"] = unreal.register_slate_post_tick_callback(tick)
