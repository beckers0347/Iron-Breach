# Iron Breach — Conventions & Collaboration Etiquette

| | |
|---|---|
| **Status** | DRAFT — pin this once you both agree |
| **Date** | 2026-07-04 |
| **Board** | u0-21; doc bay ud9; retires risks ur4 (repo fragility) + ur6 (Multi-User/GitHub collisions); proposes the uq7 boundary |
| **Team** | Connor (systems C++) · Shane (content, input, levels) · Multi-User Editing + GitHub `beckers0347/Iron-Breach` |

The point of this doc: two people, two workflows (live Multi-User sessions + async git pushes), zero merge disasters. Your devlog already recorded the near-miss — web-uploading binaries corrupts LFS pointers. These rules make that class of accident impossible.

---

## 1. Repository rules (retires ur4)

**Setup once, this week (board u0-20):**

```gitattributes
# .gitattributes — binaries through LFS, always
*.uasset filter=lfs diff=lfs merge=lfs -text
*.umap   filter=lfs diff=lfs merge=lfs -text
*.png    filter=lfs diff=lfs merge=lfs -text
*.fbx    filter=lfs diff=lfs merge=lfs -text
*.wav    filter=lfs diff=lfs merge=lfs -text
```

```gitignore
# .gitignore — never commit generated state
Binaries/
DerivedDataCache/
Intermediate/
Saved/
.vs/
*.sln
```

**Hard rules:**

1. **Never upload through the GitHub web UI again.** Web upload bypasses the LFS filter and writes pointer-corrupting blobs. All pushes go through a real client — GitHub Desktop (already installed) or git CLI.
2. `git lfs install` on **both** machines before the next binary push. Verify with `git lfs ls-files` showing your .uassets.
3. The `.sln` is generated (right-click `.uproject` → Generate Project Files) — never committed, never fought over.
4. Commit messages: `[area] what — why` (e.g., `[kaiju] Palawan aggro territory — roams the basin ring`). Your future selves are the audience.
5. Pull before every work session. Push at every stopping point. Small commits beat weekend megacommits — especially with binaries, where git can't merge, only choose.

## 2. Multi-User Editing ≠ source control (retires ur6, board u2-08's editor-side twin)

Multi-User Editing is a **live shared session**, not persistence. Changes live in the session until someone persists them to disk; git only ever sees what's been persisted and committed. Conflate the two and you get ghost work.

**Session rules:**

1. **One session owner per MU session** — whoever hosts persists. The other NEVER also pushes those assets afterward from their own machine.
2. Ritual: **pull → host session → work → persist → ONE commit by the owner → push.** The session's work becomes exactly one commit with both names in the message.
3. Never `git push` in the middle of a live session; never start a session with unpulled changes on either machine.
4. **One File Per Actor is your friend** — it's on by default with World Partition, which Lvl_Plains uses. Every placed actor is its own tiny file, so Shane editing the village and Connor placing kaiju spawns don't touch the same files, and the level file itself stays unlocked. Let OFPA do the conflict-avoidance; don't disable it.
5. If you both worked outside a session and touched the *same* binary asset: git cannot merge it. The rule is **newest work re-does, oldest work wins** — decided by a 30-second call, not by force-push. (This should be rare if §3 ownership is respected.)

## 3. Ownership map (edit freely, but this is the default)

| Area | Owner | Notes |
|---|---|---|
| `Source/` — all C++ | **Connor** | Shane consumes via BP hooks, never edits directly |
| Core BPs wired to C++ (BP_Kaiju_*, weapon DAs' defaults) | **Connor** | tuning values negotiable in standup |
| Levels (Lvl_Plains, future zones) | **Shane** | Connor places *gameplay* actors in MU sessions or by agreement |
| Input (IMC_*, IA_*), GameMode content, HUD/UI | **Shane** | GameMode *logic* moving server-side per ADR-002 is a joint review |
| `Docs/` | shared | anyone commits; big rewrites get a heads-up |
| Data assets (DA_Kaiju_*, DA_*Rifle) | creator owns | field *meanings* are C++ (Connor); field *values* are content (either) |

"Owner" means: others ask before editing, owner reviews conflicts, nobody is blocked waiting — ask, get a yes in Discord, go.

## 4. Naming & structure (locking in what you already do)

- **C++:** `AIB` prefix for actors/controllers (`AIBCharacter_Kaiju`), `U` components/data (`UHealthComponent`, `UKaijuSpeciesData`), `I` interfaces (`IDamageableInterface`). Keep it — it's clean.
- **Content:** `BP_`, `DA_`, `IMC_`/`IA_`, `Lvl_`, `M_`/`MI_` (materials), `NS_` (Niagara), `SFX_`/`MUS_` (audio), `WBP_` (UMG).
- **Folders:** `Content/IronBreach/{Kaiju, Weapons, Characters, World, Input, UI, Audio, VFX}` — game content never loose in `Content/` root; Megascans/Fab packs stay in their own vendor folders, referenced not moved.
- **References/** stays the concept-art drop zone (per the kaiju pipeline: PNG in → DA + BP out).

## 5. The C++/BP boundary (proposal for uq7)

**C++ (Connor's layer):** anything replicated, anything with authority logic, CONCORD, damage/health, AI controllers, movement modes, data asset *schemas*, save system. Rule of thumb from ADR-002: *if it decides truth, it's C++.*

**Blueprint (Shane's layer):** content wiring, FX/audio hookup via the existing `BP_OnDamaged`/`BP_OnDied`-style events, UI, level scripting, data asset *values*, one-off encounter logic that never runs on the server's authority path.

**The seam:** C++ exposes BlueprintNativeEvents/BlueprintAssignable delegates; BP never contains a `Switch Has Authority` — if content needs authority branching, that's a C++ hook request, not a BP workaround. Ratify this as uq7's ruling or amend it here.

## 6. Build hygiene (codifying the devlog's hard-won loop)

1. The rebuild ritual when the editor misbehaves after C++ changes: **close editor → delete `Binaries/Win64` → relaunch `.uproject` → accept rebuild.** (Already proven; now it's law rather than lore.)
2. After pulling C++ changes: expect the rebuild prompt; if VS is confused, regenerate project files.
3. If a pulled build breaks: the *pusher* fixes forward within the day or reverts — broken `main` blocks a two-person team completely.
4. Editor version stays pinned (5.8.0) until you *both* agree to move; engine upgrades are a scheduled event with a full backup, never a Tuesday impulse.

## 7. The checklists (print these)

**Before any push:** pulled first · LFS active (`git lfs ls-files` sane) · no `Binaries`/`Saved` in the diff · message says what+why.

**Before an MU session:** both pulled · one owner named · nobody has uncommitted work on session-target assets.

**After an MU session:** owner persists · owner commits (both names) · owner pushes · other pulls before touching anything.

**Weekly (standup):** anything in §3 ownership feel wrong? · any binary conflicts this week (if >0, adjust ownership) · LFS quota check (GitHub's free LFS is 1GB storage/bandwidth — a 2km Megascans level will test it; budget for a Data pack or keep vendor packs out of the repo and document a local-restore step instead).

---

*On ratification: mark uq7 DECIDED, flip ud9 to FINAL, check u0-21 — and do u0-20 (the LFS setup) the same day, before the next Lvl_Plains push.*

Sources: [One File Per Actor](https://dev.epicgames.com/documentation/unreal-engine/one-file-per-actor-in-unreal-engine) · [Multi-User Editing](https://dev.epicgames.com/documentation/en-us/unreal-engine/getting-started-with-multi-user-editing-in-unreal-engine) · [World Partition](https://dev.epicgames.com/documentation/unreal-engine/world-partition-in-unreal-engine)
