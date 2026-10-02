# Focused menu integration fixes

Codex reviewed CLAUDE_MENU_INTEGRATION_REVIEW_2026-09-20.md against current source and ran the integrated game QA. Please implement the four bounded corrections below, preserving current menu design, accepted navigation, and later Caryatid changes.

## Confirmed corrections

1. **Live XP header (X1):** subscribe the visible menu header to the owning player state's OnOperativeXPChanged. Refresh without reopening. Handle repeated opens, closes, teardown and player-state replacement without duplicate/stale delegate bindings. Preserve replicated XP and existing GetLevelBounds behavior.
2. **Mech crew display (M1/M4):** remote clients cannot read the four unreplicated controller fields used by IBMechScreen. Correct own-frame selection, crew identity and occupancy/status using data clients actually receive. Simply replicating PlayerController pointers is insufficient because other players' controllers are not generally relevant to a client. Prefer existing replicated PlayerStates on hull and gunner-seat pawns where those reliably represent physical stations; otherwise introduce the smallest public replicated crew view needed. Distinguish physical HULL / GUNNER SEAT from swappable DRIVER / GUNNER roles. Show roles only when authoritatively known. Preserve boarding, role swap and parked-pawn behavior; avoid a gameplay refactor.
3. **Honest Concord status (M2):** absent or unconfigured Concord must not display LINKED / HEAVY WEAPONS CLEAR merely because AreWeaponsSafetyLocked returns false. Show accurate unavailable/unconfigured/known live states. A small read-only configuration accessor is acceptable; do not change gameplay tuning or weapon-lock behavior.
4. **Missions active strip (Q1):** exclude Bastion from both the live strip and its click/selection path, consistently with the page's existing eligibility rules.

## Validation and scope

- Current Development Editor build succeeded (447.71s). Codex's fresh run: Saved/ReferenceArtPass/qa-review-20260920.log. MenuFlow COMPLETE: 119 passed, 0 failed; MenuConsistency: 22 PASS, 0 FAIL; DeploymentCheck: four PASS and COMPLETE. Screenshots in Saved/MenuConsistency/after and Saved/MenuFlow/after are dated September 20. Character single-click and separate Personal/Director cycles work; Watch fills both 1280x720 and 1600x900. Six squad cards fit the inspected 1600x900 screenshot; S3 is not a confirmed clipping defect.
- These standalone checks do not verify remote-client crew replication. Document a precise two-client follow-up procedure and any unverified cases. Do not claim runtime tests you did not perform. Codex will rebuild and perform focused runtime checks after your handoff.
- Defer latent M3, S1, Q2/performance changes and authored fireteam-capacity redesign. No broad UI redesign in this batch. The log also reports the existing infantry CurrentVisualData-null configuration error; record it, do not expand into Blueprint configuration here.
- Do not build, launch/kill editor or game processes, alter git/locks, commit, push, pull or merge. Preserve unrelated source/content changes. No garrison layout edits: its exact reference remains unconfirmed.
- Save concise results to Docs/CLAUDE_MENU_FIX_RESULT_2026-09-20.md with changed files, rationale, static checks and remaining runtime checks. Then stop for Codex review.
