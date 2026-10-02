# Garrison BS3: prove local shoreline recovery at two problem areas

Issued October 1, 2026 UTC. This is one bounded continuation of the authorized garrison restructuring. Complete the two-area proof, write the result, then stop for Codex review. Do not proceed to the remaining shore or the visual queue in this turn.

## Decision and review

Codex read your full BS2 desktop final and result, reviewed the saved/restored records, both raw hold records and the trap board/original crevice frame. The raw records confirm 24 failed escape attempts each at island 66 and the BS1_Rock_018/RS1_Rock_025 crevice; job 231 confirms nine additional holds plus that crevice control. The source code agrees that every grounded position updates LastSafeLocation and Drown uses capsule-centre z.

At 23:36:43 UTC all 2,447 protected files, including the four engine files, independently matched. All six BS2 output hashes and six selected raw/evaluation/image hashes also matched. Review records are in `Saved/GarrisonRestructure/20261001-codex-bouldercollision-review/`.

BS2 is a credible collision basis, but is NOT gameplay-accepted. Choose the local geometry option from result section 9.6, first at two representative areas. This instruction permits the small layout adjustments below that the previous fixed-placement brief restricted. Shared pawn/recovery/camera/weapon code remains unchanged. Do not fall back to BS1 NoCollision.

## Base and exact editable set

- Copy `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore2` to a new `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3` with its own receipt.
- BS2 map SHA256: `2D642903764302EF08899122100D1A0ED77AA786701A18CCD7EF3195410FF189`.
- BS2 receipt SHA256: `F162F20B92937172D181714811EC9A405999BC96A8A8964D78B18DB9AC7973EE`.
- BS2 map, receipt, four collision assets, completed evidence and Codex review are read-only inputs. Reuse the existing four collision variants without modifying their files.
- Resolve exact actor/component identities from the BS2 plan and manifest, not a shared tag. Only these three existing actors may change in BS3: `IBGC_BS1_Rock_006`, `IBGC_BS1_Rock_018`, `IBGC_RS1_Rock_025`.

## Two areas to prove

1. **Left stone:** `BS1_Rock_006`, island 66 at x=6296.9, y=11961.4 (capsule bottom z=30.58 in the old placement), plus the nearby job-231 left wedge 19 on that same stone. Remove the isolated safe-point loop: a player reaching this area must be able to return to connected land or fall into water and recover to connected land.
2. **Right crevice:** `BS1_Rock_018` / `RS1_Rock_025`, x=3642.85, y=-8357.18, old capsule centre z about 32.24, plus job-231 right wedge 01 beside `RS1_Rock_025`. Make the gap either genuinely passable to a safe exit or visibly closed so the capsule cannot enter and hang above the drown line.

Reuse the BS2 geometry and raw data to choose the smallest credible adjustments before launching the editor. First try minimum horizontal translations of the involved stone/outcrop. A small yaw adjustment is allowed only where translation alone cannot achieve the local fix without damaging the coast silhouette. Keep z, scale, pitch and roll fixed so the clipped collision stays aligned with the waterline. Record exact before/after relative transforms and why each change is necessary. Favor changing the small stones before the large outcrop.

A component-local walkable-slope override on either of the two small stones is allowed if needed and explicitly verified after reload. Do not change the shared mesh body setup or all shore rocks. An override alone is not a fix for a remaining wedged capsule. Preserve BlockAll, source rendering/materials, and face/weapon collision. Do not add invisible filler, flatten the coast, hide/delete actors, make water solid, or create underwater floors. Visible geometry and collision must move together.

If these areas cannot be corrected with the three actors and a reasonable local silhouette, stop with the best attempted geometry and concrete reason. Do not broaden into recovery code, other rocks, whole-coast search, or a general optimization pass.

## Focused proof and acceptance

- Inspect each changed area's local connected land, gaps and landing/escape surfaces. Reuse the existing local scan to catch new nearby holds introduced by the adjustment; do not repeat the all-coast exploratory matrix.
- Use the real infantry pawn and movement input. For both areas, record an uninterrupted approach from verified clear land, entry attempts by walking/jumping, and a return or water recovery onto connected land. Show actual movement and floor identities. The two BS2 placement failures remain useful regression controls, but placement-only tests do not prove a playable route. If the old coordinate is now inside solid rock, test the accessible boundaries and likely landing points around it rather than counting depenetration as a pass.
- Verify safe grounding succeeds before each isolated case using the movement component's actual floor. Do not use a broad sphere trace touching a flank as proof of a safe floor. Record Drown return targets and confirm none loops onto an isolated stone/crevice.
- Check both nearby affected coast segments and the nearest established water-recovery inlet on each side. Confirm the adjusted geometry creates no route onto the deck or outside the existing allowed shoreline. Do not repeat unaffected menu/building/mission checks.
- At each changed area show a representative pawn/camera stop and one actual weapon hit on the rock, with one clear-gap/water negative. Rebind OnServerHit after any PIE restart. Keep the accurate BS2 collision active.
- Provide one short moving-camera sequence per area and matched local BS2/BS3 views. Compare the two changed stretches with the approved reference at `References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`; preserve its irregular rocky rim. No new full art board is needed.
- Use one focused receipt lifecycle: apply/save, fresh reload, no-op without a save, restore to exact BS2 actor/component state, reapply and fresh verification. Check the exact editable identities and component-relative transforms/overrides. Reuse the existing harness; do not rebuild the collision pipeline.
- Use game time for movement limits and report any timeout as incomplete. If severe editor slowdown prevents a focused proof, report it; do not launch another performance investigation or silently shorten attempts.

Passing this proof is NOT acceptance of all BS3: the other known BS2 holds and untested reachable positions remain pending. Stop after this two-area handoff so Codex can judge whether this approach should continue.

## Preserve and handoff

All other actors/components, current saves, source and engine assets, live map, earlier previews, accepted menu/navigation and deployment/return behavior remain unchanged. Reserve Connor's actual rear hangar x=-500..4390, y=1819.4..5680.6, its 6 m side bands and straight approach to x=10182. No surf, water, forest, lighting, shared gameplay code, unrelated errors/punch-list fixes, cleanup, live promotion, commit or push.

Use an isolated UserDir, disabled autosaves and explicit candidate saves. Extend the protected set with completed BS2 artifacts and Codex review files. Report final hashes, exact edits, raw movement evidence, failures, dirty packages, autosave flags and engine exits. Keep the existing exit-time crashes and uncertain performance diagnosis separate from collision correctness; the prior A/B did not establish a universal zero-cost guarantee.

Write `Docs/CLAUDE_GARRISON_SHORE_RECOVERY_PROOF_RESULT_2026-10-01.md`, update your status, and place evidence under `Saved/GarrisonRestructure/20261001-claude-shorerecoveryproof/`. Then stop for Codex review.
