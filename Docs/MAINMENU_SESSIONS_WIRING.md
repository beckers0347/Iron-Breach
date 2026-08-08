# Main Menu — Session Flow Wiring (demo d1 + d5)

New C++: `UIBMainMenuWidget` (UI/) + status events on `UIBSessionSubsystem`.
The menu gets Host / Join / Solo / Quit with live status text — a packaged
demo can't host through PIE settings, so this is how two players get in.

## Wiring (Connor, ~5 min, after next build)
1. Open **WBP_MainMenu** → File → **Reparent Blueprint** → `IBMainMenuWidget`.
2. Name (or add) widgets — every bind is optional, any subset works:
   - `Btn_Solo`  — your current fullscreen BeginButton, renamed
   - `Btn_Host`, `Btn_Join` — new buttons for the co-op demo
   - `Btn_Quit`  — the existing invisible ExitButton, renamed
   - `Txt_Status` — a TextBlock for the narration line ("SCANNING FOR SQUADS…")
3. **Delete the old BP OnClicked graphs** (Begin/Exit) — C++ owns the clicks
   now; leftover BP graphs would double-fire.
4. Style freely. `On Session Status` BP event fires on every beat if you want
   pulses/flickers per state.

## What the code guarantees
- Solo → `/Game/FirstPerson/Lvl_FirstPerson`. Host → same map `?listen`
  (changed from stale `Lvl_Plains` so host and solo share one world).
- Input mode is forced GameOnly + cursor hidden BEFORE any travel (the
  menu-freeze lesson), and handed back (UIOnly + cursor) on failure.
- Failures narrate: no sessions found / join refused / no online service.
  Buttons re-enable; Quit is never disabled.
- Subsystem status events are BlueprintAssignable — HUD/other widgets can
  listen too.

## Test (after build, when Connor has the machine back)
1. PIE (1 player, "Play As Listen Server" off): Solo works as before; menu
   never freezes the level (cursor gone, input live).
2. Two packaged/standalone instances on one machine (NULL OSS = LAN):
   instance A Host → lands in Lvl_FirstPerson listening; instance B Join →
   should find + connect. Status text narrates each step.
3. Join with NO host up: "NO SQUADS ON THE NET — HOST ONE?" and the menu
   comes back. This is the case that used to look like a dead game.
4. Steam test (both machines Steam running, AppID 480): same flow online.
   Expect strangers' spacewar sessions possible on 480 — known dev-AppID noise.
