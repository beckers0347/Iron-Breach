"""
Iron Breach — loot content pass (closes the demo loot loop).
Runs headless: UnrealEditor-Cmd -run=pythonscript. Creates the second weapon
item (Amethyst Arc, the Special slot) and the Class-D loot table that the
native kaiju/enemy LootDropComponent falls back to. Idempotent: existing
assets are reused and re-wired. IBPY log lines per step.
"""
import traceback
import unreal

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary

ROOT = "/Game/IronBreach"
ITEMS = f"{ROOT}/Items"

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

def create_data_asset(path, name, klass):
    full = f"{path}/{name}"
    if EAL.does_asset_exist(full):
        return EAL.load_asset(full)
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", klass)
    return AT.create_asset(name, path, klass, factory)

log("=== loot asset pass starting ===")

if not EAL.does_directory_exist(ITEMS):
    EAL.make_directory(ITEMS)

# ---- 1. Amethyst Arc: the second weapon, fills the SPECIAL well ----
def make_amethyst():
    da = create_data_asset(ITEMS, "DA_Item_AmethystArc", unreal.IBItemDefinition)
    da.set_editor_property("display_name", "Amethyst Arc")
    da.set_editor_property("description",
        "Prototype arc-discharge rifle. Foundry mark: Meridian. The coil sings "
        "a ninth of a second before it fires.")
    da.set_editor_property("flavor",
        "Recovered from the Drydock's sealed lockers. Nobody signed for it.")
    da.set_editor_property("category", unreal.IBItemCategory.WEAPON)
    da.set_editor_property("rarity", unreal.IBItemRarity.RARE)
    da.set_editor_property("equip_slot", unreal.IBEquipSlot.WEAPON_SPECIAL)
    da.set_editor_property("base_clearance_rating", 14)
    da.set_editor_property("max_stack", 1)
    wd = EAL.load_asset("/Game/Weapons/Rifle/Meshes/Amethyst_Arc/DA_Amethyst_Arc")
    if wd:
        da.set_editor_property("weapon_data", wd)
        log("amethyst weapon_data wired")
    else:
        log("WARN DA_Amethyst_Arc not found — item created without weapon_data")
    return da

da_arc = step("DA_Item_AmethystArc", make_amethyst)

# ---- 2. Class-D loot table: chitin always, weapons on the roll ----
def entry(defn, weight=1.0, mn=1, mx=1, guaranteed=False):
    e = unreal.IBLootTableEntry()
    e.set_editor_property("definition", defn)
    e.set_editor_property("weight", weight)
    e.set_editor_property("min_count", mn)
    e.set_editor_property("max_count", mx)
    e.set_editor_property("guaranteed", guaranteed)
    return e

def make_table():
    chitin = EAL.load_asset(f"{ITEMS}/DA_Item_KaijuChitin")
    rifle = EAL.load_asset(f"{ITEMS}/DA_Item_AssaultRifle")
    if not chitin:
        raise RuntimeError("DA_Item_KaijuChitin missing — run ib_create_menu_assets.py first")

    table = create_data_asset(ITEMS, "DA_Loot_ClassD", unreal.IBLootTableAsset)
    entries = [entry(chitin, mn=1, mx=3, guaranteed=True)]
    if rifle:
        entries.append(entry(rifle, weight=3.0))
    if da_arc:
        entries.append(entry(da_arc, weight=1.0))
    table.set_editor_property("entries", entries)
    # Testing generosity: every kill pays out. Tune down before the demo if
    # weapon spam gets silly — guaranteed chitin is unaffected either way.
    table.set_editor_property("drop_chance", 1.0)
    table.set_editor_property("min_rolls", 1)
    table.set_editor_property("max_rolls", 1)
    log(f"table entries: {len(entries)}")
    return table

step("DA_Loot_ClassD", make_table)

step("save", lambda: EAL.save_directory(ROOT, only_if_is_dirty=False, recursive=True))
log("=== loot asset pass done ===")
