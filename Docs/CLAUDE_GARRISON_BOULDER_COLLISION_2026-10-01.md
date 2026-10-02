# Garrison: shoreline rock collision correction (BS2)

Issued October 1, 2026 UTC. Complete this one bounded correction, write the result, then stop for Codex review.

## Review and base

Codex read the full BS1 desktop completion and result, reviewed the comparison board and original PIE traversal frame 014, and checked the raw saved/restored/no-op records. At 17:06:18 UTC all 2,228 protected files, including four engine assets, matched independently. Six BS1 artifact hashes also match. Review records: `Saved/GarrisonRestructure/20261001-codex-bouldershore-review/`.

The broader, irregular coast is a useful visual base. It is NOT accepted for gameplay: all 61 coast rocks have NoCollision; your measurements report about 366 square metres of visible rock over walkable land and zero pawn/visibility hits in the sampled rock band. Traversal screenshots and your limitation section show the player/camera can enter these rocks. A successful route through visible rock is not a collision pass.

- Copy `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore1` to a new `/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore2`.
- BS1 map SHA256: `49154B4EB7959041EEE6752D25C6CC0CCF5B603D58BB63523442E57971A01599`.
- BS1 receipt SHA256: `8DB374D1DF5939BF825335D75515436F035CD34F90221D61CB65D6E67D5620EB`.
- Resolve the exact 35 edited and 26 added BS1 rock identities from `Saved/GarrisonRestructure/20261001-claude-bouldershore/run1/reapply2/ownership_manifest.json` and the receipt, not a loose shared tag.

## One correction

Give these visible rocks suitable pawn, camera and weapon-trace collision while retaining the BS1 visual arrangement and safe routes. Do not restore the oversized source tile convex hulls: BS1 already demonstrates their invisible walls and underwater floors.

1. Reuse your BS1 mesh analysis. Prove one representative large outcrop and one small stone before applying the method to all 61. Choose the smallest practical, accurate representation. You may duplicate ONLY the two used static meshes (`SM_Mountain_Plateu_01`, `SM_Mountain_05`) under a BS2-local asset folder and edit their collision, or add tightly fitted uniquely owned collision geometry/proxies under BS2. Source mesh render geometry, materials and source assets remain read-only. No plugin installation, downloads, new art assets, broad asset search or shared code changes.
2. Keep rock render geometry, materials and placements fixed initially. Collision must follow visible faces closely enough to prevent walking/camera entry and weapon shots passing through opaque rock, without coarse hulls filling visible gaps or causing invisible walls. Record simple/complex trace behavior and the actual existing weapon trace channel; do not equate Visibility alone with weapon validation. If the existing camera has no collision-avoidance mechanism, report that limitation specifically rather than rewriting the camera system.
3. Do not make submerged tile skirts into an artificial seabed or land bridge. Verify water recovery on real paths and collision beneath the waterline. Complex-as-simple is not automatically acceptable merely because it matches the entire tile. Show that the chosen solution fits this buried coastal use.
4. Preserve coast connectivity around rocks, all four drown/recovery inlets, gate/ramp access and the deck wall. A coast walk may follow a legitimate continuous path around a now-solid rock; record revised waypoints and actual pawn movement. Do not teleport, walk through rock or automatically resume after a stall and call it a pass. Only if a specific demonstrated blockage has no valid route, permit the minimum translation of the affected BS1 rock(s), recording before/after transforms and checking the silhouette/clearance. No general layout pass, hiding/removing the rock band or weakening collision to pass tests.
5. Do not spend this pass on pale underwater skirts, surf, sea colour, forest or lighting. They remain later visual tasks.

## Preserve

- All inherited actors/components outside the exact 61 rocks remain unchanged, including the other 19 RS1 inland rocks, all ground/coast/terrace geometry, trees, water, lighting, buildings, roads, doors, pads and gameplay volumes. Preserve accepted menu/navigation and working deployment/return paths.
- Reserve Connor's actual rear hangar at x=-500..4390, y=1819.4..5680.6, the 6 m side bands and straight approach x=4390..10182 at the same y. Do not build or obstruct it.
- Keep live map, earlier previews including BS1, all source/engine assets and current saves unchanged. Extend the current 2,228-file protection baseline with BS1 map/receipt/completed evidence and Codex review records; exclude transient isolated engine user directories. Keep existing unrelated changes.
- No live promotion, Git commit/push, shared asset/project setting edits, cleanup, unrelated errors/punch-list repair or gameplay-system rewrites.

## Focused evidence

Use the established safe disposable-map workflow, isolated UserDir, disabled autosaves and explicit saves. Reuse the existing harness and compare settled engine state consistently. Avoid repeating the full historical gameplay/art matrix or launching a large series of exploratory editor processes.

- Save/reload/apply/no-op/restore/reapply once with the BS2 receipt. Exact inherited actor/component state must match BS1 except the allowed rock collision/mesh references and any individually justified translations. Include component-relative transforms, new collider ownership and preview-local assets. No-op must not save or change the receipt; restore must reproduce BS1 with no BS2-owned actors. Report signed-zero normalization separately if needed. Use only focused ownership/tamper guards appropriate to the changed representation.
- Demonstrate representative real PIE pawn approaches into large and small rock faces stop outside them, plus camera behavior and weapon traces at the same visible surfaces. Include rays through adjacent genuine gaps/open water as negative controls. Inspect the entire 61-rock set for correct bindings/settings and sampled face/gap coverage; report collider/triangle counts and limitations.
- Repeat the four established drowning/recovery crossings, six deck-end jump attempts and both coast access walks. Check any route affected by added collision and one ramp/gate return. Preserve recovery and prevent a new wall/gate bypass. Other unaffected menu/building routes need not be repeated now.
- Capture a short actual PIE moving-camera sequence around the previously problematic traversal-stretch positions 014/019. Show approach, stopping at rock and movement around it, with coordinates/capsule information. Do not rely solely on static editor images or a route result boolean. Two matched BS1/BS2 shore overview images are sufficient to confirm unchanged appearance; a full new art board is unnecessary.
- Record final file hashes, before/after preservation check, dirty packages, autosave flags, process exits and observed errors. Keep existing BP_Mech/startup/exit issues accurately distinguished from new failures. Do not claim manual or packaged acceptance from scripted PIE alone.

## Handoff

Write `Docs/CLAUDE_GARRISON_BOULDER_COLLISION_RESULT_2026-10-01.md`, update your concise status, and place evidence under `Saved/GarrisonRestructure/20261001-claude-bouldercollision/`. Include the selected method, exact editable identities/assets, collision fidelity and route results, raw record/image paths, hashes, failed attempts and remaining limitations. If a credible solution cannot be achieved within this scope, stop with the small proof and concrete blocker rather than applying another knowingly nonfunctional coast. Then stop and wait for Codex review.
