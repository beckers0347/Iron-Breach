# Netcode Retrofit — Pass 1 (M2 opening)

*2026-07-05 · by Claude (Fable 5), per ADR-002 · board: u2-01→u2-03 groundwork*

The damage loop, kaiju, and enemy AI are now multiplayer-correct, and the project can host/join sessions. Everything follows one rule: **clients request, the server decides, replication informs.**

## What changed

| File | Change |
|---|---|
| `Combat/HealthComponent.*` | `CurrentHealth`/`MaxHealth` replicate; damage applies only on authority; clients re-broadcast `OnHealthChanged`/`OnDeath` locally via OnRep (so HUD/ragdoll listeners work on every machine unchanged). Client-side `OnDeath` passes `Killer = nullptr`. `bRestartLevelOnDeath` now only fires in standalone — networked death waits for the respawn flow (u1-08). |
| `Combat/HitscanWeaponComponent.*` | Cosmetic-first firing: local sound immediately, then `Server_Fire` RPC; server does the authoritative trace + damage with its own cooldown. Listen host/standalone traces directly. New `SetWeaponData()` + `bAutoBindLegacyInput` (template character keeps auto-bind; infantry disables it). |
| `Infantry/IBCharacter_Infantry.*` | Inline `Fire()` trace deleted — infantry now fires through a `UHitscanWeaponComponent` subobject (one damage path project-wide). `CurrentWeaponData` still the designer knob; forwarded in BeginPlay. |
| `Kaiju/IBCharacter_Kaiju.*` | `Species` replicates (initial-only) so runtime-spawned/late-join clients scale correctly; `CurrentArmor` replicates with armor-break FX mirrored on clients via OnRep; damage handling authority-gated; `ApplySpecies` idempotent and no longer resets armor on clients. |
| `Enemy/IBEnemyAIController.*` | Co-op targeting: `GetPlayerPawn(0)` gone. New `FindNearestVisiblePlayerPawn()` scans all player controllers (server-side); perception + aggro-on-damage accept any player-controlled pawn. |
| `Online/IBSessionSubsystem.*` **(new)** | GameInstance subsystem. Console: **`IBHost`** (create session → listen-host Lvl_Plains) and **`IBJoin`** (find + join first session). Steam when available, NULL/LAN fallback in PIE. Blueprint-callable for Shane's future front-end. |
| `IronBreach.Build.cs` | + `OnlineSubsystem`, `OnlineSubsystemUtils` |
| `IronBreach.uproject` | + `OnlineSubsystemSteam` plugin |
| `Config/DefaultEngine.ini` | Steam OSS block: SteamNetDriver (Ip fallback), `SteamDevAppId=480`, `bInitServerOnClient=true` |

## Build

1. Right-click `IronBreach.uproject` → **Generate Visual Studio project files** (new `Online/` folder + plugin).
2. Usual ritual: close editor → delete `Binaries/Win64` → launch `.uproject` → accept rebuild.

**If the compiler complains** (I wrote this without being able to build — most likely friction points):

- `SEARCH_PRESENCE` undefined → the include `Online/OnlineSessionNames.h` moved again; search the engine for `SEARCH_PRESENCE` and fix the one include in `IBSessionSubsystem.cpp`.
- `Server_Fire` linker/UHT gripes → check the `_Validate`/`_Implementation` pair matches the header signature exactly.
- Anything about `FVector_NetQuantize` → confirm `Engine/NetSerialization.h` include survived in `HitscanWeaponComponent.h`.

## Test

**PIE (5 min):** Play dropdown → Net Mode: *Play As Listen Server*, Players: 2. Both windows fight the same enemies; enemies pick their nearest visible player (they'll split aggro now); health drains on both screens; ragdolls happen everywhere. Kaiju scale check: place BP_Kaiju_Palawan, confirm the client window sees 60m, not 1.8m.

**Two machines (Steam):** Steam running on both, *different accounts*. Console (`~`): `IBHost` on one, `IBJoin` on the other. AppID 480 is shared by every dev on Earth — `IBJoin` grabs the first result, so join promptly. If Steam misbehaves, both on one LAN will still work in `-nosteam`/PIE via the NULL fallback.

## Known gaps (deliberate, next passes)

1. **Remote fire cosmetics** — other players don't hear/see your shots yet (needs a NetMulticast cosmetic + tracer Niagara). Next PR, small.
2. **No respawn flow** — networked death currently leaves you a spectator-corpse (u1-08).
3. **`BP_OnDamaged` hit reacts** fire only where damage applies (server). Client-visible hit reacts should key off `OnHealthChanged`.
4. **Classic replication, not push-model** — deliberate simplicity for pass 1; revisit if profiling ever cares.
5. No lag compensation — fine at co-op latencies vs kaiju-sized targets (ADR-002).
6. GameMode/map defaults still template (`BP_FirstPersonGameMode` / `Lvl_FirstPerson`) — swap when the zone-one loop lands.

## After first successful 2-player session

Mark in Celeste: u2-02 ✓, u2-03 ✓ (partial — cosmetics pending), u2-05 ✓ (spike-level). Then ADR-002's Day 3–4 items are next: server-run AI verification at real latency, and Palawan armor-break with both players contributing.
