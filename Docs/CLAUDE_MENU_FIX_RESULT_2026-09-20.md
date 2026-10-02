# Focused menu integration fixes — result (September 20, 2026)

Implements the four corrections in `Docs/CLAUDE_MENU_FIX_BRIEF_2026-09-20.md`. Source edits only.
**Nothing was built, launched or killed; no git, lock, commit, push, pull or merge; no garrison
work.** Unrelated files untouched, and the later Caryatid changes are preserved (verified below).

**Nothing here has been run.** Every claim below is static: read from code, not observed in a
session. §5 is the runtime procedure that would actually confirm it.

---

## 1. Changed files

| File | Change |
|---|---|
| `Source/IronBreach/Mech/IBMech_Base.h` | New `EIBMechStationOccupancy` UENUM; two replicated station properties; `RefreshCrewView()` declaration. |
| `Source/IronBreach/Mech/IBMech_Base.cpp` | Two `DOREPLIFETIME` entries; `RefreshCrewView()` and its helper; one call from the existing authority block in `Tick`. |
| `Source/IronBreach/Mech/ConcordComponent.h` | `IsTuned()` — read-only accessor, nothing else. |
| `Source/IronBreach/UI/IBMechScreen.h` | Station-based members and helper signatures; class comment. |
| `Source/IronBreach/UI/IBMechScreen.cpp` | Own-frame selection, crew rows, status line and Concord line rewritten against replicated data. |
| `Source/IronBreach/UI/IBMenuScreen.h` | XP subscription members, `NativeDestruct` override. |
| `Source/IronBreach/UI/IBMenuScreen.cpp` | Bind / rebind / unbind and the refresh handler. |
| `Source/IronBreach/UI/IBMissionsScreen.cpp` | Bastion excluded from the active strip and its click path. |

No Blueprint, content, config or project file was touched. No gameplay behaviour was changed:
boarding, role swap, parked pawns, the safety lock and the Concord tuning all run exactly as before.

---

## 2. X1 — live XP header

`UI/IBMenuScreen.h` / `.cpp`. The header now subscribes to the owning player state's
`OnOperativeXPChanged` and redraws on the broadcast, instead of only at screen-open.

- `BindOperativeXP()` resolves the current `AIBPlayerState`, compares it with the one already bound
  and does nothing when they match; otherwise it unbinds the old and `AddUniqueDynamic`s the new.
  It returns true only when the binding actually moved.
- `UnbindOperativeXP()` unbinds from `BoundOperativeState` — the object that was bound — not from
  whatever is current at the time. That is the difference that makes **player-state replacement**
  safe: on travel or a reconnect the two are different objects, and unbinding "the current one"
  would leave the old state holding the binding forever.
- `BoundOperativeState` is a `TWeakObjectPtr`, so a state destroyed under an open screen leaves
  nothing to chase.
- Bound in `NotifyScreenOpened`, dropped in `NotifyScreenClosed` **and** in a new `NativeDestruct`
  override: closing removes the screen from the viewport, but a world teardown destructs it without
  a close, and both paths have to let go. Every existing `UIBMenuScreen` subclass that overrides
  `NativeDestruct` (Inventory, Skills, Watch, WeaponRack, CharacterSelect, CharacterCreate) already
  calls `Super::`, so the chain reaches it.
- **Repeated opens** cannot accumulate bindings: `AddUniqueDynamic` plus the identity check plus the
  close/destruct unbind. Even a duplicate would be idempotent, but it cannot occur.
- `NativeTick` calls `BindOperativeXP()` once a frame — a pointer compare on all but the frame where
  the state changes — and refreshes once when it moves.
- `HandleOperativeXPChanged()` refreshes only `if (IsInViewport())`, so an award landing between a
  broadcast and an unbind cannot rebuild a screen that is no longer shown.

Replicated XP and `GetLevelBounds` are untouched: this only subscribes to an event that was already
being broadcast and had no listener.

Deliberately **not** changed: `OnOperativeIdentityChanged` is still not subscribed. A level-up
already broadcasts both (`SetOperativeXP` then `SetOperativeLevel`), so the XP binding alone
refreshes the whole header line including `LV n`. A callsign arriving with no XP change still waits
for the next open — pre-existing, out of this brief's scope.

---

## 3. M1 / M4 — Mech crew, stations and own-frame selection

### Why replicating the controller pointers would not have worked

`LeftSeatController`, `RightSeatController`, `CurrentDriver` and `CurrentGunner` are `AController*`.
Marking them `Replicated` changes nothing useful, because replication of a pointer only carries a
*reference*, and the reference resolves only if the referenced actor exists on the receiving machine:

- `AController` sets `bOnlyRelevantToOwner`, so a client is sent its **own** controller and no one
  else's. Another player's `APlayerController` is not in that client's world at all.
- `AIBMechAIController` is a server-side object; AI controllers are never replicated to anyone.

So a replicated seat pointer arrives null on every machine except the owning one — exactly the
symptom being fixed — and it would arrive null *silently*. The Caryatid pass already hit this from
the other side (§5 of `CLAUDE_CARYATID_HANDOFF_2026-09-20.md`: `GetController()` null for other
players' pawns on a client, replaced with `GetPlayerState()`).

What does reach every machine is **pawn state**: `APawn::PlayerState` replicates unconditionally, and
the hull is a pawn while the gunner seat is a pawn held by the already-replicated `GunnerSeat`
pointer. That covers identity. It does not cover the one thing a PlayerState cannot express — an AI
co-pilot, which has no PlayerState and is therefore indistinguishable from an empty station. So the
smallest missing piece, and the only thing added, is **occupancy as data**.

### What was added

`EIBMechStationOccupancy { Vacant, Operative, Copilot }` and two replicated properties,
`HullOccupancy` and `SeatOccupancy`. They are written in one place, `RefreshCrewView()`, from the
possessing controller of each station pawn:

```
HullOccupancy = Occupancy(this);           // the hull pawn
SeatOccupancy = Occupancy(GunnerSeat);     // the gunner-seat pawn
```

`RefreshCrewView()` is called from the **existing** `HasAuthority()` block in `AIBMech_Base::Tick`,
not from the seating functions. That was deliberate: it touches no boarding path, so `ServerBoard`,
`ServerDisembark`, `AssignToLeftSeat` / `AssignToRightSeat`, `VacateSeat`, `RecomputeRoles`,
`PerformRoleSwap`, `ServerRequestCrewSwap`, `BackfillSeatWithAI` and the logout cleanup are all
byte-for-byte unchanged, and every one of them is still picked up because possession is what is
read. Nothing in the game reads these two properties to make a decision — they are a view.

Stations are keyed off **possession**, which is the physical truth: `ServerBoard` seats a pilot and
then possesses them into the hull (left station) or the gunner-seat pawn (right station).

### What the sheet now does

- **Captions are stations**: `HULL` and `GUNNER SEAT`, replacing `LEFT SEAT` / `RIGHT SEAT`. A
  station never moves; the Caryatid model maps left ⇔ hull ⇔ driver and right ⇔ gunner seat.
- **Occupant name** comes from `StationOccupant()`: the replicated occupancy says *whether* someone
  is there, the station pawn's PlayerState says *who*. `EMPTY`, `AI CO-PILOT`, the operative's
  callsign, or `OPERATIVE` in the window before their identity has replicated.
- **Role** comes from `StationRole()`, which returns `DRIVER` / `GUNNER` **only where
  `Frame->HasAuthority()`**, because roles are controller-keyed and controllers do not reach other
  machines. On a remote client the role column is empty and the station caption is the whole claim.
  This is the "show roles only when authoritatively known" rule, enforced at the one place that
  prints them.
- **Own-frame selection**: `FindFrame()` now asks `IBMechSheet::IsCrewedBy(Frame, GetOwningPlayerState())`
  — the hull's PlayerState or the gunner seat's PlayerState matching the local one — instead of
  `IsControllerSeated(GetOwningPlayer())`, which could never be true on a client. The
  "first frame on station" fallback is unchanged.
- **Status line** uses the same predicate, so `CREWING / LIVE READOUT` is now correct on a client.

Member renames (`LeftSeatName` → `HullOccupantName` and the three siblings) are private
`UPROPERTY(Transient)` fields on a code-only screen class created two days ago with no `BindWidget`
and no Blueprint child, so no content binding can break. `IsControllerSeated` itself is untouched and
its two gameplay callers still use it.

---

## 4. M2 / Q1 — honest Concord, Bastion exclusion

**Concord** (`UI/IBMechScreen.cpp`). `AreWeaponsSafetyLocked()` is
`Concord && Concord->AreHeavyWeaponsLocked()`, and that is
`bDesynced && Tuning && Tuning->bDesyncLocksHeavyWeapons` — false when the link is healthy *and*
false when there is no link to speak of. The line now distinguishes four states:

| State | Line |
|---|---|
| no component | `NO CONCORD LINK FITTED ON THIS FRAME` (dim) |
| component, no tuning asset | `CONCORD UNCONFIGURED / NO SYNC PROFILE, NO SAFETY LOCK` (dim) |
| desynced and locked | `DESYNC / HEAVY WEAPONS HELD BY THE SAFETY LOCK` (amber) |
| desynced, lock flag off | `DESYNC / HEAVY WEAPONS STILL CLEAR` (amber) |
| synced | `LINKED / HEAVY WEAPONS CLEAR` (cyan) |

`UConcordComponent::IsTuned()` is the only addition: a `BlueprintPure` one-liner returning
`Tuning != nullptr`. It changes no tuning value and no lock behaviour. `Tuning` is an editor-set
component property, so it is present from the archetype on clients as well as the server; `bDesynced`
is already replicated.

**Missions** (`UI/IBMissionsScreen.cpp`). Two guards, matching the eligibility rule the page already
applies in `RebuildList` (`Kind == Bastion` → skip) and `NativeScreenOpened` (auto-select excludes
Bastion):

- strip visibility: `bLive` now also requires `Here->Kind != EIBDestinationKind::Bastion`;
- the strip's click lambda resolves the destination first and only selects a non-Bastion one, so the
  click can no longer set a `SelectedId` that `RebuildList` immediately overrides with `Entries[0]`.

---

## 5. Checks

### Static checks performed

- Every edit applied as an exact single-match replacement (assert on 0 or >1 matches).
- Line endings preserved per file: `Mech/*` LF, `UI/*` CRLF, verified pure before and after.
- Brace and parenthesis balance verified on all eight files.
- Symbol sweep: no surviving reference to `SeatName(`, `SeatRole(`, `LeftSeatName`, `LeftSeatRole`,
  `RightSeatName`, `RightSeatRole`; no dangling `PC` in `Refresh()`; every new symbol
  (`EIBMechStationOccupancy`, `HullOccupancy`, `SeatOccupancy`, `RefreshCrewView`, `IsTuned`,
  `BindOperativeXP`, `UnbindOperativeXP`, `HandleOperativeXPChanged`, `BoundOperativeState`,
  `IsCrewedBy`) is unique and defined before use.
- Includes added where types are newly dereferenced: `Mech/IBGunnerSeat.h` and
  `Mech/ConcordComponent.h` in `IBMechScreen.cpp`. `IBMechScreen.h` forward-declares `APawn` and
  `enum class EIBMechStationOccupancy : uint8` rather than pulling in the mech header.
- Caryatid work re-verified intact after the edits: the copy-then-append bevel close with its
  empty-array guard in `IBGlassBorder.cpp`, the `DA_XPTuning` path load in `IBXPSubsystem.cpp`, and
  `+DirectoriesToAlwaysCook=(Path="/Game/Characters/Infantry")` in `DefaultGame.ini`. None of those
  three files was opened for writing.
- The eight writes were mtime-guarded against the versions read; none was rejected, so nothing else
  had modified them in the meantime.

### Compile risks to watch on the next build

1. `IBMech_Base.h` gains a UENUM, so UHT regenerates that header and everything including it.
2. `IBMechScreen.h` forward-declares the UENUM instead of including `IBMech_Base.h`. If UHT objects
   (it should not — the enum appears only in private, non-reflected method signatures), replace the
   forward declaration with the include.
3. `HandleOperativeXPChanged` must stay a `UFUNCTION()` for `AddUniqueDynamic`.

### Runtime checks still required — none of this was run

**Two-client crew replication (the whole point of M1).** Standalone QA cannot see any of it.

1. PIE, Net Mode *Play As Listen Server*, **2 players**, in a map with a `BP_Mech` — the Gate
   Garrison. `BP_Mech`'s `MechMesh` must block `ECC_Visibility` or `E` will not board at all
   (Caryatid handoff §6.1).
2. Both players board. On the **client** window open MECH (`Q`/`E` to the Mech tab).
   - Expect: `CREWING / LIVE READOUT` in the header — not `FRAME ON STATION`.
   - Expect: `HULL` and `GUNNER SEAT` each showing a real callsign, not `EMPTY`.
   - Expect: the role column **empty on the client**, and `DRIVER` / `GUNNER` on the host. That is
     correct behaviour, not a bug.
3. Client solo-boards a mech with no second human: the other station must read `AI CO-PILOT`, not
   `EMPTY`. This is the case the replicated occupancy exists for.
4. Swap seats mid-fight (`ServerRequestCrewSwap`) and confirm the host's role column follows the
   swap while the station captions and names stay put.
5. Two mechs in the world, each crewed by one player: each machine's sheet must show **its own**
   frame, not the first one spawned.
6. Disembark and log out a crewed client; confirm the station reverts to `EMPTY` within a tick and
   that the remaining pilot's pawn is unaffected (the parked-pawn path is unchanged, but it shares
   the code path being observed).

**XP header.** Open a hangar page, award XP on the host (a kill on the listen server), and watch the
bar move without reopening. Repeat on the client. Open and close the menu ten times and confirm the
header refreshes exactly once per award, not N times — the symptom of a duplicated binding.

**Concord.** With `DA_ConcordTuning` still unassigned the sheet should read
`CONCORD UNCONFIGURED / NO SYNC PROFILE, NO SAFETY LOCK`. After it is assigned (Caryatid handoff
§6.2) it should read `LINKED / HEAVY WEAPONS CLEAR` and flip to the desync lines under desync.

**Missions.** The strip must stay collapsed on the Watch. To exercise the guard, place a kaiju
spawner in the Bastion temporarily — before the fix the strip appeared there and its click selected
an unrelated briefing.

**Regression.** `IB.MenuFlowCheck`, `IB.MenuConsistencyCheck` and `IB.ReferenceMenuCheck` should be
unchanged: no tab label, navigation path, hotkey or clicked string was touched. The Mech page's
station captions are new strings, but no check asserts on them.

### Unverified / not claimed

- Nothing was compiled. The 447.71 s build predates every edit in this document.
- No PIE session, no two-client test, no screenshots.
- `RefreshCrewView()` runs every server tick. Two enum compares plus two `GetController()` calls is
  negligible, but it has not been profiled.
- The `OPERATIVE` placeholder (human aboard, PlayerState not yet replicated) is a race I reasoned
  about and did not observe.

---

## 6. Recorded, not acted on

The QA log reports a pre-existing configuration error, twice:

```
qa-review-20260920.log:1941  LogIronBreach: Error: BP_IBCharacter_Infantry_C_0:
                             CurrentVisualData is NULL! Check Blueprint Class Defaults.
```

Infantry, not mech, and a Blueprint Class Defaults problem rather than a code one. Recorded here per
the brief; not investigated and not expanded into Blueprint configuration.

Deferred as instructed, unchanged from the review: M3 (latent `CurrentVisualData` / `MaxHealth` /
`MaxAmmo` non-replication on the mech, harmless while `EquipWeapon` has no caller), S1
(`FireteamSize()` reads the CDO while `CreateSession` reads the instance), S2 (authored `1–4
OPERATORS` capacity copy on two destinations — a design answer, not a code fix), Q2 (use
`UIBMissionSubsystem::GetDirector()` instead of the per-refresh actor scan), and the icon-reload
micro-optimisation. S3 is closed: six cards fit the inspected 1600×900 screenshot.

Stopping here for Codex review.
