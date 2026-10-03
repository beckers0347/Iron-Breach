"""p11a_import_door_skeletals.py - import the 38 skeletal door FBX files (1 bone at the pivot + an 'open' animation).

Run (after p07 so the M_* materials exist):
  py "X:/IronBreach/LevelGenTools/scripts/p11a_import_door_skeletals.py"

Each door becomes SK_<door> + A_<door>_Open in /Game/IronBreach/Thornfield/Doors/<Building>/ and gets its
materials from the slot names. These are the assets the existing AIBSensorDoor C++ actor drives (no Blueprint).

Look for:
  [Thornfield] VERIFY: doors_imported PASS (38 of 38)
  [Thornfield] VERIFY: door_animations PASS
  [Thornfield] VERIFY: door_materials PASS
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)

FORCE = False


def _options():
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", True)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    ui.set_editor_property("import_animations", True)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("create_physics_asset", False)
    return ui


def _find(folder, cls):
    out = []
    for p in unreal.EditorAssetLibrary.list_assets(folder, recursive=False, include_folder=False):
        o = unreal.EditorAssetLibrary.load_asset(p)
        if isinstance(o, cls):
            out.append((p, o))
    return out


def main():
    G.init_log("p11a_import_door_skeletals")
    try:
        try:
            unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
        except Exception as e:
            G.warn("console command failed: %r" % e)
        assets = G.load_json("assets.json")
        mcfg = G.load_json("materials.json")
        cfg = assets["door_skeletals"]
        total, ok, anim_ok, bad_mat = 0, 0, 0, []
        for key, entry in assets["buildings"].items():
            jpath = os.path.join(G.project_dir(), entry["door_json"].replace("/", os.sep))
            with open(jpath, "r", encoding="utf-8") as f:
                doors = json.load(f).get("doors", {})
            folder = "%s/%s" % (cfg["dest_root"], key)
            unreal.EditorAssetLibrary.make_directory(folder)
            for dname in doors:
                total += 1
                src = os.path.join(G.project_dir(), cfg["source_root"].replace("/", os.sep), key, dname + ".fbx")
                sk_path = "%s/SK_%s" % (folder, dname)
                an_path = "%s/A_%s_Open" % (folder, dname)
                if not os.path.isfile(src):
                    G.err("Door FBX missing: %s" % src)
                    continue
                if FORCE or not (unreal.EditorAssetLibrary.does_asset_exist(sk_path) and unreal.EditorAssetLibrary.does_asset_exist(an_path)):
                    t = unreal.AssetImportTask()
                    t.set_editor_property("filename", src)
                    t.set_editor_property("destination_path", folder)
                    t.set_editor_property("destination_name", "SK_%s" % dname)
                    t.set_editor_property("replace_existing", True)
                    t.set_editor_property("automated", True)
                    t.set_editor_property("save", False)
                    t.set_editor_property("options", _options())
                    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
                    # the importer names the animation itself; give it our name
                    if not unreal.EditorAssetLibrary.does_asset_exist(an_path):
                        for p, a in _find(folder, unreal.AnimSequence):
                            base = p.split(".")[0]
                            if dname in base and not base.endswith("_Open"):
                                unreal.EditorAssetLibrary.rename_asset(base, an_path)
                                break
                sk = unreal.EditorAssetLibrary.load_asset(sk_path)
                an = unreal.EditorAssetLibrary.load_asset(an_path)
                if sk is None:
                    G.err("Skeletal mesh missing after import: %s" % sk_path)
                    continue
                ok += 1
                if an is not None and an.get_editor_property("sequence_length") > 0.05:
                    anim_ok += 1
                else:
                    G.err("No usable animation for %s" % dname)
                # materials by slot name
                new = []
                for m in sk.materials:
                    slot = str(m.material_slot_name)
                    mat = unreal.EditorAssetLibrary.load_asset("%s/%s" % (mcfg["dest"], slot))
                    if mat is None:
                        bad_mat.append("%s:%s" % (dname, slot))
                        new.append(m)
                        continue
                    new.append(unreal.SkeletalMaterial(material_interface=mat, material_slot_name=m.material_slot_name,
                                                       uv_channel_data=m.uv_channel_data))
                sk.set_editor_property("materials", new)
                unreal.EditorAssetLibrary.save_loaded_asset(sk)
                if an is not None:
                    unreal.EditorAssetLibrary.save_loaded_asset(an)
                if total % 10 == 0:
                    G.log("... %d doors processed" % total)
        G.verify("doors_imported", ok == total, "%d of %d" % (ok, total))
        G.verify("door_animations", anim_ok == total, "%d of %d have an open animation" % (anim_ok, total))
        G.verify("door_materials", not bad_mat, "all slots mapped" if not bad_mat else "missing %s" % sorted(set(bad_mat))[:6])
    except G.GenError as e:
        G.err(str(e))
        G.verify("p11a_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p11a_unexpected", False, repr(e))
    G.summary()


main()
