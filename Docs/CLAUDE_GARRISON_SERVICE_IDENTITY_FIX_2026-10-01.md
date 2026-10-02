# SR2 — remove copied Armory numbers from the two service shells

October 1, 2026 UTC. One bounded correction to SR1. Claude implements and records focused visual evidence, then stops for Codex review.

## Review decision

Codex read the full SR1 result and completed desktop handoff, inspected the board and raw lifecycle/PIE records, and independently rehashed all 1,423 protected files at 07:06:56 UTC: all match. The map, receipt, plan, checks and board match the reported hashes. Evidence: `Saved/GarrisonRestructure/20261001-codex-servicerows-review/`.

The two-shell placement and clear routes are acceptable for continued disposable work. The repeated baked `03` is still visible from a useful walkway and the coast, so the identity requirement is not met. Resolve this on the two preview shells. Creating a preview-local material variant for this correction is authorized; no additional routine approval is needed. Keep the actual Armory's original number and assets unchanged.

## Exact scope

- Create `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ServiceRows2` from SR1 (`5C5ABD104B60BEB78CD65F7513771097A883A933687E10F29D8B344CBF8F5400`). Keep SR1 and its receipt/evidence intact.
- Only material overrides on `IBGC_SR1_Shell_RightBack` / `StaticMeshActor_1002` and `IBGC_SR1_Shell_RightFront` / `StaticMeshActor_1003` may change. Keep their mesh, transform, collision, visibility and all other actor/component state unchanged. All other 3,541 inherited actors remain identical, including the original functional Armory.
- Create new material assets only under a named ServiceRows2 subfolder of `_GarrisonPreview_Disposable`. Reference source textures read-only. Prefer an Unreal material-graph solution that masks/remaps only the number's UV area to compatible unmarked surface detail, preserving the building's original colour, wear, roughness and normals elsewhere. Check whether the number is encoded in more than base colour; avoid leaving a shiny or embossed ghost.
- No bitmap editing scripts, replacement building meshes, facade cover geometry, added signs/numbers, gameplay changes, actor moves, new rows, shore/palette work, or shared material/texture edits. This is a native material correction. If a clean local mask/remap is technically impossible, return the exact UV/channel evidence and a concrete minimal asset proposal; do not quietly replace the whole building with a flat material or call a visible patch finished.
- Preserve the exact hangar reservation, side bands, approach, roads, pad, pier, shore and every existing gameplay path. Continue isolated UserDir/save handling. No live promotion, Git, cleanup, or unrelated fixes.

## Focused verification only

Reuse the existing tool and receipts; do not repeat SR1's 19-process geometry/play matrix for a material-only correction.

1. Record exact expected overrides and new assets. Copy/apply/save/reload and verify: only the two intended material-slot changes; actor count still 3,543; all transforms, meshes and collision unchanged. Confirm a saved repeat is a no-op and the override can be restored exactly to SR1 without affecting another actor. Record exact identity ownership; the shared CB1 tag alone is never an edit selector.
2. Compile the new material and inspect it after reload in the engine. Take paired before/after close views of both number locations, the full affected face including roof/door detail, and the original functional Armory. Add rear-walkway, cross-road south-end and right-coast views under the same lighting as SR1, and one overall row view. Numbers must be absent on both shells; no visible rectangular patch, new seam or damaged nearby markings/details. Keep the source and final render evidence separate.
3. Hash the current 1,423-file baseline, SR1 candidate/receipt/evidence, the approved picture, current saves and every referenced mesh/material/texture before and after. Report all writes and new asset paths.
4. SR1 job 193 ended with 0xC0000005 after writing its results. Keep that as an unresolved exit-time limitation, not a clean exit. Record the actual new editor exit code and log ending for this visual check. Do not turn this task into unrelated crash debugging, and do not rerun successful visual tests solely to seek a different exit code.

Deliver `Docs/CLAUDE_GARRISON_SERVICE_IDENTITY_FIX_RESULT_2026-10-01.md`, evidence in a new `Saved/GarrisonRestructure/20261001-claude-serviceidentity/` folder, and update your own status. Include full candidate/material/receipt hashes, exact override diff, paired visual board, preservation results and any remaining limitation. Finish with a concise desktop handoff and stop.
