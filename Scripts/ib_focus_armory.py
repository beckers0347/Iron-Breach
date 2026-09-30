import unreal

loc = unreal.Vector(9330.0 - 3500, -2552.0 - 2200, 78.0 + 2200)
rot = unreal.Rotator(0, -30, 45)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
unreal.log("IBPY: camera moved to Armory (wide)")
