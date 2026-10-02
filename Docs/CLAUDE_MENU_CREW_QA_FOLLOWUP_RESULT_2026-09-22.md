# Crew QA launch, isolation and reporting corrections (September 22, 2026)

Implements `Docs/CLAUDE_MENU_CREW_QA_FOLLOWUP_2026-09-22.md`. Two files changed, both
development-only. No build, no process launch or control, no git or lock operation, no save
operation of any kind, no gameplay/menu/network config change, no assets, no garrison, no XP work.

**Nothing here has been compiled or run.** The 287.84 s `build-crewqa-20260922.log` covers the
previous version of the check, not this one. No runtime success is claimed.

---

## 1. Changed files

| File | Change |
|---|---|
| `Source/IronBreach/Online/IBDeploymentCheck.cpp` | New `-IBCrewQAAfterDeploy` flag on the existing COMPLETE hook, mutually exclusive with every other menu-check flag including `-IBXPHeaderAfterDeploy`. |
| `Source/IronBreach/UI/IBMechCrewQACheck.cpp` | Readiness gate before boarding; longer, explicitly open-loop holds; net-driver/listen-address evidence; pass/fail/skip/timeout tally with an honest COMPLETE verdict; name-collision now stops the run; screenshots moved to `Saved/MechCrewQA/shots/`. |

Nothing else opened for writing. Both files remain inside `#if !UE_BUILD_SHIPPING && !UE_BUILD_TEST`.

---

## 2. Host now starts itself (correction 1)

`-IBCrewQAAfterDeploy` issues `IB.CrewQAHost` from `IBDeploymentCheck`'s Phase-6 COMPLETE branch —
the same settled-world hook `-IBXPHeaderAfterDeploy` already uses. No console typing, so a hidden
process works.

The host command then **waits** for a second human, so it is safely started before the client
process even exists. That is what makes a one-shot `-ExecCmds` launch viable.

Exclusivity is now a matrix rather than a special case: `bOtherSuites` covers the four original
flags, and `-IBXPHeaderAfterDeploy` and `-IBCrewQAAfterDeploy` each refuse to start if any other
menu-check flag — including the other exclusive one — is present, logging an Error that names the
conflict. With none of the new flags present, the hook behaves exactly as before.

---

## 3. Save isolation (correction 2)

Using the source facts you verified: `ProjectUserDir()` returns the `-UserDir` argument (absolute
values normalized, relative ones combined with `ProjectDir`), `ProjectSavedDir()` derives from it,
and `GetSaveGamePath` is `ProjectSavedDir() + SaveGames/<name>.sav`. **Both** processes therefore
get their own absolute sandbox:

| Process | `-UserDir` | Resulting SaveGames |
|---|---|---|
| host | `D:\Unreal Games\IronBreach\Saved\MechCrewQA\host` | `…\Saved\MechCrewQA\host\Saved\SaveGames\` |
| client | `D:\Unreal Games\IronBreach\Saved\MechCrewQA\client` | `…\Saved\MechCrewQA\client\Saved\SaveGames\` |

This is a strict improvement on the previous plan, where the host used live saves: **now neither
process can read or write `D:\Unreal Games\IronBreach\Saved\SaveGames\`.** The live
`IBCharacters.sav`, `IronBreach_Vault.sav`, `IronBreach_XP.sav` and `IronBreach_Ledger.sav` are
untouched by the run.

### Host seeding — copy only, done by you, before launch

`IB.DeploymentCheck` phase 0 clicks `Btn_Deploy` on the operative select screen, so the host
sandbox needs a roster. One file, copied — never moved, and nothing is ever written back:

```
mkdir "D:\Unreal Games\IronBreach\Saved\MechCrewQA\host\Saved\SaveGames"
mkdir "D:\Unreal Games\IronBreach\Saved\MechCrewQA\client\Saved\SaveGames"
copy "D:\Unreal Games\IronBreach\Saved\SaveGames\IBCharacters.sav" "D:\Unreal Games\IronBreach\Saved\MechCrewQA\host\Saved\SaveGames\IBCharacters.sav"
```

Only the roster is seeded. The vault and XP saves are deliberately **not** copied: the sandboxed
host will seed its own empty vault from the starter loadout, which is enough for a crew check and
keeps even a read of live progression out of the run. The client sandbox stays empty — it joins with
`open` and never has an operative.

Delete `Saved\MechCrewQA\host` and `…\client` to reset between runs; deleting them touches nothing
live. I have made no copies, created no directories and run nothing.

---

## 4. Network description corrected (correction 3)

My previous document said `IpNetDriver`. That was wrong, and the deployment logs are the evidence:
with `-NoSteam` the online subsystem is NULL and the session is a LAN match, but the **GameNetDriver
is still `SteamNetDriver`** (`DefaultEngine.ini` lines 145-147 put it first with `IpNetDriver` only
as a *fallback*), running in **IP passthrough** because of the LAN/NULL listen URL — exactly as the
comment at lines 138-143 of that file describes. `IBDeploymentCheck`'s own PASS line prints the
class name, which is where the logs show it. No configuration was changed.

Because the bound address is a property of that driver and the listen URL rather than something I
should assume, the host check now logs it before doing anything:

```
[CrewQAHost] NET driver=SteamNetDriver listen=<address> url=<full listen URL>
```

**Use the address from that line for the client** if it differs from `127.0.0.1:7777`. That removes
the one guess in the previous procedure.

---

## 5. Reporting corrected (correction 4)

**Counts were wrong and are now fixed: 6 host, 13 client** on the straight-success path — your
numbers, confirmed by enumerating the call sites (the host's seventh is the no-mech failure branch,
which is off the success path). The previous document said 7/11.

**A short run can no longer read as a pass.** Each command keeps a tally of passed, failed, skipped
and timed-out, and the completion line is:

```
[CrewQAHost]   COMPLETE: PASS 6/6 (0 failed, 0 skipped, 0 timed out)
[CrewQAClient] COMPLETE: PASS 13/13 (0 failed, 0 skipped, 0 timed out)
```

The word is `PASS` only when nothing failed, nothing was skipped, nothing timed out **and the
expected number of assertions actually ran**. Anything else prints `INCOMPLETE n/13`, so a run that
stopped at phase 2 with zero failures is unmistakable.

**A name collision now stops the run.** Two humans with identical names can never evidence an
exchange, so instead of logging a SKIP and continuing into a timeout that looks like a sheet fault,
phase 0 records the SKIP with both names and finishes — `INCOMPLETE 2/13 (0 failed, 1 skipped, …)`.

**The empty-frame gap is a NOTE, not a SKIP.** It is a property of a one-mech map, not an assertion
that nearly ran, so it no longer inflates the skip count — and it is named as uncovered in §7 below.

---

## 6. Slow client readiness (correction 5)

Stated plainly: **there is no acknowledgement channel from the client to the host.** The host's
holds are open-loop, and the code now says so at each one. Building a replicated test channel would
be the framework this task is meant to avoid, so instead:

- **Readiness gate.** The host no longer boards as soon as two player states exist. It waits until
  both humans **possess a pawn** — the strongest signal actually visible on the server, and the one
  that covers the long, variable part of client start-up (travel, level load, spawn). Only then does
  it board.
- **Longer holds.** The first crewed state is held **20 s** before the swap (was 12), and 15 s each
  before the gunner leaves, before the hull empties, and at the end. The client's own phase 0→2 path
  is three ticker seconds after it possesses a pawn, so it has ample margin inside that window.
- **Unambiguous failure instead of a silent wrong answer.** The residual risk — a client alive and
  pawned but slow to open the Mech page, latching the *post*-swap pair as its "before" reading — now
  produces a phase-3 TIMEOUT that says so explicitly, prints both the latched and current names, and
  tells you to re-run before treating it as a sheet fault. It cannot pass, and it cannot look like a
  product defect.

The real boarding, swap and disembark paths are unchanged, and expected occupant values are still
derived from the station pawns' replicated PlayerStates — the file contains no call to
`UIBMechScreen::StationOccupant` at all.

---

## 7. Exact procedure

One host, one client. Seed the sandboxes first (§3).

### Process 1 — host, fully automatic

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -game -windowed -ResX=1280 -ResY=720 -WinX=40 -WinY=40 -NoSplash -NoSteam -NoSound -port=7777 -UserDir="D:\Unreal Games\IronBreach\Saved\MechCrewQA\host" -IBCrewQAAfterDeploy -ExecCmds=DisableAllScreenMessages,IB.DeploymentCheck -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceArtPass\crewqa-host-20260922.log"
```

No console input. `IB.DeploymentCheck` settles the host in Carrow Gate, then the flag starts
`IB.CrewQAHost`, which waits for the client.

### Process 2 — client, launched after `[DeploymentCheck] COMPLETE` appears in the host log

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -game -windowed -ResX=1280 -ResY=720 -WinX=700 -WinY=40 -NoSplash -NoSteam -NoSound -UserDir="D:\Unreal Games\IronBreach\Saved\MechCrewQA\client" -ExecCmds=DisableAllScreenMessages,"IB.CrewQAClient 127.0.0.1:7777?Name=GUNNER" -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceArtPass\crewqa-client-20260922.log"
```

`?Name=GUNNER` is required, not cosmetic: without it both processes take the same default name and
the client stops at phase 0 with the collision SKIP. Substitute the address from the host's
`[CrewQAHost] NET` line if it is not `127.0.0.1:7777`.

### Expected

```
[CrewQAHost]   COMPLETE: PASS 6/6 (0 failed, 0 skipped, 0 timed out)
[CrewQAClient] COMPLETE: PASS 13/13 (0 failed, 0 skipped, 0 timed out)
```

Screenshots:

```
D:\Unreal Games\IronBreach\Saved\MechCrewQA\shots\client-crewed.png
D:\Unreal Games\IronBreach\Saved\MechCrewQA\shots\client-swapped.png
D:\Unreal Games\IronBreach\Saved\MechCrewQA\shots\client-backfill.png
D:\Unreal Games\IronBreach\Saved\MechCrewQA\shots\client-departed.png
```

Greps: `[CrewQAHost]`, `[CrewQAClient]`, `COMPLETE:`, `FAIL`, `TIMEOUT`, `SKIP`, `NOTE`, `NET`.

Timing after both processes are pawned: roughly 80 s of driving. Host hard stop 480 s (it includes
waiting for you to launch the client); client hard stop 420 s, with 90 s per observation phase.
Neither process exits itself — close the client first, then the host. Process control is yours.

---

## 8. Honest limits

- **Not compiled, not run.** The build log predates every change here.
- **Is there an `AIBMech_Base` in CarrowGateGarrison?** Still unknown to me. If not, the host fails
  in ~20 s with `no AIBMech_Base in <map>` and reports `INCOMPLETE 0/6 (1 failed, …)`. This remains
  the most likely reason for a no-op first attempt.
- **Connection.** The client's `ClientTravel` to a numeric address over `SteamNetDriver` in IP
  passthrough should work, but I have not seen it do so. A failure leaves the client in phase 0 and
  ends at 420 s with `INCOMPLETE 0/13 (… 1 timed out)` and only the `connecting to …` step logged —
  a connection problem, distinguishable from a sheet problem.
- **No client acknowledgement.** §6 in full: the holds are open-loop, mitigated by the pawn
  readiness gate and longer windows, with an explicit diagnostic if arrival order still bites.
- **The client has no operative identity**, so its name comes from `GetPlayerName()` (hence
  `?Name=`), and `GetDisplayCallsign`'s callsign branch is exercised only for the host's occupant.
- **A wholly empty frame is not covered** in a one-mech map — the AI keeps the seat after the last
  human leaves. Logged as a NOTE with the actor count; it is a known gap, not a passing case.
- **Roles are asserted blank on the client**, which is the design. `DRIVER`/`GUNNER` text is not
  verified anywhere by this run.
- Compile hotspots, unchanged from before plus one: `APlayerState::IsABot()`,
  `UWidgetTree::ForWidgetAndChildren`, `FAutoConsoleCommandWithWorldAndArgs`, calling the
  `Server, Reliable, WithValidation` `Server_RequestBoard` from server code, and now
  `UNetDriver::LowLevelGetNetworkNumber()` with the added `Engine/NetDriver.h` include.

Out of scope and untouched: character preview fidelity, the garrison layout (still awaiting the
generated overhead concept — nothing implemented from the text notes), and XP.

Stopping here for your build and runtime review.
