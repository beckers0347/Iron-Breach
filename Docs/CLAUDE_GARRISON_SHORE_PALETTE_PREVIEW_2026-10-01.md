# SP1 — natural coastal ground and rock palette

October 1, 2026 UTC. One bounded continuation of the authorized garrison restructure. Claude implements and checks a disposable preview, then stops for Codex review.

## Review decision and base

SR2 is accepted as the next disposable base. Codex read the complete result and desktop handoff, inspected the paired board and both original 1920x1080 close-up renders, and reviewed the raw final/restore/repeat and collision records. The numbers are removed from the two added shells; the original Armory retains its number. The short groove curl and faint chart-edge tone step are accepted as preview limitations. Leave that material alone in this task. This is not final art or packaged-build acceptance.

At 09:51:12 UTC Codex independently rehashed all 1,560 protected files from SR2's first stamp, including the two engine shapes: zero differences. SR2 map/materials/receipt/check/board match their reported hashes. Review evidence is `Saved/GarrisonRestructure/20261001-codex-serviceidentity-review/`. No new Codex engine run or manual playtest was performed for this material review.

Copy `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ServiceRows2` to `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette1`. Base map SHA256: `0267B9A353D1877D6DA6463798E6CF356976C183C0BF97812767EF3FF3713EC2`.

## Visual target

Open the approved picture directly: `References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`. Its coastal strip reads as weathered grey rock, darker crevices and mottled olive-green ground beneath the forest. In the current preview the shoreline rocks read very pale/icy and the broad ground surfaces read flat gold. Bring those surfaces closer to the reference while retaining readable rock detail and a natural transition between ground and shore. Use existing textures with useful detail; avoid a uniform flat tint or changing exposure to disguise the difference.

## Exact scope

- Only material-slot overrides on the RS1-owned natural terrain pieces may change. Eligible identities come from RS1's recorded receipt and `20261001-claude-rearshore/plan/rs1_engine_plan_r2.json`: roles land (43), coast (30, including the two wall bands), rock (54), and terrace (9), 136 eligible actors total. Confirm the actual identities/slots against the SR2 map before selecting any. A shared tag or label prefix alone is insufficient ownership.
- Change only the needed members of that set. All other actors and every actor/component transform, mesh, visibility, collision, tags and folder remain identical to SR2. Actor count stays 3,543. Trees/trunks, buildings, roads, painted markings, water, sea wall/deck outside the listed terrain pieces, pier, pad, ship, gameplay and lighting are fixed.
- New preview-local material assets are authorized only under `_GarrisonPreview_Disposable/ShorePalette1_Materials/`. Prefer instances of existing suitable materials; if necessary duplicate a master and adjust native nodes. Reference existing local textures read-only. Keep detail, roughness and normals credible and consistent in scale across the pieces. A shared world-space mapping may reduce texture discontinuities between slabs; it must not move surfaces.
- No displacement/world-position offset, opacity/collision changes, new geometry, moved rocks/trees, added foliage, texture painting or bitmap editing scripts, downloads, new gameplay, or global lighting/post-process changes. Material work cannot fix physical slab edges; record any such limitation honestly.
- Preserve SR2's map, two materials, receipt and evidence, all earlier previews, live/shared assets and current saves. The actual rear hangar remains Connor's; preserve its reservation, side bands and approach exactly. No live promotion, Git, cleanup, engine/project setting edits or unrelated fixes.

## Focused implementation and verification

Keep this smaller than the 35-process SR2 effort. Reuse the known material/lifecycle APIs; avoid broad source probes and redundant complete lifecycle runs.

1. Record a compact eligible-identity and expected-slot manifest. Inspect the current terrain materials and choose a coherent palette. Use a small in-memory look comparison if necessary; do not run an open-ended variation search.
2. Copy/apply/save/reload. Verify the only differences from SR2 are the explicitly recorded overrides on eligible terrain actors. All meshes/transforms/collision and unrelated actors must match. Check one saved repeat is a no-op and one exact override restore to the copied base, then restore the chosen final state. Reuse the existing identity guard; repeat negative cases only if its logic actually changes. Do not repeat the geometry/walking matrix for this non-displacing material pass.
3. One final paired render session with the same lighting/cameras before and after: overall overhead aligned to the reference comparison, left and right coast, rear terrace/land edge, gate approach, a ground-level rock close-up, and a view across adjoining land slabs. Compare grey-rock detail and mottled ground at foot level as well as overhead. Show the unchanged service shells/Armory in one context view. Keep source/diagnostic images separate from actual renders.
4. Hash the current 1,560 protected baseline and SR2 artifacts/evidence before and after, including all referenced material/texture sources and saves. Record material compile results, dirty package state, actual editor exit and all new writes. Keep UserDir isolation. Report any isolated autosaves accurately; do not claim autosave disabled unless verified. Do not rerun a successful session merely to get a different exit code.

Do not investigate SR1's unresolved exit-time crash or the existing unrelated Mech/foam/startup warnings. If the available materials cannot deliver a credible palette without changing geometry or creating textures, return the best bounded comparison and precise asset gap rather than expanding scope.

## Handoff

Write `Docs/CLAUDE_GARRISON_SHORE_PALETTE_PREVIEW_RESULT_2026-10-01.md`, evidence under `Saved/GarrisonRestructure/20261001-claude-shorepalette/`, and update your status. Include exact asset/receipt hashes, override diff, a compact paired board, preserved-file results, honest remaining limitations and the next largest reference mismatch. Finish with a concise desktop update and stop for review.
