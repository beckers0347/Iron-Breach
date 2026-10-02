"""Garrison ground/collision probe. Read-only; changes nothing and saves nothing.

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script="Scripts/ib_probe_garrison_support.py"
    UnrealEditor.exe     <project> -ExecutePythonScript="Scripts/ib_probe_garrison_support.py"

Current-baseline revision (2026-09-30). The 09-30 commandlet run returned None
from every trace and could not read collision settings, because:
  * its probe points were hard-coded under the OLD folder buildings, none of
    which exist on the current map -- they sampled arbitrary deck, not "known
    ground under a building";
  * it read collision through get_editor_property('collision_enabled' ...),
    names that do not exist on StaticMeshComponent.
This version:
  * derives its points from the CURRENT map: open deck just outside each
    explicit building's door, the gate threshold, the land ramp, the lower
    apron, and two CONTROLS -- one over open water that should miss, one over
    the mainland city ground that should hit if traces work at all;
  * compares each trace with the height the mesh survey predicts there, when an
    inventory folder is supplied (IB_GARRISON_INVENTORY);
  * reads collision through the PrimitiveComponent getter METHODS;
  * decodes a HitResult with to_tuple(), then break_hit_result if present;
  * tries a second query form (line_trace_single_for_objects, WorldStatic) so a
    channel-mapping problem cannot masquerade as missing geometry;
  * states conclusions cautiously: a trace that finds nothing proves the trace
    found nothing -- not that there is no collision.

Environment:
    IB_GARRISON_OUT        output folder (default Saved/GarrisonRestructure/probe)
    IB_GARRISON_INVENTORY  optional inventory folder with support.json (predicted heights)
    IB_GARRISON_PLATFORM   platform label (default GarrisonPlatform_New)
    IB_PROBE_QUIT=1        quit the editor when done (for -ExecutePythonScript runs)
"""
import unreal, json, os, traceback, datetime, math, sys
from pathlib import Path

SCHEMA = "garrison-probe/2026-09-30"
LEVEL = "/Game/LevelPrototyping/CarrowGateGarrison"
PLATFORM_LABEL = os.environ.get("IB_GARRISON_PLATFORM", "GarrisonPlatform_New")
OUT = Path(os.environ.get("IB_GARRISON_OUT",
                          str(Path(unreal.Paths.project_saved_dir()) / "GarrisonRestructure/probe")))
INV = os.environ.get("IB_GARRISON_INVENTORY")

BUILDINGS = [("Medical", "Medical_DoorFrame"), ("Barracks", "Barracks_DoorFrame"),
             ("Armory", "Armory_DoorFrame"), ("Command", "Command_DoorFrame"),
             ("Mess_Hall", "Mess_Hall_DoorFrame"), ("SM_MainGate_Tripo", "BP_MainGateDoor")]
COLLISION_SUBJECTS = [PLATFORM_LABEL, "Medical", "Barracks", "Armory", "Command", "Mess_Hall",
                      "SM_MainGate_Tripo", "Water_Placeholder", "IB_Harbor_Surface", "CityGround_00",
                      "Cube", "Cube2", "Cube3", "Docks_Ship_Hull"]

report = {"schema": SCHEMA, "level": LEVEL, "steps": [], "errors": [], "probes": [],
          "started_utc": datetime.datetime.utcnow().isoformat() + "Z",
          "context": "commandlet" if "-run=pythonscript" in " ".join(sys.argv).lower()
          or "run=pythonscript" in str(unreal.SystemLibrary.get_command_line()).lower() else "editor"}


def say(line):
    unreal.log("SUPPORT PROBE: " + str(line))
    report["steps"].append(str(line))


def note_error(what):
    detail = traceback.format_exc()[-1200:]
    report["errors"].append({"what": what, "detail": detail})
    unreal.log_warning("SUPPORT PROBE: %s FAILED\n%s" % (what, detail))


def collision_of(component):
    out = {}
    for key, fn in (("enabled", lambda c: c.get_collision_enabled()),
                    ("profile", lambda c: c.get_collision_profile_name()),
                    ("object_type", lambda c: c.get_collision_object_type())):
        try:
            out[key] = str(fn(component))
        except Exception as error:
            out[key] = "unreadable: " + str(error).strip().splitlines()[-1][:120]
    for key, ch in (("visibility", "ECC_VISIBILITY"), ("pawn", "ECC_PAWN")):
        try:
            out["response_" + key] = str(component.get_collision_response_to_channel(
                getattr(unreal.CollisionChannel, ch)))
        except Exception as error:
            out["response_" + key] = "unreadable: " + str(error).strip().splitlines()[-1][:120]
    return out


unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
by_label = {}
for a in actors:
    try:
        by_label.setdefault(a.get_actor_label(), a)
    except Exception:
        pass

# --- 1. world --------------------------------------------------------------
world = None
for name, getter in (
        ("UnrealEditorSubsystem.get_editor_world",
         lambda: unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()),
        ("EditorLevelLibrary.get_editor_world", lambda: unreal.EditorLevelLibrary.get_editor_world())):
    try:
        world = getter()
        if world:
            say("world from %s -> %s (context %s)" % (name, world.get_name(), report["context"]))
            break
    except Exception:
        note_error("world from " + name)
report["world"] = world.get_name() if world else None

# --- 2. collision settings through supported getters -----------------------
report["collision"] = {}
for label in COLLISION_SUBJECTS:
    a = by_label.get(label)
    if a is None:
        report["collision"][label] = "not in level"
        continue
    try:
        comp = a.get_component_by_class(unreal.PrimitiveComponent)
        entry = collision_of(comp) if comp else {"component": None}
        if isinstance(a, unreal.StaticMeshActor):
            mesh = a.static_mesh_component.static_mesh
            if mesh:
                body = mesh.get_editor_property("body_setup")
                entry["body_setup"] = bool(body)
                if body:
                    entry["collision_trace_flag"] = str(body.get_editor_property("collision_trace_flag"))
                cc = mesh.get_editor_property("complex_collision_mesh")
                entry["complex_collision_mesh"] = cc.get_path_name() if cc else None
        try:
            entry["hidden_in_game"] = bool(a.get_editor_property("hidden"))
        except Exception:
            pass
        report["collision"][label] = entry
        say("  collision %-20s %s" % (label, entry))
    except Exception:
        note_error("collision of " + label)

# --- 3. probe points from the CURRENT map ----------------------------------
predicted = None
if INV:
    try:
        predicted = json.loads((Path(INV) / "support.json").read_text(encoding="utf-8"))
        if predicted.get("status") != "ok":
            predicted = None
    except Exception:
        note_error("reading predicted support from " + str(INV))


def predict(x, y):
    if not predicted:
        return None
    i = int(math.floor((x - predicted["x0"]) / predicted["step"]))
    j = int(math.floor((y - predicted["y0"]) / predicted["step"]))
    if 0 <= i < predicted["nx"] and 0 <= j < predicted["ny"]:
        return predicted["cells"][j][i]
    return None


PROBES = []
for building, door_label in BUILDINGS:
    b, d = by_label.get(building), by_label.get(door_label)
    if not b or not d:
        say("  no probe for %s: building or door missing" % building)
        continue
    bl, dl = b.get_actor_location(), d.get_actor_location()
    vx, vy = float(dl.x - bl.x), float(dl.y - bl.y)
    n = math.hypot(vx, vy) or 1.0
    # 6 m out from the door, away from the building's pivot: open deck in front
    # of the entrance, which is exactly the ground a moved deck must keep.
    PROBES.append(("outside %s door" % building, float(dl.x) + 600.0 * vx / n, float(dl.y) + 600.0 * vy / n, "hit"))
gate = by_label.get("SM_MainGate_Tripo")
if gate:
    g = gate.get_actor_location()
    PROBES.append(("land ramp mid", float(g.x) - 2100.0, float(g.y), "hit"))
PROBES += [("lower apron by trucks", 13000.0, -900.0, "hit"),
           ("control: open water", 21000.0, 1095.0, "miss"),
           ("control: city ground", -5000.0, 0.0, "hit")]


def decode(result):
    if result is None:
        return {"hit": False, "how": "None"}
    hit = result
    if isinstance(result, (list, tuple)):
        if not result or not bool(result[0]):
            return {"hit": False, "how": "tuple-false"}
        hit = result[1] if len(result) > 1 else None
    if hit is None:
        return {"hit": False, "how": "None"}
    fields = None
    try:
        fields = hit.to_tuple()
    except Exception:
        fields = None
    if fields is None and hasattr(unreal.GameplayStatics, "break_hit_result"):
        fields = unreal.GameplayStatics.break_hit_result(hit)
    if fields is None:
        loc = hit.get_editor_property("location")
        return {"hit": True, "z": round(float(loc.z), 1), "how": "get_editor_property"}
    # blocking_hit, initial_overlap, time, distance, location, impact_point,
    # normal, impact_normal, phys_mat, hit_actor, hit_component, ...
    loc, nrm = fields[4], fields[7]
    act = fields[9] if len(fields) > 9 else None
    return {"hit": bool(fields[0]), "z": round(float(loc.z), 1), "normal_z": round(float(nrm.z), 3),
            "actor": act.get_actor_label() if act and hasattr(act, "get_actor_label") else None,
            "how": "to_tuple" if hasattr(hit, "to_tuple") else "break_hit_result"}


forms = []
if world:
    for ch in ("ECC_VISIBILITY", "ECC_CAMERA"):
        if hasattr(unreal.TraceTypeQuery, ch):
            forms.append((ch, lambda s, e, c=getattr(unreal.TraceTypeQuery, ch): unreal.SystemLibrary.line_trace_single(
                world, s, e, c, True, [], unreal.DrawDebugTrace.NONE, True)))
    try:
        ws = unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1   # WorldStatic in the default project settings
        forms.append(("objects:WorldStatic", lambda s, e: unreal.SystemLibrary.line_trace_single_for_objects(
            world, s, e, [ws], True, [], unreal.DrawDebugTrace.NONE, True)))
    except Exception:
        note_error("object-type query setup")

hits_total, expected_hits, expected_hits_found = 0, 0, 0
for label, x, y, expect in PROBES:
    entry = {"probe": label, "x": round(x, 1), "y": round(y, 1), "expect": expect,
             "predicted_z_from_mesh": predict(x, y), "results": {}}
    for form, fn in forms:
        try:
            res = decode(fn(unreal.Vector(x, y, 6000.0), unreal.Vector(x, y, -3000.0)))
        except Exception as error:
            res = {"error": str(error).strip().splitlines()[-1][:200]}
            if not any(e["what"].startswith("first trace") for e in report["errors"]):
                note_error("first trace exception (%s)" % form)
        entry["results"][form] = res
        if res.get("hit"):
            hits_total += 1
    if expect == "hit":
        expected_hits += 1
        if any(r.get("hit") for r in entry["results"].values()):
            expected_hits_found += 1
    report["probes"].append(entry)
    say("  probe %-26s expect %-4s predicted %-7s -> %s" % (
        label, expect, entry["predicted_z_from_mesh"],
        "; ".join("%s:%s" % (f, ("z=%s %s" % (r.get("z"), r.get("actor"))) if r.get("hit")
                            else r.get("error") or "no hit") for f, r in entry["results"].items())))

# --- 4. verdict, cautiously --------------------------------------------------
if not world:
    verdict = "NO EDITOR WORLD -- nothing about traces or collision can be concluded from this run."
elif hits_total == 0:
    verdict = ("ALL %d trace(s) in %d form(s) returned no hit, including %d point(s) where the mesh survey "
               "predicts ground and the city-ground control. In this %s context scene queries are not "
               "answering; that is consistent with no physics scene for a commandlet world, but it is NOT "
               "evidence that the platform lacks collision. Collision settings above come from the component "
               "and mesh, not from a query. Walkability must be verified in the editor or PIE after apply."
               % (len(PROBES) * max(1, len(forms)), len(forms), expected_hits, report["context"]))
elif expected_hits_found == expected_hits:
    verdict = ("TRACES WORK in this %s context: every expected-ground probe hit and the water control %s."
               % (report["context"], "missed" if not any(r.get("hit") for r in report["probes"][-2]["results"].values())
                  else "HIT (unexpected -- check hidden water collision)"))
else:
    verdict = ("TRACES PARTIAL: %d of %d expected-ground probes hit. Read per-probe results before relying "
               "on either traces or their absence." % (expected_hits_found, expected_hits))
report["verdict"] = verdict
say("VERDICT: " + verdict)
report["finished_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "support-probe.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
say("wrote %s; nothing changed and no package saved" % (OUT / "support-probe.json"))
if os.environ.get("IB_PROBE_QUIT") == "1":
    unreal.SystemLibrary.quit_editor()
