# Caryatid Architecture — Two Pilots, One Mech, in Unreal

| | |
|---|---|
| **Status** | DRAFT — for review by Connor + Shane |
| **Date** | 2026-07-04 |
| **Resolves** | Celeste uq4 (seat model) and uq5 (GAS vs custom) |
| **Board** | u3-01; doc bay ud8; risk ur2 (dual-pilot netcode) |
| **Depends on** | ADR-002 (listen server, standard replication, server-authority discipline) |
| **Feeds** | u3-02 CONCORD component, u3-03 drama-spec port (ud7), u3-04 call-and-response, u3-05 AI copilot, M4 classes/Graft/Redline |

---

## 1. The constraint that shapes everything

Unreal's rule: **one PlayerController possesses one Pawn.** Two pilots can never both possess the Caryatid. Every viable design routes around this, and the community-standard multi-crew pattern (Squad-style vehicles, marketplace multi-seat systems) is well established: one seat holds real possession of the hull, other crew occupy attached seat pawns or send commands.

The old insight — *nobody owns the mech* — gets a UE-shaped amendment:

> **The navigator owns the hull. The gunner owns the guns. The server owns the truth.**

## 2. Decision uq4 — Seat model

### Options considered

**A. Symmetric seat pawns** — both pilots possess lightweight seat pawns; the body is possessed by no one and consumes both input streams server-side.
*Clean symmetry — and it's what ADR-002 §4's forward-look sketched, so this doc formally supersedes that sketch. The problem: the body has no owning client, so **no built-in client prediction for anyone**. The navigator's mech movement would be server-round-trip laggy or need fully custom prediction — the hardest problem in netcode, volunteered for. Rejected.*

**B. Navigator possesses the body; gunner possesses an attached seat pawn.** ✅
*The navigator gets UE's client-predicted movement **for free** because they're the owning client of the hull. The gunner owns a `AGunnerSeat` pawn attached to the body — their turret aim replicates owner→server→others continuously, and firing uses the exact `Server_Fire` cosmetic-first pattern ADR-002 already establishes for infantry weapons. Asymmetry is not a bug: the roles ARE asymmetric (movement feel needs prediction; aiming tolerates it fine, as every turret in every shipped UE game shows).*

**C. Both pilots keep personal pawns; the body is driven purely by command RPCs.**
*Maximum decoupling, worst feel — navigator input becomes RPC-latency movement. Rejected for the same reason as A.*

### The recommendation in one diagram

```
PlayerController (Navigator) ──possesses──▶ ACaryatid (ACharacter)
                                             ├─ CMC w/ custom movement modes (mech gait, server-auth, client-predicted)
                                             ├─ UAbilitySystemComponent (body ASC — shared)
                                             ├─ UConcordComponent (server-side sync brain)
                                             └─ attached: AGunnerSeat (APawn)
                                                  ├─ replicated aim (owner-authoritative rotation)
                                                  ├─ UCaryatidWeaponComponent (Server_Fire pattern)
                                                  └─ possessed by ◀── PlayerController (Gunner)
                                                              or ◀── AIBCopilotController (solo)
```

Design notes:

- **`ACaryatid` is a Character, not a bare Pawn** — heresy-sounding for a 25m mech, but CMC's replicated, client-predicted movement is the most battle-tested netcode in the industry (ADR-002 D3), and custom movement modes give the ponderous gait, dodge-chains, and desync control profiles without surrendering prediction. Only if CMC genuinely fights the scale (risk ur8) do we fall back to a custom `UPawnMovementComponent` — and by then Mover may have left Experimental.
- **Boarding = possession swap** (u3-07): interact → `Server_Board` → server parks the infantry pawn (hidden, collision off), possesses pilot into the hull or seat, swaps their Enhanced Input mapping context (`IMC_Navigator` / `IMC_Gunner`). Ejecting reverses it. Seat swap mid-fight is the same operation between hull and seat, server-arbitrated so two pilots can't trade into the same seat.
- **AI copilot** (u3-05): an `AIBCopilotController` possesses the `AGunnerSeat` — the same pawn, same input surface, same abilities as a human gunner. Parity by construction, exactly like the old `AICopilotGunner` promise. Its "damaged subroutines" state (from the drama spec) is just ability tags being revoked.
- **CONCORD reads, never guesses** (u3-02): `UConcordComponent` lives on the body, server-side, subscribing to gameplay events from both seats (ability activations, hits landed, dodges, calls answered). It is the drama spec's meter, ported: event-driven, no timers, tuning in a `UDataAsset`.

## 3. Decision uq5 — GAS, with one honest hybrid

**Recommendation: adopt the Gameplay Ability System** for pilot abilities, call-and-response, and CONCORD's tier effects. Reasons:

1. **It's built for exactly this.** Replicated, client-predicted ability activation; cooldowns; gameplay tags as state (`Concord.Tier.3`, `Caryatid.Desynced`, `Ritual.Active`); GameplayEffects as buffs. CONCORD tier bonuses become GameplayEffects granted/removed on tier change — no bespoke buff plumbing.
2. **It amortizes across the whole game.** M4's classes (Breaker/Picket/Bellringer/Corpsman), Graft Line elements, and the **Redline release system are textbook GAS**: Redline's growing ceiling % is an Attribute; release states are Effects; class kits are ability sets. Building a custom ability stack for the mech and then GAS-or-another-custom for classes would mean paying twice.
3. **Call-and-response maps cleanly** (u3-04): the Call is an ability applying an `AwaitingResponse` tag + effect window; the Response is an ability whose activation requires that tag; success fires a CONCORD coordination event; the drama spec's Reconnection Ritual is the same machinery with a dealt pattern. One system, three features.

**The hybrid:** the CONCORD **meter itself** stays plain C++ in `UConcordComponent` — event-driven accumulation logic doesn't want to be an ability, and the drama spec's rules (floor protection, T0 guard, Adrenaline/Debt modifiers) read better as explicit code. The component **mirrors** its value into a GAS Attribute so effects and UI bind naturally. Meter logic owns truth; GAS distributes consequences.

**Cost acknowledged:** GAS has a real learning curve (ASC init on possession, prediction keys, replication modes). Mitigations: the community's canonical GASDocumentation, Epic's own Lyra as reference, and the spike below proves the risky 20% before commitment. Fallback if the spike sours: custom ability component stack (uq5 reopens), losing the M4 amortization — which is why the spike tests GAS on a *class ability* too, not just mech parts.

## 4. Replication treatment (extends ADR-002 §3)

| Piece | Treatment |
|---|---|
| Hull movement | CMC replication + navigator client prediction (owning client). Simulated for gunner + infantry. |
| Gunner aim | `AGunnerSeat` rotation, owner-authoritative replicated property (continuous, quantized). |
| Weapons fire | `Server_Fire` RPC + instant local cosmetics (ADR-002 pattern, same code family as infantry). |
| CONCORD tier | Server computes; replicated tier + RepNotify drives both cockpit HUDs and the tier GameplayEffects. |
| Desync / ritual | Server states via tags; ritual step inputs are client ability activations validated server-side; Last Link slow-mo stays client-local juice (never dilate the server). |
| Boarding / seats | Server-only possession logic; seat occupancy replicated for HUD + third parties. |
| ASC placement | Body ASC owned by the hull (navigator's net owner); gunner seat gets its own ASC for gunner-personal abilities. Pilot-personal progression ASCs stay on PlayerState (M4 classes) — standard Lyra-style split. |

## 5. Spike plan — one week, gray-box (opens M3, after the M2 netcode spike)

- **Day 1:** `ACaryatid` gray-box Character at 20m scale, custom movement mode #1 (mech walk), navigator possession + `IMC_Navigator`. *Exit: driving a big box in Lvl_Plains feels weighty, predicted, replicated.*
- **Day 2:** `AGunnerSeat` attached + possessed by second player; replicated aim; `Server_Fire` turret. *Exit: one drives, one shoots, on two machines.*
- **Day 3:** Boarding possession swap from infantry, both directions; AI copilot possesses the empty seat. *Exit: solo player boards and fights with AI gunner.*
- **Day 4:** GAS proof: body ASC + one navigator ability (dodge-chain), one gunner ability (vent), one call-and-response pair granting a test CONCORD event; tier GameplayEffect applying a speed buff. **Also one infantry class ability on a PlayerState ASC** (the M4 amortization test). *Exit: a sync combo lands online through GAS.*
- **Day 5:** `UConcordComponent` v1 wired to real events; desync tag flips the movement profile; findings amend this doc. GO/NO-GO on GAS (uq5) and CMC-at-scale (ur8 watch item).

**Kill criteria:** navigator prediction misbehaves in custom movement modes beyond Day-1 tuning (→ custom movement component path); GAS prediction keys fight the seat split (→ custom ability stack, uq5 reopens); possession swaps drop input contexts or cameras irrecoverably (→ command-RPC fallback for the gunner only).

## 6. What this means for the drama spec port (ud7 / u3-03)

The SPEC-sync-failure-drama design survives intact — only §9's implementation mapping changes: `SyncMeter` → `UConcordComponent` + mirrored Attribute; `SyncTuningSO` → `UConcordTuningData : UDataAsset`; ritual machine → ability-driven pattern with server validation; HUD hooks → tag/attribute listeners; Kaiju interference (Neural Howl) → a `GameplayEffect` the kaiju applies, which slots into `AIBCharacter_Kaiju`'s attack framework. The no-timer principle holds: GAS effect windows are the *challenge definition*, transitions still fire on events.

## 7. Open questions (small, for the review)

1. Gunner camera: dedicated turret cam vs shared cockpit view with independent aim reticle — feel decision, prototype both on Day 2.
2. Can pilots swap seats mid-desync, and does that reset the ritual? (Drama call — my instinct: allowed, ritual re-deals, sync unaffected. Cheap drama.)
3. Does the navigator get a *view* of gunner aim (Pacific Rim shared-mind fantasy) or is the information asymmetry the point (per the drama spec's degraded-partner-readouts)? Recommend: normal state shows partner intent ghosted; desync removes it.
4. Hull health: reuse `UHealthComponent` as-is on the body (it already does armor-free damage + events) or a mech-specific variant with subsystem damage — defer to after the M2 spike.

## 8. Ratification checklist

1. **Both:** navigator-possesses-hull asymmetry accepted (gunner is turret-model, not co-owner)?
2. **Connor:** GAS adoption — comfortable committing the learning curve now, given the M4 payoff (classes, Graft, Redline)?
3. **Shane:** boarding/possession swaps touch GameMode/input content — any conflicts with your current input setup?
4. On ratification: mark uq4 + uq5 **DECIDED** in Celeste, flip ud8 to FINAL after the spike amends it. The spike itself is board items u3-01/u3-06 combined.

## 9. Sources

- [One-controller-one-pawn + multi-seat community patterns](https://forums.unrealengine.com/t/multi-seat-vehicles-for-multiplayer/1834496) · [Multiple players, one vehicle](https://forums.unrealengine.com/t/multiplayer-multiple-players-controlling-a-vehicle/642893)
- [GAS official docs (UE 5.8)](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-ability-system-for-unreal-engine) · [GASDocumentation (tranek) — the community bible](https://github.com/tranek/GASDocumentation)
- [CMC networked movement](https://dev.epicgames.com/documentation/unreal-engine/understanding-networked-movement-in-the-character-movement-component-for-unreal-engine) · [Mover (still Experimental — watch item)](https://dev.epicgames.com/documentation/en-us/unreal-engine/mover-in-unreal-engine)
- ADR-002 (this repo's Docs/) for the authority rule and `Server_Fire` pattern; SPEC-sync-failure-drama for everything CONCORD enforces.
