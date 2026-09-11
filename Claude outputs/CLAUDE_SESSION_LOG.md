# Iron Breach — Claude Session Log

## READ ME FIRST (for a new/fresh Claude chat)

If you are a new Claude session picking this up: this file is the running
handoff log for work Claude does on the Iron Breach UE5 project. Read this
whole file before doing anything else, then keep appending to it (never
delete prior entries — add a new dated section at the bottom).

**Project basics:**
- UE 5.8, C++ project, repo at github.com/beckers0347/Iron-Breach
- Project root: `X:\IronBreach` on Shane's PC (Windows path), mounted at
  `$HOME/mnt/IronBreach` when reached via the device_bash / remote-devices
  tools from a Claude cloud session linked to Shane's computer
- Team: Shane (Levels/Input/GameMode/HUD/content wiring) + Connor (owns
  `Source/` C++, remote collaborator) — see `Docs/IRONBREACH-collab-conventions.md`
- Military sci-fi FPS: infantry / mech ("Caryatid" two-pilot frames) / kaiju
  combat. Full architecture notes from a deep source read on 2026-09-11 are
  summarized in that day's log entry below — read it for class names,
  systems, and known bugs before touching code.
- Dev loop: `zzcharwatch.bat` polls `Saved/zz_build_request.txt` on Shane's
  machine to trigger editor rebuilds/Python scripts; `zzpush.bat`/`zzpull.bat`
  are git wrappers. Always `zzpull` (or `git status`) before big edits, and
  make sure work is committed/pushed before letting any AI tool do bulk edits
  to a level (3,000+ actor levels are not fun to lose to a bad autonomous run).
- Shane's preferences: step-by-step work with log/verification at each stage,
  complete file outputs (not snippets), specific node-by-node instructions
  when Blueprint work is involved.

**Convention:** every session, append a new `## YYYY-MM-DD` section below
with what was worked on, what changed, what's still open, and anything the
next session needs to know. Keep entries factual and specific (file paths,
actor names, asset names) so a cold-start session can act on them without
re-deriving context.

---

## 2026-09-11

- Did a full read of the entire non-binary project (all of `Source/`, every
  doc in `Docs/`, `Config/*.ini`, `Scripts/*.py`, root `.bat` tooling,
  `UnrealLevelBuilder.py`) to build complete architecture familiarity.
  Key systems: Combat framework (HealthComponent/HitscanWeaponComponent/
  WeaponRigComponent/WeaponVisualData), Infantry state machine
  (IBCharacter_Infantry — sprint/aim/crouch/carry mutual exclusion, PIP
  scope via SetupScopePip), Mech "Caryatid" two-pilot split (IBMech_Base +
  IBGunnerSeat + ConcordComponent sync-meter T0-T4), Kaiju 3-phase fight
  state machine (Armored/OrganPhase/Exposed, organ raycast probes), Missions
  (per-act director actors for M1 Landfall / M2 Dead Reckoning), Classes
  (Breaker/Picket/Bellringer/Corpsman kits). Extensive design docs: netcode
  ADR, Caryatid architecture decisions, CONCORD sync-drama spec, Phase 1
  roadmap (15 missions, 3 acts), Kaiju Codex, Bastion city design, and an
  807-line narrative bible (7 plot twists, 5-year live-service roadmap).
- Known issues on file as of this read: PIP scope camera-tick-disable bug
  (SetupScopePip / IBCharacter_Infantry.cpp) — flagged as likely cause of a
  "dead black square" scope symptom. **Shane confirmed this is now fixed**
  as of this session (fix made outside this chat, not verified by reading
  updated code yet — worth re-reading SetupScopePip in a future session to
  see what changed and log it here).
- Other known issues at time of the read (may or may not still apply, check
  before assuming): hand-IK animation-thread-safety issue in
  IBAnimInstance_Infantry; risk that mech ArmCannon Blueprint bypasses the
  kaiju damage pipeline if it doesn't call HandleTakeDamage; RaidStateMachine
  is an unwired stub; no packaged (non-PIE) build attempted yet as of the
  last updatelog doc.
- Started helping Shane use the **Aura** UE5 plugin (tryaura.dev — agentic
  AI agent for Unreal, already listed as an enabled plugin in
  `IronBreach.uproject`) to (1) improve the flat/placeholder materials on
  garrison architecture and (2) break up boxy placeholder geometry into
  more detailed "genuine military building" forms — starting with the
  Armory building in the CarrowGateGarrison level (actors:
  `07_Armory_Ceiling`, `07_Armory_DoorFrame`, `07_Armory_Wall_E_Fill0`,
  `07_Armory_Wall_E_FillTop`, `07_Armory_Wall_E_Glass0`, all currently
  flat-cube StaticMeshActors on the shared `M_AI_Wall` material). Gave
  Shane concrete Aura prompts to try (Material Agent for the wall material,
  Agent mode for breaking up the Armory's massing) — see chat for the
  exact prompt text used; log the outcome here next session (what worked,
  what Aura actually produced, whether the level held up structurally).

- Follow-up (same session, still 2026-09-11): Shane got the Aura-generated
  M_Armory_Concrete_Weathered material into the level (weathered concrete
  panel look, vents baked into the texture) but it reads as an obvious
  repeating "wallpaper" tile across the flat Armory wall. Diagnosed as
  UV-tiling repetition (single texture, uniform grid, no macro variation),
  not a texture-quality problem. Advised: (1) add a large-scale macro
  variation/noise blend layer in the material to break per-panel uniformity
  — try this first, cheapest; (2) add actual 3D geometry detail (vents,
  pipes, hatch) on top of the flat wall so depth breaks the pattern
  regardless of texture; (3) vary panel size/spacing so the grid isn't
  perfectly uniform. Also answered: yes, Aura can generate whole new
  structures via Agent mode, but recommended NOT doing one monolithic
  building replacement — instead have Aura build a small modular kit
  (wall segment / corner / door-surround / roof-cap pieces snapping at 4m
  increments) that can be placed with the existing UnrealLevelBuilder.py
  pipeline, same pattern as the current Iceland-kit mountain pieces. Next
  session: check what Shane actually got Aura to produce for the macro
  variation and/or kit pieces, and log the result.
