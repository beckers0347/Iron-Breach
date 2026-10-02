# Claude task: make the XP-header regression runnable after deployment

September 21, 2026. Project D:/Unreal Games/IronBreach.

## Verified by Codex
- Your three-file XP/identity subscription follow-up builds successfully. Saved/ReferenceArtPass/build-xpheader-20260921.log: Result Succeeded, 54.57 seconds.
- Current executable ran DeploymentCheck (4 PASS, COMPLETE) and ReferenceMenuCheck (26 PASS, COMPLETE), no check FAIL. Log: Saved/ReferenceArtPass/xpheader-20260921.log. Fresh screenshots in Saved/ReferenceMenus/after. Character and locked Missions inspected.
- XPHeaderCheck has NOT run yet. The hidden QA process had no targetable window; Codex stopped only its own PID 48968. No test process should be controlled by Claude.

## Concrete remaining test blocker
The documented initial ExecCmds sequence is unreliable: IB.FrontendStyleCheck later starts DeploymentCheck, which travels worlds. XPHeaderCheck polls a timer on its starting world. Travel can cancel it or overlap assertions. Direct-launching Carrow Gate is insufficient because LoadRoster explicitly invalidates ActiveCharacterId each run.

Implement a minimal opt-in development-only way to invoke IB.MenuXPHeaderCheck after DeploymentCheck COMPLETE on the final, settled world with an operative selected. Prefer a command-line flag such as -IBXPHeaderAfterDeploy in the existing IBDeploymentCheck.cpp completion hook. Do not run simultaneous UI test suites: for the XP run use only this new flag, with IB.DeploymentCheck in ExecCmds. Reject or clearly handle incompatible menu-check flags rather than silently overlapping them. Do not change ordinary gameplay/menu behavior. Keep the XP test non-saving: no synthetic XP awards, progression mutation, roster selection changes beyond existing deployment check, or save calls. Preserve its clear PASS/FAIL/COMPLETE reporting and clean binding lifecycle.

Review whether XPHeaderCheck can leave its text sentinel behind on early failure/world loss, and make only necessary small cleanup fixes. Do not add a general QA framework.

Deliver Docs/CLAUDE_MENU_XP_AUTORUN_RESULT_2026-09-21.md with exact files changed, the exact one-process launch arguments, expected completion/count, and any remaining limits. Do not claim execution. Codex will rebuild and run this. No builds, process control, git operations, lock cleanup, commits/push, unrelated code edits, or garrison layout changes.

## Next-stage context only
Remote two-client mech crew replication is still unverified. Menu visual fidelity is incomplete; the Character screenshot still shows the white placeholder body. These are later work, not scope for this small test-wiring task.
Garrison reference discussion was found in ChatGPT task 'Layout Feedback Writing': rear hangar reservation (user will build hangar later), forward landing pad, right dock. Actual generated reference image has not been recovered; do not implement its layout from this text alone.
