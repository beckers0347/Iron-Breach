# Handoff to Astra — Caryatid wiring, one crash fix, and repo state

From: the Cowork Claude session, 2026-09-19 → 09-20.
Read this before touching `Mech/`, `Combat/`, `Progression/`, `Infantry/IBCharacter_Infantry`, or `UI/IBGlassBorder`.

---

## 1. Repo state right now — read this first

| | |
|---|---|
| Checked out | `main` |
| Local `main` | **3 ahead, 8 behind** `origin/main` |
| Branch `claude/caryatid-wiring` | `ef91958` — **pushed to origin**, same 3 commits |
| `origin/main` | `fed25b7` — 8 commits of Shane's content (meshes, buildings, textures, interiors) |
| Uncommitted | 61 modified tracked + 22 untracked, all yours, untouched |

The three commits sit on **local `main` as well as the branch** — I committed while on `main`, then pointed the branch at the same tip. They are **not** on `origin/main`.

**Do not `git pull` / `git rebase origin/main` without checking first.** 10 uncommitted `Content/` files are also modified in Shane's 8 upstream commits — including `Content/LevelPrototyping/CarrowGateGarrison.umap`. Pulling now forces binary conflicts on a level asset. That is the entire reason this work went to a branch instead of `main`. Settle the content situation first; merge the branch after.

### Git lock files — this will bite you

The mounted folder denies deletes, so any git command that fails leaves its `.lock` behind and cannot clean up. Stale locks have already (a) hung a UBT build for 11 minutes, because UnrealBuildTool runs `git status` for its adaptive non-unity set, and (b) blocked a GitHub Desktop branch switch with "A lock file already exists in the repository".

Before every git call: `find .git -maxdepth 3 -name "*.lock" ! -path "*_stale_locks*" | while read L; do mv "$L" ".git/_stale_locks/$(basename $L).$RANDOM"; done`

There are ~18 parked files in `.git/_stale_locks/` and `.git/*.lock.stale*`. Harmless, `git fsck` is clean, but they need deleting by hand from Windows.

---

## 2. The finding: the Caryatid was never reachable

Not broken — unwired. In a shipping build you could not board a mech, drive it, aim it, fire it, or raise its sync meter. Only the `E` exit key worked. The seat/boarding/swap/CONCORD machinery was all built and correct; every *entry point* deferred to `AIBMechPlayerController`, which **no GameMode instantiates** (`BP_IronBreachGameMode` sets `BP_IBPlayerController_C`, `BP_FirstPersonGameMode` sets `BP_FirstPersonPlayerController_C`). Its existence made the wiring look done.

Specifically, before these commits:
- `AIBMech_Base::ServerBoard` had **zero callers**, and the `Server_RequestBoard` its own off-authority warning names **did not exist**.
- `AIBMech_Base::SetupPlayerInputComponent` bound nothing but `E`; its comment claimed MechPC would call `RouteMoveInput()`.
- `AIBGunnerSeat`'s Enhanced Input actions were all optional and unassigned, deferring to that same dead controller.
- `UConcordComponent::RegisterCoordinatedAction` — "the ONLY way sync goes up" per its own header — had **no caller**. The meter could only fall.
- `UIBXPSubsystem::SetTuning` had **no caller**, so `Tuning` was permanently null: zero XP rate, `ReportKaijuArmorDamage` early-returned, `OnXPLevelUp` never fired. Every operative pinned at level 1 while two correct call sites fed it damage.

---

## 3. What changed — `a155b4c` (11 files, +373/−20)

C++ only, no Blueprint or content dependency.

- **Boarding.** `AIBMech_Base` now implements `IIBInteractable`. `Interact_Implementation` runs on the boarder's client and relays via a new `AIBCharacter_Infantry::Server_RequestBoard(AIBMech_Base*, bool)` — server-validated, range-checked against a new `BoardMaxDistance` (1200cm). It requests `bWantLeftSeat=true`; `ServerBoard`'s existing correction logic then gives boarder 1 the hull, boarder 2 the seat, and refuses a third. **Do not flip that to `false`** — asking for the seat strands a solo pilot in the gun of a mech with no driver, because `BackfillSeatWithAI` only ever fills the seat.
- **Hull input.** `RawMoveForward/RawMoveRight/RawTurn/RawLookUp` + `ApplyNavigatorMove`, via `BindAxisKey` on W/D/MouseX/MouseY. **One binding per axis** — an axis-key binding fires every frame regardless of key state and each handler reads *both* its keys; binding S and A too runs each handler twice per frame. `Server_ReportDriving` is throttled client-side to 0.2s.
- **Gunner input.** LMB fire, RMB ADS press/release, MouseX/Y look. `RawTurn`/`RawLookUp` accumulate into `PendingLook` and call `ProcessLook` **once** per frame — its closing `SetLookDelta` otherwise overwrites the yaw and sway goes vertical-only. Pitch is negated on both paths to match the infantry IMC's Negate-Y.
- **CONCORD v1.** New file-scope `FIBOnWeaponServerHit` on `UHitscanWeaponComponent`, broadcast server-side from both damage paths in `PerformFire`. `AIBGunnerSeat` binds it under `HasAuthority()` and calls `RegisterCoordinatedAction()` when `AIBMech_Base::IsNavigatorDriving()` is true. **This rule is a deliberate conservative v1 and is Connor's to tune** — a landed shot while the partner drives. Widening it to dodges/abilities is the obvious next step.
- **CONCORD crash guard.** `RegisterCoordinatedAction` and `RegisterLoss` dereferenced `Tuning` unguarded; `Tuning` is `EditAnywhere`-only and nothing in C++ assigns it. The new call site was its first ever caller, so an unset `DA_ConcordTuning` would have crashed the **server** on the first landed mech shot. Both now early-return on null.
- **XP.** `UIBXPSubsystem::Initialize` loads `DA_XPTuning` by path (the `IBWatch::Registry` idiom). Added `+DirectoriesToAlwaysCook=(Path="/Game/Characters/Infantry")` to `DefaultGame.ini` — the asset is outside `/Game/IronBreach` and nothing hard-references it, so it would not cook and the fix would die silently in a packaged build.
- **Crew logout.** `OnGameModeLogout` keys parked-pawn cleanup off `LeftSeatController`/`RightSeatController` (station), not `CurrentDriver`/`CurrentGunner` (role). `ServerBoard` stores Left⇔hull⇔`ParkedDriverPawn`; `PerformRoleSwap` moves roles *without* moving parked pawns, so the old code destroyed the **remaining** pilot's pawn and stranded them.

---

## 4. Your files that I touched — please read

**`UI/IBGlassBorder.cpp` — I fixed a crash in it.** `PLAY_IronBreach` died on any keypress at the title screen:

```
Assertion failed: Addr < GetData() || Addr >= (GetData() + ArrayMax)
Attempting to use a container element which already comes from the
container being modified (ArrayMax: 8, ArrayNum: 6)
```

Line 95 closed the bevel outline with `Bevel.Add(Bevel[0])` — a reference **into the array being appended to**. `Add` reallocates past capacity and invalidates it mid-call; `TArray` asserts on that by design. Six points in an eight-slot array is exactly where the next `Add` reallocates. Now copies to a local first, with an empty-array guard. The neighbouring `Outline.Add(Shape[0])` is fine — different container. I swept `Add`/`Emplace`/`Push` across all of `Source/`; that was the only occurrence. **Please don't reintroduce the pattern**, and note that `Shape[0]` there is still unguarded if `BuildShape` can ever return empty.

`IBGlassBorder.{h,cpp}` were untracked, so commit `ef91958` necessarily lands the **whole widget**, not a one-line diff.

**Three files carry your in-flight edits into my commits.** There was no way to isolate them:

- `Infantry/IBCharacter_Infantry.cpp`
- `Progression/IBXPSubsystem.cpp` + `.h`
- `Config/DefaultGame.ini`

That entanglement already caused one defect: `a155b4c` took `IBXPSubsystem.cpp` for the XP fix, which carried your `GetLevelBounds` **definition** with it while the **declaration** stayed in the uncommitted header. The working tree built because the header was on disk; a clean checkout of that commit would not have. Fixed in `e6fab80`. **If you commit more of these files, check declaration/definition pairs land together.**

---

## 5. Verified

- Build: `Result: Succeeded`, `ZZCHAR_BUILD_EXIT=0`, DLL relinked, **zero errors and zero warnings** in any touched file.
- UHT accepted the file-scope dynamic delegate, the `IIBInteractable` interface on `AIBMech_Base`, and the `Server_ReportDriving` RPC.
- Merge-tested against all 8 upstream commits: **zero text conflicts**.
- A dedicated UE 5.8 review before commit caught and fixed: two protected-access compile errors (`Server_RequestBoard`, `IsNavigatorDriving`), the first-boarder seat bug, occupancy read via `GetController()` (`bOnlyRelevantToOwner` → null for other players' pawns on a client; now `GetPlayerState()`, which AI controllers don't create), inverted pitch, the doubled axis binding, the doubled `ProcessLook`, and the `Tuning` null-deref.

**Not verified: none of it has been run.** No PIE session, no two-player test.

---

## 6. Open — needs editor/Blueprint work, i.e. you or Shane

1. **`BP_Mech` → `MechMesh` must block `ECC_Visibility`.** `Interact()` traces on that channel, and a skeletal mesh with no physics asset generates no query collision. If it doesn't block, pressing `E` on the mech does nothing regardless of the C++.
2. **Assign `DA_ConcordTuning`** on the mech's Concord component. Unset means the meter can't move (it no longer crashes, but it won't work).
3. **Reparent `BP_FirstPersonPlayerController` to `IBPlayerController`** (outstanding since 09-10, `MENUS_UI_WIRING.md` §3). Without it the crew-disconnect guard in `PawnLeavingGame` never runs, and a navigator dropping mid-fight lets the engine destroy the hull.
4. **Infantry `DefaultMappingContext` is never removed.** Added in `BeginPlay`, no `RemoveMappingContext` anywhere in the module. Enhanced Input key consumption may swallow WASD before the hull's `BindAxisKey` bindings see it. If the mech won't move in PIE, this is the first suspect — fix is `RemoveMappingContext` in `UnPossessed`, not more binding code.

## 7. First real test

PIE, Net Mode *Play As Listen Server*, 2 players. Walk up to the mech, press `E` — one takes the helm, the other the gunner seat. Drive it. Fire while the partner is moving, and CONCORD should rise for the first time since the system was written.

---

## 8. Also on the branch, unrelated

`Scripts/ib_free_dll.py` — taskkills `CrashReportClient*` / `UnrealEditor.exe`. A crashed `-game` run keeps `UnrealEditor-IronBreach.dll` mapped and the next link fails `LNK1104`. Run it via the watcher (`py ib_free_dll.py`) when that happens.
