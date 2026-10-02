# XP-header check autorun — result (September 21, 2026)

Implements `Docs/CLAUDE_MENU_XP_AUTORUN_HANDOFF_2026-09-21.md`. Two files changed, both
development-only. **No build, no process control, no git or lock operation, no commit/push, no
garrison work, no unrelated edits.** Progression, saves and ordinary gameplay/menu behaviour are
untouched.

**Nothing here has been compiled or run.** The 54.57 s `build-xpheader-20260921.log` covers the
previous three-file change, not this one. Everything below is static.

---

## 1. Files changed

| File | Change |
|---|---|
| `Source/IronBreach/Online/IBDeploymentCheck.cpp` | New `-IBXPHeaderAfterDeploy` flag in the existing Phase-6 COMPLETE hook, made exclusive against the other menu-check flags. |
| `Source/IronBreach/UI/IBMenuXPHeaderCheck.cpp` | Sentinel watchdog, menu restored on completion, self-expiring re-entrancy guard. |

Both are already inside `#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST`, so none of this exists in a
Shipping or Test build.

---

## 2. Why the old sequence was unreliable, and what replaces it

`IB.FrontendStyleCheck` chains into `IB.DeploymentCheck`, which travels the menu world → lobby →
Carrow Gate → back → Carrow Gate. `IB.MenuXPHeaderCheck` schedules its poll and its whole sequence
on **world** timers, and a world timer manager dies with its world. Starting the check in the
initial `-ExecCmds` therefore raced the travel: at best it ran on a world about to be replaced, at
worst its timers were cancelled outright. Direct-launching Carrow Gate is not a way around it,
because `LoadRoster` invalidates `ActiveCharacterId` each run, so no operative would be on station.

The new flag starts the check from `IBDeploymentCheck`'s Phase-6 COMPLETE branch — the point where
the check already knows it is in `carrow_gate`, transport-verified, with a possessed pawn, stable
for 8 s, and no further travel scheduled. The XP check's world timers then live on the world they
will finish on.

### Exclusivity, not silent overlap

The completion hook now reads all five flags up front and treats `-IBXPHeaderAfterDeploy` as
exclusive. If it is passed together with `-IBReferenceMenusAfterDeploy`,
`-IBMenuConsistencyAfterDeploy`, `-IBMenuFlowAfterMenus` or `-IBSkillsAfterMenus`, the XP check is
**not** started and the run logs:

```
LogIronBreach: Error: [DeploymentCheck] -IBXPHeaderAfterDeploy NOT started: it is exclusive and
this run also passed one of -IBReferenceMenusAfterDeploy / -IBMenuConsistencyAfterDeploy /
-IBMenuFlowAfterMenus / -IBSkillsAfterMenus. Relaunch with -IBXPHeaderAfterDeploy as the only
menu-check flag.
```

The reason is concrete: the XP check watches one specific `UTextBlock` in the live header, and any
other suite clicking through tabs underneath it moves or rebuilds that widget. The existing suites
keep running exactly as before in that case — the conflict never silently disables work that used
to happen, it only declines to add the new check on top. **With the new flag absent, behaviour is
byte-for-byte what it was.**

Note `-IBMenuFlowAfterMenus` and `-IBSkillsAfterMenus` chain from `IB.MenuConsistencyCheck`, so on
their own they are inert; they are included in the conflict test so that passing them with the XP
flag produces an explanation rather than a silently ignored intent.

---

## 3. Sentinel cleanup — the leak that existed, and the fix

Reviewed as asked. There was one real window.

`Raise()` plants the sentinel, broadcasts, verifies and restores inside a single callback — no gap.
But the **control step** plants at `At(2.0)` and verifies at `At(2.6)`, and the whole sequence runs
on world timers. If the world went away in that 0.6 s, or any step returned early, the probe text
was left behind. That matters more than it first looks: menu screens are cached by
`UIBMenuSubsystem`, which is a **local player** subsystem, so a cached screen can outlive the world
whose timers died — and be shown again later still reading `IB XPHEADER PROBE`.

Three small fixes, no framework:

1. **Core-ticker watchdog.** `ArmSentinelWatchdog()` is armed as the sequence begins and fires once
   after 20 s on `FTSTicker::GetCoreTicker()` — the same ticker `IBDeploymentCheck` uses precisely
   because it survives world replacement. If the probe still shows the sentinel it restores the
   original and logs a warning. It holds the run state alive by shared reference, so the recorded
   original text is still there to restore. This covers every leak path at once: the control gap, an
   early return, and world loss.
2. **Menu restored on completion.** `Complete()` now calls `CloseMenu()` (guarded, a no-op when
   nothing is open). The check runs in a live gameplay map now, not the menu map, so leaving
   Inventory open would strand the player in UI-only input.
3. **Self-expiring re-entrancy guard.** A second invocation while one is running would plant a
   sentinel over the first run's recorded original and the two would restore each other's text. The
   guard is a timestamp, not a flag, expiring after 90 s, so a run stranded by a teardown cannot
   lock the command out for the rest of the session.

The check still never calls `UIBXPSubsystem`, never sets a progression value, and never writes the
XP ledger, roster, vault, inventory or any save game. The only mutation remains one text block's
text, now with three independent paths that put it back.

---

## 4. Exact launch arguments — one process

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -game -windowed -ResX=1600 -ResY=900 -WinX=100 -WinY=60 -NoSplash -NoSteam -NoSound -IBXPHeaderAfterDeploy -ExecCmds=DisableAllScreenMessages,IB.DeploymentCheck -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceArtPass\xpheader-autorun-20260921.log"
```

That is the same shape as the run that produced `qa-review-20260920.log`, with two differences:
`IB.DeploymentCheck` is the only `-ExecCmds` entry (no `IB.FrontendStyleCheck`, which is what was
chaining into travel), and `-IBXPHeaderAfterDeploy` is the only menu-check flag. No map argument —
`IB.DeploymentCheck` requires the Watch as its starting world and `GameDefaultMap` already is it.

The console command alone still works, if the game is already sitting in a settled world with an
operative on station:

```
IB.MenuXPHeaderCheck
```

### Expected log

```
LogIronBreach: Display: [DeploymentCheck] PASS listen lobby and Watch ...
LogIronBreach: Display: [DeploymentCheck] PASS Carrow Gate arrival stable for 8s ...
LogIronBreach: Display: [DeploymentCheck] PASS return to Watch ...
LogIronBreach: Display: [DeploymentCheck] PASS Carrow Gate redeployment stable for 8s ...
LogIronBreach: Display: [DeploymentCheck] COMPLETE
LogIronBreach: Display: [XPHeader] PASS header is subscribed while the screen is open
LogIronBreach: Display: [XPHeader] PASS control: the header does not redraw on its own between events
LogIronBreach: Display: [XPHeader] PASS award order: XP event redraws the header
LogIronBreach: Display: [XPHeader] PASS award order: level event redraws the header (the stale-LV regression)
LogIronBreach: Display: [XPHeader] PASS client order: level event redraws the header
LogIronBreach: Display: [XPHeader] PASS client order: XP event redraws the header
LogIronBreach: Display: [XPHeader] PASS header unsubscribes when the screen closes
LogIronBreach: Display: [XPHeader] PASS reopened screen is rebound: level event redraws the header
LogIronBreach: Display: [XPHeader] PASS reopened screen is rebound: XP event redraws the header
LogIronBreach: Display: [XPHeader] COMPLETE: 9 passed, 0 failed
```

**Expected completion: `[XPHeader] COMPLETE: 9 passed, 0 failed`**, roughly 9 s after
`[DeploymentCheck] COMPLETE`. Deployment itself takes up to ~180 s and has its own timeout.

Greps for the whole run: `[DeploymentCheck] COMPLETE`, `[XPHeader] COMPLETE`, and
`FAIL` / `SKIP` / `NOT started`.

---

## 5. Reading the result honestly

- `COMPLETE: 9 passed, 0 failed` is the pass condition.
- Any `FAIL` on the two **"level event redraws the header"** lines means the identity/level
  subscription regressed — that is the line this check exists to hold.
- A `FAIL` on **"control: the header does not redraw on its own between events"** invalidates the
  run rather than reporting a product bug: it means the page redrew its header without an event, so
  the remaining assertions are downgraded to `SKIP` and nothing after it should be read as a pass.
- `SKIP no operative on station after 45 s` means the deployment left no operative on the player
  state — a harness problem, not a header problem.
- `SKIP ... the probe is ambiguous` / `no "LV n" line` means the probe could not be located. Not a
  failure of the binding; the check declines to guess.
- `[XPHeader] probe text outlived the run; restored by the watchdog.` is a warning worth reading: it
  means the sequence did not finish cleanly, so treat the counts as incomplete.

---

## 6. Static checks performed

- Both edits applied as exact single-match replacements, asserted unique before writing.
- `IBDeploymentCheck.cpp` had **mixed line endings**: six LF-only lines (138–143), exactly the two
  chained-flag blocks an earlier pass inserted into a CRLF file. Those lines are inside the region
  replaced here, so the file is now uniformly CRLF — verified zero LF-only lines afterwards. No
  other line was touched.
- `IBMenuXPHeaderCheck.cpp` stays uniformly CRLF.
- Brace and parenthesis balance verified on both files (deployment 32/32 and 144/144; check 63/63
  and 197/197).
- `FTSTicker` / `FTickerDelegate` usage and the `Containers/Ticker.h` include mirror
  `IBDeploymentCheck.cpp`, which already uses the core ticker for the same reason.
- Verified by reading source, not by running: `UIBMenuSubsystem::CloseMenu()` early-outs when no
  menu is open (`IBMenuSubsystem.cpp:113-116`), so the new cleanup call is safe on every path; the
  Phase-6 branch runs with a valid `PC` and returns `false` immediately afterwards, so the console
  command is issued exactly once.

### Compile risks for the next build

1. `Containers/Ticker.h` is the only new include; `FPlatformTime::Seconds()` arrives via CoreMinimal.
2. The new `UE_LOG` uses adjacent `TEXT()` literal concatenation for its format string — a compile-
   time concatenation, still a single literal.
3. No new UHT-reflected types, so no header regeneration beyond the two translation units.

---

## 7. Remaining limits

- **Not compiled, not run.** No claim is made about either.
- The fix makes the check robust against the travel that exists **today**. If a future change adds
  another world transition after `[DeploymentCheck] COMPLETE`, the same world-timer fragility
  returns — the check is anchored to "the last world deployment leaves you in", not to travel in
  general.
- The check still covers only the delegate → header leg. The award → delegate leg
  (`GrantXP` → `HandleXPAwarded` → `SetOperativeXP`) is still excluded on purpose, because driving
  it writes `UXPSaveGame` and, through `SyncLevelToRoster`, `SaveRoster()`. Confirming it live
  remains a manual step: take a kill that crosses a level threshold with a hangar page open and
  watch both the XP figures and `LV n` move without reopening.
- The watchdog restores the probe text, but if the player state or the screen has been destroyed
  there is nothing to restore and nothing to report — silence there is expected, not a fault.
- Out of scope and still unverified, as stated in the handoff: remote two-client mech crew
  replication, and menu visual fidelity (the Character screenshot's white placeholder body).
- No garrison work was done. The rear-hangar / forward-pad / right-dock notes are text only; the
  generated reference image has not been recovered, so nothing was implemented from them.

Stopping here for Codex review.
