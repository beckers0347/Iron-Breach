"""Pawn clearance checks on a DISPOSABLE garrison map. Changes nothing and never saves.

    UnrealEditor.exe <project> -ExecutePythonScript="<Root>/Scripts/ib_garrison_clearance_check.py"

Runs the same checks on any disposable map, so a candidate can be compared with the
original building positions (e.g. Preview3, where Command and Mess_Hall have not moved):

  door sweeps  ENGINE collision queries (Pawn profile, the player's capsule from its
               class defaults) from each door's approach, through its threshold, to
               3 m inside the building: once as the level is, and once ignoring the
               door-frame actor, so what stands BEHIND the (closed) leaf is named.
  route sweeps (IB_GARRISON_SWEEP_ROUTES=1) the plan's routes, with the floor probe
               started from the deck level (never from a floor found on a structure),
               and a scan of every pawn-wide lane along the pier.
  door walks   SCRIPTED PIE (IB_GARRISON_PIE=1): the real player pawn is set at each
               door's approach and driven through the threshold toward 3 m inside;
               the leaf's position and what finally stops the pawn are recorded.

Environment:
  IB_GARRISON_TARGET_LEVEL  a map under /Game/_GarrisonPreview_Disposable/
  IB_GARRISON_PLAN          a plan.json (design, routes)
  IB_GARRISON_DOORS         JSON: [{"building", "door_label", "door": [x, y, z], "normal": [nx, ny]}, ...]
  IB_GARRISON_WALKS         JSON: [{"name", "points": [[x, y], ...]}, ...]  extra scripted PIE walks
  IB_GARRISON_TAG           a name for this run
  IB_GARRISON_SHOTS         output folder (writes clearance_checks.json)
"""
import unreal, json, os, time, math, traceback, datetime
from pathlib import Path

PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
PAWN_CLASS = "/Game/Characters/Infantry/BP_IBCharacter_Infantry.BP_IBCharacter_Infantry_C"
DOOR_LEAF = "NODE_AddStaticMeshComponent-5"
TARGET = (os.environ.get("IB_GARRISON_TARGET_LEVEL") or "").strip().rstrip("/")
PLAN = os.environ.get("IB_GARRISON_PLAN")
DOORS = json.loads(os.environ.get("IB_GARRISON_DOORS") or "[]")
WALKS = json.loads(os.environ.get("IB_GARRISON_WALKS") or "[]")      # [{"name", "points": [[x, y], ...]}]
TAG = os.environ.get("IB_GARRISON_TAG") or TARGET
OUT = Path(os.environ.get("IB_GARRISON_SHOTS") or str(Path(unreal.Paths.project_saved_dir())
                                                        / "GarrisonRestructure/composition/clearance"))
DO_ROUTES = os.environ.get("IB_GARRISON_SWEEP_ROUTES") == "1"
DO_PIE = os.environ.get("IB_GARRISON_PIE") == "1"

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT.mkdir(parents=True, exist_ok=True)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
R = {"tool": "ib_garrison_clearance_check", "tag": TAG, "target": TARGET, "plan": PLAN, "doors_requested": DOORS,
     "started_utc": datetime.datetime.utcnow().isoformat() + "Z", "errors": [],
     "evidence_kinds": {"door_sweeps": "engine collision queries, Pawn profile, editor world; not movement",
                        "route_sweeps": "engine collision queries, Pawn profile, editor world; not movement",
                        "door_walks": "scripted PIE: the real pawn driven by movement input; not a person playing"}}


def log(m):
    unreal.log("GARRISON CLEARANCE: " + str(m))


def save():
    R["updated_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    (OUT / "clearance_checks.json").write_bytes(json.dumps(R, indent=1).encode("utf-8"))


def note_error(what):
    R["errors"].append({"what": what, "detail": traceback.format_exc()[-900:]})
    unreal.log_warning("GARRISON CLEARANCE: " + what + "\n" + traceback.format_exc()[-900:])


if not TARGET.startswith(PREVIEW_ROOT):
    R["errors"].append({"what": "refused", "detail": "target must be under " + PREVIEW_ROOT})
    save()
    raise RuntimeError("GARRISON CLEARANCE REFUSED: target must be under " + PREVIEW_ROOT)
plan = json.loads(Path(PLAN).read_text(encoding="utf-8")) if PLAN else {}
unreal.EditorLoadingAndSavingUtils.load_map(TARGET)
R["loaded"] = UES.get_editor_world().get_path_name().split(".")[0]
Z = float(plan.get("deck_z", 385.0))
save()


def pawn_dims():
    out = {"radius": 34.0, "half_height": 88.0, "max_step_height": 45.0, "source": "engine defaults"}
    try:
        cdo = unreal.get_default_object(unreal.load_class(None, PAWN_CLASS))
        cap = cdo.get_editor_property("capsule_component")
        out.update({"radius": float(cap.get_unscaled_capsule_radius()),
                    "half_height": float(cap.get_unscaled_capsule_half_height()), "source": PAWN_CLASS})
        out["max_step_height"] = float(cdo.get_editor_property("character_movement").get_editor_property("max_step_height"))
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
    """The walkable floor under (x, y), probed from just above head height of the deck
    level (or of the previous floor, when that is lower -- the land ramp), so a probe
    never starts on top of a structure it found before."""
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


def sweep(world, name, pts, dims, ignore=(), stop_at_first=False, deck_level=False):
    r, hh, step = dims["radius"], dims["half_height"], dims["max_step_height"]
    hb = max(r, (2.0 * hh - step) / 2.0)
    smp = samples(pts)
    floors, zprev = [], None
    for x, y in smp:
        if deck_level:
            floors.append((Z, "deck level (not probed)", False))
            continue
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
        h = trace(world, (ax, ay, za + step + hb), (bx, by, zb + step + hb), r, hb, ignore)
        if h:
            hits.append(dict(h, along_cm=round(dist, 0)))
            if stop_at_first:
                break
    distinct = {}
    for b in hits:
        key = "%s/%s" % (b["actor"], b["component"])
        distinct.setdefault(key, {"first_along_cm": b["along_cm"], "segments": 0, "at": b["impact"],
                                  "normal": b["normal"]})
        distinct[key]["segments"] += 1
    fz = [f[0] for f in floors if f[0] is not None]
    return {"name": name, "samples": len(smp), "length_m": round(dist / 100.0, 1),
            "no_floor_samples": sum(1 for f in floors if f[0] is None), "segments_skipped_no_floor": gaps,
            "floor_z": [round(min(fz), 1), round(max(fz), 1)] if fz else None,
            "floor_actors": sorted(set(str(f[1]) for f in floors if f[1])), "blocked_segments": len(hits),
            "clear": not hits and not gaps, "first_block": hits[0] if hits else None, "blockers": distinct}


def door_points(dr):
    n, d = dr["normal"], dr["door"]
    return [[d[0] + n[0] * 600.0, d[1] + n[1] * 600.0], [d[0] + n[0] * 150.0, d[1] + n[1] * 150.0],
            [d[0] - n[0] * 300.0, d[1] - n[1] * 300.0]]


def find_actor(world_actors, label, near):
    best = None
    for a in world_actors:
        try:
            lab = a.get_actor_label()
        except Exception:
            lab = a.get_name()
        if label not in (lab or ""):
            continue
        l = a.get_actor_location()
        dd = math.hypot(l.x - near[0], l.y - near[1])
        if best is None or dd < best[0]:
            best = (dd, a)
    return best[1] if best else None


def leaf(a):
    if a is None:
        return None
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name() == DOOR_LEAF:
            l = c.get_editor_property("relative_location")
            return {"leaf_rel_z": round(l.z, 1)}
    return {"leaf": "none"}


def door_sweeps(dims):
    world = UES.get_editor_world()
    acts = list(EAS.get_all_level_actors())
    out = []
    for dr in DOORS:
        pts = door_points(dr)
        a = find_actor(acts, dr["door_label"], dr["door"])
        row = {"building": dr["building"], "door_label": dr["door_label"], "door": dr["door"], "normal": dr["normal"],
               "door_actor": a.get_name() if a else None, "points": pts,
               "as_is": sweep(world, "approach -> threshold -> 3 m inside", pts, dims, stop_at_first=True,
                              deck_level=True),
               "ignoring_the_door_frame": sweep(world, "same, door-frame actor ignored", pts, dims,
                                                ignore=[a] if a else [], stop_at_first=True, deck_level=True),
               "floor": "deck level %.0f throughout (a floor probe at the door line lands on the closed leaf)" % Z}
        # How far behind the door line the first wall is, when the frame is ignored.
        fb = row["ignoring_the_door_frame"]["first_block"]
        if fb:
            n, d = dr["normal"], dr["door"]
            row["first_wall_behind_door_line_cm"] = round(-((fb["impact"][0] - d[0]) * n[0] +
                                                            (fb["impact"][1] - d[1]) * n[1]), 1)
        out.append(row)
    return out


def route_sweeps(dims):
    world = UES.get_editor_world()
    out = {"routes": [], "pier_lanes": None}
    for rt in plan.get("routes") or []:
        if rt.get("waypoints"):
            out["routes"].append(dict(sweep(world, rt["name"], rt["waypoints"], dims), kind=rt.get("crosses")))
    pr = (plan.get("design") or {}).get("pier")
    if pr:
        r = dims["radius"]
        lanes = []
        y = pr["y"][0] + r + 10.0
        while y <= pr["y"][1] - r - 10.0:
            s = sweep(world, "pier lane y=%.0f" % y, [[pr["x"][0] - 300.0, y], [pr["x"][1] - 300.0, y]], dims,
                      stop_at_first=True)
            fb = s["first_block"]
            lanes.append({"y": round(y, 1), "clear": s["clear"], "first_block_x": fb["impact"][0] if fb else None,
                          "first_block": ("%s/%s" % (fb["actor"], fb["component"])) if fb else None})
            y += 50.0
        clear = [ln["y"] for ln in lanes if ln["clear"]]
        out["pier_lanes"] = {"lanes": lanes, "clear_lanes_y": clear, "x_range": [pr["x"][0] - 300.0, pr["x"][1] - 300.0],
                             "summary": ("%d of %d pawn-wide lanes run the pier's full length" % (len(clear), len(lanes)))}
    return out


def pie_world():
    try:
        return UES.get_game_world()
    except Exception:
        return None


def flow():
    yield 15.0
    dims = pawn_dims()
    R["pawn"] = dims
    try:
        R["door_sweeps"] = door_sweeps(dims)
    except Exception:
        note_error("door sweeps")
    save()
    if DO_ROUTES:
        try:
            R["route_sweeps"] = route_sweeps(dims)
        except Exception:
            note_error("route sweeps")
        save()
    if not DO_PIE or not (DOORS or WALKS):
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
        R["pie_pawn"] = {"class": pawn.get_class().get_name(), "half_height": round(hh, 1),
                         "radius": round(cap.get_scaled_capsule_radius(), 1) if cap else None}
        yield 3.0
        game_actors = list(unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor))
        R["walks"] = []
        R["route_walks"] = []
        for wk in WALKS:
            pts = wk["points"]
            rec = {"name": wk["name"], "points": pts}
            try:
                x0, y0 = pts[0]
                sz = floor_z(gw, x0, y0, {"radius": 34.0, "half_height": hh})[0] or Z
                yaw = math.degrees(math.atan2(pts[1][1] - y0, pts[1][0] - x0))
                pawn.set_actor_location_and_rotation(V(x0, y0, sz + hh + 5.0), unreal.Rotator(0.0, 0.0, yaw), False,
                                                     True)
                yield 1.5
                L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
                t_start, wp, hist, last_t, result, traj = time.monotonic(), 1, [], 0.0, None, []
                while True:
                    l = pawn.get_actor_location()
                    t = time.monotonic() - t_start
                    if t - last_t >= 0.25:
                        hist.append((t, l.x, l.y))
                        traj.append([round(t, 2), round(l.x, 1), round(l.y, 1), round(l.z, 1)])
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
                    if old and t > 3.0 and math.hypot(l.x - old[-1][1], l.y - old[-1][2]) < 30.0:
                        result = "stalled"
                        break
                    if t > L / 200.0 + 20.0:
                        result = "timeout"
                        break
                    dx, dy = gx - l.x, gy - l.y
                    n = math.hypot(dx, dy) or 1.0
                    pawn.add_movement_input(V(dx / n, dy / n, 0.0), 1.0, False)
                    yield 0.0
                l = pawn.get_actor_location()
                rec.update({"result": result, "seconds": round(time.monotonic() - t_start, 2), "length_m": round(L / 100.0, 1),
                            "end": [round(l.x, 1), round(l.y, 1), round(l.z, 1)], "trajectory": traj[-120:],
                            "max_lateral_drift_cm": round(max(abs(q[2] - pts[0][1]) for q in traj), 1) if traj else None})
            except Exception:
                note_error("walk " + wk["name"])
                rec["result"] = rec.get("result") or "error"
            R["route_walks"].append(rec)
            save()
            yield 0.5
        for dr in DOORS:
            pts = door_points(dr)
            rec = {"building": dr["building"], "door_label": dr["door_label"], "points": pts}
            try:
                door_actor = find_actor(game_actors, dr["door_label"], dr["door"])
                x0, y0 = pts[0]
                sz = floor_z(gw, x0, y0, {"radius": 34.0, "half_height": hh})[0] or Z
                yaw = math.degrees(math.atan2(pts[1][1] - y0, pts[1][0] - x0))
                pawn.set_actor_location_and_rotation(V(x0, y0, sz + hh + 5.0), unreal.Rotator(0.0, 0.0, yaw), False,
                                                     True)
                yield 1.5
                rec["leaf_before"] = leaf(door_actor)
                t_start, wp, hist, last_t, lowest_leaf = time.monotonic(), 1, [], 0.0, None
                result = None
                while True:
                    l = pawn.get_actor_location()
                    t = time.monotonic() - t_start
                    lf = leaf(door_actor) or {}
                    if lf.get("leaf_rel_z") is not None:
                        lowest_leaf = lf["leaf_rel_z"] if lowest_leaf is None else min(lowest_leaf, lf["leaf_rel_z"])
                    if t - last_t >= 0.25:
                        hist.append((t, l.x, l.y))
                        last_t = t
                    gx, gy = pts[wp]
                    if math.hypot(gx - l.x, gy - l.y) < 60.0:
                        wp += 1
                        if wp >= len(pts):
                            result = "reached 3 m inside"
                            break
                        gx, gy = pts[wp]
                    old = [h for h in hist if t - h[0] >= 2.5]
                    if old and t > 3.0 and math.hypot(l.x - old[-1][1], l.y - old[-1][2]) < 30.0:
                        result = "stalled"
                        break
                    if t > 25.0:
                        result = "timeout"
                        break
                    dx, dy = gx - l.x, gy - l.y
                    n = math.hypot(dx, dy) or 1.0
                    pawn.add_movement_input(V(dx / n, dy / n, 0.0), 1.0, False)
                    yield 0.0
                l = pawn.get_actor_location()
                n2, d = dr["normal"], dr["door"]
                depth = -((l.x - d[0]) * n2[0] + (l.y - d[1]) * n2[1])
                rec.update({"result": result, "seconds": round(time.monotonic() - t_start, 2),
                            "end": [round(l.x, 1), round(l.y, 1), round(l.z, 1)],
                            "past_door_line_cm": round(depth, 1), "entered_building": depth > 250.0,
                            "leaf_lowest_rel_z": lowest_leaf,
                            "leaf_opened": lowest_leaf is not None and (rec.get("leaf_before") or {}).get("leaf_rel_z")
                            is not None and lowest_leaf < rec["leaf_before"]["leaf_rel_z"] - 50.0})
                if result == "stalled":
                    gx, gy = pts[min(wp, len(pts) - 1)]
                    dx, dy = gx - l.x, gy - l.y
                    n = math.hypot(dx, dy) or 1.0
                    rad = cap.get_scaled_capsule_radius() if cap else 34.0
                    rec["stopped_by"] = trace(gw, (l.x, l.y, l.z), (l.x + dx / n * 120.0, l.y + dy / n * 120.0, l.z),
                                              rad, hh, [pawn])
            except Exception:
                note_error("walk " + dr["door_label"])
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
log("started on %s (%s)" % (R["loaded"], TAG))
