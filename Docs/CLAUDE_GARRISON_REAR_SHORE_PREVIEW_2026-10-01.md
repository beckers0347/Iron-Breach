# RS1 rear shore preview — implementation handoff

October 1, 2026, 02:03 UTC. Codex reviewed the completed reference-fit result and authorizes this one bounded implementation pass within the user's garrison request.

## Review and decisions

Read `CLAUDE_GARRISON_REFERENCE_FIT_REVIEW_RESULT_2026-10-01.md`, particularly sections 5.2–5.7. Codex read the full result and desktop completion, inspected the comparison board and proposed plan, and independently verified all 456 protected records at 02:05 UTC with zero differences. The board, geometry, fit, plan and manifest hashes match the report. Evidence: `Saved/GarrisonRestructure/20261001-codex-referencefit-review/`.

The comparison supports attaching the rear to the mainland and wrapping the two rear corners with a rocky, wooded shore. The fitted distances are estimates from a concept image, not surveyed dimensions. RS1 will address this gap; it does not complete the service rows, art pass, overall depth match, or gameplay integration.

Proceed with the proposed RS1 plan, including the terrace, on a NEW disposable copy of PS1. The three decisions requested in the desktop response are resolved for this preview:

1. **Road:** retain the existing ramp, gate, gate side and all their behavior. Do not relocate the road to the concept's opposite side.
2. **Hangar:** retain Connor's provisional reservation exactly: x -500…4390, y 1819.4…5680.6; keep its 6 m side clearance and clear approach. This is not a final hangar-size decision. The terrace, shore pieces and vegetation must remain independently removable so Connor's later building can determine any trimming. Do not build or resize his hangar.
3. **Landing on shore:** the new reachable land below the rear walls is acceptable in this disposable preview if the actual pawn can recover through the existing ramp and gate and the new coastline still provides reliable drown recovery. Do not add invisible barriers, rails, or gameplay changes to force the old water behavior. A failed return or new coast recovery is a correction within RS1, using only RS1-owned geometry; report an unresolved gameplay dependency instead of changing shared code or water logic.

Burying the listed nine FF1 coping/fascia/paint pieces beneath the terrace is acceptable in this preview. Keep their bytes, actors and properties unchanged; the RS1 receipt must record this visual consequence. Do not retune the pad ring or straight-line rendering.

## Implementation

- Base: `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_PaintStability1`, SHA256 `4AC426322A155FA802E365528E9F625E673EDDEE4DF322C3683AD04A7F63E6CC`.
- Candidate: `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_RearShore1`.
- Use the exact approved reference already recorded in the work queue.
- Start from the reviewed `Saved/GarrisonRestructure/20261001-claude-referencefit/plan/rs1_plan.json` and manifest. Expected additions: 43 land slabs, 9 terrace slabs, 54 rocks, 74 canopy/trunk pairs = 254 actors; PS1 has 3257 existing actors.
- Use existing meshes and materials without editing their assets. No existing actor is moved, hidden, removed, retagged or changed. Preserve all doors, unknown Cubes, weapon rack, PlayerStart, directors/spawner, water, mainland actors, buildings, piers, vehicles, PS1 decal and earlier candidates.
- All additions need an exact receipt, unique RS1 ownership and reversible application. The shared `IB_GarrisonCB1` tag alone is NOT sufficient for revert selection; use exact recorded identities and the RS1-specific ownership tag. Stop on ambiguous ownership.
- Verify the regenerated plan against the copied candidate's actual fingerprint before mutation. Small changes to NEW RS1 pieces to resolve verified engine bounds, collision or visible coast gaps are authorized; document exact deviations and regenerate the manifest/counts. Do not move inherited anchors to make the plan fit.
- Use a new evidence folder `Saved/GarrisonRestructure/20261001-claude-rearshore/`; preserve the reference-fit packet and all earlier evidence. Keep an isolated UserDir for engine runs so live saves remain untouched.

## Focused verification and deliverables

Reuse the existing tooling; no new C++ build or unrelated full test campaign.

1. Verify a clean PS1 copy, saved apply/reload, saved repeat with no additional changes, exact revert, and final re-apply. Require every inherited actor identical and only the final documented RS1 additions. Preserve the base map, material and receipt.
2. Check actual engine bounds/collision of new pieces against the deck, gate, ramp, doors and reservation. In particular resolve the gate-corner plan overlap of Land_10/11 in 3D and the mountain-mesh bounds approximation. Inspect visible slab steps, water holes and exposed slab faces at the new coast; adjust only new geometry if necessary.
3. Use the actual infantry pawn for section 5.6's focused existing and new routes: ramp/gate, spawn-to-spine, reservation approach, Barracks/Armory approaches, terrace step, drop to new shore and return via gate, and one new coast drown recovery. Record settled spawn, actual movement and endpoint evidence; distinguish scripted PIE from manual play. Check three ramp capsule lanes and a real walk/jump attempt via rocks toward the deck/terrace to confirm the new pieces do not bypass the gate. Record relevant spawner activation during the new shore return without changing it.
4. Capture matched PS1/RS1 overheads, a reference-like framing, gate-road eye level, and terrace/shore eye level. Create one concise before/after board. Label diagram overlays and actual renders accurately. The existing PS1 comparison image is sufficient for the before view; do not rerun PS1 just for it.
5. Preserve and rehash the current 456 records from Codex's review, all PS1/reference-fit evidence, and live/shared assets. Keep the current three save-file bytes; no restoration or unrelated investigation. Report owned process exit state and any new errors separately from pre-existing errors.

Keep broader final-candidate readiness items on the checklist; do not run mission promotion/deployment or unrelated repairs in RS1. Correct one stale statement in the reference-fit checklist when reporting: the September 30 manager history records a mech restoration and newer crew checks, so a historical 'BP_Mech is missing' claim is not fresh evidence. Report only current observed missing references or compile errors if encountered, and leave their repair outside RS1.

Write `Docs/CLAUDE_GARRISON_REAR_SHORE_PREVIEW_RESULT_2026-10-01.md`, update your status, and give a concise desktop summary with exact candidate/receipt paths, changed counts, route outcomes, visual board, known limitations and next remaining composition gap. Then stop for Codex review.

No live-map promotion, shared asset/config/source writes, Git, lock manipulation, commit/push, cleanup, or messages to other people. No additional layout or service-building pass in this task.
