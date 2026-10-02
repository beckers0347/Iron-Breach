# XP-header check crash — cause and fix (September 21, 2026)

Fixes the `EXCEPTION_ACCESS_VIOLATION` reported in `Docs/CLAUDE_MENU_XP_CRASH_HANDOFF_2026-09-21.md`.
**One file changed**, development-only. No build, no process control, no git or lock operation, no
save change or restore, no asset or garrison work. The production XP/identity binding
(`UI/IBMenuScreen.h/.cpp`) and the `-IBXPHeaderAfterDeploy` flag (`Online/IBDeploymentCheck.cpp`)
are untouched.

**Not compiled, not run.** Everything below is read from source and the crash evidence. No claim is
made that this build succeeds or that the check now passes.

---

## 1. Cause — a use-after-free, and Codex's hypothesis was right

The crash is a use-after-free of the check's own run state. The chain, all in
`UI/IBMenuXPHeaderCheck.cpp` as it stood:

1. The console command created the state as a shared reference on its own stack:
   `const TSharedRef<FRun> Run = MakeShared<FRun>();` (old line 258).
2. It handed a copy to the polling timer's lambda: `SetTimer(Run->Wait, ...CreateLambda([W, Run](){...}), 0.5f, /*bLoop=*/true)` (old line 263).
3. The console command then returned, destroying its local. **From that moment the capture inside
   the poll delegate was the only strong reference to `FRun`.**
4. The poll fired, found the menu subsystem and an operative, and called
   `Live->GetTimerManager().ClearTimer(Run->Wait);` (old line 285) — clearing a *repeating* timer
   **from inside its own callback**. `FTimerManager` removes the `FTimerData`, which destroys the
   `FTimerUnifiedDelegate` it owns, which destroys the lambda object — and with it the captured
   `TSharedRef`. The reference count reached zero and `FRun` was freed while the callback was still
   executing on it.
5. Old lines 286–287 then used the destroyed capture: `Run->State = PS;` and
   `RunSequence(Live, Menu, Run);`. `RunSequence` copied that dangling reference into
   `ArmSentinelWatchdog` and into every `At()` step lambda.
6. At `At(1.5f)` the step ran on freed memory and faulted.

### Why the fault landed on line 193 and not 192

```
192   Run->Probe = Line;              // TWeakObjectPtr assignment: two integers written, nothing read
193   Run->Original = Line->GetText(); // FText assignment: must RELEASE the destination's existing
                                       // internal text data, i.e. dereference a pointer inside FRun
```
Line 192 only writes into freed memory, which does not fault on a still-mapped page. Line 193 has to
read the destination `FText`'s internal reference-counted pointer before replacing it, and that
field held the freed-memory fill pattern — hence `EXCEPTION_ACCESS_VIOLATION reading
0xffffffffffffffff`, exactly the address in the crash context. The reported frame is where the
corruption *surfaced*, not where it happened; the damage was done one callback earlier, at the
`ClearTimer`.

The timing corroborates it: `[DeploymentCheck] COMPLETE` at 02:57:55, crash at 02:57:59 — the poll
at ~+0.5 s, then the `At(1.5f)` step ~2 s later, with no `[XPHeader]` line ever emitted because the
first step never finished.

**Not the cause:** the widget traversal and the `FText` copy themselves are sound.
`WidgetTree->ForEachWidget` is the same traversal `IB.MenuConsistencyCheck` already uses, and
`FText` assignment is only the victim here. They were inspected as the brief asked and left alone.

### Also fixed: the stale watchdog

Independently of the crash, `Complete()` reset the guard but left the 20 s core-ticker watchdog
scheduled. A run finishing at +8 s and a new run starting at +10 s meant the *first* run's watchdog
fired at +20 s into the *second* run: it could restore run 2's probe with run 1's remembered text —
silently turning run 2's control step into a false PASS — and could clear the guard while run 2 was
still going, letting a third run start on top. Codex identified this correctly.

---

## 2. Changed file

| File | Change |
|---|---|
| `Source/IronBreach/UI/IBMenuXPHeaderCheck.cpp` | Ownership fix for the crash; run identity; watchdog cancellation; stale source comment removed. |

Nothing else was opened for writing.

---

## 3. How ownership and cleanup work now

**Two independent strong owners, so no delegate's death can free the state.**

- `static TSharedPtr<FRun> ActiveRun` is set when the command starts. It is the one strong owner
  that is *not* a delegate capture, so destroying any callback — including one destroying itself —
  cannot take the state with it.
- The poll callback additionally takes `const TSharedRef<FRun> Keep = Run;` as its **first
  statement**, before anything can clear the timer, and uses `Keep` for the rest of the body. This
  is the part that actually fixes the crash, and it is needed even with `ActiveRun`: after
  `ClearTimer` the closure's captured reference is a destroyed object, so *reading it* is invalid
  regardless of whether the pointee survives. `Keep` is a stack local in the callback's own frame,
  untouched by the closure's destruction, and it keeps `FRun` alive across the clear — which also
  makes `ClearTimer`'s write-back into `Keep->Wait` land on live memory.

**Run identity, so a late callback cannot touch a later run.**

- Each run gets `Id` from a monotonic counter and `StartedAt`.
- `IsCurrentRun(Run)` is `ActiveRun.IsValid() && ActiveRun->Id == Run->Id`.
- Every site that writes the probe widget or reports a result is guarded by it: `Check()`,
  `Raise()`, the control step's plant and verify, `Complete()`, and the watchdog. A superseded run
  returns silently — it does not restore, does not log, does not count.

**Watchdog cancellation.**

- `ArmSentinelWatchdog` stores its `FTSTicker::FDelegateHandle` on the run.
- `Complete()` removes it, so a finished run leaves nothing scheduled.
- If it fires anyway, it clears its own handle first, then refuses to act unless it is still the
  current run. Only a genuinely stranded run reaches the restore, and only that case resets
  `ActiveRun` so a later invocation can start.

**Guard expiry.** `IsRunActive()` is `ActiveRun.IsValid() && now - StartedAt < 120 s`. A run stranded
by a world teardown cannot lock the command out for the session, and identity is what makes that
expiry safe: the stranded run's late callbacks see a different `Id` and do nothing.

The probe remains non-saving: no `UIBXPSubsystem` call, no progression value set, no save game
written. The only mutation is still one text block's text, now with three guarded paths that put it
back.

---

## 4. Correction to my previous document

The autorun result described the *check* as writing no save data, which is accurate for the check.
It should not be read as a claim about the whole run, and Codex is right to draw the line: the
deployment leg that precedes it selects and loads an operative, so `IBCharacters` and `Vault` do
change during a full `-IBXPHeaderAfterDeploy` run, as the before-hashes in
`xpheader-autorun-save-before.json` show. XP and Ledger were unchanged. Stated plainly here so the
distinction is on the record: **the XP probe is non-saving; the run that carries it is not.**

---

## 5. Launch and expected output — unchanged

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -game -windowed -ResX=1600 -ResY=900 -WinX=100 -WinY=60 -NoSplash -NoSteam -NoSound -IBXPHeaderAfterDeploy -ExecCmds=DisableAllScreenMessages,IB.DeploymentCheck -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceArtPass\xpheader-autorun-20260921b.log"
```

Still the only menu-check flag; the other four remain mutually exclusive with it and are rejected
with an Error if combined.

Target, after the four `[DeploymentCheck] PASS` lines and `[DeploymentCheck] COMPLETE`:

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

**`COMPLETE: 9 passed, 0 failed`**, roughly 9 s after `[DeploymentCheck] COMPLETE`. A run that
reaches `COMPLETE` with fewer than nine results has skipped steps and is not a pass — the SKIP lines
say which, and a `FAIL` on the control line invalidates the run rather than reporting a product bug.
Nothing in this change turns a failed or skipped run into a PASS; the identity guards make a stale
run report *less*, never more.

---

## 6. Static checks performed

- The edit was applied as exact single-match replacements, asserted unique before writing.
- Brace and parenthesis balance verified (70/70, 222/222); file remains uniformly CRLF.
- Verified no reference to the removed `RunStartedAt` guard survives.
- Verified every `SetText` on the probe and every `Check()` call now sits behind an
  `IsCurrentRun` guard.
- Traced the ownership claim in §1 directly in source: `MakeShared` at the command scope, the single
  capture into the poll delegate, and both `ClearTimer` sites followed by further use of that
  capture (the timeout path at old line 278 had the same defect and is fixed the same way).

### Compile hotspots

1. `FTSTicker::FDelegateHandle` is now stored on `FRun` and cleared with `.Reset()` / tested with
   `.IsValid()`. Both members exist on the handle type in UE 5.8; if the signature differs, that
   field and its three uses are the whole fix.
2. `FTSTicker::GetCoreTicker().RemoveTicker(Handle)` is the counterpart to the existing `AddTicker`.
3. No new includes, no UHT-reflected types, one translation unit.

---

## 7. Honest limits

- **Not built and not run.** No success of any kind is claimed for this change.
- The diagnosis is from the crash context plus source, not from a debugger on a live process. It
  explains the faulting line, the fault address and the timing, and the `ClearTimer`-inside-its-own
  -callback pattern is present at both sites — but a rerun is what confirms it.
- If the rerun crashes again, the next things to look at are the `At(1.5f)` step's widget traversal
  against a screen that is mid-teardown, and whether `GetActiveScreen()` can hand back a partially
  constructed widget on that world.
- The check still covers only the delegate → header leg. The award → delegate leg remains a manual
  runtime check, for the save-writing reason given before.
- Out of scope and untouched: `Docs/CLAUDE_MENU_CREW_QA_HANDOFF_2026-09-21.md` (queued, not
  assigned), remote two-client mech crew replication, menu visual fidelity, and the garrison layout,
  which still awaits the reference image.

Stopping here for Codex to rebuild and rerun.
