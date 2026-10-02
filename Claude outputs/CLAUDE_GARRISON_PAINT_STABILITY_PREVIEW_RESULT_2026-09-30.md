# Garrison paint stability preview (PS1) result — 2026-09-30

Claude, 00:10 UTC on 2026-10-01. This answers `Docs/CLAUDE_GARRISON_PAINT_STABILITY_PREVIEW_2026-09-30.md`. Engine jobs 170–178 ran from 22:04 to 23:05 UTC on September 30; the job logs print local time (UTC−7). The analysis and an independent verification pass followed.

**Candidate, left saved and applied for review:**
`/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_PaintStability1`
(`Content/_GarrisonPreview_Disposable/CarrowGateGarrison_PaintStability1.umap`, SHA256 `4AC426322A155FA802E365528E9F625E673EDDEE4DF322C3683AD04A7F63E6CC`, the last `applied` entry in its new receipt).

**New candidate-owned material:**
`/Game/_GarrisonPreview_Disposable/PaintStability1_Materials/M_PS1_PadRingDecal`
(file SHA256 `4F6A2A1A942F4F9BCE7480C5A2012473F245A4546C4316D2E2ABE0E450355C30`). No test process is running. The job queue holds only the inert `153-yellow-after.hold`.

## Short answer

**Cause.** The far-arc breakup is sampling of a sub-pixel band. On the far side of the ring, at eye height, the 40 cm band projects to about 1.1 px at 25 m and 0.34 px at 45 m. Making the same segments 3× wider at the same heights removes it; depth conflict and LOD are not supported by the evidence (section 2).

A geometric factor adds to it: how far each segment stands proud sets how much of its side is visible.

- On the deck strips FF1's segments stand 0.5–0.6 cm proud, and they crawl.
- On the pad's four corner chamfer pieces, whose top is 1 cm lower, the same segments stand 1.5–1.6 cm proud. There they render steady, at 1.44× the band's true coverage.

**Change.** PS1 hides FF1's 96 segments and draws the same ring with one decal. The decal's material box-filters the band analytically over each pixel's footprint.

**Result.** Measured in the same actual PIE moving sequence, same path and settings:

- **On the deck strips** (250 of the 319 far-arc points at 35–45 m, where FF1's dashes are):
  - along-arc variation: 0.311 → 0.204;
  - per-point temporal variation: 0.256 → 0.169;
  - gaps: 1.3 % → 0.2 %;
  - coverage: 0.99 → 0.93 of the true band.
- **On the chamfer arc** (69 points): FF1 was steady at 1.44× true coverage (along-arc 0.117, temporal 0.077). PS1 reads 0.82× there and is slightly less steady (0.136 / 0.103).
- **The filtering makes the difference.** The same decal with a hard edge breaks up as badly as the geometry. The near band keeps FF1's colour and width.
- **Still open** (section 10): the far line is faint and 7–18 % short of its true coverage; its residual variation is close to, not at, the measurement noise; and PS1 is slightly less steady than FF1's proud segments on the chamfer arc.

## Scope held

- **Written in Content:** only the new candidate map and the new material. The candidate's new receipt is in Saved.
- **Byte-identical before and after every job:** 18 snapshots of 451 files (section 8):
  - FF1's map `181159BF…`, material instance `93A7971E…` and receipt `F703F4A1…`, matching the brief;
  - all 328 paths of Codex's list, including the live map `FAFFD601…`;
  - FF1's evidence files.
- **Three save games no longer match Codex's recorded hashes:** `IBCharacters.sav`, `IronBreach_Vault.sav` and `IronBreach_XP.sav`, of the 328. They were written at 21:51–21:52 UTC, after Codex's list (21:50:30) and 13 minutes before this task's first process (22:04:54). They are unchanged throughout (section 8).
- **Git and scope:** nothing was deleted. No Git, locks, commit or push, no live-map promotion, no shared edit, no message to anyone.
- **Untouched:** the rear hangar (Connor's) and every assembly. The only level change is the ring's representation.

## 1. At a glance

| Item | Result |
|---|---|
| Cause | **Sub-pixel sampling, plus the segments' height.** On the far side the band's projected height is f·w·h/d² = 1.11 px at 25 m, 0.77 at 30, 0.57 at 35, 0.43 at 40, 0.34 at 45 (f = 1123.6 px, w = 40 cm, h = 154 cm). The measured far band (35–45 m) averages 0.51 px. The same 96 segments made 3× wider at the same heights lose the breakup: along-arc CV 0.304 → 0.086 on a settled frame. Depth conflict is not supported: that test keeps the clearance, and float depth resolves about 0.003 mm at 45 m. LOD is not supported either: single-LOD cubes, never distance-culled, and every segment in the view was flagged as rendered. The chamfer arc shows that segments standing taller render steadier, at a higher coverage. Section 2. |
| Representation | FF1's 96 ring segments are **hidden, not deleted**: StaticMeshComponent0 visibility True→False, each prior value captured in the receipt. **One new DecalActor**, `IBGC_PS1_PadRingDecal`, sits at the ring centre on the deck top and projects straight down. Its candidate-owned material draws the same ring (18.9 m centre radius, 40 cm wide, FF1's Base Color) with a box-filtered analytic coverage. Only one ring draws. Section 3. |
| Temporal comparison | 72 actual PIE frames at eye height, 10 cm per fixed 1/30 s frame, same path, camera and settings in both runs. Far arc 35–45 m, background-subtracted, 319 ring points, FF1 → PS1: along-arc CV **0.310 → 0.200**, per-point temporal CV **0.218 → 0.155**, gaps **1.3 % → 0.1 %**. Split by deck piece: on the deck strips 0.311/0.256/1.3 % → **0.204/0.169/0.2 %**; on the chamfer arc 0.117/0.077 → 0.136/0.103. As a control, FF1's geometry was re-shown inside the PS1 session: 0.308 / 0.201 / 0.7 %. Section 4. |
| Near / overhead | Near band sRGB median FF1 (117.8, 95.5, 58.3) vs PS1 (116.9, 95.0, 57.7). Measured/projected width: FF1 1.018, PS1 1.030. Overhead: the same clean circle, with slightly smoother edges in PS1. No colour tuning. Section 5. |
| Lifecycle | preflight → apply+save → reload-verify → saved repeat (no-op, bytes unchanged) → revert+save → reload-verify (0 differences from FF1) → re-apply+save → verify-final. **All passed.** 97 planned changes (96 visibility flags + 1 decal actor), 0 missing, 0 unexpected; 3160 other actors identical. Section 6. |
| Gameplay | One actual PIE walk across the ring **reached**, capsule centre constant at 475.2 as on FF1. No collision changed; the helicopter and every other actor are identical to FF1. Section 7. |
| Engine health | 19 processes: all logs close normally, 0 access-violation, critical or fatal lines. Only the known GameFeatureData ensure (19 ensure-type reporter folders) and known warnings. Jobs 171, 173 and 175 did not deliver and are superseded. Section 9. |

## 2. Cause: a small A/B at the same camera and actual gameplay settings

**Setup.** All frames here were taken in job 172 on FF1, at the settled start pose of the moving path: (17832, 6875, eye z 539.15), pitch −4°, yaw −104.3°. They used the actual PIE settings in section 4.

**Method.** Each frame is compared with the same pose with **no ring at all**. That reference was captured in the PS1 session with the decal hidden in the PIE world (`capture-ps1/pie/pie-noring-settled.png`). The difference is integrated across the band (method in section 4). The along-arc CV is the variation of the paint's contrast along the arc: 0 is an even line, and dashes give high values.

| Variant (PIE world only, nothing saved) | far band | along-arc CV 35–45 m | gaps | 25–35 m CV |
|---|---|---|---|---|
| a) FF1 as saved, settled back buffer (TSR converged) | 0.50 px | **0.304** | 1.0 % | 0.100 |
| b) frames 3 / 13 / 55 after re-arriving (TSR history rejected, then rebuilt) | 0.50 px | 0.329 / 0.349 / 0.312 | 1–2 % | 0.09–0.15 |
| e) the same 96 segments 3× wider (120 cm), same heights | 1.5 px | **0.086** | 0 | 0.048 |

Frame 0 after re-arriving reads 0.360. It is not a fair sample: the 4 m teleport blurs that frame, and its near band shows only about 6 % of its normal contrast.

**Sampling: supported by the ×3 test, the TSR series and the hard-edged decal.**

- The ×3 test widens the band past a pixel at unchanged heights, and the breakup disappears.
- TSR does not resolve the half-pixel band even with a static camera: (a) matches the re-arrival frames.
- A hard-edged decal, which point-samples the same band, breaks up the same way (section 4).
- The high-resolution stills are judged with the deck beside the band as reference, since no no-ring frame exists at those sizes.
  - The 1920×1080 still and the 2160p still box-averaged to 1080p are **inconclusive**: their control-ring noise (sd 45.3 and 43.6) is as large as the signal.
  - The native 3840×2160 still is interpretable (noise sd 10.4, a noise CV of about 0.14). With a 0.83 px band it still breaks up (CV 0.373), consistent with sampling: the band is still below a pixel there.

**A geometric factor: the chamfer arc.**

- The pad deck is three strips with their top at z 385.0, plus four corner chamfer pieces with their top at 384.0.
- The ring crosses the chamfers on four 17.4° arcs centred on the diagonals (19 % of the circumference; the probe and FF1's fingerprint give the pieces' transforms). There FF1's segments (top 385.5–385.6) stand 1.5–1.6 cm proud instead of 0.5–0.6 cm.
- On the far arc's chamfer section, FF1's ring is steady (CV 0.117, temporal 0.077) and its coverage measures 1.44× the band's true coverage. On the deck strips it averages 0.99× and crawls (0.311 / 0.256).
- So the taller the segment, the more of its side shows, the higher its rendered coverage and the steadier it reads. (The metric cannot tell a wider line from a brighter one at this size, for example lit side faces.) This is the same size effect that makes a raised curb read solid, which the brief rules out as the workaround.

**Depth conflict: not supported.**

- The ×3 variant keeps every segment's height (top 0.5–0.6 cm above the deck strips) and loses the breakup.
- The engine's reversed-Z float depth resolves roughly z·6×10⁻⁸, about 0.003 mm at 45 m, against 5–16 mm of clearance.

**Geometry / LOD: not supported.**

- The probe (job 170): all 96 segments are `/Engine/BasicShapes/Cube`, 1 LOD, not Nanite, draw distance 0 (never culled), receive decals. There are no cull-distance volumes.
- The renderer's last-render flag, which also counts off-screen passes such as shadows, was set on 77 of 96 segments. The farthest flagged was 43.2 m away.
- Projected with the fitted camera model, about 58 segments are in the view, and all of them were flagged. Every corner of the 19 unflagged segments lies outside the view, so they are frustum-culled, not distance-culled. The other 19 flagged segments are off-screen.
- The chords' 1 cm sagitta against the true circle is negligible.

**Camera model (fitted, not assumed; `analysis/camera_fit.json`).**

- The PIE viewport keeps the vertical field of view of a 16:9 camera: focal length (H/2)·(16/9)/tan 45° = 1123.6 px, a 74.6° horizontal view at 1713×1264.
- On the settled FF1 frame, the observed near-band centre sits 0.17 px (sd 0.24, max 0.80) from this projection over 99 columns. The horizontal-FOV model misses by 61.7 px.

Numbers are in `analysis/cause_ab_metrics.json`; the images are in `capture-ff1-r2/pie/diag-*.png`.

## 3. What changed, exactly (the ring representation)

Only these differ from FF1.

- **Plan:** `plan/ps1_plan.json` (`A96C7305…`). It was generated from FF1's own fingerprint (loaded alone in its own process) and cross-checked against the probe's segment list, with 0 problems.
- **Ownership manifest:** `run1/reapply-save/ownership_manifest.json` (`F1364BE3…`).

**Suppressed: 96 existing actors.**

- **Which:**
  - `IBGC_Pad_Ring_00..31` (P3's 32, reshaped by FF1);
  - FF1's 64 `IBGC_FF_Pad_Ring96_NN`, where NN runs from 01 to 95 skipping multiples of 3 (FF1's 96 positions gave the multiples of 3 to the reshaped P3 actors).
  - Each is a StaticMeshActor with the run tag and one in-game `StaticMeshComponent0` (Cube, `MI_FF1_DeckPaintAmber`, NoCollision).
- **Change:** that component's visibility only, True → False. Transform, mesh, material, collision, tags and folder are unchanged.
- **Restoration:** the receipt's `applied` entry holds each captured visibility (96 × True). `revert` restores them and removes the decal.

**New: one actor, `IBGC_PS1_PadRingDecal`.**

- DecalActor, tags `IB_GarrisonCB1` + `IB_GarrisonPaintStability`, folder `Carrowgate Garrison/Paint Stability PS1`.
- Location (17232, 4525, 385): the ring centre on the deck top.
- Rotation pitch −90, projecting straight down. A DecalActor's root carries its own −90° pitch, and spawning composes it with the spawn rotation, so the tool sets the rotation outright after spawning and verifies it.
- DecalSize (10, 1950, 1950). These are half-extents: ±10 cm vertically around the deck top, over a 39 m square.
- FadeScreenSize 0, SortOrder 0, no collision. Editor-only arrow and sprite components are skipped by the fingerprint (18 → 20).

**New material `M_PS1_PadRingDecal`.** It is candidate-owned, lives in the candidate's own subfolder, and its graph comes from `Scripts/ib_garrison_ring_decal.py` (`4E730D8F…`).

- **Domain and blend:** Deferred Decal, Blend Mode Translucent. With Substrate on, a deferred decal takes the material's own blend mode.
- **Surface:**
  - Base Color parameter = FF1's paint, (0.85, 0.60, 0.22) linear.
  - Roughness 1 and Metallic 0, the `M_FlatCol` values FF1's instance inherits.
  - Specular 0.5, the engine default.
  - Normal and Emissive are not connected, so the deck's own normal stays and nothing glows.
- **Opacity (analytic ring coverage):**
  - In decal UV, s = |p| − 1890 cm is the distance from the ring's centre line.
  - The pixel's footprint along s comes from the decal's own UV derivatives (DecalDerivative): Fw = |ds/dx| + |ds/dy|.
  - Coverage is the exact overlap of a one-pixel box with the 40 cm band: clamp((min(s + Fw/2, 20) − max(s − Fw/2, −20)) / Fw, 0, 1).
  - A resolvable band is solid with a one-pixel anti-aliased edge. A sub-pixel band spreads its area over the pixel whatever the TSR jitter, so it fades instead of hitting or missing sample points.
- **Verified after save and reload:** domain, blend mode, all pins connected, Normal/Emissive/FrontMaterial empty, parameters 1890 / 20 / 1950, Base Color exact.
- **Compilation:** the shader compiled in the GUI (363 pixel instructions in the transient twin). The saved material logged 0 compile failures in the capture run and rendered.

**Unchanged:**

- every other actor and component (3160 actors identical);
- the deck, pad heights and collision, quay pieces, roads, all buildings, doors and gameplay assemblies, PlayerStart, land gate, crane/trucks, helicopter, ship and the hangar reservation;
- the other paint and road geometry.

## 4. Before/after in actual PIE camera motion

**Capture.**

- Both runs used the same check script flow: job 172 on FF1 and job 178 on PS1. Both versions are kept in `tools-used/`.
- The two versions differ in three places:
  - the diagnostic blocks, including a transient preview-material build at script start. It failed harmlessly in job 172 and does not run in job 178;
  - the extra block, which runs after the moving sequence;
  - the start-up wait: 45 s with diagnostics, 30 s without.
- `pie_settings.json` is identical apart from the log path:
  - 1713×1264 game viewport, FOV 90, player camera 154.15 cm above the deck;
  - all 29 recorded console variables identical: AA method 4 (TSR), TSR history 200 % with 16 samples, screen percentage 100, motion-blur quality 4, DBuffer 1, Substrate 1, scalability 3, auto exposure on. One of them, `r.PostProcessAAQuality`, does not exist in this build and reads 0;
  - `-UseFixedTimeStep -FPS=30`.
- **Motion:** the pawn is placed 10 cm further along +X every rendered frame, with a fixed control rotation, and the game viewport's back buffer is saved every frame (`Shot`). That gives 72 ordered frames over 7.1 m of travel, in which the far arc runs at about 25–45 m.
- **This is a dense ordered frame sequence from the real PIE session. It is not a video recording and not a person playing.**
- **Clip:** `analysis/ff1_vs_ps1_far_arc.mp4` is assembled from those frames: FF1 on top, PS1 below, far-arc rows 577–654 at original resolution. It plays 72 frames at 10 fps, so 2.4 s of game time is slowed to 7.2 s. The same frames are in `analysis/ff1_vs_ps1_far_arc_frames/`, and every 6th pair is in `analysis/ff1_vs_ps1_far_arc_every6th.png`.

**Measurement** (`analysis/ps1_analysis.py`, `DC248126…`).

1. Each frame's recorded pose projects the ring's centre line and edges.
2. The frame minus the no-ring frame at the same pose (`s1-noring`, captured in the PS1 session; 0 pose mismatches) is integrated across the band, along the image normal.
3. The result is the paint's contrast per pixel of true band thickness, divided by the near band's full-coverage contrast. So 1.0 means true coverage.
4. Points where the deck is hidden (helicopter, legs, shadow) are skipped.
5. **Noise:** the same measurement on bare-deck control rings 7 m inside and outside the ring gives sd 5.4–6.5. For a perfect line of PS1's far contrast that is an along-arc CV of about 0.18 (0.15 for FF1's). It is an estimate, not a hard floor.

**Far arc, 35–45 m** (band 0.51 px; 319 ring points in every run):

| Moving sequence (72 actual PIE frames) | coverage ratio | along-arc CV | gaps | breaks /m | per-point temporal CV | frame-to-frame change |
|---|---|---|---|---|---|---|
| FF1 geometry ring (job 172) | 1.10 | 0.310 | 1.3 % | 0.005 | 0.218 | 0.110 |
| FF1 geometry re-shown inside the PS1 session (control, job 178) | 1.13 | 0.308 | 0.7 % | 0.002 | 0.201 | 0.106 |
| **PS1 decal ring (job 178)** | **0.90** | **0.200** | **0.1 %** | **0.001** | **0.155** | **0.102** |
| same decal, box-filtered, transient preview on FF1 (job 174) | 0.96 | 0.177 | 0.1 % | 0.000 | 0.140 | 0.093 |
| same decal with a HARD unfiltered edge, transient preview (job 174) | 0.73 | 0.380 | 2.5 % | 0.015 | 0.323 | 0.196 |

**Split by the deck piece under the ring** (`split_by_deck_piece` in the same JSON files):

| 35–45 m | coverage ratio | along-arc CV | per-point temporal CV | gaps |
|---|---|---|---|---|
| deck strips (250 points) FF1 / control / **PS1** | 0.99 / 1.00 / **0.93** | 0.311 / 0.287 / **0.204** | 0.256 / 0.237 / **0.169** | 1.3 % / 0.7 % / **0.2 %** |
| chamfer arc (69 points) FF1 / control / **PS1** | 1.44 / 1.52 / **0.82** | 0.117 / 0.113 / **0.136** | 0.077 / 0.069 / **0.103** | 0 / 0 / **0** |

**Resolvable band, 25–35 m** (1.64 px; almost entirely on the deck strips):

| Run | coverage ratio | along-arc CV | temporal CV | gaps |
|---|---|---|---|---|
| FF1 | 1.11 | 0.068 | 0.062 | 0 |
| control | 1.09 | 0.065 | 0.056 | 0 |
| PS1 | 0.98 | 0.087 | 0.052 | 0 |

**Near band (5–15 m, 16.7 px):** coverage ratio 1.00–1.01 in every run. Temporal CV is 0.016 for PS1 and 0.019–0.023 for the geometry.

**Settled frames at the start pose** (35–45 m):

| Frame | along-arc CV | coverage ratio |
|---|---|---|
| FF1 | 0.304 | 1.13 |
| control | 0.359 | 1.07 |
| **PS1** | **0.178** | **0.91** |
| filtered preview | 0.239 | 0.86 |
| hard preview | 0.381 | 0.77 |

**How to read these:**

- **Run-to-run agreement.** The control is FF1's representation re-shown in the PS1 session. It reproduces job 172 within 0.002 along the arc and 0.017 in time overall, so the FF1→PS1 differences are real.
- **Where PS1 helps.** On the deck strips, where FF1's far arc crawls, PS1 cuts the along-arc and per-point temporal variation by about a third, and gaps from 1.3 % to 0.2 %.
- **Where it does not.** On the chamfer arc, FF1's segments stand 1.5 cm proud and read steady at 1.44× the band's true coverage. PS1 reads 0.82× there and is slightly less steady (temporal CV 0.103 vs 0.077).
- **Space-time plot.** In `analysis/kymograph_far_and_mid_arc.png` each ring point is a column and each frame a row; an orange bar marks the chamfer arc.
  - FF1 and the control show dark/bright blotches on the deck strips that change from frame to frame: the crawling dashes. On the chamfer arc they show a steady bright block: the proud segments at 1.44× coverage.
  - PS1 is a near-even grey slightly below true coverage, with fine vertical streaks and one lighter patch at the lower left, and no drifting blotches.
  - The hard-edged decal looks like FF1 without the bright block.
- **The filtering makes the difference.** The hard-edged decal is the same decal and technique, and it is worse than the geometry. Changing to a decal did not reduce the breakup; the box filter did.
- **The noise estimate.** PS1's overall far-arc along-arc variation (0.200) is close to the noise estimate for its contrast (about 0.18). FF1's (0.310) is about twice its own (about 0.15).
- **Frame-to-frame change moves little** (0.110 → 0.102), because TSR already smooths successive frames. The crawl is slower than one frame; it shows in the per-point temporal CV and in the space-time plot.

**Visuals** (all crops of original pixels; enlargements nearest-neighbour):

- `board/ps1-board-far-settled.png`: the far arc ×3 for FF1, PS1, the control, both previews and the no-ring frame.
- `board/ps1-board-far-moving.png`: frames 0, 18, 36, 54 and 71, FF1 vs PS1, ×2.
- At 1:1, FF1's far arc on the deck strips is a chain of dashes and gaps. PS1's is a faint continuous line that thins toward 45 m.

## 5. Near view, overhead and colour

**Near-ring gameplay view** (settled actual PIE frame 2.4 m outside the ring, eye height; `board/ps1-board-near.png`):

- The band's central half (16 band points, 755 samples) has sRGB medians FF1 **(117.8, 95.5, 58.3)** and PS1 **(116.9, 95.0, 57.7)**, on deck (63.0, 66.1, 76.6).
- Measured edge-to-edge width over projected width: FF1 1.018, PS1 1.030, on bands 42–64 px wide (`analysis/near_colour.json`).
- The paint reads as the same thin, flat, matte band, with no raised edge and no glow. No colour tuning was done.

**Matched overhead.** FF1's own editor cameras `overhead-reference` and `pad-ring` were used, same camera in both runs and in the reference orientation (`board/ps1-board-overhead.png`).

- The ring is the same clean circle in the same place, with the same colour and width.
- At native pixels PS1's band edges are slightly smoother; the geometry's edge staircase is gone.
- Nothing else in the frames changed.

**PIE readout (job 178):**

- ring segment components visible: 0 of 96;
- one decal actor: material `M_PS1_PadRingDecal`, size (10, 1950, 1950), fade 0, at (17232, 4525, 385), rotation (0, −90, 0).

## 6. Lifecycle and reversibility (real engine, jobs 176–177)

**Job 176** (after job 175, which ran no step; section 9):

1. `base-fingerprint`: FF1 loaded alone, first in its process. 3256 actors, 3283 in-game components, 0 decal components.
2. `copy`, then `copy-verify` in a new process: 3256/3256 actors identical, receipt `created`.
3. `material` created the new material (the tool never overwrites); `material-again` found it already created and verified.

**Job 177:**

| Step (own process) | Result |
|---|---|
| plan-check | preflight clean |
| apply + save | applied-verified → `8706F959…`; receipt `applied` with the 96 captured visibilities |
| verify-applied (reload) | **97 planned changes (96 suppressed + 1 decal), 0 missing, 0 unexpected**; 3160 actors identical; editor-only components 18 → 20 (the decal's arrow and sprite) |
| repeat | already-applied-verified; **map and material byte-identical** |
| revert + save | reverted-verified → `B1278E75…` (decal removed, 96 visibilities restored) |
| verify-reverted (reload) | **0 differences from FF1**, actor for actor and component for component (a save re-serialises, so the bytes differ from the copy) |
| re-apply + save | applied-verified → `4AC42632…` |
| verify-final | 97 planned, 0 missing, 0 unexpected |

**Receipt** `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_PaintStability1.json` (`FADED192…`): created `2F0E2B87` → applied `8706F959` → reverted `B1278E75` → applied `4AC42632`.

- The state is current: the map equals the last applied bytes, and the material hash matches the receipt.
- The capture run (job 178) left both files byte-identical.
- Every commandlet exits 1 because of the pre-existing startup ensure, as in FF1; each step's own status was `complete`.

**Before the engine run**, the lifecycle tool was exercised against a file-backed stand-in for the editor API in my workspace: 29/29 checks. That first run left no saved output. The output kept in `tools-used/mock/`, with the driver and stand-in, is a re-run at 23:56 UTC with the same driver and the same tool version (`CD34DD7F…`). The checks covered:

- stale-target refusal (apply, revert and verify);
- a forged receipt with the decal moved;
- revert refused when the decal was moved or one segment re-shown;
- decal spawn, decal material and save failures;
- a plan with problems, a material in FF1's folder, and a base at other bytes;
- the corrected decal rotation.

## 7. Collision and gameplay

Only non-colliding visuals changed:

- the 96 segments keep NoCollision (only their visibility changed);
- the decal has no collision;
- every other actor, collision profile and component matches FF1 (section 6).

**One scripted actual PIE walk across the ring:** inside → outside, (17232, 6025) → (17232, 6825), the real `BP_IBCharacter_Infantry` driven by movement input. It **reached**, with the capsule centre at z 475.2 throughout, as on FF1 (job 172). The wall-clock durations (5.6 s vs 1.1 s) differ because the two editors rendered at different real frame rates under the fixed engine step.

The helicopter was not moved (it is identical in the fingerprint), so its clearance is FF1's.

## 8. Preservation and files

**Protected set:** 451 files, hashed natively by the job runner before and after every job (18 snapshots, `hashes/shared-*.json`, all identical to the first). They are:

- the 328 paths of `20260930-codex-forecourt-review/protected-current.json` (`21744674…`), stored here as the path list `protected-328.json`, reformatted with the same paths in the same order;
- FF1's map `181159BF…`, MI `93A7971E…` and receipt `F703F4A1…`, matching the brief in all 18 snapshots;
- FF1's evidence folder: its 120 files, excluding that folder's engine scratch UserDirs `user/` and `user-gui/`.

Also held: the live map `FAFFD601…` is unchanged; content written outside the disposable folder was 0 in every job; owned processes left were 0.

**Three save games differ from Codex's list.** 325 of the 328 match Codex's recorded hashes. The other three:

| File | Hash now | Written (UTC) |
|---|---|---|
| `Saved/SaveGames/IBCharacters.sav` | `D5B1873A…` | 21:51:03 |
| `Saved/SaveGames/IronBreach_Vault.sav` | `31FA7DAF…` | 21:52:05 |
| `Saved/SaveGames/IronBreach_XP.sav` | `C6A7C7B2…` | 21:52:06 |

- They were written after Codex's list (21:50:30) and before this task's first process (22:04:54).
- They already differed in the very first snapshot (before job 170) and are byte-identical in all 18.
- This task's PIE sessions ran in the isolated UserDir; their saves went to `20260930-claude-paintstability/user-gui/Saved/SaveGames`.
- I did not restore or touch them. Whoever wrote them should confirm.

**New evidence only**, in `Saved/GarrisonRestructure/20260930-claude-paintstability/`:

- The index is `run1/evidence.json` (`650F98FD…`), with every file's SHA256 including the 570 capture files and the exact tool versions each job used (`tools-used/`).
- Earlier evidence was not modified.
- My own first-pass analysis outputs, made before the no-ring reference existed, were moved into `analysis/first-pass-local-reference/` within this folder.

## 9. Engine health and job history

**Logs** (`run1/log_check.json`, `8BB9276A…`, 19 processes):

- all logs close normally; 0 access-violation, critical or fatal lines; 0 `LogPython: Error` lines;
- every process logs the known GameFeatureData startup ensure (19 ensure-type crash-reporter folders, all `IsEnsure=true`);
- the GUI runs also log the known `BP_Mech` compile errors, one CurrentVisualData NULL line, the pre-existing `M_AI_Foam` material compile warning, and a warning that `r.PostProcessAAQuality` does not exist;
- the two other error lines are the Python tracebacks of the preview failures below;
- the transient preview materials logged 39 compile-failure lines:
  - jobs 171 and 172 (1 and 4): partly built materials — decal domain set, then the build stopped;
  - job 173 (32): no Translucent blend mode;
  - job 174 (2): the domain was set before the blend mode;
- the saved PS1 material logged 0.

**Job history:**

| Job | What | Outcome |
|---|---|---|
| 170 | read-only probe of FF1 | done |
| 171 | cause A/B + FF1 captures | **superseded**: the floor probe hit the pawn's own capsule, so the camera bounced (51 of 72 frames 1–2.5 m too high); its decal preview also stopped (`DecalBlendMode` is protected from Python) |
| 172 | the same, corrected: the FF1 BEFORE run | done; its own decal preview stopped (`CustomInput` takes no constructor arguments from Python) |
| 173 | transient decal preview | **did not run**: `BeginDeferredActorSpawnFromClass` is not exposed to Python, and with Substrate on the decal needs Blend Mode Translucent |
| 174 | the preview, corrected | done |
| 175 | copy + material | **no step ran**: the job helper was named `PS`, which PowerShell resolves to its Get-Process alias; renamed `PStage` |
| 176 | copy + material | done |
| 177 | lifecycle | done |
| 178 | PS1 AFTER captures | done |

`tools-used/` holds exact copies of every tool version each job ran.

- The job logs print the hashes of the check script, decal module and probe versions; the copies match them.
- The job library's versions come from my own record and reproduce the live library's hash: c381bbbb → b94bfeb3 (`IB_PS_ONLY` and `IB_GARRISON_PLAN` added to its clean-up list) → 481f63f0 (the `PStage` rename) → 5b406227 (`IB_PS_EXTRA` added). The saved material's graph equals job 174's transient one, except that the blend mode is now set before the domain.

## 10. Remaining limitations

1. **The far line is faint and a little short.** At 35–45 m the band is physically 0.34–0.98 px tall on this path (mean 0.51). PS1 draws it as a faint, continuous line at 0.93× (deck strips) and 0.82× (chamfer arc) of its true coverage. The filter is designed for 1.0×; the shortfall is measured but not explained (possibly TSR's handling of low-contrast sub-pixel detail, or the surface's contrast under translucent paint). FF1's far line read stronger only where its segments stood 1.5 cm proud. Whether PS1's far line is visible enough is a visual judgement for Codex.
2. **The far arc is not perfectly still.** Its residual variation (along-arc 0.200, per-point temporal 0.155) is close to the noise estimate, not zero: TSR still reconstructs a half-pixel line from jittered samples.
3. **On the chamfer arc PS1 is less steady than FF1.** FF1's segments there stand 1.5 cm proud and read steady at 1.44× the band's true coverage (temporal CV 0.077). PS1 reads 0.82× and is slightly less steady (0.103). Matching FF1 there would need more coverage than the painted band has (a raised or thicker line), which the brief rules out.
4. **Mid-range texture shows through.** In the resolvable 25–35 m band PS1 is as stable over time as the geometry (temporal CV 0.052 vs 0.056–0.062), but its contrast varies a little more along the arc (0.087 vs 0.065–0.068). Where the band is only 1–2 px, the translucent paint lets the deck's texture show through.
5. **The decal paints what is in its box.** It paints anything inside the 40 cm annulus within ±10 cm of the deck top, for example a character's feet or an object resting on the ring, including vertical faces there (as stretched paint). It has no collision.
6. **The hidden segments remain.** The 96 segment actors stay in the level, hidden, for exact reversibility. A later integration would delete them or keep them hidden.
7. **Scope of the evidence.** The measurement method is new to this task (fitted camera model, noise estimate about 0.18 on the far arc). It covers one path, one camera direction and one lighting state. The evidence is scripted frames, not a manual playtest or a real-time video. The frames show the game's own subtitles, outside the analysed rows.
8. **Straight lines still shimmer** at a distance (see below).

**Could the approach later fix the straight-line shimmer?** In principle, yes. A straight marking is simpler than the ring: its coverage is a box-filtered distance to a segment. Drawing marking groups with such decals (or giving the painted meshes a material with the same footprint filter) would make distant lines fade instead of crawl.

It is not a drop-in change, so I converted nothing:

- the 91 generated markings and the forecourt's lines are separate proud meshes;
- each would need per-group decals or a distance-field texture with filtered lookups;
- a downward decal would streak any vertical face inside its box (curbs, fascia);
- translucent paint shows the deck's texture, as in item 4.

## 11. Paths

- **Candidate:** `Content/_GarrisonPreview_Disposable/CarrowGateGarrison_PaintStability1.umap` (`4AC42632…`).
- **Material:** `Content/_GarrisonPreview_Disposable/PaintStability1_Materials/M_PS1_PadRingDecal.uasset` (`4F6A2A1A…`).
- **Receipt:** `Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__CarrowGateGarrison_PaintStability1.json` (`FADED192…`).
- **Tools:**
  - `Scripts/ib_garrison_ring_stability.py` (lifecycle, `CD34DD7F…`)
  - `Scripts/ib_garrison_ring_decal.py` (material graph, `4E730D8F…`)
  - `Scripts/ib_garrison_ring_plan.py` (plan, `622F36C8…`)
  - `Scripts/ib_garrison_ring_check.py` (captures, `1F8FD4B6…`)
  - `Saved/zz_job/paint_lib.ps1` and the jobs `Saved/zz_job/running/170…178`
- **Evidence:** `Saved/GarrisonRestructure/20260930-claude-paintstability/`:
  - `plan/ps1_plan.json`, `probe/`, `run1/` (step reports, `evidence.json`, `log_check.json`)
  - `capture-ff1-r2/` (FF1 before + cause A/B)
  - `capture-ff1-preview-r2/` (transient previews)
  - `capture-ps1/` (PS1 after, no-ring reference, FF1 control)
  - `analysis/` (metrics incl. the deck-piece split, camera fit, space-time plot, clip, frames)
  - `board/`, `tools-used/`, `hashes/`, `backup/`
- **Superseded runs, kept as captured:** `capture-ff1/` (job 171) and `capture-ff1-preview/` (job 173).

This pass does not mark the garrison complete; it still needs final visual and functional assessment before live integration. Stopped for Codex review.
