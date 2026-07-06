# SPEC — Sync Failure States & Drama

| | |
|---|---|
| **Status** | DRAFT — for review by both pilots |
| **Date** | 2026-07-04 |
| **Closes** | GDD gap m0-22 (sync failure states + drama); half of Doc Bay d2 |
| **Depends on** | Built `SyncMeter` (0–100, five tiers incl. Overdrive, event-driven, pure C#); ADR-001 (host authority) |
| **Feeds** | m1-09 (implementation), m0-23 (call-and-response — shared ritual mechanics), m2-09 (cockpit HUD), kaiju tier spec |

---

## 0. Design thesis

The GDD defines what high sync *gives*. This spec defines what losing it *means*. The rule that governs everything below:

> **Failure must produce a story, and recovery must produce a memory.**

Desync is not a debuff — it's the second act of the fight. If two pilots never desync, they never get the "we clawed it back" moment that makes the dual-pilot fantasy land. So failure is designed to be *entered occasionally, exited actively, and remembered fondly*. Frustration is the enemy; drama is the product.

Design goals, in priority order:

1. **Legible** — both pilots always know *why* sync dropped, the instant it drops.
2. **Recoverable through play** — exit is earned by cooperative action, never by waiting.
3. **Dramatic** — failure escalates presentation (audio, HUD, kaiju behavior), not just numbers.
4. **Socially safe** — the game never points a finger at your partner. The duo is the unit.
5. **Spiral-proof** — no failure state makes further failure more likely without a counterweight.

## 1. Tier mapping

The built `SyncMeter` has five tiers with Overdrive at the top. This spec addresses the meter by **tier index**, not name, so it binds to the existing implementation without renaming anything. Proposed skin (adjust freely):

| Index | Working name | Band* | Role in this spec |
|---|---|---|---|
| T0 | **DESYNC** | 0–19 | The failure state. Everything in §3. |
| T1 | LINKED | 20–44 | Baseline. Floor for ambient losses (§5.2). |
| T2 | COHERENT | 45–69 | First buffs. |
| T3 | HARMONIZED | 70–94 | Combo unlocks. |
| T4 | OVERDRIVE | 95–100 | Ultimate window. Falling from here is special (§4.2). |

*Bands assumed — bind to the actual thresholds in `SyncMeter`'s config; this spec only requires "a bottom tier, a baseline tier, and a top tier."

## 2. Sync loss taxonomy

Every loss is an **event with a reason**, never a silent drain. No passive decay-over-time anywhere in this spec — losses are emitted by gameplay signals, consistent with the no-timer principle.

| Reason (enum) | Signal source | Magnitude* | Notes |
|---|---|---|---|
| `MissedResponse` | Call-and-response window expired (m0-23) | −8 | The bread-and-butter loss. |
| `CrossedInputs` | Navigator dodge/turn during gunner's channeled shot without a brace call | −4 | Teaches the call habit. |
| `UnshieldedCrit` | Mech takes a crit while shield was available but not raised | −10 | Navigator-side skill signal. |
| `PilotDowned` | A pilot incapacitated in-seat | −25 | Acute event; usually enters T0. |
| `SoloChain` | 3+ consecutive uncoordinated actions by one seat | −3 per, cap −9 | Anti-lone-wolf pressure, gentle. |
| `KaijuInterference` | Kaiju anti-sync attack (§6) | −6 to −15 by tier | The enemy attacks the *relationship*. |

*Provisional numbers — run the BALANCE SIM deck op before locking; expose all of them in a `SyncTuningSO` ScriptableObject (per data-driven principle).

**Legibility contract:** any loss ≥ 6 points fires a HUD reason toast + audio sting on **both** cockpit HUDs simultaneously. Wording is always about the *link*, never the person: "RESPONSE WINDOW LOST", never "GUNNER MISSED". (§7 rationale.)

## 3. The Desync state (T0)

### 3.1 Entering

Crossing into T0 fires `DesyncStarted(reason)`. One-time presentation hit (the "snap"): screen judder, a half-second of dead comms, then the failure soundscape (§8). This is the mech equivalent of a knockdown — loud, unmistakable, recoverable.

### 3.2 What desync does — and deliberately does not do

| System | In desync | Rationale |
|---|---|---|
| Navigator | No dodge-chain, no sprint; base movement intact | Weak, not helpless. Retreat is viable. |
| Gunner | Heavy weapons safety-locked; secondaries only | Can still contribute; can't carry. |
| Shared HUD | **Partner's readouts degrade to static** — your own stay clean | You lose *awareness of each other* first. Thematically perfect, mechanically forces voice comms. |
| Comms | Voice filter: partner sounds distant/degraded | Presentation only — never actually mute players. |
| Kaiju | Aggression weight up (per-kaiju modifier in its FSM data) | The monster smells blood. Pressure creates the cover-me moment. |
| Sync meter | **Loss events ignored while in T0** | Spiral-proofing. You cannot dig deeper than the bottom. |

**Rejected:** control-swap between pilots (chaos comedy, wrong tone, destroys role mastery), meter as shared health (double punishment), auto-recovery on a timer (violates the signal principle and removes agency).

### 3.3 Exiting — the Reconnection Ritual

The only exit. A short call-and-response sequence run through the same input verbs as normal play (reuses m0-23 mechanics — one system, two uses):

1. System deals a 3-step pattern, e.g. NAV brace → GUN vent → BOTH confirm (simultaneous input).
2. Each step is a **response window** — an explicit, HUD-visible player challenge (see §10 on why this doesn't violate the no-timer principle).
3. Completing the ritual → `DesyncEnded`, meter restored to the T1 floor, and an **Adrenaline Window**: the next 5 coordinated actions gain +50% sync. Recovery has momentum — the comeback arc is visible on the meter.
4. Missing a step does *not* punish — the pattern re-rolls with a new seed. Cost of failure is time under pressure, which the kaiju is already supplying.

During the ritual the mech is defensive-capable but weak. In squad content this creates the **spotlight rotation**: infantry screen the desynced mech, the ritual completes, the mech returns swinging. Ground players get their hero moment *because* the mech failed. This is the raid drama engine, for free.

## 4. Drama beats

### 4.1 Last Link (the near-miss)

First time per encounter the meter would cross into T0 *from T2 or higher in a single event*: instead it stops at the T1/T0 boundary, fires `LastLinkTriggered` — brief local slow-mo (client-side juice only, no simulation change), a partner callout VO line, and the next loss event is dampened 50%. One free save, once per encounter. The "we almost lost it" story, engineered.

### 4.2 Sync Snap (falling from Overdrive)

Desync triggered while in T4 (e.g., pilot downed mid-ultimate) is a **Sync Snap**: the collapsing link discharges — EMP burst staggers Class D/C kaiju in radius (spectacle as consolation), then a *4-step* ritual instead of 3. Overdrive greed becomes high-stakes drama, and even the worst moment produces a screenshot.

### 4.3 Solo Burden (partner down in-seat)

Downed pilot ≠ empty seat. The survivor holds a deteriorating link: **each solo action costs −2 sync** until the partner is revived (signal-per-action, not drain-per-second). Choice pressure: fight worse, or expose the mech to revive. In solo mode the `AICopilotGunner` never "dies" — it takes *damaged subroutines* (reduced ability set) so the burden mechanic has an analog without stranding solo players.

### 4.4 Sync Debt (the shaken recovery)

After `DesyncEnded`, gains are halved until 3 coordinated actions land ("shaken" HUD state). Prevents yo-yo back to Overdrive; makes the recovery arc a visible climb. Note Adrenaline (§3.3) overrides Debt for its 5 actions — net effect: strong start, then earn the rest.

## 5. Anti-frustration rules (hard constraints)

1. **No double punishment.** A loss source may cost sync *or* damage the mech, never both from one signal (flavor VFX exempt).
2. **Floor protection.** Ambient losses (`CrossedInputs`, `SoloChain`) cannot push below T1. Only acute events (`PilotDowned`, `UnshieldedCrit`, `KaijuInterference`) can enter T0.
3. **No stacking below bottom.** In T0, loss events are ignored; the ritual cannot be interrupted by sync loss — only by mech destruction.
4. **Blame masking.** Reason strings name the *event*, never the seat. Post-mission summary may show per-seat stats privately to each pilot only if they opt in. Protecting the duo's mood is a mechanic.
5. **Deterministic AI.** `AICopilotGunner` never fails a response window stochastically. Its failures are only ever caused by player action (e.g., navigator moved out of the AI's declared firing solution). Solo players must never feel robbed by dice.
6. **Duo-size honesty.** All magnitudes in §2 assume a 2-pilot mech; if difficulty scaling (m3-23) modifies them, it does so through `SyncTuningSO` variants, not hidden multipliers.

## 6. Kaiju as sync predators

Interference is **not universal**. Per the one-new-mechanic-per-tier rule, anti-sync attacks belong to *specific* kaiju as their tier mechanic — proposal: the Class B tier introduces it (working name: **Neural Howl** — a channeled scream that ticks `KaijuInterference` losses while either pilot faces the source; counterplay is the navigator breaking line-of-sight or the gunner interrupting via weak point). This gives the kaiju agency over the drift itself — the enemy attacks the relationship, not just the armor — and slots cleanly into the existing `KaijuController` FSM as an `Attacking`-state variant plus an `IWeakPoint` interrupt hook. Cross-reference: kaiju tier spec; open question q1 (Interrupted state vs sub-flag) decides the interrupt plumbing.

## 7. Social design rationale (why blame masking matters)

The sync system grades a *relationship*, and relationships are the retention engine of this game. A meter that says "your friend failed" teaches players to stop inviting friends. Every surface in this spec is therefore written duo-first: shared reason toasts, event-not-person wording, private-only per-seat stats. The failure fantasy is "our link broke under fire", never "you dragged me down". This is the difference between Pacific Rim and a ranked ladder.

## 8. Presentation hooks (for m2-09 HUD and audio identity)

- **Heartbeat** — the sync audio motif: one fused heartbeat at high tiers; splits into two off-tempo hearts as the meter falls; silence in the half-second after `DesyncStarted`, then both hearts hammering. Single `sync01` float parameter drives the whole layer.
- **HUD** — tier-indexed visual states; static shader on partner readouts scales with inverse sync; ritual widget renders the dealt pattern with per-step windows; reason toasts share one anchor (never stack more than two).
- **VO** — partner-callout table keyed by event: `LastLinkTriggered`, `DesyncStarted`, `RitualCompleted`, `SyncSnap`. Budget ~12 lines per pilot voice to start.

## 9. Architecture (maps to built systems — no redesigns)

- **`SyncMeter` (pure C#, unchanged core):** add `SyncLossReason` enum; events `DesyncStarted(reason)`, `DesyncEnded`, `LastLinkTriggered`, `SyncSnapTriggered`; T0 loss-ignore guard; Adrenaline/Debt gain modifiers as a small modifier stack. All magnitudes from `SyncTuningSO`.
- **New: `ResyncRitual` (pure C#, sibling to `RaidPhaseMachine` in style):** pattern generation (seeded), step validation from seat input signals, events `RitualStepCompleted`, `RitualStepMissed`, `RitualCompleted`. EditMode-testable, no MonoBehaviours.
- **`MechController`:** subscribes; applies the T0 control profile to `INavigator`/`IGunner` outputs; routes seat inputs to `ResyncRitual` while active.
- **`KaijuController`:** `DesyncStarted` → aggro weight modifier from kaiju data; Neural Howl as Class B `Attacking` variant emitting `KaijuInterference`.
- **EventBus / network (per ADR-001):** all loss computation host-side. Replication: `DesyncStarted/Ended`, `SyncSnapTriggered` reliable to all; ritual step inputs are client requests validated host-side; `LastLink` slow-mo is client-local presentation only (never scale the simulation clock). The network replicates outcomes; the EventBus distributes them locally.
- **Track boundary:** nothing here touches Track A. Save/load needs zero sync state (sync is per-encounter, never persisted).

## 10. On response windows vs the no-timer principle

The project principle bans *timer-driven logic* — hidden clocks that move the game state without player-perceivable cause. Response windows in the ritual (and in call-and-response generally) are **player-facing challenges**: visible, diegetic, and resolved by input. The state machine still transitions on signals (`RitualStepCompleted` / `RitualStepMissed`); the window is the challenge definition, not the driver. Flagging this explicitly so the principle stays enforceable in review.

## 11. Telemetry & playtest hypotheses (feeds m1-11 / m2-18)

| # | Hypothesis | Metric | Target |
|---|---|---|---|
| H1 | Desync happens, but not constantly | desyncs per mission | 1–3 |
| H2 | Ritual is tense but passable | first-attempt success | 70–85% |
| H3 | Failure feels self-caused | survey: "the drop was our fault, not the game's" | >70% agree |
| H4 | Infantry love the cover moment | highlight mentions in playtest notes | recurring |
| H5 | No spiral | avg time in T0 | <25s, flat across skill |

Log: loss-reason histogram, time-in-tier, ritual attempts/outcomes, Last Link and Snap counts.

## 12. Implementation order (three PRs, each testable)

1. **PR-1:** `SyncTuningSO` + `SyncLossReason` + new events + T0 guard + modifier stack. EditMode tests: tier transitions with reasons, floor rules, Adrenaline/Debt math.
2. **PR-2:** `ResyncRitual` machine + tests (pattern determinism per seed, step validation, re-roll on miss).
3. **PR-3:** `MechController` T0 profile + HUD/audio hooks + Kaiju aggro modifier. Playtest build.

## 13. Open questions (small, non-blocking)

1. Tier names/bands — bind §1 skin to the real `SyncMeter` thresholds.
2. Neural Howl on Class B — confirm against the kaiju tier spec's mechanic ladder (is B's slot free?).
3. Sync Snap EMP — intentional snapping for the stagger is possible; in pure co-op that's a legitimate play, but confirm we're comfortable with it before raids tune around it.
4. VO budget and voice casting timeline (affects §8 scope for the slice).

## 14. Acceptance criteria

- A duo can enter desync, complete the ritual, and hit Overdrive again inside one encounter, with every transition legible on both HUDs.
- No path exists where waiting (doing nothing) restores sync.
- All numbers live in `SyncTuningSO`; zero magic constants in code.
- `AICopilotGunner` sessions exercise every state in this spec, including Solo Burden's analog.
- EditMode tests cover: every loss reason, floor rules, T0 guard, ritual determinism, Adrenaline/Debt interaction.
