# MP hardening — pass 2 (2026-09-15)

*by Claude (Fable 5) · board: un-02, part of un-01 · companion: `MP_TEST_DAY_CHECKLIST.md`*

Written **without a build available** (the cloud session cannot compile UE). Every change is
small and local; the friction list in §4 is where the compiler is most likely to complain.
Nothing under `Source/IronBreach/UI/` was touched — that folder is Astra's while the menu
redesign runs.

## 1. What the read-through found

Before writing anything I read the whole join/leave path: `IBSessionSubsystem`, `IBPlayerController`
(`PawnLeavingGame`), `IBPlayerState` (`EndPlay` vault save), `IBMech_Base` (`ServerHandleCrewLogout`,
`OnGameModeLogout`), `IBGunnerSeat`, `IBWatchBoard`, `IBMissionDirector` / `IBMissionSubsystem`,
`IBCharacter_Kaiju` + organs, and the objective widget. The honest summary: **late-join and
disconnect are far more built than the board said.**

Already correct, no change:

- **Late joiner and the mission**: `AIBMissionDirector` is `bAlwaysRelevant`, `MissionPhase`
  replicates with an OnRep, and the objective widget finds the director lazily on a 0.5 s retry
  and reads the current phase — a client who joins mid-fight gets ENGAGED, not SWEEP THE ZONE.
- **Late joiner and the kaiju**: `Species` (initial-only), `CurrentArmor` and `FightPhase`
  replicate; organs replicate `bDestroyed`. A half-broken kaiju arrives half-broken; `ApplySpecies`
  refuses to reset armor on clients.
- **Client drop**: `PawnLeavingGame` hands crew stations back to the mech before the engine
  destroys the pawn; `OnGameModeLogout` is the fallback for a plain PlayerController;
  `AIBPlayerState::EndPlay` saves the vault on the host.
- **Two-human mech**: the gunner seat is fully networked (owner-auth aim, `Server_Fire`,
  `Server_RequestSwap`, `Server_RequestExit`).

Actually missing (fixed below):

1. **No link-failure handling on the client.** Host quits / times out → the engine drops the
   client onto `GameDefaultMap` with no message, and the client's local Steam session entry stays
   registered (Steam overlay keeps showing "in a lobby"). A host whose listen socket failed to open
   was never told either.
2. **A departed proposer's Watch proposal stayed on the board** (PROPOSED by someone who left).
3. **`UIBMissionSubsystem::GetDirector()` returned null on clients** for the auto-spawned director
   (clients never went through the subsystem's spawn path). Anything reading the director via the
   subsystem on a client — the Missions sheet's live objective, BP — saw nothing.
4. **`LiveKaiju` was a counter that only decremented on death.** A kaiju removed from the world
   without dying (spawner reset, dev command, level script) left the count stuck above zero and
   ZONE SECURED could never fire again in that world. The emergence timer was also not cleared on
   EndPlay.

Not fixed, documented (needs a build + PIE to do safely): a **client alone in the hull cannot take
the guns** — seat/role state is server-only and the hull's F is a no-op on clients. The obvious fix
(AI takes the hull, human takes the seat) puts the co-pilot controller into the hull, which is the
exact circular-ownership shape that froze the mech in July (`4b6355b` / `48cfd88`). Leave it for a
session with the editor open. Two humans, and host + AI, both work today.

## 2. Changes by file

| File | Change |
|---|---|
| `Online/IBSessionSubsystem.h/.cpp` | Subscribes to `GEngine->OnNetworkFailure()` / `OnTravelFailure()` and `PostLoadMapWithWorld`. Client side: maps the failure to a plain-language message (`SQUAD LINK LOST - THE HOST WENT DARK`, `THE HOST CLOSED THE LINK`, `COULD NOT REACH THE HOST`, `BUILD MISMATCH - RUN UPDATE_IronBreach.bat AND RETRY`, `DEPLOYMENT FAILED (...)`), destroys the stale local session entry, and announces through the existing `OnSessionStatusChanged` (`Failed`) 1.5 s after the title map loads (4 s fallback if no map load follows). Dev builds also print the line on screen so it is never silent. Host side: only `NetDriverListenFailure` / `NetDriverCreateFailure` / `NetDriverAlreadyExists` are surfaced (`LISTEN SOCKET FAILED - SQUAD CANNOT JOIN`); a client dropping is routine and stays a log line. New `ConsumeLastLinkFailure(FText&)` (BlueprintCallable, one-shot) so the operative sheet / main menu can print the reason on construct — **UI hook for Astra/Shane, not wired here.** Filters by GameInstance so PIE's multiple instances do not cross-talk. |
| `Online/IBWatchBoard.h/.cpp` | `ServerPlayerLeft(const APlayerState*)`: an unarmed proposal by the leaver is cleared (`ClearAll` → replicates). Armed drops are the host's and proceed. |
| `Items/IBPlayerState.cpp` | `EndPlay`, authority, **only for `EEndPlayReason::Destroyed`** (a real logout/kick — never map travel): calls `AIBWatchBoard::Get(World)->ServerPlayerLeft(this)`. |
| `Missions/IBMissionSubsystem.h/.cpp` | `GetDirector()` resolves lazily: if the cache is empty it iterates the world for the replicated director and caches it (same trick as `AIBWatchBoard::Get`). `Director` is now `mutable`. |
| `Missions/IBMissionDirectorCheck.cpp` (new) | Opt-in dev command `IB.MissionDirectorCheck` (excluded from Shipping/Test) — see §3. |
| `Missions/IBMissionDirector.h/.cpp` | `LiveKaiju` is a `TSet<TWeakObjectPtr<AIBCharacter_Kaiju>>`, not an `int32`. `TrackKaiju` dedupes, ignores corpses, binds `OnDestroyed` as well as `OnPhaseChanged`. Death and destruction both release the beast exactly once (`ReleaseKaiju`), then `EvaluateSecured()` (which also sheds GC'd entries) decides ZONE SECURED. `EndPlay` clears the emergence timer. New `GetLiveKaijuCount()` (BlueprintPure). Phase logic, text and replication are unchanged. |

No `UPROPERTY` names changed anywhere; no Blueprint bindings are affected. No content, no
config, no UI files.

Tooling added next to the .uproject (2026-09-16): `MPTEST_HostLocal.bat` / `MPTEST_JoinLocal.bat`
(rung 2 in two double-clicks), `MPTEST_CollectLogs.bat host|client` (evidence folder + summary),
`MAKE_SyncPack.bat` (rebuilds Shane's pack from a committed, built tree). The UI hook for the
link-failure line is a paste-ready brief for Astra: `Docs/ASTRA_BRIEF_link_failure_banner.md`.

## 3. How to verify

- **Link failure (client)**: rung 2 of the checklist — host Alt+F4 with a client in the world. The
  client lands on the title map and ~2 s later shows the red `SQUAD LINK LOST` line; its log has
  `Session: network failure ConnectionLost on the client` followed by `dropping the stale local
  session entry`. Then DEPLOY from that client must host cleanly (no "session already exists").
- **Build mismatch**: run a client built from a different commit against the host — the client
  should print `BUILD MISMATCH - RUN UPDATE_IronBreach.bat AND RETRY` instead of silently
  returning to the title.
- **Listen failure (host)**: hard to force; if the Steam socket ever fails to bind you will now see
  `LISTEN SOCKET FAILED - SQUAD CANNOT JOIN` on the host instead of finding out from Shane.
- **Board cleanup**: client proposes on the Watch, does not confirm, Alt+F4 → host's card clears,
  host log `[Watch] <callsign> left the net with '<id>' proposed and unarmed — standing the board down`.
- **Director on clients**: on a client, `GetDirector()` from BP (or the Missions sheet's live
  objective) is non-null once the director has replicated.
- **Director count**: `IB.MissionDirectorCheck` (console, any authority game world — new file
  `Missions/IBMissionDirectorCheck.cpp`, dev builds only) does it for you: spawns two bare kaiju,
  kills one through the damage interface, destroys the other without killing it, hurries the corpse
  along, and asserts one release each, ZONE SECURED, and that the subsystem finds a director it did
  not spawn. Every line `[MissionDirectorCheck] PASS`, then `COMPLETE — all checks passed`. By hand:
  kill one, `DestroyActor` the other → `removed from the world without dying (0 remain)` then
  `Phase -> Secured`; a normal kill logs exactly one `down` line and nothing when the corpse times out.

## 4. Build friction — where to look first if it does not compile

1. `IBSessionSubsystem.cpp`: `ENetworkFailure::ToString()` / `ETravelFailure::ToString()` return
   `const TCHAR*` — they are passed to `%s` **without** a leading `*`. If 5.8 moved them, both live
   in `Engine/EngineBaseTypes.h`.
2. `GEngine->OnNetworkFailure().AddUObject(this, &UIBSessionSubsystem::HandleNetworkFailure)` —
   handler signature must be exactly `(UWorld*, UNetDriver*, ENetworkFailure::Type, const FString&)`;
   travel: `(UWorld*, ETravelFailure::Type, const FString&)`. Removed with `RemoveAll(this)`.
3. `UGameInstance::GetTimerManager()` is used (survives the world that died). If it is not exposed
   in this engine build, swap for `GetWorld()->GetTimerManager()` and accept that the fallback timer
   dies with the world (the PostLoadMap path still announces).
4. `#include "Engine/NetDriver.h"` for `UNetDriver::GetNetMode()`.
5. `IBMissionDirector.cpp`: `TSet<TWeakObjectPtr<...>>` needs `GetTypeHash` for weak pointers —
   provided by `UObject/WeakObjectPtrTemplates.h` via CoreMinimal. `It.RemoveCurrent()` is
   `TSet::TIterator`. Delegate handlers are `UFUNCTION()` (required for `AddDynamic`).
6. Anonymous-namespace names added (`LinkFailureAnnounceDelay`, `LinkFailureFallbackDelay`) are
   unique across the module — the unity build collision that bit the character screens does not apply.
7. Pre-existing warnings (`NetUpdateFrequency` direct write, deprecation noise) are untouched.

Rebuild ritual as always: close editor → delete `Binaries/Win64` → relaunch `.uproject` →
accept rebuild (collab conventions §6).

## 5. Building from a cloud session (no shell on the PC)

The build watcher from the operative-flow work still exists: double-click **`zzcharwatch.bat`**
(project root) and leave the window open. It polls `Saved\zz_build_request.txt` — content `build`,
`buildaudit`, or `py <script.py>` — runs UBT (`IronBreachEditor Win64 Development`, ~4 min), and
writes `Saved\char_build_report.txt` ending in `ZZCHAR_BUILD_EXIT=0` when green. A cloud Claude
session can drop the request by writing the file and read the report back, which is the only way it
can compile; a request dropped while the watcher is closed just waits (one is sitting there now
from 2026-09-15, so the first thing the watcher does when started is build this patch).
