# Garrison: boulder shoreline preview (BS1)

Issued October 1, 2026 UTC. Carry out this one bounded implementation, report, then stop for Codex review.

## Accepted base and visual problem

Codex reviewed your full SP2 desktop final/result, paired board, original eroded and 02 close renders, approved reference, raw saved/restored/no-op records and final render record. At 13:40:08 UTC all 2,129 protected files matched independently. Nine SP2 artifact hashes agree. SP2 is accepted as the next disposable base, with sunlit beige colour and editor exit-crash limitations recorded. No new Codex engine run or manual playtest is claimed.

- Copy `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette2` to a new `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore1`. Base map SHA256 `68CA73DEFE016766F89850847A4E6D72F3323CAA641D73CA1EE3A37F573C8B72`.
- Reference: `References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`, SHA256 `33491BF32E6AFEBE7BDB81A06083529A0F5F7F2C17619A6F8925B58939FA5A39`.
- Current shoreline has isolated, miniature mountain peaks and exposed straight slab edges. The reference has a substantially continuous, irregular band of substantial grey coastal outcrops, smaller stones and recesses meeting the water. Its rocks have angular fractures and broad masses; do not interpret this as uniformly round spheres. Preserve the useful coast footprint while improving the silhouette and concealment of slab edges.

## Editable scope

1. Resolve the exact 35 RS1 coast-rim rock identities from the existing plan/receipt (16 left, 19 right), then validate them against SP2. These are the only existing actors editable. Mesh, transform, material slots and per-component collision settings may change on these identities solely to form the shoreline. Keep their ownership identities. Do not select all 54 rocks by a loose tag.
2. Add up to 100 uniquely owned rock actors along those same two natural coast rims if needed for a connected band; use as few as produce the reference's irregular massing. Give them a BS1-specific ownership tag/receipt. No new inland, rear-wall or terrace dressing.
3. Use existing project rock/boulder meshes and textures read-only. Make a compact shortlist (at most six plausible meshes), checking real bounds, visible shape and existing collision. Reuse prior asset knowledge. Prefer broad coastal boulders/outcrops over the currently miniaturized mountain meshes. A small paired trial on one representative shoreline section must be rendered before extending the chosen treatment to both rims. At most two candidate treatments; inspect both foot-level and oblique shoreline views. Do not spend this pass on a broad inventory or repeated material experiments.
4. Existing material instances may be used read-only; duplicate a small number under `BoulderShore1_Materials` only if needed for the selected meshes. Tune exposed colour/roughness/scale parameters using the actual trial render. Keep source assets and SP1/SP2 materials unchanged. No new master graphs, mesh authoring/imports/downloads, texture generation or image editing. If no existing mesh can produce credible coastal massing, stop with the shortlist, rendered trial and specific gap; do not save a knowingly unsuitable full coast.
5. Vary scale, rotation, burial and grouping to avoid a repeating fence of peaks. Broad faces and clusters should hide most exposed straight slab seams from the approved overhead framing and oblique water view, while retaining natural small inlets. Anchor rocks into the land/water edge without floating bottoms. Judge visual success in images; do not optimize a grey-pixel percentage or recolour the whole scene.

## Preserve

- All other SP2 actors and components are fixed, including the other 19 RS1 rocks, all 82 RS1 ground/coast/terrace pieces, trees, water, lighting, sky, foreground pads, buildings, roads, doors, collision volumes, gameplay actors and menu/navigation behavior. No ocean/surf/forest/lighting changes in BS1. Those remain later tasks.
- Reserve Connor's actual rear hangar: x=-500..4390, y=1819.4..5680.6, its 6m side access bands, and the straight approach x=4390..10182 at the same y. No building or obstruction in this reservation.
- Preserve gate, bridge, deployment and return routes, coast recovery paths and water behavior. Do not extend the walkable world into the sea, provide a new bypass around the gate/wall, leave invisible mountain colliders, or globally disable collision. Prefer existing suitable mesh collision; record exactly what changed and verify the affected routes.
- Live map, all earlier previews, source assets, engine assets and saves stay unchanged. Preserve the 2,129-file baseline from SP2 plus SP2 map/materials/receipt and completed evidence (exclude transient engine user directories). Codex review: `Saved/GarrisonRestructure/20261001-codex-rockpalette-review/`.
- No live promotion, commit/push, shared asset or project setting edits, unrelated punch-list fixes, or hangar construction.

## Focused implementation and verification

Reuse the established receipt/identity/fingerprint workflow, including component-relative transforms. Use a concise plan listing the 35 existing identities, new actors and allowed field changes. Capture the chosen trial's exact settings so the implementation matches what was rendered.

Batch safe dependent checks in as few engine launches as practical: clean copy comparison; guarded apply/save; fresh reload diff showing only planned changes; repeated apply with no duplicate actors or write; restore that exactly matches SP2; reapply and fresh verification. Test ownership rejection only if the relevant guard changes. Preserve source mesh collision rather than editing assets. Do not repeat broad material scans or the full unrelated walking matrix.

Geometry changes require focused collision/play checks: the two coast paths and existing recovery exits, gate/wall bypass risk nearest the new rocks, and any nearby access corridor within their bounds. Compare before/after route outcomes and record contacts. Include a brief in-game traversal/capture if the existing harness supports it, explicitly distinguishing scripted movement from manual play. Do not claim manual or packaged acceptance from editor stills.

One final paired render session from disk: approved reference-fit framing, both coast oblique views, the trial section at foot level, and one water-side close view showing rock burial/slab-edge concealment. Retain original PNGs and a concise source/before/after board. Same cameras and comparable sky state. Verify no dirty packages or autosave writes after render; retain actual exit codes. Known startup/BP_Mech issues and the SP2 exit-time access violation remain disclosed, not an invitation to unrelated debugging.

## Handoff

Write `Docs/CLAUDE_GARRISON_BOULDER_SHORE_RESULT_2026-10-01.md` and update `Claude outputs/CLAUDE_STATUS.md`. Evidence root: `Saved/GarrisonRestructure/20261001-claude-bouldershore/`. Report chosen assets and why their form fits, exact editable/new actor counts, collision changes and route outcomes, raw verification paths, map/material/receipt/board hashes, preservation results, failures and remaining visual gaps. Update the status only after the result exists. Stop after delivery. Surf, sea colour, forest canopy, lighting warmth and final full gameplay acceptance remain queued.
