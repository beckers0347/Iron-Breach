"""
Iron Breach — menus content pass, scripted (MENUS_UI_WIRING §3, §5, §6).
Runs headless: UnrealEditor-Cmd -run=pythonscript. Creates the player
state/controller BPs, menu input actions + IMC, the six menu WBPs, starter
items, and wires every class default. Idempotent: existing assets are reused.
Every step logs IBPY lines; failures print and continue so one bad step
doesn't strand the rest.
"""
import traceback
import unreal

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary

ROOT = "/Game/IronBreach"
DIRS = [ROOT, f"{ROOT}/Core", f"{ROOT}/UI", f"{ROOT}/Items", f"{ROOT}/Input", f"{ROOT}/Maps"]

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

def ensure_dirs():
    for d in DIRS:
        if not EAL.does_directory_exist(d):
            EAL.make_directory(d)

def create_bp(path, name, parent):
    full = f"{path}/{name}"
    if EAL.does_asset_exist(full):
        return EAL.load_asset(full)
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent)
    return AT.create_asset(name, path, unreal.Blueprint, factory)

def create_wbp(path, name, parent):
    full = f"{path}/{name}"
    if EAL.does_asset_exist(full):
        return EAL.load_asset(full)
    factory = unreal.WidgetBlueprintFactory()
    factory.set_editor_property("parent_class", parent)
    return AT.create_asset(name, path, unreal.WidgetBlueprint, factory)

def create_data_asset(path, name, klass):
    full = f"{path}/{name}"
    if EAL.does_asset_exist(full):
        return EAL.load_asset(full)
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", klass)
    return AT.create_asset(name, path, klass, factory)

def make_key(key_name):
    k = unreal.Key()
    k.set_editor_property("key_name", key_name)
    return k

def cdo(bp):
    return unreal.get_default_object(bp.generated_class())

def try_compile(bp):
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    except Exception:
        pass  # older API surface; CDO edits + save still persist

# ---------------- run ----------------
log("=== menu asset pass starting ===")
step("folders", ensure_dirs)

# §3.1/3.2 — player state + controller BPs
bp_ps = step("BP_IBPlayerState", lambda: create_bp(f"{ROOT}/Core", "BP_IBPlayerState", unreal.IBPlayerState))
bp_pc = step("BP_IBPlayerController", lambda: create_bp(f"{ROOT}/Core", "BP_IBPlayerController", unreal.IBPlayerController))

# §6.1 — input actions
ia = {}
for short in ["Inventory", "Map", "Ledger", "System"]:
    ia[short] = step(f"IA_Menu_{short}", lambda s=short: create_data_asset(f"{ROOT}/Input", f"IA_Menu_{s}", unreal.InputAction))

# §6.2 — mapping context + keys
def build_imc():
    imc = create_data_asset(f"{ROOT}/Input", "IMC_Menus", unreal.InputMappingContext)
    if len(imc.get_editor_property("mappings")) == 0:
        pairs = [("Inventory", "I"), ("Inventory", "Tab"), ("Map", "M"),
                 ("Ledger", "L"), ("System", "Escape"),
                 ("System", "Gamepad_Special_Right"), ("Map", "Gamepad_Special_Left")]
        for short, key in pairs:
            if ia.get(short):
                imc.map_key(ia[short], make_key(key))
    return imc
imc = step("IMC_Menus + mappings", build_imc)

# §6.3 — controller defaults
def wire_controller():
    c = cdo(bp_pc)
    c.set_editor_property("menu_mapping_context", imc)
    c.set_editor_property("open_inventory_action", ia["Inventory"])
    c.set_editor_property("open_map_action", ia["Map"])
    c.set_editor_property("open_ledger_action", ia["Ledger"])
    c.set_editor_property("open_system_action", ia["System"])
    try_compile(bp_pc)
if bp_pc and imc:
    step("controller defaults (IMC + 4 actions)", wire_controller)

# §5 — the six widgets (C++ parents drive everything; trees start bare)
wbp_tile   = step("WBP_ItemTile", lambda: create_wbp(f"{ROOT}/UI", "WBP_ItemTile", unreal.IBItemTileWidget))
wbp_inv    = step("WBP_InventoryScreen", lambda: create_wbp(f"{ROOT}/UI", "WBP_InventoryScreen", unreal.IBInventoryScreen))
wbp_ledger = step("WBP_LedgerScreen", lambda: create_wbp(f"{ROOT}/UI", "WBP_LedgerScreen", unreal.IBLedgerScreen))
wbp_map    = step("WBP_MapScreen", lambda: create_wbp(f"{ROOT}/UI", "WBP_MapScreen", unreal.IBMapScreen))
wbp_marker = step("WBP_MapMarker", lambda: create_wbp(f"{ROOT}/UI", "WBP_MapMarker", unreal.IBMapMarkerWidget))
wbp_system = step("WBP_SystemScreen", lambda: create_wbp(f"{ROOT}/UI", "WBP_SystemScreen", unreal.IBSystemScreen))

def set_class_prop(bp, prop, klass_bp):
    c = cdo(bp)
    c.set_editor_property(prop, klass_bp.generated_class())
    try_compile(bp)
if wbp_inv and wbp_tile:
    step("Inventory.GridTileClass", lambda: set_class_prop(wbp_inv, "grid_tile_class", wbp_tile))
if wbp_ledger and wbp_tile:
    step("Ledger.GridTileClass", lambda: set_class_prop(wbp_ledger, "grid_tile_class", wbp_tile))
if wbp_map and wbp_marker:
    step("Map.MarkerClass", lambda: set_class_prop(wbp_map, "marker_class", wbp_marker))

# §3.4 — starter items (the loot->gun seam proof + a stackable material)
def build_rifle_item():
    item = create_data_asset(f"{ROOT}/Items", "DA_Item_AssaultRifle", unreal.IBItemDefinition)
    item.set_editor_property("display_name", "Service Rifle")
    item.set_editor_property("description", "Standard Defense Force issue. It has never jammed when it mattered, which is the highest praise a rifle gets.")
    item.set_editor_property("category", unreal.IBItemCategory.WEAPON)
    item.set_editor_property("rarity", unreal.IBItemRarity.COMMON)
    item.set_editor_property("equip_slot", unreal.IBEquipSlot.WEAPON_PRIMARY)
    item.set_editor_property("base_clearance_rating", 10)
    wd = EAL.load_asset("/Game/Weapons/Rifle/DA_AssultRifle")
    if wd:
        item.set_editor_property("weapon_data", wd)
    return item

def build_chitin_item():
    item = create_data_asset(f"{ROOT}/Items", "DA_Item_KaijuChitin", unreal.IBItemDefinition)
    item.set_editor_property("display_name", "Kaiju Chitin")
    item.set_editor_property("description", "Plate fragments recovered from a kill. The Foundry pays in clearance for every kilogram.")
    item.set_editor_property("category", unreal.IBItemCategory.KAIJU_MATERIAL)
    item.set_editor_property("rarity", unreal.IBItemRarity.UNCOMMON)
    item.set_editor_property("max_stack", 99)
    return item

item_rifle  = step("DA_Item_AssaultRifle", build_rifle_item)
item_chitin = step("DA_Item_KaijuChitin", build_chitin_item)

def wire_player_state():
    c = cdo(bp_ps)
    loadout = [i for i in [item_rifle, item_chitin] if i]
    c.set_editor_property("starter_loadout", loadout)
    try_compile(bp_ps)
if bp_ps:
    step("PlayerState.StarterLoadout", wire_player_state)

# §3.3 — GameMode assignments
def wire_gamemode():
    gm = EAL.load_asset("/Game/BP_IronBreachGameMode")
    c = cdo(gm)
    c.set_editor_property("player_state_class", bp_ps.generated_class())
    c.set_editor_property("player_controller_class", bp_pc.generated_class())
    try_compile(gm)
    EAL.save_asset("/Game/BP_IronBreachGameMode")
if bp_ps and bp_pc:
    step("GameMode PlayerState+PlayerController classes", wire_gamemode)

step("save /Game/IronBreach", lambda: EAL.save_directory(ROOT, recursive=True))
log("=== menu asset pass complete ===")
