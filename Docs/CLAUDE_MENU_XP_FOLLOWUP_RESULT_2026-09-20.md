# XP level-up follow-up — result (September 20–21, 2026)

Implements `Docs/CLAUDE_MENU_XP_FOLLOWUP_2026-09-20.md`. Source edits and one new check file
only. **No build, no process control, no git/lock operation, no commit/push/pull/merge, no
garrison work.** Unrelated edits and the Caryatid changes are untouched.

**Build barrier:** satisfied before starting. `Saved/ReferenceArtPass/build-fixes-20260920.log`
— `Result: Succeeded`, `Total execution time: 352.58 seconds`. That build covers the previous
eight-file change; **it does not cover anything in this document**, which has not been compiled.

Static review vs runtime verification is marked throughout. Nothing below was run.

---

## 1. Changed files

| File | Change |
|---|---|
| `Source/IronBreach/UI/IBMenuScreen.h` | `BindOperativeXP` → `BindOperativeEvents`, same for the unbind; handler renamed `HandleOperativeStateChanged`; contract documented. |
| `Source/IronBreach/UI/IBMenuScreen.cpp` | Both events bound/unbound together; stale XP comment corrected. |
| `Source/IronBreach/UI/IBMenuXPHeaderCheck.cpp` | **New.** Opt-in `IB.MenuXPHeaderCheck`. |

Nothing else was opened for writing. No Blueprint, content, config or project file.

---

## 2. The defect — confirmed, and my earlier claim was wrong

Codex is right and the previous result document was wrong. Re-read against current source:

- `Progression/IBXPSubsystem.cpp:159` broadcasts `OnXPAwarded`; `:163` broadcasts `OnXPLevelUp`,
  after it and only when the level actually moved.
- `Items/IBPlayerState.cpp:208` `HandleXPAwarded` → `SetOperativeXP` → `OnRep_OperativeXP` →
  `OnOperativeXPChanged`. The header redrew here — while `OperativeLevel` still held the **old**
  value, because nothing had updated it yet.
- `:200` `HandleXPLevelUp` → `SetOperativeLevel` → `OnRep_OperativeLevel` →
  `OnOperativeIdentityChanged`, which the header was **not** subscribed to.

So `LV n` stayed stale until the next award or a reopen. My previous claim — "a level-up already
broadcasts both, so the XP binding alone refreshes the whole header line including LV n" — had the
ordering backwards: both events do fire, but the one the header listened to fires *first*, and the
one carrying the new level fires second and went nowhere. Correcting that sentence is part of this
change; the old claim is withdrawn.

On clients the two are separate RepNotifies (`OperativeXP` and `OperativeLevel` each have their
own), so their arrival order is not ours to assume in either direction. The fix does not depend on
an order.

### The fix

`BindOperativeEvents()` now binds **both** `OnOperativeXPChanged` and `OnOperativeIdentityChanged`
to one handler, and `UnbindOperativeEvents()` removes both. They are bound and unbound as a pair so
they cannot drift apart. Every guarantee from the previous pass is preserved and now covers both:

- **unique** — `AddUniqueDynamic` for each, plus the "already bound to this state" early-out.
- **correct-old-state unbind** — both removals target `BoundOperativeState`, the object that was
  actually bound, not whatever is current. This is what makes player-state replacement safe.
- **replacement** — `NativeTick` re-resolves the owning state each frame (a pointer compare) and
  rebinds + redraws once when it moves.
- **reopen** — bound in `NotifyScreenOpened`, dropped in `NotifyScreenClosed`; screens are cached
  and reused (`UIBMenuSubsystem::GetOrCreateScreen`), so the reopen genuinely re-binds the same
  widget object.
- **teardown** — `NativeDestruct` drops both, for the world-teardown path that never calls close.
- The handler still early-outs on `!IsInViewport()`.

Either event redraws the whole header from the player state, so whichever lands second corrects
whatever the first drew early. XP award order and all gameplay/save behaviour are untouched: this
subscribes to an event that was already being broadcast.

**Stale comment corrected** in `RefreshTabBanner()`. It claimed "No XP fraction exists on the
client, so none is drawn" — written in pass 1, made false by the pass-2 replicated XP mirror. It now
says the XP total and the level's bounds replicate alongside the level, so every machine draws the
same real numbers.

`UIBInventoryScreen` is a second, unrelated listener on `OnOperativeIdentityChanged` (its character
preview, `IBInventoryScreen.cpp:460`). Different object, different function, no interaction.

---

## 3. The opt-in check — `IB.MenuXPHeaderCheck`

New file `Source/IronBreach/UI/IBMenuXPHeaderCheck.cpp`, following the existing check pattern:
`#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST`, a named namespace, `FAutoConsoleCommandWithWorld`,
timer-sequenced steps, `[XPHeader] PASS/FAIL/SKIP` lines and a `COMPLETE: n passed, n failed`
footer — the same shape as `IB.MenuConsistencyCheck` and `IB.MenuFlowCheck`.

### How it stays out of real save data

It **never calls `UIBXPSubsystem`** and never sets a progression value. It broadcasts the player
state's own public change events — the same ones replication and the award path raise — and watches
the real `UTextBlock` in the open header. Nothing is written to the XP ledger, the roster, a vault,
an inventory or any save game.

The only mutation is one text block's text: a sentinel is planted, the event is raised, and the
original text is restored whenever the redraw under test did not already replace it. `Complete()`
restores unconditionally as a backstop, so no failure path can leave the probe on screen.

That boundary was chosen deliberately. Driving the real award leg would write `UXPSaveGame` through
`GrantXP`, and `SetOperativeLevel` reaches `SyncLevelToRoster` → `UIBCharacterSubsystem::SetCharacterLevel`
→ `SaveRoster()` (`IBCharacterSubsystem.cpp:175-190`) for any operative that exists in the roster —
i.e. the real one. Writing and then restoring is still writing, so the check does not go there.

**What it therefore does not cover:** the award → delegate leg (`GrantXP` → `HandleXPAwarded` →
`SetOperativeXP`). That is left to the runtime pass in §5. The check covers the leg the regression
actually lived in: delegate → header.

### What it asserts

1. **Subscribed while open** — `OnOperativeXPChanged.IsBound()`. The header is that delegate's only
   listener, so `IsBound()` reflects it exactly. (`OnOperativeIdentityChanged` is deliberately not
   asserted this way, because the inventory screen is a second listener on it.)
2. **Control** — plant the sentinel, raise nothing, require it to survive. This proves the page does
   not redraw its header on its own; without it every assertion below could be a false PASS. If the
   control fails, the rest are downgraded to SKIP rather than reported as passes.
3. **Award order** — XP event redraws; then level event redraws (**this is the regression**).
4. **Client order** — level event redraws; then XP event redraws.
5. **Unsubscribes on close** — `!OnOperativeXPChanged.IsBound()` after `CloseMenu()`.
6. **Reopen rebinds** — reopen the cached screen, then both events redraw again.

It runs on **Inventory** (the Character page) on purpose. `UIBWatchScreen::NativeTick` calls
`RefreshTabBanner()` once a second (`IBWatchScreen.cpp:690`), which would redraw the header whether
or not any binding existed — running this on the Watch would pass no matter what. Inventory has no
`NativeTick` override at all, so only the base tick runs and it redraws only when the binding moves.
The control step in (2) is the guard that makes this assumption checkable rather than assumed.

The command polls (0.5 s, up to 45 s) for a menu subsystem and a player state with an operative
before starting, so it can be dropped into an existing QA run or typed at the console without
depending on a fixed moment. With no operative it logs a SKIP explaining why and completes — it does
not report a false pass.

### Exact command for Codex

After rebuilding, the console command is:

```
IB.MenuXPHeaderCheck
```

As a full run, in the same style as the existing QA chain, from the project root:

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -game -windowed -ResX=1600 -ResY=900 -WinX=100 -WinY=60 -NoSplash -NoSteam -NoSound -ExecCmds=DisableAllScreenMessages,IB.FrontendStyleCheck,IB.MenuXPHeaderCheck -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceArtPass\xpheader-20260921.log"
```

Both commands in `-ExecCmds` fire at startup; that is fine, because `IB.MenuXPHeaderCheck` waits for
an operative to be on station while `IB.FrontendStyleCheck` puts one there. Expect in the log:

```
[XPHeader] PASS header is subscribed while the screen is open
[XPHeader] PASS control: the header does not redraw on its own between events
[XPHeader] PASS award order: XP event redraws the header
[XPHeader] PASS award order: level event redraws the header (the stale-LV regression)
[XPHeader] PASS client order: level event redraws the header
[XPHeader] PASS client order: XP event redraws the header
[XPHeader] PASS header unsubscribes when the screen closes
[XPHeader] PASS reopened screen is rebound: level event redraws the header
[XPHeader] PASS reopened screen is rebound: XP event redraws the header
[XPHeader] COMPLETE: 9 passed, 0 failed
```

Against the **previous** build the two "level event redraws the header" lines would have been FAIL —
that is the regression this check exists to hold.

---

## 4. Mech two-client procedure — corrected

The previous procedure conflated two different swap paths. Codex is right; corrected here, and **no
mech gameplay was changed to match the mistaken expectation**.

### Two humans — `ServerRequestCrewSwap` → confirm handshake → `PerformPossessionSwap`

`IBMech_Base.cpp:709` takes the two-human branch only when both stations hold a `APlayerController`.
First press arms; the partner's press inside the window executes `PerformPossessionSwap` (`:753`),
which **exchanges possession**: `AssignToLeftSeat(GunnerPC)`, `AssignToRightSeat(DriverPC)`, the
parked pawns swap with their pilots, then `GunnerPC->Possess(this)` and `DriverPC->Possess(GunnerSeat)`.

Because the sheet reads each station pawn's PlayerState, the correct expectation is:

- station captions `HULL` / `GUNNER SEAT` stay fixed — **and so do their roles**: reseating runs
  `RecomputeRoles`, which rebuilds left = driver, right = gunner;
- the **occupant names exchange** between the two rows. That is the visible change, on host and
  client alike, and it is what proves the possession swap reached the UI.

The earlier text ("names stay put, roles follow the swap") described the wrong path.

### One human + AI co-pilot — legacy `PerformRoleSwap`

`IBMech_Base.cpp:718-728`: with either station held by a non-player controller it takes
`PerformRoleSwap()` (or `RequestRoleSwap`). Possession does **not** move, so:

- occupant names stay where they are;
- the roles exchange — visible only on the host, since the role column is authority-only by design.

### Post-disembark occupancy — AI backfill

`BackfillSeatWithAI()` (`:547`) runs at the end of `ServerDisembark`, `ServerHandleCrewLogout`
(`:656`) and `OnGameModeLogout` (`:706`). It fills **only the gunner seat**, and only when the hull
still holds a player: `bHullHasPlayer && GunnerSeat->GetController() == nullptr`. So:

- **Gunner leaves, hull still crewed** → `GUNNER SEAT` reads **`AI CO-PILOT`**, not `EMPTY`.
- **Navigator disconnects with a human gunner aboard** → `ServerHandleCrewLogout` (`:637-645`)
  promotes the gunner into the hull via the same `PerformPossessionSwap`, then disembarks the
  leaver. Expect the remaining human's name to move from `GUNNER SEAT` to `HULL`, and the seat to
  then read `AI CO-PILOT` once the backfill runs.
- **Last human leaves the hull** → the backfill's `bHullHasPlayer` test fails, so it does not run;
  `HULL` reads `EMPTY`. What the seat reads in that moment is not asserted here — observe it rather
  than assume it.

Everything else in the previous two-client procedure stands: `CREWING / LIVE READOUT` on the client,
real callsigns at both stations, an empty role column on the client and `DRIVER`/`GUNNER` on the
host, the solo-board `AI CO-PILOT` case, and two crewed mechs each showing their own frame.

---

## 5. Checks

### Static — performed

- Edits applied as exact single-match replacements; asserted on 0 or >1 matches.
- Line endings preserved: both `UI/` files CRLF, verified pure before and after; the new file
  written CRLF to match the folder.
- Brace and parenthesis balance verified on all three files (check file: 56/56, 180/180).
- No surviving reference to `BindOperativeXP`, `UnbindOperativeXP` or `HandleOperativeXPChanged`.
- Widget/delegate APIs used by the check are the ones the existing checks already use
  (`WidgetTree->ForEachWidget`, `UTextBlock::GetText/SetText`, `IsBound()`, `Broadcast()`,
  `FTimerDelegate::CreateLambda`, `FAutoConsoleCommandWithWorld`).
- Verified by reading source, not by running: `UIBInventoryScreen` has no `NativeTick` override;
  `UIBWatchScreen` refreshes the banner on a 1 Hz tick; `IBInventoryScreen.cpp:77` builds the shared
  hangar header, so the `LV n` probe exists on that page.
- The two modified files were mtime-guarded against the versions read; neither was rejected.

### Compile risks for the next build

1. `IBMenuXPHeaderCheck.cpp` is a new translation unit; UBT picks it up from the module directory,
   no project-file change needed. It is excluded from Shipping and Test by the `#if`.
2. `HandleOperativeStateChanged` must stay a `UFUNCTION()` for `AddUniqueDynamic`.
3. The check compares text with `FString ==` rather than `FText::EqualTo`, deliberately, to avoid
   culture-aware comparison semantics.

### Runtime — not performed, still required

- Nothing in this document has been compiled or run. The 352.58 s build predates it.
- Run `IB.MenuXPHeaderCheck` after the rebuild and confirm `9 passed, 0 failed`.
- The award → delegate leg is still only verifiable live: open a hangar page, take a kill on the
  listen host that crosses a level threshold, and watch **both** the XP figures and `LV n` update
  without reopening. Repeat on a client.
- The corrected two-client mech procedure in §4 remains unrun.

---

## 6. Recorded, not acted on

`qa-review-20260920.log:1941` and `:2176` — `BP_IBCharacter_Infantry_C_0: CurrentVisualData is
NULL! Check Blueprint Class Defaults.` Infantry, pre-existing, a Blueprint Class Defaults problem.
Recorded again here; not investigated, per the brief.

Still deferred, unchanged: M3, S1, S2, Q2 and the icon-reload micro-optimisation. S3 is closed.

Stopping here for Codex review.
