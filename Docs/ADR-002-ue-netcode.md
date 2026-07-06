# ADR-002 — Netcode Architecture for Iron Breach (Unreal Engine 5.8)

| | |
|---|---|
| **Status** | DRAFT — awaiting ratification by Connor + Shane |
| **Date** | 2026-07-04 |
| **Supersedes** | ADR-001 (written for the Unity build; void since the UE migration) |
| **Decides** | Celeste decision log uq1 (topology), uq2 (online subsystem), uq3 (Iris) |
| **Board** | u2-01; doc bay ud6; risk ur1 (single-player logic → MP retrofit) |

---

## 1. Problem statement

Everything built so far is single-player logic running with local authority: `UHealthComponent`, `UHitscanWeaponComponent`, `IDamageableInterface`, the enemy AI (`AIBEnemyAIController` / `AIBCharacter_Enemy`), and the kaiju framework (`UKaijuSpeciesData` / `AIBCharacter_Kaiju`). Your own Phase 1 roadmap names netcode the critical path. This ADR decides the three foundation questions — who hosts, which online service, which replication tech — and defines the replication treatment for each existing system, so the retrofit happens once, correctly, instead of system-by-system improvisation.

Scale target: 2-player co-op now; 3-player dungeon and a raid later; one 60m kaiju plus dozens of humanoid enemies in a 2km World Partition zone.

**The good news the Unity ADR never had:** UE ships the hard parts. Server-authoritative actor replication, RPCs, and client-predicted character movement (CMC) are built-in and battle-tested. The question is no longer "which vendor" — it's configuration and discipline.

## 2. Decisions

### D1 — Topology (uq1): **Listen server**, with dedicated-compatible discipline

One player (usually you or Shane) hosts; the game runs server logic + local client in one process. Rationale:

- Co-op has no host-advantage problem (nobody cheats at fighting a kaiju together).
- Dedicated servers require a **source-built engine from GitHub** — a real cost in build times, disk, and maintenance for a two-person team, plus infrastructure to rent and operate. Wrong spend before the game is fun online.
- The hedge: **write everything server-authoritative anyway** (`HasAuthority()` gates, server-only damage, no client-trusted state). Then "dedicated" stays a compile-target decision you can make at raid/PVP scale, not a rewrite. Revisit at M4 when PVP survives or dies (uq10).

### D2 — Online subsystem (uq2): **Steam-first** (OnlineSubsystemSteam + Steam Sockets); EOS Plus deferred

- Phase 1 ships on Steam PC. `OnlineSubsystemSteam` is the battle-tested path: sessions, invites, presence. **Steam Sockets** gives listen servers NAT traversal, encryption, and DDoS protection over Steam's relay network — the classic "can't connect to my friend" problem solved without your own relay.
- Develop today with Steam's shared dev AppID (SpaceWar, 480); buy the real AppID ($100 Steam Direct) when the store page milestone arrives (u5-04).
- **EOS** is free (relay, lobbies, voice) and the crossplay story is OSS EOS + **EOS Plus** mirroring sessions to Steam — but it adds account-linking complexity you don't need for a Steam-only Phase 1. Keep session logic behind the OSS abstraction (no direct Steamworks calls in gameplay code) so EOS Plus can layer in later without surgery.

### D3 — Replication tech (uq3): **Standard replication + push model. Not Iris. Not Mover.**

- **Iris** (the Fortnite-derived replication system) is opt-in and on the Beta track in 5.8, but its honest break-even is on the order of **~100+ concurrently replicated actors** — battle-royale and big-world territory. Iron Breach's worst case (8 players, a kaiju, a few dozen enemies and events) sits comfortably under that. Standard replication with net dormancy and sensible NetUpdateFrequency is the boring, correct choice. Because Iris is opt-in *alongside* standard replication, this decision is reversible later without rearchitecting.
- **Mover** (Epic's CMC successor with rollback prediction) got a broad 5.8 update but **remains Experimental**. Infantry uses **CMC** — its client prediction is the most proven piece of netcode in the industry. Kaiju don't need prediction at all (server-owned AI pawns; clients interpolate). Track Mover for the Caryatid later, but don't ship Phase 1 on an Experimental movement stack.

## 3. Per-system replication treatment (the retrofit map)

| System | Treatment |
|---|---|
| `UHealthComponent` | Health becomes a replicated property (push model) with `OnRep` for HUD/FX. Damage is applied **only on the server**; the `OnTakeAnyDamage` engine bridge gets an authority gate. Death → server decides, clients play cosmetic death via rep notify. |
| `UHitscanWeaponComponent` | Client presses fire → immediate **cosmetic** tracer/sound locally → `Server_Fire` RPC with aim data → server performs the ECC_Pawn trace and applies damage through `IDamageableInterface`. Server enforces fire interval (client cooldown is UX, not law). Lag-compensated rewind is a later nicety; at co-op latencies vs kaiju-sized targets, plain server traces are fine. |
| `IDamageableInterface` | Becomes a **server-only execution contract** — document it in the interface header: implementations may assume authority. |
| Enemy AI (`AIBEnemyAIController`) | AI controllers exist **only on the server** (UE default). Pawn movement replicates; your per-tick LOS stays server-side unchanged. Ragdoll death is cosmetic → trigger on clients via rep notify; the 15s cleanup runs server-side and destroys the replicated actor. |
| `AIBCharacter_Kaiju` | Server-owned. Armor pool + organ states replicate via rep notify; `OnArmorBroken` fires on the server → replicated event drives roar/FX on every client. **Gotcha:** species-driven auto-scale currently runs at `BeginPlay` from the data asset — on clients the species reference must be present *before* scaling (replicate the `UKaijuSpeciesData` pointer with `COND_InitialOnly` and apply scale in its OnRep, so join-in-progress players see a 60m Palawan, not a 2m one). |
| `WeaponDataAsset` / `UKaijuSpeciesData` | Data assets are content, not state — both clients load them from pak; only *references* replicate. |
| Restart-on-death | Single-player behavior. In MP: server-controlled respawn flow (already tracked as u1-08). |
| GameMode / GameState | Shane's GameMode logic is **server-only by design** (UE never replicates GameMode). Anything clients must see (match state, event timers) moves to `GameState`/`PlayerState`. |
| Lvl_Plains / World Partition | Server is authoritative over streaming-relevant state; kaiju and events far from all players use **net dormancy** to cost nothing. |
| SaveGame (u2-06) | The host's save is the world's save. Design saves server-side from day one; client profiles (cosmetics, settings) stay local. |

**One rule to pin above both desks:** *clients request, the server decides, replication informs.* It's the same authority discipline as the old EventBus rule, wearing Unreal clothes.

## 4. Caryatid forward-compatibility (informs uq4, decided in the Caryatid doc)

Nothing chosen here blocks the dual-pilot mech, and one UE constraint shapes it: **one PlayerController possesses one Pawn.** The pattern that fits is seat pawns — each pilot possesses a lightweight seat; the Caryatid body is a single server-authoritative pawn that consumes both seats' replicated input streams; the navigator seat gets client prediction via a custom movement component; CONCORD runs as a server-side component reading coordination signals from both seats. That is exactly the "nobody owns the mech" insight from the old ADR, and standard replication handles it. GAS-vs-custom for abilities (uq5) stays open for the Caryatid architecture doc (ud8).

## 5. Spike plan — one week, on the real project

Goal: the existing damage loop, playable by two machines, before any new systems land.

- **Day 1 — Sessions.** Enable OnlineSubsystemSteam + Steam Sockets (dev AppID 480). Host on one machine, join from the other via session find/invite. *Exit: both of you standing in Lvl_Plains.*
- **Day 2 — Movement + weapons.** CMC replication defaults verified; `Server_Fire` RPC path in `UHitscanWeaponComponent`; health replication with OnRep HUD. *Exit: you can shoot each other's targets and watch health drain on both screens.*
- **Day 3 — Enemy AI over the network.** Server-run controllers, ragdoll-on-rep, kill feel checked at real latency (also artificial 100ms). *Exit: co-op firefight against the village enemies feels right.*
- **Day 4 — Palawan replicated.** Armor pool + OnArmorBroken FX on both clients; join-in-progress scale check (the InitialOnly gotcha above). *Exit: two players break armor together; late-joiner sees a correct kaiju.*
- **Day 5 — Sanity + report.** Reconnect behavior, host-quit behavior, save/load smoke test. Amend this ADR with findings; GO/NO-GO on the M2 plan.

**Watch items (not kill criteria — there's no vendor to switch, only scope to adjust):** Steam Sockets connection reliability across your two networks (fallback: EOS P2P relay); join-in-progress vs World Partition streaming (fallback: lobby-start sessions for Phase 1); host-machine perf with 194K foliage instances + server duties (fallback: perf budget pass, u0-22).

## 6. Costs

| | Now | At ship | If it outgrows this |
|---|---|---|---|
| Listen server + Steam Sockets | $0 (AppID 480) | $100 Steam Direct | — |
| EOS (deferred) | $0 | $0 | EOS Plus for crossplay, still $0 |
| Dedicated servers | avoided | avoided | source-built engine + Linux target + hosting |
| Iris | avoided | avoided | opt-in flip if actor counts explode |

## 7. Ratification checklist

1. **Both:** listen server through Phase 1, dedicated-compatible discipline everywhere — agreed?
2. **Shane:** GameMode/GameState split — anything in your current gamemode/input content that clients need to *see* (and therefore must move to GameState)?
3. **Connor:** the `Server_Fire` refactor touches your weapon component's public surface — happy with cosmetic-first firing (instant local tracer, server-confirmed damage)?
4. **Both:** Steam-first, EOS Plus later — or is crossplay a Phase 1 requirement after all?
5. On ratification: mark uq1/uq2/uq3 **DECIDED** in Celeste, flip doc ud6 to DRAFT→FINAL after the spike amends it, and schedule the 5-day spike as the opening of M2.

## 8. Sources

- [UE 5.8 release notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes) · [Networking overview](https://dev.epicgames.com/documentation/unreal-engine/networking-overview-for-unreal-engine)
- [Iris replication system (5.8 docs)](https://dev.epicgames.com/documentation/unreal-engine/iris-replication-system-in-unreal-engine) · [Iris on the public roadmap (Beta track)](https://portal.productboard.com/epicgames/1-unreal-engine-public-roadmap/c/2251-iris-beta-) · [Should you opt in? (2026 analysis, ~100-actor break-even)](https://www.strayspark.studio/blog/iris-replication-unreal-engine-opt-in-2026)
- [Mover in UE (Experimental)](https://dev.epicgames.com/documentation/en-us/unreal-engine/mover-in-unreal-engine) · [CMC networked movement](https://dev.epicgames.com/documentation/unreal-engine/understanding-networked-movement-in-the-character-movement-component-for-unreal-engine)
- [Steam Sockets (NAT traversal, encryption, DDoS protection)](https://dev.epicgames.com/documentation/unreal-engine/using-steam-sockets-in-unreal-engine) · [EOS OSS plugin + EOS Plus crossplay](https://dev.epicgames.com/documentation/unreal-engine/online-subsystem-eos-plugin-in-unreal-engine) · [EOS P2P relay scope](https://edgegap.com/blog/can-epic-online-services-eos-relays-allow-for-dedicated-server-or-authoritative-server)
- [Dedicated servers require a source-built engine](https://forums.unrealengine.com/t/is-it-required-to-build-engine-from-source-code-when-building-dedicated-server-in-ue5/785841)
