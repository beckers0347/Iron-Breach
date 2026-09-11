# The Watch — the command deck (v2, 2026-09-08)

*Iron Breach's "orbit". The planet turns outside the deck window; every sector of the world is
pinned on it; the card reads the pick; DEPLOY drops the squad. v1 (the flat breach board in a
box, 09-06) is now the sector-level detail view inside this.*

## What it is

After **DEPLOY** on the operative sheet the session stands up and you land in the menu map as a
live lobby with **THE WATCH** open: a full-screen planet (invented world, generated at runtime),
seen through the deck framing, with seven **sector pins** — CARROW SECTOR (home, live) and six
closed ones that say what the rest of the world is doing. Drag turns the planet, the wheel zooms,
a click selects a pin, a double-click (or **VIEW MISSION · BREACH BOARD**) opens the sector's
breach board over the zoomed-in terrain. The card on the right shows the selected site: recon
still, THREAT CLASS + meter, MISSION TYPE, OBJECTIVE, FIRETEAM | MECH DEPLOYMENT, and the
**DEPLOY** button (PROPOSE for clients — anyone proposes, the host confirms).

**DEPLOY is not a countdown.** The board arms with `DeployAtServerTime = now + 2.4 s`
(`IBWatch::DeployDropSeconds`) and every screen plays the same drop from that clock: the camera
aims at the breach, the pins fade, the deck cuts out, the camera falls, white-out, and the server
travels on the black frame. No ABORT once it has started (host / proposer can still STAND DOWN /
WITHDRAW a proposal before that).

In a mission the same screen is a menu tab — **B**, or SYSTEM → THE WATCH — so "return to the
Watch" is the CARROW-1 pin on the board.

## Flow

```
Press Any Button -> SELECT OPERATIVE -> DEPLOY
  -> IBHost (Steam session)  -> bLobbyBeforeDeploy=true -> ServerTravel Lvl_MainMenu?listen
  -> menu widget spawns in the lobby world -> EnterHostLobbyState -> OpenWatch()
       friends: Squad tab INVITE / JOIN -> ClientTravel into the lobby -> EnterClientLobbyState -> OpenWatch()
  -> orbit: pick CARROW SECTOR (card shows GATE GARRISON / EXCLUSION ZONE / FIRING LINE chips)
     or double-click / VIEW MISSION -> the breach board (v1) over the zoomed planet
  -> DEPLOY (host) / PROPOSE (client) -> host CONFIRM & DEPLOY
  -> AIBWatchBoard arms -> 2.4 s drop -> UIBSessionSubsystem::IBDeployTo(map) -> ServerTravel map?listen
  -> in the world: B (or System -> THE WATCH) reopens the deck; CARROW-1 pin = back to the lobby
Steam unavailable: the NULL subsystem hosts a LAN lobby with IP networking. If session
creation itself fails, the Watch opens in the standalone menu and DEPLOY travels alone.
```

## The planet (no content)

`Scripts/ib_build_watch_materials.py` (run headless: `py ib_build_watch_materials.py` through the
build watcher, or `UnrealEditor-Cmd ... -run=pythonscript -script=...`) generates two materials in
`/Game/IronBreach/Watch/`, each a single Custom HLSL node — the shader is the mockup's, ported:

- `M_WatchMap` (Surface/Unlit): UV → (height, city density, moisture). `UIBPlanetWidget` draws it
  **once** into a 2048×1024 render target at startup, reads it back to place every sector pin on
  the nearest coastline (kaiju come out of the sea) and to set the sea level (68 % ocean), then
  hands the RT to
- `M_WatchPlanet` (UI domain): ray-casts a unit sphere per pixel of the full-screen Image —
  ocean + sun glint, biomes, snow and sea ice, warped-FBM clouds with a swirl storm (placed over
  open ocean east of home so it sits in daylight), city lights on the night side, atmosphere rim
  + halo, terminator warmth, a faint 15° graticule, stars. Parameters set per tick: `RotX/Y/Z`
  (planet→camera rotation columns), `Cam` (dist, tan(fov/2), aspect), `Shift` (principal-point
  shift so the planet sits left of the card), `Sun`, `Storm`, `Sea`, `CloudT`, `Gamma`, `Map`.

Re-running the script regenerates both assets; it is the source of truth for the HLSL. The first
game launch after a regeneration compiles the shaders (~20 s of low frame rate, once).

## Code

| Piece | File | Notes |
|---|---|---|
| Data | `Online/IBWatchTypes.h/.cpp` | `FIBDestination` (+ `SectorId`, `ShortName`, `ThreatLevel` 0–5, `MissionType`, `Fireteam`, `MechDeployment`, `ReconStill` texture) and **`FIBSector`** (name, region, status, lat/lon target, color, glyph, threat level, bLive/bHot/bHome, brief, lock reason). `UIBDestinationRegistry` at `/Game/IronBreach/Watch/DA_Destinations` overrides either list. `DeployDropSeconds = 2.4`. |
| Board state | `Online/IBWatchBoard.h/.cpp` | Unchanged v1 state machine (Proposed / Armed / DeployAt / Current, server-side, replicated). `UIBWatchSubsystem` also carries the dev hooks below. |
| Client → server | `Items/IBPlayerState.h/.cpp` | `WatchPropose / WatchConfirm / WatchCancel`. |
| The planet | `UI/IBPlanetWidget.h/.cpp` | Full-screen Image + dynamic material; camera (orbit spin/pitch/zoom, sector park, drop fall); bake + coast snapping + storm placement; paints pins (diamond, class glyph, hex-grid halo, sonar ring), the callout box, the drop fx (converging rings, speed lines, darkening, drop marker, name card) and the deck framing (pillar, console, truss). Emits `OnSectorPicked` / `OnSectorOpened`. `BoardRect()` is shared with the screen. |
| Paint helpers | `UI/IBPaintKit.h` | `IBPaint::` Line/Ring/Fill/Rect/Diamond/Label/Font… (namespaced — unity build). |
| The board | `UI/IBSectorBoardWidget.h/.cpp` | v1's painted Carrow map, now inside a dark frame over the zoomed planet. |
| The screen | `UI/IBWatchScreen.h/.cpp` | Layout (planet → shade → board frame → HUD → flash), the two views (`bBoardView`, eased `DiveT`), the drop (HUD cut at 20 %, board zooms about the pin, white-out then black), the card (name, sector · codename, site chips, recon still or placeholder, threat block + meter, rows, two-col, narrator, DEPLOY / CONFIRM & DEPLOY / DEPLOY HERE INSTEAD / PROPOSE / … , WITHDRAW / STAND DOWN, VIEW MISSION ⇄ BACK TO ORBIT), roster chips from `GameState->PlayerArray` (+ INVITE SQUAD → Squad tab), hints, LEAVE / CLOSE. |
| Session | `Online/IBSessionSubsystem` | `IBDeployTo`, `IBReturnToWatch`, PreLoadMap input-mode reset; listen URLs match the active Steam/LAN transport. |
| Menu | `UI/IBMainMenuWidget` | Unchanged: opens the Watch in both lobby states and the offline fallback. |

Layout constants live in `IBPlanetLayout` (planet widget) and `IBWatchUI` (screen): card 400 px,
pillar 72 px, console 84 px, 40° vertical FOV.

## Dev hooks

- `-IBWatch` on the command line opens the deck directly in the standalone menu world (skips the
  boot screen and the sheet). `-IBWatchShots` adds a timed tour with screenshots into
  `Saved/Screenshots/Watch/` (orbit, board, orbit back, drop start / mid / late — the drop
  really travels). `Scripts/ib_launch_game.py` (via the watcher: `py ib_launch_game.py`) kills a
  running -game instance and launches with the args in `Saved/zz_launch_args.txt`.
- `UIBWatchScreen::DevOpenBoard / DevOpenOrbit / DevDeploy` are what the tour calls.

## Adding content

- **A destination**: add a row in `BuiltInDestinations()` (or the DA). `SectorId` says which pin
  it belongs to; `BoardPosition` is 0..1 on that sector's board (Carrow: land west of the coast
  at x≈0.34–0.71, the scar around (0.51–0.58, 0.52–0.72)); `ThreatLevel` fills the meter;
  `ReconStill` (a captured level screenshot as a texture) replaces the card placeholder.
- **A sector**: add a row in `BuiltInSectors()`. Latitude/longitude are a target — the pin snaps
  to the nearest coast of the generated world. `bLive` needs destinations with that `SectorId`
  and (today) the Carrow board; a second live sector needs its own board coastline.
- **The planet look**: edit the HLSL strings in `ib_build_watch_materials.py`, re-run it.

## Verification checklist

1. Boot → sheet → DEPLOY → "THE WATCH IS LIVE" → the deck: planet turning, CARROW pin with the
   callout, roster shows you as HOST, card on GATE GARRISON.  ✔ (offline path, 09-08)
2. Drag / wheel work; click another pin → locked card + reason; double-click CARROW → board over
   the terrain; BACK TO ORBIT / Esc returns.  ✔ (board + back via dev tour, 09-08)
3. Host: DEPLOY → drop (aim, cut, fall, white-out) → travel to the garrison with pawn control;
   cursor gone (input-mode law).  ✔ travel (09-08); pawn control unchanged from v1
4. In the garrison: B opens the deck with tabs; CARROW-1 on the board → DEPLOY → back in the
   lobby with the Watch open, session intact.  ☐
5. Client (Shane): joins → deck, "THE HOST HOLDS THE TRIGGER", PROPOSE → host sees "<callsign>
   PROPOSES … — CONFIRM?" + cyan pulse on the board → CONFIRM & DEPLOY → both drop together.  ☐
6. Steam off: "OFF THE NET — SOLO" → DEPLOY → solo world.  ✔ (09-08)

The live lobby now opens WBP_MainMenu directly and removes only WBP_BootScreen's title gate.
Fresh standalone launches retain the boot screen. Recon stills are captured from the three
playable maps. The six closed sectors are flavor until their maps exist.

### Deployment regression check (2026-09-09)

`-ExecCmds="DisableAllScreenMessages,IB.DeploymentCheck"` from the default title map runs the
existing operative's DEPLOY button, verifies the listen lobby and Watch, clicks the Watch's
DEPLOY, waits for a possessed pawn in Carrow Gate, returns to the Watch and deploys again.
It creates a real host session and selects the existing operative; it sends no invites.
The check is excluded from Shipping/Test builds. Each arrival must remain stable for eight seconds.

Passed with Steam active, and again with Steam API initialization failing and the online
subsystem falling back to NULL. The latter reproduced the reported title-screen bounce:
SteamNetDriver was still available, but could not create a Steam socket. Every NULL/LAN
listen URL now carries `?bIsLanMatch`, selecting the driver's supported IP passthrough.
Steam URLs retain Steam transport. Logs: `Saved/DeploymentFix/steam-final.log` and
`Saved/DeploymentFix/fallback-final.log`. Remote two-player Steam travel remains unverified.
