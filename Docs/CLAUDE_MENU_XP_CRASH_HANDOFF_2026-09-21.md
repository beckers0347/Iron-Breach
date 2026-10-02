# Claude task: fix XP-header regression check crash

September 21, 2026. This takes priority over all later menu/crew work.

## Fresh evidence from Codex
- Your two-file autorun change builds: Saved/ReferenceArtPass/build-xpheader-autorun-20260921.log, Result Succeeded,14.82s,5actions.
- Ran exactly your one-process post-deployment flag/ExecCmds sequence, hidden. PID28008.
- Saved/ReferenceArtPass/xpheader-autorun-20260921.log has four DeploymentCheck PASS and COMPLETE at02:57:55UTC.
- Then the process CRASHED and exited before ANY XPHeader PASS/COMPLETE. At02:57:59UTC EXCEPTION_ACCESS_VIOLATION reading0xffffffffffffffff.
- First project stack frame: IBMenuXPHeaderCheck::RunSequence lambda_3, Source/IronBreach/UI/IBMenuXPHeaderCheck.cpp:193, Run->Original = Line->GetText(). Prior line assigns Run->Probe = Line.
- Full crash evidence: Saved/Crashes/UECC-Windows-52C23DF1444D7B2DF657F3BFDD34E1ED_0000/CrashContext.runtime-xml and colocated log/dump if needed. Process already exited; no process control needed.
- Save hashes were captured BEFORE this full deployment+XP attempt in Saved/ReferenceArtPass/xpheader-autorun-save-before.json. XP and Ledger unchanged. IBCharacters and Vault changed during this run (existing deployment selects/loads an operative); do not claim that the whole run is non-saving. No restores or progression edits by Codex. Keep XP probe itself non-saving.

## Required correction
Diagnose the actual object/lambda/timer lifetime behind the crash. One specific area to review is the polling callback clearing its own timer with ClearTimer(Run->Wait), then continuing to use its captured Run and passing it by reference into RunSequence; ensure state is strongly owned through any delegate destruction/reallocation. Also inspect the widget traversal and FText copy. This is a hypothesis to verify, not an instruction to assume the cause. Add only focused guards/ownership fixes that preserve a meaningful assertion; do not turn a failed or skipped run into a PASS.

Also fix the overlapping-run cleanup flaw: the core watchdog remains scheduled after Complete resets RunStartedAt. A new run before the old20s watchdog fires can have its guard reset or probe restored by the old run. Cancel the run's own watchdog on completion or use run identity so stale callbacks cannot affect later runs. Remove the stale source comment suggesting FrontendStyleCheck startup.

Keep the post-deployment flag, explicit9PASS/0FAIL completion target and mutually exclusive UI suites. No general framework. Preserve production XP/identity binding fix; no normal menu/gameplay changes unless you prove they caused this crash and document necessity. No builds, test process launches/control, git/lock operations, save changes/restores, asset edits or garrison work.

Deliver Docs/CLAUDE_MENU_XP_CRASH_RESULT_2026-09-21.md with actual cause, exact changed files, how ownership/cleanup works, expected launch/check output, and honest unexecuted limits. Do not claim build/runtime success. Stop for Codex to rebuild and rerun next scheduled check.

Docs/CLAUDE_MENU_CREW_QA_HANDOFF_2026-09-21.md was prepared as a LATER task but has NOT been assigned. Do not start it until this XP check is verified. Garrison still awaits the exact reference image requested from the user.
