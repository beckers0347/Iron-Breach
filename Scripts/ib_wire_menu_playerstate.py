"""
Iron Breach -- front-end GameMode wiring for the operative flow.
Runs headless (zzcharwatch: "py ib_wire_menu_playerstate.py"). Idempotent.

Lvl_MainMenu runs under the GlobalDefaultGameMode (BP_FirstPersonGameMode),
whose PlayerState is the stock APlayerState -- so the operative identity had
nowhere to land and the fireteam banner kept showing the Steam name. This
points that GameMode's Player State Class at BP_IBPlayerState (the same class
BP_IronBreachGameMode already uses). The controller class is left alone on
purpose: the template controller owns first-person input, and identity now
travels through the PlayerState, so it doesn't need the IB controller.
"""
import traceback
import unreal

EAL = unreal.EditorAssetLibrary

def log(msg):
    unreal.log(f"IBPY: {msg}")

GM_PATH = "/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode"
PS_PATH = "/Game/IronBreach/Core/BP_IBPlayerState"

def try_compile(bp):
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    except Exception:
        pass

def cls_name(c):
    return c.get_name() if c else "None"

log("=== front-end PlayerState wiring ===")
try:
    gm = EAL.load_asset(GM_PATH) if EAL.does_asset_exist(GM_PATH) else None
    ps = EAL.load_asset(PS_PATH) if EAL.does_asset_exist(PS_PATH) else None
    if not gm:
        log(f"FAIL GameMode not found: {GM_PATH}")
    elif not ps:
        log(f"FAIL PlayerState BP not found: {PS_PATH}")
    else:
        target = ps.generated_class()
        cdo = unreal.get_default_object(gm.generated_class())
        current = cdo.get_editor_property("player_state_class")
        log(f"INFO {GM_PATH} PlayerStateClass before: {cls_name(current)}")
        if current is not None and current.get_name() == target.get_name():
            log("OK   already wired -- nothing to do")
        else:
            cdo.set_editor_property("player_state_class", target)
            try_compile(gm)
            saved = EAL.save_asset(GM_PATH)
            after = unreal.get_default_object(gm.generated_class()).get_editor_property("player_state_class")
            ok = saved and after is not None and after.get_name() == target.get_name()
            log(("OK   " if ok else "FAIL ") + f"PlayerStateClass now: {cls_name(after)} (saved={saved})")
        log(f"INFO PlayerControllerClass left as: {cls_name(cdo.get_editor_property('player_controller_class'))}")

    # For the record: the gameplay GameMode's wiring.
    gm2_path = "/Game/BP_IronBreachGameMode"
    if EAL.does_asset_exist(gm2_path):
        gm2 = EAL.load_asset(gm2_path)
        c2 = unreal.get_default_object(gm2.generated_class())
        log(f"INFO {gm2_path}: PlayerState={cls_name(c2.get_editor_property('player_state_class'))} "
            f"PlayerController={cls_name(c2.get_editor_property('player_controller_class'))}")
except Exception:
    log("FAIL exception")
    unreal.log_error(traceback.format_exc())
log("=== wiring done ===")
