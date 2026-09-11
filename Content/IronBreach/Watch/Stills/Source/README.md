# Watch recon sources

These PNGs are captures of the actual project levels, without UI or generated imagery.
They are 1280 x 720; no level package was saved by the capture tool.

| Image | Level |
|---|---|
| T_Recon_CarrowGate.png | /Game/LevelPrototyping/CarrowGateGarrison |
| T_Recon_Plains.png | /Game/Lvl_Plains |
| T_Recon_FiringLine.png | /Game/FirstPerson/Lvl_FirstPerson |

`Scripts/ib_capture_watch_stills.py` documents the camera positions. Launch it in a full
editor process with `IB_RECON_SHOT` set to the desired shot. The script waits for editor
frames and uses Unreal's screenshot API; a render commandlet cannot produce these captures.
Copy a reviewed capture from `Saved/WatchPolish/recon/` to its filename here, then run
`Scripts/ib_import_watch_stills.py` through the Python commandlet to rebuild the texture.

The mission card loads these through `FIBDestination::ReconStill` in `IBWatchTypes.cpp`.
An existing destination registry asset still takes precedence over the built-in rows.
