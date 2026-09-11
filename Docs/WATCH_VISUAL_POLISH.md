# The Watch visual polish — 2026-09-08

This pass refines the existing command deck presentation. The planet projection and material
parameter contract, sector selection, proposal/host confirmation, and 2.4-second deployment
timeline are retained. No commits or pushes were made.

## Review status

The remaining checkpoint concern was investigated on resume and proved to be a false alarm
in the earlier image review. Full-resolution inspection of the original screenshot and a
fresh standalone tour show the leading card characters intact. Windows OCR independently
reads `FIRETEAM`, `1-8 OPERATORS`, and `OFF THE NET - DEPLOY TAKES YOU ALONE` in the original,
fresh orbit, and fresh return-to-orbit images. The complete DEPLOY button label was checked
visually (OCR only reads `DEPLO` with this widely spaced lettering).

No speculative clipping/layout change was made. The existing Watch source and successful
build were retained. The fresh 1600×900 tour again captured all ten views and reached the
garrison, with no Watch material errors, Slate warnings, asserts, or fatal errors in its log.
The corrected vignette has no hard band, and the orbit back-arrow renders correctly.

Fresh evidence is in `Saved/WatchPolish/resumed/`; log: `Saved/WatchPolish/tour-resumed.log`.
The test process launched for this verification was closed; the already-running game was
left alone. This resumed step changed documentation/evidence only. No new build, multiplayer
test, or performance capture was needed for an unchanged Watch implementation.

## Changes by file

| File | Change |
|---|---|
| `Scripts/ib_build_watch_materials.py` | Finer baked terrain and city networks; terrain normal shading; revised land, sea and ice; sheared cloud fronts, shadows and a broken hurricane; atmosphere and sunlight refinement. Rebuilds existing material graphs in place. |
| `Content/IronBreach/Watch/M_WatchMap.uasset`, `M_WatchPlanet.uasset` | Regenerated from that script. |
| `Source/IronBreach/UI/IBPlanetWidget.cpp` | Softer and fewer hex lines, layered diamond glow, constrained callout placement, bevels/seams/contact shadows on the deck, cosmetic drop shake and vignette. The shake uses the same camera for both pins and material projection. |
| `Source/IronBreach/UI/IBPaintKit.h` | A two-stop Slate gradient helper, used for deck depth and drop edges. |
| `Source/IronBreach/UI/IBWatchScreen.h/.cpp` | Chamfered native Slate mission card; condensed headings; 16:9 recon image and caption backing; darker board backdrop; a small HUD translation before the existing cut. Adds an explicit development-only screenshot tour. |
| `Source/IronBreach/UI/IBSectorBoardWidget.cpp` | Dark teal land, restrained cyan grid/coastline glow, and clipping to the board frame. Paint helpers have their own named namespace. |
| `Source/IronBreach/UI/IBStyleKit.h` | Opt-in `UseDisplayFace` helper using the engine's existing BoldCondensed font. |
| `Source/IronBreach/Online/IBWatchTypes.cpp` | Only adds recon texture soft references to the three deployable mission rows. |
| `Content/IronBreach/Watch/Stills/` | Three real level textures; original 1280×720 PNG captures and provenance in `Source/`. |
| `Scripts/ib_capture_watch_stills.py`, `ib_import_watch_stills.py` | Repeatable editor capture and texture import. Captures never save level packages. |

No changes were made by this pass to the Watch replicated state machine, player RPCs,
session travel, screen registry, or other owners' level/Blueprint content. Existing local
changes in those areas were present before this pass and were preserved.

## Reproduce

Close Unreal before rebuilding the editor target with `BUILD_IronBreach.bat`.
The material and import scripts run through `UnrealEditor-Cmd.exe <uproject>` with
`-run=pythonscript -script="<absolute script path>" -unattended -nopause -nosplash`.

For the expanded visual tour, launch the editor executable with the project and:

```text
/Game/FirstPerson/Lvl_MainMenu -game -windowed -ResX=1600 -ResY=900
-NoSplash -NoSound -NoSteam -IBWatch -IBWatchVisualShots
-ExecCmds="DisableAllScreenMessages"
```

Use `-IBWatchVisualShots` without `-IBWatchShots`. It selects a locked sector, visits the
range/plains cards, opens and closes the board, deploys through the existing button handler,
and captures the destination world. It is excluded from Shipping/Test behavior.
Screenshots are written to Unreal's project Saved directory under `Screenshots/WatchPolish/`.

The original screenshots and source files were preserved in `Saved/WatchPolish/before/`.
Reviewed final screenshots, build/material/import logs and timing evidence are under
`Saved/WatchPolish/`. That directory is local review evidence and is normally git-ignored.

## Validation

- `IronBreachEditor Win64 Development`: succeeded. The existing compiler/plugin/deprecation
  warnings remain; there were no compile errors. Log: `Saved/WatchPolish/build-final.log`.
- Material generation: succeeded with zero errors. The only warning was an existing missing
  StarterArmor material. Recon import: all three texture assets saved, zero errors.
- At 1600×900, the standalone tour exercised orbit, locked-sector card with disabled deployment,
  all three real recon thumbnails, board, settled return to orbit, and the existing drop/travel.
  The garrison world began play after the 2.4-second armed interval and has an arrival capture.
- The final review caught and corrected a missing orbit arrow glyph and Slate gradient stop
  orientation (which otherwise produced a hard vignette edge).
- No Watch material compile errors occurred in the game tour. Coast/pin projection code and
  sphere geometry remain unchanged; the new detail only affects shading.
- Performance capture: 3,300 Watch samples at 1600×900 on this machine measured **5.889 ms
  median / 7.531 ms p95** frame time, **4.51 ms median / 5.45 ms p95** GPU time. Five frames
  exceeded 16.667 ms at screenshot captures (maximum 597.994 ms); this is not a claim of
  hitch-free loading/capture. CSV and sample window are preserved in
  `Saved/WatchPolish/performance-final.csv` and `performance-summary.json`. The measurements
  precede the final gradient-direction and arrow-character correction.

## Screenshot comparison

| View | Before | After |
|---|---|---|
| Orbit | [Before](<D:/Unreal Games/IronBreach/Saved/WatchPolish/before/Screenshots/watch_orbit.png>) | [After](<D:/Unreal Games/IronBreach/Saved/WatchPolish/after/watch_orbit.png>) |
| Board | [Before](<D:/Unreal Games/IronBreach/Saved/WatchPolish/before/Screenshots/watch_board_open.png>) | [After](<D:/Unreal Games/IronBreach/Saved/WatchPolish/after/watch_board_open.png>) |
| Drop | [Before](<D:/Unreal Games/IronBreach/Saved/WatchPolish/before/Screenshots/watch_drop_mid.png>) | [After](<D:/Unreal Games/IronBreach/Saved/WatchPolish/after/watch_drop_mid.png>) |

Additional final captures: [locked sector](<D:/Unreal Games/IronBreach/Saved/WatchPolish/after/watch_locked.png>),
[range](<D:/Unreal Games/IronBreach/Saved/WatchPolish/after/watch_range.png>),
[plains](<D:/Unreal Games/IronBreach/Saved/WatchPolish/after/watch_plains.png>),
[return to orbit](<D:/Unreal Games/IronBreach/Saved/WatchPolish/after/watch_orbit_back.png>),
[arrival](<D:/Unreal Games/IronBreach/Saved/WatchPolish/after/watch_arrival.png>).

## Limits

The planet is still procedural; this pass does not replace it with photographic surface maps.
The recon thumbnails faithfully show the current levels: the firing line is a blockout, and
the plains overview includes the map's existing heavy haze/foliage rendering. Those level
art issues are outside this UI pass. Steam host/client co-op and a packaged build require
separate validation; the automated tour runs standalone.
