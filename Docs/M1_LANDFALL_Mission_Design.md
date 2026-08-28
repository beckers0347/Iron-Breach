# M1 "LANDFALL" — Mission Design & Build Status

**Level:** `CarrowGateGarrison` (reused as-is for the whole mission — no new level geometry)
**Code home:** `Source/IronBreach/Missions/M1Landfall/`
**Last updated:** 2026-08-25

This doc tracks the actual build state of M1 against the narrative bible, so it's clear at a
glance what's playable, what's designed-but-not-built, and what's still open. Update the "Built"
sections as code lands; treat "Planned" as a living design doc until it moves up.

---

## 1. How the mission is structured (engineering pattern)

Every act is one `AActor` "Director" that:

- owns a `TArray<FDialogueLine>` script (`Speaker`, `Text`, `HoldDuration`, `PauseAfter`,
  optional `ScriptedEventTag`) built in `BuildDefaultBeats()`
- plays it back on an `FTimerManager` timer, line by line
- broadcasts `OnScriptedEvent(FName)` at the moment a tagged line fires, so lighting / audio /
  animation / combat spawns can hang off the timeline without touching the Director's code
- implements `IActBeatProviderInterface` (`GetCurrentLine`, `IsActRunning`) so the single generic
  `AMissionSubtitleHUD` can find whichever act is currently live and draw its line as a subtitle —
  no per-act HUD code, no UMG widget required
- exposes a `TSoftObjectPtr<PreviousActDirector>` chaining hook: if set, this act auto-starts the
  instant the previous act's `OnActXComplete` fires; if unset, it runs on its own
  `bAutoStart`/`InitialDelay` timer for isolated testing
- exposes a `CallInEditor` skip function (`SkipToStandTo`, `SkipToEruption`, ...) so playtesting a
  late act doesn't require replaying everything before it

Acts III–V will extend this pattern but are **not** pure dialogue timelines — they're combat
encounters, so they additionally drive `AIBKaijuSpawner` (existing spawn/threat-class system) and
the mech roster (`IBMech_Base` / `IBGunnerSeat`). See §4.

---

## 2. Built

### Act I — "Barracks Intro" ✅ code complete, placed & wired in-editor
`Act1BarracksDirector.h/.cpp`

04:12, Carrowgate watch room. Static theorizes the Green Tomb hum matches the anomaly's
frequency signature — first time he's been right about the Nine, and nobody's listening. Rhodes
enters; Comms reports a climbing micro-seismic cluster (`SeismicContact`); Rhodes calls it a
birthquake precursor and gives the stand-to order (`StandToOrder`). Closes on a narration beat
foreshadowing how wrong "supporting" the evac is about to feel. Fires `OnAct1Complete`.

8 beats, pure dialogue/narration — no combat.

### Act II — "An Eerie Escalation" ✅ code complete, placed & wired in-editor
`Act2EscalationDirector.h/.cpp`

Auto-chains off Act I via `PreviousActDirector`. Civilian district, evac underway
(`BusesLoading`). Environmental dread beats: gulls vanish (`GullsVanish`), a K9 refuses to advance
(`K9Refusal`), glow-veins surface through the asphalt (`GlowVeinsAppear`), a child nearly touches
one (`ChildTouchesVein`). The street swells like an inhale (`TheSwellBegins`), sirens change tone,
Rhodes calls contact directly beneath them (`ContactBeneath`) — hard cut into Act III. Fires
`OnAct2Complete`.

10 beats, pure dialogue/narration — no combat.

### Shared plumbing ✅ code complete
- `IBLandfallDialogueTypes.h` — `FDialogueLine`, `EDialogueSpeaker`, speaker display-name helper
- `ActBeatProviderInterface.h` — the interface both Directors implement
- `MissionSubtitleHUD.h/.cpp` — generic Canvas subtitle renderer, finds whichever act is running

### Editor integration ✅ done
- `Act1BarracksDirector` and `Act2EscalationDirector` instances placed in `CarrowGateGarrison`
- Act II's `Previous Act Director` wired to the placed Act I instance (auto hand-off confirmed in
  Details panel)
- `BP_IronBreachGameMode`'s `HUD Class` set to `MissionSubtitleHUD` (compiled + saved)
- Level saved, all changes confirmed via editor ("All Saved")

**Not yet done:** a PIE playtest pass to confirm Act I → Act II hand-off and subtitles actually
render end-to-end. `SquadNPCs` (Act I) / `DistrictNPCs` (Act II) arrays are still empty — optional,
for hanging animation cues off scripted events later.

---

## 3. Planned — Acts III, IV, V (design agreed, not yet built)

Escalation ladder for the rest of the mission, per threat class (existing
`EKaijuClass`: `ClassD` → `ClassC` → `ClassB` → `ClassA` → `Catastrophe`):

- **Class C** — infantry can beat it solo. What's already animated (`DA_Kaiju_Alpha` /
  codex-pending-rename `RIDGEBACK`).
- **Class B** — needs an infantry army or one—two mechs. *(Referenced for context/pacing; not
  necessarily fought on-screen in M1.)*
- **Class A** — needs multiple mechs. M1's Act IV threat is a **lower-tier Class A** — the squad
  loses this fight.

### Act III — "Contact" (Class C assault, winnable)
Two or three Class-C kaiju surface near the garrison perimeter. Infantry-solvable: the squad
holds the line, Rhodes calls targets, attack repelled. An earned, confident win that sets up the
fall that's coming. Dialogue beats (contact klaxon, mid-fight callouts, "clear") bracket the fight
via `ScriptedEventTag`s the same way Acts I/II do; the actual spawn/kill logic lives on an
`AIBKaijuSpawner` instance (`MinClass = MaxClass = ClassC`, `MaxConcurrentKaijus` 2–3), not in the
Director.

### Act IV — "Deep Water" (Class A surfaces, the tide turns)
Comms picks up something bigger moving under the district. Command scrambles two mechs
(`IBMech_Base` + `IBGunnerSeat`). The fight holds briefly, then visibly doesn't — a mech goes down
or gets disabled, the deterrent battery doesn't work on this thing. Rhodes orders a full fall-back
to the base (not just a squad retreat). Act ends in a **loss**, not a win — that's the pivot point
of the mission.

### Act V — "Full Retreat" (base evacuation)
The garrison itself falls back — gates, motor pool, whatever's still standing gets stripped and
abandoned. Also the natural home for the civilian carry sequence originally slated for "Act IV" in
the early narrative doc (now bumped a slot since Act IV is the mech battle). Ends with the garrison
lost and the squad regrouping elsewhere, setting up mission 2.

### Open design questions (need your call before implementation)
1. **Species for Act III.** Reuse `DA_Kaiju_Alpha` (multiple instances / reskins), or spin up a
   second Class C species data asset?
2. **Act IV kaiju identity.** Codex (`Docs/Design/KAIJU-CODEX.md`) already reserves Class A for
   the Green Tomb raid boss `SUNDA` ("Warden", 150 m, raid tier) and has `PALAWAN` pinned as M1's
   Class C campaign boss ("the one that made the harbor scar"). A "lower-tier Class A" attacking in
   M1 Act IV isn't in the codex yet — needs either a new individual (codex entry + `DA_Kaiju_*`) or
   a decision to reuse/scale down `SUNDA`'s data with M1-specific tuning. Recommend resolving this
   before writing the Act IV Director so the fight and the codex don't contradict each other.
   *(Does `PALAWAN` become the Act III Class C encounter, or a separate beat entirely?)*
3. **Carry sequence target.** Still Ms. Idris specifically for Act V?
4. **Naming.** Kaiju stays unnamed/classified in-mission dialogue ("the thing under the district")
   regardless of what the codex calls it internally?

---

## 4. Still to build (once the open questions above are answered)

- [ ] `Act3ContactDirector` — beat timeline + `AIBKaijuSpawner` wiring, Class C wave(s)
- [ ] `Act4DeepWaterDirector` — beat timeline + Class A spawn, mech deploy trigger, scripted
      "losing" beats (mech disabled, deterrent failing), fall-back order
- [ ] `Act5RetreatDirector` — evacuation beats, civilian carry sequence, base-lost ending
- [ ] Kaiju codex reconciliation: new/adjusted `DA_Kaiju_*` data asset(s) for the Act III and Act
      IV threats, consistent with `KAIJU-CODEX.md`
- [ ] `AIBKaijuSpawner` instances placed in `CarrowGateGarrison` for Act III (Class C pool) and
      Act IV (Class A, low concurrent count)
- [ ] Mech deploy hookup for Act IV — spawning/possessing the two mechs, wiring their loss/disable
      state into the Director's scripted events
- [ ] Evacuation gameplay for Act V — likely a timed escort/carry objective, not just dialogue
- [ ] PIE playtest of Act I → II hand-off (leftover from §2, blocks trusting the pattern going
      into III–V)
- [ ] `SquadNPCs` / `DistrictNPCs` population (optional, Acts I–II) if scripted-event-driven NPC
      animation is wanted before III–V ship
