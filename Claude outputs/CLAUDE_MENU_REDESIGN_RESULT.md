# Claude menu redesign — implementation result (September 16, 2026)

Scope: the handoff in `Docs/CLAUDE_MENU_REDESIGN_HANDOFF.md`. Implemented against the current dirty
checkout; unrelated uncommitted work, gameplay state and saved data untouched. Nothing was compiled,
launched or committed from my side — Codex owns build, run, screenshots and any commit.

## What changed, in one paragraph

A shared chamfered-glass frame (`UIBGlassBorder`) now backs every native content panel through the
existing `IBHangar::Panel` / `IBMenuLayout::Card` entry points (signatures unchanged), plus preset
variants (Inset, Chip, Dossier, Plinth, Band). A painted line-art mark widget (`UIBMenuGlyph`)
replaces the Unicode diamond / bullets in the chrome (Breakwater insignia, cog, notch, diamond,
lock, search, target). The menu header is one slim band: insignia chip + callsign / `LV n CLASS`,
centered tab ring with a lit notch under the active tab, `CLEARANCE n` chip, `DIRECTOR [B]` /
`CHARACTER [I]` link, cog for Settings. Inventory, Ledger, Missions received their finishing pass
(category rails with lit accent edges and live counts, dossier inspectors with real art and glyph
fallback, recon rows with chamfered dossier, filter tabs). The preview stage frames the operative
full-body, only plays `MM_Idle` on a compatible skeleton (otherwise snapshots the pawn pose or holds
the reference pose) and mirrors the pawn's actual third-person weapon on the same socket.

## Exact file list

New files

- `Source/IronBreach/UI/IBGlassBorder.h` / `.cpp` — `FIBGlassStyle` presets + `UIBGlassBorder`
  (UBorder subclass, custom `SBorder::OnPaint`: cut-corner fill polygon, hairline edge, inset bevel
  line, top-left accent stroke, bottom-right tick, sheen; fill/edge come from the border's own brush
  and `BrushColor`, multiplied by the parent tint and the disabled state).
- `Source/IronBreach/UI/IBMenuGlyph.h` / `.cpp` — `UIBMenuGlyph` (UWidget + SLeafWidget) with
  `EIBMenuGlyph` Insignia / Diamond / Cog / Chevron / ChevronLeft / Search / Lock / Notch / Grid /
  Target / Check. Hit-test invisible, scales to its box.
- `Scripts/ib_import_kaiju_chitin_icon.py` — editor script (see "Chitin icon" below).
- `Docs/CLAUDE_MENU_REDESIGN_RESULT.md` — this file.

Modified files

- `Source/IronBreach/UI/IBMenuLayout.h` — `Card` builds a `UIBGlassBorder` (same signature; brush
  still `RoundedBrush(fill, 0, Line, 1)`). Includes `IBGlassBorder.h`.
- `Source/IronBreach/UI/IBHangarStyle.h` — `Panel` is glass (signature stable). Added `Edge()`,
  `Lit()`, `Fade()`, `Glass()`, `Inset()`, `Chip()`, `Dossier()`, `Plinth()`, `Glyph()`,
  `StyleRail()`, `StyleTab()`, `SectionTitle()`. Existing `Cyan/Ink/Label/StyleButton/Background/
  Frontend/Button/Rule/Stat` unchanged.
- `Source/IronBreach/UI/IBMenuScreen.h` / `.cpp` — `TabUnderlines` is now `TArray<TObjectPtr<UIBMenuGlyph>>`
  (private transient, not a BindWidget); slim header (`BuildMenuHeader`), tab ring with notch,
  identity from PlayerState only (callsign, level, class name in class color, clearance) — no XP
  bar. Hangar page body padding tightened; full-screen shade is a plain border (no hairline frame).
  Active-tab visibility toggling (Hidden / HitTestInvisible) preserved.
- `Source/IronBreach/UI/IBInventoryScreen.h` / `.cpp` — finished the partial pass: `FilterAccents`,
  `DetailCategory` members; rail rows (accent edge + glyph + label + live per-category counts);
  search inset with magnifier glyph; inspector = dossier frame with real icon / glyph fallback,
  rarity line, category · slot line, `CLEARANCE` or `QUANTITY` value block, stats, description,
  accent-colored frame; loadout plinth shows real CLEARANCE / EQUIPPED n / 8 / IN BACKPACK n; wells
  140x108; portrait scale 1.1; live weapon passed to the preview stage. Equip / unequip / select
  logic untouched. Labels the checks click (`INVENTORY`, `ALL ITEMS`, `ARMOR`, `SORT: RARITY`,
  `NOT EQUIPPABLE`, `EQUIP SELECTED ITEM`, widget name `InventorySearch`) kept.
- `Source/IronBreach/UI/IBItemTileWidget.cpp` — glyph fallback widget is created with the tile as
  owner (was owning player, which can be null while a tile initializes). No visual change.
- `Source/IronBreach/UI/IBLedgerScreen.h` / `.cpp` — defined the previously declared-but-missing
  `ShowDetails` and `HandleTileClicked` (link errors otherwise); hover-out returns to the kept
  record instead of the idle copy; rail with accent edges; dossier inspector with real icon / glyph
  fallback, `BASE CLEARANCE`, stats and sealed-record copy for undiscovered entries. Added members
  `DetailRatingLabel`, `DetailFooter`, `DetailFrame`, `FilterLabels`, `FilterAccents`.
- `Source/IronBreach/UI/IBMissionsScreen.cpp` — filter chips via `StyleTab`; recon rows framed by
  `StyleRow` (hairline / cyan when selected); diamond / lock glyph marks; objective target glyph;
  dossier frame for the briefing, inset frame for the recon still. ALL / OPERATIONS / PATROLS /
  TRAINING and `VIEW ON WATCH  >` routing unchanged.
- `Source/IronBreach/UI/IBFriendsScreen.cpp` — friends flyout and location card on glass frames.
- `Source/IronBreach/UI/IBReferenceMenuCheck.cpp` — `FindButton` walks up from a matching text
  block to its nearest `UButton` (same rule as `IB.MenuConsistencyCheck`), so rail rows whose label
  sits beside a glyph and a count are still found. Added `Components/PanelWidget.h`.
- `Source/IronBreach/Player/IBOperativePreviewStage.h` / `.cpp` — `ConfigureForInventory(Body,
  Weapon = nullptr)`; closer dead-center framing (lens -424 / target z 95, FOV 26); `ApplyIdlePose`
  plays `MM_Idle` only if `USkeleton::IsCompatibleMesh` (or same skeleton) says it fits, otherwise
  `CopyPoseFromSkeletalComponent` from the pawn body with animation paused, else reference pose;
  `SyncWeapon` mirrors `GetThirdPersonWeaponMesh()` (static mesh, materials, attach socket,
  relative transform, visibility) onto a transient `WeaponProp` shown only to the capture. The
  front-end select/create stage keeps its default framing; `ShowOperative` now routes through
  `ApplyIdlePose` too.

Untouched but restyled through the shared primitives: Skills, Map, System, Settings, operative
select / create, weapon rack (all build panels with `IBHangar::Panel` / `IBMenuLayout::Card`).
Watch keeps its own `UIBWatchCardBorder` and fullscreen geometry; title menu untouched.

## Behavior preserved (by inspection)

- Personal / Director groups, Q/E cycling, `DIRECTOR [B]` / `CHARACTER [I]` links, one-click
  Character, Character/Backpack alias routing — header logic unchanged apart from presentation.
- Named Watch widgets (`DirectorScene`, `WatchPlanet`, `WatchBriefingPanel`, `WatchDeployButton`)
  untouched.
- All inventory mutations still go through `RequestEquip` / `RequestUnequip`.
- No currencies, XP fractions, rewards, invented gear or armor. The header shows level and class
  from `AIBPlayerState`; clearance is `GetTotalClearanceRating()`.

## Compile hotspots to look at first

Nothing here was compiled. If UBT complains, these are the most likely lines:

1. `IBGlassBorder.cpp` `UIBGlassBorder::PushStyle` reads the public `Background` brush
   (`TintColor`, `OutlineSettings`) and `GetBrushColor()` and pushes them to the Slate border, so no
   SBorder accessor is assumed. If `Background` direct access only warns as deprecated, ignore it;
   if it errors, swap in whatever brush getter 5.8 exposes at that one spot. A runtime
   `SetBrush` / `SetBrushColor` on a glass panel needs a `SynchronizeProperties()` call afterwards
   (no current caller does this).
2. `IBOperativePreviewStage.cpp` `ApplyIdlePose` uses `USkeleton::IsCompatibleMesh(const USkeletalMesh*)`
   (`Animation/Skeleton.h`). Replace with a plain `ClipSkeleton == Body->GetSkeleton()` test if the
   API moved.
3. `CopyPoseFromSkeletalComponent` takes a non-const pointer; the call `const_cast`s the source
   body (read-only use).
4. `UIBMenuGlyph` / `UIBGlassBorder` are new UCLASSes: UHT must regenerate; generated headers are last.
5. `IBHangarStyle.h` now includes `IBGlassBorder.h` and `IBMenuGlyph.h`; every cpp including it
   pulls the two new headers (no circular includes).

## Verification steps for Codex

1. Build the editor target; fix anything from the list above.
2. `IB.ReferenceMenuCheck` — expects INVENTORY tab, `ARMOR` / `ALL ITEMS` rail rows, `SORT:` cycling,
   `NOT EQUIPPABLE` on an empty search, `DIRECTOR  [B]`, `MISSIONS`, `TRAINING`, `VIEW ON WATCH  >`,
   `CHARACTER  [I]`, and one preview stage on Character / none on Backpack.
3. `IB.MenuConsistencyCheck` and `IB.MenuFlowCheck -IBMenuConsistencyAfterDeploy -IBMenuFlowAfterMenus`
   — real clicks on tab labels; tabs are still the button's direct text content.
4. Inspect `Saved/ReferenceMenus/after/character.png`: operative should fill most of the sheet height
   with weapon wells left / armor wells right and the loadout plinth at the feet; `inventory.png`:
   rail + grid + dossier; `missions.png`: recon rows + dossier.
5. Run `Scripts/ib_import_kaiju_chitin_icon.py` with `UnrealEditor-Cmd ... -run=pythonscript
   -script=... -SCCProvider=None`. It imports `Art/MenuSources/kaiju-chitin-v1.png` as
   `/Game/Items/Icons/Generated/T_Icon_KaijuChitin` and sets only the Icon of the single
   `UIBItemDefinition` whose asset name contains "KaijuChitin" and whose category is Kaiju Material;
   it aborts without changes on zero or several candidates.

## Known limits / not done

- No new item or armor art was created; items without an `Icon` show the category glyph in their
  rarity color (tiles, inspectors) until real icons land. Rifle_C / ArmCannon still have no icons.
- The reference's currency chips, XP bar, mission rewards/objective checklists and "TRACK" have no
  backing data and are not shown.
- Skills / Map / System / Settings / select / create / rack only received the shared frame and
  header; no per-screen layout rework beyond that.
- Line endings: files that were CRLF (or mixed after the earlier partial edits) are written CRLF
  throughout; LF files stay LF; new C++ files are CRLF, the script and this doc LF.
