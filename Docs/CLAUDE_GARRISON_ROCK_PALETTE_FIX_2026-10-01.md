# Garrison SP2 rock palette correction

October 1, 2026. One bounded follow-up to the completed SP1 pass. Claude owns implementation; Codex reviews. Stop after the result and status handoff.

## Review decision and base

Codex read the complete final desktop update and revised result, inspected the paired board and both original rock close-up renders, and checked the raw final/restored/repeat records and final GUI log. The olive ground and its world-aligned surface detail are accepted for continued disposable work. The rock palette is unfinished: the eroded family is much too dark, and the other two families remain brown/taupe under the current lighting.

At 11:50:14 UTC all 1,980 files in SP1's initial protected stamp match, including the four engine files. Candidate, seven materials, receipt, material manifest and check/board hashes agree with the report. Evidence: `Saved/GarrisonRestructure/20261001-codex-shorepalette-review/`. This was a focused evidence/visual review; no new Codex engine run or manual playtest.

- Base map: `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette1`, SHA256 `333A3A4463B0A1A1F4CD00C804637BE2F5CA2DB101FCB9AD6AEC648306B01C20`.
- SP1 receipt: `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ShorePalette1.json`, SHA256 `F6BA8E00CEBEEA1FC8732D64B3356FF4F08B8C40C3AA4BA47B75CFEA2E1C68D9`.
- Source of truth for eligible identities: SP1's recorded plan/receipt, cross-checked with RS1's recorded rock role. Exactly 54 rocks, 18 per mesh family. Shared tags alone never select actors.
- Reference: `References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png` (unchanged).

## Authorized change

Create `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette2` from SP1. Create three duplicate rock material instances under `/Game/_GarrisonPreview_Disposable/ShorePalette2_Materials/`, retaining SP1's existing rock parent and original texture assignments. Change only the new instances' rock colour parameters (gain, gamma, tint; desaturation only if needed) and slot 0 on the exact 54 recorded rocks to point to them. Keep normal strength and roughness unchanged.

Preserve SP1 and all seven SP1 material assets byte-for-byte. Leave both SP1 ground instances and both material graphs alone. All other 3,489 actors must remain identical to SP1, and the 54 rocks must differ only in the intended material reference. Actor count stays 3,543. Keep actor and component transforms, meshes, collision, visibility, tags and folders fixed. Keep trees, CityGround, background mountains, water, lighting/exposure, buildings, markings, pier, pad, ship and gameplay fixed. The actual rear hangar building, its reservation, side bands and approach remain for Connor.

Aim for readable weathered neutral-grey rock in both light and shade, with dark crevices and surface texture retained. Eliminate the crushed-dark eroded family without restoring snow-white tops to the other families. Your suggested eroded gain around 0.6 / gamma 1.0 and cooler tint around (0.96, 0.97, 1.0) are starting points, not pre-approved final numbers. Render the exact chosen setting before saving it. Judge individual rock surfaces; the reference's rock-plus-surf median and percentage are not a rock-only colour target.

Use one small comparison: SP1 plus at most two candidate parameter sets, including all three mesh families in a sunlit/partly shaded close view and an existing shaded-rim view. Reuse the existing graph, tools, camera data and ownership checks. Do not rebuild graphs, scan more material libraries, edit/generate textures, change geometry, add surf, recolour the sea, change foliage or start another task.

## Focused verification

- Record exact identity/slot and old/new parameter manifests, and the chosen rendered setting. Duplicate only the three instances and candidate map; existing assets stay read-only.
- Apply/save/reload and verify the expected 54 material-reference changes with zero other differences. Include component-relative transforms in this comparison if available; do not describe unmeasured fields as directly verified.
- One saved-state no-op check and one exact override restore to SP1, then return the candidate to the chosen final state. Reuse the established identity guard; run refusal checks only if its logic changes. Batch stages sensibly instead of launching a fresh process for every read. No geometry/walking regression matrix is needed for this material-only correction.
- One final paired session loading SP1 and SP2 from disk: all three rock families close, shaded rear/rim rocks, and the existing reference-aligned overhead or coast overview. Same cameras and lighting; the final values must be the values actually rendered. Keep a compact board and original renders, clearly separating the source reference from renders. Avoid a large new diagnostic packet.
- Hash the 1,980-file baseline plus SP1's map, receipt, seven materials and completed evidence (excluding its engine scratch directories). Keep the live map, current user saves and prior accepted previews unchanged. Record actual compile/dirty-package state, exits, and writes; isolated UserDir, verified autosave setting. Do not chase known unrelated startup ensures or the older exit crash.

## Deliver and stop

Result: `Docs/CLAUDE_GARRISON_ROCK_PALETTE_FIX_RESULT_2026-10-01.md`.

Evidence: `Saved/GarrisonRestructure/20261001-claude-rockpalette/`.

Give the map/instance/receipt hashes, exact parameter changes, focused verification and preservation results, compact paired board, and remaining visible limitations. Update `Claude outputs/CLAUDE_STATUS.md`, then stop for Codex. Do not promote live, commit, push or expand scope.

The separate shoreline-form mismatch (sparse pointed mountains versus a boulder band), surf, sea colour and forest canopy remain queued for later bounded work; do not implement them in SP2.
