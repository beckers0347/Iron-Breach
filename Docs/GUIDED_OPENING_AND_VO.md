# Guided opening + NPC voice-over (M1)

Added 2026-10-02. C++ in `Source/IronBreach/Missions/M1Landfall/`.

## Voice-over

`FDialogueLine` has a new optional `VoiceSound` (USoundBase). If empty, the line's voice is
found by file name with no wiring:

    /Game/IronBreach/Audio/VO/M1/<ActTag>_L<NNN>      e.g. A1_L003

| ActTag | Source |
|---|---|
| A1..A5 | Act I..V director, NNN = 0-based line index in `Beats` |
| GA | guide-route waypoint arrival lines (NNN = waypoint index) |
| GC | guide-route call-outs (NNN = call-out index) |

Playback: Rhodes/Bricks/Static/Vance/Achterberg lines play in 3D from the actor tagged
`VO_Rhodes` / `VO_Bricks` / `VO_Static` / `VO_Vance` / `VO_Achterberg` (nearest to the
player if several). Player / Idris / Comms / narration play 2D. A line's hold time becomes
`max(HoldDuration, clip length)`, so subtitles and the next line wait for the voice. No
sound found = old subtitle-only behaviour. Set `LogIronBreach` to Verbose to see `[VO]`
lines.

`ib_setup_guided_opening.py` adds the VO_ tags to the NPC actors.

## Guide route (drag the player along)

`AIBGuideRoute`: a lead NPC walks `Waypoints` (nav-mesh pathing, ground-snapped), squad
`Followers` trail it, and it waits for the player (`LeashDistanceCm`, per-waypoint
`WaitForPlayerRadius`), with call-out lines while waiting. Events: `OnWaypointReached(index,
tag)`, `OnRouteComplete`. Starts via `StartAfterAct1`, `bAutoStart`, or `StartRoute()`.

The NPC's ABP needs Speed fed from `Get Owning Actor -> Get Velocity -> Vector Length`;
the route keeps `ComponentVelocity` updated so the Idle/Walk blend works.

v1 limits: authority/host only (co-op clients see NPCs stationary); the HUD shows one
beat provider at a time, so call-outs can be briefly hidden while an Act director's line
is on screen.
