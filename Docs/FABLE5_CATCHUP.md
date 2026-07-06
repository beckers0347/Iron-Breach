# IRON BREACH — CATCH-UP BRIEF FOR FABLE 5
*Paste everything below the line into the other chat to correct its stale context.*

---

**IMPORTANT — the project has changed engines. Please update your understanding.** Anything in our earlier conversation that assumed **Unity** is now obsolete. IRON BREACH is no longer a Unity project. It was migrated to **Unreal Engine 5.8** (kept forward-compatible toward UE6), and substantial work has happened since. Here is the current ground truth.

## The switch
- **Engine: Unreal Engine 5.8** (5.8.0-55116800), not Unity. All prior Unity-specific plans (C# MonoBehaviours, Unity prefabs, Unity's input/physics, etc.) do not apply. The game is now C++ + Blueprints in Unreal.
- Migration is done and verified: the module builds, the editor runs, and it's pushed to GitHub.
- IDE is **Visual Studio Community 2026** (MSVC 14.51). Project lives at `D:\Unreal Games\IronBreach`. Repo: **beckers0347/Iron-Breach** (`main`). A collaborator, Shane Becker, also edits via Unreal Multi-User Editing.

## What's been BUILT in Unreal (working C++)
- **Combat:** `UHealthComponent` (death + restart-on-death, engine-damage bridge), `UHitscanWeaponComponent` (data-driven weapon, ECC_Pawn trace, interface-first damage), `IDamageableInterface`, `WeaponDataAsset`. The full damage loop is playtested and working.
- **Enemy AI:** `AIBEnemyAIController` (patrol / chase / attack, line-of-sight, lose-interest) + `AIBCharacter_Enemy` (fire cooldown, spread, aggro-on-damage, ragdoll death).
- **Kaiju framework:** `UKaijuSpeciesData` (data asset — 5-tier threat class enum, height→auto-scale, health, armor pool, organ count, mesh/anim) + `AIBCharacter_Kaiju` (armor-first damage, `OnArmorBroken`, applies species stats at BeginPlay). First creature **DA_Kaiju_Palawan / BP_Kaiju_Palawan** (Class C, 60 m) created and verified auto-scaling in Play-in-Editor.
- **Infantry** character class, plus Shane's rifle/crosshair/gamemode/input content.

## What's been BUILT in Unreal (content)
- **Lvl_Plains** — a 2 km open-world level (the future "Carrow Exclusion Zone"): mountain-ringed basin, Megascans grass biome (~194K instances), Silver Birch trees, a 6-building medieval village, daylight lighting. This is the first playable open-world zone.
- A first-person template level where the damage loop was proven (enemy chases and shoots the player, health drains, death restarts).

## What's been DESIGNED (four docs in `Docs/`, all written this project)
1. **Narrative research** — study of what makes game stories last → 38 reusable design laws.
2. **Franchise narrative bible** (20 sections) — the full story. Premise: near-future 2042 Earth; giant **kaiju** erupt from beneath cities; humanity's defense force is **"the Breakwater"**; the weapons are **two-pilot "Caryatid" mechs** driven by a neural-sync system called **CONCORD / "the clasp."** The hidden truth: the kaiju are a **response, not an invasion** — a 1971 deep-drill breach woke a living planetary layer ("the Understory"); **the war is secretly a hospice.** Signature motifs: the nine-beat "Nine" signal, "Deepfall," a "null-quiet" player character. Built for years of live content.
3. **Phase 1 roadmap** — campaign + two open-world zones (public events, biome-matched kaiju, mini-dungeons, secrets, loot, easter eggs) + PVP + a 3-player Nightfall-style dungeon + a finale **raid** ("The Green Tomb," final boss CHALLENGER). Milestone plan; netcode is the critical path.
4. **Classes & progression** — 4 classes (Breaker/Picket/Bellringer/Corpsman), 3 "Graft Line" elements (Ossein/Toll/Veinlight), and a Kaiju-No.8-style **Redline** release system with a growing ceiling %.

## Current status
The team is mid-way through making the first open-world zone playable (adding navigation + enemies + the first kaiju) and has just verified the kaiju scaling tech. The next major block is **online/netcode** (replication, sessions, saves), since everything built so far is single-player logic.

**If you (Fable 5) want to help going forward, work in Unreal terms — C++/Blueprints, UE data assets, UE navmesh/AI, etc. — not Unity.** If you need specifics, the four docs above plus a `DEVLOG.md` are in the project's `Docs/` folder and hold the full detail.
