# Garrison reference and first layout pass

The user has now supplied the exact overhead concept requested in this conversation. The missing-reference blocker is resolved. Inspect the image itself before implementation:

`D:/Unreal Games/IronBreach/References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png`

This is an unchanged copy of the user's attachment, SHA256 `33491BF32E6AFEBE7BDB81A06083529A0F5F7F2C17619A6F8925B58939FA5A39`. The reference is an oblique aerial illustration, not a surveyed orthographic plan. Do not interpret pixel distances as world units.

Read `Docs/CLAUDE_GARRISON_BASELINE_2026-09-23.md` for the actual map audit, dependency notes and current comparison captures under `Saved/GarrisonRestructure/20260923/baseline-shots/`. Its historical missing-image section is superseded by this handoff. User explicitly asked Codex to prepare this while you handled menus and then said to get the garrison looking like the picture.

## What to match

- An organized coastal compound with a broad rear platform and a clear central road running from the rear forecourt straight out to the front landing platform.
- Several low, substantial service buildings arranged to either side of the rear forecourt, with service lanes and deliberate space between them. Avoid scattering isolated concrete boxes across empty ground.
- A secondary platform projecting to image-left halfway forward, with a control/watch tower and a low operations building, joined directly to the central route.
- A large chamfered/octagonal landing platform at the front, connected through a narrower neck, with its circular landing marking and a clear approach.
- A long narrow dock running along image-right, parallel to the central route, with the ship berth on its outside. Reuse existing suitable ship assets if available; preserve the berth if an exact asset is unavailable.
- Continuous seawall foundations, coherent platform edges, rails/bollards, readable road and safety markings, and restrained service details. Behind the compound, a road enters through rocky, wooded land. Later dressing should reinforce this coastal military setting.

**The rear hangar is a reserved footprint, not a building to construct in this task.** The user's earlier explicit instruction was to build it themselves later. Leave the correctly scaled site and usable forecourt/approach ready for it. Do not recreate the missing BP_Mech or invent new gameplay to populate the concept. Reuse suitable existing aircraft/ship/props where present; document unavailable exact-art elements honestly.

## Bounded next task

Prepare the first executable layout pass for Codex to review and run in Unreal. You own the heavy spatial analysis and implementation code; Codex owns engine execution, comparison and gameplay verification.

1. Inspect the confirmed reference and all four fresh baseline views. Read existing environment scripts and available actor/asset evidence. Map the reference's major shapes onto the current garrison coordinates and scale using known existing actors, rather than assuming the screenshot's orientation equals world north. Give a concise explanation of the alignment and dimensions.
2. Author narrowly scoped Unreal Python tooling for this layout in `Scripts/`, following the existing project patterns. It should first inventory relevant actor labels, paths, transforms, bounds, assets and mission references without changing anything. If the current evidence is insufficient to identify building groups and platforms safely, supply that read-only inventory step and the concrete transformation plan; explicitly identify what Codex must run before an apply pass can be completed. Do not guess selectors or claim an untested script ran.
3. Where selectors and scale are evidence-backed, prepare an explicit opt-in apply mode for the first structural pass: platform/route relationships, building placement, hangar reserve, left control area, front pad and right berth. Keep run-created actors identifiable and repeated runs controlled. Default execution must be read-only. Validate targets before applying; do not clear/delete all existing level actors or blindly overwrite shared assets. Save only the intended map/new task-owned assets when Codex explicitly invokes the reviewed apply mode.
4. Preserve the same playable map identity, spawn access, weapon rack, doors, mission directors/spawner and their configured references, existing travel/return behavior and unrelated/Caryatid work. Existing hidden water actors may carry collision; do not delete them because they are hidden. Do not restore old whole-map backups over current work. Report any conflict that needs a specific resolution.
5. Include a repeatable aerial comparison camera aligned approximately to the reference, plus useful ground-level inspection views. Defer small dressing until the layout is reviewable; the first pass must improve the overall arrangement rather than merely repaint unchanged boxes.

Write `Docs/CLAUDE_GARRISON_LAYOUT_RESULT_2026-09-23.md` with the intended layout, changed files, exact inventory/apply/capture invocation, expected outputs, preserved anchors, limitations and the next focused checks. Do not launch Unreal/builds, manipulate running processes, touch live saves, run git/lock operations, commit or push. Do not modify menu/network/progression code for this task. Stop when the bounded pass is ready for Codex's review; no claim of visual or gameplay verification without actual evidence.

Codex will review tooling, make a current-map backup before the first approved apply run, inspect before/after aerial and ground views, and check affected collision/navigation, spawn/interactions and deployment/return. The full garrison is not complete until those checks and reference comparisons pass.
