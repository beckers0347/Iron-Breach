"""PS1 PAINT STABILITY: pad-ring captures and diagnostics on a garrison candidate (FF1 before, PS1 after).
Changes nothing on disk and never saves. Derived from Scripts/ib_garrison_forecourt_check.py (left unchanged).

    UnrealEditor.exe <project> -ExecutePythonScript="<Root>/Scripts/ib_garrison_ring_check.py"

Environment: IB_PS_TARGET (a candidate under /Game/_GarrisonPreview_Disposable/), IB_PS_OUT (output folder),
IB_GARRISON_PLAN (the PF1 layout plan: the overhead cameras FF1 used), IB_PS_FRAMES (frames in the moving sequence,
default 72), IB_PS_DIAG=1 (the in-memory cause A/B and the in-memory decal preview; FF1 only), IB_PS_WALK=0 (skip the
representative walk), IB_PS_ONLY=preview (with IB_PS_DIAG=1: skip the near view, the plain sequence and the cause A/B
already captured, and run only the transient decal preview: the filtered decal and, as its own A/B, the same decal with
a hard unfiltered edge), IB_PS_EXTRA=background,control (candidate runs: after the candidate's own frames, the SAME
settled / near / moving captures with the ring's decal hidden in the PIE world (background: no ring at all, the
reference the ring's own signal is measured against), and with the decal hidden and the 96 geometry segments shown
again in the PIE world (control: FF1's representation inside the same session); both restored before the walk).

Evidence kinds, kept apart in ring_checks.json:
  editor_shots   level-viewport high-resolution stills in game view (the FF1 overhead cameras); no actor spawned
  pie_settings   the ACTUAL play-in-editor settings: viewport size, the player camera's FOV and height above the deck,
                 anti-aliasing / screen-percentage / TSR / motion-blur / scalability console variables
  sequences      ACTUAL PIE frames: the game viewport's own back buffer ('Shot' console command), one per rendered frame,
                 while the player pawn is moved a fixed 10 cm per frame along a fixed path with a fixed control
                 rotation (the pawn's own first-person camera at its normal eye height). The camera pose of every
                 frame is recorded. This is a dense ordered frame sequence, not a video recording and not a person
                 playing.
  near_view      one ACTUAL PIE frame near the ring, after the view has settled
  diag           (IB_PS_DIAG=1) in-memory variants inside the PIE world only, each at the same settled camera:
                 settled back buffer; TSR convergence after re-arrival; high-resolution stills at 1920x1080 and
                 3840x2160 (the still path FF1's frames used, and a supersampled reference); the ring segments
                 widened x3; the pad deck hidden; which segments the renderer drew; and a transient decal preview of
                 the proposed marking (never saved) with its own moving sequence
  walk           one scripted PIE walk of the real pawn across the ring (movement input); reached / stalled / fell
"""
import unreal, json, os, time, math, traceback, datetime, shutil, struct, sys
from pathlib import Path

PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
TARGET = (os.environ.get("IB_PS_TARGET") or "").strip().rstrip("/")
OUT = Path(os.environ.get("IB_PS_OUT") or str(Path(unreal.Paths.project_saved_dir()) / "ps1check"))
PLAN = os.environ.get("IB_GARRISON_PLAN")
N_FRAMES = int(os.environ.get("IB_PS_FRAMES") or "72")
DIAG = os.environ.get("IB_PS_DIAG") == "1"
WALK = os.environ.get("IB_PS_WALK", "1") != "0"
ONLY = (os.environ.get("IB_PS_ONLY") or "").strip().lower()      # "preview": only the transient decal preview (DIAG)
EXTRA = set(x.strip() for x in (os.environ.get("IB_PS_EXTRA") or "").lower().split(",") if x.strip())
DECAL_LABEL = "IBGC_PS1_PadRingDecal"
FIXED = {"command_line_has_UseFixedTimeStep": "usefixedtimestep" in (unreal.SystemLibrary.get_command_line() if hasattr(unreal.SystemLibrary, "get_command_line") else "").lower(),
         "command_line": (unreal.SystemLibrary.get_command_line() if hasattr(unreal.SystemLibrary, "get_command_line") else None)}
RES_X, RES_Y = 1920, 1080
C = (17232.0, 4525.0)
Z = 385.0
RING_R = 1890.0
RING_PREFIXES = ("IBGC_Pad_Ring_", "IBGC_FF_Pad_Ring96_")
DECK_LABELS = ("IBGC_Pad_Deck_00", "IBGC_Pad_Deck_01", "IBGC_Pad_Deck_02", "IBGC_Pad_Chamfer_00", "IBGC_Pad_Chamfer_01",
               "IBGC_Pad_Chamfer_02", "IBGC_Pad_Chamfer_03")
STEP = 10.0                                                     # cm per rendered frame along +X
S1_START = (C[0] + 600.0, C[1] + 2350.0)                        # 5.2 m outside the ring's +Y side, on the pad deck
S1_YAW = math.degrees(math.atan2(C[1] - S1_START[1], C[0] - S1_START[0]))   # toward the pad centre
S1_PITCH = -4.0
NEAR_POS = (C[0], C[1] + 2150.0)                                # 2.4 m outside the ring
NEAR_LOOK = (C[0] - 700.0, C[1] + 1756.0)                       # a point on the ring's centre line, 8 m away
WALK_PTS = [[C[0], C[1] + 1500.0], [C[0], C[1] + 2300.0]]       # inside the ring -> across it -> outside

sys.path.insert(0, str(Path(__file__).resolve().parent))
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
OUT.mkdir(parents=True, exist_ok=True)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
R = {"tool": "ib_garrison_ring_check", "target": TARGET, "diag": DIAG, "only": ONLY or None, "extra": sorted(EXTRA),
     "frames_requested": N_FRAMES,
     "started_utc": datetime.datetime.utcnow().isoformat() + "Z", "editor_shots": [], "sequences": {}, "diag": {},
     "errors": [], "path": {"start": S1_START, "step_cm_per_frame": [STEP, 0.0], "yaw": round(S1_YAW, 3), "pitch": S1_PITCH},
     "evidence_kinds": __doc__.split("Evidence kinds, kept apart in ring_checks.json:")[1].strip()}


def log(m):
    unreal.log("GARRISON PS1 CHECK: " + str(m))


def save():
    R["updated_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    (OUT / "ring_checks.json").write_bytes(json.dumps(R, indent=1, default=str).encode("utf-8"))


def note_error(what):
    R["errors"].append({"what": what, "detail": traceback.format_exc()[-900:]})
    unreal.log_warning("GARRISON PS1 CHECK: " + what + "\n" + traceback.format_exc()[-900:])


def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


if not TARGET.startswith(PREVIEW_ROOT):
    R["errors"].append({"what": "refused", "detail": "target must be under " + PREVIEW_ROOT})
    save()
    raise RuntimeError("GARRISON PS1 CHECK REFUSED: target must be under " + PREVIEW_ROOT)
plan = json.loads(Path(PLAN).read_text(encoding="utf-8"))
unreal.EditorLoadingAndSavingUtils.load_map(TARGET)
R["loaded"] = UES.get_editor_world().get_path_name().split(".")[0]


def label(a):
    return safe(lambda: a.get_actor_label(), "") or ""


def ring_readout(actor_list, where):
    segs = [a for a in actor_list if label(a).startswith(RING_PREFIXES)]
    comps = [c for a in segs for c in (a.get_components_by_class(unreal.StaticMeshComponent) or [])]
    decals = []
    for a in actor_list:
        if isinstance(a, unreal.DecalActor):
            dc = safe(lambda a=a: a.get_editor_property("decal"))
            m = safe(lambda: dc.get_decal_material()) if dc else None
            s = safe(lambda: dc.get_editor_property("decal_size")) if dc else None
            l, r = a.get_actor_location(), a.get_actor_rotation()
            decals.append({"label": label(a), "material": m.get_path_name() if m else None,
                           "decal_size": [round(s.x, 2), round(s.y, 2), round(s.z, 2)] if s else None,
                           "fade_screen_size": safe(lambda: dc.get_editor_property("fade_screen_size")) if dc else None,
                           "loc": [round(l.x, 2), round(l.y, 2), round(l.z, 2)],
                           "rot": [round(r.roll, 3), round(r.pitch, 3), round(r.yaw, 3)],
                           "hidden_in_game": safe(lambda a=a: bool(a.get_editor_property("hidden")))})
    return {"where": where, "ring_segment_actors": len(segs), "ring_components": len(comps),
            "ring_components_visible": sum(1 for c in comps if safe(lambda c=c: bool(c.is_visible()), False)),
            "ring_actors_hidden_in_game": sum(1 for a in segs if safe(lambda a=a: bool(a.get_editor_property("hidden")), False)),
            "ring_materials": sorted(set(str(safe(lambda c=c: c.get_material(0).get_path_name())) for c in comps)),
            "decal_actors": decals}


try:
    R["editor_readout"] = ring_readout(EAS.get_all_level_actors(), "editor world (loaded map)")
except Exception:
    note_error("editor readout")
save()

# the overhead cameras FF1 used (Scripts/ib_garrison_forecourt_check.py), from the same PF1 plan values
fr, d = plan["frame"], plan["design"]
D = float(fr["depth"])
axis = float(d["spine"]["axis_y"])
SHOTS = [("overhead-reference", (fr["front"][0] + 0.42 * D, axis, Z + 0.95 * D), (fr["centre"][0] + 0.08 * D, axis, Z), None),
         ("pad-ring", (C[0] + 4000.0, C[1] - 1200.0, Z + 1300.0), (C[0], C[1], Z), None)]


def look(eye, target):
    return unreal.MathLibrary.find_look_at_rotation(V(*eye), V(*target))


def viewport_key():
    return safe(lambda: LES.get_active_viewport_config_key())


def set_camera(loc, rot):
    try:
        return LES.set_level_viewport_camera_info(loc, rot, viewport_key())
    except Exception:
        return UES.set_level_viewport_camera_info(loc, rot)


# ------------------------------------------------------------------------------------------------ collision helpers

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
    act = f[9] if len(f) > 9 else None
    return {"initial_overlap": bool(f[1]), "impact": [round(f[5].x, 1), round(f[5].y, 1), round(f[5].z, 1)],
            "actor": act.get_actor_label() if act and hasattr(act, "get_actor_label") else None}


def trace(world, a, b, radius, hh, ignore=()):
    return decode(unreal.SystemLibrary.capsule_trace_single_by_profile(
        world, V(*a), V(*b), radius, hh, "Pawn", False, list(ignore), unreal.DrawDebugTrace.NONE, True))


def floor_z(world, x, y):
    """The walkable floor under (x, y), ignoring the player pawn (a probe that hits the pawn's own capsule would
    stack the pawn on itself)."""
    ign = [PIE["pawn"]] if PIE.get("pawn") else []
    h = trace(world, (x, y, Z + 300.0), (x, y, Z - 1200.0), 17.0, 17.0, ign)
    return h["impact"][2] if h and not h["initial_overlap"] else None


# ------------------------------------------------------------------------------------------------ screenshots

def shot_dir():
    return Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.screen_shot_dir()))


def shots_now():
    d_ = shot_dir()
    return set(p.name for p in d_.glob("*.png")) if d_.is_dir() else set()


def png_size(p):
    with open(str(p), "rb") as f:
        head = f.read(24)
    return list(struct.unpack(">II", head[16:24])) if head[:8] == b"\x89PNG\r\n\x1a\n" else None


def collect(before, want, folder, names):
    """Generator: waits for `want` new 'Shot' files, then moves them IN NUMERIC ORDER to folder/names[i]."""
    t0 = time.monotonic()
    while True:
        new = sorted(shots_now() - before)
        if len(new) >= want or time.monotonic() - t0 > 90.0:
            break
        yield 0.5
    yield 1.5
    new = sorted(shots_now() - before)
    folder.mkdir(parents=True, exist_ok=True)
    out = []
    for i, n in enumerate(new[:want]):
        dst = folder / names[i]
        shutil.move(str(shot_dir() / n), str(dst))
        out.append({"file": str(dst), "source_name": n, "size": png_size(dst)})
    R.setdefault("shot_collection", []).append({"folder": str(folder), "wanted": want, "got": len(new),
                                               "moved": len(out), "extra_ignored": max(0, len(new) - want)})
    return out


# ------------------------------------------------------------------------------------------------ PIE helpers

PIE = {}


def cvars():
    names = ["r.AntiAliasingMethod", "r.TemporalAA.Upsampling", "r.ScreenPercentage", "r.ScreenPercentage.Mode",
             "r.SecondaryScreenPercentage.GameViewport", "r.TSR.History.ScreenPercentage", "r.TSR.History.SampleCount",
             "r.TSR.ShadingRejection.Flickering", "r.TSR.ThinGeometryDetection", "r.MotionBlurQuality", "r.DefaultFeature.MotionBlur",
             "r.MotionBlur.Amount", "r.Tonemapper.Sharpen", "r.DBuffer", "r.Substrate", "r.PostProcessAAQuality",
             "sg.ResolutionQuality", "sg.AntiAliasingQuality", "sg.PostProcessQuality", "sg.ShadowQuality", "sg.TextureQuality",
             "sg.EffectsQuality", "sg.ViewDistanceQuality", "sg.GlobalIlluminationQuality", "sg.ReflectionQuality",
             "r.EyeAdaptationQuality", "r.DefaultFeature.AutoExposure", "t.MaxFPS", "r.VSync"]
    gw = PIE.get("gw")
    out = {}
    for n in names:
        out[n] = {"int": safe(lambda n=n: unreal.SystemLibrary.get_console_variable_int_value(n)),
                  "float": safe(lambda n=n: round(unreal.SystemLibrary.get_console_variable_float_value(n), 4))}
    return out


def cam_pose():
    pcm = PIE["pcm"]
    l, r = pcm.get_camera_location(), pcm.get_camera_rotation()
    return {"loc": [round(l.x, 2), round(l.y, 2), round(l.z, 2)], "rot": [round(r.roll, 4), round(r.pitch, 4), round(r.yaw, 4)],
            "fov": round(float(pcm.get_fov_angle()), 4),
            "dt": round(float(safe(lambda: unreal.GameplayStatics.get_world_delta_seconds(PIE["gw"]), 0.0)), 5)}


def place(x, y, yaw, pitch):
    fz = floor_z(PIE["gw"], x, y)
    fz = fz if fz is not None else Z
    PIE["pawn"].set_actor_location(V(x, y, fz + PIE["hh"] + 2.15), False, True)
    PIE["pc"].set_control_rotation(unreal.Rotator(roll=0.0, pitch=pitch, yaw=yaw))


def frames(n):
    for _ in range(n):
        yield 0.0


MODE = {"shot": "Shot"}          # "Shot" (the game viewport's back buffer) unless the first test finds no file


def request_shot(path=None):
    if MODE["shot"] == "Shot":
        unreal.SystemLibrary.execute_console_command(PIE["gw"], "Shot")
    else:
        vs = R.get("pie_settings", {}).get("viewport_size") or [RES_X, RES_Y]
        unreal.AutomationLibrary.take_high_res_screenshot(int(vs[0]), int(vs[1]), str(path))


def collect_any(before, folder, names):
    """Generator: 'Shot' mode -> the new files in numeric order; fallback mode -> the named files themselves."""
    if MODE["shot"] == "Shot":
        return (yield from collect(before, len(names), folder, names))
    t0 = time.monotonic()
    while time.monotonic() - t0 < 60.0 and not all((folder / n).is_file() for n in names):
        yield 0.5
    yield 1.0
    return [{"file": str(folder / n), "source_name": None, "size": png_size(folder / n)} for n in names if (folder / n).is_file()]


def settled_shot(name, x, y, yaw, pitch, settle=90):
    place(x, y, yaw, pitch)
    t0 = time.monotonic()
    yield from frames(settle)
    while time.monotonic() - t0 < 3.0:          # at least 3 s for auto exposure as well
        place(x, y, yaw, pitch)
        yield 0.0
    before = shots_now()
    place(x, y, yaw, pitch)
    (OUT / "pie").mkdir(parents=True, exist_ok=True)
    request_shot(OUT / "pie" / (name + ".png"))
    yield 0.0
    pose = cam_pose()
    got = yield from collect_any(before, OUT / "pie", [name + ".png"])
    rec = {"name": name, "pose": pose, "file": got[0]["file"] if got else None, "size": got[0]["size"] if got else None,
           "kind": "ACTUAL PIE frame (game viewport back buffer), settled"}
    save()
    return rec


def sequence(name):
    """One Shot per rendered frame while the pawn moves STEP cm per frame along +X from S1_START."""
    place(S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
    t0 = time.monotonic()
    yield from frames(90)
    while time.monotonic() - t0 < 3.0:
        place(S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
        yield 0.0
    before = shots_now()
    poses, wanted = [], []
    (OUT / name).mkdir(parents=True, exist_ok=True)
    for k in range(N_FRAMES):
        x = S1_START[0] + STEP * k
        place(x, S1_START[1], S1_YAW, S1_PITCH)
        request_shot(OUT / name / ("frame_%03d.png" % k))
        yield 0.0
        p = cam_pose()
        p.update({"k": k, "pawn_xy": [round(x, 2), S1_START[1]]})
        poses.append(p)
        wanted.append("frame_%03d.png" % k)
    got = yield from collect_any(before, OUT / name, wanted)
    rec = {"name": name, "frames": len(got), "files_dir": str(OUT / name), "poses": poses,
           "sizes": sorted(set(str(g["size"]) for g in got)),
           "method": ("Shot console command (game viewport back buffer), one per rendered frame" if MODE["shot"] == "Shot"
                      else "FALLBACK: high-resolution still per frame at the viewport size ('Shot' produced no file)"),
           "kind": "ACTUAL PIE dense ordered frame sequence (not a video recording)"}
    R["sequences"][name] = rec
    save()
    return rec


def pie_actors(prefixes=None, labels=None):
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(PIE["gw"], unreal.Actor):
        lab = label(a)
        if (prefixes and lab.startswith(prefixes)) or (labels and lab in labels):
            out.append(a)
    return out


# ------------------------------------------------------------------------------------------------ decal preview (DIAG)

PREVIEW = {}
if DIAG:
    try:
        import ib_garrison_ring_decal as ringdecal
        PREVIEW["module"] = ringdecal
        for key, name, hard in (("material", "M_PS1_PreviewRingDecal", False), ("material_hard", "M_PS1_PreviewRingDecalHardEdge", True)):
            m = unreal.new_object(unreal.Material, name=name)          # TRANSIENT: never saved, never in a package
            conn = ringdecal.build(m, hard=hard)
            unreal.MaterialEditingLibrary.recompile_material(m)
            f = ringdecal.facts(m)
            f["connections"] = conn
            R["diag"]["preview_" + key] = {"variant": "hard edge, unfiltered (diagnostic)" if hard else "box-filtered (the proposal)",
                                           "facts": f, "issues": ringdecal.issues(f)}
            PREVIEW[key] = m
    except Exception:
        note_error("preview material")
    save()


def spawn_preview_decal(m):
    """A transient DecalComponent in the PIE world (GameplayStatics.SpawnDecalAtLocation: owned by the world settings,
    never saved), at the pad centre, projecting straight down, the same size the candidate's decal will have."""
    rot = unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0)
    hs = PREVIEW["module"].HALF_SIZE
    dc = unreal.GameplayStatics.spawn_decal_at_location(PIE["gw"], m, V(10.0, hs, hs), V(C[0], C[1], Z), rot, 0.0)
    if dc is None:
        raise RuntimeError("spawn_decal_at_location returned nothing")
    fade = safe(lambda: dc.set_editor_property("fade_screen_size", 0.0), "unset")
    fwd, l, r = dc.get_forward_vector(), dc.get_world_location(), dc.get_world_rotation()
    sz = dc.get_editor_property("decal_size")
    info = {"kind": "transient DecalComponent (GameplayStatics.spawn_decal_at_location), PIE world only",
            "loc": [round(l.x, 2), round(l.y, 2), round(l.z, 2)], "rot": [round(r.roll, 3), round(r.pitch, 3), round(r.yaw, 3)],
            "projection_direction": [round(fwd.x, 4), round(fwd.y, 4), round(fwd.z, 4)],
            "decal_size": [round(sz.x, 2), round(sz.y, 2), round(sz.z, 2)],
            "fade_screen_size": safe(lambda: round(float(dc.get_editor_property("fade_screen_size")), 4)),
            "fade_set": fade is None, "material": safe(lambda: dc.get_decal_material().get_name()),
            "projects_straight_down": abs(fwd.z + 1.0) < 1e-3}
    return dc, info


def remove_preview_decal(dc):
    safe(lambda: dc.set_visibility(False, False))
    return safe(lambda: dc.destroy_component(dc), "failed")


# ------------------------------------------------------------------------------------------------ flow

def flow():
    yield 45.0 if DIAG else 30.0                      # map streaming and shader compilation
    safe(lambda: LES.editor_set_game_view(True))
    yield 2.0
    for name, eye, target, rot in (SHOTS if ONLY != "preview" else []):
        try:
            set_camera(V(*eye), rot or look(eye, target))
        except Exception:
            note_error("camera " + name)
            continue
        yield 12.0
        try:
            f = OUT / "editor" / (name + ".png")
            f.parent.mkdir(parents=True, exist_ok=True)
            ok = unreal.AutomationLibrary.take_high_res_screenshot(RES_X, RES_Y, str(f))
            R["editor_shots"].append({"name": name, "file": str(f), "eye": [round(v, 1) for v in eye],
                                      "target": [round(v, 1) for v in target], "requested": bool(ok),
                                      "kind": "EDITOR high-resolution still (level viewport, game view)"})
        except Exception:
            note_error("screenshot " + name)
        save()
        yield 6.0
    try:
        LES.editor_request_begin_play()
    except Exception:
        note_error("begin play")
        return
    t0 = time.monotonic()
    while time.monotonic() - t0 < 45.0:
        yield 1.0
        gw = safe(lambda: UES.get_game_world())
        pawn = unreal.GameplayStatics.get_player_pawn(gw, 0) if gw else None
        if pawn:
            PIE.update({"gw": gw, "pawn": pawn, "pc": unreal.GameplayStatics.get_player_controller(gw, 0)})
            break
    if "pawn" not in PIE:
        R["pie_error"] = "no player pawn in PIE within 45 s"
        save()
        return
    PIE["pcm"] = PIE["pc"].player_camera_manager
    cap = PIE["pawn"].get_component_by_class(unreal.CapsuleComponent)
    PIE["hh"] = cap.get_scaled_capsule_half_height() if cap else 88.0
    PIE["rad"] = cap.get_scaled_capsule_radius() if cap else 34.0
    yield 3.0
    try:
        vs = PIE["pc"].get_viewport_size()
        place(S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
        yield from frames(5)
        pose = cam_pose()
        fz = floor_z(PIE["gw"], S1_START[0], S1_START[1])
        R["pie_settings"] = {"viewport_size": [int(vs[0]), int(vs[1])], "camera_fov_deg": pose["fov"],
                             "camera_height_above_floor_cm": round(pose["loc"][2] - (fz if fz is not None else Z), 2),
                             "pawn_class": PIE["pawn"].get_class().get_name(), "capsule_half_height": PIE["hh"],
                             "capsule_radius": PIE["rad"], "cvars": cvars(), "screen_shot_dir": str(shot_dir()),
                             "path": R["path"], "frames": N_FRAMES,
                             "fixed_time_step": FIXED,
                             "note": "PIE plays in the level editor's active viewport; no project, scalability or "
                                     "console setting is changed by this script. The editor process runs with a fixed "
                                     "engine time step (command line) so that every captured frame advances the same "
                                     "game time in both runs (motion blur, auto exposure, walk speed)."}
        R["pie_readout"] = ring_readout(list(unreal.GameplayStatics.get_all_actors_of_class(PIE["gw"], unreal.Actor)),
                                        "PIE world (play session)")
        (OUT / "pie_settings.json").write_text(json.dumps(R["pie_settings"], indent=1), encoding="utf-8")
    except Exception:
        note_error("pie settings")
    save()
    try:                                          # does 'Shot' write a file from this PIE session?
        before = shots_now()
        request_shot()
        t1 = time.monotonic()
        while time.monotonic() - t1 < 12.0 and not (shots_now() - before):
            yield 0.25
        new = sorted(shots_now() - before)
        R["shot_test"] = {"screen_shot_dir": str(shot_dir()), "new_files": new}
        if new:
            yield 1.0
            (OUT / "pie").mkdir(parents=True, exist_ok=True)
            dst = OUT / "pie" / "shot-test.png"
            shutil.move(str(shot_dir() / new[0]), str(dst))
            R["shot_test"]["size"] = png_size(dst)
        else:
            MODE["shot"] = "highres"
        R["shot_test"]["mode"] = MODE["shot"]
    except Exception:
        note_error("shot test")
        MODE["shot"] = "highres"
    save()
    # 1. near-ring gameplay view
    if ONLY != "preview":
        try:
            yaw = math.degrees(math.atan2(NEAR_LOOK[1] - NEAR_POS[1], NEAR_LOOK[0] - NEAR_POS[0]))
            dist = math.hypot(NEAR_LOOK[0] - NEAR_POS[0], NEAR_LOOK[1] - NEAR_POS[1])
            pitch = -math.degrees(math.atan2(R.get("pie_settings", {}).get("camera_height_above_floor_cm", 154.0), dist))
            R["near_view"] = yield from settled_shot("pie-near-ring", NEAR_POS[0], NEAR_POS[1], yaw, pitch)
        except Exception:
            note_error("near view")
        save()
    # 2. the moving sequence (the matched temporal evidence)
    if ONLY != "preview":
        try:
            yield from sequence("s1")
        except Exception:
            note_error("sequence s1")
        save()
    # 3. diagnostics (FF1 only)
    if DIAG and ONLY != "preview":
        dg = R["diag"]
        try:
            dg["a_settled"] = yield from settled_shot("diag-a-settled", S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
            segs = pie_actors(prefixes=RING_PREFIXES)
            cl = PIE["pcm"].get_camera_location()
            rr = []
            for a in segs:
                l = a.get_actor_location()
                rr.append({"label": label(a), "distance_m": round(math.dist((l.x, l.y, l.z), (cl.x, cl.y, cl.z)) / 100.0, 2),
                           "recently_rendered": bool(safe(lambda a=a: a.was_recently_rendered(0.25), False))})
            dg["g_rendered_segments"] = {"segments": len(rr), "rendered": sum(1 for x in rr if x["recently_rendered"]),
                                         "not_rendered": [x for x in rr if not x["recently_rendered"]][:40],
                                         "farthest_rendered_m": max([x["distance_m"] for x in rr if x["recently_rendered"]] or [None])}
        except Exception:
            note_error("diag a/g")
        save()
        try:                                      # b. TSR convergence after re-arrival (history rejected by the jump)
            place(S1_START[0], S1_START[1] - 400.0, S1_YAW, S1_PITCH)
            yield from frames(30)
            idx = [0, 1, 2, 3, 5, 8, 13, 21, 34, 55]
            before = shots_now()
            names = []
            for k in range(max(idx) + 1):
                place(S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
                if k in idx:
                    names.append("diag-b-arrival-frame%02d.png" % k)
                    request_shot(OUT / "pie" / names[-1])
                yield 0.0
            got = yield from collect_any(before, OUT / "pie", names)
            dg["b_convergence"] = {"frames_after_arrival": idx, "files": [g["file"] for g in got]}
        except Exception:
            note_error("diag b")
        save()
        for tag, w, h in (("c-highres-1920x1080", 1920, 1080), ("d-highres-3840x2160", 3840, 2160)):
            try:                                  # c/d. the still path FF1's frames used, and a supersampled still
                place(S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
                yield from frames(30)
                f = OUT / "pie" / ("diag-%s.png" % tag)
                ok = unreal.AutomationLibrary.take_high_res_screenshot(w, h, str(f))
                t1 = time.monotonic()
                while time.monotonic() - t1 < 20.0 and not f.is_file():
                    place(S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
                    yield 0.1
                yield 2.0
                dg[tag] = {"file": str(f), "requested": bool(ok), "written": f.is_file(), "size": png_size(f) if f.is_file() else None,
                           "kind": "high-resolution still requested during PIE (player camera)"}
            except Exception:
                note_error("diag " + tag)
            save()
        try:                                      # e. ring segments widened x3 (sampling test), PIE world only
            segs = pie_actors(prefixes=RING_PREFIXES)
            orig = [(a, a.get_actor_scale3d()) for a in segs]
            for a, s in orig:
                a.set_actor_scale3d(V(s.x, s.y * 3.0, s.z))
            dg["e_wide3"] = yield from settled_shot("diag-e-ring-wide3", S1_START[0], S1_START[1], S1_YAW, S1_PITCH, settle=60)
            dg["e_wide3"]["segments_widened"] = len(orig)
            for a, s in orig:
                a.set_actor_scale3d(s)
        except Exception:
            note_error("diag e")
        save()
        try:                                      # f. pad deck hidden (depth-conflict test), PIE world only
            decks = pie_actors(labels=DECK_LABELS)
            for a in decks:
                a.set_actor_hidden_in_game(True)
            dg["f_deck_hidden"] = yield from settled_shot("diag-f-deck-hidden", S1_START[0], S1_START[1], S1_YAW, S1_PITCH, settle=60)
            dg["f_deck_hidden"]["deck_actors_hidden"] = [label(a) for a in decks]
            for a in decks:
                a.set_actor_hidden_in_game(False)
        except Exception:
            note_error("diag f")
        save()
    if DIAG and PREVIEW.get("material") is not None:
        dg = R["diag"]
        segs, dc = [], None
        try:                                      # h. transient decal preview: segments hidden, decal spawned, PIE only
            segs = pie_actors(prefixes=RING_PREFIXES)
            for a in segs:
                a.set_actor_hidden_in_game(True)
            for key in ("material", "material_hard"):
                if PREVIEW.get(key) is not None:
                    dg["preview_" + key]["stats"] = PREVIEW["module"].stats(PREVIEW[key])
            dc, info = spawn_preview_decal(PREVIEW["material"])
            dg["h_decal_actor"] = info
            dg["h_segments_hidden"] = len(segs)
            dg["h_pie_readout"] = ring_readout(list(unreal.GameplayStatics.get_all_actors_of_class(PIE["gw"], unreal.Actor)),
                                               "PIE world with the transient preview decal")
            save()
            near_yaw = math.degrees(math.atan2(NEAR_LOOK[1] - NEAR_POS[1], NEAR_LOOK[0] - NEAR_POS[0]))
            near_pitch = -math.degrees(math.atan2(R.get("pie_settings", {}).get("camera_height_above_floor_cm", 154.0),
                                                  math.hypot(NEAR_LOOK[0] - NEAR_POS[0], NEAR_LOOK[1] - NEAR_POS[1])))
            dg["h_decal_settled"] = yield from settled_shot("diag-h-decal-settled", S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
            dg["h_decal_near"] = yield from settled_shot("diag-h-decal-near-ring", NEAR_POS[0], NEAR_POS[1], near_yaw, near_pitch)
            yield from sequence("s1-decal-preview")
            if PREVIEW.get("material_hard") is not None:      # the same decal, hard unfiltered edge (A/B of the filtering)
                dc.set_decal_material(PREVIEW["material_hard"])
                dg["h_hard_settled"] = yield from settled_shot("diag-h-decal-hard-settled", S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
                yield from sequence("s1-decal-hard")
                dc.set_decal_material(PREVIEW["material"])
        except Exception:
            note_error("diag h")
        finally:
            if dc is not None:
                dg["h_decal_removed"] = remove_preview_decal(dc) is None
            for a in segs:
                safe(lambda a=a: a.set_actor_hidden_in_game(False))
        save()
    # 3b. candidate runs: settled frame, then background (no ring) and control (FF1's geometry) in the PIE world only
    if EXTRA:
        ex = R.setdefault("extra_captures", {})
        near_yaw = math.degrees(math.atan2(NEAR_LOOK[1] - NEAR_POS[1], NEAR_LOOK[0] - NEAR_POS[0]))
        near_pitch = -math.degrees(math.atan2(R.get("pie_settings", {}).get("camera_height_above_floor_cm", 154.0),
                                              math.hypot(NEAR_LOOK[0] - NEAR_POS[0], NEAR_LOOK[1] - NEAR_POS[1])))
        decal_comps, seg_comps = [], []
        try:
            ex["settled"] = yield from settled_shot("pie-settled", S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
            for a in pie_actors(labels=(DECAL_LABEL,)):
                decal_comps += list(a.get_components_by_class(unreal.DecalComponent) or [])
            for a in pie_actors(prefixes=RING_PREFIXES):
                seg_comps += list(a.get_components_by_class(unreal.StaticMeshComponent) or [])
            ex["decal_components_found"] = len(decal_comps)
            ex["segment_components_found"] = len(seg_comps)
            ex["segment_components_visible_at_start"] = sum(1 for c in seg_comps if safe(lambda c=c: bool(c.is_visible()), False))
        except Exception:
            note_error("extra: settled / find")
        save()
        if "background" in EXTRA:
            try:
                for c in decal_comps:
                    c.set_visibility(False, False)
                ex["background"] = {"what": "the ring's decal hidden in the PIE world (segments stay hidden): no ring at all",
                                    "decal_components_hidden": len(decal_comps)}
                ex["background"]["settled"] = yield from settled_shot("pie-noring-settled", S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
                ex["background"]["near"] = yield from settled_shot("pie-noring-near", NEAR_POS[0], NEAR_POS[1], near_yaw, near_pitch)
                yield from sequence("s1-noring")
            except Exception:
                note_error("extra: background")
            save()
        if "control" in EXTRA:
            try:
                for c in decal_comps:
                    c.set_visibility(False, False)
                for c in seg_comps:
                    c.set_visibility(True, False)
                ex["control"] = {"what": "the decal hidden and the 96 geometry segments shown in the PIE world: FF1's ring "
                                         "representation inside this session",
                                 "segment_components_shown": sum(1 for c in seg_comps if safe(lambda c=c: bool(c.is_visible()), False))}
                ex["control"]["settled"] = yield from settled_shot("pie-control-settled", S1_START[0], S1_START[1], S1_YAW, S1_PITCH)
                yield from sequence("s1-geometry-control")
            except Exception:
                note_error("extra: control")
            save()
        try:                                      # restore the candidate's own state for the walk
            for c in seg_comps:
                c.set_visibility(False, False)
            for c in decal_comps:
                c.set_visibility(True, False)
            ex["restored"] = {"decal_visible": sum(1 for c in decal_comps if safe(lambda c=c: bool(c.is_visible()), False)),
                              "segments_visible": sum(1 for c in seg_comps if safe(lambda c=c: bool(c.is_visible()), False))}
        except Exception:
            note_error("extra: restore")
        save()
    # 4. one representative walk across the ring (real movement input)
    if WALK:
        rec = {"name": "across the pad ring (inside -> outside)", "waypoints": WALK_PTS}
        try:
            pawn, rad, hh = PIE["pawn"], PIE["rad"], PIE["hh"]
            x0, y0 = WALK_PTS[0]
            sz = floor_z(PIE["gw"], x0, y0) or Z
            pawn.set_actor_location_and_rotation(V(x0, y0, sz + hh + 5.0), unreal.Rotator(0.0, 0.0, 90.0), False, True)
            yield 1.5
            L = math.hypot(WALK_PTS[1][0] - x0, WALK_PTS[1][1] - y0)
            t_start, traj, last_t, result, zmin, zmax = time.monotonic(), [], 0.0, None, 1e9, -1e9
            hist = []
            while True:
                l = pawn.get_actor_location()
                t = time.monotonic() - t_start
                zmin, zmax = min(zmin, l.z), max(zmax, l.z)
                if t - last_t >= 0.2:
                    traj.append([round(t, 2), round(l.x, 1), round(l.y, 1), round(l.z, 1)])
                    hist.append((t, l.x, l.y))
                    last_t = t
                gx, gy = WALK_PTS[1]
                if math.hypot(gx - l.x, gy - l.y) < 70.0:
                    result = "reached"
                    break
                if l.z < sz - 200.0:
                    result = "fell"
                    break
                old = [h for h in hist if t - h[0] >= 2.5]
                if old and t > 3.0 and math.hypot(l.x - old[-1][1], l.y - old[-1][2]) < 40.0:
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
                        "end": [round(l.x, 1), round(l.y, 1), round(l.z, 1)], "capsule_centre_z": [round(zmin, 1), round(zmax, 1)],
                        "crosses_ring_at_y": C[1] + RING_R, "trajectory": traj,
                        "kind": "scripted PIE walk: the real pawn driven by movement input; not a person playing"})
        except Exception:
            note_error("walk")
            rec["result"] = rec.get("result") or "error"
        R["walk"] = rec
        save()
    safe(lambda: LES.editor_request_end_play())
    yield 4.0


state = {"due": time.monotonic(), "busy": False, "handle": None, "gen": flow()}


def finish():
    safe(lambda: LES.editor_set_game_view(False))
    R["dirty_map_packages_at_exit"] = safe(lambda: [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()], "unreadable")
    R["dirty_content_packages_at_exit"] = safe(lambda: [p.get_name() for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()], "unreadable")
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
        safe(lambda: LES.editor_request_end_play())
        finish()
    finally:
        state["busy"] = False


state["handle"] = unreal.register_slate_post_tick_callback(tick)
log("started on " + R["loaded"])
