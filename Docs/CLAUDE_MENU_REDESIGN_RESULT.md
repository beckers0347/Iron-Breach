# Claude menu redesign — implementation result (September 16–19, 2026)

Scope: the handoff in `Docs/CLAUDE_MENU_REDESIGN_HANDOFF.md`, then Connor's September 17 decisions
(pass 2, below). Implemented against the current dirty checkout; unrelated uncommitted work, gameplay
state and saved data untouched. Nothing was compiled, launched or committed from my side — Codex owns
build, run, screenshots and any commit.

State of the tree on September 19: pass 1 + its corrections + pass 2 are all written. The only build
so far (`Saved/ReferenceArtPass/build-claude.log`, September 16) failed on exactly one error, the
C2039 fixed in "Corrections" below; every other translation unit in that build compiled. Pass 2 has
not been compiled by anyone yet — start with "Pass 2 — compile hotspots".

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
full-body, only plays `MM_Idle` on a compatible skeleton (otherwise runs the pawn's own animation
class, else holds the reference pose) and mirrors the pawn's actual third-person weapon on the same
socket.

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
  runs the pawn's own animation class on the copied mesh, else the reference pose (see
  "Corrections" below); `SyncWeapon` mirrors `GetThirdPersonWeaponMesh()` (static mesh, materials,
  attach socket, relative transform, visibility) onto a transient `WeaponProp` shown only to the
  capture. The front-end select/create stage keeps its default framing; `ShowOperative` now routes
  through `ApplyIdlePose` too.

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

## Corrections after the first build (September 17)

Codex's build log (`Saved/ReferenceArtPass/build-claude.log`) reported one error: C2039
`CopyPoseFromSkeletalComponent` is not a member of `USkeletalMeshComponent` in 5.8. Fixed, plus the
two follow-ups Codex asked for:

- `IBOperativePreviewStage.cpp` `ApplyIdlePose` no longer snapshots a pose. Order is now:
  1. `MM_Idle` as a single-node animation when `USkeleton::IsCompatibleMesh` (or the same skeleton)
     says the clip fits the body — that line compiled in the first build.
  2. Otherwise the pawn's own animation class, `SourceBody->GetAnimInstance()->GetClass()`, applied
     with `SetAnimInstanceClass`. It is skeleton-compatible by construction (it already drives that
     exact mesh on the pawn), and `UIBAnimInstance_Infantry::NativeUpdateAnimation` returns early
     when `TryGetPawnOwner()` is null, so the stage body settles in the graph's default idle state.
  3. Otherwise `Stop()` + `SetAnimation(nullptr)` — the reference pose, never a foreign clip.
  `bPauseAnims` and the `const_cast` are gone. Only stock `USkeletalMeshComponent` calls remain:
  `SetAnimationMode`, `PlayAnimation`, `SetAnimInstanceClass`, `GetAnimInstance`, `Stop`,
  `SetAnimation`.
- `IBGlassBorder.cpp`: the Slate border keeps a `TWeakObjectPtr` to its owning `UIBGlassBorder` and
  reads `Background` (`TintColor`, `OutlineSettings`) and `GetBrushColor()` at paint time, so a
  runtime `SetBrush` / `SetBrushColor` repaints on the next frame with no extra call. One tint —
  parent color/opacity x BrushColor x the disabled dim — now multiplies fill, edge, bevel line,
  accent stroke, corner tick and sheen alike (before, only the fill took BrushColor and the dim).

Note on verification: the folder-access prompt for `A:\Unreal Engine\UE_5.8\Engine\Source\Runtime`
timed out twice, so the engine headers were not read from here; the calls above are the ones with
the longest-standing signatures rather than a header check. If any of them moved in 5.8, the
report line for it is the place to look.

## Compile hotspots to look at first

1. `IBGlassBorder.cpp` reads `UBorder::Background` directly (public per the handoff) and
   `GetBrushColor()`. If direct access only warns as deprecated, ignore it; if it errors, swap in
   whatever brush getter 5.8 exposes at that one spot in `SGlassBorder::OnPaint`.
2. `IBOperativePreviewStage.cpp` `ApplyIdlePose`: `USkeleton::IsCompatibleMesh(const USkeletalMesh*)`
   compiled in the first build; `SetAnimInstanceClass(UClass*)` / `GetAnimInstance()` are the
   Blueprint-exposed component calls.
3. `UIBMenuGlyph` / `UIBGlassBorder` are new UCLASSes: UHT must regenerate; generated headers are last.
4. `IBHangarStyle.h` now includes `IBGlassBorder.h` and `IBMenuGlyph.h`; every cpp including it
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

## Pass 2 — applied September 19

Decisions from Connor (September 17): fireteam size goes to six; the Mech page shows real mech data
only; Missions keeps the briefings and gains a live ACTIVE strip; XP bar + account name first.
Connor asked on September 18 for everything to land in the tree at once, so these are in now, on
top of the pass-1 corrections. Every file was re-read from disk before writing; the only drift
found was `Online/IBSessionSubsystem.h`, which had gained the link-failure handlers from
`MP_HARDENING_2026-09-15.md` — the pass-2 edit was re-applied on top of that version, so nothing
from the hardening is lost. Files touched by pass 2:

- `Progression/IBXPSubsystem.h/.cpp` — `GetLevelBounds(Track, TotalXP, Floor, Next)` walks the
  ledger's own `LevelForXP` (binary search over the tuned thresholds), so it is right whether the
  thresholds are cumulative or per-level steps.
- `Items/IBPlayerState.h/.cpp` — replicated `OperativeXP` / `OperativeLevelFloorXP` /
  `OperativeNextLevelXP` mirrored from the host ledger on every award (`OnXPAwarded`) and when an
  identity lands; `GetOperativeLevelProgress()`, `HasNextLevel()`; a separate lightweight
  `OnOperativeXPChanged` event so combat awards never trigger roster saves or identity refreshes;
  copied across seamless travel.
- `UI/IBMenuScreen.h/.cpp` — header identity gains the platform account name beside the callsign
  (hidden when identical) and a 3 px XP bar with `current / needed XP` through the level, `TOP OF
  LADDER` at the top, raw total when no ladder is tuned. Nothing drawn without a real value.
- `UI/IBInventoryScreen.h/.cpp` — equipment well captions hide (Hidden, not Collapsed) once a slot
  is filled; equipped gear speaks for its slot.
- `Online/IBSessionSubsystem.h` — `MaxPlayers` 4 -> 6 and `static FireteamSize()`; the advertised
  session size follows (`NumPublicConnections`). `Online/IBWatchTypes.h` — `SquadMax` default 6.
  `IBWatchTypes.cpp` is untouched on purpose: its built-in destinations carry authored fireteam
  copy (`1–8 OPERATORS` on the Gate Garrison and Watch, `1–4 OPERATORS` on the Exclusion Zone and
  Firing Line, with matching `SquadMax` 8 / 4) and `SquadMax` is only ever displayed, never used to
  gate a deploy. Whether the two `1–4` sites should read `1–6` is a design call for Astra / Connor,
  not a code fix — one string + one number per row if so.
- `UI/IBFriendsScreen.cpp`, `UI/IBLobbyStripWidget.cpp` — banner pools read `FireteamSize()`;
  the Squad row dips toward the middle (subtle V) with the hero card still at seat 1.
- `UI/IBMissionsScreen.h/.cpp` — ACTIVE OPERATION strip above the filters: the replicated mission
  director's live objective for the map you stand in, with the destination name; clicking it
  selects that briefing. Collapsed when there is no director. Existing filters and VIEW ON WATCH
  untouched.

- `UI/IBMechScreen.h/.cpp` (new) + `Config/DefaultGame.ini` — the MECH tab, Personal ring between
  Inventory and Skills (no hotkey; Q/E reach it). Real frame data only, from the live `AIBMech_Base`
  in the world (the one you crew, else the first on station): chassis name from the class, hull
  integrity bar (amber < 60 %, red < 30 %), the fixed arm weapon (`CurrentVisualData` name / icon /
  rarity, ammo bar, recovery), both seats with callsign and DRIVER / GUNNER role, the Concord safety
  lock, and the Watch destination's mech authorization + fireteam for the current map. With no frame
  in the world it says so. It never boards, fires or swaps seats. No hardpoints or cores are drawn
  because none exist.
- `UI/IBMenuFlowCheck.cpp`, `UI/IBMenuVisualTour.cpp` — Personal ring now CHARACTER / INVENTORY /
  MECH / SKILLS / LEDGER; the E-cycle expectations gained the Mech step (20.7 / 21.4 / 22.1 s) and
  the tour expects "E cycles to Mech". Director ring untouched.
- `Skills/IBSkillCatalog.cpp` — node positions only (ids, costs, levels, specs untouched). Saber is
  one rising slash from the dash at bottom-left to the Redline apex at top-right, variants fanning
  off like blade edges; Sentinel is a wide kite — the veil at the left point, sensors and decoys on
  the wings, all converging on Blackout; Guardian is a bastion — Citadel at the keystone, the four
  roots holding the walls, variants outside them.
- `UI/IBSkillConstellation.cpp` — per-class spines drawn from those shapes (Guardian ring + spokes,
  Sentinel fan-in, Saber chain), the overdrive as a larger keystone with a crystalline hex frame,
  late-ladder variants (level 30+) on a hex facet instead of a plain ring — the Breach influence,
  kept quiet — and a slow pulse travelling along the inspected node's links (time-driven; the
  widget is forced volatile so it never freezes in a cached paint).
- `UI/IBMenuScreen.h/.cpp` — every screen settles 12 px up into place over 160 ms when opened
  (translation only; RoundedBox outlines ignore RenderOpacity, so no fade). The flow check's real
  clicks land a second or more after opening, well after the settle.

Not started yet: a Squad-screen hover/selected pass beyond the existing banner states, and any
per-screen transition beyond the shared settle.

### Pass 2 — compile hotspots

1. `UI/IBMechScreen.cpp` is the one wholly new translation unit. It reads `AIBMech_Base` members
   directly (`CurrentHealth` / `MaxHealth`, `CurrentAmmo` / `MaxAmmo`, `WeaponCooldownRemaining`,
   `CurrentVisualData`, `LeftSeatController` / `RightSeatController`, `CurrentDriver` /
   `CurrentGunner`, `AreWeaponsSafetyLocked()`), taken from the header as it stood on September 17.
   If any of those is private or was renamed since, that line is the whole fix; the sheet needs no
   new accessors on the mech.
2. `Items/IBPlayerState.h` adds three replicated ints and a dynamic multicast delegate — UHT
   regenerates; `GetLifetimeReplicatedProps` in the .cpp lists the three new properties.
3. `Progression/IBXPSubsystem.cpp` `GetLevelBounds` only calls the subsystem's own `LevelForXP` and
   the tuning data's threshold arrays; nothing engine-side.
4. `UI/IBSkillConstellation.cpp` includes `Framework/Application/SlateApplication.h` for the pulse
   clock (`FSlateApplication::Get().GetCurrentTime()`), and calls `ForceVolatile(true)`.
5. `Config/DefaultGame.ini` registers `/Script/IronBreach.IBMechScreen` under `ScreenId="Mech"`;
   if the tab does not appear, that line (and the class name) is where to look.

### Pass 2 — verification for Codex

1. Build; then `IB.MenuFlowCheck` — the Personal ring must read CHARACTER / INVENTORY / MECH /
   SKILLS / LEDGER and the E-cycle now has five stops (the timings moved by 0.7 s per stop after
   Mech). `IB.MenuTour` expects "E cycles to Mech".
2. Header: callsign, then the platform account name beside it (absent when identical), `LV n CLASS`,
   and the 3 px XP bar with `current / needed XP`. On a client, award XP on the host and watch the
   bar move without a menu reopen.
3. Mech tab with no mech in the world: `NO FRAME ON STATION`. In the Gate Garrison with a frame:
   chassis, hull bar, arm weapon with ammo, both seats, Concord line, and the Watch authorization.
4. Squad: six seats, the row dipping toward the middle; lobby strip also six.
5. Missions: with a mission director in the map, the ACTIVE OPERATION strip shows the live
   objective and clicking it selects that briefing; on the Watch map the strip is collapsed.
6. Skills: each class reads as its shape (Saber slash, Sentinel kite, Guardian bastion); hovering a
   node runs the pulse along its links.
