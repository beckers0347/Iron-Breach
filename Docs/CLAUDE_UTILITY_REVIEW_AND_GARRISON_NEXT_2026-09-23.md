# Utility review and confirmed garrison reference

Codex review of `CLAUDE_MENU_UTILITY_FINISH_RESULT_2026-09-23.md`:

- Development Editor build PASSED, 16 actions, 46.70 seconds. Log: `Saved/ReferenceArtPass/build-utility-20260923.log`. This also compiles the latest crew diagnostic.
- Isolated 1280x720 and 1600x900 runs each passed all four DeploymentCheck assertions and all 16 MenuConsistency assertions, reaching COMPLETE for both. Logs: `Saved/UtilityMenuQA/run-20260923-reference/1280.log` and `1600.log`.
- Codex visually inspected the actual System, Settings, Squad and Friends PNGs at both sizes. System/Settings are readable and ordinary Squad shows all six seats. **Friends is not ready at EITHER size: the first seat is mostly off the left edge.** Assertions did not cover this geometry failure.
- Each run used a separate absolute UserDir with copy-only roster seeding. All four live save hashes and lengths matched before/after; evidence JSON is in that QA run directory. Only owned QA processes and their matching crash monitors were stopped after inspection.

## Fix this first

Inspect these actual screenshots directly:

`Saved/UtilityMenuQA/run-20260923-reference/1280/Saved/MenuConsistency/after/squad.png`

`Saved/UtilityMenuQA/run-20260923-reference/1280/Saved/MenuConsistency/after/friends.png`

Equivalent captures for the larger size are under `1600/Saved/MenuConsistency/after/` in the same run directory; the clipping reproduces there too.

The fixed 360-unit right padding in `UIBFriendsScreen::SetFlyoutOpen` pushes the fixed-width row beyond the left viewport edge when the flyout opens. At 1280x720 only a narrow right portion of the first card remains visible. Keep all SIX seats completely visible and reachable, in the existing order and slight V arrangement, alongside the separate flyout. The selected origin mark must remain visible. Adapt the row/card sizing or layout to the available space; do not mask the issue by clipping, deleting a seat, hiding the origin mark or reverting to the sixth seat underneath the flyout. Restore the ordinary full-size arrangement when the flyout closes. Preserve behavior and existing rest/hover/focus/selection treatments. No new test framework.

Record the narrow correction and changed files in `Docs/CLAUDE_MENU_UTILITY_FLYOUT_FIX_RESULT_2026-09-23.md`. Codex will rebuild and recheck both target sizes. Hover/keyboard focus and actual friends presence states were not established by these automated offline screenshots; do not claim they were.

## Then prepare the garrison pass

The user has now supplied the EXACT requested overhead concept. The image blocker is resolved. Read `Docs/CLAUDE_GARRISON_REFERENCE_HANDOFF_2026-09-23.md`, inspect its linked reference and all baseline views, and prepare the bounded first layout pass described there.

Do the heavy layout analysis and author the inventory/implementation tooling. Codex will execute it after review. Do not mutate/save any map or asset during this turn, and do not run the apply mode yourself. If the current audit lacks actor grouping details needed for evidence-backed transforms, author the specific read-only inventory step first and state precisely what information Codex needs to return; do not invent actor selectors.

Keep the rear hangar footprint reserved for the user's later building. Preserve mission actors/references, spawn access, navigation/collision and deployment/return. No live saves, process/build operations, git/locks, commit or push. Stop once the correction and the bounded garrison preparation are ready; report both result-file paths honestly.
