# Crew QA compile and startup logging correction — September 22, 2026

The follow-up has been reviewed and built once. Build FAILED; no runtime processes, save copies, or sandbox directories were started this check.

Evidence: Saved/ReferenceArtPass/build-crewqa-followup-20260922.log. Result Failed (OtherCompilationError), 24.03 s. IBDeploymentCheck.cpp compiled; IBMechCrewQACheck.cpp failed.

Please make only these bounded corrections:
1. IBMechCrewQACheck.cpp:246-249 declares const UNetDriver* Driver, but UE5.8 UNetDriver::LowLevelGetNetworkNumber() is non-const (Engine/Classes/Engine/NetDriver.h:1637). Compiler C2662 is the root error; C2100 and format-string C7595 follow. Use the appropriate non-const local pointer returned by World->GetNetDriver; no const_cast or engine edit. Keep FString lifetime/format arguments correct.
2. The NET diagnostic is currently below TwoHumans and WithPawn gates. Your launch procedure asks Codex to use that address before connecting the client, so that is circular. Emit driver/listen/url once on the settled host before waiting for the second player. Keep the existing readiness gates before boarding and avoid per-tick log spam.
3. Update the result with exactly what changed and any remaining launch caveat. Do not claim compiled/runtime success. If startup log cannot provide a usable client address, state how to read the confirmed port/bind evidence (wildcard bind is not a connect target).

Write Docs/CLAUDE_MENU_CREW_QA_BUILD_FIX_RESULT_2026-09-22.md when done. Preserve all previous behavior, tallies, UserDir isolation, XP/menu code, unrelated/Caryatid changes. No other implementation; no builds, running/stopping processes, save copies/writes, git/locks, assets, network config, or garrison layout changes. Codex will build once and run the focused isolated host/client check after completion.
