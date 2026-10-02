"""FF1 FORECOURT FINISH: matched before/after captures of a garrison candidate (YM1 before, FF1 after):
lit editor views, in-game pawn-view captures, a MOVING-CAMERA frame sequence across the pad ring's joints,
the actual material in every generated marking's slot 0 in the editor world AND in the PIE world, pawn-profile
sweeps and lane scans of the forecourt roads, and the scripted PIE walks the forecourt finish affects.
Changes nothing and never saves. Derived from Scripts/ib_garrison_yellow_check.py (left unchanged).

    UnrealEditor.exe <project> -ExecutePythonScript="<Root>/Scripts/ib_garrison_forecourt_check.py"

Environment: IB_GARRISON_TARGET_LEVEL (a candidate under /Game/_GarrisonPreview_Disposable/),
IB_GARRISON_PLAN (the PF1 layout plan.json the candidates carry), IB_GARRISON_FF_PLAN (the FF1 plan: the new
pieces and the forecourt roads), IB_GARRISON_SHOTS (output folder), IB_GARRISON_PIE=1 (PIE captures and walks),
IB_GARRISON_WALKS (comma-separated walk-name prefixes; "none" = no walks; unset = all),
IB_GARRISON_SWEEPS=0 (skip sweeps and lane scans), IB_GARRISON_FRAMES=0 (skip the moving-camera sequence),
IB_GARRISON_PAINT_MI (the material every generated marking is expected to carry, optional).

Evidence kinds, kept apart in forecourt_checks.json:
  editor_shots  level-viewport cameras in game view (no actor spawned); world lighting unchanged
  frames        a moving editor camera at eye height across the pad ring: successive frames, same settings
  sweeps        ENGINE collision queries in the editor world, "Pawn" profile, the player pawn's own capsule
  lane_scans    the body capsule swept along each forecourt road at 25 cm steps across it (not movement)
  walks         SCRIPTED PIE: the real player pawn driven by movement input through waypoints; reached /
                stalled / fell / timeout recorded as they happen. Not a person playing.
  pie_shots     screenshots requested while PIE runs, from the player's own camera
  materials_*   the slot-0 material of every generated marking (the 91 and, when present, every new FF1
                paint piece) in the editor world and in the PIE world, plus the inherited live-map users of the
                shared marking MI (never touched)
"""
import unreal, json, os, time, math, traceback, datetime
from pathlib import Path

PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
PAWN_CLASS = "/Game/Characters/Infantry/BP_IBCharacter_Infantry.BP_IBCharacter_Infantry_C"
TARGET = (os.environ.get("IB_GARRISON_TARGET_LEVEL") or "").strip().rstrip("/")
PLAN = os.environ.get("IB_GARRISON_PLAN")
OUT = Path(os.environ.get("IB_GARRISON_SHOTS") or str(Path(unreal.Paths.project_saved_dir()) / "forecourtfinish"))
FF_PLAN = os.environ.get("IB_GARRISON_FF_PLAN")
DO_FRAMES = os.environ.get("IB_GARRISON_FRAMES", "1") != "0"
DO_PIE = os.environ.get("IB_GARRISON_PIE") == "1"
WALK_FILTER = [w.strip() for w in (os.environ.get("IB_GARRISON_WALKS") or "").split(",") if w.strip()]
DO_SWEEPS = os.environ.get("IB_GARRISON_SWEEPS", "1") != "0"
EXPECT_MI = (os.environ.get("IB_GARRISON_PAINT_MI") or "").strip()
RES_X, RES_Y = 1920, 1080

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT.mkdir(parents=True, exist_ok=True)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
R = {"tool": "ib_garrison_forecourt_check", "target": TARGET, "plan": PLAN, "ff_plan": FF_PLAN, "walk_filter": WALK_FILTER or "all",
     "sweeps_run": DO_SWEEPS, "expected_paint_mi": EXPECT_MI or None,
     "started_utc": datetime.datetime.utcnow().isoformat() + "Z", "editor_shots": [], "frames": [], "pie_shots": [], "walks": [],
     "errors": [], "evidence_kinds": {
         "editor_shots": "level viewport cameras in game view; no actor spawned; world lighting unchanged",
         "sweeps": "engine collision queries, Pawn profile, editor world; not movement",
         "lane_scans": "engine collision queries along each forecourt road, 25 cm apart across it; not movement",
         "frames": "a moving editor camera at eye height across the pad ring, successive frames, same settings",
         "walks": "scripted PIE: the real pawn driven by movement input; not a person playing",
         "pie_shots": "screenshots requested during PIE from the player's camera (gameplay view)",
         "materials": "slot-0 material of every generated marking, read from the loaded editor world and the PIE world"}}


def log(m):
    unreal.log("GARRISON FF1 CHECK: " + str(m))


def save():
    R["updated_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    (OUT / "forecourt_checks.json").write_bytes(json.dumps(R, indent=1).encode("utf-8"))


def note_error(what):
    R["errors"].append({"what": what, "detail": traceback.format_exc()[-900:]})
    unreal.log_warning("GARRISON FF1 CHECK: " + what + "\n" + traceback.format_exc()[-900:])


if not TARGET.startswith(PREVIEW_ROOT):
    R["errors"].append({"what": "refused", "detail": "target must be under " + PREVIEW_ROOT})
    save()
    raise RuntimeError("GARRISON FF1 CHECK REFUSED: target must be under " + PREVIEW_ROOT)
plan = json.loads(Path(PLAN).read_text(encoding="utf-8"))
if not plan.get("finish") or not plan.get("pier_lane"):
    R["errors"].append({"what": "refused", "detail": "the plan is not a PF1 plan"})
    save()
    raise RuntimeError("GARRISON FF1 CHECK REFUSED: the plan has no PF1 finish")
unreal.EditorLoadingAndSavingUtils.load_map(TARGET)
R["loaded"] = UES.get_editor_world().get_path_name().split(".")[0]
LEVEL_PREFIX = "%s.%s:PersistentLevel." % (TARGET, TARGET.split("/")[-1])
SRC_PREFIX = "/Game/LevelPrototyping/CarrowGateGarrison.CarrowGateGarrison:PersistentLevel."
actors = {a.get_path_name(): a for a in EAS.get_all_level_actors()}
tags_of = lambda a: [str(t) for t in (a.get_editor_property("tags") or [])]
R["generated_actors_in_level"] = sum(1 for a in actors.values() if plan["run_tag"] in tags_of(a))
R["finish_actors_in_level"] = sum(1 for a in actors.values() if plan["finish"]["tag"] in tags_of(a))
placed = {}
for m in plan["moves"]:
    if m["role"] not in ("pier crane", "pier dressing") and not str(m["role"]).startswith("assembly"):
        continue
    a = actors.get(LEVEL_PREFIX + m["identity"][len(SRC_PREFIX):])
    if a is None:
        placed[m["label"]] = "MISSING"
        continue
    l, rr = a.get_actor_location(), a.get_actor_rotation()
    placed[m["label"]] = {"loc": [round(l.x, 1), round(l.y, 1), round(l.z, 1)], "yaw": round(rr.yaw, 3),
                          "at_plan": abs(l.x - m["to"]["loc"][0]) < 0.6 and abs(l.y - m["to"]["loc"][1]) < 0.6
                          and abs(((rr.yaw - m["to"]["rot"]["yaw"]) + 180) % 360 - 180) < 0.06}
R["props_and_assemblies_in_level"] = placed
MARK_MAT = plan["finish"]["materials"]["markings"]
MARK_LABELS = sorted(p["label"] for p in plan["pieces"] if p.get("material") == MARK_MAT)
ff = json.loads(Path(FF_PLAN).read_text(encoding="utf-8"))
FF_MI = ff["material_object"]
FF_PAINT = sorted(p["label"] for p in ff["pieces"] if p.get("material") == FF_MI)
FF_ALL = sorted(p["label"] for p in ff["pieces"])
R["ff1_pieces_in_level"] = sum(1 for a in actors.values() if ff["finish_tag"] in tags_of(a))
R["ff1_pieces_in_plan"] = len(FF_ALL)


def mat_path(m):
    return m.get_path_name() if m else None


def material_readout(actor_list, where):
    """Slot-0 material of every generated marking: the 91 that existed before FF1 (the PF1 plan's pieces that
    carried the shared marking MI) and every NEW FF1 paint piece; plus every OTHER actor whose static meshes
    still use the shared MI (inherited from the live map, never touched)."""
    marks, new = set(MARK_LABELS), set(FF_PAINT)
    per, per_new, counts, counts_new, inherited = {}, {}, {}, {}, set()
    for a in actor_list:
        try:
            label = a.get_actor_label()
        except Exception:
            label = a.get_name()
        tg = tags_of(a)
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            mats = [mat_path(c.get_material(i)) for i in range(c.get_num_materials())]
            m0 = mats[0] if mats else None
            if plan["run_tag"] in tg and label in marks:
                per[label] = m0
                counts[m0] = counts.get(m0, 0) + 1
            elif ff["finish_tag"] in tg and label in new:
                per_new[label] = m0
                counts_new[m0] = counts_new.get(m0, 0) + 1
            elif any(m and m.split(".")[0] == MARK_MAT.split(".")[0] for m in mats):
                inherited.add(label)
    out = {"where": where, "marking_labels_in_plan": len(MARK_LABELS), "marking_actors_found": len(per),
           "slot0_material_counts": counts, "missing_labels": sorted(marks - set(per))[:20],
           "ff1_paint_labels_in_plan": len(FF_PAINT), "ff1_paint_actors_found": len(per_new),
           "ff1_slot0_material_counts": counts_new,
           "inherited_users_of_shared_marking_mi": sorted(inherited)[:40], "inherited_users_count": len(inherited)}
    if EXPECT_MI:
        out["all_markings_use_expected_mi"] = (len(per) == len(MARK_LABELS) and all(v == EXPECT_MI for v in per.values())
                                               and all(v == EXPECT_MI for v in per_new.values()))
    return out


try:
    R["materials_editor"] = material_readout(list(actors.values()), "editor world (loaded map)")
except Exception:
    note_error("material readout (editor)")
save()

Z = float(plan["deck_z"])
fr, d = plan["frame"], plan["design"]
front, centre, D = fr["front"], fr["centre"], float(fr["depth"])
axis = float(d["spine"]["axis_y"])
LANE = plan["pier_lane"]
LC = float(LANE["centre_y"])
PX0, PX1 = float(d["pier"]["x"][0]), float(d["pier"]["x"][1])
PY0, PY1 = float(d["pier"]["y"][0]), float(d["pier"]["y"][1])
comp = plan["composition"]
CMD, MH = comp["buildings"]["Command"], comp["buildings"]["Mess_Hall"]
PAD_C = d["pad"]["centre"]


def look(eye, target):
    return unreal.MathLibrary.find_look_at_rotation(V(*eye), V(*target))


# Editor cameras. The sun (DirLight_PreDawn, yaw 165) is low over the sea, so views look landward
# (-X) or across the site with the sun behind the camera.
CX = ff["corridors"]["cross_road"]
CR_X = (CX["x"][0] + CX["x"][1]) / 2.0           # the cross-road's centre line
CR_Y0, CR_Y1 = CX["y"]
GR = ff["corridors"]["gate_road"]
GR_Y = (GR["y"][0] + GR["y"][1]) / 2.0
AX = ff["corridors"]["axis_road"]
X_SEA = float(d["forecourt"]["seaward_edge_x"])
SHOTS = [
    ("overhead-reference", (front[0] + 0.42 * D, axis, Z + 0.95 * D), (centre[0] + 0.08 * D, axis, Z), None),
    ("overhead-topdown", (centre[0], axis, Z + 1.35 * D), None, unreal.Rotator(roll=0.0, pitch=-89.9, yaw=180.0)),
    # FF1: from above the spine entrance, landward across the cross-road to the gate and axis roads
    ("forecourt-ground", (X_SEA + 1300.0, 1000.0, Z + 650.0), (X_SEA - 4500.0, 1500.0, Z), None),
    # FF1: the forecourt's docks-side (-Y) quay edge from over the water, landward along it
    ("forecourt-quay", (X_SEA + 700.0, -4200.0, Z + 450.0), (3000.0, -2400.0, Z + 40.0), None),
    # FF1: the curb along Medical's seaward face, from over the forecourt / control-platform gap
    ("medical-front", (X_SEA + 800.0, 4700.0, Z + 380.0), (X_SEA - 60.0, 6600.0, Z + 40.0), None),
    ("pad-ring", (PAD_C[0] + 4000.0, PAD_C[1] - 1200.0, Z + 1300.0), (PAD_C[0], PAD_C[1], Z), None),
]
# the moving-camera sequence: eye height, 16 frames 30 cm apart, looking across the ring's near arc
FRAMES = [((PAD_C[0] + 700.0 + 30.0 * k, PAD_C[1] + 2350.0, Z + 165.0), (PAD_C[0], PAD_C[1] + 900.0, Z)) for k in range(16)]


def call_first(what, attempts):
    last = None
    for label, fn in attempts:
        try:
            out = fn()
            R.setdefault("api_used", {})[what] = label
            return out
        except Exception as error:
            last = error
            R.setdefault("api_failed", {}).setdefault(what, []).append(label + ": " + (str(error).splitlines() or [""])[-1][:160])
    raise last


def viewport_key():
    try:
        return LES.get_active_viewport_config_key()
    except Exception:
        return None


def set_camera(loc, rot):
    return call_first("camera", [
        ("LevelEditorSubsystem.set_level_viewport_camera_info(loc, rot, active key)",
         lambda: LES.set_level_viewport_camera_info(loc, rot, viewport_key())),
        ("UnrealEditorSubsystem.set_level_viewport_camera_info(loc, rot)",
         lambda: UES.set_level_viewport_camera_info(loc, rot))])


def game_view(on):
    return call_first("game_view", [("LevelEditorSubsystem.editor_set_game_view(on)", lambda: LES.editor_set_game_view(on))])


def pawn_dims():
    out = {"radius": 34.0, "half_height": 88.0, "max_step_height": 45.0, "source": "engine defaults"}
    try:
        cdo = unreal.get_default_object(unreal.load_class(None, PAWN_CLASS))
        cap = cdo.get_editor_property("capsule_component")
        out.update({"radius": float(cap.get_unscaled_capsule_radius()),
                    "half_height": float(cap.get_unscaled_capsule_half_height()), "source": PAWN_CLASS + " class defaults"})
        mv = cdo.get_editor_property("character_movement")
        out["max_step_height"] = float(mv.get_editor_property("max_step_height"))
    except Exception:
        note_error("pawn dims")
    return out


def decode(result):
    if result is None:
        return None
    hit = result
    if isinstance(result, (list, tuple)):
        if not result or not bool(result[0]):
            return None
        hit = result[1] if len(result) > 1 else None
    if hit is None:
        return None
    f = hit.to_tuple()
    if not bool(f[0]):
        return None
    act, comp_ = (f[9] if len(f) > 9 else None), (f[10] if len(f) > 10 else None)
    return {"initial_overlap": bool(f[1]), "loc": [round(f[4].x, 1), round(f[4].y, 1), round(f[4].z, 1)],
            "impact": [round(f[5].x, 1), round(f[5].y, 1), round(f[5].z, 1)],
            "normal": [round(f[7].x, 3), round(f[7].y, 3), round(f[7].z, 3)],
            "actor": act.get_actor_label() if act and hasattr(act, "get_actor_label") else None,
            "component": comp_.get_name() if comp_ else None}


def trace(world, a, b, radius, hh, ignore=()):
    return decode(unreal.SystemLibrary.capsule_trace_single_by_profile(
        world, V(*a), V(*b), radius, hh, "Pawn", False, list(ignore), unreal.DrawDebugTrace.NONE, True))


def floor_z(world, x, y, dims, zprev=None):
    """Floor under (x, y), probed down from just above head height of the deck (or of the previous
    floor when lower), so a probe never starts on top of a structure it met before."""
    base = min(zprev, Z + 20.0) if zprev is not None else Z
    top = base + 2.0 * dims["half_height"] + 30.0
    h = trace(world, (x, y, top), (x, y, base - 1200.0), dims["radius"] * 0.5, dims["radius"] * 0.5)
    return (h["impact"][2], h["actor"], h["initial_overlap"]) if h else (None, None, None)


def samples(pts, step=50.0):
    out = [tuple(pts[0])]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L // step))
        for k in range(1, n + 1):
            out.append((ax + (bx - ax) * k / n, ay + (by - ay) * k / n))
    return out


def sweep(world, name, pts, dims, stop_at_first=False, step=50.0):
    r, hh, st = dims["radius"], dims["half_height"], dims["max_step_height"]
    hb = max(r, (2.0 * hh - st) / 2.0)
    smp = samples(pts, step)
    floors, zprev = [], None
    for x, y in smp:
        z, act, ov = floor_z(world, x, y, dims, zprev)
        floors.append((z, act, ov))
        if z is not None and not ov:
            zprev = z
    hits, dist, gaps = [], 0.0, 0
    for k in range(1, len(smp)):
        (ax, ay), (bx, by) = smp[k - 1], smp[k]
        dist += math.hypot(bx - ax, by - ay)
        za, zb = floors[k - 1][0], floors[k][0]
        if za is None or zb is None:
            gaps += 1
            continue
        h = trace(world, (ax, ay, za + st + hb), (bx, by, zb + st + hb), r, hb)
        if h:
            hits.append(dict(h, along_cm=round(dist, 0)))
            if stop_at_first:
                break
    distinct = {}
    for b in hits:
        key = "%s/%s" % (b["actor"], b["component"])
        distinct.setdefault(key, {"first_along_cm": b["along_cm"], "segments": 0, "at": b["impact"]})
        distinct[key]["segments"] += 1
    fz = [f[0] for f in floors if f[0] is not None]
    steps = [abs(floors[k][0] - floors[k - 1][0]) for k in range(1, len(floors))
             if floors[k][0] is not None and floors[k - 1][0] is not None]
    return {"name": name, "waypoints": pts, "samples": len(smp), "length_m": round(dist / 100.0, 1),
            "no_floor_samples": sum(1 for f in floors if f[0] is None), "segments_skipped_no_floor": gaps,
            "floor_z": [round(min(fz), 1), round(max(fz), 1)] if fz else None, "largest_floor_step_cm": round(max(steps or [0.0]), 1),
            "floor_actors": sorted(set(str(f[1]) for f in floors if f[1])), "blocked_segments": len(hits),
            "clear": not hits and not gaps, "first_block": hits[0] if hits else None, "blockers": distinct}


SY0, SY1 = float(d["spine"]["y"][0]), float(d["spine"]["y"][1])


def road_scan(world, name, along, run, band, dims, margin=200.0):
    """Pawn-centre lines along one forecourt road, 25 cm apart across it (from `margin` outside its painted
    band on each side), each swept by the body capsule; reports the clear band that holds the painted one."""
    r = dims["radius"]
    rows = []
    c = band[0] - margin
    while c <= band[1] + margin + 1e-6:
        pts = [[run[0], c], [run[1], c]] if along == "x" else [[c, run[0]], [c, run[1]]]
        sw = sweep(world, "%s line %.1f" % (name, c), pts, dims, stop_at_first=True)
        fb = sw["first_block"]
        rows.append({"across": round(c, 1), "clear": sw["clear"], "no_floor_samples": sw["no_floor_samples"],
                     "first_block": ("%s/%s" % (fb["actor"], fb["component"])) if fb else None,
                     "first_block_at": fb["impact"] if fb else None})
        c += 25.0
    inside = [q for q in rows if band[0] + r <= q["across"] <= band[1] - r]
    out = {"name": name, "along": along, "run": run, "painted_band": band, "step_cm": 25.0, "lines": rows,
           "lines_inside_painted_band": len(inside), "clear_inside_painted_band": sum(1 for q in inside if q["clear"])}
    k = min(range(len(rows)), key=lambda i: abs(rows[i]["across"] - (band[0] + band[1]) / 2.0))
    if rows[k]["clear"]:
        lo = k
        while lo - 1 >= 0 and rows[lo - 1]["clear"]:
            lo -= 1
        hi = k
        while hi + 1 < len(rows) and rows[hi + 1]["clear"]:
            hi += 1
        out["clear_centre_band"] = [rows[lo]["across"], rows[hi]["across"]]
        out["obstacle_free_corridor_cm"] = round(rows[hi]["across"] - rows[lo]["across"] + 2.0 * r, 1)
        out["band_limited_by"] = [rows[lo - 1]["first_block"] if lo > 0 else "scan limit (%.0f cm outside the paint)" % margin,
                                  rows[hi + 1]["first_block"] if hi + 1 < len(rows) else "scan limit (%.0f cm outside the paint)" % margin]
    out["summary"] = "%s: %d of %d pawn-centre lines inside the painted band clear; clear band %s" % (
        name, out["clear_inside_painted_band"], out["lines_inside_painted_band"], out.get("clear_centre_band"))
    return out


def lane_scans(dims):
    world = UES.get_editor_world()
    return [road_scan(world, "gate road", "x", [GR["x"][0] + 50.0, X_SEA - 80.0], GR["y"], dims),
            road_scan(world, "axis road", "x", [AX["x"][0] + 100.0, X_SEA - 80.0], AX["y"], dims),
            road_scan(world, "cross-road", "y", [CR_Y0 + 40.0, CR_Y1 - 50.0], CX["x"], dims, margin=150.0)]


def ff_routes():
    """The walks and sweeps this pass affects: the land join, the pier and spine entrances (beside the new
    corner curbs), the cross-road, the door routes the new paint marks, and one step onto the new curb."""
    PY0, PY1 = float(d["pier"]["y"][0]), float(d["pier"]["y"][1])
    out = [
        ("land join: city road -> gate -> gate road", "land-join",
         [[-3450.0, -251.0], [348.0, -251.0], [1848.0, -251.0], [1848.0, GR_Y], [X_SEA - 900.0, GR_Y]]),
        ("pier entrance: gate road -> pier lane", "pier-join", [[X_SEA - 900.0, GR_Y], [X_SEA + 1000.0, GR_Y]]),
        ("pier entrance beside its -Y curb", "pier-join", [[X_SEA - 700.0, PY0 + 175.0], [X_SEA + 1000.0, PY0 + 175.0]]),
        ("pier entrance beside its +Y curb", "pier-join", [[X_SEA - 700.0, PY1 - 175.0], [X_SEA + 1000.0, PY1 - 175.0]]),
        ("spine entrance beside its -Y curb", "spine-join", [[X_SEA - 700.0, SY0 + 175.0], [X_SEA + 1000.0, SY0 + 175.0]]),
        ("spine entrance on the axis", "spine-join", [[X_SEA - 900.0, axis], [X_SEA + 1000.0, axis]]),
        ("cross-road: docks-side end -> Medical's corner", "cross-road", [[CR_X, CR_Y0 + 250.0], [CR_X, CR_Y1 - 200.0]]),
    ]
    for rt in ff.get("routes") or []:
        legs = rt["legs"]
        pts = [list(legs[0][0])] + [list(l[1]) for l in legs]
        if abs(pts[0][0] - pts[1][0]) < 1.0:             # a leg across a road along X: start on its centre line
            pts[0][1] = GR_Y if "Barracks" in rt["to"] else axis
        out.append(("door route: %s" % rt["to"], "door-route", pts))
    out.append(("forecourt curb: onto the new docks-side coping, along it and back", "curb",
                [[5000.0, -2300.0], [5000.0, -2468.0], [5300.0, -2468.0], [5300.0, -2300.0]]))
    return out


def sweeps(dims):
    world = UES.get_editor_world()
    out = {"method": "capsule_trace_single_by_profile('Pawn'), the pawn's own capsule; floor probed per sample "
                     "(clamped); body capsule from max step height to head height swept sample to sample",
           "pawn": dims, "routes": []}
    for name, kind, pts in ff_routes():
        out["routes"].append(dict(sweep(world, name, pts, dims, step=25.0), kind=kind))
    return out


def pie_world():
    try:
        return UES.get_game_world()
    except Exception:
        return None


def walks():
    out = ff_routes()
    if WALK_FILTER:
        out = [w for w in out if any(w[0].startswith(f) for f in WALK_FILTER)]
    return out


PIE_SHOTS = [  # (name, pawn position, look-at point): the player's own camera
    ("pie-crossroad", (CR_X, CR_Y0 + 600.0), (CR_X, CR_Y1)),
    ("pie-crossroad-to-pier", (CR_X, CR_Y1 - 400.0), (CR_X, CR_Y0)),
    ("pie-gate-road", (2200.0, GR_Y), (X_SEA, GR_Y)),
    ("pie-pad-ring", (PAD_C[0] + 1100.0, PAD_C[1] + 2200.0), (PAD_C[0] - 1200.0, PAD_C[1] - 600.0)),
]


def flow():
    yield 20.0
    try:
        game_view(True)
    except Exception:
        note_error("game view on")
    yield 1.0
    for name, eye, target, rot in SHOTS:
        try:
            set_camera(V(*eye), rot or look(eye, target))
        except Exception:
            note_error("camera " + name)
            continue
        yield 12.0
        try:
            ok = unreal.AutomationLibrary.take_high_res_screenshot(RES_X, RES_Y, str(OUT / (name + ".png")))
            R["editor_shots"].append({"name": name, "file": str(OUT / (name + ".png")), "eye": [round(v, 1) for v in eye],
                                      "target": [round(v, 1) for v in target] if target else None, "requested": bool(ok),
                                      "kind": "EDITOR view (level viewport, game view)"})
        except Exception:
            note_error("screenshot " + name)
        save()
        yield 5.0
    if DO_FRAMES:
        (OUT / "frames").mkdir(parents=True, exist_ok=True)
        for k, (eye, target) in enumerate(FRAMES):
            try:
                set_camera(V(*eye), look(eye, target))
            except Exception:
                note_error("frame camera %d" % k)
                continue
            yield 10.0 if k == 0 else 3.0
            try:
                f = OUT / "frames" / ("frame_%02d.png" % k)
                ok = unreal.AutomationLibrary.take_high_res_screenshot(RES_X, RES_Y, str(f))
                R["frames"].append({"k": k, "file": str(f), "eye": [round(v, 1) for v in eye],
                                    "target": [round(v, 1) for v in target], "requested": bool(ok),
                                    "kind": "EDITOR view, moving camera at eye height (level viewport, game view)"})
            except Exception:
                note_error("frame %d" % k)
            save()
            yield 3.0
    dims = pawn_dims()
    R["pawn"] = dims
    if DO_SWEEPS:
        try:
            R["sweeps"] = sweeps(dims)
        except Exception:
            note_error("sweeps")
        save()
        try:
            R["lane_scans"] = lane_scans(dims)
        except Exception:
            note_error("lane scans")
        save()
    if not DO_PIE:
        return
    try:
        LES.editor_request_begin_play()
    except Exception:
        note_error("begin play")
        return
    t0, pawn, gw = time.monotonic(), None, None
    while time.monotonic() - t0 < 45.0:
        yield 1.0
        gw = pie_world()
        pawn = unreal.GameplayStatics.get_player_pawn(gw, 0) if gw else None
        if pawn:
            break
    if not pawn:
        R["walks_error"] = "no player pawn in PIE within 45 s"
        save()
    else:
        cap = pawn.get_component_by_class(unreal.CapsuleComponent)
        hh = cap.get_scaled_capsule_half_height() if cap else 88.0
        rad = cap.get_scaled_capsule_radius() if cap else 34.0
        R["pie_pawn"] = {"class": pawn.get_class().get_name(), "half_height": round(hh, 1), "radius": round(rad, 1)}
        try:
            R["materials_pie"] = material_readout(list(unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor)),
                                                  "PIE world (play session)")
        except Exception:
            note_error("material readout (PIE)")
        save()
        pc = unreal.GameplayStatics.get_player_controller(gw, 0)
        yield 3.0
        # in-game pawn-view captures first (the player's own camera)
        for name, (x, y), (tx, ty) in PIE_SHOTS:
            try:
                sz = floor_z(gw, x, y, {"radius": rad, "half_height": hh})[0] or Z
                yaw = math.degrees(math.atan2(ty - y, tx - x))
                pawn.set_actor_location_and_rotation(V(x, y, sz + hh + 5.0), unreal.Rotator(0.0, 0.0, yaw), False, True)
                if pc:
                    pc.set_control_rotation(unreal.Rotator(roll=0.0, pitch=-4.0, yaw=yaw))
                yield 2.5
                f = OUT / (name + ".png")
                ok = unreal.AutomationLibrary.take_high_res_screenshot(RES_X, RES_Y, str(f))
                R["pie_shots"].append({"name": name, "file": str(f), "pawn_at": [round(x, 1), round(y, 1)],
                                       "looking_at": [round(tx, 1), round(ty, 1)], "requested": bool(ok),
                                       "kind": "GAMEPLAY view requested during PIE (player camera)"})
                yield 6.0
                R["pie_shots"][-1]["file_written"] = f.is_file()
            except Exception:
                note_error("pie shot " + name)
            save()
        for name, kind, pts in walks():
            rec = {"name": name, "kind": kind, "waypoints": pts}
            try:
                x0, y0 = pts[0]
                sz = floor_z(gw, x0, y0, {"radius": rad, "half_height": hh})[0]
                sz = sz if sz is not None else Z
                yaw = math.degrees(math.atan2(pts[1][1] - y0, pts[1][0] - x0))
                pawn.set_actor_location_and_rotation(V(x0, y0, sz + hh + 5.0), unreal.Rotator(0.0, 0.0, yaw), False, True)
                yield 1.5
                L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
                limit = L / 200.0 + 20.0
                t_start, wp, traj, last_t, hist, result = time.monotonic(), 1, [], 0.0, [], None
                zmax, zmin, drift = -1e9, 1e9, 0.0
                while True:
                    l = pawn.get_actor_location()
                    t = time.monotonic() - t_start
                    zmax, zmin = max(zmax, l.z), min(zmin, l.z)
                    (ax_, ay_), (bx_, by_) = pts[wp - 1], pts[min(wp, len(pts) - 1)]
                    seg = math.hypot(bx_ - ax_, by_ - ay_) or 1.0
                    drift = max(drift, abs((l.x - ax_) * (by_ - ay_) - (l.y - ay_) * (bx_ - ax_)) / seg)
                    if t - last_t >= 0.25:
                        traj.append([round(t, 2), round(l.x, 1), round(l.y, 1), round(l.z, 1)])
                        hist.append((t, l.x, l.y))
                        last_t = t
                    gx, gy = pts[wp]
                    if math.hypot(gx - l.x, gy - l.y) < 70.0:
                        wp += 1
                        if wp >= len(pts):
                            result = "reached"
                            break
                        gx, gy = pts[wp]
                    if l.z < sz - 200.0:
                        result = "fell"
                        break
                    old = [h for h in hist if t - h[0] >= 2.5]
                    if old and t > 3.0 and math.hypot(l.x - old[-1][1], l.y - old[-1][2]) < 40.0:
                        result = "stalled"
                        break
                    if t > limit:
                        result = "timeout"
                        break
                    dx, dy = gx - l.x, gy - l.y
                    n = math.hypot(dx, dy) or 1.0
                    pawn.add_movement_input(V(dx / n, dy / n, 0.0), 1.0, False)
                    yield 0.0
                l = pawn.get_actor_location()
                rec.update({"result": result, "waypoints_reached": min(wp, len(pts)) - 1, "of": len(pts) - 1,
                            "seconds": round(time.monotonic() - t_start, 2), "length_m": round(L / 100.0, 1),
                            "end": [round(l.x, 1), round(l.y, 1), round(l.z, 1)],
                            "capsule_centre_z": [round(zmin, 1), round(zmax, 1)],
                            "max_lateral_drift_cm": round(drift, 1), "trajectory": traj[-200:]})
                if result == "stalled":
                    gx, gy = pts[min(wp, len(pts) - 1)]
                    dx, dy = gx - l.x, gy - l.y
                    n = math.hypot(dx, dy) or 1.0
                    rec["blocked_by"] = trace(gw, (l.x, l.y, l.z), (l.x + dx / n * 120.0, l.y + dy / n * 120.0, l.z),
                                              rad, hh, [pawn])
            except Exception:
                note_error("walk " + name)
                rec["result"] = rec.get("result") or "error"
            R["walks"].append(rec)
            save()
            yield 0.5
    try:
        LES.editor_request_end_play()
    except Exception:
        note_error("end play")
    yield 4.0


state = {"due": time.monotonic(), "busy": False, "handle": None, "gen": flow()}


def finish():
    try:
        game_view(False)
    except Exception:
        pass
    try:
        dirty = [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    except Exception:
        dirty = "unreadable"
    R["dirty_map_packages_at_exit"] = dirty
    R["finished_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    save()
    log("COMPLETE; nothing saved -> " + str(OUT))
    unreal.unregister_slate_post_tick_callback(state["handle"])
    unreal.SystemLibrary.quit_editor()


def tick(dt):
    if state["busy"] or time.monotonic() < state["due"]:
        return
    state["busy"] = True
    try:
        wait = next(state["gen"])
        state["due"] = time.monotonic() + float(wait or 0.0)
    except StopIteration:
        finish()
    except Exception:
        note_error("flow")
        save()
        try:
            LES.editor_request_end_play()
        except Exception:
            pass
        finish()
    finally:
        state["busy"] = False


state["handle"] = unreal.register_slate_post_tick_callback(tick)
log("started on " + R["loaded"])
