# Crew QA runtime fixture — result (September 22, 2026)

Bounded task from `Docs/CLAUDE_MENU_CREW_QA_FIXTURE_2026-09-22.md`. Development-only. No build, no
process launch or control, no git or lock operation, no save operation, no asset, map, config,
progression, production-crew or garrison change.

---

## Verdict, up front

**Neither arm of the brief is achievable against the project as it stands on disk, and the reason is
the same for both: the mech Blueprint does not exist in this project.** Not unplaced in the wrong
map — absent. `/Game/Characters/Mech/Blueprints/Class/BP_Mech` has no package anywhere under the
project root.

That collapses the brief's conditional from both ends. No existing map can be selected, because a
map can only place a class that exists. No runtime fixture can be written either, because a fixture
spawns that same class; and the brief correctly forbids the only remaining substitute — *"do not
substitute an unconfigured bare native actor or fake occupancy"*. A bare `AIBMech_Base` would board,
swap and disembark happily and would evidence nothing whatsoever about the shipped mech, which is
the entire point of the exercise.

So, per the brief's own instruction — *"Fail clearly if setup cannot produce a usable real mech"* —
**I implemented no fixture.** I added one diagnostic so the next run says out loud which of the two
very different failures it hit. Everything else about the check is untouched.

The good news is narrow but real: every *dependency* the mech needs is present and hydrated. Only
the Blueprint that ties them together is gone. Restoring it is a small, bounded content action, and
§7 below is a ready-to-run procedure for the moment it is back.

---

## 1. What changed

One file. One helper and one log line, both inside the existing "no frame found" failure branch.

| File | Change |
|---|---|
| `Source/IronBreach/UI/IBMechCrewQACheck.cpp` | Added `ConfiguredMechClassPath()` (a path constant, nothing spawns from it) and, in the `Phase == 0 && Count == 0` timeout branch, one `LoadClass<AIBMech_Base>` probe emitting a `NOTE` that distinguishes *"class resolves but is not placed here"* from *"class failed to load"*. The `NOTE` reports the load result and nothing more — a cook, path or dependency fault fails the same way, so it does not infer a missing package. That the package is absent is established separately, on disk, in §2. |

```cpp
/** The mech Blueprint the project's placed actors are instances of, used only to tell a missing
 *  asset apart from an unplaced one when a run finds no frame. Nothing spawns from this. */
static const TCHAR* ConfiguredMechClassPath() { return TEXT("/Game/Characters/Mech/Blueprints/Class/BP_Mech.BP_Mech_C"); }
```

```cpp
Verdict(false, FString::Printf(
    TEXT("no AIBMech_Base in %s — this map cannot exercise the crew sheet"), *World->GetMapName()));
const UClass* Configured = LoadClass<AIBMech_Base>(nullptr, ConfiguredMechClassPath());
Say(TEXT("CrewQAHost"), TEXT("NOTE"), FString::Printf(TEXT("configured mech Blueprint '%s' %s"),
    ConfiguredMechClassPath(),
    Configured
        ? TEXT("resolves — it is simply not placed in this map")
        : TEXT("FAILED TO LOAD: the class did not resolve in this run. Confirm on disk whether the package exists before concluding the asset is missing")));
return Finish();
```

It runs only on the already-failing path, after the `Verdict(false, …)` that was there before, and
still returns `Finish()`. A passing run never reaches it.

**Unchanged and verified by grep after the edit:** zero `SpawnActor` (no fixture), zero writes to
`HullOccupancy`/`SeatOccupancy` (no faked occupancy), zero `UIBMechScreen::StationOccupant` calls
(expectations stay independent of the display helper), zero `ClearTimer` (the UAF class of bug stays
impossible), tallies still `HostExpected = 6` / `ClientExpected = 13` with `PASS` only on a full run,
both `-UserDir` sandboxes and the readiness gate exactly as before.

---

## 2. The evidence

All read-only, from the working tree on disk.

| Check | Result |
|---|---|
| `Content/Sandbox/BP_Mech.uasset` | Exists, **2,239 bytes**, and its package contains `/Script/CoreUObject.ObjectRedirector` — it is a **redirector**, not a Blueprint. Target: `/Script/Engine.BlueprintGeneratedClass'/Game/Characters/Mech/Blueprints/Class/BP_Mech.BP_Mech_C'` |
| That target folder | Contains exactly `BP_MechAIController.uasset` and `BP_MechPlayerController.uasset`. **No `BP_Mech.uasset`.** |
| `find . -name "BP_Mech.uasset"` over the whole project root | Returns **only the redirector** |
| `find . -name "*Mech*.uasset"` | Anim BP, both controllers, `WBP_MechHUD`, the `Starter_Mech` meshes/skeleton, `Mech_Arm_Cannon`, `Mech_HUD` image, the two Sandbox redirectors. **No mech Blueprint.** |
| Binary grep for `IBMech_Base` across `Content/` | One placed instance only: `Content/__ExternalActors__/FirstPerson/Lvl_FirstPerson/2/EA/Y18X3E6GO2K93JSKTIE9JP.uasset` (plus unrelated `WBP_SeatSelect` autosaves) |
| `Plugins/` (`Tripo3DUEBridge`, `meshy`) | No `BP_Mech*` |
| LFS hydration | Real assets in `Content/Characters/Mech/` are full-size on disk (e.g. `DA_ConcordTuning.uasset` 1,301 B, `ABP_Mech` present). This is **not** an unfetched-LFS artifact — the package is genuinely absent. |

### The control case that rules out a false alarm

`Content/Sandbox/BP_IronBreachGameMode.uasset` is *also* a 2,354-byte redirector, from the same
Sandbox relocation — and **its** target resolves: `Content/BP_IronBreachGameMode.uasset`, 22,148
bytes, a real Blueprint naming `BP_IBCharacter_Infantry_C` and `BP_IBPlayerController_C`.

So the Sandbox redirectors are not systematically broken, and my reading of them is not mistaken.
One relocation completed and one did not. `BP_Mech` is specifically missing.

### What the placed actor proves

The Lvl_FirstPerson external actor is a genuine, fully configured `BP_Mech_C` instance
(`BP_Mech_C_UAID_7085C268933097F102_1411656567`) carrying MechMesh, MechWeaponMesh, Concord,
DriverSpringArm, DriverCamera_3PV, GunnerCamera_FPV, ArmCannon, HealthBarWidget and a `Boarding
Zone` with bound begin/end-overlap events, and it names `/Script/IronBreach.IBMech_Base` as the
native base.

That actor is the fingerprint of the asset we are missing. It tells us the real mech existed, was
correctly configured, and was placed — and it will fail to load with its class gone.

---

## 3. Your named candidate, resolved

The brief flagged `Content/Sandbox/BP_Mech.uasset` as a candidate whose *"inheritance/configuration
has NOT been confirmed"*. **Confirmed: it has no inheritance and no configuration.** It is a
2,239-byte `ObjectRedirector` — a forwarding stub, roughly a hundredth the size of a real mech
Blueprint — and it forwards to a package that is not there. Loading `/Game/Sandbox/BP_Mech.BP_Mech_C`
will follow the redirector and fail.

That is worth stating plainly because from a file inventory it looks exactly like a viable
candidate. It is the most misleading artifact in the project right now.

---

## 4. Map selection, resolved

| Map | Mech instances | Verdict |
|---|---|---|
| `LevelPrototyping/CarrowGateGarrison` | none (proved at runtime: `INCOMPLETE 0/6`; the map has no `__ExternalActors__` directory either) | Cannot exercise crew. This is where the `-IBCrewQAAfterDeploy` route lands, which is why the last run failed. |
| `LevelPrototyping/TestLevel1` | **zero** `BP_Mech` references in a 6.2 MB map | Not a mech test map despite the name |
| `FirstPerson/Lvl_FirstPerson` | **one** placed `BP_Mech_C`, fully configured, plus one PlayerStart, and the map overrides DefaultGameMode to `BP_IronBreachGameMode_C` | **The right map — once the Blueprint is restored.** Today its mech actor cannot load. |

`Lvl_FirstPerson` is also the `firing_line` Watch destination, so it is already an exercised map
rather than something invented for this test.

### The route correction this implies

The previous run used `-IBCrewQAAfterDeploy`, which starts the host check after `IB.DeploymentCheck`
COMPLETE — and the deployment leg ends in **CarrowGateGarrison**. That route can never find a mech
without placing one in the garrison, which would be a saved-map change and is out of scope.

The correct route opens `Lvl_FirstPerson` as a listen server directly and starts `IB.CrewQAHost` from
`-ExecCmds`, with no deployment leg at all. It lands in the only map that holds a mech, and it drops
the deployment leg that wrote `IBCharacters` and `Vault` on the last run. No roster seeding is needed
either, because the crew path requires no operative.

**That is not a claim that the route saves nothing.** Removing the deployment leg removes the writes
we observed; it does not establish that the engine and the game write nothing else during start-up,
and no run has been made to check. Both absolute `-UserDir` sandboxes therefore stay exactly as they
are — they are the isolation, not a formality — and the live-save hash comparison before and after is
still worth doing.

---

## 5. Why I wrote no fixture

Spelling out the reasoning, because "I could not do the thing you asked" deserves it.

A fixture would have to spawn *something*. The only three candidates:

1. **`BP_Mech_C` by path** — the brief's intent, and the correct answer. `LoadClass` returns null.
   There is nothing to spawn.
2. **Bare native `AIBMech_Base`** — explicitly forbidden, and rightly. It has no mesh, no physics
   asset, no `DA_ConcordTuning`, no gunner-seat child actor, no boarding volume. Boarding, swap and
   disembark are native and would all "pass", producing a green 6/13 that says nothing about the
   asset Shane actually ships. That is worse than a clear failure: it is a false negative on a bug
   we have not looked for yet.
3. **A native actor dressed up with the mech's meshes at runtime** — a bare actor with extra steps,
   with the added cost of new code that guesses at configuration the Blueprint owns.

Given (1) is empty and (2)/(3) are excluded by the brief, the honest output is the diagnostic in §1
and this report.

---

## 6. What restoring the asset takes — yours, not mine

Editor and content work, outside my authorized scope, so this is a pointer rather than a plan.

The dependency graph is intact: anim BP, skeleton, meshes, arm cannon, both controllers, the HUD
widget and `DA_ConcordTuning` are all present. Only the Blueprint class asset is missing. Three
routes, in the order I would try them:

1. **Git history.** If `Content/Characters/Mech/Blueprints/Class/BP_Mech.uasset` was ever committed,
   restore it from the last commit that had it. Note the Caryatid handoff's warning about stale
   `.git` lock files before any git work. I performed no git operation of any kind, including
   read-only ones.
2. **A collaborator's working tree.** Shane's machine, or an editor autosave under `Saved/Autosaves/`.
3. **Rebuild it in-editor** from `AIBMech_Base` at exactly
   `/Game/Characters/Mech/Blueprints/Class/BP_Mech`, then let the redirector and the placed actor
   re-bind. Two items from the Caryatid handoff §6 apply directly if you take this route: `MechMesh`
   must block `ECC_Visibility`, and `DA_ConcordTuning` must be assigned on the Concord component.

Restoring it at that exact path makes both the redirector and the `Lvl_FirstPerson` placed actor
resolve, with no code change and no change to the check.

---

## 7. Exact procedure, once `BP_Mech` is restored

Both `-UserDir` values absolute and separate, as before. Create a fresh run root; seed the host
roster copy-only if you want to, though this route does not need it.

**Preflight, one command, before spending a two-process run:**

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" /Game/FirstPerson/Lvl_FirstPerson -game -windowed -ResX=640 -ResY=360 -NoSplash -NoSteam -NoSound -UserDir="D:\Unreal Games\IronBreach\Saved\MechCrewQA\preflight" -ExecCmds=DisableAllScreenMessages,IB.CrewQAHost -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceArtPass\crewqa-preflight.log"
```

Single process, no client. **This preflight can only return a negative, so read it that way.** The
`NOTE` is printed from one branch and one only: phase 0, *zero* frames in the world, 20 s elapsed. So:

- A `NOTE` inside ~25 s means the map has no mech. Stop there — the two-process run cannot succeed.
- **No** `NOTE` means a frame was found, and the run then simply waits for a second human that will
  never arrive, all the way to its 480 s hard stop. Nothing is printed in the meantime. Kill it once
  ~30 s have passed with no `NOTE`.

That second outcome is an inference from an absence, not a positive result: it says a frame exists,
not that the mech is correctly configured or that the crew sheet works. Only the two-process run
establishes that. The earlier version of this section called this a ~20 s success check; it is not
one, and it never was.

**Process 1 — listen host:**

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" "/Game/FirstPerson/Lvl_FirstPerson?listen?bIsLanMatch?Name=PILOT" -game -windowed -ResX=1280 -ResY=720 -WinX=40 -WinY=40 -NoSplash -NoSteam -NoSound -port=7777 -UserDir="D:\Unreal Games\IronBreach\Saved\MechCrewQA\host" -ExecCmds=DisableAllScreenMessages,IB.CrewQAHost -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceArtPass\crewqa-host-20260923.log"
```

No `-IBCrewQAAfterDeploy` and no `IB.DeploymentCheck` on this route — the map on the command line is
already the final world, so there is no travel for the check to lose, and the deployment leg would
only move the host to the wrong map.

**`?bIsLanMatch` is not decoration.** Every listen URL in the logs that actually carried a client
has it — `IBHost` builds them that way — and the SteamNetDriver IP-passthrough behaviour we have
observed under `-NoSteam` was observed *with* that flag set. A hand-rolled command-line URL without
it has never been run here, so it is unverified, not known-good. If the client cannot reach the host,
check the host's `NET` line first: `driver=`, `url=` and whether `?bIsLanMatch` survived into the
URL the engine actually browsed.

**Process 2 — client, launched after the host's `[CrewQAHost] NET` line appears:**

```
"A:\Unreal Engine\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe" "D:\Unreal Games\IronBreach\IronBreach.uproject" -game -windowed -ResX=1280 -ResY=720 -WinX=700 -WinY=40 -NoSplash -NoSteam -NoSound -UserDir="D:\Unreal Games\IronBreach\Saved\MechCrewQA\client" -ExecCmds=DisableAllScreenMessages,"IB.CrewQAClient 127.0.0.1:7777?Name=GUNNER" -abslog="D:\Unreal Games\IronBreach\Saved\ReferenceArtPass\crewqa-client-20260923.log"
```

`?Name=` on both processes only has to make the two names **differ** — the client check skips rather
than guesses if both humans render the same name. Take the **port** from the host's `NET` line;
`listen=` is a bind address and commonly reads `0.0.0.0:7777`, which is not a connect target.

---

## 8. Expected evidence

Host, in order: the `NET` line first (it is emitted once, before every gate, so you have the port
before the client exists), then a `STEP` naming both humans, then boarding through
`Server_RequestBoard`, two `ServerRequestCrewSwap` steps, `ServerDisembark`, and
`[CrewQAHost] COMPLETE: PASS 6/6 (0 failed, 0 skipped, 0 timed out)`.

Client: `[CrewQAClient] COMPLETE: PASS 13/13 (…)`, having read `HULL` and `GUNNER SEAT` rows from the
rendered widget — names exchanging across the swap, and the seat reading `AI CO-PILOT` after the
gunner departs.

Anything short of `PASS n/n` on both is a real finding. `INCOMPLETE` with a `NOTE` about the
Blueprint means the asset situation is unresolved, not that the menu is broken.

---

## 9. Limitations — what this report does not establish

- **Nothing was built and nothing was run.** No claim here is runtime-verified.
- The `Lvl_FirstPerson` route is **untested in this project**. Specifically untested: that
  `-ExecCmds` fires `IB.CrewQAHost` reliably on a command-line initial map in a `-game` run. If it
  does not, the failure is unambiguous — the host log will contain no `[CrewQAHost]` lines at all.
- I read the game mode's pawn and controller classes from **package strings**, not from a loaded
  asset. The evidence is strong (`BP_IBCharacter_Infantry_C`, `BP_IBPlayerController_C`) but if the
  spawned pawn is not an `AIBCharacter_Infantry`, the check fails clearly at boarding rather than
  misreporting.
- `Lvl_FirstPerson` has **one** PlayerStart, so both players spawn together. This does not affect the
  test: the harness moves each pawn adjacent to the mech before requesting board, and the real
  `BoardMaxDistance` check in `Server_RequestBoard` still decides.
- Whether `BP_Mech` is recoverable from history is **unknown to me** — I performed no git operation,
  read-only ones included.
- The two-process run remains genuinely two-human. There is still no acknowledgement channel from
  the client, so the host's readiness gate is "both humans possess a pawn", as before.

---

## 10. Restrictions honored

No build, no process launch, control or kill. No git operation and no lock-file change. No save
operation — no copy, write or restore of live saves; and on the route above the run performs no
`IBCharacters` or `Vault` write at all. No asset, map, map-default, network-config, gameplay,
progression or XP change. No garrison layout work. No Caryatid or unrelated edit. No general test
framework. One dev-only source file touched, in one already-failing branch.

Stopping here for your review, build and run.
