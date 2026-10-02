# Garrison preview: yellow markings correction

Prepared by Codex, September 30, 2026, after the 18:03 UTC check. This is the next authorized, bounded preview task. Proceed without asking the user to choose a material strategy.

## Reviewed base

Codex reviewed your PF1 result, overhead-reference, actual PIE pier-lane-from-forecourt and editor pier-channel-quay captures, raw movement/diff/material-probe JSON, and independently rehashed all 116 protected paths. All are unchanged; PF1 candidate and receipt match your final hashes. Raw evidence records 16/16 scripted PIE routes reached, 15/15 clear capsule sweeps, no script errors/dirty map packages and zero unexpected actor differences. This is acceptance of the circulation/quay geometry as a base for the next preview, not final reference or live-map acceptance. No new build or duplicate route matrix was needed.

- Base: /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_PierFinish1
- Base map SHA256: C904EF8C6B35850BD9E6498A0C8B93ABFFAB758A2E756F6E1BACAA6675D75DA2
- Independent review: Saved/GarrisonRestructure/20260930-codex-pierfinish-review/review-summary.json
- Target image: References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png

## Implement the preview-local correction

1. Preserve PF1 and its receipt/evidence unchanged. Create a new clearly named disposable candidate from the final PF1 state, with provenance and a new correction receipt. Keep the already verified layout, crane/truck transforms, six-metre pier corridor, quay geometry and gameplay assemblies.
2. Create a new material instance inside a clearly named subfolder of Content/_GarrisonPreview_Disposable. Parent it to the existing M_FlatCol without editing the parent. Set the actual exposed vector parameter Base Color to the intended muted yellow (start from the existing intended 0.95,0.82,0.15). Do not set the nonexistent Color parameter. Preserve appropriate non-emissive, matte surface behaviour.
3. Assign this new instance ONLY to generated, candidate-owned yellow paint using explicit actor/component/material-slot identity. Include PF1 route/edge/door-approach markings and generated P3 pad ring, spine markings and rear-reservation paint where those were intended yellow. Do not globally replace every occurrence or recolour inherited live-map actors, buildings, decks, coping, fascia, shared materials or any prior preview. Record a complete assignment list and original values for reversal. Keep paint NoCollision.
4. Make the markings visibly read as yellow road/deck paint from overhead and player eye height, including the pad ring. If the existing 40 P3 coplanar overlaps cause flickering or dark intersections, correct only candidate-owned paint joins/overlaps or tiny paint surface offsets needed for stable rendering. Preserve route widths, platform silhouettes and clearances; avoid thick raised slabs, props or unrelated art changes. Document any paint-geometry differences. The current grey strips are visibly dark at eye height and do not yet satisfy the reference.

## Focused verification

- Verify the new instance's effective Base Color and actual material assignments after save/reload, not only the override list. Demonstrate yellow in lit editor and actual PIE player-camera captures. Use matching overhead-reference and pier-camera views plus a useful pad/control view for before/after comparison. Record image provenance and keep exposure/lighting comparable; do not repair lighting assets to mask the issue.
- Validate apply/repeat/revert/reapply of this correction with exact original assignment restoration and no unexpected actor changes. Include the new material package in ownership bookkeeping. Do not change existing layout receipts to falsely claim new material assignments are the unchanged old state.
- If collision/geometry stays unchanged, one representative scripted PIE pier walk with the player-camera capture is enough; do not rerun the entire lifecycle/movement/build suite. If you alter paint geometry, confirm all affected paint remains NoCollision and narrowly verify affected joins/visual stability.
- Rehash the existing 116 protected paths plus PF1 map and receipt before/after. Keep all earlier preview maps, receipts, shared assets, live map and live save files untouched. Report the precise files changed and hashes, final candidate/material paths, checks and limitations.

## Scope and stop point

The rear hangar building is reserved for Connor. Its existing provisional reservation remains; do not build the hangar or invent final dimensions. Preserve accepted menu/navigation and all working spawn/deployment/return/interactions. No Git operations, lock handling, commit/push, cleanup, messages to Shane/others, live-map promotion, shared MI_Landmass family edits, interior-collision/Blueprint repairs, helicopter/ship/unknown Cube changes, or unrelated environment work.

Record existing engine startup/Blueprint errors and any shutdown failure honestly. The two PF1 shutdown access violations occurred after saved evidence and remain unresolved; do not present a wholly clean engine run or expand into a crash investigation unless the new correction cannot be completed because of a reproducible failure.

Write the full result to Docs/CLAUDE_GARRISON_YELLOW_MARKINGS_PREVIEW_RESULT_2026-09-30.md, update your status, and provide the candidate plus matched screenshots for Codex review. Stop after that bounded result. Codex will review at the next scheduled check.