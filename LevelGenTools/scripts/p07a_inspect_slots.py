"""p07a_inspect_slots.py - read-only: list every material slot of every building/door mesh so Phase 7 can map textures.

Run:   py "X:/IronBreach/LevelGenTools/scripts/p07a_inspect_slots.py"
Output goes to the log (LevelGenTools/logs). Changes nothing.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)


def main():
    G.init_log("p07a_inspect_slots")
    try:
        assets = G.load_json("assets.json")
        total = 0
        for key, entry in assets["buildings"].items():
            paths = unreal.EditorAssetLibrary.list_assets(entry["dest"], recursive=False, include_folder=False)
            for p in sorted(paths):
                obj = unreal.EditorAssetLibrary.load_asset(p)
                if not isinstance(obj, unreal.StaticMesh):
                    continue
                slots = [str(s.material_slot_name) for s in obj.static_materials]
                G.log("%s | %s | slots=%s" % (key, obj.get_name(), slots))
                total += 1
        G.verify("slots_listed", total > 0, "%d meshes" % total)
    except Exception as e:
        G.verify("p07a_unexpected", False, repr(e))
    G.summary()


main()
