# Crew QA build fix and startup NET evidence (September 22, 2026)

Implements `Docs/CLAUDE_MENU_CREW_QA_BUILD_FIX_2026-09-22.md` — the two corrections and nothing
else. No build, no process control, no save copies or writes, no sandbox directories created, no
git or lock operation, no gameplay/menu/network config, no assets, no garrison, no XP work.

**Not compiled and not run.** `build-crewqa-followup-20260922.log` is the *failing* build this
fixes. No compile or runtime success is claimed for the new version.

---

## 1. Changed file

| File | Change |
|---|---|
| `Source/IronBreach/UI/IBMechCrewQACheck.cpp` | Non-const net-driver pointer with named FString locals; the NET diagnostic moved ahead of the readiness gates and emitted once. |

`IBDeploymentCheck.cpp` is unchanged — it compiled. Nothing else was opened for writing.

---

## 2. The compile error

```
IBMechCrewQACheck.cpp(249,23): error C2662: 'FString UNetDriver::LowLevelGetNetworkNumber(void)':
                               cannot convert 'this' pointer from 'const UNetDriver' to 'UNetDriver &'
IBMechCrewQACheck.cpp(249,14): error C2100: you cannot dereference an operand of type 'FString'
IBMechCrewQACheck.cpp(247,57): error C7595: ... TCheckedFormatStringPrivate ... not a constant expression
```

I declared `const UNetDriver* Driver`. `UNetDriver::LowLevelGetNetworkNumber()` is non-const
(`NetDriver.h:1637`), so C2662 is the root; C2100 and the checked-format-string C7595 are both
consequences of the first error poisoning the expression's type.

Fixed by taking the pointer non-const, as `World->GetNetDriver()` already returns it — no
`const_cast`, no engine edit:

```cpp
if (UNetDriver* Driver = World->GetNetDriver())
{
    const FString DriverName = Driver->GetClass()->GetName();
    const FString Listen     = Driver->LowLevelGetNetworkNumber();
    const FString Url        = World->URL.ToString();
    Say(TEXT("CrewQAHost"), TEXT("NET"), FString::Printf(
        TEXT("driver=%s listen=%s url=%s netmode=%d — connect the client to 127.0.0.1:<port from listen/url>"),
        *DriverName, *Listen, *Url, int32(World->GetNetMode())));
}
```

Each of the three `FString`s is now bound to a **named local** before `*` is applied, so no
`const TCHAR*` points into a temporary inside the format call. The previous version dereferenced
three returned-by-value `FString`s inline, which is what the checked-format-string machinery
objected to; binding them is both the correct lifetime pattern and what silences C7595.

---

## 3. NET evidence now precedes the wait

You were right that it was circular: the launch procedure tells you to read the address from the
NET line, but the line sat below `TwoHumans` and the `WithPawn` gate — both of which require the
client that the address is needed to start.

It now runs at the top of the host ticker, before every gate, guarded by a `bNetLogged` capture so
it emits **once** and cannot spam per tick. It fires on the first tick where `World->GetNetDriver()`
exists, which on the settled host is immediately after `IB.DeploymentCheck` COMPLETE.

**Preserved unchanged:** the `TwoHumans` + both-players-possess-a-pawn readiness gate still guards
boarding, the open-loop holds (20/15/15/15 s) are as before, the tallies are still 6 host and 13
client with `PASS` only on a full run, and both `-UserDir` sandboxes and the copy-only seeding
procedure are untouched. The real boarding/swap/disembark paths and the display-helper-independent
expectations are also untouched — the file still contains no `UIBMechScreen::StationOccupant` call
and no `ClearTimer`.

---

## 4. Reading the address — and the wildcard caveat

Expected shape, early in the host log:

```
[CrewQAHost] NET driver=SteamNetDriver listen=<bound address> url=<listen URL> netmode=2 — connect the client to 127.0.0.1:<port from listen/url>
```

**`listen=` is a bind address, not necessarily a connect target.** A listen server commonly binds
the wildcard, so this may read `0.0.0.0:7777`, which you cannot connect to. Take only the **port**
from it and connect the client to `127.0.0.1:<that port>`. The same port should also appear in
`url=`, and `-port=7777` in the host launch line pins it, so the expected value is `7777` and the
documented client address `127.0.0.1:7777` stands unless the log disagrees.

If the NET line is missing or its address is unusable, the confirmed bind evidence is the engine's
own startup entry in the same log — the `LogNet` line recording the game net driver listening on a
port — and `netmode=2` on the NET line independently confirms the process is a listen server.
Should `-port=7777` fail to take effect for this driver, that port line is the authority; use its
port rather than assuming 7777.

The launch commands and sandbox procedure are otherwise exactly as in
`CLAUDE_MENU_CREW_QA_FOLLOWUP_RESULT_2026-09-22.md` §3 and §7 — nothing there needs changing.

---

## 5. Honest limits

- **Not built, not run.** One compile error was reported and fixed; I cannot rule out a second that
  the failed build never reached, since compilation stopped at this translation unit.
- The `LowLevelGetNetworkNumber()` output format is not something I have observed for
  `SteamNetDriver` in IP-passthrough mode. §4 is written so the procedure works whether it returns a
  wildcard bind, a concrete address, or something unexpected.
- Everything still unverified from the previous document remains so: whether CarrowGateGarrison
  contains an `AIBMech_Base`, whether the client's `ClientTravel` reaches the host over this driver,
  and the open-loop timing caveat with its explicit phase-3 diagnostic.
- Remaining compile hotspots, unchanged: `APlayerState::IsABot()`,
  `UWidgetTree::ForWidgetAndChildren`, `FAutoConsoleCommandWithWorldAndArgs`, and calling the
  `Server, Reliable, WithValidation` `Server_RequestBoard` from server code.

Stopping here for your build and the isolated two-player run.
