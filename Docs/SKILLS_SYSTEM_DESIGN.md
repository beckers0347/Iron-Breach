# Skills system — accepted direction

Source: the user's **Research Saber Skills** conversation, reviewed September 12, 2026. The final choices override the earlier shopping-card layout and passive-tree proposals.

- Three classes: Saber (movement and pressure), Sentinel (positioning and engagement control), Guardian (defense into offense).
- Match the existing menu's player bar and top tabs, with a Skills tab. Show only the operative's class; no class-switching control.
- A holographic class silhouette and connected constellation of abilities and variants. Major abilities use larger nodes. Nodes show icons, with names and practical descriptions in a side panel on selection, hover or keyboard focus.
- Distinguish selected, equipped, unlocked and locked nodes. Illuminate unlocked connections.
- Signature, two tacticals and an overdrive form the equipped bar. Unlocking expands choices; it does not activate everything. One variant per equipped ability.
- Levels 1–50: one skill point per level after level 1, up to 49. Level 1 starts with a signature and two basic tacticals; overdrive, alternatives and variants are purchases. Exact prices and combat numbers are tuning choices, not finalized balance.
- Refunds are free at the Bastion. Conditional bonuses such as dodge-triggered reload buffs belong on equipped gear, not this tree. The earlier two-passive/keystone proposal is superseded by that choice.

Named examples from the accepted conversation:

| Class | Abilities |
| --- | --- |
| Saber | Vector Dash, Breach Charge, Kinetic Sweep; dash variants Clean Vector, Long Vector, Return Vector (return anchor) |
| Sentinel | Veil Shift (brief camouflage), targeting darts, decoys |
| Guardian | Timed guard, impact discharge, protective surge |

Keep saved operative identities and existing XP/inventory records intact. The current repository has the older Breaker/Picket/Bellringer enum values; their display-name migration must preserve serialized values. Gameplay effects must use authority checks and the existing damage pipeline, and equipped skill choices must persist per operative across map travel.

## Integration — September 13, 2026

The Skills tab is registered in the shared menu header. K opens it in game; K or Escape closes it. Hover/click an icon to inspect it, or use arrows/D-pad to navigate. Unlock and equip are separate actions. The four equipped slots appear above the constellation; the detail panel offers only compatible slots. Locked nodes use dashed rings and lock badges, equipped nodes a diamond, and selection an outer ring. The current operative's available body model supplies the cyan hologram; this does not add the proposed class outfit meshes.

| Slot | Key | Level-one loadout |
| --- | --- | --- |
| Signature | V | Saber: Vector Dash; Sentinel: Veil Shift; Guardian: Timed Guard |
| Tactical 1 | Q | Breach Charge / Targeting Dart / Impact Discharge |
| Tactical 2 | Z | Kinetic Sweep / Echo Decoy / Protective Surge |
| Overdrive | X | Initially empty; unlock an overdrive from level 8 |

Each class has five parent abilities and ten variants: **45 selectable nodes** total. The alternative tactical opens at level 7. Variant gates span levels 3–35. Names beyond the accepted examples, numerical combat values, unlock costs, and gates are initial tuning. A complete class catalog currently costs 40 of the possible 49 points; spare endgame points are not converted into automatic power or invented passives. Conditional gear bonuses remain outside this skill catalog.

### Compatibility and saved progression

- Serialized enum values and character IDs stay intact: Breaker displays as Guardian, Picket as Sentinel, Bellringer as Saber. The old unavailable Corpsman enum remains readable for compatibility but is removed from character creation.
- `UIBSkillComponent` lives on PlayerState, separate from the possessed pawn. The host validates class, ownership, parent prerequisites, level, balance and slot compatibility. Clients send an ID and slot, never a level or a point total.
- `IronBreach_Skills.sav` stores host-owned records under the same platform/operative key as XP and the vault. No existing XP, roster or vault format changes. Missing skill records receive a free starter kit. Save writes complete before a purchase/equip/refund becomes active; failed writes keep the previous state. Unreadable/newer save files are preserved.
- Save restoration discards invalid IDs, wrong-class unlocks, overspending and duplicate equipped roots. Valid tactical order and variants survive. Seamless travel copies the durable component state and key.
- Refunds require the actual Bastion world (`watch`, the command-deck destination). Opening the Watch overlay in a mission does not authorize a refund. Refund is free, takes two clicks, returns all spent points and restores the starter kit. Ordinary equipment changes preserve both slot and ability cooldowns on the current pawn.
- The skill catalog now supplies live kit specs. Old `KitData` assets and the Q/V Blueprint methods remain for compatibility; editing those legacy assets no longer retunes playable skills. Edit `Skills/IBSkillCatalog.cpp` for this catalog.

### Live behavior

- Saber: directional dashes, delayed frontal charges, circular shockwaves and surface tethers. Return Vector permits one return within three seconds, with a capsule sweep and occupied-destination check. Failed/expired return attempts do not reset recovery. Redline variants alter its pulse and defensive window.
- Sentinel: replicated concealment breaks ordinary infantry AI tracking; accepted gunfire or a damaging skill ends it. Kaiju and area attacks still threaten the player. Echoes copy the operative pose, take damage and attract visible ordinary enemies; kaiju targeting is unchanged. Sensors provide cyan HUD markers, including behind cover. Their slows survive AI speed updates and overlapping fields use the strongest slow. Disruption Echo emits its sensor field on expiry/destruction.
- Guardian: timed guard stores absorbed damage up to 100 energy. Impact consumes it once and adds it to damage. Friendly fields protect infantry, including the caster. Guard, personal defense and friendly ward windows use the strongest current protection instead of multiplying. Citadel also slows hostiles; Rescue Advance deploys a ward after its dash.
- Damage uses the existing damageable interface and collision/armor path, excluding infantry teammates and friendly echoes. Movement/effects and cooldown acceptance run on authority. Remote movement awaits the server; this pass does not add movement prediction. Four HUD chips expose recovery, guard energy, concealment and Return Vector's second activation.

### Verification and limits

`IronBreach.Skills.ProgressionAndSaves` is an Unreal automation test for catalog validity, starter kits, point caps, prerequisites, balance, ownership, slot validation, duplicate roots, damaged saves, tactical ordering, and save serialization with separate player records. It passed in `Saved/SkillsSystem/rules-1.log`; the exported report is in `Saved/SkillsSystem/automation`.

`IB.SkillsCheck` is an opt-in development check. Temporary actors away from the playable area exercise actual damage, guard energy, friendly wards, concealment/AI, decoys, sensor slows, cooldown swapping and safe/blocked/expired returns. It also opens Skills, inspects a locked overdrive and variant, exercises arrows, Escape and K, and checks portrait cleanup. It never changes the user's unlocks, XP or saved equipment. `-IBSkillsAfterMenus` runs it after `IB.MenuConsistencyCheck`.

Builds and local listen-host checks are recorded under `Saved/SkillsSystem`. Remote two-player skills, a packaged shipping build, gamepad ability bindings for all four slots, and final combat balance still need dedicated validation. This pass retains existing Q/V Enhanced Input hooks; Z/X have keyboard bindings. Existing fortress material warnings and the pawn's startup diagnostic for an unassigned default weapon visual are separate from the skill system.
