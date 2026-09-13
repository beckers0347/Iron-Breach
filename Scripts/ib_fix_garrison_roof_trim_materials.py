"""
Iron Breach -- fix the 12 Roof/Trim FAILs from
ib_fix_garrison_building_materials.py.

Runs directly in the editor's Python console:
    exec(open(r"X:\IronBreach\Scripts\ib_fix_garrison_roof_trim_materials.py").read())

WHY THE PREVIOUS SCRIPT FAILED ON THESE 12: Aura built the Roof/Trim slots
as plain base Material assets (class "Material"), not
MaterialInstanceConstant like the Concrete slots. set_material_instance_parent
only works on an instance -- there's no "parent" to set on a base Material,
so those 12 correctly failed rather than silently doing nothing.

THE FIX: for each flat Roof/Trim Material,
  1. Rename it out of the way to "<Name>_Flat_Backup" (kept, not deleted, in
     case Aura's version is ever wanted again).
  2. Create a brand-new MaterialInstanceConstant AT THE ORIGINAL PATH,
     parented to the real textured M_Armory_Concrete_Weathered.
Putting the new instance at the exact original asset path means anything
already referencing that Roof/Trim slot (a mesh, a BP construction script,
etc.) picks up the textured material automatically -- no need to hunt down
and re-point individual usages.

Same stopgap caveat as before: Roof/Trim will look like weathered concrete,
not roof-specific, until a follow-up Aura/Tripo3D pass makes real roof and
trim textures.
"""
import traceback
import unreal

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()

GOOD_PARENT_PATH = "/Game/Generated_Materials/M_Armory_Concrete_Weathered"

BUILDINGS = [
    "M_04_Watch_Tower",
    "M_05_Barracks",
    "M_06_Mess_Hall",
    "M_07_Armory",
    "M_08_Command_Comms",
    "M_09_Sensor_Array",
]
SLOTS = ["_Roof", "_Trim"]
GEN_MAT_DIR = "/Game/Generated_Materials/"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def fix_one(path, good_parent):
    if not EAL.does_asset_exist(path):
        log(f"SKIP {path}: asset not found (already fixed or never existed)")
        return None

    asset = EAL.load_asset(path)
    class_name = asset.get_class().get_name()

    if class_name == "MaterialInstanceConstant":
        log(f"SKIP {path}: already a MaterialInstanceConstant -- reparenting instead")
        try:
            unreal.MaterialEditingLibrary.set_material_instance_parent(asset, good_parent)
            EAL.save_asset(path)
            log(f"OK   {path} reparented (was already an instance)")
        except Exception as e:
            log(f"FAIL {path}: reparent-of-existing-instance failed ({e})")
        return None

    if class_name != "Material":
        log(f"FAIL {path}: unexpected class {class_name} -- not touching, check by hand")
        return None

    backup_path = path + "_Flat_Backup"
    if EAL.does_asset_exist(backup_path):
        log(f"INFO backup already exists at {backup_path} -- leaving it, just replacing {path}")
        try:
            EAL.delete_asset(path)
        except Exception as e:
            log(f"FAIL {path}: could not delete original to make room for the new instance ({e})")
            return None
    else:
        renamed = EAL.rename_asset(path, backup_path)
        if not renamed:
            log(f"FAIL {path}: rename_asset to {backup_path} failed")
            return None
        log(f"OK   backed up flat material to {backup_path}")

    package_path, asset_name = path.rsplit("/", 1)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    new_instance = AT.create_asset(asset_name, package_path, unreal.MaterialInstanceConstant, factory)
    if not new_instance:
        log(f"FAIL could not create new MaterialInstanceConstant at {path}")
        return None

    try:
        unreal.MaterialEditingLibrary.set_material_instance_parent(new_instance, good_parent)
    except Exception as e:
        log(f"FAIL {path}: created instance but could not set parent ({e})")
        return None

    EAL.save_asset(path)
    log(f"OK   {path} -> new textured MaterialInstanceConstant (parent {good_parent.get_name()})")
    return True


def main():
    log("=== fixing garrison Roof/Trim materials (flat base Material -> textured instance) ===")

    if not EAL.does_asset_exist(GOOD_PARENT_PATH):
        log(f"FAIL good parent not found at {GOOD_PARENT_PATH} -- check the path.")
        return
    good_parent = EAL.load_asset(GOOD_PARENT_PATH)

    ok_count = 0
    fail_count = 0
    for building in BUILDINGS:
        for slot in SLOTS:
            path = f"{GEN_MAT_DIR}{building}{slot}"
            result = fix_one(path, good_parent)
            if result:
                ok_count += 1
            elif result is None:
                pass
            else:
                fail_count += 1

    log(f"=== done: {ok_count} Roof/Trim materials fixed ===")
    log("NOTE: these are the same weathered-concrete texture as a stopgap, not "
        "roof/trim-specific -- worth a follow-up Aura/Tripo3D prompt for real "
        "roof shingle/panel and trim textures once this looks right in the viewport. "
        "The original flat Aura materials are preserved as *_Flat_Backup if you ever "
        "want to compare or revert.")


try:
    main()
except Exception:
    log("FAIL unhandled exception")
    unreal.log_error(traceback.format_exc())
