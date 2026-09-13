"""
Iron Breach -- fix Aura's Generated_Materials pass on the six garrison
buildings.

Runs directly in the editor's Python console:
    exec(open(r"X:\IronBreach\Scripts\ib_fix_garrison_building_materials.py").read())

WHAT WENT WRONG (verified by reading the actual .uasset content, not
guessing): Aura built a brand-new shared base material,
/Game/Generated_Materials/M_Garrison_Building_Concrete, with ZERO texture
nodes -- just flat Vector/Scalar color parameters. All six buildings'
"_Concrete" material instances (M_04_Watch_Tower_Concrete,
M_05_Barracks_Concrete, etc.) are instances of that flat base, and the
"_Roof"/"_Trim" materials are the same story -- solid color, no texture
sampling at all. This threw away the real, already-working weathered
concrete material (M_Armory_Concrete_Weathered, with actual 2K color+normal
textures) we built together earlier instead of building on it, which is why
the buildings now look like flat plastic instead of concrete.

THE FIX: reparent every building's "_Concrete" instance from the flat
M_Garrison_Building_Concrete to the real, textured M_Armory_Concrete_Weathered.
"_Roof"/"_Trim" get reparented to the same textured material as an interim
fix (a textured surface, even if not roof-specific yet, beats flat plastic) --
worth a proper follow-up Aura/Tripo3D pass later specifically for real roof
and trim textures, called out clearly at the end of this script's log.

This does NOT touch anything else in the project (Blockouts/MIC_Wall,
MIC_Roof, road pieces, etc.) -- those showed up as "recently modified" in a
file-timestamp check but that's routine Unreal asset re-save noise across
this project, not something this script assumes is broken or touches.
"""
import traceback
import unreal

EAL = unreal.EditorAssetLibrary

GOOD_PARENT_PATH = "/Game/Generated_Materials/M_Armory_Concrete_Weathered"

BUILDINGS = [
    "M_04_Watch_Tower",
    "M_05_Barracks",
    "M_06_Mess_Hall",
    "M_07_Armory",
    "M_08_Command_Comms",
    "M_09_Sensor_Array",
]
SLOTS = ["_Concrete", "_Roof", "_Trim"]
GEN_MAT_DIR = "/Game/Generated_Materials/"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def reparent(instance_path, new_parent):
    if not EAL.does_asset_exist(instance_path):
        log(f"FAIL {instance_path}: asset not found")
        return False
    instance = EAL.load_asset(instance_path)
    if not isinstance(instance, unreal.MaterialInstanceConstant):
        log(f"FAIL {instance_path}: not a MaterialInstanceConstant (class={instance.get_class().get_name()}) -- skipping")
        return False
    try:
        unreal.MaterialEditingLibrary.set_material_instance_parent(instance, new_parent)
    except Exception as e:
        log(f"    (set_material_instance_parent failed: {e}; trying set_editor_property fallback)")
        try:
            instance.set_editor_property("parent", new_parent)
        except Exception as e2:
            log(f"FAIL {instance_path}: could not reparent either way ({e2})")
            return False
    saved = EAL.save_asset(instance_path)
    log(f"OK   {instance_path} -> parent now {new_parent.get_name()} (saved={saved})")
    return True


def main():
    log("=== fixing garrison building materials (Aura flat-color regression) ===")

    if not EAL.does_asset_exist(GOOD_PARENT_PATH):
        log(f"FAIL good parent not found at {GOOD_PARENT_PATH} -- check the path (it may have moved).")
        return
    good_parent = EAL.load_asset(GOOD_PARENT_PATH)
    log(f"INFO using {GOOD_PARENT_PATH} as the real textured parent for all slots")

    ok_count = 0
    fail_count = 0
    for building in BUILDINGS:
        for slot in SLOTS:
            path = f"{GEN_MAT_DIR}{building}{slot}"
            if reparent(path, good_parent):
                ok_count += 1
            else:
                fail_count += 1

    log(f"=== done: {ok_count} materials reparented, {fail_count} failed ===")
    log("NOTE: Roof/Trim now use the same weathered-concrete texture as a stopgap -- "
        "they'll look textured instead of flat, but not roof-specific. Worth a follow-up "
        "prompt asking specifically for real roof shingle/panel and trim textures once "
        "this immediate flat-plastic problem is confirmed fixed in the viewport.")


try:
    main()
except Exception:
    log("FAIL unhandled exception")
    unreal.log_error(traceback.format_exc())
