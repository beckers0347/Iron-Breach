"""
IBPY: ib_barracks_tune.py

Quick tuning pass for the already-placed Barracks_02 -- no re-import, no re-placement:
  1. rebuilds the procedural materials (see ib_barracks_materials.py) and applies them to the
     SM_Barracks_02 asset and to the three sensor doors
  2. sets how fast each door opens/closes (seconds, full swing)

HOW TO RUN (editor open, level loaded):
  py "X:/IronBreach/Scripts/ib_barracks_tune.py"

Edit OPEN_SECONDS / CLOSE_DELAY below and re-run any time. Nothing is saved automatically.
"""
import importlib
import os
import sys
import unreal

DEST_ROOT = "/Game/Buildings/Barracks_02"
TAG = "IB_Barracks02"
OPEN_SECONDS = {"Nose": 1.0, "Side": 1.0, "Hatch": 0.6}   # was 3.0 / 3.0 / 1.5 s
CLOSE_DELAY = 1.5                                         # seconds after the last player leaves
REBUILD_MATERIALS = True

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "X:/IronBreach/Scripts"
if _here not in sys.path:
    sys.path.insert(0, _here)
import ib_barracks_materials as mats_mod
importlib.reload(mats_mod)


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("=== ib_barracks_tune START ===")
    mats = {}
    if REBUILD_MATERIALS:
        log("[1/3] building materials")
        mats = mats_mod.build_all(f"{DEST_ROOT}/Materials")
        mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST_ROOT}/Static/SM_Barracks_02")
        if mesh:
            log("[2/3] applying to SM_Barracks_02")
            mats_mod.apply_to_static_mesh(mesh, mats)
        else:
            unreal.log_warning(f"IBPY: WARNING -- {DEST_ROOT}/Static/SM_Barracks_02 not found; run ib_replace_barracks.py first")

    log("[3/3] doors")
    n = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = a.get_actor_label()
        if not label.startswith("Barracks_Door_"):
            continue
        key = label.split("_")[-1]
        if key in OPEN_SECONDS:
            a.set_editor_property("open_duration_override", OPEN_SECONDS[key])
            a.set_editor_property("close_delay", CLOSE_DELAY)
            log(f"  {label}: open/close {OPEN_SECONDS[key]:.2f}s, close delay {CLOSE_DELAY:.1f}s")
        if mats:
            mats_mod.apply_to_component(a.get_editor_property("door_mesh"), mats)
        n += 1
    if not n:
        unreal.log_warning("IBPY: WARNING -- no Barracks_Door_* actors found in this level")
    log("=== DONE. Nothing saved: File > Save All when happy. ===")


main()
