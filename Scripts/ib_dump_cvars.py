import unreal
unreal.log("IBPY: === DumpCVars (all) ===")
unreal.SystemLibrary.execute_console_command(None, "DumpCVars")
unreal.log("IBPY: === DUMP DONE ===")
