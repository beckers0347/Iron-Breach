"""
Iron Breach -- import Tripo3D-generated Roof/Trim textures and apply them to
the six garrison buildings.

Runs directly in the editor's Python console:
    exec(open(r"X:\IronBreach\Scripts\ib_import_apply_tripo_roof_trim.py").read())

BACKGROUND: after pulling Aura out entirely, all 6 buildings' _Concrete,
_Roof and _Trim material slots are MaterialInstanceConstant assets parented
to the real textured M_Armory_Concrete_Weathered (a Material that exposes
its textures as named TextureSampleParameter2D params: "BaseColorTexture"
and "NormalMap", plus a "Tiling" scalar param -- confirmed by reading the
asset directly). Right now Roof and Trim just inherit the parent's
concrete textures untouched, which is why they still look like walls.

WHAT THIS SCRIPT DOES:
  1. Looks in SOURCE_DIR (X:\Downloads by default) for the 4 PNGs you
     downloaded from Tripo3D and expects them named:
         Roof_Color.png   Roof_Normal.png
         Trim_Color.png   Trim_Normal.png
     (.jpg also accepted; matching is case-insensitive.)
  2. Imports each as a proper Texture2D asset into
     /Game/Generated_Materials/, named T_Garrison_Roof_Metal_Color,
     T_Garrison_Roof_Metal_Normal, T_Garrison_Trim_Metal_Color,
     T_Garrison_Trim_Metal_Normal. Normal maps get their compression
     setting forced to TC_Normalmap and sRGB turned off (required for
     normal maps to read correctly in UE -- easy to forget by hand).
  3. For each of the 6 buildings' existing _Roof / _Trim material
     instances, overrides the "BaseColorTexture" and "NormalMap"
     parameters with the matching new texture -- so Roof gets the roof
     metal texture, Trim gets the trim texture, and Concrete is left
     alone (still weathered concrete, untouched by this script).

Every import and every parameter set is individually try/except'd with
OK/FAIL logging -- if the exposed parameter names turn out not to be
exactly "BaseColorTexture"/"NormalMap" this will tell you plainly instead
of silently doing nothing, and you can fix the CANDIDATE lists below and
rerun (it's idempotent).
"""
import os
import traceback
import unreal

EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary

SOURCE_DIR = os.environ.get("IB_TRIPO_DIR", r"X:\Downloads")
DEST_PATH = "/Game/Generated_Materials"

BUILDINGS = [
    "M_04_Watch_Tower",
    "M_05_Barracks",
    "M_06_Mess_Hall",
    "M_07_Armory",
    "M_08_Command_Comms",
    "M_09_Sensor_Array",
]

# slot -> (source filename stem, new texture asset name stem)
SLOT_SOURCES = {
    "_Roof": ("Roof", "T_Garrison_Roof_Metal"),
    "_Trim": ("Trim", "T_Garrison_Trim_Metal"),
}

# Guessed exposed parameter names on M_Armory_Concrete_Weathered (confirmed
# via strings that TextureSampleParameter2D nodes exist -- these are the
# most likely display/param names, tried in order).
BASECOLOR_PARAM_CANDIDATES = ["BaseColorTexture", "BaseColor", "Base Color Texture"]
NORMAL_PARAM_CANDIDATES = ["NormalMap", "Normal", "Normal Map"]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def find_source_file(stem, kind):
    """kind is 'Color' or 'Normal'. Tries .png then .jpg, case-insensitive."""
    for ext in (".png", ".jpg", ".jpeg", ".tga"):
        for name in (f"{stem}_{kind}{ext}", f"{stem}_{kind}{ext.upper()}"):
            candidate = os.path.join(SOURCE_DIR, name)
            if os.path.isfile(candidate):
                return candidate
    # case-insensitive fallback scan
    try:
        for fname in os.listdir(SOURCE_DIR):
            lower = fname.lower()
            if lower.startswith(f"{stem.lower()}_{kind.lower()}") and lower.endswith((".png", ".jpg", ".jpeg", ".tga")):
                return os.path.join(SOURCE_DIR, fname)
    except Exception:
        pass
    return None


def import_texture(src_path, asset_name, is_normal):
    dest_asset_path = f"{DEST_PATH}/{asset_name}"
    if EAL.does_asset_exist(dest_asset_path):
        log(f"INFO {dest_asset_path} already exists -- reimporting over it")

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src_path)
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("factory", unreal.TextureFactory())

    AT.import_asset_tasks([task])

    if not EAL.does_asset_exist(dest_asset_path):
        log(f"FAIL import produced no asset at {dest_asset_path} (source: {src_path})")
        return None

    texture = EAL.load_asset(dest_asset_path)

    if is_normal:
        try:
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            texture.set_editor_property("srgb", False)
            EAL.save_asset(dest_asset_path)
            log(f"OK   imported {dest_asset_path} (normal map settings applied)")
        except Exception as e:
            log(f"OK   imported {dest_asset_path}, but FAILED to set normal-map compression ({e}) -- fix by hand in Texture editor")
    else:
        log(f"OK   imported {dest_asset_path}")

    return texture


def set_param_first_match(instance, candidates, texture, label):
    for name in candidates:
        try:
            MEL.set_material_instance_texture_parameter_value(instance, name, texture)
            log(f"    OK   set {label} param '{name}'")
            return True
        except Exception:
            continue
    log(f"    FAIL could not set {label} texture param -- tried {candidates}; "
        f"check the exact TextureSampleParameter2D name in M_Armory_Concrete_Weathered's material graph")
    return False


def apply_to_slot(building, slot, color_tex, normal_tex):
    path = f"{DEST_PATH}/{building}{slot}"
    if not EAL.does_asset_exist(path):
        log(f"FAIL {path}: instance not found -- run ib_fix_garrison_roof_trim_materials.py first")
        return
    instance = EAL.load_asset(path)
    if not isinstance(instance, unreal.MaterialInstanceConstant):
        log(f"FAIL {path}: not a MaterialInstanceConstant (class={instance.get_class().get_name()})")
        return
    log(f"INFO applying textures to {path}")
    ok_color = set_param_first_match(instance, BASECOLOR_PARAM_CANDIDATES, color_tex, "BaseColor")
    ok_normal = set_param_first_match(instance, NORMAL_PARAM_CANDIDATES, normal_tex, "Normal")
    if ok_color or ok_normal:
        EAL.save_asset(path)


def main():
    log(f"=== importing Tripo3D roof/trim textures from {SOURCE_DIR} ===")

    imported = {}
    for slot, (stem, asset_stem) in SLOT_SOURCES.items():
        color_src = find_source_file(stem, "Color")
        normal_src = find_source_file(stem, "Normal")
        if not color_src:
            log(f"FAIL could not find a {stem}_Color.(png/jpg) in {SOURCE_DIR} -- "
                f"download it from Tripo3D and save it there with that name, then rerun")
        if not normal_src:
            log(f"FAIL could not find a {stem}_Normal.(png/jpg) in {SOURCE_DIR}")
        if not (color_src and normal_src):
            continue

        color_tex = import_texture(color_src, f"{asset_stem}_Color", is_normal=False)
        normal_tex = import_texture(normal_src, f"{asset_stem}_Normal", is_normal=True)
        if color_tex and normal_tex:
            imported[slot] = (color_tex, normal_tex)

    if not imported:
        log("FAIL nothing imported -- nothing to apply. Check SOURCE_DIR and filenames above.")
        return

    log("=== applying imported textures to the 6 buildings ===")
    for building in BUILDINGS:
        for slot, (color_tex, normal_tex) in imported.items():
            apply_to_slot(building, slot, color_tex, normal_tex)

    log("=== done ===")
    log("If you see FAIL lines under 'applying textures', the parameter names on "
        "M_Armory_Concrete_Weathered aren't exactly BaseColorTexture/NormalMap -- open that "
        "material in the editor, click the two TextureSampleParameter2D nodes, and tell me "
        "the exact Parameter Name shown in the Details panel so I can fix the candidate list.")


try:
    main()
except Exception:
    log("FAIL unhandled exception")
    unreal.log_error(traceback.format_exc())
