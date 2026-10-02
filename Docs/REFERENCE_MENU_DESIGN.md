# Reference menu design

## Current direction — September 14, 2026

The user's new request supersedes the earlier single tab strip. There are two menu groups, following Destiny's distinction between personal character management and the activity Director:

- Personal: **Character, Inventory, Skills, Ledger**. I/Tab opens Character directly, even when Inventory was the last personal page used.
- Director: **Watch, Map, Missions, Squad**. B opens Watch. Each group's Q/E and shoulder-button cycle stays within that group, including Character and Inventory as distinct pages.
- The header includes an explicit `DIRECTOR [B]` / `CHARACTER [I]` link between groups. Screen hotkeys remain available from either group. Settings/System are outside both tab cycles.
- Character and Inventory navigation routes through the menu subsystem in one operation. The user clarified that the extra click concerned **opening/switching to Character**, not equipping gear. Equipment actions are unchanged by this pass.
- Watch is a full-viewport planet scene with compact Director navigation above it. The hangar wrapper and painted command-window frame are removed. The briefing scrolls independently of the fixed deployment controls. The existing authoritative proposal/confirmation/travel flow is retained.
- Top navigation now uses text tabs with an active underline instead of a row of outlined boxes.

Research: [Bungie's Character menu guide](https://help.bungie.net/hc/en-us/articles/45753961638292--6-Navigating-The-Menu-Screen) and [Director guide](https://help.bungie.net/hc/en-us/articles/45946334996756--7-Understanding-The-Director). This adapts their personal/activity separation to Iron Breach's existing features; it does not add Destiny-specific currencies or systems.

### Later visual redesign

The user also requested a later appearance pass and explicitly rejected the current generic box-heavy look. The original supplied images were recovered from `C:/Users/kraki/Downloads` and preserved at `References/MenuTargets/character.png`, `inventory.png`, and `missions.png`. Treat these as visual targets: finer angular framing, integrated navigation, strong item imagery, deliberate spacing, and gear around a detailed central operative. The fullscreen/navigation pass does not complete that larger artwork and layout redesign.

### Verification for this change

`IB.MenuFlowCheck` sends actual Slate mouse movement/down/up and keyboard events, checks both menu groups and viewport edges at 1280x720 and 1600x900, and captures results under `Saved/MenuFlow/after`. It checks reopening Character with I after closing Inventory, and switching from each Director page with one mouse click. It does not equip items, spend points, or deploy. It restores the original window size and leaves Watch open. Existing reference and consistency checks follow the new group links.

Build and run results for this pass are recorded in `Saved/MenuFlow`.

Final validation: `build-verified.log` succeeded; `qa-verified.log` passed 116 mouse/keyboard/viewport checks with zero failures, all startup/menu consistency checks, and four local listen-host deployment checks. Both 1280x720 and 1600x900 screenshots were inspected. The startup test now respects a full saved operative roster. Summary and limitations: `Saved/MenuFlow/verification.json` and `verification.md`. Remote second-player testing is outside this pass. No commit or push was made.

The Character, Inventory, and Missions sheets follow the three visual references supplied on September 10, 2026. This pass uses a shared cinematic hangar background, translucent blue-black panels, thin cyan borders, separate Character/Inventory navigation, and readable item/mission details.

## Content and controls

- Character places the local operative's animated body between four weapon/field-gear slots and four armor slots. Callsign, class, level, clearance and equipped count use the current player state. The available body and gear models determine the character's appearance; the concept's armor is not a supplied 3D asset.
- Inventory has category filters, case-insensitive name search, rarity/name/clearance sorting, and a persistent selected-item inspector. Click a backpack item to select it, then Equip Selected Item to use the existing server-authoritative request. Clicking equipped gear still requests unequip. Empty grid cells are visual spacing, not a storage limit.
- Missions (J, or its navigation tab) reads the Watch destination registry. Briefings show actual recon images, threats, team sizes and mech authorization. The current destination shows the replicated mission director's live objective when present. View on Watch focuses the selected destination without proposing or confirming deployment. Locked locations remain locked.
- Left/Right switch Character and Inventory. Q/E and gamepad shoulders retain the registered screen cycle. Escape returns to play. Search owns printable keyboard input while focused.

The references' currencies, invented gear, rewards, quest-completion history, and unimplemented tabs are not presented as player data. The existing Watch deployment/confirmation flow remains authoritative.

## Assets and generation

Generated with the built-in imagegen tool using the supplied images as visual references. Source asset: `Art/MenuSources/hangar-v1.png`. Imported texture: `/Game/IronBreach/UI/Hangar/T_MenuHangar`. The source PNG is retained in the project and is not dependent on the generation cache.

Final prompt:

> Use case: stylized-concept. Asset type: production background plate for the IronBreach in-game character, inventory and missions menus, wide 16:9. Use the three reference images for background atmosphere, composition, material quality and color palette only. Create a clean empty futuristic military hangar opening onto a misty fortified industrial city. Large dark spacecraft and heavy industrial ceiling beams overhead, cold blue atmospheric light through the open bay, subtle warm amber practical lights at the edges, wet brushed steel floor and restrained reflections, crates at far edges. Cinematic realistic AAA game environment. Eye-level view, floor visible in lower third, central standing area empty and readable for a separately rendered full-body character. Dark low-contrast left and right areas for real interactive UI panels. Match the reference understated blue-gray/teal and amber palette. No characters, no human figures, no text, no letters, no UI, no frames, no buttons, no icons, no emblems, no watermark. This is only the background environment, never a screenshot of a menu.

`Scripts/ib_import_menu_hangar.py` imports the backdrop and builds the UI portrait material. Inventory switches its isolated scene capture to HDR with inverse opacity; the UI material tone-maps the body and composites it over the backdrop. The front-end portrait capture defaults are unchanged. The capture actor, render target and dynamic material are released when leaving Character or closing the menu.

The portrait material uses the linear `T_PortraitDefault` texture as its editor default; the transient capture replaces it at runtime. `Scripts/ib_refresh_menu_recon.py` refreshes the shared Watch/Missions Carrow thumbnail from `Art/MenuSources/carrow-gate-recon-v1.png`, a real screenshot of the updated fortress. The older thumbnail is backed up under `Saved/ReferenceMenus/before`.

## Verification

`IB.ReferenceMenuCheck` is an opt-in development command. It exercises tab clicks, category filtering, search empty state, sorting, mission selection, locked briefings, Watch focus, Escape and capture lifecycle. It writes screenshots to `Saved/ReferenceMenus/after` and PASS/FAIL results to the game log. It neither grants items nor changes the loadout or deployment state.

Verified September 12, 2026:

- Editor build succeeded: `Saved/ReferenceMenus/build-ready.log`.
- Menu interactions: 25 passes, zero failures at 1280x720 (`qa-1280-final.log`); 25 passes, zero failures in the final 1600x900 fortress run (`qa-1600-deployment-final.log`). The last layout adjustment reduces the search font and keeps mission intel visible without scrolling for the built-in briefings.
- Steam listen-host deployment, arrival, return to the Watch, and redeployment: four passes in the final run. Remote two-player travel was not tested here.
- All three final screenshots inspected: full viewport background, transparent live character, separate tabs, persistent item inspection, readable mission rows, and current fortress recon. The menu material produces no runtime shader errors. The existing unrelated `M_AI_Foam` warning still occurs when the fortress loads.
- Summary: `Saved/ReferenceMenus/verification.json`. Final screenshots: `Saved/ReferenceMenus/after/character.png`, `inventory.png`, and `missions.png`. Earlier 720p screenshots are in `Saved/ReferenceMenus/1280`.

That first pass ended on Character inside the fortress. Backups of touched existing menu files are under `Saved/ReferenceMenus/before`. No commit or push was made during this completion pass.

## Remaining menus and skills — September 13, 2026

Ledger, Map, Squad/Friends, Watch, System, Settings, operative selection/creation and the weapon-rack overlay now share the hangar scene, flat glass panels, cyan interaction states, restrained typography and angular outlines. Rarity, threat and destructive-action colors keep their existing meaning. System and Settings retain the player header. Character and Inventory remain separate tabs, with gear surrounding the central operative on Character.

The Watch uses the same navigation header in the lobby and in missions. Its briefing scrolls independently of the deployment actions so Deploy remains visible in a smaller window. Existing proposal, host confirmation, travel and return behavior is retained. The title screen keeps its authored logo, animation and input gate; only existing text is restyled. `Scripts/ib_style_title_menu.py` does not inject unmanaged native widgets into the Blueprint tree.

`IB.MenuConsistencyCheck` exercises registered screens, navigation, Ledger filters, quit confirmation/disarming, settings, the social flyout and weapon-rack close. `IB.FrontendStyleCheck` checks title, operative selection, creation and cancel, then hands off to the existing deployment check. No friend invitation is sent and no settings or gear are changed. The rack check validates its layout and close behavior with an empty source, not a live stock transfer.

The three class names and the new Skills constellation are covered in [SKILLS_SYSTEM_DESIGN.md](SKILLS_SYSTEM_DESIGN.md). Skills uses the same player bar and menu tabs, an equipped strip above the icon-only constellation, a faint operative hologram and a fixed detail inspector. Its keyboard entry is K.

Broader menu backups: `Saved/MenuConsistency/before`. Menu screenshots: `Saved/MenuConsistency/after`. Skills, deployment and combined menu test logs/screenshots: `Saved/SkillsSystem`. The initial combined 1600x900 run passed progression, menu, deployment and combat checks. Smaller-window and final verification are summarized in `Saved/SkillsSystem/verification.json`.
