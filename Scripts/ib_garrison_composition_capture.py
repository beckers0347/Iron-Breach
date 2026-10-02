"""P3 COMPOSITION candidate: lit captures, pawn clearance sweeps and scripted PIE walks.
Changes nothing and never saves.

    UnrealEditor.exe <project> -ExecutePythonScript="<Root>/Scripts/ib_garrison_composition_capture.py"

Loads the candidate named by IB_GARRISON_TARGET_LEVEL (must be under
/Game/_GarrisonPreview_Disposable/) and the reviewed P3 plan (IB_GARRISON_PLAN).
Three kinds of evidence, kept apart in the output:

  shots   the level viewport is moved to fixed cameras (no actor is spawned). The
          sun in this level is low over the sea (DirLight_PreDawn, yaw 165), so
          every camera looks landward or across with the sun behind it.
  sweeps  ENGINE collision queries in the editor world with the "Pawn" collision
          profile and the player pawn's own capsule (read from its class
          defaults): a floor probe under each route sample, then a BODY capsule
          (from the pawn's max step height to the top of its head) swept from
          sample to sample along every plan route, and through both relocated
          doorways. A blocking hit names what a walking pawn would meet. These are
          collision queries, not movement.
  walks   SCRIPTED PIE (IB_GARRISON_PIE=1): the real player pawn is set at each
          route's start and driven with movement input through the route's
          waypoints, then through each relocated doorway. Progress, stalls, falls
          and whether the door leaf moved are recorded. Not a person playing.

Writes <IB_GARRISON_SHOTS>/composition_checks.json (after every phase) and the PNGs,
then quits the editor.
"""
import unreal, json, os, time, math, traceback, datetime
from pathlib import Path

PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
PAWN_CLASS = "/Game/Characters/Infantry/BP_IBCharacter_Infantry.BP_IBCharacter_Infantry_C"
DOOR_LEAF = "NODE_AddStaticMeshComponent-5"          # BP_DoorFrame's door leaf (the audit's component list)
TARGET = (os.environ.get("IB_GARRISON_TARGET_LEVEL") or "").strip().rstrip("/")
PLAN = os.environ.get("IB_GARRISON_PLAN")
OUT = Path(os.environ.get("IB_GARRISON_SHOTS") or str(Path(unreal.Paths.project_saved_dir())
                                                        / "GarrisonRestructure/composition/shots"))
DO_PIE = os.environ.get("IB_GARRISON_PIE") == "1"
try:
    RES_X, RES_Y = (int(v) for v in os.environ.get("IB_GARRISON_RES", "1920x1080").lower().split("x"))
except Exception:
    RES_X, RES_Y = 1920, 1080

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT.mkdir(parents=True, exist_ok=True)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
RESULT = {"tool": "ib_garrison_composition_capture", "target": TARGET, "plan": PLAN,
          "started_utc": datetime.datetime.utcnow().isoformat() + "Z", "shots": [], "sweeps": {}, "walks": [],
          "errors": [], "evidence_kinds": {
              "shots": "level viewport cameras; no actor spawned",
              "sweeps": "engine collision queries, Pawn profile, editor world; not movement",
              "walks": "scripted PIE: the real pawn driven by movement input; not a person playing"}}


def log(m):
    unreal.log("GARRISON COMPOSITION CAPTURE: " + str(m))


def save_result():
    RESULT["updated_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    (OUT / "composition_checks.json").write_bytes(json.dumps(RESULT, indent=1).encode("utf-8"))


def note_error(what):
    RESULT["errors"].append({"what": what, "detail": traceback.format_exc()[-900:]})
    unreal.log_warning("GARRISON COMPOSITION CAPTURE: " + what + "\n" + traceback.format_exc()[-900:])


if not TARGET.startswith(PREVIEW_ROOT):
    RESULT["errors"].append({"what": "refused", "detail": "target must be under " + PREVIEW_ROOT})
    save_result()
    raise RuntimeError("GARRISON COMPOSITION CAPTURE REFUSED: target must be under " + PREVIEW_ROOT)
plan = json.loads(Path(PLAN).read_text(encoding="utf-8"))
if not plan.get("composition"):
    RESULT["errors"].append({"what": "refused", "detail": "the plan is not a P3 composition plan"})
    save_result()
    raise RuntimeError("GARRISON COMPOSITION CAPTURE REFUSED: the plan has no composition")
unreal.EditorLoadingAndSavingUtils.load_map(TARGET)
RESULT["loaded"] = UES.get_editor_world().get_path_name().split(".")[0]
LEVEL_PREFIX = "%s.%s:PersistentLevel." % (TARGET, TARGET.split("/")[-1])
SRC_PREFIX = "/Game/LevelPrototyping/CarrowGateGarrison.CarrowGateGarrison:PersistentLevel."
actors = {a.get_path_name(): a for a in EAS.get_all_level_actors()}
RESULT["generated_actors_in_level"] = sum(1 for a in actors.values()
                                          if plan["run_tag"] in [str(t) for t in (a.get_editor_property("tags") or [])])
placed = {}
for m in plan["moves"]:
    if not str(m.get("role", "")).startswith("assembly"):
        continue
    a = actors.get(LEVEL_PREFIX + m["identity"][len(SRC_PREFIX):])
    if a is None:
        placed[m["label"]] = "MISSING"
        continue
    l, r = a.get_actor_location(), a.get_actor_rotation()
    placed[m["label"]] = {"loc": [round(l.x, 1), round(l.y, 1), round(l.z, 1)], "yaw": round(r.yaw, 3),
                          "planned_loc": m["to"]["loc"], "planned_yaw": m["to"]["rot"]["yaw"],
                          "at_plan": abs(l.x - m["to"]["loc"][0]) < 0.6 and abs(l.y - m["to"]["loc"][1]) < 0.6
                          and abs(((r.yaw - m["to"]["rot"]["yaw"]) + 180) % 360 - 180) < 0.06}
RESULT["assemblies_in_level"] = placed
save_result()

Z = float(plan["deck_z"])
fr, d = plan["frame"], plan["design"]
front, centre, D = fr["front"], fr["centre"], float(fr["depth"])
axis = float(d["spine"]["axis_y"])
comp = plan["composition"]
CMD, MH = comp["buildings"]["Command"], comp["buildings"]["Mess_Hall"]
res = plan.get("hangar_reserve") or {}
rx = sum(res.get("x", [0, 0])) / 2.0
V = unreal.Vector


def look(eye, target):
    return unreal.MathLibrary.find_look_at_rotation(V(*eye), V(*target))


def cam_toward(target, direction_deg, dist, height):
    a = math.radians(direction_deg)
    return (target[0] + dist * math.cos(a), target[1] + dist * math.sin(a), Z + height)


mid = ((CMD["to"]["door_loc"][0] + MH["to"]["door_loc"][0]) / 2.0,
       (CMD["to"]["door_loc"][1] + MH["to"]["door_loc"][1]) / 2.0, Z + 300.0)
cmd_door, mh_door = CMD["to"]["door_loc"], MH["to"]["door_loc"]
SHOTS = [
    ("overhead-reference", (front[0] + 0.42 * D, axis, Z + 0.95 * D), (centre[0] + 0.08 * D, axis, Z), None),
    ("overhead-topdown", (centre[0], axis, Z + 1.35 * D), None, unreal.Rotator(roll=0.0, pitch=-89.9, yaw=180.0)),
    # both entrances: from over the spine at the seaward corner, sun behind the camera
    ("control-platform", cam_toward(mid, -51.5, 5000.0, 3200.0), mid, None),
    # the tower's entrance from its own apron, sun directly behind the camera
    ("control-tower-entrance", (cmd_door[0] + 1800.0, cmd_door[1] - 600.0, Z + 350.0),
     (cmd_door[0], cmd_door[1], Z + 250.0), None),
    # the low block's entrance from the spine
    ("control-lowblock-entrance", (mh_door[0] + 900.0, mh_door[1] - 1900.0, Z + 300.0),
     (mh_door[0], mh_door[1], Z + 250.0), None),
    # toward the rear reservation: elevated, then at eye height; looking landward, sun behind
    ("rear-reservation", (9800.0, axis - 650.0, Z + 1100.0), (rx, axis, Z), None),
    ("rear-reservation-eye", (8600.0, axis, Z + 180.0), (rx, axis, Z + 400.0), None),
]


# -- version-tolerant editor calls (UE 5.8 added a required viewport_config_key) ----------------

def call_first(what, attempts):
    last = None
    for label, fn in attempts:
        try:
            out = fn()
            RESULT.setdefault("api_used", {})[what] = label
            return out
        except Exception as error:
            last = error
            seen = RESULT.setdefault("api_failed", {}).setdefault(what, [])
            if not any(x.startswith(label + ": ") for x in seen):
                seen.append(label + ": " + (str(error).splitlines() or [""])[-1][:160])
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
         lambda: UES.set_level_viewport_camera_info(loc, rot)),
        ("LevelEditorSubsystem.set_level_viewport_camera_info(loc, rot)",
         lambda: LES.set_level_viewport_camera_info(loc, rot))])


def game_view(on):
    return call_first("game_view", [
        ("LevelEditorSubsystem.editor_set_game_view(on)", lambda: LES.editor_set_game_view(on)),
        ("LevelEditorSubsystem.editor_set_game_view(on, active key)",
         lambda: LES.editor_set_game_view(on, viewport_key()))])


# -- pawn-profile collision queries -------------------------------------------------------------

def pawn_dims():
    out = {"radius": 34.0, "half_height": 88.0, "max_step_height": 45.0, "source": "engine defaults"}
    try:
        cdo = unreal.get_default_object(unreal.load_class(None, PAWN_CLASS))
        cap = cdo.get_editor_property("capsule_component")
        out.update({"radius": float(cap.get_unscaled_capsule_radius()),
                    "half_height": float(cap.get_unscaled_capsule_half_height()),
                    "source": PAWN_CLASS + " class defaults"})
        mv = cdo.get_editor_property("character_movement")
        out["max_step_height"] = float(mv.get_editor_property("max_step_height"))
        out["max_walk_speed"] = float(mv.get_editor_property("max_walk_speed"))
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
    return {"initial_overlap": bool(f[1]), "time": round(float(f[2]), 4), "loc": [round(f[4].x, 1), round(f[4].y, 1),
                                                                                  round(f[4].z, 1)],
            "impact": [round(f[5].x, 1), round(f[5].y, 1), round(f[5].z, 1)],
            "normal": [round(f[7].x, 3), round(f[7].y, 3), round(f[7].z, 3)],
            "actor": act.get_actor_label() if act and hasattr(act, "get_actor_label") else None,
            "component": comp_.get_name() if comp_ else None}


def trace(world, a, b, radius, hh, ignore=()):
    r = unreal.SystemLibrary.capsule_trace_single_by_profile(world, V(*a), V(*b), radius, hh, "Pawn", False,
                                                             list(ignore), unreal.DrawDebugTrace.NONE, True)
    return decode(r)


def floor_z(world, x, y, dims, near=None):
    z0 = (near if near is not None else Z)
    h = trace(world, (x, y, z0 + 500.0), (x, y, z0 - 1200.0), dims["radius"] * 0.5, dims["radius"] * 0.5)
    return (h["impact"][2], h["actor"]) if h else (None, None)


def samples(pts, step=50.0):
    out = [tuple(pts[0])]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L // step))
        for k in range(1, n + 1):
            out.append((ax + (bx - ax) * k / n, ay + (by - ay) * k / n))
    return out


def sweep_route(world, name, pts, dims, kind):
    """Floor under every sample, then a body capsule (step height to head) from sample to sample."""
    r, hh, step = dims["radius"], dims["half_height"], dims["max_step_height"]
    hb = max(r, (2.0 * hh - step) / 2.0)
    smp = samples(pts)
    floors = []
    zprev = None
    for x, y in smp:
        z, act = floor_z(world, x, y, dims, zprev)
        floors.append((z, act))
        zprev = z if z is not None else zprev
    blocks, dist, gaps = [], 0.0, 0
    for k in range(1, len(smp)):
        (ax, ay), (bx, by) = smp[k - 1], smp[k]
        dist += math.hypot(bx - ax, by - ay)
        za, zb = floors[k - 1][0], floors[k][0]
        if za is None or zb is None:
            gaps += 1
            continue
        h = trace(world, (ax, ay, za + step + hb), (bx, by, zb + step + hb), r, hb)
        if h:
            blocks.append(dict(h, along_cm=round(dist, 0)))
    distinct = {}
    for b in blocks:
        key = "%s/%s" % (b["actor"], b["component"])
        distinct.setdefault(key, {"first_along_cm": b["along_cm"], "segments": 0, "at": b["impact"],
                                  "normal": b["normal"]})
        distinct[key]["segments"] += 1
    fz = [f[0] for f in floors if f[0] is not None]
    return {"name": name, "kind": kind, "waypoints": pts, "samples": len(smp), "length_m": round(dist / 100.0, 1),
            "no_floor_samples": sum(1 for f in floors if f[0] is None), "segments_skipped_no_floor": gaps,
            "floor_z": [round(min(fz), 1), round(max(fz), 1)] if fz else None,
            "floor_actors": sorted(set(str(f[1]) for f in floors if f[1])),
            "blocked_segments": len(blocks), "clear": not blocks and not gaps, "blockers": distinct}


def door_threshold(b):
    n = b["door_normal"]
    dl = b["to"]["door_loc"]
    return [[round(b["approach"][0], 1), round(b["approach"][1], 1)],
            [round(dl[0] + n[0] * 150.0, 1), round(dl[1] + n[1] * 150.0, 1)],
            [round(dl[0] - n[0] * 300.0, 1), round(dl[1] - n[1] * 300.0, 1)]]


def physics_sweeps():
    world = UES.get_editor_world()
    dims = pawn_dims()
    out = {"method": "capsule_trace_single_by_profile('Pawn'), the pawn's own capsule; body capsule from max step "
                     "height to head height; editor world, doors in their editor state",
           "pawn": dims, "routes": []}
    for rt in plan.get("routes") or []:
        if rt.get("waypoints"):
            out["routes"].append(sweep_route(world, rt["name"], rt["waypoints"], dims, rt.get("crosses")))
    for lab, b in (("Command", CMD), ("Mess_Hall", MH)):
        out["routes"].append(sweep_route(world, "%s doorway: approach -> threshold -> 3 m inside" % lab,
                                         door_threshold(b), dims, "doorway"))
    gate = [p for p in plan["checks"]["paths"] if p["path"].startswith("city road")]
    if gate:
        out["routes"].append(sweep_route(world, "existing route: city road -> land ramp -> gate -> forecourt",
                                         gate[0]["points"] + [[gate[0]["points"][-1][0] + 1500.0,
                                                               gate[0]["points"][-1][1]]], dims, "existing"))
    return out


# -- scripted PIE walks ---------------------------------------------------------------------------

def walks():
    """(name, kind, waypoints, door label or None)"""
    out = []
    for rt in plan.get("routes") or []:
        if rt.get("waypoints"):
            out.append((rt["name"], rt.get("crosses"), rt["waypoints"], None))
    for lab, b in (("Command", CMD), ("Mess_Hall", MH)):
        rt = [r for r in plan["routes"] if r["name"] == "spine -> %s approach" % b["door_label"]]
        pts = (rt[0]["waypoints"] if rt else [b["approach"]])[:-1] + door_threshold(b)
        out.append(("walk into %s through %s" % (lab, b["door_label"]), "doorway", pts, b["door_label"]))
    gate = [p for p in plan["checks"]["paths"] if p["path"].startswith("city road")]
    if gate:
        pts = gate[0]["points"] + [[gate[0]["points"][-1][0] + 1500.0, gate[0]["points"][-1][1]]]
        out.append(("existing route: city road -> gate -> forecourt", "existing", pts, "BP_MainGateDoor"))
    return out


def pie_world():
    try:
        return UES.get_game_world()
    except Exception:
        return None


def door_leaf_state(gw, door_label, near):
    best = None
    for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor):
        try:
            lab = a.get_actor_label()
        except Exception:
            lab = a.get_name()
        if door_label not in (lab or "") and door_label not in a.get_name():
            continue
        l = a.get_actor_location()
        dd = math.hypot(l.x - near[0], l.y - near[1])
        if best is None or dd < best[0]:
            best = (dd, a)
    if best is None:
        return None
    a = best[1]
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name() == DOOR_LEAF:
            l, r = c.get_editor_property("relative_location"), c.get_editor_property("relative_rotation")
            return {"actor": a.get_name(), "leaf_rel": [round(l.x, 1), round(l.y, 1), round(l.z, 1)],
                    "leaf_yaw": round(r.yaw, 2), "leaf_visible": bool(c.is_visible()),
                    "leaf_collision": str(c.get_collision_enabled()).split(".")[-1].split(":")[0].strip("<> ")}
    return {"actor": a.get_name(), "leaf": "no %s component" % DOOR_LEAF}


def flow():
    """A generator driven by the slate tick: each yield is the number of seconds to wait."""
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
            RESULT["shots"].append({"name": name, "file": str(OUT / (name + ".png")), "eye": [round(v, 1) for v in eye],
                                    "target": [round(v, 1) for v in target] if target else None, "requested": bool(ok)})
            log("shot " + name)
        except Exception:
            note_error("screenshot " + name)
        save_result()
        yield 5.0
    try:
        RESULT["sweeps"] = physics_sweeps()
    except Exception:
        note_error("sweeps")
    save_result()
    if not DO_PIE:
        return
    try:
        call_first("begin_play", [("LevelEditorSubsystem.editor_request_begin_play()",
                                   lambda: LES.editor_request_begin_play())])
    except Exception:
        note_error("begin play")
        return
    t0 = time.monotonic()
    pawn = gw = None
    while time.monotonic() - t0 < 45.0:
        yield 1.0
        gw = pie_world()
        pawn = unreal.GameplayStatics.get_player_pawn(gw, 0) if gw else None
        if pawn:
            break
    if not pawn:
        RESULT["walks_error"] = "no player pawn in PIE within 45 s"
        save_result()
    else:
        cap = pawn.get_component_by_class(unreal.CapsuleComponent)
        RESULT["pie_pawn"] = {"class": pawn.get_class().get_name(),
                              "radius": round(cap.get_scaled_capsule_radius(), 1) if cap else None,
                              "half_height": round(cap.get_scaled_capsule_half_height(), 1) if cap else None}
        hh = cap.get_scaled_capsule_half_height() if cap else 90.0
        yield 3.0
        for name, kind, pts, door in walks():
            rec = {"name": name, "kind": kind, "waypoints": pts, "door": door}
            try:
                x0, y0 = pts[0]
                sz = floor_z(gw, x0, y0, {"radius": 34.0, "half_height": hh})[0]
                sz = sz if sz is not None else Z
                yaw = math.degrees(math.atan2(pts[1][1] - y0, pts[1][0] - x0))
                pawn.set_actor_location_and_rotation(V(x0, y0, sz + hh + 5.0), unreal.Rotator(0.0, 0.0, yaw),
                                                     False, True)
                yield 1.5
                if door:
                    rec["door_before"] = door_leaf_state(gw, door, pts[-2])
                L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
                limit = L / 200.0 + 20.0
                t_start, wp, traj, last_t, hist = time.monotonic(), 1, [], 0.0, []
                door_seen = None
                result = None
                while True:
                    l = pawn.get_actor_location()
                    t = time.monotonic() - t_start
                    if t - last_t >= 0.25:
                        traj.append([round(t, 2), round(l.x, 1), round(l.y, 1), round(l.z, 1)])
                        hist.append((t, l.x, l.y))
                        last_t = t
                    gx, gy = pts[wp]
                    if math.hypot(gx - l.x, gy - l.y) < 70.0:
                        wp += 1
                        if door and wp == len(pts) - 1:
                            door_seen = door_leaf_state(gw, door, pts[-2])
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
                            "seconds": round(time.monotonic() - t_start, 2),
                            "end": [round(l.x, 1), round(l.y, 1), round(l.z, 1)], "trajectory": traj[-160:]})
                if result == "stalled":
                    gx, gy = pts[min(wp, len(pts) - 1)]
                    dx, dy = gx - l.x, gy - l.y
                    n = math.hypot(dx, dy) or 1.0
                    rad = cap.get_scaled_capsule_radius() if cap else 34.0
                    h = trace(gw, (l.x, l.y, l.z), (l.x + dx / n * 120.0, l.y + dy / n * 120.0, l.z), rad, hh, [pawn])
                    rec["blocked_by"] = h
                if door:
                    rec["door_at_threshold"] = door_seen
                    rec["door_after"] = door_leaf_state(gw, door, pts[-2])
                    rec["door_leaf_moved"] = bool(rec.get("door_before") and rec.get("door_at_threshold") and
                                                  rec["door_before"].get("leaf_rel") != rec["door_at_threshold"].get("leaf_rel"))
                    if kind == "doorway":
                        b = CMD if door == CMD["door_label"] else MH
                        dl, n2 = b["to"]["door_loc"], b["door_normal"]
                        depth = (l.x - dl[0]) * n2[0] + (l.y - dl[1]) * n2[1]
                        rec["inside_by_cm"] = round(-depth, 1)
                        rec["entered"] = depth < -100.0
            except Exception:
                note_error("walk " + name)
                rec["result"] = rec.get("result") or "error"
            RESULT["walks"].append(rec)
            save_result()
            yield 0.5
    try:
        call_first("end_play", [("LevelEditorSubsystem.editor_request_end_play()",
                                 lambda: LES.editor_request_end_play())])
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
    RESULT["dirty_map_packages_at_exit"] = dirty
    RESULT["finished_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    save_result()
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
        save_result()
        try:
            LES.editor_request_end_play()
        except Exception:
            pass
        finish()
    finally:
        state["busy"] = False


state["handle"] = unreal.register_slate_post_tick_callback(tick)
log("started on " + RESULT["loaded"])
