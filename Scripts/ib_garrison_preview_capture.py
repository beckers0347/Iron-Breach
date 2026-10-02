"""Captures and physics checks of the DISPOSABLE garrison preview. Changes nothing, never saves.

    UnrealEditor.exe <project> -ExecutePythonScript="<Root>/Scripts/ib_garrison_preview_capture.py"

Needs the editor's render and tick loop (a commandlet has neither, and a
commandlet world answered no scene queries at all). Loads the preview map named
by IB_GARRISON_TARGET_LEVEL, which must be under /Game/_GarrisonPreview_Disposable/,
and then:

  1. SHOTS, framed from the reviewed plan's frame (IB_GARRISON_PLAN): an oblique
     overhead framed like the approved reference (over the sea beyond the pad,
     looking back at the compound: land at the top of the frame, the docks side
     on the right), a straight top-down, and ground views. The level viewport is
     moved; no actor is spawned.
  2. EDITOR-WORLD PHYSICS: pawn-sized capsule sweeps (simple collision, the way
     character movement collides; WorldStatic + WorldDynamic) straight down onto
     every plan path, along the deck seams, and over the proposed water gaps and
     the old apron. These are engine collision queries, not play.
  3. PLAY (IB_GARRISON_PIE=1): Play-In-Editor. The player pawn is set down on the
     spine beside the channel, then above the channel, and read back after it
     falls: back on dry ground means Drown() snapped it back; resting near the
     waterline means the water plane holds pawns. PIE never touches the editor
     level.

Writes <IB_GARRISON_SHOTS>/preview_checks.json (updated after every phase) and the
PNGs. Quits the editor at the end.
"""
import unreal, json, os, time, math, traceback, datetime
from pathlib import Path

PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
TARGET = (os.environ.get("IB_GARRISON_TARGET_LEVEL") or "").strip().rstrip("/")
PLAN = os.environ.get("IB_GARRISON_PLAN")
OUT = Path(os.environ.get("IB_GARRISON_SHOTS") or str(Path(unreal.Paths.project_saved_dir())
                                                        / "GarrisonRestructure/preview/shots"))
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
RESULT = {"tool": "ib_garrison_preview_capture", "target": TARGET, "plan": PLAN,
          "started_utc": datetime.datetime.utcnow().isoformat() + "Z", "shots": [], "physics": {}, "pie": None,
          "errors": []}


def log(m):
    unreal.log("GARRISON PREVIEW CAPTURE: " + str(m))


def save_result():
    RESULT["updated_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    (OUT / "preview_checks.json").write_bytes(json.dumps(RESULT, indent=1).encode("utf-8"))


def note_error(what):
    RESULT["errors"].append({"what": what, "detail": traceback.format_exc()[-900:]})
    unreal.log_warning("GARRISON PREVIEW CAPTURE: " + what + "\n" + traceback.format_exc()[-900:])


if not TARGET.startswith(PREVIEW_ROOT):
    RESULT["errors"].append({"what": "refused", "detail": "target must be under " + PREVIEW_ROOT})
    save_result()
    raise RuntimeError("GARRISON PREVIEW CAPTURE REFUSED: target must be under " + PREVIEW_ROOT)
plan = json.loads(Path(PLAN).read_text(encoding="utf-8"))
unreal.EditorLoadingAndSavingUtils.load_map(TARGET)
world_pkg = UES.get_editor_world().get_path_name().split(".")[0]
RESULT["loaded"] = world_pkg
generated = [a for a in EAS.get_all_level_actors()
             if plan["run_tag"] in [str(t) for t in (a.get_editor_property("tags") or [])]]
RESULT["generated_actors_in_level"] = len(generated)
save_result()

fr, d = plan["frame"], plan["design"]
Z = float(plan["deck_z"])
front, centre, D = fr["front"], fr["centre"], float(fr["depth"])
axis = float(d["spine"]["axis_y"])
pad = d["pad"]["centre"]
res = plan.get("hangar_reserve") or {}
rx = sum(res.get("x", [0, 0])) / 2.0
pier_y = sum(d["pier"]["y"]) / 2.0


def look(eye, target):
    return unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*eye), unreal.Vector(*target))


SHOTS = [
    ("overhead-reference", (front[0] + 0.42 * D, axis, Z + 0.95 * D), (centre[0] + 0.08 * D, axis, Z), None),
    ("overhead-topdown", (centre[0], axis, Z + 1.35 * D), None, unreal.Rotator(roll=0.0, pitch=-89.9, yaw=180.0)),
    ("ground-spine-to-pad", (d["spine"]["x"][0] + 600.0, axis - 300.0, Z + 180.0), (pad[0], pad[1], Z + 250.0), None),
    ("ground-pad-to-hangar-reserve", (pad[0] - 800.0, axis, Z + 180.0), (rx, axis, Z + 600.0), None),
    ("ground-pier-and-berth", (d["pier"]["x"][0] + 400.0, pier_y, Z + 200.0),
     (d["pier"]["x"][1], pier_y - 1500.0, Z + 200.0), None),
    ("ground-channel", (d["spine"]["x"][0] + 300.0, (d["pier"]["y"][1] + d["spine"]["y"][0]) / 2.0, Z + 250.0),
     (d["pier"]["x"][1], (d["pier"]["y"][1] + d["spine"]["y"][0]) / 2.0, Z - 300.0), None),
]


def decode(result):
    if result is None:
        return {"hit": False}
    hit = result
    if isinstance(result, (list, tuple)):
        if not result or not bool(result[0]):
            return {"hit": False}
        hit = result[1] if len(result) > 1 else None
    if hit is None:
        return {"hit": False}
    fields = hit.to_tuple()
    loc, act = fields[4], (fields[9] if len(fields) > 9 else None)
    return {"hit": bool(fields[0]), "z": round(float(loc.z), 1),
            "actor": act.get_actor_label() if act and hasattr(act, "get_actor_label") else None}


def sweep(world, x, y, top, bottom):
    """A standing pawn's capsule (radius 34, half height 88) swept straight down."""
    objs = [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2]
    r = unreal.SystemLibrary.capsule_trace_single_for_objects(
        world, unreal.Vector(x, y, top), unreal.Vector(x, y, bottom), 34.0, 88.0, objs, False, [],
        unreal.DrawDebugTrace.NONE, True)
    out = decode(r)
    if out.get("hit"):
        out["ground_z"] = round(out["z"] - 88.0, 1)     # capsule centre at impact minus half height
    return out


def ramp_z(x):
    rp = (plan.get("site") or {}).get("ramp")
    if not rp:
        return None
    (x0, x1), (z0, z1) = rp["x"], rp["z"]
    if x0 <= x <= x1:
        return z0 + (x - x0) * (z1 - z0) / (x1 - x0)
    return None


def physics_checks():
    world = UES.get_editor_world()
    out = {"method": "capsule_trace_single_for_objects r34 hh88, WorldStatic+WorldDynamic, simple collision"}
    paths = []
    for p in plan["checks"].get("paths", []):
        pts = p.get("points") or []
        samples, missing, off, actors = 0, [], [], {}
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(bx - ax, by - ay) // 100.0))
            for k in range(n + 1):
                x, y = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
                want = ramp_z(x) if ramp_z(x) is not None and p["path"].startswith("city road") else Z
                h = sweep(world, x, y, want + 400.0, want - 900.0)
                samples += 1
                if not h.get("hit"):
                    missing.append([round(x), round(y)])
                    continue
                actors[h.get("actor")] = actors.get(h.get("actor"), 0) + 1
                if abs(h["ground_z"] - want) > 15.0 and not (h.get("actor") or "").startswith("IBGC_"):
                    off.append([round(x), round(y), h["ground_z"], h.get("actor")])
        paths.append({"path": p["path"], "samples": samples, "no_ground": len(missing), "first_missing": missing[:5],
                      "unexpected_ground": off[:8], "ground_actors": actors})
    out["paths"] = paths
    seams = []
    sx = d["spine"]["x"]
    for label, pts in (
            ("forecourt|spine x=%.0f" % sx[0], [(sx[0] + dx, y) for y in (d["spine"]["y"][0] + 100.0, axis,
                                                                       d["spine"]["y"][1] - 100.0) for dx in (-2.0, 2.0)]),
            ("spine|pad x=%.0f" % sx[1], [(sx[1] + dx, y) for y in (axis - 500.0, axis, axis + 500.0) for dx in (-2.0, 2.0)]),
            ("forecourt|pier x=%.0f" % d["pier"]["x"][0], [(d["pier"]["x"][0] + dx, pier_y) for dx in (-2.0, 2.0)]),
            ("spine|control y=%.0f" % d["spine"]["y"][1], [(12800.0, d["spine"]["y"][1] + dy) for dy in (-2.0, 2.0)])):
        hs = [sweep(world, x, y, Z + 400.0, Z - 900.0) for x, y in pts]
        seams.append({"seam": label, "samples": len(hs), "hits": sum(1 for h in hs if h.get("hit")),
                      "ground_z": sorted(set(h.get("ground_z") for h in hs if h.get("hit"))),
                      "actors": sorted(set(str(h.get("actor")) for h in hs if h.get("hit")))})
    out["seams"] = seams
    gaps = []
    for g in plan["checks"].get("gaps", []):
        xs, ys = [q[0] for q in g["polygon"]], [q[1] for q in g["polygon"]]
        pts = [(min(xs) + (max(xs) - min(xs)) * i / 6.0, (min(ys) + max(ys)) / 2.0) for i in range(1, 6)]
        hs = [sweep(world, x, y, Z + 400.0, -1500.0) for x, y in pts]
        gaps.append({"gap": g["gap"], "samples": len(hs), "blocking_hits": [h for h in hs if h.get("hit")]})
    apron = [(13000.0, -3000.0), (11500.0, -5000.0), (15500.0, 4800.0)]
    hs = [sweep(world, x, y, Z + 400.0, -1500.0) for x, y in apron]
    gaps.append({"gap": "old apron area (now water)", "samples": len(hs), "blocking_hits": [h for h in hs if h.get("hit")]})
    out["gaps"] = gaps
    return out


state = {"phase": "settle", "due": time.monotonic() + 20.0, "i": 0, "busy": False, "handle": None,
         "pie_t0": None, "pawn_rest": None}


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


def call_first(what, attempts):
    """Try each (label, callable) in turn; record which one worked. UE 5.8 changed some editor
    signatures (set_level_viewport_camera_info gained a required viewport_config_key)."""
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
         lambda: LES.set_level_viewport_camera_info(loc, rot)),
        ("EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)",
         lambda: unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot))])


def game_view(on):
    return call_first("game_view", [
        ("LevelEditorSubsystem.editor_set_game_view(on)", lambda: LES.editor_set_game_view(on)),
        ("LevelEditorSubsystem.editor_set_game_view(on, active key)",
         lambda: LES.editor_set_game_view(on, viewport_key()))])


def pie_world():
    try:
        return UES.get_game_world()
    except Exception:
        return None


def tick(dt):
    if state["busy"] or time.monotonic() < state["due"]:
        return
    state["busy"] = True
    try:
        ph = state["phase"]
        if ph == "settle":
            try:
                game_view(True)
            except Exception:
                note_error("game view on")
            state["phase"], state["due"] = "camera", time.monotonic() + 1.0
        elif ph == "camera":
            if state["i"] >= len(SHOTS) or state.get("camera_broken"):
                state["phase"], state["due"] = "physics", time.monotonic() + 1.0
            else:
                name, eye, target, rot = SHOTS[state["i"]]
                rot = rot or look(eye, target)
                try:
                    set_camera(unreal.Vector(*eye), rot)
                    state["phase"], state["due"] = "shoot", time.monotonic() + 12.0
                except Exception:
                    note_error("camera for " + name + " (no camera API worked; shots skipped)")
                    state["camera_broken"] = True
                    state["due"] = time.monotonic() + 0.5
        elif ph == "shoot":
            name, eye, target, rot = SHOTS[state["i"]]
            try:
                ok = unreal.AutomationLibrary.take_high_res_screenshot(RES_X, RES_Y, str(OUT / (name + ".png")))
                RESULT["shots"].append({"name": name, "file": str(OUT / (name + ".png")), "eye": list(eye),
                                        "target": list(target) if target else None, "requested": bool(ok)})
                log("shot " + name)
            except Exception:
                note_error("screenshot " + name)
            save_result()
            state["i"] += 1
            state["phase"], state["due"] = "camera", time.monotonic() + 5.0
        elif ph == "physics":
            try:
                RESULT["physics"] = physics_checks()
            except Exception:
                note_error("physics checks")
            save_result()
            if DO_PIE:
                state["phase"], state["due"] = "pie-start", time.monotonic() + 1.0
            else:
                finish()
                return
        elif ph == "pie-start":
            RESULT["pie"] = {"requested": True}
            call_first("begin_play", [("LevelEditorSubsystem.editor_request_begin_play()",
                                       lambda: LES.editor_request_begin_play())])
            state["pie_t0"] = time.monotonic()
            state["phase"], state["due"] = "pie-find", time.monotonic() + 12.0
        elif ph == "pie-find":
            gw = pie_world()
            pawn = unreal.GameplayStatics.get_player_pawn(gw, 0) if gw else None
            if pawn is None:
                if time.monotonic() - state["pie_t0"] < 45.0:
                    state["due"] = time.monotonic() + 3.0
                    return
                RESULT["pie"].update({"result": "no player pawn in PIE within 45 s", "game_world": bool(gw)})
                state["phase"], state["due"] = "pie-stop", time.monotonic() + 0.5
                return
            RESULT["pie"]["pawn_class"] = pawn.get_class().get_name()
            spot = (12000.0, d["spine"]["y"][0] + 250.0, Z + 150.0)
            pawn.set_actor_location(unreal.Vector(*spot), False, True)
            RESULT["pie"]["placed_on_spine"] = list(spot)
            state["pawn"] = pawn
            state["phase"], state["due"] = "pie-rest", time.monotonic() + 3.0
        elif ph == "pie-rest":
            l = state["pawn"].get_actor_location()
            state["pawn_rest"] = [round(l.x, 1), round(l.y, 1), round(l.z, 1)]
            RESULT["pie"]["rest_on_spine"] = state["pawn_rest"]
            over = (12000.0, (d["pier"]["y"][1] + d["spine"]["y"][0]) / 2.0, Z + 150.0)
            state["pawn"].set_actor_location(unreal.Vector(*over), False, True)
            RESULT["pie"]["placed_over_channel"] = list(over)
            state["over_t"] = round(time.monotonic() - state["pie_t0"], 2)
            RESULT["pie"]["placed_over_channel_at_s"] = state["over_t"]
            state["samples"] = []
            state["phase"], state["due"] = "pie-fall", time.monotonic() + 0.25
        elif ph == "pie-fall":
            # Sample every 0.25 s for up to 20 s; stop early once the pawn has fallen
            # below the deck and is standing back at its spine rest spot.
            l = state["pawn"].get_actor_location()
            state["samples"].append([round(time.monotonic() - state["pie_t0"], 2), round(l.x, 1), round(l.y, 1),
                                     round(l.z, 1)])
            rest = state["pawn_rest"]
            lowest = min(s[3] for s in state["samples"])
            fell = lowest < Z - 150.0
            home = math.hypot(l.x - rest[0], l.y - rest[1]) < 150.0 and abs(l.z - rest[2]) < 60.0
            if len(state["samples"]) < 80 and not (fell and home):
                state["due"] = time.monotonic() + 0.25
                return
            end = state["samples"][-1]
            water_z = float(plan.get("water_z", -35.0))
            placed = RESULT["pie"]["placed_over_channel"]
            held = abs(end[1] - placed[0]) < 150.0 and abs(end[2] - placed[1]) < 150.0 and end[3] > Z - 150.0
            RESULT["pie"].update({"trajectory": state["samples"], "lowest_z": lowest, "fell_below_deck": fell,
                                  "returned_to_spine": fell and home,
                                  "seconds_from_drop_to_return": (round(end[0] - state["over_t"], 2)
                                                                  if fell and home else None),
                                  "result": ("fell into the channel and was returned to the spine rest spot"
                                             if fell and home else
                                             "did not fall: something above the channel held the pawn" if held else
                                             ("resting near the waterline: the water held the pawn"
                                              if abs(end[3] - (water_z + 90.0)) < 60.0 else
                                              "neither returned within 20 s nor resting at the waterline; "
                                              "see trajectory"))})
            state["phase"], state["due"] = "pie-stop", time.monotonic() + 0.5
        elif ph == "pie-stop":
            try:
                call_first("end_play", [("LevelEditorSubsystem.editor_request_end_play()",
                                         lambda: LES.editor_request_end_play())])
            except Exception:
                note_error("end play")
            save_result()
            state["phase"], state["due"] = "done", time.monotonic() + 4.0
        elif ph == "done":
            finish()
            return
    except Exception:
        note_error("phase " + state["phase"])
        save_result()
        if state["phase"].startswith("pie") and state["phase"] != "pie-stop":
            state["phase"], state["due"] = "pie-stop", time.monotonic() + 0.5
        else:
            finish()
    finally:
        state["busy"] = False


state["handle"] = unreal.register_slate_post_tick_callback(tick)
log("started on " + world_pkg)
