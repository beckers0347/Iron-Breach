# Reference menu design

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

## Verification

`IB.ReferenceMenuCheck` is an opt-in development command. It exercises tab clicks, category filtering, search empty state, sorting, mission selection, locked briefings, Watch focus, Escape and capture lifecycle. It writes screenshots to `Saved/ReferenceMenus/after` and PASS/FAIL results to the game log. It neither grants items nor changes the loadout or deployment state.

Build and visual verification results will be recorded after runtime review. Backups of touched existing menu files are under `Saved/ReferenceMenus/before`. No commit or push is part of this pass.
