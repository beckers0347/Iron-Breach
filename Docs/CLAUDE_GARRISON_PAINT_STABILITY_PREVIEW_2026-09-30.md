# Garrison paint stability correction — September 30, 2026

## Review and bounded objective

Codex accepts FF1's forecourt circulation, quay treatment and muted amber colour as the next preview base. This is not final reference acceptance or live integration. Codex read the full FF1 result and raw final/reverted/repeat checks, reviewed overhead-reference, actual PIE cross-road and far-arc frame comparisons against the confirmed reference, and independently rehashed all 328 protected files: zero changes. FF1 map/material/receipt match the result. The 11 scripted pawn routes reached their targets; these are reviewed engine results, not a new manual playtest.

The unresolved defect is visible: the far pad-ring arc breaks into moving dashes at normal eye height. FF1 improves the near arc but worsens far coverage relative to YM1. Do a focused rendering correction in a NEW disposable candidate derived from FF1, retaining FF1 intact. Keep the accepted layout and colour. Implement and demonstrate a stable, thin-looking ring; do not request routine permission for a candidate-local rendering technique within this task.

## Exact scope

- Preserve the FF1 deck footprint/heights/collision, quay pieces, roads, all building/door/gameplay assemblies, PlayerStart, land gate, crane/trucks, helicopter and ship. Connor's rear hangar reservation stays fixed; the actual building is his.
- Correct only the generated helipad ring's rendering. Preserve its centre, nominal 18.9 m radius, 40 cm width, muted amber appearance, NoCollision and helicopter clearance. You may replace or suppress its 96 generated geometry segments inside the NEW candidate with a candidate-local marking representation, with exact ownership and reversible restoration. Do not leave both versions drawing over each other.
- First establish whether the far breakup is sampling, depth conflict, geometry/LOD, or a combination; the report's aliasing explanation is not yet a demonstrated cause. Use a small A/B at the same camera and actual gameplay settings. A decal or analytically filtered material is permitted if it solves the observed problem, but changing technique alone is not proof.
- Make any required material/mesh/texture assets inside the new candidate's own disposable subfolder. Do not modify FF1's MI, shared parents/materials, engine content, project rendering configuration, lighting, exposure or global anti-aliasing/screen percentage to mask the defect. Keep the reference orientation and existing camera settings for comparisons. No further colour tuning in this pass.
- Aim for a stable continuous arc where it is resolvable and a smooth, unobtrusive fade when genuinely subpixel, rather than crawling dots or an inflated/glowing stripe. Preserve a thin paint appearance near the player and a clean overhead ring. Avoid a thick raised curb as the workaround.
- Keep other paint and road geometry unchanged. Briefly report whether the successful approach could later address the straight-line shimmer; do not convert the whole garrison now.

## Focused verification and stopping point

Reuse existing tools and evidence. Do not rebuild the engine/game or repeat the 11/16-route matrix. One representative actual PIE walk across the corrected ring plus unchanged collision/gameplay actor verification is enough if only non-colliding visuals changed.

Capture a matched FF1/candidate overhead, a near-ring gameplay view, and a short actual PIE moving-camera sequence at normal player eye height showing the near and far arcs through roughly 25–45 m. Use the same resolution, field of view, graphics settings and path in both runs. Save the applied settings with the evidence. Existing FF1 editor frames may support comparison but are not an actual PIE temporal check. Supply a short clip if the capture tools support it, otherwise a dense ordered frame sequence; label it honestly. Judge frames at original resolution and include the previously failing far arc. Do not claim video/manual playtesting from scripted stills.

Use the existing receipt/fingerprint workflow for one successful save/reload, no-op repeat and reversible restore/reapply check of the new candidate. Verify only the declared ring representation/assets change, with no unexpected map/component/collision changes. Keep the evidence concise; do not create a new general validation framework or rerun established checks without a new failure.

Before and after, preserve the 328 paths in Saved/GarrisonRestructure/20260930-codex-forecourt-review/protected-current.json plus FF1 map/material/receipt below. Keep existing evidence unchanged and place new evidence in a separate folder. Do not clean up unrelated processes/files.

If a technique fails, use at most two well-grounded small alternatives, then report the best comparison and concrete remaining limitation rather than beginning an open-ended render rewrite. A saved improved candidate with an honest remaining limitation is preferable to unsupported acceptance claims.

## Base identity

- Content/_GarrisonPreview_Disposable/CarrowGateGarrison_ForecourtFinish1.umap: 181159BF9FB6A68598D7CFC297B71118FF3019F15B62ACD590E9E4EE3A08C1C3
- Content/_GarrisonPreview_Disposable/ForecourtFinish1_Materials/MI_FF1_DeckPaintAmber.uasset: 93A7971E1D152D075A52D72AC4604D788F65D67846243491E5923FAB0896F9CE
- Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ForecourtFinish1.json: F703F4A1B535D71FFF4DF13A48BCD94CF7036267440B115AC9E05B7CC326C12F
- FF1 result: Docs/CLAUDE_GARRISON_FORECOURT_FINISH_PREVIEW_RESULT_2026-09-30.md
- FF1 evidence: Saved/GarrisonRestructure/20260930-claude-forecourtfinish/
- Codex review: Saved/GarrisonRestructure/20260930-codex-forecourt-review/
- Confirmed reference: References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png

## Delivery

Write Docs/CLAUDE_GARRISON_PAINT_STABILITY_PREVIEW_RESULT_2026-09-30.md with the candidate/assets, exact changed ring representation, cause supported by evidence, before/after temporal comparison, reversible check, protected hashes and remaining limitations. Update your status and stop for Codex review. The overall garrison still needs final visual and functional assessment before live integration; this pass does not mark it complete.

No Git/locks/commit/push, live-map promotion, shared edits, unrelated animation/Blueprint/interior collision repairs, new environmental dressing or messages to anyone. The earlier step label about staging scripts did not establish a Git action; your result says none occurred. Continue that no-Git boundary explicitly.