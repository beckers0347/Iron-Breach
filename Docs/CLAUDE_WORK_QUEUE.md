# Iron Breach — Codex and Claude work queue

Updated September 30, 2026 UTC from the user's instructions and supplied reference. Current check interval: 15 minutes.

## Working arrangement

Claude handles heavy coding, implementation and analysis. Codex coordinates, reviews results, builds and checks the game. After sending Claude a task and verifying delivery, Codex ends its turn and checks back every 15 minutes. Do not repeatedly poll or duplicate Claude's implementation.

## 1. Finish the current work

First check Claude's current conversation and latest result. Complete and verify the work it is already updating before starting the next stage. Prior menu handoff and result are in `CLAUDE_MENU_REDESIGN_HANDOFF.md` and `CLAUDE_MENU_REDESIGN_RESULT.md`; inspect current files and logs rather than assuming the earlier build state still applies.

## 2. Restructure the garrison to the earlier picture

Explicitly requested by the user on September 18: once Claude finishes the current work, both agents should restructure the garrison to match the picture created earlier.

- Reference CONFIRMED: the user reattached the requested overhead concept. Unchanged durable copy: `References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`. Use this image directly; the missing-image blocker is resolved. See `CLAUDE_GARRISON_REFERENCE_HANDOFF_2026-09-23.md` and the fresh audit/captures documented in `CLAUDE_GARRISON_BASELINE_2026-09-23.md`.
- Preserve the user's earlier instruction to leave the actual rear hangar building for them; reserve its place and develop its surroundings.
- Review the current garrison map and `GARRISON_PLAYTEST_PUNCHLIST.md`, then give Claude a concrete implementation brief grounded in the reference.
- Claude owns the heavy layout/implementation work. Codex checks changes in Unreal and compares in-game screenshots with the reference.
- Preserve working spawn/deployment/return paths, collision, navigation and mission interactions as the environment is restructured. Review and test any affected behavior.
- Keep existing unrelated edits. No commit or push was requested.

Continue the 15-minute management cycle through this second stage; do not mark all authorized work complete after the menu pass alone.
