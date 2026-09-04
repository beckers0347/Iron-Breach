"""
Iron Breach — character flow audit (operative select / create).
Runs headless: UnrealEditor-Cmd -run=pythonscript (zzcharbuild.bat step 2).
Read-only: verifies the editor side of Boot -> Menu -> Operative flow and
prints IBPY lines. Nothing is created or saved — the flow is C++-driven and
needs no new Blueprint graphs; this proves the two assets it rides on are
wired the way the code expects.
"""
import unreal

def log(msg):
    unreal.log(f"IBPY: {msg}")

RESULT = {"ok": True}

def check(name, cond, detail=""):
    if cond:
        log(f"OK   {name}" + (f" -- {detail}" if detail else ""))
    else:
        RESULT["ok"] = False
        log(f"FAIL {name}" + (f" -- {detail}" if detail else ""))

EAL = unreal.EditorAssetLibrary

log("=== character flow audit starting ===")

# 1) The new C++ classes made it into the module (build + module load proof).
for cls in ["IBCharacterSubsystem", "IBCharacterSelectScreen",
            "IBCharacterCreateScreen", "IBCharacterSaveGame"]:
    check(f"C++ class visible: {cls}", hasattr(unreal, cls))

# 2) WBP_MainMenu: still parented (through any BP chain) to the C++ brains the flow hooks into.
mm = EAL.load_asset("/Game/UI/WBP_MainMenu") if EAL.does_asset_exist("/Game/UI/WBP_MainMenu") else None
check("WBP_MainMenu loads", mm is not None)
if mm:
    try:
        gen = mm.generated_class()
        cdo = unreal.get_default_object(gen) if gen else None
        is_child = bool(cdo) and isinstance(cdo, unreal.IBMainMenuWidget)
        check("WBP_MainMenu derives from IBMainMenuWidget", is_child, gen.get_name() if gen else "no generated class")
        # Optional binds the C++ looks for -- report which ones the WBP actually has.
        if cdo:
            found = []
            for name in ["Btn_Solo", "Btn_Host", "Btn_Join", "Btn_Quit", "Btn_Settings", "Txt_Status", "Txt_Operative", "Btn_Operative"]:
                try:
                    if cdo.get_editor_property(name) is not None:
                        found.append(name)
                except Exception:
                    pass
            log(f"INFO WBP_MainMenu optional binds present on CDO: {found if found else 'none resolvable headless (BindWidgetOptional binds resolve per-instance)'}")
    except Exception as e:
        check("WBP_MainMenu class chain readable", False, str(e))

# 3) WBP_BootScreen: the press-any-button screen that spawns the menu.
check("WBP_BootScreen loads", EAL.does_asset_exist("/Game/UI/WBP_BootScreen"))

# 4) Front-end GameMode carries the IB PlayerState (operative identity -> fireteam banners).
gm_path = "/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode"
if EAL.does_asset_exist(gm_path):
    try:
        gm = EAL.load_asset(gm_path)
        ps_cls = unreal.get_default_object(gm.generated_class()).get_editor_property("player_state_class")
        ps_cdo = unreal.get_default_object(ps_cls) if ps_cls else None
        check("Front-end GameMode PlayerState is an IBPlayerState", bool(ps_cdo) and isinstance(ps_cdo, unreal.IBPlayerState),
              ps_cls.get_name() if ps_cls else "None")
    except Exception as e:
        check("Front-end GameMode readable", False, str(e))
else:
    check("BP_FirstPersonGameMode exists", False, gm_path)

log("AUDIT RESULT: " + ("ALL CLEAR -- no Blueprint wiring needed" if RESULT["ok"] else "ISSUES FOUND (see FAIL lines)"))
