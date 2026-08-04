# Menus & Inventory — Pass 1 (M2 spine: inventory · ledger · map)

*2026-08-03 · by Claude (Fable 5) · roadmap M2 "Loot & progression spine" + "director map UI"*

Destiny's menu grammar in Iron Breach terms: a character/inventory screen with equipment wells and a Clearance Rating, **the Ledger** (Collections — named from the design docs' "collectible ledger"), a pannable/zoomable **zone map** with live POI pins and a player pip, and a **system screen** on Escape (resume / leave session / quit). One key opens each; Q/E and shoulders cycle between them; Escape drops back to the game. Menu input lives on a new **project PlayerController** so menus open while dead and from inside a mech. And the spine now has a faucet: **loot drops** — kill something carrying a loot table and rarity-lit pickups hit the ground.

Everything follows the house rules: clients request / the server decides / replication informs (inventory is a replicated fast-array on a new `AIBPlayerState`); C++ decides truth, BP skins it (every screen is an `Abstract` C++ base Shane children into WBPs); cross-system delivery is signals-only (`OnMenuOpened`, `OnEquipmentChanged`, `OnPOIActivated` — the ZoneConfirmed pattern).

## File map

| New | What |
|---|---|
| `Items/IBItemTypes.h` | Categories/rarity/equip-slot enums, `FIBItemInstance`, fast-array list |
| `Items/IBItemDefinition.h` | `DA_Item_*` schema (icon, rarity, slot, stats, optional `WeaponData` link) |
| `Items/IBInventoryComponent.*` | Replicated inventory + equipment; request seam (`RequestEquip/Unequip`) |
| `Items/IBLedgerSubsystem.*` | Discovery set + save slot + full catalog via Asset Manager |
| `Items/IBPlayerState.*` | Hosts the inventory; grants `StarterLoadout` server-side |
| `Items/IBLootTableAsset.h` | `DA_Loot_*` schema: weighted entries, guaranteed lines, roll logic |
| `Items/IBLootDropComponent.*` | Drop on any enemy/kaiju → its death rolls the table **per eligible player** (contributors or all; pickups or direct) |
| `Items/IBLootPickup.*` | The engram: replicated, rarity-lit, **per-player** — only the owner sees or collects it; ownerless = shared/hand-placed |
| `Player/IBPlayerController.*` | Project PC: menu input home — survives death and the infantry↔mech swap |
| `UI/IBUISettings.h` | Project Settings > **Iron Breach UI**: screen registry, hotkeys, rarity palette |
| `UI/IBMenuSubsystem.*` | LocalPlayer subsystem: open/close/cycle, input mode, open/close signals |
| `UI/IBMenuScreen.*` | Screen base: close/cycle/hotkey handling (menus run UI-only input) |
| `UI/IBSystemScreen.*` | Escape's screen: Resume / Leave to Main Menu / Quit (buttons are yours) |
| `UI/IBItemTileWidget.*` | The one item square: grid cell, equipment well, ledger silhouette |
| `UI/IBInventoryScreen.*` | Wells + Clearance + category-filtered grid; click-to-equip |
| `UI/IBLedgerScreen.*` | Catalog grid, discovered vs silhouette, per-category progress |
| `UI/IBMapScreen.*` + `UI/IBMapMarkerWidget.*` | Pan/zoom map, pins, player pip, select→deploy |
| `World/IBMapTypes.h` | `DA_Map_*` schema: texture + world rect + UV projection |
| `World/IBMapPOIComponent.*` | Drop on any actor → it's a pin (self-registers) |
| `World/IBMapZoneInfo.*` | One per level; points the world at its map asset |
| `World/IBMapSubsystem.*` | POI/zone registry + `OnPOIActivated` deploy signal |

| Patched | Change |
|---|---|
| `IronBreach.Build.cs` | + `Slate`, `SlateCore`, `DeveloperSettings`, `NetCore` |
| `Infantry/IBCharacter_Infantry.*` | Additive only, all pre-existing UPROPERTY names untouched: binds to the PlayerState inventory and swaps `CurrentWeaponData`/ADS when Primary changes (the loot→gun seam, live on every machine via replication). Menu input deliberately does NOT live here — see `Player/` |
| `Online/IBSessionSubsystem.*` | + `IBLeave()` (console `IBLeave` works too): destroys/unregisters the session — host or client — then travels to `LeaveTravelURL` (the main-menu map). Existing Host/Join untouched |
| `Combat/HealthComponent.*` | Additive: server-only **damage-contributor tracking** (every controller that hurt this thing, first-hit order). Feeds per-player loot eligibility now; assists/aggro/scoreboards get it free later. Nothing replicates — same rule as the OnDeath killer |

## 1. Apply + build (Claude Code / Connor)

1. Pull first (conventions §7), then copy the bundle's `Source/` and `Docs/` over the project root at `D:\Unreal Games\IronBreach`. Four files **overwrite on purpose**: `IronBreach.Build.cs`, `Infantry/IBCharacter_Infantry.h/.cpp`, `Online/IBSessionSubsystem.h/.cpp`, and `Combat/HealthComponent.h/.cpp` (all patched from today's `main` — additive only; if Shane pushed changes to those files since, diff before copying).
2. **New folders exist (`Items/`, `UI/`, `World/`, `Player/`)** → right-click `IronBreach.uproject` → **Generate Visual Studio project files** (same as the `Online/` folder last time).
3. Ritual §6.1: close editor → delete `Binaries/Win64` → launch `.uproject` → accept rebuild.

## 2. Asset Manager (one-time, 2 minutes — Connor or Shane)

Project Settings → **Asset Manager** → Primary Asset Types to Scan → add two rows:

| Primary Asset Type | Asset Base Class | Directories | Rules |
|---|---|---|---|
| `IBItem` | `IBItemDefinition` | `/Game/IronBreach/Items` | Apply Recursively ✓ |
| `IBMapZone` | `IBMapZoneData` | `/Game/IronBreach/Maps` | Apply Recursively ✓ |

Type strings must be exactly `IBItem` / `IBMapZone`. Without the `IBItem` row the Ledger logs a warning and shows an empty catalog — that warning is your breadcrumb back here.

## 3. GameMode → PlayerState + PlayerController (Shane — GameMode content is yours, §3)

1. Content Browser → Blueprint Class → parent `IBPlayerState` → `BP_IBPlayerState` in `Content/IronBreach/Core/`.
2. Blueprint Class → parent `IBPlayerController` → `BP_IBPlayerController`, same folder. (Menu keys live on the controller — it's the one player object that survives death AND the future infantry↔mech possession swap, so the map opens from a mech seat and from the respawn wait. If you had controller-BP logic planned, this child is its home.)
3. `BP_IronBreachGameMode` → Class Defaults → **Player State Class = BP_IBPlayerState**, **Player Controller Class = BP_IBPlayerController**.
4. In `BP_IBPlayerState` defaults, fill **Starter Loadout** with a few `DA_Item_*` (make one Weapon item whose `WeaponData` points at your existing rifle DA — that's the end-to-end proof). `bAutoEquipStarters` stays on.

If the inventory screen ever comes up empty with a log line about Player State Class — it's step 3. If no key opens any menu and the log says MenuMappingContext not assigned — that's §6.

## 4. Screen registry (Project Settings → Game → **Iron Breach UI**)

Add four rows to **Screens**, in this order (order = Q/E cycle order):

| ScreenId | TabLabel | WidgetClass | Hotkeys |
|---|---|---|---|
| `Inventory` | Inventory | `WBP_InventoryScreen` | I, Tab |
| `Ledger` | Ledger | `WBP_LedgerScreen` | L |
| `Map` | Map | `WBP_MapScreen` | M |
| `System` | System | `WBP_SystemScreen` | *(leave empty)* |

ScreenIds are what the C++ opens (`Inventory`/`Ledger`/`Map`/`System` exactly). Hotkeys here are the **in-menu** jump/toggle keys — keep them matching the IA mappings in §6 so one key means one thing everywhere. System's stays empty on purpose: in-menu, Escape is the universal *close* key (screens check close before hotkeys), and in-game it opens System via the controller's IA — same key, sane meaning in both worlds. Rarity palette lives on this same page; the defaults are a service-metal ramp up to Relic amber — make it yours.

## 5. The WBPs (Shane — HUD/UI is yours, §3)

All in `Content/IronBreach/UI/`. C++ drives anything named exactly as below (all optional binds — add what you want, skip what you don't); layout, style, and animation are entirely yours. Hook `On Screen Opened/Closed` for transitions.

**WBP_ItemTile** (parent `IBItemTileWidget`) — used by every grid and well:
`IconImage` (Image) · `StackText` (TextBlock) · `RarityBorder` (Border). C++ sets icon, stack, rarity frame color, and blacks the icon out for undiscovered ledger entries. `On Tile Updated` fires after every change for extra styling.

**WBP_InventoryScreen** (parent `IBInventoryScreen`):
- `ItemGrid` (Uniform Grid Panel) — the backpack. Set **Grid Tile Class = WBP_ItemTile** in class defaults.
- Equipment wells: place eight WBP_ItemTile instances named `Tile_WeaponPrimary`, `Tile_WeaponSpecial`, `Tile_WeaponHeavy`, `Tile_ArmorHead`, `Tile_ArmorChest`, `Tile_ArmorArms`, `Tile_ArmorLegs`, `Tile_GearAntiKaiju` (Destiny layout: weapons down the left, armor down the right).
- `ClearanceText` (TextBlock) — the big Clearance Rating number.
- Category tabs: your buttons → **Set Category Filter** (Weapon/Armor/Splice/…).
- Details pane: build it your way, feed it from `On Item Focused` (item + bEquipped) / `On Item Unfocused`.
- Interaction is already live: click backpack item → equips; click a filled well → unequips.

**WBP_LedgerScreen** (parent `IBLedgerScreen`): `ItemGrid` + `ProgressText` ("12 / 48 CATALOGUED"), Grid Tile Class again, category tabs → **Set Category Filter**, detail pane from `On Entry Focused` — style undiscovered as **DATA SEALED** (bDiscovered=false: no flavor text, keep the chase honest).

**WBP_MapScreen** (parent `IBMapScreen`):
```
[Overlay filling the screen, Clipping = Clip to Bounds]
  └─ SizeBox — Width/Height Override 2048×2048, alignment CENTERED
       └─ MapCanvas (Canvas Panel)
            └─ MapImage (Image, anchors 0→1, offsets 0)
  └─ PlayerMarkerImage (Image, ~24px, give it a pip brush — C++ re-parents it onto the canvas and moves it)
  └─ ZoneNameText (TextBlock, header)
```
The SizeBox matters twice: a bare Canvas Panel has no desired size (it would collapse or stretch to the screen, and pin math assumes 2048² — match **Map Canvas Size** if you change it), and *centered* is what the cursor-centered zoom math assumes. Off-center won't break anything, the zoom focus just drifts.

Set **Marker Class = WBP_MapMarker**. Drag/wheel pan-zoom (pan is clamped — you can't fling the map away), pin selection, and the live player pip are all C++. Build a POI info card off `On POI Selected` with a Deploy button → **Activate Selected POI**; right-click on empty map (or `On POI Deselected`) dismisses it.

**WBP_MapMarker** (parent `IBMapMarkerWidget`): `IconImage` + `Label`, fill the **Type Icons** map in class defaults (Mission/Vendor/FastTravel/KaijuAlert…). `On Marker Updated` is where KaijuAlert gets its throb.

**WBP_SystemScreen** (parent `IBSystemScreen`): no bound names — it's all buttons, and buttons are yours. Wire clicks to the three BlueprintCallables: **Resume Game**, **Leave To Main Menu**, **Quit To Desktop**. Use **Is In Networked Session** to hide/relabel Leave when solo. Leave a visual slot for a Settings panel — the screen gains it later with zero C++ churn. Design note: this is a menu, not a pause — the co-op world keeps running behind it, so keep it visually light (Destiny's approach, not a full-screen blackout).

## 6. Input (Shane — IA/IMC are yours, §3)

Menu input lives on **`BP_IBPlayerController`**, not the infantry pawn — that's why the map opens while you're dead or in a mech seat.

1. Four Input Actions in `Content/IronBreach/Input/`: `IA_Menu_Inventory`, `IA_Menu_Map`, `IA_Menu_Ledger`, `IA_Menu_System` (all Digital/bool).
2. New mapping context **`IMC_Menus`** (its own asset — don't fold these into `IMC_Default`; the controller adds it at priority 1 so menu keys win over any pawn's context): I → Inventory, M → Map, L → Ledger, **Escape → System** (Tab on Inventory too if you like — mirror whatever you choose into §4's Hotkeys). Gamepad: Menu/Start → System, View/Select → Map.
3. `BP_IBPlayerController` class defaults → **Menu Mapping Context = IMC_Menus** + assign the four **Open … Action** slots.

These actions only *open* menus. In-menu keys (Escape close, Q/E + shoulders cycle, hotkey jumps) are handled by the screens themselves because menus run UI-only input mode — don't rebuild them in BP. Escape is deliberately double-duty: in-game it opens System (controller IA); in-menu it closes (screen CloseKeys) — one key, both directions.

## 7. Map data + pins

1. Capture: in Lvl_Plains run `BugItGo 0 0 150000 -89 0 0` (the known top-down recipe), high-res screenshot, crop square, import to `Content/IronBreach/Maps/T_Map_Carrow`. A SceneCapture2D ortho pass can replace it later — same asset slot, nothing else changes.
2. Data asset: right-click → Miscellaneous → Data Asset → **IBMapZoneData** → `DA_Map_Carrow`. ZoneName "Carrow Exclusion Zone", the texture, and the world rect (2 km centered on origin = Min −100000,−100000 / Max 100000,100000 — check the landscape's actual bounds). Pins mirrored? Flip `bFlipU`/`bFlipV`, no math.
3. Place an **IBMapZoneInfo** actor in Lvl_Plains, assign `DA_Map_Carrow`. (OFPA: it's one tiny actor file, MU-friendly.)
4. Add **IBMapPOIComponent** to anything that should pin: the village (Vendor), a spawn pad (FastTravel), BP_Kaiju_Palawan (KaijuAlert — a Class C on the map on day one is a statement). Name, type, done.

**Deploy semantics:** the map itself decides nothing. `UIBMapSubsystem.OnPOIActivated` fires with the pin; fast travel, mission launch, and the future event director each listen for their types. First consumer (fast travel) is a ~20-line listener — flagged for next pass, deliberately not smuggled into this one.

## 8. Loot: table → pickup BP → drop components (Shane)

The faucet — **per-player instanced**, Destiny-style: every eligible player rolls the table independently and gets their own drops. Your drops are invisible and untouchable to everyone else; no ninja-looting, ever. Three assets and it's alive:

1. **Loot table:** right-click → Misc → Data Asset → **IBLootTableAsset** → `DA_Loot_ClassD` in `Content/IronBreach/Items/`. Entries: your KaijuMaterial item with **bGuaranteed** ✓ (chitin always comes off the kill), plus the weapon/armor items as weighted rolls (Weight 1 each to start; DropChance 1 while testing so every kill pays out — tune down later). One table per enemy *family*, not per enemy.
2. **Pickup BP:** Blueprint Class → parent `IBLootPickup` → `BP_LootPickup`. Add a mesh (crystal/canister/whatever an engram is in Breakwater kit), a point light, Niagara if you have it — all under the root, beside the CollectionSphere. Hook **On Loot Initialized**: it hands you the item definition, count, and the **rarity color already resolved from settings** — pipe that into the light/material so a Relic drop reads amber from across the field. Movement (bob + spin) is already C++.
3. **Wire the dead things:** open `BP_Enemy_*` and the kaiju BPs → Add Component → **IBLootDrop** → assign the table + **Pickup Class = BP_LootPickup**. Same drill as the map POI component — level/content side, add freely.

Two knobs on the component, both defaulting to the Destiny answer:

- **Eligibility:** *Damage Contributors* (default — you rolled if you hurt it, tracked server-side by HealthComponent; falls back to everyone if the set is empty, so scripted/environmental kills never void loot) or *All Players* (co-op generosity — right for story beats and event completion rewards).
- **Delivery:** *Physical Pickups* (default — each player's own rarity-lit ring; every ring occupies the same spots but they're mutually invisible, so it just reads as "my drops") or *Direct Grant* (straight into each eligible inventory — mission rewards, things that shouldn't sit on the ground).

Physical-with-no-PickupClass falls back to direct grant and logs, so loot is never silently eaten. Collection feedback: the collecting player's machine fires the inventory's `OnItemGranted` — that's the loot-toast hook, no pickup-side FX plumbing needed. **Shared pickups still exist** when you want them: hand-place a `BP_LootPickup` in a level (no owner) and it's visible to all, first-come — chest/cache behavior for free.

## 9. Test plan

**Solo PIE (7 min):** I opens inventory → starter items on the grid, Clearance sums, wells filled; click a second weapon → viewmodel/ADS swap (loot→gun end-to-end); Q/E cycles Inventory→Ledger→Map→System; Ledger shows starters discovered + everything else silhouetted; M → Carrow map, drag/wheel, pip tracks you, click the Palawan pin → info card → Deploy logs `[Map] POI activated`; right-click empty map → card dismisses. **Kill an enemy carrying the loot component → pickups scatter in a ring, lit by rarity → walk over one → toast fires, it's in the inventory, Ledger discovers it.** **Escape → System screen; Escape again → closes; Resume works; Quit works.** Escape while DEAD (during the respawn wait) → System still opens: that's the controller earning its keep. Then Escape → clean return, no stuck cursor, no stuck WASD.

**Listen server, 2 players:** client equips → **server window's** view of that player fires correct shots (server-authoritative weapon data — the real test); second client's ledger stays independent; respawn → weapon survives (PlayerState outlives the pawn — the reason inventory lives there). **Both players shoot one enemy → BOTH get their own drops; each window shows only its own ring (the host must NOT see the client's pickups — that's the listen-host visibility filter working); host walks through the client's drop spot → nothing happens; client collects → client toast, client inventory.** Client opens System → Leave to Main Menu → client lands in Lvl_MainMenu, host keeps playing; client can IBJoin back in (drop-in is on). **After any leave-and-rejoin (or host: leave → IBHost again): press Tab — the inventory must open cleanly. That exact sequence used to touch a dead cached widget; it's the regression test for the menu-cache purge.**

## 10. If the compiler complains

Written without a local build; likeliest friction, in order:

- `FFastArraySerializer` unresolved → confirm `NetCore` landed in Build.cs and project files were regenerated (step 1.2 — new folders make this mandatory, not optional).
- `OnPlayerStateChanged` override mismatch → 5.8 signature should be `(APlayerState*, APlayerState*)`; if UHT disagrees, check `APawn::OnPlayerStateChanged` in the engine source and match it exactly.
- `SetIsFocusable` deprecation gripes → engine drift; swap to whatever `UUserWidget` accessor 5.8 wants (worst case: `bIsFocusable = true;` with the deprecation pragma noted).
- `SetNetUpdateFrequency` missing on 5.8 → use `NetUpdateFrequency = 10.0f;` in the `AIBPlayerState` constructor instead.
- Linker on `UIBItemDefinition::PrimaryAssetType` → the inline definition at the bottom of `IBItemDefinition.h` must have survived the copy.
- `bOnlyRelevantToOwner` access — it's written as the public member on purpose (setter names drifted across versions); if 5.8 has privatized it, use whatever accessor the deprecation message names.
- `GetPlayerState<T>` template unresolved in the loot files → include order; `GameFramework/Pawn.h` + `GameFramework/Controller.h` are both in `IBLootDropComponent.cpp`, confirm they survived.
- `AddOnDestroySessionCompleteDelegate_Handle` signature drift → same interface family as the Create/Find/Join handles right above it in `IBSessionSubsystem.cpp`; match whatever 5.8's `IOnlineSession` header declares.
- `SetReplicatingMovement` deprecated-in-favor-of-something → it's a plain bool underneath; use the replacement setter or `bReplicateMovement = false` per the deprecation note.

## 11. Known gaps (deliberate, next passes)

1. **Weapon slot switching** — Primary is the live gun; Special/Heavy equip and replicate but don't swap in-hand yet (needs scroll/1-2-3 input + HUD grammar; small, own PR).
2. **No fast-travel/mission consumer** of `OnPOIActivated` yet (§7).
3. **Loot delivery exists; the drop *generator* doesn't** — instances copy `BaseClearanceRating` flat and tables are hand-weighted. Rarity-tier weighting, stat variance, and Clearance-relative scaling are M2 §3.3 proper, layering on top of `IBLootTableAsset` (not replacing it).
4. **Contributor tagging is binary and lifetime-long** — one bullet at any point makes you loot-eligible; no damage thresholds, no decay. Fine at squad scale; a public-event "tag it once for the payout" meta is a tuning problem for the event director era (thresholds slot into `GetDamageContributors` consumers, not the tracker).
5. **Per-player drops cost per-player actors at scale** — N players × M drops server-side (bandwidth stays flat via owner-only relevancy; host-side actor count doesn't). Irrelevant at 4 players; revisit if public events ever mean 20.
6. **System screen has no Settings panel** — the slot exists in the layout, the content (what settings?) doesn't yet. Audio sliders + sensitivity is the natural first page.
7. **Host leaving ends the session for everyone** — listen-server reality (ADR-002). Host migration is a dedicated-server-era problem; the System screen copy should just be honest about it ("End Session" when hosting).
8. **Splice sockets** — Splices exist as items; socketing into armor is its own system (design first: "socketed by armor quality").
9. **Ledger saves locally** (per machine). Cloud profile (EOS Player Data Storage, roadmap) swaps the backend inside `UIBLedgerSubsystem` only.
10. **Gamepad in-menu navigation** is coarse (shoulders/B work; no analog cursor). Fine until the PVP/console pass.
11. **Director zone-select layer** — this map is single-zone by design; the destination browser stacks on top when Zone 2 exists.
12. Vendor/bounty screens — same `UIBMenuScreen` base, add rows to settings when they exist.

## Signals now available (Shane's hookup menu)

`UIBMenuSubsystem.OnMenuOpened/OnMenuClosed` — HUD dim, weapon lower, **the menu hum** (the roadmap's Long Nine at 1/100× finally has its attach point) · `UIBInventoryComponent.OnItemGranted` — loot toast · `.OnEquipmentChanged` — HUD ammo/weapon card · `UIBLedgerSubsystem.OnEntryDiscovered` — "NEW ENTRY" flourish · `UIBMapSubsystem.OnPOIActivated` — deploy/fast-travel/mission launch.
