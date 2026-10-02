# Claude implementation handoff — September 15, 2026

## Objective

The user wants **all menus to match the supplied reference photos**, not merely tinted rectangular panels. They explicitly asked Codex to delegate the heavy coding and analysis work to Claude. Please implement the remaining visual pass in the existing local project. Codex will coordinate, compile, run Unreal, inspect screenshots, and feed back problems. Do not start a second build/editor/game or a Windows command watcher; coordinate those with Codex.

Project: `D:/Unreal Games/IronBreach`, Unreal Engine 5.8. The tree contains substantial unrelated uncommitted work. Preserve it. No commit, push, reset, broad rollback, saved-game changes, or gameplay feature expansion.

## References and existing evidence

Read and visually inspect `References/MenuTargets/character.png`, `inventory.png`, and `missions.png`. These are the user's original targets. Read `Docs/REFERENCE_MENU_DESIGN.md` for existing mechanics and prior tests. The September 14 navigation/fullscreen pass is complete and user-approved. The September 15 visual pass is partially edited and **not compiled or visually verified**.

Prior screenshots are under `Saved/MenuFlow/after`, `Saved/ReferenceMenus/after`, and `Saved/MenuConsistency/after`. Do not treat prior test success as validation of today's edits.

Desired appearance: cinematic military hangar; slim integrated navigation; angular/beveled translucent glass and fine cyan hairlines; restrained typography; strong real item art; coherent selected/hover/disabled states; content-led layouts with clear breathing room. Keep existing rarity, threat, and destructive-action colors meaningful. Avoid decorating every background tint or tiny line as a framed card.

## Behavior to preserve

- Personal group: Character, Inventory, Skills, Ledger. Director: Watch, Map, Missions, Squad. Q/E and shoulders cycle only within the current group.
- I/Tab opens Character directly. B opens Watch. Header group links work in one click. Character and Backpack/Inventory alias routing stays through the menu subsystem.
- The user's double-click complaint concerned **opening/switching to Character**, not equipping gear. Existing equipment actions and server authority must remain.
- Watch remains fullscreen, with independent scrolling briefing and fixed deploy controls. Preserve actual proposal/confirmation/travel flow.
- All data comes from current game state. Do not invent XP fractions, currency, rewards, item ownership, quest history, gear, or class armor to make the picture fuller.
- Maintain live interactive UMG/Slate menus. Do not place a reference screenshot over the UI or replace the live operative with a flat concept photo.

## Work already in progress; finish and review it

Codex's earlier workers stopped when the user requested Claude. Their edits are in the shared working tree:

1. `UI/IBInventoryScreen.cpp/.h`, `UI/IBItemTileWidget.cpp/.h`: Character portrait overlay behind equipment, compact equipment presentation, category rail, denser inventory, larger inspector, native `UIBItemGlyphWidget` fallback. These may be partially finished. Inspect current code and complete missing pieces.
2. `UI/IBMissionsScreen.cpp/.h`: recon-backed mission list rows, briefing/intel split. It introduces a local `UIBMissionImageShade` gradient border. Preserve ALL/OPERATIONS/PATROLS/TRAINING filters and VIEW ON WATCH routing.
3. `UI/IBLedgerScreen.cpp/.h`: narrow rail, gallery, larger item inspector with real icons and glyph fallback. It uses the shared item glyph. Inspect for incomplete changes and type/include errors.

No one is actively editing these now. You can own the full visual implementation across the menu files.

## Remaining implementation priorities

### A. Shared visual system and navigation

`UI/IBStyleKit.h`, `IBMenuLayout.h`, `IBHangarStyle.h`, `IBMenuScreen.cpp/.h` need the main reference treatment. Existing `IBHangar::Panel(Tree, Child, Padding)` and `IBMenuLayout::Card` signatures should remain stable.

Consider a reusable `UBorder` subclass with a custom `SBorder::OnPaint` for chamfered glass panels and tasteful corner accents. Existing `UIBWatchCardBorder` in `IBWatchScreen.h/.cpp` is a working example. `IBPaintKit.h` supplies polygon fills, lines, gradients, diamonds and text. Respect parent tint/opacity and the border's configured fill/accent. `UBorder::Background` is public; `GetBrushColor()` exists; there is no assumed `GetBrush()` accessor. Only true content panels should gain bevels: full-screen shades, accent bars, tab underlines and image overlays should not.

Slim and integrate the shared header, retaining legibility and all navigation labels. Replace the placeholder Unicode diamond with a small native geometric military insignia if helpful. Use actual callsign, class, level, clearance. Do not fabricate XP progress: `IBXPSubsystem` totals are server-side and current PlayerState does not replicate fractional progress. Keep the 1600x900 design surface and smaller-window scaling readable.

### B. Apply coherent reference styling across every menu

In addition to Character/Inventory/Missions/Ledger, polish Skills, Map, Squad/Friends, System, Settings, operative select/create, and weapon rack. Shared primitives should do most of the work, then targeted spacing/hierarchy changes where needed. Relevant files are `IBSkillsScreen`, `IBMapScreen`, `IBFriendsScreen`, `IBSystemScreen`, `IBSettingsScreen`, `IBCharacterSelectScreen`, `IBCharacterCreateScreen`, and `IBWeaponRackScreen` under `Source/IronBreach/UI`.

Skills remains an icon-only constellation with a faint operative hologram and clear inspector. Watch geometry remains fullscreen. Title menu keeps its authored logo/animation/input gate; do not inject unmanaged widgets into its Blueprint. Existing script `Scripts/ib_style_title_menu.py` only styles authored text.

### C. Real portrait and item art

Preview stage is `Source/IronBreach/Player/IBOperativePreviewStage.cpp/.h`. Character should occupy most of its available height, with natural full-body framing rather than a tiny figure. Keep portrait faithful to actual pawn mesh/materials. Existing `ConfigureForInventory` copies the live pawn but always plays mannequin `MM_Idle`; make it skeleton-compatible or retain a valid pose. If showing an equipped weapon, copy only the actual local weapon using the existing public `GetThirdPersonWeaponMesh()` data; no gameplay mutation.

Read-only audit script: `Scripts/ib_audit_reference_assets.py`. Codex can run it in the editor. Asset findings:

- `/Game/Characters/Infantry/Meshes/StarterArmor/SK_StarterArmor` has its own skeleton.
- `/Game/Characters/Infantry/Meshes/Chaos_Armor/Chaos_Armor` uses Chaos_Armor_Skeleton; infantry idle/idle__2_/idle__3_ appear compatible.
- Five actual `DA_Visual_*_B` weapon definitions already reference matching generated icons at `/Game/Items/Icons/Generated/T_Icon_*`: Pistol_B (Spark_G1), Rifle_B (Nova_Edge), SMG_B (Amethyst_Arc), Shotgun_B (Levithan_Prime), Sniper_B (Iron_Horizon).
- Rifle_C, ArmCannon, and KaijuChitin have no icon references visible in the audit yet. No modular armor item definitions were found.
- Codex generated a transparent loot icon for the existing Kaiju Chitin material. Source copied to `Art/MenuSources/kaiju-chitin-v1.png`. Please prepare a small editor import script assigning only the actual KaijuChitin definition's Icon, preserving all other fields. Codex will execute it. No remote asset creation is needed.

Do not silently assign unrelated armor as a player's owned outfit to imitate the concept. Report any exact art match that requires new assets.

## Engine/API pitfalls observed earlier

- UE 5.8 `UButton` has no `SetIsFocusable()`. Constructor subclasses can use `InitIsFocusable(false)`. `UUserWidget` has SetIsFocusable.
- Local variable `Slot` shadows a UWidget member and fails this build; use descriptive variable names.
- Unity builds can collide across anonymous namespaces; use distinct named helper namespaces.
- RoundedBox outline alpha may not follow RenderOpacity as expected. Active tab underlines already use Hidden/HitTestInvisible visibility. Preserve that fix.
- Keep UCLASS generated headers last and dependencies correct for new native widgets.

## Validation and deliverables

Codex owns build/game execution. Please provide exact edited files, any concerns, and a reviewable completion report at `Docs/CLAUDE_MENU_REDESIGN_RESULT.md`. You may run local lightweight static checks through your existing file/code tools, but do not launch terminal apps, Run dialog, shell commands through Explorer, build watchers, editor, or game via UI.

Existing opt-in checks for Codex:

- `IB.MenuFlowCheck`: actual single mouse clicks, keyboard navigation and Watch edge geometry at 1280x720 and 1600x900. Preserve named Watch widgets DirectorScene, WatchPlanet, WatchBriefingPanel, WatchDeployButton.
- `IB.MenuConsistencyCheck`: menu navigation, filters, settings/social/rack closure and utility controls.
- `IB.ReferenceMenuCheck`: inventory search/filter/sort, mission selection and preview lifecycle. Preserve existing user-facing control labels used by checks where practical.
- `IB.FrontendStyleCheck` and local `IB.DeploymentCheck`: startup and Watch travel. Existing chain arguments are `-IBMenuConsistencyAfterDeploy -IBMenuFlowAfterMenus`.

Do the heavy implementation now rather than returning only a plan. If file access prevents implementation, state the exact missing access and do not claim files were changed. Work with the current dirty checkout; do not overwrite it with stale copies from old chats.

## Live asset audit follow-up
Codex successfully ran the read-only Unreal asset audit. Confirmed findings and exact loaded asset paths are in Saved/ReferenceArtPass/asset-audit-summary.txt. Rifle_C and ArmCannon are empty definitions (no display name, mesh, icon or combat reference); do not populate them in this visual pass. The KaijuChitin definition path is /Game/IronBreach/Items/DA_Item_KaijuChitin. The prior test game is closed; Codex owns all build and editor execution.
