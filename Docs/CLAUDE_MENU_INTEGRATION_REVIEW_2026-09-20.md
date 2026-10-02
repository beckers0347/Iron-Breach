# Menu pass 2 — integration review (September 20, 2026)

Read-only review requested by Astra. **Nothing was changed**: no source, no content, no build, no
launch, no git operation, no lock file touched. The only file this session writes is this one.

Scope, as briefed: the pass-2 Mech page live data and crew handling, XP replication and level
bounds, six-seat session/UI agreement, and the Missions active strip. Reviewed against the files as
they stand on disk today, after the Caryatid commits — not against the 09-19 copies.

Build state: `Saved/ReferenceArtPass/build-review-20260920.log` — `Result: Succeeded`, 447.71 s,
4 actions, DLL relinked, no errors and no warnings from any menu-pass file. **Nothing below has been
run.** Every finding is read from code; the two marked *untested runtime* are things code cannot
settle.

Severity is my read of blast radius, not a schedule: nothing here blocks a build.

---

## 1. Mech page — live data and crew

### M1 · Crew readout is empty on every client (high, code-confirmed)

The seat and role pointers are not replicated. `Mech/IBMech_Base.h:96,99,104,107` declare
`LeftSeatController`, `RightSeatController`, `CurrentDriver`, `CurrentGunner` as plain
`UPROPERTY(BlueprintReadOnly)`, and `GetLifetimeReplicatedProps` (`Mech/IBMech_Base.cpp:92-100`)
lists only `GunnerSeat`, `CurrentHealth`, `CurrentAmmo`, `WeaponCooldownRemaining`, `PartnerName`.
All four are therefore null on a client, and the Mech sheet reads all four:

- `UI/IBMechScreen.cpp:284-287` — both crew rows print `EMPTY` with no role, even with two people
  aboard.
- `UI/IBMechScreen.cpp:192` — `FindFrame()`'s "the frame you are crewing wins" rule
  (`IsControllerSeated(Local)`) can never be true on a client, so it silently degrades to "the first
  `AIBMech_Base` the iterator finds", which may be someone else's frame.
- `UI/IBMechScreen.cpp:224-226` — the status line reads `FRAME ON STATION` for a client who is in
  fact crewing.

Trigger: PIE, *Play As Listen Server*, 2 players. Board with the client, open MECH on the client.
On the listen host and in standalone every line above is correct, so a single-player pass will not
show this.

Minimal fix — two routes, and the second stays out of Caryatid state:

1. Replicate them: add `Replicated` to the four `UPROPERTY`s and four `DOREPLIFETIME` lines. Cheapest,
   and it fixes every future consumer, but it is your file and your call.
2. UI-only: derive occupancy from PlayerStates, which replicate to everyone — hull =
   `Frame->GetPlayerState()`, gunner = `Frame->GunnerSeat ? Frame->GunnerSeat->GetPlayerState() :
   nullptr` (`GunnerSeat` is replicated, `IBMech_Base.h:176-177`), and "am I crewing" = either equals
   `GetOwningPlayerState()`. This is the same idiom your §5 adopted after `GetController()` proved
   null for other players' pawns on a client. Role (DRIVER/GUNNER) still cannot be shown on a client
   this way, which is why M4 below suggests labelling the rows by station instead.

### M2 · "HEAVY WEAPONS CLEAR" is printed when Concord is absent or untuned (medium, code-confirmed)

`UI/IBMechScreen.cpp:256-258` prints one of exactly two states from
`AIBMech_Base::AreWeaponsSafetyLocked()`, which is `Concord && Concord->AreHeavyWeaponsLocked()`
(`Mech/IBMech_Base.cpp:751-754`), and that resolves to `bDesynced && Tuning &&
Tuning->bDesyncLocksHeavyWeapons` (`Mech/ConcordComponent.cpp:299-302`).

So a frame with no Concord component, or with `DA_ConcordTuning` unassigned — which your §6.2 lists
as still open — reads as `LINKED / HEAVY WEAPONS CLEAR`. The sheet is asserting a healthy link it
has not verified, which is the one thing this page was built not to do.

No crash risk: the unguarded `Tuning` dereference you fixed was in `RegisterCoordinatedAction` /
`RegisterLoss`; both accessors the sheet reaches are already null-guarded.

Trigger: open MECH with a frame whose Concord tuning is unset — the current content state.

Minimal fix: branch on `Frame->Concord == nullptr` first in that block and print
`NO CONCORD LINK FITTED` in `IBStyle::TextLo()`. Covering the untuned case honestly needs a one-line
`bool IsTuned() const { return Tuning != nullptr; }` on `UConcordComponent` — a Caryatid-file change,
so yours to take or leave.

### M3 · The arm weapon goes stale on clients the moment anything equips one (low, latent)

`UI/IBMechScreen.cpp:261` reads `Frame->CurrentVisualData`, declared
`UPROPERTY(EditAnywhere, BlueprintReadWrite)` at `Mech/IBMech_Base.h:223-224` and not replicated;
same for `MaxHealth` (`:277-278`) and `MaxAmmo` (`:283-284`). This is correct **today** only because
`AIBMech_Base::EquipWeapon` (`Mech/IBMech_Base.cpp:975`) has no caller anywhere in the module, so
every machine reads the Blueprint archetype default.

Trigger: none today. The first runtime `EquipWeapon` call makes the client sheet show the old weapon,
its icon and its rarity while the server shows the new one.

Minimal fix: replicate `CurrentVisualData` when a runtime equip path lands (an object pointer to a
data asset replicates fine). Flagged now because the Mech sheet is the first reader that would
expose it.

### M4 · LEFT SEAT / RIGHT SEAT no longer matches what the boarding code calls the stations (low, naming)

`UI/IBMechScreen.cpp:133-134` labels the rows LEFT SEAT / RIGHT SEAT, but the Caryatid model maps
Left ⇔ hull ⇔ driver and Right ⇔ gunner seat (your §3; `RecomputeRoles`,
`Mech/IBMech_Base.cpp:296-330`, "Left drives, Right shoots").

Minimal fix: relabel to `HULL` / `GUNNER SEAT`. The role column then stops repeating the caption, and
the page survives M1's route 2, which can name stations on a client but not roles.

---

## 2. XP replication and level bounds

### X1 · The header XP bar never moves while the menu is open (medium, code-confirmed)

`Items/IBPlayerState.h:115` declares `OnOperativeXPChanged` and `Items/IBPlayerState.cpp:169-172`
broadcasts it from `OnRep_OperativeXP`, but **nothing subscribes**: a module-wide search finds no
`AddDynamic` / `AddUniqueDynamic` for it (only `OnOperativeIdentityChanged` is bound, by
`UI/IBInventoryScreen.cpp:460`).

The header reads the XP numbers inside `RefreshTabBanner()` (`UI/IBMenuScreen.cpp:121-142`), whose
only callers are `NotifyScreenOpened` (`:202`), the Inventory tab switch
(`UI/IBInventoryScreen.cpp:282,734`) and the Watch (`UI/IBWatchScreen.cpp:171,690`). So the bar is a
snapshot taken when the page opened, and on MECH / MISSIONS / SKILLS / LEDGER it never updates at
all while open.

That is exactly the check the result doc asks for — `Docs/CLAUDE_MENU_REDESIGN_RESULT.md`, Pass 2
verification step 2, "award XP on the host and watch the bar move without a menu reopen" — and the
code as written cannot satisfy it. The delegate was added for this and then not wired.

Trigger: open any hangar page, award XP on the host (a kill on a listen server does it), watch the
bar. It stays put until you cycle pages.

Minimal fix, entirely inside `UI/IBMenuScreen`: make `RefreshTabBanner()` a `UFUNCTION()`, then in
`NotifyScreenOpened`, after the existing call,

```cpp
if (AIBPlayerState* PS = GetOwningPlayerState<AIBPlayerState>())
{
    PS->OnOperativeXPChanged.AddUniqueDynamic(this, &UIBMenuScreen::RefreshTabBanner);
}
```

with the matching `RemoveDynamic` in `NotifyScreenClosed`. The unbind is required, not optional:
screens are removed from the viewport on close (`UI/IBMenuSubsystem.cpp:91-92,118-119`), not hidden.

### X2 · Verified correct — no defect found

Stating these so they don't get re-reviewed:

- `GetLevelBounds` (`Progression/IBXPSubsystem.cpp:238-272`) is convention-agnostic by construction:
  it binary-searches the ledger's own `UXPTuningData::LevelForXP`, so it is right whether
  `PilotLevelThresholds` is cumulative or per-level steps. The ceiling at `:250-252` is
  `TotalXP + sum(thresholds)`, which is ≥ the true top of the ladder under either convention, and it
  is clamped to `MAX_int32 - 1`. Both searches are monotonic-predicate searches over a monotonic
  `LevelForXP`.
- No tuning, or empty thresholds, returns (0, 0) → `HasNextLevel()` (`Items/IBPlayerState.h:84`) is
  false → the header prints the raw total rather than inventing a fraction
  (`UI/IBMenuScreen.cpp:131-140`). Honest under the failure case your XP fix was written for.
- The mirror is keyed correctly. `HandleXPAwarded` (`Items/IBPlayerState.cpp:208-214`) filters on
  `Track == Pilot && RecordKey == MakeProgressionKey()`, so one player's kill never moves another's
  bar, and `MakePlayerKey` folds in the operative GUID (`Progression/IBXPSubsystem.cpp:66-74`), so
  three billets are three separate bars.
- Ordering is safe: `GrantXP` broadcasts `OnXPAwarded` before `OnXPLevelUp`
  (`Progression/IBXPSubsystem.cpp:159-167`), so `SetOperativeXP` recomputes the bounds against the
  new total before `SetOperativeLevel` mirrors the new level — the two can't disagree on a level-up
  frame.
- Bind and unbind are authority-guarded and symmetric (`Items/IBPlayerState.cpp:30-40` and `:61-71`),
  and `CopyProperties` (`:297-300`) carries the total, both bounds and the level through seamless
  travel.

---

## 3. Six-seat session / UI agreement

### S1 · `FireteamSize()` reads the CDO, `CreateSession` reads the live instance (medium, code-confirmed)

`Online/IBSessionSubsystem.h:124` — `static int32 FireteamSize() { return FMath::Max(1,
GetDefault<UIBSessionSubsystem>()->MaxPlayers); }` — the **class default object**.
`Online/IBSessionSubsystem.cpp:349` — `Settings.NumPublicConnections = FMath::Max(MaxPlayers, 2);` —
**this instance**.

`MaxPlayers` is `EditDefaultsOnly, BlueprintReadWrite` (`:120-121`), so the two can drift: any
Blueprint write at runtime, or a Blueprint subclass of the subsystem carrying a different default,
moves the advertised session size while the UI keeps building six seats
(`UI/IBFriendsScreen.cpp:33,70`; `UI/IBLobbyStripWidget.cpp:23,79`). The UI pools are also built once
in `NativeOnInitialized`, so a later change never reaches them at all.

Today, with nothing writing it, both paths give 6 — this is about keeping them from separating.

Minimal fix, pick one: have `CreateSession` call `FireteamSize()` at `:349` so both sides read the
same object, or make `MaxPlayers` `BlueprintReadOnly` so the CDO is the only source.

### S2 · Two shipped destinations still advertise a 4-operator fireteam (medium, data vs. code — design call)

`Online/IBWatchTypes.h:103`'s new `SquadMax = 6` default is inert for every shipped destination,
because `Online/IBWatchTypes.cpp:47-71` passes explicit values per row: the Watch and Gate Garrison
carry `1, 8` and the text "1–8 OPERATORS"; the Exclusion Zone (`:60-61`) and Firing Line (`:65-66`)
carry `1, 4` and "1–4 OPERATORS"; the Drowned Quarter `2, 4`, locked and untexted.

Both surfaces prefer the authored text when present (`UI/IBWatchScreen.cpp:1114`,
`UI/IBMechScreen.cpp:239-241`), so a six-player fireteam standing in the Exclusion Zone reads
"FIRETEAM 1–4 OPERATORS" on the Mech sheet and the same on its Watch card.

Nothing gates on it: `SquadMin` / `SquadMax` are assigned only in `IBWatchTypes.cpp` and displayed
only in those two places, module-wide. So this is copy, not a deploy blocker.

Minimal fix if you want them consistent: one string and one number per row at `:60-61` and `:65-66`.
I left them alone deliberately — a patrol grid and a training lane sized for four read as authored
design, and that is Connor's call and yours, not a code fix.

### S3 · The six-card row is wider than the four it replaced (low, **untested runtime**)

`UI/IBFriendsScreen.cpp:69-89` builds `Seats` cards with 8 px side padding, centered, with no scroll
box and no shrink; `UI/IBLobbyStripWidget.cpp:78-88` does the same at 7 px. Two more
`UIBPlayerBannerWidget` cards is roughly a card-width plus 30 px more than this layout has ever been
seen at. Code cannot settle whether it fits.

Worth a look on the Squad page and in the lobby at 1920×1080 and at 1280×720. If it clips, the
minimal fix is a `UScaleBox` (`ScaleDownToFit`) around `BannerRow` rather than shrinking the cards.

The V itself is correct: `SeatDrop` (`UI/IBFriendsScreen.cpp:36-40`) gives `Center = 2.5` for six, so
seats 2 and 3 take a 45 px top padding under `VAlign_Top` (lowest on screen) and seats 0 and 5 take
none — a dip toward the middle, which is the shape Connor asked for.

One look question while you are there: `LocalSlotIndex` is a fixed `1` (`UI/IBFriendsScreen.h:69`),
so with six seats the local player's hero card sits second from the left rather than near the middle.

---

## 4. Missions active strip

### Q1 · The strip does not exclude the Bastion, so the lobby can advertise itself as an active operation (medium, code-confirmed)

`UI/IBMissionsScreen.cpp:272-274` — `bLive = Director != nullptr && Here != nullptr`.
`IBWatch::Find` resolves the Watch map to the `watch` destination, whose `Kind` is `Bastion`
(`Online/IBWatchTypes.cpp:47-51`). Everywhere else on this screen the Bastion is excluded explicitly:
auto-selection at `:181`, and the briefing list itself at `:197`.

Two consequences once a director exists in the Watch map: the strip appears reading
"CARROW-1 · THE WATCH", and clicking it calls `SelectDestination(watch)` (`:96-100`), which passes the
`IBWatch::Find` guard at `:242` and is then silently overridden by `RebuildList`'s `:203` fallback to
`Entries[0]` — the click lands on an unrelated briefing.

Trigger today: none. `UIBMissionSubsystem::OnWorldBeginPlay` only spawns a director in a world holding
a kaiju or a spawner (`Missions/IBMissionSubsystem.cpp:30-35`), and the menu map has neither. It goes
live the moment anyone places a kaiju, a spawner, or a hand-placed director in the Bastion —
including for a test.

Minimal fix: `const bool bLive = Director && Here && Here->Kind != EIBDestinationKind::Bastion;` at
`:273`, and the same guard inside the click lambda at `:99`.

### Q2 · The strip takes the first director in the world; the subsystem already has a cached accessor (low, code-confirmed)

`UI/IBMissionsScreen.cpp:266-267` iterates every actor and takes the first `AIBMissionDirector`.
`UIBMissionSubsystem::GetDirector()` (`Missions/IBMissionSubsystem.cpp:45-59`) does that lookup once,
caches it in a `TWeakObjectPtr`, and honours the "a hand-placed director always wins" rule that
`OnWorldBeginPlay:14-19` establishes.

There is one `AIBMissionDirector` class and no subclasses, and a hand-placed director short-circuits
the auto-spawn, so "first" and "the one" coincide today — correct by luck rather than by rule.

Minimal fix: ask the subsystem instead of iterating. It also drops a full-world actor scan that
currently runs twice a second while the page is open (`:291-295`). That scan is not a background
cost — closed screens are removed from the viewport (`UI/IBMenuSubsystem.cpp:91-92,118-119`), so they
do not tick.

### Q3 · Verified correct — no defect found

`ActiveObjective` is only re-set when the text actually changes (`:278`); the detail pane's
LIVE FIELD OBJECTIVE / MISSION BRIEFING source label is correctly gated on the selected destination
matching the current map (`:286-287`); the click's `FilterIndex = 0` does reach the filter tabs,
because `SelectDestination` rebuilds the list (`:240-243` → `:189-193`); and `GetObjectiveText` reads
the replicated `MissionPhase` (`Missions/IBMissionDirector.h:64`), so the strip is live on clients as
well as the host.

---

## 5. Smaller notes

- `UI/IBMechScreen.cpp:262,267` — `Arm->Icon.LoadSynchronous()` and `SetBrushFromTexture` run on
  every 0.5 s refresh. Cheap once resident, but caching the last `UTexture2D*` and only re-setting
  the brush on change avoids a synchronous load on the game thread the first time and a brush
  invalidation twice a second after.
- `Items/IBPlayerState.h:192-199` — `OperativeXP` carries `ReplicatedUsing = OnRep_OperativeXP` while
  `OperativeLevelFloorXP` / `OperativeNextLevelXP` are plain `Replicated`, so a bounds-only change
  would not notify. There is no gameplay trigger (the bounds are a pure function of the total), so
  this is a consistency nit only — but if X1's binding lands, putting the RepNotify on all three
  costs nothing.
- `UI/IBMechScreen.cpp:177-182` and `UI/IBMissionsScreen.cpp:291-295` do tick work without the
  `IsVisible()` guard that `UI/IBFriendsScreen.cpp:210` and `UI/IBMenuScreen.cpp:180` use. Harmless
  while closed screens are removed from the viewport rather than hidden — noted so nobody changes
  the close path to hide without revisiting these two.

---

## 6. Caryatid work — preserved, and re-checked

All three of your later fixes are intact on disk and were left untouched:

- `UI/IBGlassBorder.cpp:95-103` — the bevel loop still closes through a copy, with the empty-array
  guard. The self-append pattern does not appear anywhere else in the file.
- `Progression/IBXPSubsystem.cpp:26-37` — `DA_XPTuning` still loads by path with the
  `MISSING - XP will not accrue` log.
- `Config/DefaultGame.ini:34-36` — `+DirectoriesToAlwaysCook=(Path="/Game/Characters/Infantry")`
  still present, with its comment.

Every other menu-pass file is byte-identical to what was written on 09-19; those three are the only
ones that moved, and this review reads the current versions.

On your open question at `UI/IBGlassBorder.cpp:88` (`Outline.Add(Shape[0])` unguarded if `BuildShape`
can return empty): it cannot be empty there. `BuildShape` (`:9-21`) always appends at least four
points for any W/H — each corner contributes one point or two — and `OnPaint` returns early when
`W < 2 || H < 2` (`:41-44`). No change needed, and it is a different container from the one being
appended to, so the assert you hit cannot fire on that line either.

---

## 7. Suggested order, if any of this gets picked up

1. **X1** — the XP bar not moving is the one thing a demo viewer would notice, and the fix is
   confined to `UI/IBMenuScreen`.
2. **M1** — decide route 1 (replicate the seats) or route 2 (read PlayerStates). Route 1 is yours;
   route 2 I can do inside `IBMechScreen` alone.
3. **Q1** and **M2** — two small guards, both preventing the menus from stating something that
   isn't true.
4. **S1** — one line, prevents a future divergence.
5. **S2** — a design answer from Connor, then a two-token edit if the answer is "make them six".
6. **M3**, **M4**, **Q2**, §5 — whenever convenient.

I have made no source changes and am not starting garrison work. Say the word on which of these you
want implemented and by whom.
