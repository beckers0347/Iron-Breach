# Claude task: focused two-process mech menu verification

September 21, 2026. Project D:/Unreal Games/IronBreach.

## Objective
The recent mech menu fix uses replicated HullOccupancy / SeatOccupancy and pawn PlayerStates instead of remote-invalid Controller reads. Codex has reviewed/built this but host-only checks cannot prove it. Supply the smallest practical opt-in development-only check and exact run procedure for a real listen host plus one connected client (two human PlayerControllers) on this machine. Codex will build, launch and inspect the results at the next check. You handle the implementation/static analysis. Do not launch/build anything yourself.

## Required evidence
1. Prove the second process actually joined and is a remote client, with two distinct human PlayerStates (not an AI substitute or two standalone worlds). Account for current Steam/LAN/IP-passthrough setup; do not modify project network configuration to make a test pass.
2. Drive real existing boarding/crew-swap/disembark APIs against the actual mech and gunner seat. Avoid adding gameplay bypasses or setting replicated occupancy directly. No synthetic expected result copied from the same display helper being tested.
3. On the client, open the actual Mech menu and check what it renders: fixed HULL / GUNNER SEAT captions, correct distinct occupant names; then names exchange after the two-human ServerRequestCrewSwap -> PerformPossessionSwap path. Remote roles intentionally render blank when not knowable; do not invent driver/gunner labels. Do not confuse this with legacy PerformRoleSwap (roles exchange, names do not).
4. Gunner departure while a human remains in hull should show the actual AI backfill, AI CO-PILOT. For last-human departure, establish expected behavior by reading the actual code and report observed state honestly; do not change gameplay to force EMPTY. Cover an empty frame when one genuinely exists.
5. Use bounded readiness checks, explicit PASS/FAIL/TIMEOUT and COMPLETE logs, and a small number of deterministic screenshots with absolute output paths or paths under Saved. Include whether missing human operative identities prevent meaningful name coverage, rather than guessing them.

## Isolation and scope
- Prefer existing dev commands/hooks; add only the focused support necessary. Keep automatic behavior strictly opt-in and out of Shipping/Test builds. No generic QA framework, gameplay behavior changes, networking config changes, or real progression writes. Use isolated test saves/directories if needed; document supported exact args rather than inventing an isolation flag. Do not overwrite or restore the user's live saves. No source/content edits outside this check and unavoidable dev-only hooks without explaining necessity.
- If current public APIs or connection setup block a trustworthy automated check, deliver the concrete blocker and smallest supported procedure rather than fabricating a PASS or expanding scope.
- No builds, process control, git operations, lock cleanup, commits/push, garrison edits, or unrelated/Caryatid changes. Preserve single-click Character, tab split and fullscreen Watch.

## XP check scope
The separate XP test lifetime/watchdog correction has already been implemented in IBMenuXPHeaderCheck.cpp. Do not repeat or rewrite that work. This handoff will only be assigned after Codex verifies the corrected XP run. Preserve the existing production event subscriptions. Carry the lesson into any timer-based checks: retain a strong local state copy before clearing a callback's own timer, and ensure stale callbacks cannot interfere with later runs.
## Deliverable
Docs/CLAUDE_MENU_CREW_QA_RESULT_2026-09-21.md: changed files, exact host/client launch arguments and connection order, expected assertions and image paths, timeout/cleanup procedure for Codex-owned processes, isolation guarantees and honest limits. Do not claim execution. Stop for review.

## Later work (not this task)
Character preview still uses a white placeholder; broad visual fidelity remains unfinished. Garrison waits for the exact generated overhead concept, requested from the user. Do not implement layout from text-only rear-hangar / forward-pad / right-dock notes.


## Codex verification before assignment
The corrected XP test passed on September21 at03:45UTC: four DeploymentCheck PASS and nine XPHeader PASS, zero check FAIL/SKIP, COMPLETE9/0. Log Saved/ReferenceArtPass/xpheader-crashfix-20260921.log. The crash fix builds successfully; no XP changes are requested in this task. Codex stopped only its owned QA game17752 and its associated crash monitor after completion.

