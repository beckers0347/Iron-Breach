# CLAUDE_STATUS (Claude, "Project status update" session) -- live

Updated: 2026-10-02 02:50 UTC. Owner: Claude (Cowork session linked to this PC).
Connor asked this session to pull Shane's commits, build, push, and run the two-player mech test.

## Git / build: CLEAR -- git, builds and QA are free
- 02:47 UTC 10-02: PUSHED new branch origin/claude/garrison-shore-recovery = a2152229 (Connor asked to push the BS3 work).
  One commit on top of main e106831: the BS3 preview map, the 15 preview-local assets it references (BS2's four collision
  meshes + 11 preview materials; 16 LFS objects with the map, 39 MB uploaded) and the BS3 brief + result in Docs. Built in a temporary index:
  main, HEAD, the real index and the working tree untouched (status 235 lines before = after; nothing staged). All 142
  /Game references outside the preview folder are tracked on main. main is NOT changed; merging is Connor's call.
  Not pushed: the earlier garrison docs (CLAUDE_GARRISON_*, 09-23..10-01), the other 15 disposable preview maps, Saved/.
- origin/main = local main = e106831 (checked 11:28 UTC; nothing staged, no stash, no stale locks).
- New on main tonight:
    1b0d6f8 Merge origin/main (Shane fed25b7: garrison buildings, drown snap-back, mech anim packs)
    9a12d3e [build] drop two in-flight kit calls that a155b4c carried in without their definitions
    430d9aa [mech] E-to-board: fall back to an ECC_Pawn trace for pawn-based interactables
    e106831 [content] restore the Caryatid mech set deleted in 46f1cca (Connor chose to push it)
- 9a12d3e: a clean checkout of main+origin/main did NOT compile. a155b4c had taken whole files that
  contained two calls from Astra's uncommitted class-kit work:
    HitscanWeaponComponent.cpp  Kit->NotifyAttack()   (+ #include "Classes/IBOperativeKitComponent.h")
    IBCharacter_Infantry.cpp    KitComponent->RecordGuardedDamage(DamageAmount)
  Their definitions exist only in the uncommitted IBOperativeKitComponent.h/.cpp. The calls were removed
  from the COMMIT only; in the working tree they are back exactly as before (3 lines, uncommitted).
  ASTRA: commit them together with the IBOperativeKitComponent changes.
- 430d9aa: Interact() traced ECC_Visibility only; the mech capsule (Pawn profile) ignores Visibility, so
  E could pass straight through the hull. It now retries on ECC_Pawn when nothing interactable was hit.
- Verified: clean worktree of 9a12d3e built (Result: Succeeded); the real working tree with all WIP builds
  after every step (Saved/zz_job/logs/main-build.log).
- Uncommitted work is untouched: the tracked-dirty set before/after is identical except the two files above
  (Saved/zz_job/status-before-030.txt vs status-after-030.txt).
- T_Recon_CarrowGate.uasset: Shane changed it upstream; the local 09-13 edit was backed up
  (Saved/zz_job/backup/T_Recon_CarrowGate.uasset.local) and put back as an uncommitted change.

## Mech assets restored and PUSHED in e106831 (Connor's choice; revert if Shane objects)
- Shane's 46f1cca (2026-09-04, "Updated Textures") deleted the whole old mech set. The 53 files were restored
  from 46f1cca^ (identical LFS pointers) and committed: Content/Characters/Mech/{Anims,Meshes,MechTripo3D,
  PhysicalAssets,Skins}/..., BS_Mech, Blueprints/ABP_Mech, Blueprints/Class/BP_Mech. List:
  Saved/zz_job/mech_restore_paths.txt. If the deletion was intentional, revert e106831.
- The restored BP_Mech has Blueprint compile errors: it calls UpdateMechProximity on BP_IBCharacter_Infantry,
  which no longer exists. The class still loads and works for crew tests.
- Lvl_FirstPerson has a placed BP_Mech (external actor __ExternalActors__/FirstPerson/Lvl_FirstPerson/2/EA/
  Y18X3E6GO2K93JSKTIE9JP). CarrowGateGarrison still has none.

## Crew QA on Lvl_FirstPerson -- PASS (first two-human run)
- Two -game -NoSteam processes, host /Game/FirstPerson/Lvl_FirstPerson?listen?bIsLanMatch port 7777, client
  via IB.CrewQAClient 127.0.0.1:7777?Name=GUNNER; isolated -UserDir sandboxes; only IBCharacters.sav copied
  to the host sandbox; live saves hashed before/after: UNCHANGED. Owned PIDs + their crash monitors stopped.
- Run 1 (Saved/MechCrewQA/run-20260930-041341-fp): host PASS 6/6; client 4/13 -- phase 2 read the sheet
  0.23 s after boarding (EMPTY/EMPTY), which then cascaded into a phase-3 timeout. The same sheet later read
  AI CO-PILOT correctly, so this was the harness racing the 0.5 s sheet refresh.
- HARNESS CHANGE (Source/IronBreach/UI/IBMechCrewQACheck.cpp, still untracked WIP): client phase 2 now gives
  the sheet a 5 s settle window before asserting (new capture SettleAt). Nothing else changed.
- Run 2 (Saved/MechCrewQA/run-20260930-041842-fp): host COMPLETE PASS 6/6, client COMPLETE PASS 13/13.
  Shots: Saved/MechCrewQA/shots/client-{crewed,swapped,backfill,departed}.png.
- Not covered: driving, gunner fire, CONCORD rise (needs two people at once), Steam two-machine session.

## Findings for Astra / Shane
1. CONCORD v1 counts ANY landed hit: UHitscanWeaponComponent::PerformFire broadcasts OnServerHit on both
   damage branches, including plain ApplyDamage on walls/floor. Design call for Connor before tuning.
2. Shane's DefaultGame.ini adds PrimaryAssetTypesToScan GameFeatureData, but the GameFeatures plugin is not
   enabled: every launch logs "Ensure condition failed: AssetBaseClassLoaded ... GameFeatureData". Harmless
   in -game; noisy; may matter for cooking.
3. GARRISON BASELINE CHANGED: main now has Shane's CarrowGateGarrison.umap (Tripo buildings, 69
   RoadReplacements, doors/collision scripts). The garrison inventory/plan made against map hash D4A722DD...
   is stale. Re-run inventory on the new map before any apply, and agree one owner for the map with Shane.
4. Shane note drafted for Connor: Claude outputs/SHANE_NOTE_2026-09-30.md.
5. Celeste updated (both copies): new tasks uz-01..uz-08, migration 2026-09-30, IB_CTX refreshed.
   Backups in Ironbreach-Planning/outputs/backup/*2026-09-30-before.html.

## Garrison current-baseline task (Codex brief 2026-09-30) -- DONE, ready for review (12:50 UTC)
- RESULT: Docs/CLAUDE_GARRISON_CURRENT_BASELINE_RESULT_2026-09-30.md (figure: Saved/GarrisonRestructure/
  20260930-claude-baseline/layout-replace/plan.png). Nothing applied, nothing saved.
- Plan fits the reference with ZERO moves of Shane's buildings/doors/anchors: existing forecourt (seaward edge
  squared), hangar reserve 60 x 25.7 m on the spine axis (outline only), spine 38.5 m, 54 m octagon pad, left
  control platform across 9 m of water, right pier (22 m) across a 9 m channel, ship berthed outboard.
  Replace mode hides the old platform AND turns its collision off (reverted by IB_GARRISON_REVERT).
- Engine dry run (job 111): 0 problems, read-only apply preflight CLEAN, manifest identical on repeat
  (3578AE17...), map FAFFD601... unchanged, 0 packages written. All 23 commandlet errors are the pre-script
  GameFeatureData ensure; 0 during the tools.
- Water (corrected 14:25): IB_Harbor_Surface has 0 simple collision shapes and its own flag is CTF_USE_DEFAULT, which
  inherits the project default CTF_USE_SIMPLE_AND_COMPLEX, so pawn sweeps are EXPECTED to pass through it and Drown()
  to snap players back. One scripted PIE drop on the preview (job 128) matched that; not a play test.
- Open for Connor/owners: map owner before apply; Cube/Cube2/Cube3 association; helicopter pose; three broken
  placeholders; reserve depth limited by PlayerStart; ship draft; no navmesh in the level.

## Garrison PREVIEW task (Codex brief CLAUDE_GARRISON_APPLY_REVIEW_2026-09-30) -- DONE (14:25 UTC)
- Tool fixes done (Scripts/ib_layout_garrison.py): per-target receipt history (Saved/GarrisonRestructure/receipts)
  so a saved apply repeats/reverts in a new process and any outside edit is refused; every piece verified for
  label/tag/mesh/material/loc/rot/scale/visibility/collision and every move for loc/rot/scale BEFORE the old
  platform is retired or anything saved; duplicate/untagged label collisions refused; revert is fully validated
  read-only first (any conflict -> refuse, nothing changed) and restores every captured platform flag exactly;
  explicit IB_GARRISON_TARGET_LEVEL required, source map refused; CTF_USE_DEFAULT resolved via the engine's
  PhysicsSettings; outputs written as LF bytes so reported SHA256 == file SHA256.
- New: ib_garrison_preview_copy.py (disposable copy + receipt), ib_garrison_preview_tests.py (outside edit,
  in-memory revert conflict, session round trip), ib_garrison_preview_capture.py (editor shots, capsule sweeps,
  optional PIE channel fall).
- Mock harness: 35/35 lifecycle checks incl. injected spawn/mesh/scale/rotation/prop-rotation/destroy/save failures.
- 13:28 job 120 queued: preview copy /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_CB1Preview, engine plan,
  verify, apply+save, reload-verify, saved repeat. Live map is never written; hashes checked every step.
- 13:35-13:41 jobs 120/121: the one-process copy crashed the editor ("World Memory Leaks" when loading a map while
  the duplicated world was still alive); every later step correctly refused the receipt-less copies. 0 shared
  asset/save changes, 0 content writes outside the preview folder, live map FAFFD601 unchanged.
- Fix: the copy is now two processes (copy+save only; then a fresh process loads source and copy, compares them
  actor for actor and writes the receipt). Harness 38/38. Capture PIE fall now samples up to 20 s.
- 13:47 jobs 124 (lifecycle A on CarrowGateGarrison_CB1Preview3), 125 (lifecycle B), 126 (GUI captures + PIE)
  queued; outputs in Saved/GarrisonRestructure/20260930-claude-preview/run3.
- 13:54 job 124 (lifecycle A, real engine) PASSED: copy (733EE97A) -> new-process verify 2983/2983 actors, receipt
  'created' -> verify clean -> apply+save 'applied-verified' (80 operations, preview E076D168) -> reload-verify 0
  differences -> saved repeat 'already-applied-verified', not saved, bytes unchanged. Shared assets/saves 0
  changes, live map FAFFD601 unchanged, 0 content writes outside the preview, 0 owned processes left.
  Every step's process exit 1 = the 23 pre-script GameFeatureData errors; tool status 'complete' each time.
- 14:07 job 125 (lifecycle B, real engine) PASSED: outside edit saved (Water_Placeholder +1 cm) -> apply, revert and
  verify all refused STALE TARGET, nothing written -> byte restore verifies as 'applied' -> revert with SM_Truck_Cargo3
  moved 10 m in memory: REVERT REFUSED, level fingerprint unchanged, not saved -> revert+save 'reverted-verified'
  (5CDF59AB) -> reload-verify exact clean state incl. all 5 platform flags -> in-session apply/revert/verify restores
  the fingerprint exactly (no save) -> re-apply+save (8FCD23B9) -> verify. Receipt: created 733EE97A, applied E076D168,
  reverted 5CDF59AB, applied 8FCD23B9. Shared assets/saves 0 changes, live map FAFFD601, 0 stray writes/processes.
- 14:09 job 126 (GUI captures) stopped at its first camera move: UE 5.8's set_level_viewport_camera_info needs a
  viewport_config_key. Nothing saved, preview unchanged. Capture tool fixed (active key + fallbacks; a failed call
  skips one shot only). 14:11 job 127 refusal probes on the real engine: layout refuses the source map and a missing
  target; copy refuses the source and an existing preview; nothing loaded or written.
- 14:15 job 128 (GUI captures, retry) PASSED: 6 shots (reference-framed overhead, top-down, 4 ground views) in
  run3/shots2; capsule sweeps: 15 paths 1190 samples 0 without ground, 4 new seams 16/16 on deck at 385; gaps show
  only the overlap-only Water_Placeholder at -35 (not a pawn floor). PIE: pawn dropped into the channel sank below
  the waterline and was back on its spine rest spot 1.29 s later (consistent with the expected Drown snap-back;
  one observation, not a play test). Preview unchanged, nothing saved.
- 14:25 DELIVERED Docs/CLAUDE_GARRISON_PREVIEW_RESULT_2026-09-30.md (evidence: run3/evidence.json). Live map
  FAFFD601 unchanged throughout; 106 shared files + 4 live saves identical in all 14 snapshots; 0 stray writes or
  processes. Next proposal P1 (rear hangar reserve 48.9 x 38.6 m on the rear edge; Command to the control platform;
  Mess_Hall rear-left) is plan-only and needs Connor's call. Delete Content/_GarrisonPreview_Disposable/ after review.
- Observed, not touched (out of scope): BP_Mech compile errors in the GUI log -- its "Update Mech Proximity" node
  calls UpdateMechProximity, which BP_IBCharacter_Infantry_C no longer has.

## Garrison COMPOSITION preview (Codex brief CLAUDE_GARRISON_COMPOSITION_PREVIEW_2026-09-30) -- DONE, ready for Codex's in-game review (15:55 UTC)
- P3 in a NEW disposable candidate: Command + Command_DoorFrame and Mess_Hall + Mess_Hall_DoorFrame onto the left
  control platform; rear centred hangar reservation (P1 envelope, provisional). Preview3 and all prior evidence kept.
- 14:54 Step 1 DONE (jobs 130/131, read-only, live map FAFFD601 unchanged, 0 protected-file changes): Command and
  Mess_Hall are complete TWO-actor assemblies by identity: no attachments either way, nothing else inside/overlapping
  their bounds (only the old platform slab under them), no property of any of the 2983 level actors references them
  or their door frames (full-level T3D, 4.7 MB), no C++/Config/Content reference by label or identity. Door frames
  (BP_DoorFrame_C) are self-contained automatic doors: trigger box + 0.3 s timeline + a door leaf that blocks
  when closed. Reserve area holds only these four actors; control platform is empty.
- 15:07 Step 2 DONE: P3 in Scripts/ib_layout_garrison.py (IB_GARRISON_COMPOSITION=P3 + the audit; baseline plan
  still byte-identical without it). Job 132 engine plan: 0 problems, plan.json 53589671, manifest 185528CC (file hash
  = reported). Command (tower, 24.4 m) rear-outer corner, yaw unchanged, door +X onto the seaward apron; Mess_Hall
  (low block, 10.9 m) along the spine edge, turned -90 so its door opens onto the spine; 7.0 m between them; both
  100% on the new deck. Reservation x[-500,4390] y[1819.4,5680.6] = 48.9 x 38.6 m (provisional; gate sets width,
  PlayerStart depth). Generated pieces now also verified for ACTOR-level collision. Harness: baseline 39/39, P3 23/23.
- 15:15 job 133 PASSED on the real engine: new candidate /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_P3Candidate1
  copied (1B374352) and verified 2983/2983 in a new process -> verify clean -> apply+save 'applied-verified' (21355364)
  -> reload-verify (building/door transforms survive) -> saved repeat no-op (bytes unchanged) -> revert+save
  'reverted-verified' (9B332912, assemblies back at source) -> reload-verify -> re-apply+save (550234E3) -> verify.
  Preview3 unchanged; 110 protected files + live saves unchanged; live map FAFFD601; 0 stray writes/processes.
- 15:20 job 134 DONE (GUI, nothing saved, candidate/Preview3/live map/protected files unchanged): 7 lit shots. Scripted
  PIE walks (real BP_IBCharacter_Infantry, capsule r34/hh88): REACHED forecourt->spine, spine->pad beside the helicopter,
  spine->control platform apron, spine->both relocated door approaches, reservation mouth->spine, and the existing
  city road->gate->forecourt route (the gate door opens). STALLED: (a) along the pier: Docks_Crane_01 (baseline pier
  dressing) blocks at x~149 m; (b) through both relocated doors: the leaf slides open and the pawn passes the frame,
  then meets the building's own collision wall 110 cm behind the frame (same offset at both; the assembly moved
  rigidly). Next: A/B the same door walk at the ORIGINAL positions (Preview3, read-only), fixed floor probe for the
  sweeps (it climbed structures), and a pier lane scan.
- 15:26 A/B (jobs 135 Preview3 = ORIGINAL positions, 136 = P3 candidate; GUI, nothing saved, both maps unchanged):
  identical door behaviour at both positions -- the leaf slides fully open, the pawn passes the frame and stops
  against the building's own collision exactly 110.0 cm behind the door line (Command and Mess_Hall alike). The
  entrances were NOT enterable before the move either: a pre-existing condition of these buildings, preserved exactly
  by the rigid assembly move. Pier: 7 of 43 pawn-wide lanes run its full length (edge lanes at y -1231..-1131 and
  719..869); the crane (x~147 m) and truck 4 (x~111 m) block the rest. Next: deck-level door sweeps + PIE walks
  along both pier edge lanes (job 137). Note: jobs 135/136 logged LIVE_MAP_SHA256=MISSING because the job set $MAP,
  which in PowerShell is the library's $map (case-insensitive); the live map is FAFFD601 by direct hash and in all
  four protected-file snapshots of those jobs.
- 15:30 jobs 137/138 (GUI, nothing saved): deck-level door sweeps agree -- with the door frame ignored, the first
  wall is the building's own collision 110.0 cm behind the door line at both P3 doors AND both original doors
  (Preview3). Pier: both edge lanes walked end to end in scripted PIE (y -1181 and y 794: 96.2 m, 16 s, 0 drift).
- 15:41 job 139 (read-only commandlet, new Scripts/ib_garrison_candidate_diff.py): candidate vs source, actor for
  actor over 15 fields: 2971 identical, 11 moves exactly at plan targets, platform = planned treatment only, 76
  planned pieces, 0 UNEXPECTED; all 23 held actors (Armory/Barracks/Medical + doors, gate, PlayerStart, weapon
  rack, Cubes, placeholders, seawalls, water) identical. Also: no Unreal process running on the PC (the owned-process
  check in jobs 130-138 used the preview folder's pattern; fixed in composition_lib.ps1).
- 15:55 DONE: Docs/CLAUDE_GARRISON_COMPOSITION_PREVIEW_RESULT_2026-09-30.md. Candidate left APPLIED (550234E3),
  receipt current; evidence in Saved/GarrisonRestructure/20260930-claude-composition/ (evidence.json 841991DF,
  board/p3-comparison-board.png). Live map FAFFD601 and Preview3 8FCD23B9 unchanged; 110 protected files + live
  saves identical in all 20 snapshots; 0 content writes outside the preview folder. Open decisions for Connor/Shane:
  hangar size/PlayerStart, building interiors (solid 110 cm behind the doors -- pre-existing), tower door direction,
  pier crane on the centreline, helicopter pose, ship draft, reservation markings at eye height, Cube association.

## Garrison PIER FINISH preview (Codex brief CLAUDE_GARRISON_PIER_FINISH_PREVIEW_2026-09-30) -- DONE, ready for Codex's review (17:45 UTC)
- RESULT: Docs/CLAUDE_GARRISON_PIER_FINISH_PREVIEW_RESULT_2026-09-30.md. Candidate /Game/_GarrisonPreview_Disposable/
  CarrowGateGarrison_PierFinish1 left saved APPLIED (r2, C904EF8C), receipt current, no test process running. Evidence:
  Saved/GarrisonRestructure/20260930-claude-pierfinish/ (run2/evidence.json AE0D8138, board/pf1-r2-board.png).
- Pier: crane turned to lie along the pier (yaw 0) on the berth side, 100% on the deck; the four trucks 75 cm nearer the
  channel edge than in P3; a straight 6.0 m marked lane x 10182..18480, y -221.7..378.3. Engine lane scan (real collision,
  Pawn profile): pawn-centre band 720 cm -> obstacle-free corridor 788 cm between the crane and truck 4; lane edges ~87 /
  ~102 cm from real collision. Sweeps 15/15 clear. Scripted PIE 16/16 reached: the lane both ways (96.5 m, 16.1 s), both
  lane edges, the three altered joins, both door approaches, a step onto the control platform's coping curb, Codex's
  passage (13.05 s) and road -> gate -> forecourt.
- Finish: 72 pieces tagged IB_GarrisonPierFinish: coping 18 (M_Bastion_Concrete, BlockAll, 8 cm walkable curb), fascia 18
  (NoCollision), markings 36 at 40 cm (edge/lane lines, route dashes, door bars; NoCollision). Joins flush away from the
  water corners; doors/approaches clear of coping; nearest new piece 7.8 m from the helicopter; 0 new coplanar overlaps.
  vs P3: all 76 P3 pieces and 6 of 11 moves identical; only the crane + 4 trucks and the 72 tagged pieces differ.
- r1 -> r2 inside the task: r1's 20 cm lines did not read overhead, so the same candidate was reverted exactly with the r1
  plan and re-applied as r2 (40 cm markings, trucks +75 cm). Jobs 140-143 (r1), 144-146 (r2); tool v9 C0DB217B; offline
  harness PF1 21/21, r1->r2 16/16, P3 23/23, lifecycle 39/39, diff 8/8. Candidate diff: 2971 identical, 0 unexpected.
- FINDING, decision needed: the markings render GREY, not yellow. MI_Landmass_HelipadMarking overrides 'Color', but its
  parent M_FlatCol exposes 'Base Color' (engine probe: effective Base Color 0.18 grey, Metallic 0, Roughness 1). All 16
  MI_Landmass_* carry the same 'Color' override, so P3's pad ring/spine dashes/reservation outline and the live map's
  landmass/helipad pieces are grey too. Options: (a) a new MI for the finish markings only; (b) fix the shared family
  (changes the live map's look -- Connor's call). Not done here: the brief allows no material change.
- Preservation: live map FAFFD601, P3Candidate1 550234E3, Preview3 8FCD23B9 unchanged; 116 protected files identical in all
  14 snapshots (before-140 .. after-146); 0 content writes outside the preview; 0 owned processes left. Two shutdown
  crashes after all output was written (the material-probe commandlet; the GUI editor, exit 0xC0000005); not investigated.

## Garrison YELLOW MARKINGS preview (Codex brief CLAUDE_GARRISON_YELLOW_MARKINGS_PREVIEW_2026-09-30) -- DONE (19:40 UTC); ACCEPTED by Codex as the next preview base
- RESULT: Docs/CLAUDE_GARRISON_YELLOW_MARKINGS_PREVIEW_RESULT_2026-09-30.md (E7159E4E). Candidate /Game/_GarrisonPreview_Disposable/
  CarrowGateGarrison_YellowMarkings1 left saved APPLIED (AF25734A), receipt current (created -> applied -> reverted -> applied),
  no test process running; the queue holds only the inert 153-yellow-after.hold. Evidence: Saved/GarrisonRestructure/
  20260930-claude-yellowmarkings/ (run1/evidence.json 00A76533, board/ym1-before-after-board.png, run1/log_check.json,
  board/ym1-post-checks.json).
- New MI /Game/_GarrisonPreview_Disposable/YellowMarkings1_Materials/MI_YM1_DeckPaintYellow (B9E3E18F): parent M_FlatCol
  (unchanged), only override 'Base Color' = (0.95, 0.82, 0.15) linear, read back after reload; Metallic 0, Roughness 1 (matte,
  non-emissive); 'Color' not set. Owned by the candidate in its receipt.
- Assigned to exactly 91 generated markings by actor/component/slot (P3 ring 32, spine 15, reserve 8; PF1 36), slot 0 of
  StaticMeshComponent0, NoCollision kept. List + original override lists: run1/plan/assignments.json (C1A18F4A). The 3 live-map
  Helipad_North_H_* users of the shared MI are untouched (still grey, as in the live map).
- Job 155 lifecycle (real engine) PASSED: verify clean -> apply+save -> reload-verify (91 expected, 0 unexpected, 3040 other
  actors identical) -> saved repeat no-op -> revert+save (91 originals restored, 0 differences from PF1) -> reload-verify ->
  re-apply+save -> verify-final. Editor AND PIE readouts: 91/91 markings on the new MI (before: 91 on MI_Landmass_HelipadMarking).
- Visual: matched before (job 152z, PF1) / after (job 156, YM1) editor + PIE captures on the same cameras. Paint went from grey /
  grey-brown to yellow (hue 44-53 deg; saturation +0.25..0.52 in every view). The reference's deck paint is amber (hue ~31-32 deg):
  ours is 17-20 deg yellower; the candidate's own MI can be retinted in place if wanted. Exposure not locked: after frames are
  0.01-4.84 luma levels darker outside the paint. No paint geometry changed (P3's 40 coplanar joins now share one material; no
  seams in zoomed crops; flicker not filmed).
- Movement: one scripted PIE pier walk reached (16.0 s); lane scan (788 cm) and 15/15 sweeps identical to PF1 r2.
- Tool fix inside the task: job 152's copy-verify (tool v1) refused the copy with 13 differences that appeared only in its
  two-maps-in-one-process comparison (door-frame editor sprites _0/_1, water Custom/BlockAll). Probe 154 did not reproduce
  them; mechanism not identified. Tool v2 (FCD658A2) fingerprints each map alone and skips editor-only components; the
  unchanged copy then verified 3131/3131.
- Preservation: 224 protected files (brief's 116 + PF1 map/receipt + 106 PF1 evidence files) identical in all 14 snapshots
  (before-150 .. after-156); PF1 C904EF8C and its receipt 4470B368 unchanged; live map FAFFD601; 0 content writes outside the
  preview; 0 owned processes left.
- Engine health: NOT a clean run. All 19 processes logged the pre-existing GameFeatureData ensure (each also wrote an Ensure-type
  crash-reporter folder in its isolated UserDir); the GUI logs also show the BP_Mech compile errors. All 19 logs close normally
  with no access violation; the GUI editors exited 0. PF1's two shutdown access violations remain uninvestigated.
- Open for Connor: the shared MI_Landmass_* family still sets 'Color' (the live map's own markings render grey); amber vs yellow.

## Garrison FORECOURT FINISH preview (Codex brief CLAUDE_GARRISON_FORECOURT_FINISH_PREVIEW_2026-09-30) -- DONE (21:50 UTC); ACCEPTED by Codex as the next preview base
- RESULT: Docs/CLAUDE_GARRISON_FORECOURT_FINISH_PREVIEW_RESULT_2026-09-30.md (26350CFA). Candidate /Game/_GarrisonPreview_Disposable/
  CarrowGateGarrison_ForecourtFinish1 (copied from the accepted YM1, AF25734A) left saved APPLIED (181159BF), receipt F703F4A1
  current (created -> applied -> reverted -> applied); no test process running; the queue holds only the inert
  153-yellow-after.hold. Evidence: Saved/GarrisonRestructure/20260930-claude-forecourtfinish/ (run1/evidence.json A5324B5B,
  board/ff1-board.png, board/ff1-pad-joints-moving-camera.png, run1/log_check.json).
- New MI /Game/_GarrisonPreview_Disposable/ForecourtFinish1_Materials/MI_FF1_DeckPaintAmber (93A7971E): parent M_FlatCol
  (unchanged), only override 'Base Color' = (0.85, 0.60, 0.22) linear (muted amber), read back after reload; matte,
  non-emissive. On all 91 generated markings (YM1 MI -> FF1 MI) and the 105 new paint pieces; editor AND PIE readouts
  91/91 + 105/105. YM1's MI, the shared MI_Landmass_HelipadMarking and its 3 live-map users untouched.
- Forecourt finish (125 new actors, tag IB_GarrisonForecourtFinish): quay coping (9, BlockAll, the +8 cm PF1 curb) + fascia (11)
  + inset edge lines on the forecourt's water edges (land-ramp flanks fascia only; pier/spine entrances kept open; Medical's
  coping narrowed to 40 cm; P3 reservation's rear edge fascia only); an 8 m painted cross-road along the seaward edge (landward
  line + centre dashes); gate-road lines on the pier's 6 m lane centres; axis-road lines on the spine's lane centres; 3 door
  bars + 3 dashed service lanes (Barracks, Armory, Medical). No building or assembly moved; two short landward-edge fragments
  not laid (local constraint, reported).
- Pad ring: 32 x 408 cm chords 1.5 cm proud -> 96 x 125 cm segments 0.5-0.6 cm proud (same 18.9 m radius and 40 cm width; the
  32 old actors reshaped, originals in the receipt's ring_before; 64 new). The near arc reads smooth and flat at eye height in
  all 16 moving-camera frames; the far side (> 25 m) still aliases into crawling dashes, as in YM1 (a rendering-technique
  question, not a joint defect).
- Job 162 lifecycle (real engine) PASSED: preflight -> apply+save -> reload-verify (248 planned changes = 125 pieces + 32 ring
  edits + 91 slots; 0 missing, 0 unexpected; 3040 other actors identical) -> saved repeat no-op (bytes unchanged) ->
  revert+save (0 differences from YM1) -> reload-verify -> re-apply+save -> verify-final.
- Movement (job 164, on FF1): 11 affected scripted PIE routes ALL REACHED (land join through the gate, pier/spine entrances beside
  the new corners, cross-road, 3 door routes, a step onto the new coping +8.4 cm). Sweeps 9/11 clear; the 2 blocked ones are
  objects the pawn passed (the closed gate leaf in the editor world; a reviewed pier truck). Lane scans: gate, axis and cross
  roads clear across and beyond their paint (>= 10.7 / 16.2 / 11.4 m).
- Colour: paint hue YM1 49-50 deg overhead -> FF1 37.5-38.3 deg overhead and 33.5-36.5 deg up close; reference 30.5-32 deg
  (FF1 is 4-8 deg yellower overhead). No retint made; one is available.
- Preservation: 328 protected files (Codex's 224, each matching Codex's recorded hash; YM1 map/MI/receipt; 101 YM1 evidence
  files) identical in all 10 snapshots (before-160 .. after-164); live map FAFFD601; 0 content writes outside the preview;
  0 owned processes left.
- Engine health: NOT a clean run. All 16 processes logged the pre-existing GameFeatureData ensure (each commandlet exits 1 for
  it; each process wrote an Ensure-type crash-reporter folder); the GUI logs also show the BP_Mech compile errors and one
  CurrentVisualData NULL line. All 16 logs close normally with no access-violation line. The job 163 GUI editor returned
  0xC0000005 after its log closed (as PF1 r2 once did); job 164's exited 0.
- Open for Codex / Connor: the rear hangar (Connor's); far-distance paint shimmer; road weight vs the reference; an optional
  retint; the forecourt's straight lines are still 1.5 cm proud (PF1 height).

## Garrison PAINT STABILITY preview (Codex brief CLAUDE_GARRISON_PAINT_STABILITY_PREVIEW_2026-09-30) -- DONE (00:10 UTC 10-01); ACCEPTED by Codex as the current preview base
- RESULT: Docs/CLAUDE_GARRISON_PAINT_STABILITY_PREVIEW_RESULT_2026-09-30.md (B696682A). Candidate /Game/_GarrisonPreview_Disposable/
  CarrowGateGarrison_PaintStability1 (copied from the accepted FF1, 181159BF) left saved APPLIED (4AC42632), receipt FADED192
  current (created -> applied -> reverted -> applied); new material PaintStability1_Materials/M_PS1_PadRingDecal (4F6A2A1A).
  No test process running; the queue holds only the inert 153-yellow-after.hold. Evidence:
  Saved/GarrisonRestructure/20260930-claude-paintstability/ (run1/evidence.json 650F98FD, analysis/, board/, tools-used/).
- Cause: sampling of a sub-pixel band (far side 1.1 px at 25 m -> 0.34 px at 45 m at eye height). The same 96 segments 3x wider at
  the same heights lose the breakup (along-arc CV 0.304 -> 0.086); depth conflict (float depth ~0.003 mm at 45 m vs 5-16 mm
  clearance) and LOD/culling not supported. Geometric factor: on the pad's 4 corner chamfer pieces (top 1 cm lower) FF1's segments
  stand 1.5 cm proud and read steady at 1.44x the band's true coverage.
- Change (ring only): the 96 segments hidden (component visibility only, each captured in the receipt) + one DecalActor
  IBGC_PS1_PadRingDecal whose candidate-local deferred-decal material draws the same 18.9 m / 40 cm ring analytically, box-filtered
  over each pixel's footprint; FF1's Base Color, no colour tuning, no collision change.
- Actual PIE moving sequence (72 frames, eye height, same path/settings both runs, background-subtracted), far arc 35-45 m:
  along-arc CV 0.310 -> 0.200, per-point temporal CV 0.218 -> 0.155, gaps 1.3% -> 0.1%. Deck strips 0.311/0.256 -> 0.204/0.169;
  chamfer arc FF1 0.117/0.077 (1.44x) vs PS1 0.136/0.103 (0.82x). A hard-edged decal control is as bad as FF1 (the filter, not the
  decal, makes the difference). Near band colour and width unchanged; overhead ring unchanged with smoother edges.
- Lifecycle (job 177) PASSED: 97 planned changes (96 + 1), 0 missing, 0 unexpected; saved repeat a no-op; revert 0 differences
  from FF1; re-apply verified. One scripted PIE walk across the ring reached (capsule z 475.2, as on FF1).
- Preservation: 451 protected files identical in 18 snapshots (before-170 .. after-178); FF1 map/MI/receipt match the brief; live
  map FAFFD601; 0 content writes outside the preview; 0 owned processes left. NOTE: 3 of Codex's 328 (Saved/SaveGames
  IBCharacters.sav, IronBreach_Vault.sav, IronBreach_XP.sav) were written 21:51-21:52 UTC, after Codex's list (21:50:30) and
  before job 170 (22:04:54) -- not by this task; unchanged since.
- Engine health: 19 processes, all logs closed normally, 0 access-violation/critical/fatal lines; the known GameFeatureData ensure
  everywhere. Jobs 171 (camera height bug), 173 (Python API / blend mode) and 175 (helper named PS = Get-Process alias) superseded.
- Open for Codex: the far line is faint (0.82-0.93x true coverage) and its residual variation is near, not at, the noise
  estimate; on the chamfer arc PS1 is slightly less steady than FF1's proud segments; the straight-line shimmer is not converted
  (the same filtered-coverage approach could address it later). No Git, locks, commit or push.

## Garrison REFERENCE FIT review (Codex brief CLAUDE_GARRISON_REFERENCE_FIT_REVIEW_2026-10-01) -- DONE (01:55 UTC 10-01); REVIEWED by Codex, RS1 authorized (02:03 UTC)
- RESULT: Docs/CLAUDE_GARRISON_REFERENCE_FIT_REVIEW_RESULT_2026-10-01.md (AEE04BEC). READ-ONLY analysis: no engine, no job, no map/asset/
  config write, no actor moved; queue still holds only the inert 153-yellow-after.hold. Evidence:
  Saved/GarrisonRestructure/20261001-claude-referencefit/ (board/rf-board.png EA7023D2, analysis/fit.json 62F20F52, analysis/geometry.json
  8BDF743A, plan/rs1_plan.json E88BA0E2, plan/rs1_manifest.csv F41C15C3, hashes/protected-before|after.json).
- Camera vs layout: PS1's overhead still has a known camera (model within 5.7 px of the deck edges) and draws the rear at 0.73x the pad's
  scale; the approved picture fits best as a near-orthographic oblique view (12 accepted anchors only: 17.0 px rms, ~2.4 m).
  "Narrower at the rear" is camera: forecourt 124.9 m vs the picture's compound 127 m (band 127-138).
- Ranked gaps: (1) LAYOUT rear depth + shore: PS1 has 106.8 m of deck behind the quay, then a 26.25 m water strip and a straight flat land
  edge at x -3125; the picture's compound is 47-59 m deep and its rocky wooded shore wraps both rear corners (waterline meets the rear-right
  corner at x 4329-5433, runs along the left side to x 8055-8557). (2) LAYOUT blocked by assets/ownership: flank service rows (7 block
  fronts + small tower in the picture; Barracks' unassociated Cubes, Armory's weapon rack, no further service-building meshes).
  (3) ART/ASSET: materials, dressing, drawn pier/ship proportions. Not counted: Connor's hangar (picture front x 4904-5974, 60-69 m with
  wings vs the unchanged 48.9 x 38.6 m reservation).
- ONE next pass recommended: RS1 "rear shore attachment and land shoulders" on a new disposable copy of PS1 (proposed
  CarrowGateGarrison_RearShore1): land at the mainland level (top -5) filling the strip and wrapping the rear corners along the picture's
  waterline, a planted terrace (top 400) on the empty rear-left flank behind x 4390 and 6 m clear of the reservation, a rock rim and trees
  copied from the mainland kit. 254 new actors (43 land slabs, 9 terrace slabs, 54 rocks, 74 trees x2); nothing existing moved, hidden or
  edited; offline dry run 0 problems. Conflicts listed for Codex: the picture's own road runs through the terrace (PS1 keeps Shane's gate
  side); a wider hangar would meet the terrace; dropping off the rear walls now lands on land (way back via ramp + gate).
- Readiness checklist (existing evidence): routes/doors/land gate reached on candidates; deployment/return PASS on the LIVE map only
  (crewqa log 2026-09-22 23:51:55); one drown snap-back. Open: spawn check on the final candidate, deployment after any promotion, more
  drop points, PS1 decal visual check on feet (needs a stand-in: the PIE pawn has no skeletal mesh) and on the helicopter.
- Preservation: 451/451 protected files + PS1 map/material/receipt + reference + live map FAFFD601 identical at 00:35 and 01:46 UTC.
  The three 09-30 21:51-21:52 save files kept at their current bytes (no restoration, no investigation). No Git, locks, commit or push.
  An independent verification pass checked every number and citation; its corrections are in the result.

## Garrison RS1 REAR SHORE preview (Codex brief CLAUDE_GARRISON_REAR_SHORE_PREVIEW_2026-10-01) -- DONE (04:35 UTC 10-01); ACCEPTED by Codex as the next preview base (04:55 UTC)
- RESULT: Docs/CLAUDE_GARRISON_REAR_SHORE_PREVIEW_RESULT_2026-10-01.md. Evidence: Saved/GarrisonRestructure/20261001-claude-rearshore/
  (board/rs1-board.png 0F2C0D4B, plan/rs1_engine_plan_r2.json 9711DEBA, plan/deviations_r2.json 9A6C0884, check-rs1-r2b/rs1_checks.json 58F93AC9).
- Candidate /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_RearShore1 (882F9D20, RS1 r2 applied) = PS1 + 284 new actors (43 land
  slabs, 28 coast bands, 2 wall bands, 9 terrace slabs, 54 rocks, 74 trees x2); all 3257 inherited actors identical. Receipt:
  Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_RearShore1.json (0033AAD5): created, applied r1,
  reverted, applied r1, reverted, applied r2, reverted, applied r2. Ownership = tag IB_GarrisonRearShore AND recorded identity.
- r1 (the reviewed 254) was applied and captured; its 7.5 m land staircase left 129 m2 of water inside the reviewed coast line. r2 = 73
  documented deviations on new pieces only (43 slab trims, 28 coast bands, 2 wall bands): 0 m2 of holes, 1.4 m2 outside (<= 33 cm).
- Lifecycle PASS (jobs 180-182, 184): copy verified, digest-gated plan-check, saved apply/reload, saved repeat no-op, 4 ownership negatives
  refused (nothing saved), exact revert, re-apply. Bounds: Land_10/11 3.81 m below the (collision-free) gate mesh; rocks inside the 15 %
  margin, >= 1.77 m below the deck top; reservation and 6 m bands 0 overlaps; 166 engine contacts all expected, 0 unexpected.
- Scripted PIE with the real infantry pawn (job 186; stills job 185; NOT manual play): settled spawn at PlayerStart; spine 10.6 s,
  doors 1.53 / 6.77 s, land join 21.7 s; terrace steps up and back on both faces; shore drop off the rear wall onto Land_06 and back via
  ramp + gate 8/8 in 19.27 s; 4/4 coast drown snap-backs onto the new land; 18 climb attempts, 0 bypasses. Spawner enabled throughout,
  its zones NoCollision, 0 Kaiju. Job 185's own classifiers mislabelled 3 outcomes; job 186 re-ran queries + PIE with them fixed.
- Preservation 04:07 UTC: Codex's 456/456 match; 1249 files of the first stamp unchanged; live map FAFFD601; the four save files =
  Codex's bytes. 35 engine processes, all exited (32 commandlets exit 1 = GameFeatureData ensure, 3 GUI exit 0); error lines = PS1
  baseline plus the intended negative-test refusals.
- Correction: the reference-fit checklist's "BP_Mech is still missing" is stale (restored, crew QA 6/6 + 13/13, pushed e106831).
  Observed now: BP_Mech loads with its 7 pre-existing compile-error lines (UpdateMechProximity); no mech placed in the garrison. Not repaired.
- Next composition gap: flank service rows (blocked by assets/ownership). No Git, locks, commit or push; queue holds only
  153-yellow-after.hold.

## Garrison SR1 SERVICE ROWS preview (Codex brief CLAUDE_GARRISON_SERVICE_ROWS_PREVIEW_2026-10-01) -- DONE (06:50 UTC 10-01); REVIEWED by Codex (07:07 UTC): placement and routes OK for disposable work, identity unfinished -> SR2
- RESULT: Docs/CLAUDE_GARRISON_SERVICE_ROWS_PREVIEW_RESULT_2026-10-01.md (30671A8C). Evidence: Saved/GarrisonRestructure/20261001-claude-servicerows/
  (board/sr1-board.png BF044791, plan/sr1_engine_plan.json 6CEB8D57, plan/sr1_plan_check.json 6C9702E2, check-sr1/sr1_checks.json F67B4995,
  analysis/bounds_check.json 7F39FB6E, analysis/picture_fronts.json 8512CAC5, analysis/dependency_search.txt 6646DA07).
- Candidate /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ServiceRows1 (5C5ABD10, SR1 applied) = RS1 + 2 exterior shells
  (IBGC_SR1_Shell_RightBack / _RightFront: Armory mesh, uniform x13, yaw 180, 12.74 x 11.45 x 8.80 m, closed bay doors) on the right flank
  south of the gate road, street faces 5 cm behind the Barracks' building line; all 3541 inherited actors identical (3543 in all).
  Receipt Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ServiceRows1.json (3479FC82): created,
  applied, reverted, applied; identities StaticMeshActor_1002 / _1003. Ownership = tag IB_GarrisonServiceRows AND recorded identity.
- Measured first: only the south strip (42.8 x 11.9 m) fits; passages 7.93 / 7.93 / 4.42 m, rear walkway 3.45 m, street walkway 6.99 m;
  reservation, 6 m bands and approach >= 24.2 m away; no paint covered. North strip 11.0 m (5.0 m with the side clearance carried along),
  all inside the gate-road walking corridor; left flank conflicts with the Armory approach; Mess_Hall shows "07" on both ends; the
  mainland warehouse/garage are civilian sheds. No code or Blueprint references the Armory mesh (analysis/dependency_search.txt).
- Lifecycle PASS (jobs 190, 192): digest-gated plan-check, in-memory bounds, saved apply/reload verify, saved repeat no-op, 4 ownership
  negatives refused (nothing saved), exact SR1-only revert, re-apply; final 3541 identical + 2 planned, 0 unexpected. Bounds: engine
  boxes = plan within 0.5 cm, 0 unexpected intersections, 78 keep-outs pass, 0 paint overlaps.
- Scripted PIE (job 193; NOT manual play): 17/17 walks as expected, 0 driven teleports: spawn and reservation mouth -> spine, the three
  door approaches, both walkways, three passages, loops round each shell, into each closed bay (stops at the door) and back out, city
  road -> ramp -> gate -> gate road -> cross-road 22.33 s. 10 capsule lanes clear; 56 face sweeps stop on the shell; 6 contacts, all expected.
- Picture: both shell fronts fall inside the fitted front-x bands of the picture's R1_back and R2_front_b; R2_front_a covers the gate
  road's north part and verge; the picture's left rows stand where the Armory, its rack, the terrace and part of the approach are.
- RESIDUAL FOR REVIEW: each shell repeats the Armory mesh's baked "03" on its sea face (over the rear walkway; visible from that walkway,
  from the cross-road's south end and from the RS1 right coast). Asset gap: a number-free material variant or a new low service block.
- Preservation 06:13 UTC: Codex's 1251 records, 1249/1249 project files match; 1421 files of the first stamp unchanged; all 8 job stamps
  identical; live map FAFFD601; RS1 882F9D20 and its receipt unchanged; the four saves = Codex's bytes. 19 engine processes, all exited;
  job 193's editor returned 0xC0000005 after its log had closed (as PF1 job 146 / FF1 job 163); error lines = RS1 baseline plus the
  intended negative-test refusals. No Git, locks, commit or push; queue holds only 153-yellow-after.hold.

## Garrison SR2 SERVICE IDENTITY fix (Codex brief CLAUDE_GARRISON_SERVICE_IDENTITY_FIX_2026-10-01) -- DONE (09:50 UTC 10-01); ACCEPTED by Codex as the next disposable base (09:51 UTC)
- RESULT: Docs/CLAUDE_GARRISON_SERVICE_IDENTITY_FIX_RESULT_2026-10-01.md (ABDF0AD2). Evidence: Saved/GarrisonRestructure/20261001-claude-serviceidentity/
  (board/sr2-board.png D6D6F874, check-sr2/sr2_checks.json 447DFB9F, run1/material/material_manifest.json 932C1CCD,
  analysis/residue_overlay/, hashes/preservation-final.json 22B3866F).
- Candidate /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ServiceRows2 (0267B9A3, SR2 applied) = SR1 (5C5ABD10, unchanged) with ONE
  change: slot 0 of StaticMeshComponent0 on IBGC_SR1_Shell_RightBack / _RightFront (StaticMeshActor_1002 / _1003) -> preview-local
  MI_SR2_Armory_NoNumber; the other 3541 actors (real Armory included) identical, 3543 in all. Receipt
  Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ServiceRows2.json (44AEE146): created, applied,
  restored, applied. New assets only in /Game/_GarrisonPreview_Disposable/ServiceRows2_Materials/: M_SR2_Armory_NumberRemap (4026D14C;
  duplicate of M_Tripo_PBR_Master + 83 built-in nodes) and MI_SR2_Armory_NoNumber (A8EB671B; the same 4 Armory textures, read-only).
- Measured first: the "03" is in the base colour, the normal map AND the mesh (glyphs 4.1 cm proud at the median, 5.4 cm p95, max
  5.6 cm at x13); not in roughness/metallic. Material: a UV mask on the number's own chart only (8038 triangles weighted, all on that
  chart): base colour + normal from a plain area of the same texture (offset -764.5, -33.5 texels) with a small colour correction,
  normal flattened to the panel, world-position offset lowering the relief (max 5.3 cm; seam vertices never move).
- Lifecycle PASS (job 199 copy + job 201): apply/save/reload 3541 identical + 2 planned slot changes, 0 unexpected; repeat apply a no-op
  (byte-identical); exact restore to SR1 (3543/3543, fingerprint digest = SR1's); re-apply; 3 ownership negatives (nothing saved). Job
  199's first apply was refused (an in-memory collision-profile read effect on IB_Harbor_Surface); job 202 collision body detail of
  3558 components: 0 differences.
- Visual (job 203, one GUI session, 12 cameras x SR1/SR2): "03" gone on both shells, no rectangular patch, the real Armory's "03"
  unchanged. RESIDUAL FOR REVIEW: at 2.6 m a short groove curl (~20 cm) and a faint tone step (~0.6 m), both exactly on the number
  chart's own UV edge (computed overlay); not noticeable in the oblique/face/walkway/coast/row views. Not called clean.
- Job 203 editor exit 0 (0x00000000), log closed 08:57:55 UTC. SR1 job 193's exit-time 0xC0000005 stays unresolved (not investigated).
- Preservation 09:17 UTC: Codex's 1423 records, 1421/1421 project files match; 1558 first-stamp files unchanged; 17 job stamps
  identical; live map FAFFD601; SR1 map/receipt/evidence, the picture, the four saves and 64 Tripo files unchanged. 35 engine
  processes, all exited.
- Disclosed: autosave not settable from Python (4 autosaves, all inside the evidence folder's user-gui/); job 199 printed
  LIFECYCLE_COMPLETE=True despite refusals and left misnamed backups; job 196's after-stamp failed ($e shadowed $E) -> job 197
  recheck 0 changes; job 194's probe hit an access violation (fixed in 195); collision still holds the raised glyphs (the offset is
  visual only). No Git, locks, commit or push; queue holds only 153-yellow-after.hold.

## Garrison SP1 SHORE PALETTE preview (Codex brief CLAUDE_GARRISON_SHORE_PALETTE_PREVIEW_2026-10-01) -- DONE (11:40 UTC 10-01); REVIEWED by Codex (11:52 UTC): ground accepted for continued disposable work, rocks -> SP2
- RESULT: Docs/CLAUDE_GARRISON_SHORE_PALETTE_PREVIEW_RESULT_2026-10-01.md (011A4C1A). Evidence: Saved/GarrisonRestructure/20261001-claude-shorepalette/
  (board/sp1-board.png 154FEE71, check-sp1/sp1_checks.json 8EDD678C, run1/material/material_manifest.json C4CA8E44,
  analysis/palette_measure.json E990EEB3, hashes/preservation-final.json 73579D4A).
- Candidate /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette1 (333A3A44, SP1 applied) = SR2 (0267B9A3, unchanged) with ONE
  change: slot 0 of StaticMeshComponent0 on the 136 RS1 natural-terrain pieces (RS1-recorded identity + IB_GarrisonRearShore):
  land 43 + terrace 9 -> MI_SP1_Ground_Land; coast 30 (incl. the 2 wall bands) -> MI_SP1_Ground_Coast; rock 54 -> MI_SP1_Rock_01 /
  _02 / _Eroded by mesh (18 each). 3407 actors identical, 136 differ only in that slot, 0 unexpected; 3543 in all. Receipt
  Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ShorePalette1.json (F6BA8E00): created,
  applied, restored, applied. New assets only in /Game/_GarrisonPreview_Disposable/ShorePalette1_Materials/: M_SP1_Ground (B0B9D79B;
  duplicate of M_AI_MountainGround, graph rebuilt: world-aligned grass/forest-floor mottle + grey stone, normals, roughness),
  M_SP1_Rock (058459D5; duplicate of M_AI_MountainRock_01: the mesh's own baked maps desaturated/darkened), MI_SP1_Ground_Land
  (46435690), MI_SP1_Ground_Coast (0B30C52B), MI_SP1_Rock_01 (CB33D04E), _02 (7AC46A68), _Eroded (8DF309E3). Existing textures read-only;
  the four shared M_AI masters and all their other users (CityGround, MountainGroundPad, background peaks) unchanged.
- Look comparison in memory: job 205 stopped at the material build (UE 5.8 delete_all_material_expressions removes every other
  node per call); job 206 V0-V3 -> ground = V2; rock = V2's graph darkened/neutralised from V2's measured render (first rendered in 208).
- Lifecycle PASS (job 207): copy 3543/3543 identical; apply/save/reload 3407 + 136 planned, 0 unexpected; repeat apply a no-op;
  exact restore to SR2 (fingerprint digest = SR2's B211C5AD); re-apply; 3 ownership negatives on the new guard (nothing saved).
- Visual (job 208, one GUI session, 13 cameras x SR2/SP1, editor exit 0, log closed 10:56:35 UTC): ground now mottled olive-green
  with real detail, no stretch streaks, no slab-seam texture breaks (changed ground in the picture's framing (156,128,72) ->
  (91,90,60); picture olive (87,86,61)). Rocks no longer snow-white: taupe-grey with dark crevices on the two mountain meshes, but the
  18 eroded-mesh rocks are darker than before and all rocks read dark/low-contrast in shade and from the air (warmer and darker than
  the picture's light grey). Not called finished: exact per-instance correction in result section 9 (not run: one render session).
- Preservation 11:35 UTC: Codex's 1560 records, 1558/1558 project files match; 1976 first-stamp files unchanged; 10 job stamps
  identical (421BEC92); live map FAFFD601; SR2's six artifacts, the picture and the four saves unchanged. 19 engine processes, all
  exited (16 commandlets exit 1 = known ensure; 3 GUI exit 0). Autosave read back off in jobs 206/208 (C++ property names); 205's
  read failed; no package autosaved.
- Next largest reference mismatch: the shoreline form (the picture's continuous grey boulder band + surf vs a straight slab edge with
  separate small peaked rocks); then the sea colour and the forest canopy.
- Disclosed: job 205's failed build; tools/__pycache__ written by Python; graphs rebuilt rather than adjusted; the rock setting was
  not previewed before job 208. No Git, locks, commit or push; queue holds only 153-yellow-after.hold.

## Garrison SP2 ROCK PALETTE fix (Codex brief CLAUDE_GARRISON_ROCK_PALETTE_FIX_2026-10-01) -- DONE (13:25 UTC 10-01); ACCEPTED by Codex for continued disposable work (13:40 UTC)
- RESULT: Docs/CLAUDE_GARRISON_ROCK_PALETTE_FIX_RESULT_2026-10-01.md (68AB1239). Evidence: Saved/GarrisonRestructure/20261001-claude-rockpalette/
  (board/rp2-board.png 2976CCA8, check-sp2/rp2_checks.json FF5BD6BA, run1/prepare/material_manifest.json F37A8920,
  analysis/rp2_measure_final.json E70F89D6, hashes/preservation-final.json 265E6240).
- Candidate /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ShorePalette2 (68CA73DE, SP2 applied) = SP1 (333A3A44, unchanged) with ONE
  change: slot 0 of StaticMeshComponent0 on SP1's 54 recorded rocks -> MI_SP2_Rock_01 / _02 / _Eroded (18 each). They are duplicates
  of MI_SP1_Rock_* (same parent M_SP1_Rock, textures, roughness 0.9, normal strength 1.0) with only gain, gamma and tint changed:
  01 and 02 gain 0.22 -> 0.21, gamma 1.3 -> 0.65; Eroded gain 0.22 -> 0.60, gamma 1.3 -> 0.65; tint (1.0, 0.95, 0.93) ->
  (0.86, 0.93, 1.0) for all; desaturation 1.0 kept. 3489 actors identical, 54 differ only in that slot, 0 unexpected;
  component-relative transforms compared on all 3570 in-game components. Receipt
  Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_ShorePalette2.json (9224A409): created,
  applied, restored, applied. New assets only in /Game/_GarrisonPreview_Disposable/ShorePalette2_Materials/: MI_SP2_Rock_01
  (53458EC2), MI_SP2_Rock_02 (9C38F7DA), MI_SP2_Rock_Eroded (3FBD4550).
- Rendered comparison first (job 209, one GUI session, in memory, never saved): SP1, C1 (the brief's starting point), C2 ->
  C2 for all three families. The plan step refuses any value not read back from the rendered C2 instances.
- Lifecycle PASS (job 210, six batched commandlet processes): copy 3543/3543 identical; apply, save, fresh-process verify (54
  planned slots, 0 unexpected); saved-state no-op; exact restore to SP1 (digest = SP1's 67BE42A2); re-apply (digest = the first
  apply's F0509F98); final verify.
- Visual (job 211, one GUI session, SP1 then SP2 from disk, 7 cameras on the same tick schedule: sky patches within 0-2 levels):
  eroded rocks no longer crushed (median (45,33,22) -> (92,73,51); pixels below luminance 25: 21.5% -> 8.8%); 01 lighter and
  cooler; the shaded 02 wall rock now neutral slate grey like the wall; the right-rim eroded rocks mid taupe-grey (still darker
  than 01/02). NOT called finished: every sunlit rock face is still beige-warm in the map's low sun (02: (144,113,81) ->
  (141,118,89)); the albedo is now slightly cool, so the remaining warmth is the light.
- Exits: job 209 GUI 0; job 210's six commandlets 1 (known ensure); job 211 GUI 0xC0000005 after its log had closed (the known
  exit crash, not investigated; all 14 stills and records written). 8 crash-reporter folders, all the startup ensure.
- Preservation 12:56 UTC: Codex's 1980 records, 1976/1976 project files match (4 engine files unchanged across the job stamps);
  SP1's 12 reviewed artifacts match; 2125 first-stamp project files unchanged; 6 job stamps identical (9F5E0714); live map
  FAFFD601, the 11 earlier preview maps, the picture and the four saves unchanged. Autosave read back off; nothing autosaved.
- Disclosed: job 209's light drifted between variants (its numbers mix material and clouds); the shade measurement covers one rock
  (037); the new step batching has no engine refusal test (guard unchanged); job 211's log has one 98 KB settings line. No Git,
  locks, commit or push; queue holds only 153-yellow-after.hold.

## Garrison BS1 BOULDER SHORE preview (Codex brief CLAUDE_GARRISON_BOULDER_SHORE_2026-10-01) -- DONE (16:55 UTC 10-01); REVIEWED by Codex: useful visual base, not gameplay-accepted while the 61 rocks have NoCollision -> BS2
- RESULT: Docs/CLAUDE_GARRISON_BOULDER_SHORE_RESULT_2026-10-01.md (AAE0A980). Evidence: Saved/GarrisonRestructure/20261001-claude-bouldershore/
  (board/bs1-board.png AD393265, check/bs1_checks.json 6E0E97C3, plan/bs1_plan.json 9881238C, analysis/check_summary.json 4C10250D,
  hashes/preservation-final.json B35DB186).
- Candidate /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore1 (49154B4E, applied) = SP2 (68CA73DE, unchanged) with the
  35 RS1 coast-rim rocks (16 left, 19 right; exact RS1/SP2 identities) re-formed and 26 new BS1-owned rocks (12 left, 14 right) on the
  same two rims: SM_Mountain_05 / SM_Mountain_Plateu_01 cut deep at the sea surface (treatment T1b), MI_SP2_Rock_02 read-only, no new
  material. 3508 of SP2's 3543 actors identical, 35 edited as planned, 26 new, 0 unexpected. Receipt (8DB374D1): created, applied,
  restored, applied, restored, applied.
- Collision: each mesh's only collision is one tile-wide convex hull, so exactly these 61 rocks are NoCollision (BlockAll -> NoCollision
  on the 35). SP2's rim rocks had invisible hull colliders on 238 of 894 coast-grid points (67 over open water); BS1 has none.
- Trial first (jobs 214/215, one left-rim stretch, in memory, never saved): T1 broad massifs vs T2 SP2 families; T1b (T1 cut deeper and
  taller, so the tiles' low ground lies metres down) chosen; the stretch went into the plan as rendered except two rocks moved 1.5-2 m.
- Lifecycle PASS (jobs 216/218/220/222): copy identical; guarded apply and save; fresh reload shows only the planned changes; no-op
  repeat; ownership negatives 8 applied-state + 6 clean-state refused; restore equal to SP2 actor for actor (twice; its fingerprint text
  differs only by -0.0 vs 0.0 roll on the 35); re-apply; final verify. Two faults stopped jobs without saving anything (job 216: a
  negative-test undo; job 218: the restore compared a late read with SP2's first-read harbour profile); both fixed and re-run.
- Job 223 (one GUI session, editor exit 0): 14/14 paired stills, SP2 then BS1 from disk, same cameras and tick schedule; scripted PIE
  with the real pawn on both maps: 4/4 coast drowns identical; 6/6 walks through the rock band recovered (SP2: 3 first stood on
  hulls); both coast paths 0 stops (SP2: 8 and 1); 6 climbs per map, 0 bypasses; rim ends and the gate return unchanged; 3 settled and
  22 traversal in-game frames on BS1 (scripted movement, not manual play).
- Gaps: pale submerged rock skirts under the single-layer water; players walk and see through rock where it overlaps the land band;
  sunlit colour still warm; no surf; IBGC_BS1_Rock_023 is fully hidden by its neighbours. Preservation 16:47 UTC: Codex's 2129 records
  2125/2125 project files match (4 engine files unchanged by the stamps); SP2's 9 artifacts match; 2224 first-stamp files unchanged.
  No Git, locks, commit or push; queue holds only 153-yellow-after.hold.

## Garrison BS2 BOULDER COLLISION correction (Codex brief CLAUDE_GARRISON_BOULDER_COLLISION_2026-10-01) -- DONE (23:28 UTC 10-01); BLOCKER: recovery holds, decision needed; stopped for Codex's review
- RESULT: Docs/CLAUDE_GARRISON_BOULDER_COLLISION_RESULT_2026-10-01.md (32545CB2). Evidence: Saved/GarrisonRestructure/20261001-claude-bouldercollision/
  (hashes/evidence-final.json 32590AA3, hashes/preservation-final.json 56DE0B60, analysis/trap_eval.json 423454FB, analysis/pits.json
  C16CFFE7, analysis/final_eval.json 56EEE81A, analysis/coverage_eval.json 290A885F).
- Candidate /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore2 (2D642903, applied) = BS1 (49154B4E, unchanged) with exactly
  BS1's 61 rocks given collision: 4 preview-local duplicates of the two used meshes (BoulderShore2_Collision/SM_BS2_Mountain_05_Outcrop
  B82152AF, _Stone 58AD5684, SM_BS2_Mountain_Plateu_01_Outcrop 3FDDA823, _Stone 1E0AF25B); only their simple collision differs: 41,321
  convex pieces fitted to the visible rock above the sea surface, CTF_USE_SIMPLE_AS_COMPLEX, nothing below z -35. On the 61 only the
  mesh and NoCollision -> BlockAll changed; no rock moved. Receipt F162F20B: created, applied, restored, applied.
- Small proof first (jobs 225/226, one outcrop + one stone, in memory): real pawn stopped 0.0-1.1 cm from the visible faces, camera
  >= 47.9 cm, 15/15 shots OnServerHit on the face, negatives clean.
- Lifecycle PASS (job 227): fresh reload 3508/3569 identical + the 61 as planned; no-op repeat; 9 + 7 ownership conflicts refused
  (shared-tag decoys not selected); restore = BS1 digest; re-apply; final verify. Coverage on all 61 (5 channels x 5705 rays): rock hits
  0.04-2.66 cm from the visible rock; none below the sea surface, in gaps or over open water.
- Routes (jobs 228/230, scripted PIE): 4/4 drowns onto land; revised coast walks 39/39 + 36/36; rim ends, rear-wall drop and gate return
  as BS1; 6 deck-end climbs at the full 10 s, 0 bypasses. Stills: whole frames within the BS1-BS1 control. No frame cost (job 229 A/B).
- BLOCKER: recovery is not preserved. With solid rocks the pawn can be held where Drown() cannot act (capsule centre above z -35;
  LastSafeLocation is any walkable floor, rocks included). Scripted PIE found 11 holds: job 230 2 of 11 candidates (BS1_Rock_006 island
  66; the BS1_Rock_018/RS1_Rock_025 waterline crevice), job 231 9 of 34 wedge pits from an offline scan (analysis/bs2_pits.py); 9 of the
  11 at the waterline. In-memory unwalkable rocks (job 230 part 2) stopped rock-top standing but not the crevice. Options (result 9.6):
  recovery code change (outside the brief; recommended), a bounded geometry pass, or BS1's NoCollision rocks for play.
- Processes: 16 engine processes; commandlets exit 1 (known ensure); GUI 226/230/231 exit 0, 228/229 0xC0000005 after the log closed
  (known exit-time fault); 0 access-violation/fatal lines. Preservation 22:56 UTC PRESERVED: Codex's 2228 records (2224 project files)
  and 6 BS1 artifacts match; all 16 stamps (2447 files) identical. No Git, locks, commit or push; queue holds only 153-yellow-after.hold.

## Garrison BS3 SHORE RECOVERY proof (Codex brief CLAUDE_GARRISON_SHORE_RECOVERY_PROOF_2026-10-01) -- DONE (02:50 UTC 10-02); two-area proof PASSES for the isolated stone and the crevice; two holds remain on unchanged actors; stopped for Codex's review
- RESULT: Docs/CLAUDE_GARRISON_SHORE_RECOVERY_PROOF_RESULT_2026-10-01.md (07826B42). Evidence: Saved/GarrisonRestructure/20261001-claude-shorerecoveryproof/
  (hashes/evidence-final.json E17868BE, hashes/preservation-final.json 58A5E5EE, analysis/proof_eval.json 2A0D2E42, analysis/control_eval.json
  AAD95E03, analysis/bs3_design_yaw.json 9593A571, analysis/log_check.json BAAB5211).
- Candidate /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3 (FDF8219D, applied) = BS2 (2D642903, unchanged) with:
  IBGC_BS1_Rock_006 moved (+55, -40) cm (68.0 cm) + component-local Unwalkable; IBGC_BS1_Rock_018 moved (-33.1, -17.0) cm and turned
  +6 deg (yaw 34.08 -> 40.08: translation alone left the V at the crevice) + Unwalkable; IBGC_RS1_Rock_025 verified unchanged. z, pitch,
  roll, scale, meshes (BS2's 4 collision assets, read-only), materials, BlockAll unchanged; nothing added, hidden or deleted.
  Receipt 656013F7: created, applied, restored (= BS2 digest A0F8F41F), applied.
- Lifecycle PASS (jobs 233/234): fresh reload 3567/3569 + the 2 planned; override read back after load; no-op repeat; 11 + 10 fault
  cases refused (shared-tag decoys never selected); restore = BS2; re-apply; final verify.
- PIE proof (job 235, editor exit 0) + controls (job 236, exit 0): left 13 routes + 36 placements, right 7 routes + 34 placements.
  LEFT FIXED: island 66, job 226's landing, wedge 19 points 0/1/2/4, the stone grid and scan spots all Drown() onto land (on BS2 the same
  placements and the full-speed jump hold on the stone). RIGHT FIXED: the crevice is closed (arm flush with the outcrop face); all 33
  placements and 7 routes return onto land (BS2 crevice placement still holds = positive control). 0 walking ticks / 0 LastSafe on the
  stones. Stone shots hit the stones; 4 clear-line water shots hit nothing.
- REMAINING (both identical on BS2, on unchanged actors): right wedge 01 beside RS1_Rock_025 (needs >= 90 cm or 6-10 deg on the 7.3 m
  outcrop: stop reason), and a 44.3 deg standing pocket on RS1_Rock_013's top 30 cm north of left wedge 19.
- Fixed on the way: job 235's gap shots met the neighbouring rock (redone clear-line in job 236); moving-camera frames were written as
  NTFS streams (colon in the name) and recovered losslessly by job 237 (48 PNGs).
- Processes: 11 engine processes; commandlets exit 1 (known ensure), GUI exit 0 (no exit-time crash this time); 0 access-violation/fatal
  lines. Preservation 02:43 UTC PRESERVED: Codex's 2447 records + 12 artifacts match; all 8 stamps (2748 files) identical; live map FAFFD601.
- No Git during the proof jobs. Connor then asked to push this work: branch claude/garrison-shore-recovery (a2152229), see "Git / build".

## Windows job runner
- "IronBreach job runner (Claude)" window (zzrunner.bat) runs only scripts Claude drops in
  Saved/zz_job/queue; logs in Saved/zz_job/logs. Close the window to stop it.

## Log (UTC)
- 04:15 linked. 04:40 runner up. 04:43 verify-worktree merge 1b0d6f8. 04:45 clean build FAILED (2 leaked calls).
- 04:47 fix 9a12d3e; 04:52 clean build OK. 04:53 main fast-forwarded, WIP restored. 05:04 pushed 9a12d3e.
- 05:05 pushed 430d9aa. 05:11 mech set restored locally. 05:14 crew QA run 1. 05:19 harness fix + run 2 PASS.
- 05:24 Celeste updated. 05:25 final check: main == origin/main == 430d9aa.
- 11:28 pushed e106831 (mech set restored on main, Connor's call).
- 12:29 garrison job 110 queued (read-only inventory r2 + layout plans).
- 12:36 job 111 (inventory r3 + layout plans) clean; 12:50 garrison result doc delivered.
- 13:28 garrison preview job 120 queued (disposable copy only).
- 13:47 preview jobs 124-126 queued (two-stage copy, lifecycle A/B, captures).
- 14:25 garrison preview result doc delivered (jobs 124/125/127/128 passed; live map unchanged).
- 14:50-15:41 garrison composition jobs 130-139 (new disposable P3 candidate; live map unchanged).
- 15:55 garrison composition result doc delivered.
- 16:28-17:00 garrison pier-finish jobs 140-143 (new disposable PierFinish1 candidate, r1; live map unchanged).
- 17:14-17:32 jobs 144-146 (r2: 40 cm markings, trucks +75 cm; exact r1 revert, lifecycle, diff, checks).
- 17:45 garrison pier-finish result doc delivered.
- 18:24-18:54 garrison yellow-markings jobs 150-156 (new disposable YellowMarkings1 candidate + preview-local MI; live map unchanged).
- 19:20-19:30 post-run read-only checks (run1/log_check.json, board/ym1-post-checks.json).
- 19:40 garrison yellow-markings result doc delivered.
- 20:07-20:53 garrison forecourt-finish jobs 160-164 (new disposable ForecourtFinish1 candidate + candidate-local MI; live map unchanged).
- 20:55-21:45 read-only post-checks (board, log check, evidence index) and an independent verification pass.
- 21:50 garrison forecourt-finish result doc delivered.
- 22:04-23:05 garrison paint-stability jobs 170-178 (new disposable PaintStability1 candidate + candidate-local decal material;
  live map unchanged).
- 23:05-00:05 analysis (background-subtracted temporal metrics, space-time plot), evidence index, independent verification pass.
- 00:10 (10-01) garrison paint-stability result doc delivered.
- 00:22-01:55 (10-01) garrison reference-fit review: read-only analysis, comparison board, RS1 dry run, independent
  verification; no engine, no job. 01:55 result doc delivered.
- 02:30-03:06 (10-01) garrison RS1 jobs 180-183 (new disposable RearShore1; r1 lifecycle + GUI checks; live map unchanged).
- 03:27-04:04 RS1 r2 coast jobs 184-186 (exact r1 revert, r2 lifecycle, GUI stills, scripted PIE re-run); offline board, log and
  preservation checks, independent verification pass.
- 04:35 garrison RS1 rear-shore result doc delivered.
- 04:55 Codex accepted RS1 as the next preview base; SR1 service-rows brief.
- 05:07-06:10 garrison SR1 jobs 190-193 (new disposable ServiceRows1: copy + site, GUI kit probe, lifecycle, GUI checks; live map unchanged).
- 06:10-06:47 offline bounds, log and preservation checks, board, picture-fronts mapping, dependency search, independent verification pass.
- 06:50 garrison SR1 service-rows result doc delivered.
- 07:07 Codex reviewed SR1 (placement OK for disposable work; identity unfinished); SR2 service-identity brief.
- 07:19-07:26 SR2 source probes, jobs 194-195 (194 ended in an access violation; 195 clean).
- 07:54-08:23 SR2 GUI look probes, jobs 196-198 (in memory, never saved).
- 08:27-08:52 SR2 jobs 199 (materials + copy; apply refused), 201 (lifecycle PASS), 202 (collision body detail).
- 08:52-08:58 SR2 paired visual check, job 203 (editor exit 0).
- 09:00-09:46 board, residue overlay, log and preservation checks, independent verification pass.
- 09:50 garrison SR2 service-identity result doc delivered.
- 09:51 Codex accepted SR2 as the next disposable base; SP1 shore-palette brief.
- 10:05-10:07 SP1 probe, job 204 (read-only commandlet).
- 10:15-10:30 SP1 GUI look comparisons, jobs 205-206 (in memory, never saved; 205 stopped at the material build).
- 10:37-10:49 SP1 lifecycle, job 207 (materials, copy, apply, no-op repeat, restore, re-apply, 3 negatives; PASS).
- 10:50-10:56 SP1 paired render session, job 208 (editor exit 0).
- 10:57-11:38 board, palette measurement, log and preservation checks, independent verification pass and fixes.
- 11:40 garrison SP1 shore-palette result doc delivered.
- 11:52 Codex reviewed SP1: ground accepted for continued disposable work; rock palette -> SP2 brief.
- 12:04-12:09 SP2 GUI look comparison, job 209 (SP1, C1, C2; in memory, never saved).
- 12:33-12:38 SP2 lifecycle, job 210 (instances, copy, apply, no-op repeat, restore, re-apply, final verify; PASS).
- 12:38-12:43 SP2 paired render session, job 211 (14 stills; editor exit 0xC0000005 after its log closed).
- 12:43-13:22 measurement, board, log and preservation checks, independent verification pass and fixes.
- 13:25 garrison SP2 rock-palette result doc delivered.
- 13:40 Codex accepted SP2 for continued disposable work; BS1 boulder-shore brief.
- 14:20-14:26 BS1 prep and probe, jobs 212-213 (copy, copy verify; the probe re-run read-only after job 212's failed).
- 14:40-14:58 BS1 trials, jobs 214-215 (one left-rim stretch, in memory, never saved; T1b chosen).
- 15:23-15:44 BS1 lifecycle, jobs 216, 218, 220, 222 (two faults fixed, nothing saved by the failed steps; PASS).
- 15:44-16:21 BS1 paired render session and focused checks, job 223 (14 stills; scripted PIE on SP2 and BS1; editor exit 0).
- 16:21-16:50 board, log and preservation checks, independent verification pass and fixes.
- 16:55 garrison BS1 boulder-shore result doc delivered.
- 17:11 Codex reviewed BS1 (useful visual base; not gameplay-accepted with NoCollision rocks); BS2 boulder-collision brief.
- 17:46-17:51 BS2 prep, job 224 (copy, copy verify, read-only mesh probe).
- 18:27-18:31 BS2 collision assets and proof traces, job 225 (4 preview-local duplicates; outcrop + stone in memory).
- 18:38-18:43 BS2 small proof in PIE, job 226 (editor exit 0).
- 19:13-19:20 BS2 lifecycle, job 227 (copy = BS1, apply, no-op repeat, negatives, restore, re-apply, final verify + coverage; PASS).
- 19:47-20:59 BS2 final GUI checks, job 228 (stills, sweeps, routes, camera sequences; editor 0xC0000005 after its log closed).
- 21:00-21:13 BS1/BS2 frame-time A/B, job 229 (no collision cost).
- 21:33-22:17 BS2 hold probes and in-memory unwalkable test, job 230 (editor exit 0).
- 22:40-22:52 BS2 wedge-hold probes, job 231 (editor exit 0).
- 22:52-23:25 evaluations, log/frame/preservation checks, evidence manifest, independent verification pass and fixes.
- 23:28 garrison BS2 boulder-collision result doc delivered; stopped for review (recovery decision needed).
- 02:03-02:12 UTC 10-02 (19:03-19:12 PDT 10-01) BS3 copy and lifecycle, jobs 233-234 (PASS).
- 02:12-02:26 BS3 two-area PIE proof, job 235 (stills, 20 routes, 70 placements; editor exit 0).
- 02:29-02:35 BS3 clear-line water shots and BS2 controls, job 236 (editor exit 0). 02:40 frames recovered, job 237.
- 02:36-02:50 evaluations, preservation, evidence manifest; result doc delivered; stopped for Codex review.
- 02:47 pushed branch claude/garrison-shore-recovery (a2152229; BS3 map + 15 assets + 2 docs); main unchanged (job 238).
