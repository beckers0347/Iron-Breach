# Two-process mech crew verification — implementation and procedure (September 21, 2026)

Implements `Docs/CLAUDE_MENU_CREW_QA_HANDOFF_2026-09-21.md`. **One new file**, development-only and
opt-in. No build, no process launch or control, no git or lock operation, no gameplay or network
configuration change, no garrison work, no XP edits, no save restores.

**Nothing here has been compiled or run.** No PASS is claimed for anything below.

---

## 1. Changed files

| File | Change |
|---|---|
| `Source/IronBreach/UI/IBMechCrewQACheck.cpp` | **New.** Two console commands: `IB.CrewQAHost` and `IB.CrewQAClient <address>`. |

Nothing else was opened for writing. `IBMechScreen`, `IBMech_Base`, `IBMenuScreen`,
`IBMenuXPHeaderCheck`, `IBDeploymentCheck` and all config are untouched. The whole file is inside
`#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST`, so none of it exists in a Shipping or Test build, and
neither command runs unless typed or passed in `-ExecCmds`.

---

## 2. Two things I checked first that shape the whole design

**The `ECC_Visibility` blocker does not apply.** `AIBCharacter_Infantry::Server_RequestBoard`
(`IBCharacter_Infantry.cpp:991`) validates **authority and distance only** — no visibility trace.
So the outstanding `BP_Mech` → `MechMesh` collision item from the Caryatid handoff §6.1 blocks the
`E` interaction path but **not** this automated one. Boarding can be driven today.

**The client process is nearly save-safe by construction.** On a client: `UIBXPSubsystem::SaveNow`
is gated by `HasServerAuthority()` (`IBXPSubsystem.cpp:311-317`), `AIBPlayerState::SaveVaultNow`
by `HasAuthority()`, and `SyncLevelToRoster` by `bHasOperative` — which a process that joins with
`open` never has. The one residual write is the XP save at `Deinitialize` **if the client ends its
life back in a standalone world**; `-UserDir` closes it. That is a narrow, specific exposure rather
than a vague worry, and §6 says exactly what to do about it.

---

## 3. What the check does

### Host — `IB.CrewQAHost`

Drives the real crew lifecycle so the client has something true to observe. Every step is an
existing entry point; nothing sets `HullOccupancy` or `SeatOccupancy`, which are still written only
by the mech's own `RefreshCrewView`:

| Phase | Action | Assertion |
|---|---|---|
| 0 | wait for two humans | listen server, two distinct non-bot player states |
| 1 | position both pawns, then `Server_RequestBoard(Mech, true)` on each | two boarding requests issued |
| 2 | — | hull and gunner seat hold two different humans |
| 3 | `ServerRequestCrewSwap(hull)` then `ServerRequestCrewSwap(seat)` inside the 5 s window | logs who armed and who confirmed |
| 4 | — | both stations still human, after `PerformPossessionSwap` |
| 5 | `ServerDisembark(seat human)` | — |
| 6 | — | the seat is held by a non-player controller (the AI backfill) |
| 7 | `ServerDisembark(hull human)` | — |
| 8 | — | the hull holds no human; the seat's controller is logged as OBSERVED, not asserted |

**The one harness liberty** is positioning: both test pawns are moved next to the hull before
boarding. That is not a boarding bypass — `Server_RequestBoard`'s `BoardMaxDistance` check still
runs and must pass, and its passing is itself part of the evidence. Both pilots ask for the hull;
`ServerBoard`'s own correction logic decides who ends up in the seat, so the seat assignment is the
product's, not the test's.

### Client — `IB.CrewQAClient <address>`

Connects, then **watches**. It never drives crew state: each phase waits for a condition to appear
and asserts what the real widgets render when it does. That means the two processes need no clock
agreement — only the host actually doing the work — and a slow step produces a TIMEOUT naming the
phase instead of a misleading FAIL.

| Phase | Waits for | Asserts |
|---|---|---|
| 0 | `NM_Client` + two humans | genuinely a remote client of the host's map; two distinct human player states, one of them local |
| 1 | menu subsystem | the real Mech page opens |
| 2 | two distinct human station occupants | each station names its own occupant; the two differ; **both role cells blank** |
| 3 | the two rendered names to have exchanged | exchange happened; each cell still matches the pawn's actual occupant; roles still blank |
| 4 | seat reads `AI CO-PILOT` | the seat pawn carries **no** human player state; the hull still names its human |
| 5 | hull reads `EMPTY` | hull carries no human player state; roles blank; the seat's text is logged as OBSERVED |

Screenshots (absolute, under the real `Saved/` even when a process runs with `-UserDir`):

```
D:\Unreal Games\IronBreach\Saved\MechCrewQA\client-crewed.png
D:\Unreal Games\IronBreach\Saved\MechCrewQA\client-swapped.png
D:\Unreal Games\IronBreach\Saved\MechCrewQA\client-backfill.png
D:\Unreal Games\IronBreach\Saved\MechCrewQA\client-departed.png
```

### Expectations are independent of the code under test

Required, and done three ways:

1. **`ExpectedOccupant()` is not `UIBMechScreen::StationOccupant`.** It re-derives the name from the
   station pawn's own replicated `PlayerState`, which reaches every machine. The file contains no
   call to the display helper at all — only a comment saying why.
2. **The exchange assertion uses no helper whatsoever.** It compares rendered text across time:
   hull-after must equal seat-before and vice versa. A bug in the display path cannot satisfy that
   by agreeing with itself.
3. **The AI backfill is corroborated, not taken on the sheet's word.** `AI CO-PILOT` is only
   accepted when the seat pawn independently carries no human player state.

The row is located by its caption and read in slot order — `[caption, occupant, role]` — so nothing
depends on the screen's private members either.

### Last-human departure — derived from code, not wished for

`ServerDisembark` (`IBMech_Base.cpp:590-622`) vacates the seat, re-possesses the parked pawn, then
calls `BackfillSeatWithAI`, whose `bHullHasPlayer` test (`:551`) now fails — so it neither fills the
hull nor **evicts the AI already in the seat**. Predicted state: **HULL `EMPTY`, GUNNER SEAT
`AI CO-PILOT`**. The check asserts the hull and *logs* the seat as `OBSERVED`, so a surprise is
reported rather than converted into a failure of the sheet.

A wholly empty frame is therefore not observable in a one-mech map, and the check says so explicitly
with the actor count rather than quietly skipping.

### The XP crash lesson, carried forward

Both commands run on `FTSTicker::GetCoreTicker()` — needed anyway, because the client travels worlds
— and each is stopped by **returning false**, never by clearing itself from inside its own callback.
The file contains no `ClearTimer` at all, so the delegate-destroys-its-own-state failure mode cannot
occur here. State lives in the ticker lambda's own init-captures, which remain valid for the whole
call and are destroyed only after it returns.

---

## 4. Exact procedure

Two processes, **host first**. The host is the existing, already-proven deployment run; only the
trailing flag differs.

### Process 1 — host

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -game -windowed -ResX=1280 -ResY=720 -WinX=40 -WinY=40 -NoSplash -NoSteam -NoSound -port=7777 -ExecCmds=DisableAllScreenMessages,IB.DeploymentCheck -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceArtPass\crewqa-host-20260921.log"
```

Wait for `[DeploymentCheck] COMPLETE` in that log — the host is then a listen server settled in
Carrow Gate with a pawn. Then, in that window's console:

```
IB.CrewQAHost
```

`-port=7777` pins the listen port so the client's address is deterministic. It is a launch argument,
not a project setting; no `.ini` was touched. `-NoSteam` keeps the run on NULL OSS and `IpNetDriver`,
which is what the existing QA runs already use.

### Process 2 — client (start only after `[DeploymentCheck] COMPLETE`)

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -game -windowed -ResX=1280 -ResY=720 -WinX=700 -WinY=40 -NoSplash -NoSteam -NoSound -UserDir=CrewQAClient -ExecCmds=DisableAllScreenMessages,"IB.CrewQAClient 127.0.0.1:7777?Name=GUNNER" -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceArtPass\crewqa-client-20260921.log"
```

`IB.CrewQAHost` can be issued before or after the client starts — the host's phase 0 waits for the
second human.

**`?Name=GUNNER` matters.** Two processes on one machine with NULL OSS otherwise receive the same
default player name, and the name-exchange assertion cannot distinguish two identical strings. The
option is read by `AGameModeBase::InitNewPlayer`; it is a connect-URL option, not a config change.
If the names do collide anyway, phase 0 logs a SKIP saying exactly that instead of passing.

### Reading the result

Host log: `[CrewQAHost] COMPLETE: 7 passed, 0 failed`.
Client log: `[CrewQAClient] COMPLETE: 11 passed, 0 failed`.

The two logs are meant to be read together: the host records which named human it put where and
when it swapped and dismounted them; the client records what the sheet rendered. Cross-checking them
is the real evidence, and it does not pass through any shared helper.

Greps: `[CrewQAHost]`, `[CrewQAClient]`, `FAIL`, `TIMEOUT`, `SKIP`, `OBSERVED`, `COMPLETE`.

### Timeouts and cleanup — Codex owns both processes

- Host ticker: hard stop at 240 s from `IB.CrewQAHost`; if no mech exists it fails within ~20 s.
- Client ticker: hard stop at 300 s; each observation phase times out at 90 s naming the phase and
  the text it last read.
- Both processes log `COMPLETE` and then **keep running** — neither closes itself, by design, since
  process control is yours. Expect ~60–90 s of work after the client connects. Close the client
  first, then the host.
- The check leaves the menu open on the client; it changes no gameplay state that outlives the
  process.

---

## 5. Blockers and honest limits

**Unverified preconditions that will decide whether this runs at all:**

1. **Is there an `AIBMech_Base` in CarrowGateGarrison?** I cannot tell from source. If not, the host
   fails in ~20 s with `no AIBMech_Base in <map>` and the run must move to a map that has one. This
   is the single most likely reason for a no-op first attempt.
2. **Does `-UserDir=` isolate saves in 5.8?** I have not verified it, and I will not claim it.
   **Verify before trusting it:** start the client, and within a few seconds confirm
   `D:\Unreal Games\IronBreach\CrewQAClient\Saved\` has appeared. If it has not, stop the client —
   without isolation it shares `Saved\SaveGames\` with the host, and the residual XP write in §2
   could overwrite host progress. I have deliberately not added an isolation flag of my own, per
   the brief.
3. **Does the client's `ClientTravel` reach the host?** `-NoSteam` should put both on `IpNetDriver`.
   If the connect fails, the client sits in phase 0 and TIMEOUTs at 300 s with no assertions — that
   is a connection problem, not a sheet problem, and the log will show only the `connecting to …`
   step.

**Limits of what a PASS would mean:**

- The client has **no operative identity** (it joins with `open`, bypassing operative selection), so
  its name comes from `GetPlayerName()` rather than a callsign. Name coverage is still real and
  distinct, but the `AIBPlayerState::GetDisplayCallsign` callsign branch is exercised only for the
  host's occupant, not the client's. The brief asked for this to be stated rather than guessed.
- Roles are asserted **blank** on the client, which is the intended design, not a limitation — but
  it also means this run does not verify `DRIVER`/`GUNNER` text anywhere. That remains host-only and
  is not covered here.
- A wholly empty frame is not covered in a one-mech map; the check reports the actor count so the
  gap is visible.
- Compile hotspots: `APlayerState::IsABot()`, `UWidgetTree::ForWidgetAndChildren`,
  `FAutoConsoleCommandWithWorldAndArgs`, and calling the `Server, Reliable, WithValidation`
  `Server_RequestBoard` from server code (which executes locally on the authority). Each is used
  once and is easy to adjust if a signature differs.
- Not compiled, not run. No screenshot in the list above exists yet.

Out of scope and untouched: character preview fidelity, the garrison layout (still waiting on the
generated overhead concept — nothing was implemented from the text-only notes), and any further XP
work.

Stopping here for your build and runtime review.
