# In-game menus — September 2026

Inventory, Ledger, Map, System and Settings use a shared dark field-terminal presentation. The user requested a dedicated Character tab with an operative in the center and equipment around it, and a separate Backpack tab.

## Inventory

- `IBInventoryScreen` builds **Character** and **Backpack** pages inside the existing Inventory screen. Click their buttons or use Left/Right (gamepad D-pad). The selection survives closing and reopening. Q/E and shoulder buttons still cycle the registered menus; Escape still closes them.
- Character shows the existing animated operative preview, with primary/special/heavy weapons on the left and helm/chestplate/gauntlets/greaves/anti-kaiju gear on the right. It reads the operative's identity from PlayerState and the current infantry body's mesh/materials when available. While piloting a mech, it uses the operative's gender-specific infantry body.
- The preview is a transient local actor. It is destroyed on switching to Backpack, closing Inventory, or widget destruction. Its render-target reference is cleared as well. Identity/equipment updates refresh the visible preview.
- `IBOperativePreviewStage::ConfigureForInventory` centers this screen's camera. The existing character creation/selection camera defaults are unchanged.
- Backpack has a scrollable eight-column grid, category filters, an item count and a dedicated inspection panel. Equipped items retain their existing exclusion from the backpack.
- The native item tile can use compact sizes for equipment wells. Item data, equip/unequip requests and replication are unchanged.

## Shared presentation

- `IBMenuLayout.h` supplies consistent typography, controls, panels and a scale-to-fit design surface. `IBMenuBackdrop` paints the subtle grid and edge details without new image assets.
- Inventory, Ledger and Map navigation tabs are clickable through `IBMenuNavButton`, using the existing screen registry and `OpenScreen` path. Watch and Squad retain their existing presentation.
- Ledger has matching item cards, filters, collection progress and an inspection panel. Sealed entries keep their names/descriptions hidden in the native details view.
- System has a clear Resume action, readable destination/session context, and the existing two-click quit confirmation.
- Settings uses separate video and audio/control panels. Its value, apply, save and reset handlers are unchanged.
- Map has a player-facing unavailable-survey state. Actual cartography still needs the project's authored map layout and zone data. No terrain, POIs or deployment data are invented by this pass.

## Validation and reproduction

Run an Editor Development build, then launch the test map with:

```text
UnrealEditor.exe IronBreach.uproject /Game/FirstPerson/Lvl_FirstPerson -game -windowed -ResX=1600 -ResY=900 -NoSteam -NoSound -unattended -ExecCmds="DisableAllScreenMessages,IB.MenuTour"
```

`IB.MenuTour` is excluded from Shipping/Test. It opens the registered WBP screens, captures settled UI frames, exercises category filters and navigation, checks preview actor cleanup, and clicks the first quit-confirmation step only. It does not grant/equip items, edit settings, travel, or send invitations. Screenshots go to `Saved/MenuPolish/after`; log assertions begin with `[MenuTour]`.

Validation results are recorded in `Saved/MenuPolish/verification.md`. The source snapshot before this menu pass is in `Saved/MenuPolish/before`; `first-pass` images predate the requested Character/Backpack split and are not the final design. The early `before/inventory.png` startup capture is blank and is not usable visual evidence.

No content assets or screen registry settings were changed for this menu pass. Other pre-existing project edits remain in the working tree. No commit or push was made.
