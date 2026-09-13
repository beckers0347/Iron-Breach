import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")

les = unreal.LevelEditorSubsystem()
# Move camera above Mess Hall, looking down slightly, and give streaming a moment
target = unreal.Vector(3000.0, 7806.5, 1200.0)
rot = unreal.Rotator(0.0, -30.0, 0.0)
les.set_level_viewport_camera_info(target, rot)
log(f"IBPY: moved camera to {target}")
