"""PF1 PIER FINISH candidate: lit editor captures, pawn-profile collision sweeps, a measured pier
lane corridor, scripted PIE walks and in-game pawn-view captures. Changes nothing and never saves.

    UnrealEditor.exe <project> -ExecutePythonScript="<Root>/Scripts/ib_garrison_pierfinish_check.py"

Environment: IB_GARRISON_TARGET_LEVEL (a candidate under /Game/_GarrisonPreview_Disposable/),
IB_GARRISON_PLAN (the PF1 plan.json), IB_GARRISON_SHOTS (output folder), IB_GARRISON_PIE=1 (walks).

Evidence kinds, kept apart in pierfinish_checks.json:
  editor_shots  level-viewport cameras in game view (no actor spawned); world lighting unchanged
  sweeps        ENGINE collision queries in the editor world, "Pawn" profile, the player pawn's own
                capsule: floor probe per sample (clamped, so it never climbs onto what it found),
                then a BODY capsule (max step height to head) swept sample to sample
  lane_scan     the same body capsule swept along the pier at 25 cm steps across it; the clear
                band around the marked lane is refined to ~1 cm at both edges
  walks         SCRIPTED PIE: the real player pawn driven by movement input through waypoints;
                reached / stalled / fell / timeout recorded as they happen. Not a person playing.
  pie_shots     screenshots requested while PIE runs, from the player's own camera
"""
import unreal, json, os, time, math, traceback, datetime
from pathlib import Path

PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
PAWN_CLASS = "/Game/Characters/Infantry/BP_IBCharacter_Infantry.BP_IBCharacter_Infantry_C"
TARGET = (os.environ.get("IB_GARRISON_TARGET_LEVEL") or "").strip().rstrip("/")
PLAN = os.environ.get("IB_GARRISON_PLAN")
OUT = Path(os.environ.get("IB_GARRISON_SHOTS") or str(Path(unreal.Paths.project_saved_dir()) / "pierfinish"))
DO_PIE = os.environ.get("IB_GARRISON_PIE") == "1"
RES_X, RES_Y = 1920, 1080

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT.mkdir(parents=True, exist_ok=True)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
R = {"tool": "ib_garrison_pierfinish_check", "target": TARGET, "plan": PLAN,
     "started_utc": datetime.datetime.utcnow().isoformat() + "Z", "editor_shots": [], "pie_shots": [], "walks": [],
     "errors": [], "evidence_kinds": {
         "editor_shots": "level viewport cameras in game view; no actor spawned; world lighting unchanged",
         "sweeps": "engine collision queries, Pawn profile, editor world; not movement",
         "lane_scan": "engine collision queries along the pier, 25 cm apart, edges refined; not movement",
         "walks": "scripted PIE: the real pawn driven by movement input; not a person playing",
         "pie_shots": "screenshots requested during PIE from the player's camera (gameplay view)"}}


def log(m):
    unreal.log("GARRISON PIER FINISH CHECK: " + str(m))


def save():
    R["updated_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    (OUT / "pierfinish_checks.json").write_bytes(json.dumps(R, indent=1).encode("utf-8"))


def note_error(what):
    R["errors"].append({"what": what, "detail": traceback.format_exc()[-900:]})
    unreal.log_warning("GARRISON PIER FINISH CHECK: " + what + "\n" + traceback.format_exc()[-900:])


if not TARGET.startswith(PREVIEW_ROOT):
    R["errors"].append({"what": "refused", "detail": "target must be under " + PREVIEW_ROOT})
    save()
    raise RuntimeError("GARRISON PIER FINISH CHECK REFUSED: target must be under " + PREVIEW_ROOT)
plan = json.loads(Path(PLAN).read_text(encoding="utf-8"))
if not plan.get("finish") or not plan.get("pier_lane"):
    R["errors"].append({"what": "refused", "detail": "the plan is not a PF1 plan"})
    save()
    raise RuntimeError("GARRISON PIER FINISH CHECK REFUSED: the plan has no PF1 finish")
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


def look(eye, target):
    return unreal.MathLibrary.find_look_at_rotation(V(*eye), V(*target))


# Editor cameras. The sun (DirLight_PreDawn, yaw 165) is low over the sea, so views look landward
# (-X) or across the site with the sun behind the camera.
SHOTS = [
    ("overhead-reference", (front[0] + 0.42 * D, axis, Z + 0.95 * D), (centre[0] + 0.08 * D, axis, Z), None),
    ("overhead-topdown", (centre[0], axis, Z + 1.35 * D), None, unreal.Rotator(roll=0.0, pitch=-89.9, yaw=180.0)),
    # the pier's service lane from its seaward end, landward (front-lit): the whole lane, crane and trucks
    ("pier-lane-ground", (PX1 - 150.0, LC, Z + 420.0), (PX0 - 400.0, LC, Z + 60.0), None),
    ("pier-lane-eye", (PX1 - 150.0, LC, Z + 170.0), (PX0, LC, Z + 150.0), None),
    # the pier's quay edges and the channel, from over the channel, landward
    ("pier-channel-quay", (PX1 + 900.0, (PY1 + float(d["spine"]["y"][0])) / 2.0, Z + 520.0),
     ((PX0 + PX1) / 2.0 - 1500.0, (PY1 + float(d["spine"]["y"][0])) / 2.0 - 250.0, Z - 60.0), None),
    # the control platform's seaward edge and the pad's west flats, from over the notch water, landward
    ("control-pad-edge", (16900.0, 8600.0, Z + 950.0), (13600.0, 6900.0, Z), None),
    # the spine / control-platform seam at Mess_Hall's door, with its threshold bar
    ("spine-control-join", (13300.0, 3900.0, Z + 420.0), (12500.0, 5725.0, Z + 60.0), None),
]


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


def lane_clear(world, y, dims):
    s = sweep(world, "pier lane y=%.1f" % y, [[PX0 - 300.0, y], [PX1 - 300.0, y]], dims, stop_at_first=True)
    fb = s["first_block"]
    return s["clear"], (("%s/%s" % (fb["actor"], fb["component"])), fb["impact"][0]) if fb else (None, None)


def lane_scan(dims):
    """Pawn-centre lanes along the pier 25 cm apart, then both edges of the clear band that holds the
    marked lane refined by bisection to ~1 cm. Band + capsule diameter = obstacle-free corridor."""
    world = UES.get_editor_world()
    r = dims["radius"]
    rows, y = [], PY0 + r + 5.0
    while y <= PY1 - r - 5.0:
        ok, (who, bx) = lane_clear(world, y, dims)
        rows.append({"y": round(y, 1), "clear": ok, "first_block": who, "first_block_x": bx})
        y += 25.0
    out = {"lanes": rows, "step_cm": 25.0, "x_range": [PX0 - 300.0, PX1 - 300.0],
           "clear_lanes": sum(1 for q in rows if q["clear"]), "of": len(rows)}
    k = min(range(len(rows)), key=lambda i: abs(rows[i]["y"] - LC))
    if not rows[k]["clear"]:
        out["summary"] = "the lane centre y=%.0f is NOT clear: %s" % (LC, rows[k]["first_block"])
        return out
    lo = k
    while lo - 1 >= 0 and rows[lo - 1]["clear"]:
        lo -= 1
    hi = k
    while hi + 1 < len(rows) and rows[hi + 1]["clear"]:
        hi += 1
    edges = {}
    for side, ci, bi in (("outboard", lo, lo - 1), ("inboard", hi, hi + 1)):
        yc = rows[ci]["y"]
        if 0 <= bi < len(rows):
            yb, who = rows[bi]["y"], rows[bi]["first_block"]
            for _ in range(5):
                mid = (yc + yb) / 2.0
                ok, (w2, _) = lane_clear(world, mid, dims)
                if ok:
                    yc = mid
                else:
                    yb, who = mid, w2
            edges[side] = {"last_clear_centre_y": round(yc, 1), "first_blocked_centre_y": round(yb, 1), "by": who}
        else:
            edges[side] = {"last_clear_centre_y": round(yc, 1), "first_blocked_centre_y": None, "by": "pier edge (scan limit)"}
    band = edges["inboard"]["last_clear_centre_y"] - edges["outboard"]["last_clear_centre_y"]
    out.update({"centre_band": [edges["outboard"]["last_clear_centre_y"], edges["inboard"]["last_clear_centre_y"]],
                "edges": edges, "pawn_centre_band_cm": round(band, 1),
                "obstacle_free_corridor_cm": round(band + 2.0 * r, 1),
                "marked_lane": LANE["y"], "marked_lane_inside_band": edges["outboard"]["last_clear_centre_y"] - r <= LANE["y"][0]
                and edges["inboard"]["last_clear_centre_y"] + r >= LANE["y"][1]})
    out["summary"] = ("clear pawn-centre band y %.1f..%.1f (%.0f cm) -> obstacle-free corridor %.0f cm (capsule %.0f cm "
                      "wide); bounded by %s and %s" % (out["centre_band"][0], out["centre_band"][1], band,
                                                       out["obstacle_free_corridor_cm"], 2 * r, edges["outboard"]["by"],
                                                       edges["inboard"]["by"]))
    return out


def door_approach_legs():
    out = []
    for rt in plan.get("routes") or []:
        if rt.get("crosses") == "entrance" and rt.get("waypoints"):
            out.append((rt["name"], rt["waypoints"]))
    return out


def extra_routes():
    """Walks/sweeps beyond the plan's routes: the lane's two edges, joins, the coping curb."""
    lo, hi = LANE["y"][0] + 40.0, LANE["y"][1] - 40.0
    return [
        ("pier lane, crane-side edge (y %.0f), forecourt -> pier end" % lo, "lane-edge", [[PX0 - 1500.0, lo], [PX1 - 300.0, lo]]),
        ("pier lane, truck-side edge (y %.0f), pier end -> forecourt" % hi, "lane-edge", [[PX1 - 300.0, hi], [PX0 - 1500.0, hi]]),
        ("join spine -> pad beside the notch coping (y 3600)", "join", [[13600.0, 3600.0], [15400.0, 3700.0]]),
        ("join spine -> control platform on the apron (x 14100)", "join", [[14100.0, 4600.0], [14100.0, 6600.0]]),
        ("join forecourt -> spine (y 3750)", "join", [[9300.0, 3750.0], [11200.0, 3750.0]]),
        ("coping curb: from the passage onto the control platform's rear coping, along it, and back",
         "curb", [[11400.0, 7333.0], [11107.0, 7333.0], [11107.0, 7600.0], [11350.0, 7600.0]]),
    ]


def sweeps(dims):
    world = UES.get_editor_world()
    out = {"method": "capsule_trace_single_by_profile('Pawn'), the pawn's own capsule; floor probed per sample "
                     "(clamped); body capsule from max step height to head height swept sample to sample",
           "pawn": dims, "routes": []}
    for rt in plan.get("routes") or []:
        if rt.get("waypoints"):
            out["routes"].append(dict(sweep(world, rt["name"], rt["waypoints"], dims), kind=rt.get("crosses")))
    for name, kind, pts in extra_routes():
        out["routes"].append(dict(sweep(world, name, pts, dims, step=25.0), kind=kind))
    return out


def pie_world():
    try:
        return UES.get_game_world()
    except Exception:
        return None


def walks():
    out = []
    for rt in plan.get("routes") or []:
        if rt.get("waypoints"):
            out.append((rt["name"], rt.get("crosses"), rt["waypoints"]))
    out += extra_routes()
    gate = [p for p in plan["checks"]["paths"] if p["path"].startswith("city road")]
    if gate:
        pts = gate[0]["points"] + [[gate[0]["points"][-1][0] + 1500.0, gate[0]["points"][-1][1]]]
        out.append(("existing route: city road -> gate -> forecourt", "existing", pts))
    return out


PIE_SHOTS = [  # (name, pawn position, look-at point): the player's own camera
    ("pie-pier-lane-from-forecourt", (PX0 - 600.0, LC), (PX1, LC)),
    ("pie-pier-lane-from-pier-end", (PX1 - 400.0, LC), (PX0 - 1000.0, LC)),
    ("pie-control-apron-to-command", (14100.0, 7000.0), (CMD["to"]["door_loc"][0], CMD["to"]["door_loc"][1])),
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
    dims = pawn_dims()
    R["pawn"] = dims
    try:
        R["sweeps"] = sweeps(dims)
    except Exception:
        note_error("sweeps")
    save()
    try:
        R["lane_scan"] = lane_scan(dims)
    except Exception:
        note_error("lane scan")
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
