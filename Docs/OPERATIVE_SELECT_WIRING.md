# Operative Select & Creation — Wiring (character flow v1)

*Built + verified in-game 2026-09-03/04 (standalone, hosted world). Build green, headless audit ALL CLEAR.*

New C++: `UIBCharacterSubsystem` + `UIBCharacterSaveGame` + `IBCharacterTypes.h` +
`AIBOperativePreviewStage` (Player/), `UIBCharacterSelectScreen` + `UIBCharacterCreateScreen` +
`IBSheetDismissProcessor.h` (UI/), hooks in `UIBMainMenuWidget`, operative
identity on `AIBPlayerState` / `AIBPlayerController`, banner + lobby-strip
updates. The flow after PRESS ANY BUTTON is now:

```
WBP_BootScreen (any key, unchanged BP)
  -> WBP_MainMenu spawns (already reparented to IBMainMenuWidget)
       -> SELECT OPERATIVE sheet (viewport Z40) — always, it IS the front end
            -> 3 billets: click to see them on the stage / + NEW OPERATIVE / DECOMMISSION
            -> empty roster routes STRAIGHT into creation (no way around it)
            -> NEW OPERATIVE -> intake form: callsign, combat trade, gender -> ENLIST
       -> DEPLOY / ENLIST -> sheet narrates -> IBHost (Steam session) -> ServerTravel
          into Lvl_FirstPerson?listen (your own drop-in world)
       -> identity on the PlayerState -> in-game Squad tab: invite / join / leave
       -> in the world: the body you picked, the trade's kit on Q / V, and a vault
          (inventory + level) that is YOURS per operative, not per Steam account
```

## v1.3 — class kits, per-operative vault, the body you picked (2026-09-04)

Classes are still open design — everything below is a data-driven placeholder that
Connor/Shane retune (or replace outright) without touching C++.

- **Class kits (`Classes/`).** `UIBOperativeKitComponent` on the infantry pawn resolves
  the operative's trade → `UIBClassKitData` (`/Game/IronBreach/Classes/DA_Kit_<Trade>`,
  created headless by `Scripts/ib_create_class_kits.py`; missing asset → the same
  built-in defaults). A kit is two `FIBKitAbilitySpec`s — **kit ability on Q**, **movement
  tool on V** (raw keys via `KitAbilityKey` / `MovementToolKey` on the component; assign
  `Kit Ability Action` / `Movement Tool Action` on BP_IBCharacter_Infantry for rebindable
  Enhanced Input on top) — each with a cooldown, duration, strength/range/radius/damage knobs and an
  `Effect`: `Dash`, `Grapple`, `Glide`, `ConeStrike`, `DeployZone`, or `Blueprint` (fires
  `BP_OnKitActivated` on the pawn and nothing else — the "we'll design it later" slot).
  Placeholders: Breaker RAM CHARGE / BULWARK DASH (0.35× damage taken for 0.6 s), Picket
  LAMPLIGHT FLARE (thrown marker zone, marks hostiles via Custom Depth stencil 1) / LINE
  BOLT (grapple), Bellringer DETERRENT PYLON (slow zone) / NULL STEP (glide), Corpsman
  STIM LINE (Blueprint) / SURGE CARRY. Activation is server-authoritative
  (`Server_Activate` → `Multicast_Activated`), cooldowns tick locally, the HUD
  (`UIBKitHudWidget`, bottom-right, two chips with key badge / name / READY · x.xs /
  progress bar in the trade color) is pure C++ and needs no WBP.
- **`AIBKitZone`** is the built-in pylon for `DeployZone`: replicated disc + post +
  colored light, pulses every 0.25 s, slows and/or marks HOSTILE characters inside
  (never infantry), restores speed on exit/expiry. Thrown flares land on the floor under
  the aim point (a wall hit lands at the wall's foot; a Kaiju hit lands under the Kaiju).
  Look: `M_IBKitZone` (unlit glow, `Scripts/ib_create_kit_materials.py`; Color · Glow ·
  Opacity parameters) — missing asset → engine cylinder tinted. Subclass in BP and set
  `ZoneClass` on the spec for a real look.
- **Per-operative progression.** `UIBXPSubsystem::MakePlayerKey` appends
  `#<OperativeId>` when the PlayerState carries an operative, so XP / ledger / vault are
  keyed per character (`<SteamId>#<guid>`); an accountless run keeps the old key. New
  `UIBVaultSubsystem` (GameInstance; slot `IronBreach_Vault`): the PlayerState restores
  the vault when identity lands (`RestoreVault`: existing record → `ClearAllItems` +
  `GrantItemInstance` per item + `RequestEquip`; no record → seed from what the inventory
  has) and saves 2 s after the last inventory/equipment change. Level-ups on the
  PlayerState (`HandleXPLevelUp`) write `FIBCharacterRecord.Level` back to the roster
  (`SyncLevelToRoster`, local player only) so the select sheet's LV is live.
- **The body you picked.** `AIBCharacter_Infantry::ApplyOperativeBody` swaps the third-
  person mesh to `MaleBody` / `FemaleBody` (soft paths, default `SKM_Manny_Simple` /
  `SKM_Quinn_Simple` — same skeleton + `ABP_Infantry`) whenever the operative identity
  changes; the kit re-resolves at the same moment. `HandleTakeDamage` multiplies incoming
  damage by the kit's defense window.
- Verified in-game (Picket, female): HUD chips READY → cooldown countdown; Q dropped the
  flare at the cylinder's foot and under the Jaeger when aimed at it (glow disc + post +
  light); V zipped the pawn at the Jaeger; log: `Kit: PICKET -> LAMPLIGHT FLARE / LINE
  BOLT (asset)`, `Vault: restored 1 item(s)`, `SKM_Quinn_Simple` loaded for the body.
  The "missing bones … SK_Mannequin" LoadErrors are the template skeleton merging the
  Simple meshes' IK/twist bones — pre-existing (the preview stage triggered them first),
  gone once someone re-saves `SK_Mannequin` in the editor.

## v1.2 — deploy straight into your own world; the squad forms in-game (2026-09-03)

- **DEPLOY / ENLIST → your own listen-hosted world, no lobby, no menu.** The sheet stays
  up as the loading screen ("… LINKING TO THE BREAKWATER NET…"), `IBHost` creates the
  Steam session (`bLobbyBeforeDeploy` is now OFF by default) and ServerTravels to
  `HostTravelURL` (`Lvl_FirstPerson?listen`, 4 slots, join-in-progress). If the online
  service is unreachable the sheet says so and drops you into a solo world instead.
- **The Solo / Host / Join menu and the lobby strip never show any more** — the sheet is
  the whole front end (returning from the world via LEAVE / MAIN MENU brings it back with
  your operative pre-selected). WBP_MainMenu is untouched; its buttons are just under the sheet.
- **Friends join you from inside the world:** Squad tab (F / Q·E) → INVITE seats → SOCIAL
  flyout → INVITE (Steam overlay "join game") or JOIN a friend who's in-game. Accepting an
  invite / JOIN tears down your own session properly first (`DestroyThen`: Steam destroys
  asynchronously, so create/join now waits for the callback instead of failing with
  "session already exists"), then client-travels into their instance. LEAVE FIRETEAM / the
  System menu's LEAVE SESSION bring you back to the sheet.
- Verified in-game: DEPLOY → world in ~1.5 s, log shows the online session + net driver on
  7777, Squad tab shows OPERATIVE-3453 · HOST, three INVITE seats, LEAVE FIRETEAM, and the
  Steam friends list with live INVITE buttons.

## v1.1 — the body on the stage (2026-09-03)

- **`AIBOperativePreviewStage`** (Player/): a transient actor spawned 1.8 km off-world
  while a sheet is open — mannequin (Male → `SKM_Manny_Simple`, the infantry body;
  Female → `SKM_Quinn_Simple`; both idle on `MM_Idle`) under three studio lights, filmed
  by a ShowOnly scene capture (no sky / fog / sun / skylight / auto-exposure, fixed EV0)
  into a 1024² render target. Never visible in the real view
  (`SetVisibleInSceneCaptureOnly`). Swap the soft paths on a BP child when real
  operative bodies land.
- **Select screen is Destiny-shaped now:** body on the left (ScaleBox-fit to screen
  height, framed right-of-center), roster as a vertical list on the right. Click a
  billet → that operative stands on the stage, rim light in their trade color, nameplate
  at the feet (callsign / trade + motto / LV · gender · last deployed). DEPLOY /
  DECOMMISSION act on the selected billet. LAST ON STATION is auto-selected on open.
- **Creation previews live:** gender swaps the mannequin, the chosen trade lights the
  rim, the nameplate shows the sanitized callsign as you type.
- **Placeholder title art is gone behind both sheets** — opaque stage-black (black, not
  Ink, so the capture's empty background is seamless).

## What the code guarantees

- **Max 3 characters**, saved to slot `IBCharacters` (`Saved/SaveGames/IBCharacters.sav`),
  same local-disk-is-truth posture as `XPSaveGame` (ADR-002). Each record:
  guid, callsign, class, gender, level, created / last-played stamps.
- **The door law:** every fresh boot chooses a character at the door (the active
  choice is per-run; the roster persists, the choice does not). Quit-to-menu and
  host/join travels do NOT re-ask — the GameInstance keeps the choice for the run.
- **Empty roster = forced creation.** No BACK / Escape on the intake form until at
  least one operative is on file. Decommissioning the last operative drops you back
  into intake, not into an empty menu.
- **Creation is the choice:** ENLIST puts the new operative on station and lands you
  on the main menu. Classes come from `CLASSES_AND_PROGRESSION.md` (Breaker / Picket /
  Bellringer; Corpsman renders locked — CORPS NOT YET OPEN — per Phase-1 scope).
  Callsigns: 16 chars, A–Z 0–9 space - _ ., uppercased; blank gets a service-issued
  `OPERATIVE-####`; duplicates refused.
- **Decommission is two-step** (arm → CONFIRM — FOR GOOD?) and deletes the record.
- **Travel guard:** Solo / Host / Join refuse to fire without an operative on station
  (status line narrates + the select sheet opens). Input-mode law respected: the sheets
  run UIOnly + cursor; the existing LockForTravel path still flips to GameOnly first.
- **Lobby states:** ?listen menus (host lobby / client) never show the gate and disable
  operative switching — no swapping soldiers mid-lobby.
- **Identity travels with the player:** `AIBPlayerState` carries replicated
  `OperativeCallsign / Class / Gender`. The menu pushes it on every spawn (authority
  sets directly, clients Server-RPC on the PlayerState — so it works under the template
  controller the front end runs); `AIBPlayerController` re-pushes on BeginPlay and
  OnRep_PlayerState for gameplay levels. `IBPlayerBannerWidget` prints the callsign and
  paints the trade color on the top edge; the lobby strip's fingerprint includes it so
  late-arriving callsigns land without a roster change.
- **Dismiss key:** Escape / gamepad B on the sheets goes through a Slate input
  preprocessor (`FIBSheetDismissProcessor`) registered while a sheet is up — it sees the
  key before any focused widget (text field, button, viewport) can eat it. BACK buttons
  are verified in-game; Escape itself could not be exercised through the remote-control
  harness (it never delivers Escape — even PRESS ANY BUTTON ignores it), so give it one
  real keypress.

## Wiring done (nothing left for you)

- `Scripts/ib_wire_menu_playerstate.py` (ran headless, saved): **BP_FirstPersonGameMode
  → Player State Class = BP_IBPlayerState**. The front end runs under the
  GlobalDefaultGameMode, whose stock PlayerState had nowhere to put the identity.
  PlayerController class deliberately left as the template controller (it owns FP input).
  BP_IronBreachGameMode already had both IB classes.
- No new WBPs, no BP graph edits, no registry rows. Both sheets are pure C++
  (LobbyStrip pattern) and hook in through `IBMainMenuWidget`, which `WBP_MainMenu`
  already parents.
- `Scripts/ib_audit_character_flow.py` proves it headless: classes visible in the
  module, WBP_MainMenu derives from IBMainMenuWidget, WBP_BootScreen present, front-end
  GameMode carries an IBPlayerState.

## Build loop (`zzcharwatch.bat`)

Double-click once, leave it open. It watches `Saved/zz_build_request.txt`:
`build` · `audit` · `buildaudit` · `py <script in Scripts/>` — results in
`Saved/char_build_report.txt` (ends with `ZZCHAR_ALL_DONE`; if that line is missing,
the appender lost a race with something reading the report — the watcher's own window
still says "done"). `zzchargame.bat` launches the game windowed straight to the title
screen (`-game -windowed 1600x900`). Close the editor and the game before a build
(Live Coding holds the DLL). `zzcharpush.bat` commits ONLY the operative-flow / class-kit
files listed inside it and pushes `main` — the 1000+ re-saved assets from the 5.8
upgrade stay local, and it clears a stale `.git/index.lock` first (only when no git.exe
is running).

## Optional binds (art passes, any subset)

In **WBP_MainMenu**:
- `Txt_Operative` — TextBlock; gets "OPERATIVE — CALLSIGN · CLASS".
- `Btn_Operative` — Button; reopens the select sheet. When NOT bound, a small
  service-console chip (operative line + SWITCH) is injected bottom-left on
  Canvas/Overlay roots (that's what's live now).

To reskin the sheets: parent WBPs to `IBCharacterSelectScreen` /
`IBCharacterCreateScreen` the way the other C++ screens work.

## Verified in-game (2026-09-03, -game windowed)

1. Fresh save: any key → intake form directly (no BACK). Typed callsign, Breaker + Male,
   ENLIST → menu, status "VOSS ON STATION — BREAKER", chip bottom-left, banner "VOSS"
   with the Breaker edge.
2. Relaunch: any key → select screen, VOSS card (LAST ON STATION tag, LV 1 · MALE,
   LAST DEPLOYED — TODAY), two empty billets. + NEW OPERATIVE → form WITH BACK → BACK.
3. DEPLOY → menu. SWITCH → select with BACK; BACK → menu.
4. DECOMMISSION → armed (CONFIRM — FOR GOOD?) → confirm → roster empty → intake
   form, no BACK. Blank callsign + Picket + Female → OPERATIVE-3453, cyan edge.
5. HOST → session up → lobby world → menu in lobby state (no gate, SWITCH hidden,
   DEPLOY SQUAD amber) → banner OPERATIVE-3453 · HOST.
6. Save file `Saved/SaveGames/IBCharacters.sav` persists across runs. (A test operative,
   OPERATIVE-3453, is on your roster — decommission it whenever.)

## Follow-ups this unlocks (not in this pass)

- Design the real kits: retune `DA_Kit_*` or point a spec's `Effect` at `Blueprint` and
  build it in `BP_OnKitActivated` (on the kit component); wire Input Actions for Q / V
  into the infantry IMC for rebindable keys; a Custom-Depth outline post-process so LAMPLIGHT
  FLARE marks actually show; real zone art via a BP `AIBKitZone` child.
- Vault v2: store weapon rig state (`CurrentVisualData` is still a BP default — the
  pre-existing "CurrentVisualData is NULL" error on spawn is that, not the vault);
  server-side vault for clients (today only the host's disk is truth, per ADR-002).
- Voice / face pick to go with the gender-driven body.
- Title-screen camera move into a 3D select hangar (SPEC-title-screen §2): these sheets
  keep working — they're UMG over whatever camera runs.
- The main menu's Solo/Host/Join chips sit behind the fireteam banners at 1600×900
  and their labels don't render — pre-existing WBP layout, worth a pass.
