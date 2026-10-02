# SR1 — service-row preview from the accepted rear-shore candidate

October 1, 2026 UTC. One bounded continuation of the authorized reference-based garrison restructure. Claude implements and records evidence; Codex reviews. Stop after the result is ready.

## Review and objective

Codex reviewed the full RS1 result, completed desktop reply, comparison board, raw final/reverted/no-op checks, and job 186 movement evidence. At 04:55 UTC all 1,251 protected files matched the pre-job-180 baseline; the final RS1 map, receipt, plan, movement evidence and board also matched the reported hashes. Review: `Saved/GarrisonRestructure/20261001-codex-rearshore-review/`.

RS1 is accepted as the base for the next disposable preview. This accepts the improved shore attachment and verified return paths. It does not mean the whole scene matches the picture or is ready for live promotion. White mountain-like rocks, gold ground, remaining rear depth and broader gameplay readiness are still open. No additional shore or paint tuning in this task.

Address the next composition gap: low service-building rows framing the apron, especially the empty image-right flank. Use the exact approved reference at `References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`, SHA256 `33491BF32E6AFEBE7BDB81A06083529A0F5F7F2C17619A6F8925B58939FA5A39`, and your reference-fit analysis. Indicative reference dimensions are not surveyed requirements. Access and the user's hangar reservation take priority.

## Concrete scope and decisions

1. Create one disposable `CarrowGateGarrison_ServiceRows1` candidate from `CarrowGateGarrison_RearShore1` (SHA256 `882F9D2060EC97916B919C6EA969D361D546FAAE49D8AA17C7510E45DD94A870`). Keep RS1 and its evidence intact.
2. This is an additions-only pass. Keep all 3,541 inherited actors and their component state identical. In particular, do not move or alter Barracks, Armory, Medical, Command, Mess Hall, their doors, the three Barracks Cubes, the weapon rack, gate, PlayerStart, or gameplay actors. Resolve their physical bounds and associations read-only as necessary to place around them; an uncertain association is a keep-out constraint, not permission to move it.
3. For this disposable layout study, **reuse of existing low military-building static meshes is authorized**. Add up to four low exterior service-block shells where they materially improve the two-flank composition. Choose the smallest useful set from measured space, rather than forcing a count. Do not clone gameplay Blueprints, interactions, signage or service identities; these additions are environment shells, and their non-interactive status belongs in the report. Existing functional services remain the functional services. Avoid copies that visibly promise a new working service or leave an open door leading into solid collision.
4. Prefer existing suitable low-building meshes, sensible orientation and uniform scaling with credible door/storey sizes. Inspect their actual materials, bounds and simple collision. Do not squash existing tall buildings to counterfeit low blocks. If the available kit cannot yield a credible, safely accessible addition, stop with the measured proposed plan and the specific asset need rather than manufacturing a poor candidate. No imported/downloaded assets, purchases, shared-mesh/material edits or new gameplay systems.
5. Plan first within this task, then implement the safe plan without waiting for another routine approval. Document selected meshes, exact actor/component identities, transforms, actual bounds, setbacks, collision, approach routes, and a small before/proposed plan. The approximate reference has seven low block fronts across both flanks and a roughly 28 m central apron; the original three service buildings stay fixed in this pass, so document the remaining mismatch honestly.

## Fixed layout constraints

- Connor's actual rear hangar is reserved for him. Keep the existing provisional reserve x -500..4390, y 1819.4..5680.6, its 6 m side clearance and straight approach from x 4390..10182 unchanged. Do not resize it to the pictured hangar, place a substitute, or fill that approach with service buildings.
- Keep the gate and road on their current side. Keep the full accepted gate-road corridor, the 8 m forecourt crossroad, central access axis and all existing usable approach widths. Protect the entire walking corridor, not just painted line bounds. A building cannot cover a road simply because its mesh avoids the paint.
- The nominal empty right flank is x 4646..10182, y -2500..1819, but the gate road and crossroad reduce its buildable area. Derive exact keep-outs from the candidate and accepted plans. Keep clear circulation around new shells and between all existing entrances, the rack, quay, pier and spine.
- Keep the command platform, pier, ship, helicopter, pad/ring, shores, terrace, trees, rocks and existing world/gameplay state unchanged. Do not extend the deck, relocate roads, add invisible barriers or alter water recovery to make room.
- Existing decorative paint may be visually covered only in a non-route area by a justified new footprint; list every such overlap. No inherited paint edits or hidden blockers.

## Ownership and focused verification

Use SR1-specific labels, folder and ownership tag plus a receipt of exact object identity/class/mesh. The inherited shared CB1 tag is never a deletion selector. Reuse the established candidate tooling. Keep a complete final plan/manifest for any new pieces; changes during engine fitting must be limited to those pieces and documented.

Do only the checks needed for these additions:

- Base-copy identity, apply/save/reload, a saved repeat no-op, exact SR1-only revert, and final reapply/reload. Final diff: all 3,541 inherited actors identical, only the recorded new actors present. Verify ownership refusal on a conflicting identity without saving; reuse established broader negative-case evidence unless code changes require more.
- Real engine bounds and capsule clearance for every new footprint against the hangar bands, roads, existing buildings/doors/rack, deck edges and each other. Check accessible gaps, corners and the new shells' collision; do not equate BlockAll with usable simple collision.
- Focused real-infantry PIE: settled spawn to spine, reservation mouth to spine, city road through ramp/gate and along the road to the crossroad, and affected existing service-door approaches. Include a walk past each new row and through its narrowest intended passage. No navigation teleport between waypoints; report any setup teleport separately. Reuse RS1 shore/drop evidence if those areas are physically unaffected.
- If new placement is near the weapon rack, record approach and its existing interaction, without modifying the rack. Do not broaden into unrelated mission or character fixes.
- Capture the same overhead/reference-fit views as RS1, one readable plan, and eye-level views along both sides of the apron and the gate-road corridor. Compare directly with the approved picture and RS1. Keep screenshots and measured game evidence distinct from diagrams and assumptions.

Use isolated UserDir/save handling. Preserve the 1,251-file current baseline in Codex's review, all RS1 outputs/reference-fit evidence, all previous accepted previews, live map and current saves. Capture fresh before/after hashes for referenced assets and the candidate's base. No shared writes, live promotion, Git operations, cleanup, or changes to unrelated known BP_Mech/character issues. Reuse current engine helpers; no full build or broad test matrix unless this exact change requires it.

## Deliverable

Write `Docs/CLAUDE_GARRISON_SERVICE_ROWS_PREVIEW_RESULT_2026-10-01.md` and update your own status. Store task evidence under a new `Saved/GarrisonRestructure/20261001-claude-servicerows/` directory. Provide candidate/receipt hashes, final manifest, before/after board, raw focused checks, preservation results, exact differences, and remaining reference/readiness gaps. If no credible safe shell fits, provide the concrete measured rejection and proposed placement/asset dimensions; do not repeat a generic request for permission to duplicate assets or move unknown actors.

Finish with a concise desktop handoff and stop for Codex review.
