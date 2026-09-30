import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
result = les.save_current_level()
log(f"IBPY: save_current_level() -> {result}")
unreal.EditorAssetLibrary.save_loaded_asset(unreal.EditorLevelLibrary.get_editor_world(), only_if_is_dirty=False) if False else None
log("IBPY: === save done ===")
