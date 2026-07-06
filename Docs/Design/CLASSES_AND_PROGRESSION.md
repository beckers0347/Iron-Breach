# IRON BREACH — CLASSES, GRAFT LINES & THE REDLINE SYSTEM
*Progression design v1.0 · July 2026 · Companions: `PHASE1_ROADMAP.md`, `../Story/02_IRONBREACH_Narrative_Bible.md`*

---

## 1. DESIGN GOALS & TONE GUARDS

**Goals:** (1) 3–4 playable classes with distinct combat verbs; (2) an "element"-style build layer that creates Destiny-depth theorycrafting *without* Destiny's cosmic-magic vocabulary; (3) a Kaiju No. 8-inspired limiter/release fantasy adapted to our grounded tone; (4) a progression ladder where every level visibly buys power, options, or identity — a reason to log in that survives the campaign.

**Tone guards (contractual):**
- No magic. Every player power is **harvested technology** — reverse-engineered kaiju biology, militarized. Powers look like *equipment doing something slightly wrong*, never superheroics.
- Release states read as **controlled equipment failure** (plating that grows, suit-veins that glow, sound that drops out) — not golden auras. The camera stays at soldier height; the fantasy is *"I am brave enough to run my gear past spec,"* not "I am a god."
- Everything in this system is **diegetically load-bearing** (§6): using it deepens the story's mystery instead of sitting beside it.

---

## 2. THE FICTION: THE GRAFT PROGRAM

After VITYAZ (2035), the Breakwater's materials division did what Meridian did — harvested — but wove the tissue into infantry equipment: **graft-weave combat suits**. Three recovered kaiju biological systems proved stable enough to militarize; the service calls them **Graft Lines**. Every suit carries a **governor** — a hard limiter that keeps the graft dormant-adjacent. Since 2039, line troops have been quietly authorized to override it. Soldiers call it **running the redline**.

What nobody tells them (bible §IV.5, twist T2): graft tissue is never dead, mass is memory, and every override *sings*. The progression system is part of the transmission. (Seeded from launch — §6.)

---

## 3. THE FOUR CLASSES

*(Class = combat verb + kit + movement tool. Class is your role; Graft Line is your element; the two cross freely, Destiny-style — 4 classes × 3 lines = 12 base builds.)*

### 3.1 BREAKER — "hold the door" (vanguard)
- **Fantasy:** the wall between the shoal and the civilians. First through the breach, last off the line.
- **Kit ability:** *Breach Frame* — deployable man-high shield-frame (cover that walks with you when braced) **or** *Ram Charge* (shoulder-mounted concussive breach — opens armor seams on D/C-class limbs).
- **Movement:** *Bulwark Dash* — short armored lunge that can carry a downed ally (the carry verb, mechanized).
- **Squad role:** front anchor, seam-opener (kaiju armor-break synergy with the existing `ArmorHealth` C++ system).

### 3.2 PICKET — "see it first" (recon/skirmish)
- **Fantasy:** the forward sentry of the exclusion zones; the one who walks where the sensor grid doesn't.
- **Kit ability:** *Lamplight Flare* — thrown sensor spike: marks targets through terrain, reveals birthquake gestation glow, exposes weak points (crit windows) for the fireteam.
- **Movement:** *Line Bolt* — launchable cable runner (fast horizontal zip between anchor points; the exclusion-zone traversal tool).
- **Squad role:** intel, precision damage, secret-hunting (Pickets passively detect undercroft entrances and easter-egg resonances — the *explorer's class*).

### 3.3 BELLRINGER — "shape the field" (control/support)
- **Fantasy:** sonic-warfare corps; the ones who learned the enemy's grammar without knowing it.
- **Kit ability:** *Deterrent Pylon* — area denial: kaiju avoid/slow inside its cone (it sings "nothing here"); alt-spec *Standing Wave* — a corridor-shaped harmonic wall that **redirects** enemies along its face rather than blocking (deliberately not a bubble — no Well/Bubble clone).
- **Movement:** *Null Step* — brief acoustic-dampened glide (silent, no fall damage; synergizes with raid Quiet mechanics).
- **Squad role:** crowd control, kaiju behavior manipulation, the dungeon/raid utility king.

### 3.4 CORPSMAN — "bring them home" (sustain — ships in first major patch, §8)
- **Fantasy:** the extraction specialist; tide-marks made flesh. The class the Breakwater decorates.
- **Kit ability:** *Stim Line* — tethered field-dressing dart (burst heal + downed-ally auto-stabilize at range); alt-spec *Beacon Litter* — deployable extraction point that speeds revives and grants damage resist while carrying.
- **Movement:** *Surge Carry* — sprint that ignores carry penalties (bodies, objectives).
- **Squad role:** sustain, revive economy, rescue-scoring multiplier (public events count extractions — Corpsmen make them gold).

---

## 4. THE GRAFT LINES (the "element" layer — ours, not Destiny's)

Three harvested kaiju systems. Where Destiny's elements are cosmic damage colors, Graft Lines are **borrowed anatomy** — each answers "which part of the enemy are you wearing?" Each line has its own damage/status identity, ability suite per class, and Release form (§5).

### 4.1 OSSEIN — the plate (bone/armor system)
- **Identity:** force, mass, shatter. Status: **Staggered** (posture break — heavies flinch, D-class knockdown).
- **Texture:** graft-weave grows visible bone-lattice when active; abilities sound like ice cracking in reverse.
- **Sample abilities:** Breaker/Ossein — *Set the Wall* (brace: directional damage immunity, then release stored force as a shatter-cone). Picket/Ossein — *Splinter Round* (next shot fragments in armor seams). Bellringer/Ossein — pylon gains a physical rampart. Corpsman/Ossein — *Casket Guard* (bone-shell over a downed ally).

### 4.2 TOLL — the song (resonance/signal system)
- **Identity:** vibration, disruption, echo. Status: **Rung** (enemy accuracy/coordination broken; kaiju call/response interrupted — Rung kaiju can't summon or coordinate pack behavior).
- **Texture:** low bell-tones; the world's audio ducks when Toll abilities fire; nine-beat cadences hidden in the ability SFX (fingerprint, L27).
- **Sample abilities:** Breaker/Toll — *Bell Hammer* (melee shockwave that Rings a cone). Picket/Toll — *Echo Mark* (marked targets ping their pack-mates too). Bellringer/Toll — *Chord Lash* (chain disruption arc). Corpsman/Toll — *Heartbeat Sync* (squad regen metronome).

### 4.3 VEINLIGHT — the glow (artery/energy system)
- **Identity:** heat, speed, burn-over-time. Status: **Kindled** (artery-light burn; killing Kindled enemies chains ignition).
- **Texture:** suit veins glow gold-white under the weave; abilities leave brief glowing seam-lines in the world (the birthquake aesthetic, weaponized).
- **Sample abilities:** Breaker/Veinlight — *Floodline Dash* (dash leaves a burning seam wall). Picket/Veinlight — *Filament Shot* (piercing lance that Kindles everything along its line). Bellringer/Veinlight — pylon becomes a burn-zone emitter. Corpsman/Veinlight — *Cauter Stim* (heal that also Kindles attackers of the target).

**Build depth (endgame):** each line has 6 **Doctrines** (equip 2 — build-defining perks, e.g., Ossein: "Load-Bearing" — Staggered enemies take shatter damage from all sources) and 12 **Splices** (equip up to 4 — stat/behavior mods socketed by armor quality). Doctrines drop from activities; Splices from vendors/events. This is the Aspects/Fragments *function* with original economy and names — the theorycraft layer that makes leveling matter forever.

---

## 5. THE REDLINE SYSTEM (the Kaiju No. 8 conversation)

### 5.1 Verdict first: yes — build it. It's not too much; it's the missing piece.
The K8 "release percentage" fantasy solves three problems at once: it's our **super-equivalent** (without Destiny's charge-and-forget nuke), it's the **leveling carrot** you asked for (your ceiling % *is* visible character growth), and it's **on-theme** — the bible's whole sync system is already "power that costs you something hidden." Adapted correctly it will feel native to Iron Breach, not borrowed. The failure mode to avoid is only tonal: if Releases turn players into anime kaiju-hybrids, the grounded register dies. Our version stays a *suit* pushed past spec — never a transformation.

### 5.2 How it works
- Combat builds **Charge** (damage dealt/taken, extractions, ability use — support actions charge too).
- At will, pop the governor: **RELEASE** — 12–20 seconds in your Graft Line's full expression:
  - **Ossein Release — "RAMPART":** living plate juggernaut. Damage resist, melee rework, drawing aggro (kaiju *see the plate as kin* — they hesitate: 1-second stagger on activation. Lore in a mechanic, L23).
  - **Toll Release — "KNELL":** walking bell. Continuous Rung aura, ability spam, team reload/handling metronome; every footstep tolls.
  - **Veinlight Release — "SOLDER":** luminous skirmisher. Speed, chained Kindle on all hits, dash resets on ignition kills; you leave a burning seam-path.
- **The ceiling — your K8 percentage:** every character has a **Redline Rating** — the % of full graft output the governor safely allows. It starts at **9%** (of course it does) and grows with level, gear, and feats. Release strength/duration scales off it. The number is on your character sheet like a title: *"Redline 34%."* Players will chase it, compare it, and screenshot it.
- **Overcharge — the risk-reward:** you may *hold the trigger past your ceiling* — pushing Release beyond rating for escalating bonus output. Costs: post-Release **Exhaust** (ability cooldown penalty scaled by how far past you ran) and suit **Exposure** (§5.3). Redlining past ceiling in clutch moments = the game's highlight-reel verb. Skilled players manage the meter like heat; new players get a safe default.
- **Failure texture:** ending an overcharged Release drops you to a knee for a beat (animation), suit venting, audio ringing — power priced in vulnerability, per tone guards.

### 5.3 Exposure (the hidden cost that feeds the story)
A slow meter across a play session/week: heavy overcharging raises Exposure. Effects are **cosmetic and narrative only** (never a stat punishment — respect the player's time): at high Exposure your character's idle begins the **nine-tap** (§XIII.1's fingerprint — on YOUR character), suit veins glow faintly at rest, and certain NPCs comment ("You hear it yet? Don't answer."). Exposure decays with time or Ward-adjacent rest. When Year 2's "the port has no diode" twist lands, every player who mained overcharge realizes what their build was doing all along (T2, L12 — *the twist recontextualizes the player's own progression*). This is the cheapest, most Iron Breach feature in the whole system.

### 5.4 PVP normalization
In Wargames (sim-deck fiction): all Redline Ratings normalize to a flat sim value, Exposure disabled, Releases tuned as tactical (shorter, counterable — audible wind-up tell: the governor whine). No PVE grind advantage; the sim framing makes normalization diegetic.

---

## 6. WHY LEVELING FEELS GOOD — THE LADDER

**Levels 1–30 (campaign span, one unlock EVERY level — no dead levels):**
| Band | Unlocks |
|---|---|
| 1–5 | Class kit pieces (kit ability → movement tool → kit alt-spec) |
| 6–8 | **Graft attunement** (post-M6 fiction beat): choose first Graft Line; first line ability |
| 9–12 | Line ability 2; grenade-slot graft tool; **Redline unlocked at 12** (ceiling 9%) |
| 13–19 | +1% ceiling per level; first Doctrine slot; weapon specialization perks |
| 20–24 | Second Graft Line unlocked (swap freely out of combat); Splice slots 1–2 |
| 25–29 | Second Doctrine slot; Splice slots 3–4; kit master-mods |
| 30 | **Governor Certification** (fiction: Marrick's posthumous sign-off letter — a lore reward) — Overcharge unlocked; Clearance Rating begins |

**Post-30 (the forever game):** Clearance Rating (gear score) gates Directive Ops tiers and the raid; **ceiling % keeps growing** via feats, exotics, raid/dungeon triumphs (soft cap 49%, hard-capped below 51% in Phase 1 — the number 50+ is *reserved*, and the community will notice the wall and theorize correctly that something happens past it; that's Year 2 content: bible §XI's Concord Tier-2). Third Graft Line via zone questlines. Exotic gear that **rewrites your Release** (e.g., exotic gauntlets: Rampart taunts become a pull; exotic boots: Solder's path detonates on the ninth step) — the build-chase meta.

**Prestige identity:** tide-mark rings engraved on your own armor per 100 extractions (rescue prestige > kill prestige, Theme 5); Release VFX tints from raid ("foam-green Rampart" = Green Tomb clear); title strings from collectible ledgers.

---

## 7. DIFFERENTIATION AUDIT (so it never reads as a copy)
| | Destiny | Kaiju No. 8 | **IRON BREACH** |
|---|---|---|---|
| Power source | Cosmic magic (Light/Dark) | Innate kaiju hybridization | **Harvested enemy biology, worn as equipment** |
| "Elements" | Damage colors (Solar/Arc/Void…) | — | **Borrowed anatomy** (plate/song/glow) with behavioral statuses (Stagger/Rung/Kindle) |
| Super | Charge → nuke, no downside | Unleash %, hidden potential | **Redline: player-owned ceiling %, overcharge risk-reward, priced in Exhaust/Exposure** |
| Classes | Fantasy archetypes | Numbered suits | **Military trades** (Breaker/Picket/Bellringer/Corpsman) with deployable kits |
| Narrative link | Powers sit beside story | Suit = personal secret | **Progression IS the mystery** — using power feeds the transmission (T2) |

---

## 8. PHASE 1 SCOPE & BUILD ORDER (ties to `PHASE1_ROADMAP.md`)
- **Ship at 1.0:** 3 classes (Breaker, Picket, Bellringer) × 3 Graft Lines; Redline with ceiling to 30%+; Doctrines (4 of 6 per line) + Splices; PVP normalization. → build inside milestones **M2** (progression spine), **M5** (Release states ride frame-tech animation/VFX budget), tuning through **M8–M10**.
- **First major patch (with the post-raid season):** CORPSMAN class (marketing beat: "the Breakwater opens the medical corps"), remaining Doctrines, exotic-Release interactions wave 2.
- **Engineering notes:** statuses (Stagger/Rung/Kindle) implement on the existing damage-interface layer; Release = GAS-style state machine on BP_IBCharacter_Infantry; Exposure = profile-persistent float + cosmetic hooks; all abilities server-authoritative from day one (M1 netcode rules apply).

*The pitch in one line: in Destiny you wield the gods' magic; in Iron Breach you wear a piece of the thing you're fighting, and every time you push it past the line, somewhere under the ocean floor, something learns your name a little better.*
