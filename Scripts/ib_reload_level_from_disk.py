"""
Reloads CarrowGateGarrison fresh from disk, discarding whatever is currently
in memory. Run this AFTER the .umap file has been restored on disk (e.g. from
git/LFS) to make the open editor actually reflect the restored file, instead
of risking a later save re-writing the in-memory (unwanted) state back out.

Run: exec(open(r"X:\IronBreach\Scripts\ib_reload_level_from_disk.py").read())
"""
import unreal

def log(msg):
    unreal.log(f"IBPY: {msg}")

MAP_PATH = "/Game/LevelPrototyping/CarrowGateGarrison"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
log(f"IBPY: reloading {MAP_PATH} fresh from disk (discarding in-memory state)")
result = les.load_level(MAP_PATH)
log(f"IBPY: load_level() -> {result}")
log("IBPY: === reload done -- do NOT save until you've confirmed this looks right ===")
