# Garrison reference fit and next layout pass — October 1, 2026

## Review decision

PS1 is accepted as the current disposable preview base for its ring-rendering improvement. This is not final garrison acceptance or live integration. Codex read the full PS1 result and refreshed the desktop conversation to its completed response; the older activity indicator was stale.

Codex reviewed the actual PIE far-moving frame board, near view and overhead comparison against the approved reference. The far ring is visibly more continuous and sufficiently readable for this preview; the near colour and width still agree. Retain the documented faintness, residual variation and chamfer tradeoff as limitations. Do not spend another pass tuning this ring or converting every straight marking now.

Raw lifecycle records agree: 97 expected changes (96 hidden components and one decal), zero missing/unexpected, all 3256 FF1 actors identical after revert, saved repeat is a no-op. The actual scripted PIE ring crossing reached, at constant capsule centre z475.2, and recorded errors/dirty maps are empty. Codex reviewed this existing evidence; this was not another manual playtest or engine run.

Independent review at 00:20:52 UTC: all 451 protected files match the pre-job170 snapshot; all 18 snapshots have identical hashes. The PS1 files match the reported receipt and final verification:

- Map: `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_PaintStability1.umap`, SHA256 `4AC426322A155FA802E365528E9F625E673EDDEE4DF322C3683AD04A7F63E6CC`.
- Material: `Content/_GarrisonPreview_Disposable/PaintStability1_Materials/M_PS1_PadRingDecal.uasset`, `4F6A2A1A942F4F9BCE7480C5A2012473F245A4546C4316D2E2ABE0E450355C30`.
- Receipt: `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_PaintStability1.json`, `FADED1920A1DE9B03C729BF94BF3071475C557BE941D3FC1FF5EBB9554519ED3`.
- Review evidence: `Saved/GarrisonRestructure/20261001-codex-paint-review/`.

The three save files differ from the earlier 21:50:30 review, with filesystem times 21:51–21:52, and already had their current hashes before job170. This confirms preservation throughout the recorded PS1 jobs; it does not identify who wrote them. Preserve the current saves, do not restore them or investigate unrelated gameplay sessions. Keep both old and current records so that history is not erased.

## Next bounded task: assess the whole composition and prepare one concrete layout pass

The user's goal is the coastal compound in the confirmed picture. We have spent several passes on local finish details; now assess the major shapes together before more small dressing. Do the spatial analysis and prepare a reviewable next implementation plan, with no saved level changes in this task.

Use the actual image directly:

`References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`

SHA256 `33491BF32E6AFEBE7BDB81A06083529A0F5F7F2C17619A6F8925B58939FA5A39`.

Use PS1's existing full-resolution captures, the current fingerprints and inventory, and the prior composition/forecourt records. The picture is oblique concept art, not a surveyed plan; do not convert pixels directly into metres.

1. Produce one labelled comparison board at comparable framing/orientation. Crop or annotate separate evidence images, never the map or game UI. Distinguish camera/perspective differences from real layout differences. Existing PS1 overhead-reference capture should be enough; take at most a small targeted read-only engine capture if a necessary view or measurement is missing.
2. Evaluate the reference's broad rear compound with low service buildings flanking the central apron; the straight central spine and neck; left tower/low operations block; front octagonal pad; right parallel pier and outside berth; and rocky wooded shore connection. The present overhead appears narrower and sparser at the rear than the reference, and the shoreline reads as a straight land/water boundary. Treat these as review observations to resolve with current bounds, not directions to guess transforms.
3. Rank at most three remaining high-impact differences. Clearly separate layout, art/asset limitations and the deliberately absent user-owned hangar. Do not count constructing that hangar as work for us. Do not declare the reference matched just because the deck topology and paint are now present.
4. Select ONE next substantive implementation pass from those findings. Give exact proposed actor/assembly identities, before/after bounds or transforms where possible, generated geometry, available assets, ownership, access/door/collision dependencies, protected anchors, and the minimum checks needed. Prepare a dry-run manifest or concise coordinate table and a diagram if useful. Prefer reusing appropriate existing assets and keeping the accepted spine/control/pad/pier relationships unless evidence demonstrates a necessary correction. Do not ask Connor to choose routine preview implementation details; Codex will review this concrete proposal and dispatch it.
5. Add a concise final gameplay-readiness checklist tied to actual existing evidence. Identify what still needs checking for spawn, the moved entrances, mission/deployment/return, land-gate access and water/drown recovery. Reuse the existing successful route/menu checks; do not rerun the full old matrix or fix unrelated BP_Mech/animation/kit problems. Record the PS1 decal's possible projection onto feet/vertical surfaces as a remaining visual check, not a new rendering rewrite.

## Boundaries

- Read-only level analysis in this task. No candidate save, live promotion, actor move, shared asset/material/config/lighting changes, new build or full test campaign. New analysis/report/plan/evidence files are allowed in clearly named task-owned paths.
- The actual rear hangar remains entirely Connor's. Keep its current provisional reservation (48.9m depth ×38.6m width), clear approach and ownership explicit. Do not silently resize it to match concept pixels. If a proposed surrounding change conflicts, show the conflict for Codex's review.
- Preserve all accepted menu/navigation/gameplay paths, unrelated project changes, existing live map and current saves. Do not delete previews or old evidence. Use an isolated UserDir for any necessary engine inspection, record its scope and stop only owned processes.
- Preserve the 451 current protected hashes plus PS1's map/material/receipt and evidence. Avoid blanket filesystem/repository audits. No Git, lock changes, commit/push, cleanup or messages to others.
- Keep this as one focused review packet. Do not extend it into an open-ended rendering/asset overhaul or a new implementation before Codex review.

Write `Docs/CLAUDE_GARRISON_REFERENCE_FIT_REVIEW_RESULT_2026-10-01.md`, update `Claude outputs/CLAUDE_STATUS.md`, provide a concise desktop result and stop. Include the one recommended next pass and exact evidence paths.
