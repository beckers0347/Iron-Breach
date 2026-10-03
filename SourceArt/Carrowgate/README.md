# Carrowgate garrison buildings (Blender-built, same style as Barracks_02 / Hangar_04)

| Building | Code | Replaces (Tripo) | Doors (IBSensorDoor) |
|---|---|---|---|
| Armory | 03 | `Armory` | Vault (sliding), FrontHatch, RearHatch |
| Medical | 05 | `Medical` | DoorL/DoorR (bi-parting), SideHatch, RearHatch |
| Command | 06 | `Command` | Blast (sliding), SideHatch, RearHatch |
| MessHall | 07 | `Mess_Hall` | FrontL/FrontR (hinged pair), FrontHatch, RearHatch, RearRoll (sliding) |
| MainGate | 01 | `SM_MainGate_Tripo` + `BP_MainGateDoor` | GateL/GateR (bi-parting), TowerWHatch, TowerEHatch |

Regenerate everything (Blender 5.2, headless):

    "D:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b -P SourceArt/Carrowgate/_scripts/build_all.py -- "X:/IronBreach/SourceArt/Carrowgate" [Armory Medical ...]

Each `<Name>/` folder gets `SM_<Name>.fbx` (+ UCX hulls), `SK_<Name>_Door_<key>.fbx` (1 bone + 'open' animation),
`<Name>.json` (door pivots, sensor/blocker volumes, lights, box collision), and front/rear preview PNGs.

Place in Unreal (open the garrison level first, then run in the editor):

    py "X:/IronBreach/Scripts/ib_replace_garrison_buildings.py"

Env options: `IB_ONLY=Armory,Medical`, `IB_DRY_RUN=1`. Old Tripo actors are parked (hidden, no collision) in `_Replaced_<Name>`, never deleted.
Nothing is saved by the script. Re-running replaces the previous spawn (tag `IB_<Name>`).

Note: the scripted FBX import does not keep the UCX hulls on this engine build (also true for Barracks_02 / Hangar_04),
so the script writes the same hulls as box collision primitives instead.
