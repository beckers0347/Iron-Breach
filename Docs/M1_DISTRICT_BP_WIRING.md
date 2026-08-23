# M1 District -- Blueprint/Sequencer Wiring Plan

Companion to `build_m1_district.py` (grey-boxes the space) and
`M1_LANDFALL_Mission_Design.md` (the design source of truth). This doc covers
the gameplay this mission needs that a level-blockout Python script correctly
can't build: PALAWAN's non-combat scripted presence, the deterrent battery,
the carry, the extraction counter, and checkpoints.

**Everything below is Blueprint / Data Asset / Level Sequencer work, on
purpose -- zero new files under `Source/`.** Per `Docs/IRONBREACH-collab-
conventions.md` §3, `Source/` is Connor's; this content is exactly what §5
calls Shane's layer ("content wiring... UI, level scripting, data asset
values, one-off encounter logic that never runs on the server's authority
path"). M1 is also explicitly infantry-only, no-CONCORD, no-mech content per
the mission doc's own §12 -- there is no authority-branching reason to need a
new C++ system here. If that changes (the §11 co-op staging decision leans
toward parallel carries, or extraction needs to be strictly server-
authoritative for competitive integrity), that's a C++ hook request for
Connor, not a Blueprint workaround -- flag it, don't route around it.

---

## 1. BP_Palawan_Scripted -- the non-combat kaiju actor

**Do not reuse `AIBCharacter_Kaiju`/`BP_Kaiju_Palawan`.** That class is the
fightable boss framework (armor -> organ phase -> exposed -> dead,
`KAIJU_FIGHT_WIRING.md`). M1's PALAWAN is LOCKED as "not a boss, not an AI...
no combat AI, no damage model, no health, no targeting" (mission doc §5). The
level script places `BP_Kaiju_Palawan` at the eruption point ONLY as a
scale/silhouette placeholder and logs a loud warning about it -- swap it for
this instead before the level ships.

**Build:**
1. New Blueprint Class, parent `Actor` (not `Character` -- it never needs
   movement input, capsule collision, or a controller). Name it
   `BP_Palawan_Scripted`, folder `Content/M1_District/BP/`.
2. Add a **Spline Component** as the root's child. Populate its points from
   `PALAWAN_ROUTE` in `build_m1_district.py`'s comments / the "PALAWAN Route"
   marker actors the level script placed (tagged `PALAWAN_RoutePoint`, folder
   `4.3a Burst - Eruption Crater/PALAWAN Route`) -- either hand-place spline
   points at those marker locations, or in the Construction Script call `Get
   All Actors With Tag` and build the spline from their transforms so it
   stays in sync if the markers move.
3. Add the creature mesh (Skeletal Mesh Component) once it exists -- until
   then, keep a simple placeholder mesh so the actor is visible for timing
   work. **Do not give it a `HealthComponent` or any `IDamageableInterface`
   implementation** -- that would silently let players "kill" it, which
   breaks the mission's whole thesis.
4. Sequencer: a `LevelSequence` (`LS_M1_Eruption`, `LS_M1_PalawanDrift`,
   `LS_M1_Calcify`) drives position along the spline over the mission's real
   time (roughly the Burst + Aftermath runtime, ~23 min per the doc's beat
   timings) via a **Spline Component track / Transform track keyed to spline
   distance**, not physics or AI movement -- matches §5's "spline-driven
   locomotion, sequencer-owned animation."
5. One `BlueprintCallable` function, `TriggerFlinch()`: plays a flinch
   montage/animation on the current limb and does nothing else. This is the
   ONLY interactive affordance the design allows (§5). Called by the
   deterrent battery below, never by player damage.
6. Collision: `WorldDynamic`, blocks nothing the player needs to path around
   except where the mission scripts a scripted collapse -- keep `Pawn`
   channel overlap-only so it is never mistaken for a shootable/targetable
   actor by `UHitscanWeaponComponent`'s line traces.

**Test:** PIE through the Burst beat with `LS_M1_PalawanDrift` playing --
confirm the creature never blocks the player's route, is visible only in
partial/low frame per §9's scale-language rule (shot from below / partial
frame, never a clean full-body hero shot), and that firing a weapon at it
produces zero response from `HandleTakeDamage` (it shouldn't implement the
interface at all, so this should just not do anything).

---

## 2. Deterrent battery -- the honest-ceiling beat

The level script already placed two `DeterrentBattery_HitVolume` trigger
boxes (Bellringer emplacements) and the siege gun prop at the gun line
(`4.3c Burst - Gun Line`).

**Build:**
1. New Blueprint Class, parent `Actor`, `BP_DeterrentBattery`. Placed at each
   `Bellringer_Emplacement_*` location (or made the parent of that mesh --
   either works; parenting keeps the visual and the logic in one actor).
2. On player interact (reuse whatever interact-prompt pattern the garrison's
   `BP_DoorFrame` uses, per `IRONBREACH-collab-conventions.md`'s naming
   conventions -- an `IA_Interact` input action if one exists, or a simple
   overlap+keypress) while standing in the crew position: fire a cosmetic
   sonic-charge effect, then call `BP_Palawan_Scripted::TriggerFlinch()` on
   the currently-tracked PALAWAN instance (cache a reference via `Get Actor
   Of Class` at `BeginPlay`, or expose a `PalawanRef` variable set from the
   level).
3. Rate-limit: a short cooldown (2-3s) per emplacement so the "ringing"
   reads as a deliberate beat, not a rapid-fire button-mash.
4. The siege gun prop needs NO logic -- it's set dressing that "accomplishes
   nothing but noise and spall" per §4.3. A looping fire VFX/SFX on a timer
   is enough; do not wire it to deal any damage or produce any gameplay
   effect, that's the point.

**Test:** stand at each Bellringer position, interact during
`LS_M1_PalawanDrift`'s "crosses behind the gun line" segment, confirm
`TriggerFlinch()` fires a visible reaction and the cooldown prevents spam.

---

## 3. The carry -- Ms. Idris, 400m, no HUD

**Build:**
1. New Blueprint **Actor Component** (parent `ActorComponent`),
   `BP_CarryComponent`, added to `BP_IBCharacter_Infantry` (the content-side
   child of `AIBCharacter_Infantry` Shane already owns per the handoff docs).
   Pure BP component -- no `Source/` change needed since `AIBCharacter_
   Infantry` already exposes what this needs (movement speed via `Character
   Movement Component`, `bIsArmed`/weapon holster state, the existing
   `WeaponRig`).
2. `BeginCarry(AActor* Carriable)`:
   - Cache and zero `MaxWalkSpeed` override (or set a `bForceWalkOnly` flag
     the movement blend space reads) -- "walking pace is forced" (§4.4).
   - Set `bIsArmed = false` / holster (reuses the existing armed-state
     branch already in `AIBCharacter_Infantry`'s weapon mesh visibility).
   - Pull the camera in slightly (a small FOV/offset lerp on
     `FirstPersonCamera`, reversible in `EndCarry`).
   - Hide/clear the HUD widget stack entirely (§7: "the game removes UI at
     its most important moments" -- this is the precedent-setting instance).
   - Attach a simple carried-NPC mesh/socket for Ms. Idris (or hide her
     separate pawn and drive a carried-pose anim state -- whichever the
     Idris performance ends up needing; this is a placeholder-scope call).
3. VO waypoint triggers: place a series of trigger volumes along the
   `CARRY_WAYPOINTS` polyline the level script already laid out (it logs
   each waypoint's exact coordinates to the Output Log when run) and bind
   each to a VO line cue (`Bakery_Awning_Down_Marker`, `SistersFlat_Marker`
   tags already exist as level markers to hang these off of).
4. `Idris_Stops_Marker` (already placed, tag `Beat_IdrisStops`): on overlap,
   stop her VO permanently for this playthrough, no sting, no slow-mo (§4.4,
   §10 sensitivity rules) -- just silence from here to the muster.
5. **No stamina bar, no timer, no fail state, no score, ever, anywhere in
   this component.** This is not a systems opportunity, it's a rite (§4.4)
   -- resist the urge to add a "carry meter."
6. Abandoning the carry (walking away / going idle) soft-resets to
   `CARRY_START` per §7 -- simplest implementation is a distance-from-path
   check on tick that teleports back to the last waypoint trigger if the
   player somehow strands themselves, logged not punished.

**Test:** full walkthrough from `Idris_Found_Marker` to
`ExtractionMuster_Hospital`, confirming: HUD stays cleared the entire time,
walk speed never exceeds the forced pace, all three landmark VO cues fire in
order, `Beat_IdrisStops` silences her exactly once, and the final ~100m
(from `Beat_IdrisStops` to the muster) reads as navigable by level geometry
alone -- literally play it with the HUD off and see if you get lost. If you
do, the geometry needs another pass before the VO cut is trustworthy.

---

## 4. Extraction counter -- "extraction counts on-screen, kills don't"

The level script tagged every muster point `ExtractionMuster` (3 buses in
Dread, the gun-line convoy chokepoint, the hospital plaza) -- 6 volumes total.

**Build:**
1. A single manager, either the Level Blueprint itself or a dedicated
   `BP_ExtractionCounterManager` actor placed once in the level (cleaner,
   survives a level-BP reorganization later).
2. `On Actor Begin Overlap` on each `ExtractionMuster`-tagged trigger (loop
   `Get All Actors With Tag` at `BeginPlay` and bind dynamically rather than
   hand-wiring six event nodes) -- filter to civilian/evacuee pawns only
   (once crowd agents exist; until then, any non-player actor overlap is
   fine for testing).
3. Increment an integer, broadcast a **Blueprint Event Dispatcher**
   `OnExtractionCounted(int32 NewTotal)`. This is the BP-native equivalent
   of "signals-only... no direct references" (mission doc §12) -- the HUD
   widget binds to the dispatcher instead of polling or holding a direct
   reference to the manager.
4. `WBP_ExtractionHUD` (new UMG widget, or a new element on the existing
   objective widget `IBObjectiveWidget`/`WBP_*` per naming conventions):
   text reads `CIVILIANS EXTRACTED: {NewTotal}`, counts up only, never
   decrements, no kill counter anywhere (LOCKED, §7).
5. Objective text stays radio-procedural per §7 ("Run the routes," not
   "Escort the civilians (0/12)") -- if `IBMissionDirector`'s
   `GetObjectiveText()` pattern is worth reusing for M1's beat banners
   later, that's a real conversation to have with Connor (the existing
   director is built around a kill-based Patrol->Emergence->Engaged->Secured
   spine that doesn't fit M1's no-kill structure as-is) -- out of scope for
   this pass; M1's beat banners can ship as Level-Blueprint-triggered UMG
   text for now.

**Test:** walk each of the 6 `ExtractionMuster` volumes in sequence, confirm
the HUD number only ever goes up, confirm no kill count appears anywhere in
any HUD state during this mission.

---

## 5. Checkpoints -- four beat boundaries + mid-burst

The level script placed 7 `Checkpoint`-tagged trigger volumes:
`Checkpoint_Dread`, `Checkpoint_Burst_RoadLifts`, `Checkpoint_Burst_Eruption`,
`Checkpoint_Burst_MidPoint`, `Checkpoint_Burst_GunLine`,
`Checkpoint_Burst_CollapseSprint_End`, `Checkpoint_Aftermath_HospitalMuster`,
`Checkpoint_MissionEnd` -- more than the doc's minimum ask ("beat boundaries
+ one mid-burst," §7) since the Burst beat is long and has several natural
seams; cut the ones that feel redundant once it's walkable.

**Build:**
1. Level Blueprint (or the same manager actor as §4): on overlap with any
   `Checkpoint`-tagged trigger, cache that trigger's transform as
   `LastCheckpointTransform` (a simple `FTransform` variable, Game Instance
   or a level-scoped save -- doesn't need to survive a full session restart
   for M1, just a within-attempt respawn).
2. On player death (`AIBCharacter_Infantry::BP_OnDied`, already an exposed
   `BlueprintImplementableEvent` -- bind to it, don't touch the C++), respawn
   at `LastCheckpointTransform` instead of the pawn's existing
   `RespawnTimerHandle`/`RespawnDelay` full-level-restart behavior.
3. `Checkpoint_MissionEnd` doubles as the trigger for the title card (§4.4
   "Mission end" beat) -- fade to black, show the IRON BREACH card over the
   kneeling silhouette shot, cut on the first bell-toll per the mission doc.

**Test:** die deliberately in each beat, confirm respawn lands at the most
recent checkpoint, not mission start, and that the carry (§3) is NOT
checkpoint-interruptible mid-beat per §7 ("the carry cannot fail and cannot
be skipped") -- if the player dies mid-carry, that needs its own soft-reset
behavior (back to `CARRY_START`/`Idris_Found_Marker`, not a hard fail), not
generic death handling.

---

## 6. What's still not covered here

Crowd agents (evacuee nav-to-muster flocks), the collapse's actual Chaos
destruction events, PALAWAN's animation set, and Idris's VO/performance are
all real production work this doc doesn't attempt to script around -- they're
listed in that order of cost in the mission doc's own §12. This wiring plan
gets the level from "walkable grey box" to "every system has a hook and a
place to plug in," which is the honest ceiling of what's buildable without
an artist, an animator, and a voice actor in the loop.
