# Garrison forecourt and paint finish preview

Codex handoff after the September 30, 2026, 19:48 UTC review. This is a bounded continuation of the authorized reference restructure. Proceed with the reversible preview without asking Connor to make routine paint/layout implementation choices.

## Accepted base and evidence

Use /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_YellowMarkings1 as the base of a NEW named disposable candidate. Preserve YM1, its own material and receipt, and all prior previews unchanged.

- YM1 map SHA256 AF25734AB4E78445A40A971D6F2B60DEAEE89A7A30683CAAB4A3BB6F26418855
- YM1 MI SHA256 B9E3E18F8DCDBB77B065A73B3F704727EB4420F4DBAF033FCE939E8ECEBF20C8
- YM1 receipt SHA256 C2A52B7698F5C0C701A431E3472929601CA00D39545010E66C73CD6D9900CEB1
- Codex review evidence: Saved/GarrisonRestructure/20260930-codex-yellow-review/

Codex read the complete YM1 result and current desktop completion. Raw final verification confirms91expectedmaterialslotchanges and0unexpected, with correct effective Base Color; editor and PIE readouts show91/91. Raw reverted verification has3131identicalactors. The representative scripted pier walk reached3/3waypoints in16seconds with constantcapsuleheight. Independently rehashed all224protectedfiles with0changes, and YM1map/MI/receipt match final hashes. Reviewed after overhead and actual PIE pad view, gameplay before/after board and the exact approved reference. The colour bug is fixed and accepted as the next preview base. This is not final reference acceptance or live integration.

## Why this pass

The large forecourt remains a mostly unmarked slab, while the supplied reference has a clear cross-road at the spine junction and connected service lanes around its buildings. The lower spine/control/pier/pad finish now stops abruptly at that forecourt. The new paint reads yellow but is more lemon than the reference's muted amber. At player eye height the pad ring reads as a faceted raised strip; bring that closer to painted deck markings without disturbing the helicopter or walkable deck.

Reference: References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png (1672x941, SHA33491BF32E6AFEBE7BDB81A06083529A0F5F7F2C17619A6F8925B58939FA5A39). Use this exact image directly.

## Implement in the new candidate

1. Finish the existing generated FORECOURT footprint: add restrained quay fascia/coping and inset edge paint to its exposed water perimeter, continuing the accepted lower-deck treatment. Do not close the land connection, pier entrance, spine entrance or any building approach with curbs. Use actual current world bounds, not the old actor pivot. Preserve deck footprint and collision, water gaps, heights and existing bridges/joins.
2. Lay out a readable painted cross-road along the seaward forecourt edge where the spine enters, continuing to the right-side pier entrance and left-side approaches. Connect it to the existing central axis and existing building approaches with only the service-lane paint needed for coherent circulation. Match the reference's restrained road/edge hierarchy. Keep the main spine and six-metre pier lane clear and aligned. Measure the resulting corridors and use existing verified routes as constraints. No random parking rows or extra props to fill empty space.
3. Keep the actual rear hangar building reserved for Connor. Preserve the P3 rear reservation and its current provisional dimensions/location and a clear central approach. Keep PlayerStart, all existing buildings/doors/assemblies, unknown held actors, road/gate connection, helicopter, ship, crane and trucks in their reviewed positions. Do not shift buildings or expand the platform to achieve a road layout. If a local paint route cannot fit, report that local constraint instead of moving protected assemblies.
4. Create a NEW candidate-owned paint instance, leaving the YM1 material unchanged. Bring its colour toward the reference's muted amber/gold and apply it only to this candidate's generated paint (existing91plusyournewpieces). Keep correct Base Color, non-emissive/matte behaviour. A visually sound comparison under comparable lighting is the acceptance criterion; do not spend a large pixel-matching project trying to reproduce an illustration under different lighting. Shared MI_Landmass assets, parent material and inherited live-map marking actors stay untouched.
5. Inspect the actual pad-ring paint thickness/height and joints. Refine only generated paint as needed so it reads as thin deck paint at player eye height rather than a raised polygon strip. Keep a small anti-z-fighting offset; all paint NoCollision. A smoother ring using64-96segments is reasonable if needed; keep the accepted radius, line width and helicopter clearance. Preserve actual deck geometry. Record any changed paint transforms/meshes/counts and original values for exact restoration. Do not repair helicopter pose, deck textures or lighting in this pass.

## Focused checks and handoff

- Use current source/receipt preflight, a new ownership manifest and reversible receipt for this additional finish. Reuse the existing working tools as far as practical; avoid a new broad framework or duplicating old test matrices.
- Verify saved/reloaded candidate content against YM1: only the authorized new forecourt finish pieces, candidate-local paint assignments/material and necessary generated-paint refinements may differ. Preserve all gameplay actors and their components. Verify repeat is a no-op and reversal restores the new pass's base state; never overwrite earlier receipts.
- Check the affected forecourt/spine/pier/land-gate joins and building approach clearances. Run only the few scripted PIE routes affected by the new forecourt finish, not the full prior16route/buildsuite. Report realpawn movement versus sweeps clearly. NoCollision paint-only changes do not require another full movement matrix.
- Supply a matched lit overhead-reference capture, one clear forecourt ground view, and actual PIE views showing the cross-road and pad paint. Observe pad joints during a short moving-camera sequence (several successive frames or brief video) to support any claim about flicker, not only identical-material reasoning. Keep lighting comparable; no saved lighting/postprocess changes.
- Rehash the224protectedfiles plus YM1map/material/receipt before/after. Keep the old baseline/source evidence and live saves untouched. Record final paths, hashes, exact differences, representative checks and known limitations in Docs/CLAUDE_GARRISON_FORECOURT_FINISH_PREVIEW_RESULT_2026-09-30.md; update your status. Include a short remaining-gap list against the reference, distinguishing the user's reserved hangar, existing asset appearance and any remaining functional verification. Stop for Codex review.

## Boundaries

No live-map promotion, shared material/mesh edits, Git/locks/commit/push, cleanup, unrelated animation/Blueprint/interior-collision repairs or messages to Shane/others. Preserve accepted menus/navigation and working spawn/deployment/return/interactions. The older GARRISON_PLAYTEST_PUNCHLIST contains unrelated texture/animation recommendations; it is background, not authorization to expand this finish task. Existing GameFeatureData/BP_Mech issues remain documented. Do not claim a clean whole-engine run because the scoped check succeeded.