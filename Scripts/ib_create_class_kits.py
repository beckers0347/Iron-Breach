"""
Iron Breach -- class kit data assets (Content/IronBreach/Classes/DA_Kit_<Trade>).
Headless: zzcharwatch "py ib_create_class_kits.py". Idempotent: existing assets
are left alone (designer edits win) -- delete one to regenerate it from the
C++ defaults. Values mirror UIBOperativeKitComponent::DefaultKitFor.
"""
import traceback
import unreal

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
ROOT = "/Game/IronBreach/Classes"

def log(msg):
    unreal.log(f"IBPY: {msg}")

def spec(name, desc, effect, cooldown, duration=0.0, strength=1200.0, rng=600.0, radius=500.0,
         damage=0.0, taken=1.0, slow=1.0, marks=False, at_aim=False):
    s = unreal.IBKitAbilitySpec()
    s.set_editor_property("display_name", name)
    s.set_editor_property("description", desc)
    s.set_editor_property("effect", effect)
    s.set_editor_property("cooldown", cooldown)
    s.set_editor_property("duration", duration)
    s.set_editor_property("strength", strength)
    s.set_editor_property("range", rng)
    s.set_editor_property("radius", radius)
    s.set_editor_property("damage", damage)
    s.set_editor_property("damage_taken_scale", taken)
    s.set_editor_property("slow_factor", slow)
    s.set_editor_property("marks_targets", marks)
    s.set_editor_property("place_at_aim", at_aim)
    return s

E = unreal.IBKitEffect
KITS = {
    "Breaker": (unreal.IBOperativeClass.BREAKER,
        spec("RAM CHARGE", "Shoulder-mounted concussive breach: a short lunge that hammers everything in front of you and opens armor seams.",
             E.CONE_STRIKE, 10.0, duration=0.2, strength=1500.0, rng=380.0, radius=220.0, damage=60.0),
        spec("BULWARK DASH", "Armored lunge -- most incoming damage shrugs off for the length of the dash.",
             E.DASH, 6.0, duration=0.6, strength=1600.0, taken=0.35)),
    "Picket": (unreal.IBOperativeClass.PICKET,
        spec("LAMPLIGHT FLARE", "Thrown sensor spike: everything hostile around it is marked for the fireteam while it burns.",
             E.DEPLOY_ZONE, 14.0, duration=8.0, rng=2500.0, radius=900.0, marks=True, at_aim=True),
        spec("LINE BOLT", "Launchable cable runner -- zip to whatever you're aiming at.",
             E.GRAPPLE, 5.0, rng=3000.0, strength=2200.0)),
    "Bellringer": (unreal.IBOperativeClass.BELLRINGER,
        spec("DETERRENT PYLON", "Area denial: it sings 'nothing here' -- hostiles inside crawl.",
             E.DEPLOY_ZONE, 16.0, duration=10.0, radius=700.0, slow=0.45),
        spec("NULL STEP", "Acoustic-dampened glide: hang in the air with full control for a few seconds.",
             E.GLIDE, 5.0, duration=2.5, strength=0.12)),
    "Corpsman": (unreal.IBOperativeClass.CORPSMAN,
        spec("STIM LINE", "Tethered field-dressing dart. (Post-launch corps -- Blueprint placeholder.)",
             E.BLUEPRINT, 10.0),
        spec("SURGE CARRY", "A sprint that ignores carry penalties.",
             E.DASH, 6.0, duration=0.3, strength=1300.0)),
}

log("=== class kit assets ===")
try:
    if not EAL.does_directory_exist(ROOT):
        EAL.make_directory(ROOT)
    for trade, (cls, kit_ability, movement) in KITS.items():
        name = f"DA_Kit_{trade}"
        path = f"{ROOT}/{name}"
        if EAL.does_asset_exist(path):
            log(f"OK   {name} exists -- left alone (designer edits win)")
            continue
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.IBClassKitData)
        da = AT.create_asset(name, ROOT, unreal.IBClassKitData, factory)
        if not da:
            log(f"FAIL {name} could not be created")
            continue
        kit = unreal.IBClassKit()
        kit.set_editor_property("kit_ability", kit_ability)
        kit.set_editor_property("movement_tool", movement)
        da.set_editor_property("operative_class", cls)
        da.set_editor_property("kit", kit)
        saved = EAL.save_asset(path)
        log(("OK   " if saved else "FAIL ") + f"{name} created ({kit_ability.get_editor_property('display_name')} / {movement.get_editor_property('display_name')})")
except Exception:
    log("FAIL exception")
    unreal.log_error(traceback.format_exc())
log("=== class kit assets done ===")
