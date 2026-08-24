"""
Iron Breach — audio channel assets for the Settings screen.
Creates /Game/IronBreach/Audio: SC_Master with SC_Music + SC_SFX children,
and SMix_IB (empty mix — runtime SetSoundMixClassOverride does the work).
Shane: assign SC_Music/SC_SFX on sounds and the sliders start ruling them.
Idempotent.
"""
import traceback
import unreal

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
AUDIO_DIR = "/Game/IronBreach/Audio"

def log(msg):
    unreal.log(f"IBPY: {msg}")

def step(name, fn):
    try:
        result = fn()
        log(f"OK   {name}")
        return result
    except Exception:
        log(f"FAIL {name}")
        unreal.log_error(traceback.format_exc())
        return None

def create(name, klass, factory):
    full = f"{AUDIO_DIR}/{name}"
    if EAL.does_asset_exist(full):
        return EAL.load_asset(full)
    return AT.create_asset(name, AUDIO_DIR, klass, factory)

log("=== audio asset pass starting ===")

if not EAL.does_directory_exist(AUDIO_DIR):
    EAL.make_directory(AUDIO_DIR)

sc_factory = unreal.SoundClassFactory()
sc_master = step("SC_Master", lambda: create("SC_Master", unreal.SoundClass, sc_factory))
sc_music  = step("SC_Music",  lambda: create("SC_Music",  unreal.SoundClass, unreal.SoundClassFactory()))
sc_sfx    = step("SC_SFX",    lambda: create("SC_SFX",    unreal.SoundClass, unreal.SoundClassFactory()))

def parent_children():
    kids = [c for c in (sc_music, sc_sfx) if c]
    if sc_master and kids:
        sc_master.set_editor_property("child_classes", kids)
    return True

step("parent music/sfx under master", parent_children)

step("SMix_IB", lambda: create("SMix_IB", unreal.SoundMix, unreal.SoundMixFactory()))

step("save", lambda: EAL.save_directory(AUDIO_DIR, only_if_is_dirty=False, recursive=True))
log("=== audio asset pass done ===")
