# Iron Breach — Development Log
*Updated: July 2, 2026 · Engine: Unreal Engine 5.8 · Repo: beckers0347/Iron-Breach*

---

## 1. Engine Migration — UE 5.8 (UE6-Ready)
- Fixed all build errors after the swap to UE 5.8; code written to survive UE6 (no deprecated APIs).
- Added the missing `Modules` section to `IronBreach.uproject` (Runtime module + Engine/EnhancedInput dependencies).
- `IronBreach.Build.cs`: added `PublicIncludePaths.Add(ModuleDirectory)` (fixes `Combat/...` include errors) and module deps: Core, CoreUObject, Engine, InputCore, EnhancedInput, Niagara, AIModule, NavigationSystem, GameplayTasks.
- Migrated raw pointers to `TObjectPtr<>`, added explicit IWYU includes (`Engine/HitResult.h`, `Engine/World.h`, etc.).
- Fixed compile errors: C1083 (include paths), C2445 (`TObjectPtr` ternary ambiguity).
- Enabled **Nanite Foliage (Experimental)** in Project Settings (required by the new tree assets).

## 2. Tooling & Infrastructure
- Installed **Visual Studio Community 2026** (18.7.3, MSVC 14.51) to **D:** drive (C: was out of space) with the Game Development C++ workload.
- Established a reliable rebuild loop: close editor → delete stale `Binaries/Win64` DLL → relaunch `.uproject` → rebuild on prompt.
- **GitHub**: full migrated project pushed to `beckers0347/Iron-Breach` (main) via browser upload — 11+ commits, including cleanup of committed junk (`.vs/`, `DerivedDataCache/`).

## 3. Combat Systems (C++)
- **`UHealthComponent`** — damage/death events; new: engine-damage bridge (`OnTakeAnyDamage`) so `UGameplayStatics::ApplyDamage` works with it; optional **Restart Level on Death** (used by the player).
- **`UHitscanWeaponComponent`** *(new)* — gives any pawn a hitscan gun. Left-mouse fire, data-driven from `WeaponDataAsset` (damage 25, range 50 m, 0.2 s fire interval by default), camera-accurate ECC_Pawn trace, interface-first damage with engine fallback. Added to BP_FirstPersonCharacter.
- **`IDamageableInterface`** — shared BlueprintNativeEvent damage entry point used by player weapons, enemies, and kaiju.
- Key fix: hitscan traces use **ECC_Pawn** (pawn capsules ignore ECC_Visibility — shots used to pass through characters).

## 4. Enemy AI
- **`AIBCharacter_Enemy`** — AI-possessed soldier: fires with cooldown + 2.5° spread, aggro when damaged, ragdoll death (cleans up after 15 s), Blueprint hooks (`BP_OnDamaged`, `BP_OnDied`).
- **`AIBEnemyAIController`** — Patrol / Chase / Attack state machine. Direct line-of-sight check every tick (AIPerception events proved unreliable), attack range 15 m, loses interest after 6 s, random patrol within 12 m of home.
- Editor content: **DA_EnemyRifle** (damage 10, range 50 m, 0.5 s fire rate), **BP_Enemy**, NavMeshBoundsVolume in Lvl_FirstPerson, 2 enemies placed.
- **Damage loop verified in playtests**: enemies spot → chase → shoot; player health drains (watched 100 → 10 → death); death restarts the level; player weapon fires and hits.

## 5. Kaiju Framework (C++, new)
- **`UKaijuSpeciesData`** (data asset) — one asset per species: name, field-guide text, concept art slot, **5-tier threat classification** (Class D 20–40 m swarm → Catastrophe 200 m+), height (drives world scale), health, armor pool, organ count, walk speed, mesh/anim.
- **`AIBCharacter_Kaiju`** — armor-first damage matching the raid design (**ArmorBreak** phase soaks all damage until armor shatters → `OnArmorBroken` event → health/organ phase), species-driven auto-scaling, ponderous turn rate, BP hooks for roars/FX.
- `References/` folder created for concept art. *Still to do: create the first DA_Kaiju_* asset + BP_Kaiju in-editor once the concept PNG is dropped in.*

## 6. Lvl_Plains — Plains Biome + Village (new level)
- Open World (World Partition) level: 2 km × 2 km landscape, mountain ring around a central basin, Megascans **Uncut Grass** landscape material.
- **Meadow**: ~194,000 Megascans **Wild Grass** foliage instances (3 variants) painted around the village site.
- **Trees**: 8 **Silver Birch** (Megaplants, 4 variants) — Nanite-assembly, wind-animated.
- **Village**: 6 distinct half-timbered medieval houses placed in a plaza ring around PlayerStart (west/east/north/south/NE/SE, rotated to face center).
- **Lighting**: sun raised 16° → 55° elevation, intensity 6 → 12 lux — bright daylight instead of dusk.
- All content saved to disk.

## 7. Asset Packs Acquired (all free, Fab EULA accepted)
| Pack | Source | Used for |
|---|---|---|
| Uncut Grass (surface) | Quixel Megascans | Landscape material |
| Wild Grass (3D plants) | Quixel Megascans | Meadow foliage |
| Silver Birch (Megaplants PVE) | Fab | Trees |
| Medieval Fantasy Village Houses (13 buildings) | Fab (karaman, free personal license) | Village |
| Wooden Stool | Quixel Megascans | Village prop (imported, not yet placed) |

Duds: "Stylized Fantasy Architecture Set" (imported as a single plane), "Rural Australia" (never downloaded).

## 8. Open Items / Next Session
- Clear the tall grass out of the village plaza (erase brush was misbehaving).
- Add NavMeshBoundsVolume + BP_Enemy placements to Lvl_Plains so the AI works there.
- Create DA_Kaiju data asset + BP_Kaiju placeholder (needs your concept PNG in `References/`).
- Push Lvl_Plains + Kaiju source + new assets to GitHub — needs a real git client with LFS (web upload would corrupt LFS pointers).
- You: verify player→enemy kill feel (4 hits should ragdoll an enemy).
