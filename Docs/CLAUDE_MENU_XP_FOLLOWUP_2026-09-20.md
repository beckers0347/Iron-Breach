# XP level-up follow-up and focused validation

The four-fix result was reviewed. The current code still has one concrete live-header defect. Please handle this bounded follow-up, with the build barrier below.

## Build barrier

Codex completed Development Editor compilation of your eight-file change. Saved/ReferenceArtPass/build-fixes-20260920.log reports Result: Succeeded, Total execution time: 352.58 seconds, all 29 actions complete. The build barrier is satisfied; implementation may proceed. Do not start another build or control any processes. Preserve all unrelated edits.

## Remaining XP defect

IBXPSubsystem.cpp:159 broadcasts OnXPAwarded BEFORE OnXPLevelUp at line 163. AIBPlayerState::HandleXPAwarded calls SetOperativeXP, which broadcasts the new header's XP subscription immediately. Only afterward does HandleXPLevelUp call SetOperativeLevel; this broadcasts OnOperativeIdentityChanged, which the header does not subscribe to. Consequently the XP amount/bar updates but LV remains old until another award or reopening. The result document's assertion that XP alone refreshes the level is incorrect. On clients, replicated identity/XP arrival order also must not be assumed.

Fix this within IBMenuScreen's binding lifecycle: refresh on the existing identity/level event as well as XP, with the same unique binding, correct-old-state unbind, reopen/replacement and teardown guarantees. Preserve XP award order and gameplay/save behavior. Correct the stale comment claiming no client XP fraction exists.

Add a small opt-in regression check, following existing project check patterns, that actually observes the visible header during XP-before-level delivery, level-before-XP delivery, and reopening/rebinding. It must not write the user's real progression, roster, inventory or content; use isolated/transient test state and clean up/restore all injected state. Keep it focused, avoid a broad test framework or gameplay refactor. Document the precise command for Codex to run after rebuilding. If safe isolation cannot be established, explain the limitation instead of writing real save data.

## Mech validation procedure correction

The report conflates legacy PerformRoleSwap with the current two-human ServerRequestCrewSwap -> PerformPossessionSwap path. The latter actually exchanges pawn possession, seat bookkeeping and parked pawns (IBMech_Base.cpp:753 onward). Therefore physical station captions stay fixed but their occupant names should exchange on that path. In the legacy role-only swap, names stay and roles change. Correct the two-client procedure accordingly; do not change mech gameplay to match a mistaken test expectation. Also reflect existing AI backfill when specifying expected post-disembark occupancy.

Save results and final build-log outcome to Docs/CLAUDE_MENU_XP_FOLLOWUP_RESULT_2026-09-20.md, clearly distinguishing static review from runtime verification. No builds, process control, git/lock operations, commits, pushes, pulls or merges. No garrison edits. Stop after the handoff; Codex will rebuild and run the focused checks.
