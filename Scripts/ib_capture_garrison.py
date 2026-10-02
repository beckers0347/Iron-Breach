"""Garrison comparison captures. Changes nothing and never saves the level.

Needs the editor's render and tick loop, exactly as ib_capture_bastion.py does --
a commandlet has no Slate tick, so the screenshot sequence never fires:

    UnrealEditor.exe <project> -ExecutePythonScript="Scripts/ib_capture_garrison.py"

The aerial is framed the way the approved reference is: out over the water off
the seaward tip, high, looking back along the spine at the compound, so the
control platform falls on the left of frame and the dock and ship on the right.
That handedness is not assumed -- it comes from the same garrison frame the
layout pass uses, which derives landward from the Main Gate and image-right from
where the docks already are.

Environment:
    IB_GARRISON_INVENTORY  inventory folder (default Saved/GarrisonRestructure/inventory)
    IB_GARRISON_LAYOUT     layout folder, for plan.json (default .../layout)
    IB_GARRISON_SHOTS      output folder  (default .../shots)
    IB_GARRISON_RES        "WxH" (default 1600x900, the reference's aspect)

Run it before and after an apply pass; the framings are derived, not typed, so
the two sets line up.
"""
import unreal, time, os, json, traceback
from pathlib import Path

LEVEL = "/Game/LevelPrototyping/CarrowGateGarrison"
BASE = Path(unreal.Paths.project_saved_dir()) / "GarrisonRestructure"
INV = Path(os.environ.get("IB_GARRISON_INVENTORY", str(BASE / "inventory")))
LAY = Path(os.environ.get("IB_GARRISON_LAYOUT", str(BASE / "layout")))
OUT = Path(os.environ.get("IB_GARRISON_SHOTS", str(BASE / "shots")))
try:
    RES_X, RES_Y = (int(v) for v in os.environ.get("IB_GARRISON_RES", "1600x900").lower().split("x"))
except Exception:
    RES_X, RES_Y = 1600, 900

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT.mkdir(parents=True, exist_ok=True)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)


def axis_snap(dx, dy):
    return (1.0 if dx > 0 else -1.0, 0.0) if abs(dx) >= abs(dy) else (0.0, 1.0 if dy > 0 else -1.0)


def load_frame():
    """The one garrison frame. Prefers the layout's plan, so a capture can never
    be framed on a different site than the plan it is meant to illustrate."""
    try:
        plan = json.loads((LAY / "plan.json").read_text(encoding="utf-8"))
        fr = plan["frame"]
        fr["deck_z"] = plan.get("deck_z", fr.get("bbox_top_z", 0.0))
        fr["source"] = "layout plan.json"
        return fr
    except Exception:
        pass
    try:
        data = json.loads((INV / "assemblies.json").read_text(encoding="utf-8"))
        gf = data["garrison_frame"]
        by = {a["folder"]: a for a in data.get("assemblies", [])}
        centre = gf["centre"]
        gate = by["Carrowgate Garrison/Main Gate"]["bounds"]["centre"]
        deep = axis_snap(gate[0] - centre[0], gate[1] - centre[1])
        perp = (-deep[1], deep[0])
        dock = by["Carrowgate Garrison/Docks / Harbor"]["bounds"]["centre"]
        across = (dock[0] - centre[0]) * perp[0] + (dock[1] - centre[1]) * perp[1]
        right = perp if across > 0 else (-perp[0], -perp[1])
        depth = abs(deep[0]) * gf["size"][0] + abs(deep[1]) * gf["size"][1]
        width = abs(right[0]) * gf["size"][0] + abs(right[1]) * gf["size"][1]
        return {"deep": list(deep), "right": list(right), "depth": depth, "width": width,
                "front": [centre[0] - deep[0] * depth / 2.0, centre[1] - deep[1] * depth / 2.0],
                "centre": centre, "deck_z": gf["bbox_top_z"], "source": "inventory assemblies.json"}
    except Exception:
        return None


FRAME = load_frame()
if FRAME is None:
    unreal.log_error("GARRISON CAPTURE: no garrison frame. Run ib_inventory_garrison.py "
                     "(and ideally ib_layout_garrison.py) first. Nothing captured.")
    unreal.SystemLibrary.quit_editor()
    SHOTS = []
else:
    unreal.log("GARRISON CAPTURE: frame from " + str(FRAME.get("source")))
    deep, right = FRAME["deep"], FRAME["right"]
    D, W = FRAME["depth"], FRAME["width"]
    Z = FRAME["deck_z"]
    front, centre = FRAME["front"], FRAME["centre"]

    def at(v, u, height):
        """v along the spine from the seaward tip (negative is out to sea),
        u across it in the reference's sense (positive is the dock side)."""
        return (front[0] + deep[0] * v * D + right[0] * u * W,
                front[1] + deep[1] * v * D + right[1] * u * W,
                Z + height)

    SHOTS = [
        # Out over the water off the tip, ~48 degrees down: the reference's view.
        ("aerial-reference", at(-0.45, 0.0, 1.05 * D), (centre[0], centre[1], Z)),
        ("road-from-pad",    at(0.08, 0.0, 300.0),  at(0.80, 0.0, 600.0)),
        ("road-from-rear",   at(0.82, 0.0, 450.0),  at(0.06, 0.0, 200.0)),
        ("control-platform", at(0.30, -0.30, 700.0), at(0.20, -0.02, 200.0)),
        ("dock-and-berth",   at(0.18, 0.30, 500.0),  at(0.46, 0.38, 200.0)),
        ("hangar-reserve",   at(0.62, -0.10, 900.0), at(0.86, 0.0, 300.0)),
    ]

state = {"i": 0, "phase": "camera", "due": time.monotonic() + 3, "cam": None, "busy": False}


def finish():
    unreal.unregister_slate_post_tick_callback(state["handle"])
    unreal.log("GARRISON CAPTURE COMPLETE; nothing changed and no level saved -> " + str(OUT))
    unreal.SystemLibrary.quit_editor()


def tick(dt):
    if state["busy"] or time.monotonic() < state["due"]:
        return
    state["busy"] = True
    try:
        if state["i"] >= len(SHOTS):
            finish()
            return
        name, eye, target = SHOTS[state["i"]]
        if state["phase"] == "camera":
            rot = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*eye), unreal.Vector(*target))
            cam = EAS.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*eye), rot)
            cam.get_component_by_class(unreal.CameraComponent).set_editor_property(
                "field_of_view", 60.0 if name.startswith("aerial") else 75.0)
            state["cam"] = cam
            LES.set_level_viewport_camera_info(unreal.Vector(*eye), rot, LES.get_active_viewport_config_key())
            LES.editor_set_game_view(True)
            state["phase"] = "capture"
            state["due"] = time.monotonic() + 18      # streaming and shadows settle
        elif state["phase"] == "capture":
            state["task"] = unreal.AutomationLibrary.take_high_res_screenshot(
                RES_X, RES_Y, str(OUT / (name + ".png")), state["cam"])
            unreal.log("GARRISON CAPTURE: " + name)
            state["phase"] = "next"
            state["due"] = time.monotonic() + 4
        else:
            EAS.destroy_actor(state["cam"])           # the only actor this script creates
            state["cam"] = None
            state["i"] += 1
            state["phase"] = "camera"
    except Exception:
        unreal.log_error(traceback.format_exc())
        finish()
    finally:
        state["busy"] = False


if SHOTS:
    state["handle"] = unreal.register_slate_post_tick_callback(tick)
