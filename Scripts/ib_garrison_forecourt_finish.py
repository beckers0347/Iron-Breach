"""FF1: FORECOURT FINISH on a NEW disposable candidate made from the accepted YM1 candidate.

Derived from Scripts/ib_garrison_paint_correction.py (YM1, SHA256 FCD658A2..., left unchanged): the same
base / copy / fingerprint / receipt / material machinery, extended to the three kinds of change a reviewed
FF1 plan (Scripts/ib_garrison_forecourt_plan.py -> ff1_plan.json) contains:

  pieces       NEW generated actors (forecourt quay coping and fascia, forecourt paint, the 64 new pad-ring
               segments), each a Cube StaticMeshActor tagged IB_GarrisonCB1 + IB_GarrisonForecourtFinish,
               verified for label, tags, folder, mesh, material, transform, visibility and collision
  ring edits   the 32 existing P3 pad-ring actors re-shaped IN PLACE into every third segment of a thin
               96-segment ring (same actor, same centre, same yaw; new length, height and z), with their
               exact prior transforms captured from the engine at apply time and restored by revert
  assignments  every generated marking of the base (the 91 on YM1's paint instance) -> the NEW
               candidate-owned paint instance, by actor / component / slot, originals recorded

The base candidate, its material instance and receipt, the live map and every earlier preview are never
written. Only the target map and the new material instance are ever saved.

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script="Scripts/ib_garrison_forecourt_finish.py"

Stages (IB_GARRISON_FF_STAGE), each in its own process:
  base-fingerprint  loads ONLY the base (first map in the process) and records its fingerprint
  copy              duplicate the verified base to the NEW target; saves only the target
  copy-verify       (new process) loads ONLY the target; compares it with the base fingerprint; receipt 'created'
  material          create the NEW paint instance (never overwrites a package; retints only its own)
  plan-check        read-only: the plan's preconditions against the loaded target (identities, current
                    transforms and materials, free labels, assets) -- exactly the apply preflight
  apply             preflight -> pieces -> ring edits -> assignments -> whole-state check -> save the target
                    -> receipt 'applied'. A repeat on the verified applied state changes and saves nothing.
  revert            the level must be exactly the applied state (else REFUSED, nothing changed) -> remove the
                    FF1 actors -> restore the ring transforms captured at apply -> restore the base paint ->
                    verify clean -> save -> receipt 'reverted'
  verify            (new process) receipt state == file bytes; the instance's effective parameters; and an
                    actor-for-actor, component-for-component comparison with the base fingerprint in which
                    ONLY the plan's pieces, ring edits and slot changes may differ (applied) or nothing may (clean)

Environment:
  IB_GARRISON_BASE, IB_GARRISON_BASE_SHA256     the accepted base (YM1) and its map SHA256
  IB_GARRISON_TARGET_LEVEL                      the NEW candidate under /Game/_GarrisonPreview_Disposable/
  IB_GARRISON_FF_PLAN                           ff1_plan.json (plan-check / apply / revert / verify)
  IB_GARRISON_PAINT_MI, IB_GARRISON_PAINT_RGB   the NEW paint instance (in a subfolder) and its linear Base Color
  IB_GARRISON_BASE_MI                           the base's paint instance (YM1), never written
  IB_GARRISON_BASE_FINGERPRINT                  base_fingerprint.json from the base-fingerprint stage
  IB_GARRISON_OUT                               output folder for the stage report (ff_<stage>.json)
"""
import unreal, json, os, hashlib, datetime, traceback, re, math
from pathlib import Path

PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
LIVE = "/Game/LevelPrototyping/CarrowGateGarrison"
PARENT = "/Game/LevelPrototyping/Materials/M_FlatCol.M_FlatCol"
PARAM = "Base Color"
TOL = 1e-4
RUN_TAG = "IB_GarrisonCB1"
FF_TAG = "IB_GarrisonForecourtFinish"
KIND = "FF1 forecourt finish candidate"
LOC_TOL, ROT_TOL, SCALE_TOL = 0.5, 0.05, 1e-4
STAGE = (os.environ.get("IB_GARRISON_FF_STAGE") or "").strip().lower()
BASE = (os.environ.get("IB_GARRISON_BASE") or "").strip().rstrip("/")
BASE_SHA = (os.environ.get("IB_GARRISON_BASE_SHA256") or "").strip().upper()
TARGET = (os.environ.get("IB_GARRISON_TARGET_LEVEL") or "").strip().rstrip("/")
PLAN = os.environ.get("IB_GARRISON_FF_PLAN")
MI_PKG = (os.environ.get("IB_GARRISON_PAINT_MI") or "").strip().rstrip("/").split(".")[0]
BASE_MI_PKG = (os.environ.get("IB_GARRISON_BASE_MI") or "").strip().rstrip("/").split(".")[0]
RGB = [float(v) for v in (os.environ.get("IB_GARRISON_PAINT_RGB") or "0.85,0.60,0.22").split(",")]
BASE_FP = os.environ.get("IB_GARRISON_BASE_FINGERPRINT")
PROJECT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = Path(os.environ.get("IB_GARRISON_OUT") or str(PROJECT / "Saved/GarrisonRestructure/ff1"))
RECEIPTS = PROJECT / "Saved/GarrisonRestructure/receipts"
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary
REPORT = {"tool": "ib_garrison_forecourt_finish", "stage": STAGE, "base": BASE, "target": TARGET,
          "material_instance": MI_PKG, "rgb": RGB, "started_utc": datetime.datetime.utcnow().isoformat() + "Z"}


def log(m):
    unreal.log("GARRISON FF1: " + str(m))


def fail(m):
    raise RuntimeError("GARRISON FF1 REFUSED: " + str(m))


def now():
    return datetime.datetime.utcnow().isoformat() + "Z"


def sha(path):
    path = Path(path)
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def umap(pkg):
    return PROJECT / "Content" / (pkg[len("/Game/"):] + ".umap")


def uasset(pkg):
    return PROJECT / "Content" / (pkg[len("/Game/"):] + ".uasset")


def obj(pkg):
    return "%s.%s" % (pkg, pkg.split("/")[-1])


def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def enum_name(v):
    s = str(v).strip()
    if s.startswith("<") and ":" in s:
        s = s[1:].split(":")[0]
    return s.split(".")[-1].strip("<> ")


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(json.dumps(data, indent=1).encode("utf-8"))
    os.replace(str(tmp), str(path))


def receipt_file(pkg):
    return RECEIPTS / (pkg.strip("/").replace("/", "__") + ".json")


def read_receipt(pkg):
    f = receipt_file(pkg)
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None


def world_package():
    w = safe(lambda: unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world())
    return w.get_path_name().split(".")[0] if w else None


def load(pkg):
    unreal.EditorLoadingAndSavingUtils.load_map(pkg)
    if world_package() != pkg:
        fail("loading %s left %s loaded" % (pkg, world_package()))


def level_prefix(pkg):
    return "%s.%s:PersistentLevel." % (pkg, pkg.split("/")[-1])


def live_actors(pkg):
    pre = level_prefix(pkg)
    out = {}
    for a in EAS.get_all_level_actors():
        p = safe(lambda: a.get_path_name())
        if p and p.startswith(pre):
            out[p[len(pre):]] = a
    return out


def tags_of(a):
    return sorted(str(t) for t in (safe(lambda: a.get_editor_property("tags")) or []))


def norm_path(p, pkg):
    if not p:
        return p
    if p.startswith(pkg + "."):
        p = "<level>" + p[len(pkg):]
    return re.sub(r"MaterialInstanceDynamic_\d+", "MaterialInstanceDynamic_#", p)


def mat_list(c, pkg):
    n = safe(lambda: c.get_num_materials(), 0) or 0
    return [norm_path(safe(lambda i=i: c.get_material(i).get_path_name()), pkg) for i in range(n)]


def override_list(c, pkg):
    return [norm_path(m.get_path_name(), pkg) if m else None
            for m in (safe(lambda: c.get_editor_property("override_materials")) or [])]


def component_record(c, pkg):
    rec = {"class": c.get_class().get_name()}
    if isinstance(c, unreal.PrimitiveComponent):
        rec["visible"] = safe(lambda: bool(c.is_visible()))
        rec["profile"] = safe(lambda: str(c.get_collision_profile_name()))
        rec["collision"] = safe(lambda: enum_name(c.get_collision_enabled()))
    if isinstance(c, unreal.StaticMeshComponent):
        m = safe(lambda: c.get_editor_property("static_mesh"))
        rec["mesh"] = m.get_path_name() if m else None
        rec["materials"] = mat_list(c, pkg)
        rec["overrides"] = override_list(c, pkg)
    elif isinstance(c, unreal.MeshComponent):
        rec["materials"] = mat_list(c, pkg)
    return rec


EDITOR_ONLY = {"count": 0}


def fingerprint(pkg):
    """Identical to the YM1 tool's fingerprint: every actor's transform, flags, tags, folder and every
    in-game primitive component (editor-only components are counted, not compared)."""
    out = {}
    EDITOR_ONLY["count"] = 0
    for key, a in live_actors(pkg).items():
        l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
        comps = {}
        for c in (safe(lambda: a.get_components_by_class(unreal.PrimitiveComponent)) or []):
            if safe(lambda: bool(c.get_editor_property("is_editor_only")), False) is True:
                EDITOR_ONLY["count"] += 1
                continue
            comps[c.get_name()] = component_record(c, pkg)
        out[key] = {"label": safe(lambda: a.get_actor_label()), "class": a.get_class().get_name(),
                    "loc": [round(l.x, 2), round(l.y, 2), round(l.z, 2)],
                    "rot": [round(r.roll, 3), round(r.pitch, 3), round(r.yaw, 3)],
                    "scale": [round(s.x, 5), round(s.y, 5), round(s.z, 5)],
                    "hidden": safe(lambda: bool(a.get_editor_property("hidden"))),
                    "actor_collision": safe(lambda: bool(a.get_actor_enable_collision())),
                    "tags": tags_of(a), "folder": safe(lambda: str(a.get_folder_path()), ""),
                    "components": comps}
    return out


def snapshot(pkg):
    load(pkg)
    fp = fingerprint(pkg)
    unreal.SystemLibrary.collect_garbage()
    return fp


# ---------------------------------------------------------------------------------------- transforms

def rot_axes(r):
    p, y, ro = (math.radians(float(r.get("pitch", 0.0))), math.radians(float(r.get("yaw", 0.0))),
                math.radians(float(r.get("roll", 0.0))))
    sp, cp, sy, cy, sr, cr = math.sin(p), math.cos(p), math.sin(y), math.cos(y), math.sin(ro), math.cos(ro)
    return ((cp * cy, cp * sy, sp),
            (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp),
            (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp))


def rot_close(a, b, tol=ROT_TOL):
    A, B = rot_axes(a), rot_axes(b)
    c = math.cos(math.radians(tol))
    return all(sum(A[i][k] * B[i][k] for k in range(3)) >= c - 1e-12 for i in range(3))


def vec_close(a, b, tol):
    return a is not None and b is not None and all(abs(float(a[k]) - float(b[k])) <= tol for k in range(3))


def rotd(v):
    """[roll, pitch, yaw] (fingerprint) or a dict -> dict."""
    if isinstance(v, dict):
        return v
    return {"roll": v[0], "pitch": v[1], "yaw": v[2]}


def transform_ok(loc, rot, scale, want):
    out = []
    if not vec_close(loc, want["loc"], LOC_TOL):
        out.append("location %s, expected %s" % ([round(x, 2) for x in loc], want["loc"]))
    if not rot_close(rotd(rot), rotd(want["rot"])):
        out.append("rotation %s, expected %s" % (rot, want["rot"]))
    if not vec_close(scale, want["scale"], SCALE_TOL * max([1.0] + [abs(float(x)) for x in want["scale"]])):
        out.append("scale %s, expected %s" % (scale, want["scale"]))
    return out


def actor_transform(a):
    l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    return [l.x, l.y, l.z], {"roll": r.roll, "pitch": r.pitch, "yaw": r.yaw}, [s.x, s.y, s.z]


def set_transform(a, loc, rot, scale):
    a.set_actor_scale3d(unreal.Vector(*scale))
    a.set_actor_rotation(unreal.Rotator(roll=rot["roll"], pitch=rot["pitch"], yaw=rot["yaw"]), False)
    a.set_actor_location(unreal.Vector(*loc), False, False)


# ---------------------------------------------------------------------------------------- material

def mi_facts(mi):
    f = {"object": safe(lambda: mi.get_path_name()), "class": safe(lambda: mi.get_class().get_name())}
    p = safe(lambda: mi.get_editor_property("parent"))
    f["parent"] = p.get_path_name() if p else None
    f["vector_overrides"] = [{"name": str(v.get_editor_property("parameter_info").get_editor_property("name")),
                              "value": [round(float(x), 6) for x in (lambda c: (c.r, c.g, c.b, c.a))(
                                  v.get_editor_property("parameter_value"))]}
                             for v in (safe(lambda: mi.get_editor_property("vector_parameter_values")) or [])]
    f["scalar_overrides"] = [{"name": str(v.get_editor_property("parameter_info").get_editor_property("name")),
                              "value": float(v.get_editor_property("parameter_value"))}
                             for v in (safe(lambda: mi.get_editor_property("scalar_parameter_values")) or [])]
    f["texture_overrides"] = len(safe(lambda: mi.get_editor_property("texture_parameter_values")) or [])
    f["vector_parameter_names"] = sorted(str(n) for n in (safe(lambda: MEL.get_vector_parameter_names(mi)) or []))
    f["scalar_parameter_names"] = sorted(str(n) for n in (safe(lambda: MEL.get_scalar_parameter_names(mi)) or []))
    c = safe(lambda: MEL.get_material_instance_vector_parameter_value(mi, PARAM))
    f["effective_base_color"] = [round(float(c.r), 6), round(float(c.g), 6), round(float(c.b), 6), round(float(c.a), 6)] \
        if c is not None else None
    f["effective_scalars"] = {n: safe(lambda n=n: round(float(MEL.get_material_instance_scalar_parameter_value(mi, n)), 6))
                              for n in f["scalar_parameter_names"]}
    bp = safe(lambda: mi.get_editor_property("base_property_overrides"))
    f["base_property_overrides"] = {k: safe(lambda k=k: str(bp.get_editor_property(k)))
                                    for k in ("override_shading_model", "override_blend_mode", "override_two_sided")} \
        if bp is not None else None
    return f


def mi_issues(f):
    want = [round(v, 6) for v in RGB] + [1.0]
    out = []
    if f.get("parent") != PARENT:
        out.append("parent is %s, not %s" % (f.get("parent"), PARENT))
    if PARAM not in (f.get("vector_parameter_names") or []):
        out.append("the parent exposes no %r" % PARAM)
    if [o["name"] for o in f.get("vector_overrides") or []] != [PARAM]:
        out.append("vector overrides are %s, expected only %r" % ([o["name"] for o in f.get("vector_overrides") or []], PARAM))
    eff = f.get("effective_base_color")
    if not eff or any(abs(a - b) > TOL for a, b in zip(eff, want)):
        out.append("effective %r is %s, expected %s" % (PARAM, eff, want))
    if f.get("scalar_overrides"):
        out.append("unexpected scalar overrides %s" % f["scalar_overrides"])
    if f.get("texture_overrides"):
        out.append("unexpected texture overrides")
    return out


def create_material():
    folder, name = MI_PKG.rsplit("/", 1)
    parent = unreal.EditorAssetLibrary.load_asset(PARENT)
    if parent is None or not isinstance(parent, unreal.Material):
        fail("parent %s did not load as a Material" % PARENT)
    factory = unreal.MaterialInstanceConstantFactoryNew()
    safe(lambda: factory.set_editor_property("initial_parent", parent))
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.MaterialInstanceConstant, factory)
    if mi is None:
        fail("create_asset returned nothing for %s" % MI_PKG)
    MEL.set_material_instance_parent(mi, parent)
    ok = MEL.set_material_instance_vector_parameter_value(mi, PARAM, unreal.LinearColor(RGB[0], RGB[1], RGB[2], 1.0))
    MEL.update_material_instance(mi)
    facts = mi_facts(mi)
    facts["set_vector_returned"] = bool(ok)
    return mi, facts


# ---------------------------------------------------------------------------------------- guards

def guard_names(need_mi=False):
    if not TARGET.startswith(PREVIEW_ROOT) or TARGET in (LIVE, BASE):
        fail("the target must be a NEW package under %s (not the live map or the base)" % PREVIEW_ROOT)
    if not BASE.startswith(PREVIEW_ROOT) or BASE == TARGET:
        fail("the base must be a verified candidate under %s" % PREVIEW_ROOT)
    if need_mi:
        rest = MI_PKG[len(PREVIEW_ROOT):] if MI_PKG.startswith(PREVIEW_ROOT) else ""
        if "/" not in rest or not rest.split("/")[-1]:
            fail("the material instance must be in a SUBFOLDER of %s, got %r" % (PREVIEW_ROOT, MI_PKG))
        if MI_PKG == BASE_MI_PKG:
            fail("the new material instance must not be the base's")


def base_facts():
    cur = sha(umap(BASE))
    rec = read_receipt(BASE)
    if not BASE_SHA or cur != BASE_SHA:
        fail("the base %s is %s..., expected %s..." % (BASE, str(cur)[:12], BASE_SHA[:12]))
    if rec is None or not rec.get("history"):
        fail("the base has no receipt; only a verified candidate can be a base")
    last = rec["history"][-1]
    if last.get("state") != "applied" or last.get("sha256") != cur:
        fail("the base's receipt ends in %s %s..., not 'applied' at the current bytes"
             % (last.get("state"), str(last.get("sha256"))[:12]))
    bm = rec.get("material") or {}
    out = {"package": BASE, "file": str(umap(BASE)), "sha256": cur, "receipt": str(receipt_file(BASE)),
           "receipt_sha256": sha(receipt_file(BASE)), "receipt_last": last,
           "lineage": {"source_package": rec.get("source_package"), "source_sha256": rec.get("source_sha256")}}
    if BASE_MI_PKG:
        if bm.get("package") != BASE_MI_PKG or sha(uasset(BASE_MI_PKG)) != bm.get("sha256"):
            fail("the base's own material instance is not %s at its recorded bytes" % BASE_MI_PKG)
        out["base_material"] = {"package": BASE_MI_PKG, "sha256": bm.get("sha256")}
    return out


def read_base_fp():
    if not BASE_FP or not Path(BASE_FP).is_file():
        fail("IB_GARRISON_BASE_FINGERPRINT must name the base-fingerprint stage's base_fingerprint.json")
    d = json.loads(Path(BASE_FP).read_text(encoding="utf-8"))
    cur = sha(umap(BASE))
    if d.get("package") != BASE or d.get("sha256") != cur or cur != BASE_SHA:
        fail("the recorded base fingerprint is of %s at %s..., not of %s at its current %s..."
             % (d.get("package"), str(d.get("sha256"))[:12], BASE, str(cur)[:12]))
    return d["fingerprint"]


def target_state(rec):
    if rec is None:
        fail("no receipt for %s; create it with the copy stages first" % TARGET)
    if rec.get("kind") != KIND or rec.get("source_package") != BASE:
        fail("the receipt does not describe an FF1 candidate made from %s" % BASE)
    cur = sha(umap(TARGET))
    last = rec["history"][-1]
    if cur != last.get("sha256"):
        older = [h["state"] for h in rec["history"][:-1] if h.get("sha256") == cur]
        fail("STALE TARGET: its file (%s...) is not its last recorded state '%s' (%s...)%s"
             % (str(cur)[:12], last.get("state"), str(last.get("sha256"))[:12],
                (" (it equals an older recorded state '%s'; nothing is assumed)" % older[-1]) if older else ""))
    return last


def material_state(rec):
    m = rec.get("material")
    if not m:
        fail("no material instance recorded for %s; run the material stage" % TARGET)
    if m.get("package") != MI_PKG:
        fail("the receipt's material is %s, not %s" % (m.get("package"), MI_PKG))
    cur = sha(uasset(MI_PKG))
    if cur != m.get("sha256"):
        fail("the material instance file changed since it was recorded (%s... != %s...)"
             % (str(cur)[:12], str(m.get("sha256"))[:12]))
    return m


def load_mi(pkg=None):
    mi = unreal.EditorAssetLibrary.load_asset(obj(pkg or MI_PKG))
    if mi is None:
        fail("%s did not load" % (pkg or MI_PKG))
    return mi


def read_plan():
    if not PLAN or not Path(PLAN).is_file():
        fail("IB_GARRISON_FF_PLAN must name the reviewed ff1_plan.json")
    plan = json.loads(Path(PLAN).read_text(encoding="utf-8"))
    if plan.get("base") != BASE or plan.get("target") != TARGET:
        fail("the plan is for %s -> %s" % (plan.get("base"), plan.get("target")))
    if plan.get("material_object") != obj(MI_PKG) or plan.get("base_material_object") != obj(BASE_MI_PKG):
        fail("the plan paints with %s over %s" % (plan.get("material_object"), plan.get("base_material_object")))
    if (plan.get("inputs") or {}).get("base_fingerprint", {}).get("package_sha256") != BASE_SHA:
        fail("the plan was made from a fingerprint of other base bytes")
    if plan.get("problems"):
        fail("the plan has %d problem(s)" % len(plan["problems"]))
    return plan, sha(PLAN)


def save_target():
    if world_package() != TARGET:
        fail("refusing to save: the loaded world is %s, not %s" % (world_package(), TARGET))
    before = sha(umap(TARGET))
    ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    if not ok:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        ok = bool(unreal.EditorLoadingAndSavingUtils.save_map(w, TARGET))
    if not ok:
        fail("level save failed")
    after = sha(umap(TARGET))
    if after == before:
        log("note: the save left the target byte-identical")
    return after


def component_of(a, name):
    for c in (safe(lambda: a.get_components_by_class(unreal.StaticMeshComponent)) or []):
        if c.get_name() == name:
            return c
    return None


# ---------------------------------------------------------------------------------------- state checks

def assignment_issues(actors, asg, expect_to):
    a = actors.get(asg["actor_key"])
    if a is None:
        return ["%s: actor %s missing" % (asg["label"], asg["actor_key"])]
    out = []
    if safe(lambda: a.get_actor_label()) != asg["label"]:
        out.append("%s: label is %r" % (asg["label"], safe(lambda: a.get_actor_label())))
    if asg["run_tag"] not in tags_of(a):
        out.append("%s: run tag missing" % asg["label"])
    c = component_of(a, asg["component"])
    if c is None:
        return out + ["%s: component %s missing" % (asg["label"], asg["component"])]
    m = safe(lambda: c.get_editor_property("static_mesh"))
    if (m.get_path_name() if m else None) != asg["mesh"]:
        out.append("%s: mesh is %s" % (asg["label"], m.get_path_name() if m else None))
    if safe(lambda: str(c.get_collision_profile_name())) != "NoCollision":
        out.append("%s: collision profile is %s (paint stays NoCollision)" % (asg["label"], safe(lambda: str(c.get_collision_profile_name()))))
    mats, ovs = mat_list(c, TARGET), override_list(c, TARGET)
    want_m = asg["to"] if expect_to else asg["from"]
    want_o = [asg["to"]] + asg["from_overrides"][1:] if expect_to else asg["from_overrides"]
    if len(mats) != asg["slots"] or (mats[asg["slot"]] if len(mats) > asg["slot"] else None) != want_m:
        out.append("%s: slot %d is %s, expected %s" % (asg["label"], asg["slot"], mats, want_m))
    if ovs != want_o:
        out.append("%s: override list %s, expected %s" % (asg["label"], ovs, want_o))
    return out


def ring_issues(actors, e, which):
    a = actors.get(e["actor_key"])
    if a is None:
        return ["%s: actor %s missing" % (e["label"], e["actor_key"])]
    if safe(lambda: a.get_actor_label()) != e["label"]:
        return ["%s: label is %r" % (e["label"], safe(lambda: a.get_actor_label()))]
    loc, rot, scale = actor_transform(a)
    return ["%s: %s" % (e["label"], x) for x in transform_ok(loc, rot, scale, e[which])]


def piece_issues(a, spec):
    out = []
    smc = safe(lambda: a.static_mesh_component)
    if smc is None:
        return ["%s: no static mesh component" % spec["label"]]
    if safe(lambda: a.get_actor_label()) != spec["label"]:
        out.append("label is %r" % safe(lambda: a.get_actor_label()))
    if tags_of(a) != sorted(spec["tags"]):
        out.append("tags %s" % tags_of(a))
    if safe(lambda: str(a.get_folder_path()), "") != spec["folder"]:
        out.append("folder %s" % safe(lambda: str(a.get_folder_path())))
    mesh = safe(lambda: smc.get_editor_property("static_mesh"))
    if mesh is None or mesh.get_path_name() != spec["mesh"]:
        out.append("mesh is %s" % (mesh.get_path_name() if mesh else None))
    mats, ovs = mat_list(smc, TARGET), override_list(smc, TARGET)
    if mats != [spec["material"]] or ovs != [spec["material"]]:
        out.append("materials %s / overrides %s" % (mats, ovs))
    loc, rot, scale = actor_transform(a)
    out += transform_ok(loc, rot, scale, {"loc": spec["location"], "rot": spec["rotation"], "scale": spec["scale"]})
    if not smc.is_visible():
        out.append("component not visible")
    if bool(a.get_editor_property("hidden")):
        out.append("actor hidden")
    if not bool(a.get_actor_enable_collision()):
        out.append("actor collision disabled")
    prof, ce = str(smc.get_collision_profile_name()), enum_name(smc.get_collision_enabled())
    want = "QUERY_AND_PHYSICS" if spec["collision"] == "BlockAll" else "NO_COLLISION"
    if prof != spec["collision"] or ce != want:
        out.append("collision %s/%s, expected %s/%s" % (prof, ce, spec["collision"], want))
    return ["%s: %s" % (spec["label"], x) for x in out]


def ff_actors(actors):
    """Every actor carrying the FF1 tag, by label."""
    out = {}
    for k, a in actors.items():
        if FF_TAG in tags_of(a):
            out.setdefault(safe(lambda: a.get_actor_label()), []).append((k, a))
    return out


def planned_labels_in_use(actors, plan):
    want = set(p["label"] for p in plan["pieces"])
    out = []
    for k, a in actors.items():
        lab = safe(lambda: a.get_actor_label())
        if lab in want and FF_TAG not in tags_of(a):
            out.append("label %s is already used by %s" % (lab, k))
    return out


def check_state(plan, actors, which):
    """Every difference between the loaded level and the plan's 'clean' or 'applied' state."""
    issues = []
    ff = ff_actors(actors)
    if which == "clean":
        if ff:
            issues.append("%d FF1 actor(s) present: %s" % (sum(len(v) for v in ff.values()), sorted(ff)[:6]))
    else:
        want = {p["label"]: p for p in plan["pieces"]}
        for lab, spec in sorted(want.items()):
            got = ff.get(lab, [])
            if len(got) != 1:
                issues.append("%s: %d FF1 actor(s) carry this label" % (lab, len(got)))
                continue
            issues += piece_issues(got[0][1], spec)
        extra = sorted(l for l in ff if l not in want)
        if extra:
            issues.append("FF1 actor(s) the plan does not contain: %s" % extra[:6])
    for e in plan["ring"]["edits"]:
        issues += ring_issues(actors, e, "from" if which == "clean" else "to")
    for asg in plan["assignments"]:
        issues += assignment_issues(actors, asg, which == "applied")
    return issues


def compare(base_fp, tgt_fp, plan, applied):
    """Actor for actor against the base: clean -> identical; applied -> ONLY the plan's pieces (extra actors,
    each exactly as specified), ring edits (transform only) and slot changes may differ."""
    asg = {(a["actor_key"], a["component"]): a for a in plan["assignments"]} if applied else {}
    ring = {e["actor_key"]: e for e in plan["ring"]["edits"]} if applied else {}
    pieces = {p["label"]: p for p in plan["pieces"]} if applied else {}
    unexpected, expected = [], {"pieces": 0, "ring_edits": 0, "slot_changes": 0}
    extra = [k for k in tgt_fp if k not in base_fp]
    for k in sorted(set(base_fp) - set(tgt_fp)):
        unexpected.append({"actor": k, "issue": "missing in target"})
    for k in sorted(set(base_fp) & set(tgt_fp)):
        b, t = base_fp[k], tgt_fp[k]
        if b == t:
            continue
        e = ring.get(k)
        for f in b:
            if f == "components":
                continue
            if e and f in ("loc", "rot", "scale"):
                continue
            if b[f] != t.get(f):
                unexpected.append({"actor": k, "label": b.get("label"), "field": f, "base": b[f], "target": t.get(f)})
        if e:
            bad = transform_ok(t["loc"], t["rot"], t["scale"], e["to"])
            if bad:
                unexpected.append({"actor": k, "label": b.get("label"), "ring": bad})
            else:
                expected["ring_edits"] += 1
        bc, tc = b["components"], t["components"]
        for cn in sorted(set(bc) | set(tc)):
            x, y = bc.get(cn), tc.get(cn)
            if x == y:
                continue
            a = asg.get((k, cn))
            if a and x and y:
                want = dict(x, materials=[a["to"]] + x["materials"][1:], overrides=[a["to"]] + x["overrides"][1:])
                if (x.get("materials") or [None])[0] == a["from"] and x.get("overrides") == a["from_overrides"] and y == want:
                    expected["slot_changes"] += 1
                    continue
            unexpected.append({"actor": k, "label": b.get("label"), "component": cn, "base": x, "target": y})
    # extra actors: exactly the plan's pieces
    seen = {}
    for k in extra:
        t = tgt_fp[k]
        spec = pieces.get(t["label"])
        if spec is None:
            unexpected.append({"actor": k, "label": t["label"], "issue": "extra actor not in the plan"})
            continue
        seen[t["label"]] = seen.get(t["label"], 0) + 1
        bad = []
        want = {"class": "StaticMeshActor", "hidden": False, "actor_collision": True, "tags": sorted(spec["tags"]),
                "folder": spec["folder"]}
        for f, v in want.items():
            if t.get(f) != v:
                bad.append("%s %s (expected %s)" % (f, t.get(f), v))
        bad += transform_ok(t["loc"], t["rot"], t["scale"], {"loc": spec["location"], "rot": spec["rotation"],
                                                             "scale": spec["scale"]})
        wc = {"StaticMeshComponent0": {"class": "StaticMeshComponent", "visible": True, "profile": spec["collision"],
                                       "collision": "QUERY_AND_PHYSICS" if spec["collision"] == "BlockAll" else "NO_COLLISION",
                                       "mesh": spec["mesh"], "materials": [spec["material"]], "overrides": [spec["material"]]}}
        if t["components"] != wc:
            bad.append("components %s" % t["components"])
        if bad:
            unexpected.append({"actor": k, "label": t["label"], "piece": bad})
        else:
            expected["pieces"] += 1
    for lab in pieces:
        if seen.get(lab, 0) != 1 and applied:
            unexpected.append({"label": lab, "issue": "%d actor(s) for this planned piece" % seen.get(lab, 0)})
    want_total = (len(plan["pieces"]) + len(plan["ring"]["edits"]) + len(plan["assignments"])) if applied else 0
    got_total = sum(expected.values())
    return {"actors_base": len(base_fp), "actors_target": len(tgt_fp),
            "identical_actors": sum(1 for k in base_fp if tgt_fp.get(k) == base_fp[k]),
            "extra_actors": len(extra), "expected": expected, "expected_changes": got_total,
            "expected_missing": want_total - got_total, "unexpected": unexpected[:60], "unexpected_count": len(unexpected)}


# ---------------------------------------------------------------------------------------- stages

def stage_base_fingerprint():
    guard_names()
    REPORT["base_facts"] = base_facts()
    fp = snapshot(BASE)
    if sha(umap(BASE)) != BASE_SHA:
        fail("the base changed while it was being fingerprinted")
    data = {"package": BASE, "sha256": BASE_SHA, "actors": len(fp),
            "components": sum(len(v["components"]) for v in fp.values()), "editor_only_components_skipped": EDITOR_ONLY["count"],
            "loaded_first_in_process": True, "utc": now(), "by": "ib_garrison_forecourt_finish.py base-fingerprint",
            "fingerprint": fp}
    write_json(OUT / "base_fingerprint.json", data)
    REPORT.update({"result": "fingerprinted", "actors": data["actors"], "components": data["components"],
                   "editor_only_components_skipped": EDITOR_ONLY["count"], "file": str(OUT / "base_fingerprint.json"),
                   "file_sha256": sha(OUT / "base_fingerprint.json")})


def stage_copy():
    guard_names()
    REPORT["base_facts"] = base_facts()
    if umap(TARGET).exists() or unreal.EditorAssetLibrary.does_asset_exist(TARGET):
        fail("%s already exists; candidates are never overwritten" % TARGET)
    if receipt_file(TARGET).exists():
        fail("a receipt for %s already exists without its map" % TARGET)
    live0 = sha(umap(LIVE))
    dup = unreal.EditorAssetLibrary.duplicate_asset(BASE, TARGET)
    if dup is None:
        fail("duplicate_asset returned nothing")
    saved = unreal.EditorAssetLibrary.save_asset(TARGET, only_if_is_dirty=False)
    dup = None
    if not saved or not umap(TARGET).is_file():
        fail("duplicated but could not save %s" % TARGET)
    if sha(umap(BASE)) != BASE_SHA:
        fail("THE BASE FILE CHANGED during the copy")
    if sha(umap(LIVE)) != live0:
        fail("THE LIVE MAP CHANGED during the copy")
    pend = {"target": TARGET, "target_sha256": sha(umap(TARGET)), "base": REPORT["base_facts"], "live_sha256": live0,
            "method": "EditorAssetLibrary.duplicate_asset + save_asset", "utc": now()}
    write_json(OUT / "copy_pending.json", pend)
    REPORT.update({"result": "copied", "target_sha256": pend["target_sha256"],
                   "next": "IB_GARRISON_FF_STAGE=copy-verify in a NEW process"})


def stage_copy_verify():
    guard_names()
    if receipt_file(TARGET).exists():
        fail("%s already has a receipt" % TARGET)
    pf = OUT / "copy_pending.json"
    if not pf.is_file():
        fail("no copy_pending.json: only a copy made by the copy stage can be verified")
    pend = json.loads(pf.read_text(encoding="utf-8"))
    if pend.get("target") != TARGET:
        fail("the pending copy is %s" % pend.get("target"))
    facts = base_facts()
    tgt_sha = sha(umap(TARGET))
    if tgt_sha != pend.get("target_sha256"):
        fail("the copy changed since it was made")
    if facts["sha256"] != pend["base"]["sha256"]:
        fail("the base changed since the copy was made")
    bfp = read_base_fp()
    tfp = snapshot(TARGET)
    empty = {"pieces": [], "ring": {"edits": []}, "assignments": []}
    cmp_ = compare(bfp, tfp, empty, applied=False)
    cmp_["editor_only_components_skipped_in_target"] = EDITOR_ONLY["count"]
    REPORT["comparison"] = cmp_
    if cmp_["unexpected_count"]:
        fail("the copy does not mirror the base (%d differences)" % cmp_["unexpected_count"])
    if sha(umap(TARGET)) != tgt_sha or sha(umap(BASE)) != facts["sha256"]:
        fail("a map file changed while it was being verified")
    rec = {"target_package": TARGET, "target_file": str(umap(TARGET)), "kind": KIND,
           "base_fingerprint": {"file": BASE_FP, "sha256": sha(BASE_FP)},
           "disposable": True, "source_package": BASE, "source_sha256": facts["sha256"],
           "source_receipt": {"file": facts["receipt"], "sha256": facts["receipt_sha256"], "last": facts["receipt_last"]},
           "source_material": facts.get("base_material"), "source_lineage": facts["lineage"],
           "method": pend.get("method"), "material": None, "ownership": None,
           "history": [{"state": "created", "sha256": tgt_sha, "utc": now(), "by": "ib_garrison_forecourt_finish.py copy",
                        "actors": len(tfp), "verified_against_base": "actor for actor, component for component (%d)"
                        % sum(len(v["components"]) for v in tfp.values())}]}
    write_json(receipt_file(TARGET), rec)
    REPORT.update({"result": "created-verified", "target_sha256": tgt_sha, "receipt": str(receipt_file(TARGET))})


def stage_material():
    guard_names(need_mi=True)
    rec = read_receipt(TARGET)
    target_state(rec)
    if rec.get("material"):
        m = material_state(rec)
        mi = load_mi()
        f = mi_facts(mi)
        if f.get("parent") != PARENT or [o["name"] for o in f.get("vector_overrides") or []] != [PARAM]:
            fail("the recorded material instance is not this tool's: %s" % f)
        want = [round(v, 6) for v in RGB] + [1.0]
        if all(abs(a - b) <= TOL for a, b in zip(f.get("effective_base_color") or [], want)):
            REPORT.update({"result": "already-created-verified", "material": m})
            return
        old = {k: m.get(k) for k in ("sha256", "value", "created_utc", "retinted_utc")}
        MEL.set_material_instance_vector_parameter_value(mi, PARAM, unreal.LinearColor(RGB[0], RGB[1], RGB[2], 1.0))
        MEL.update_material_instance(mi)
        f = mi_facts(mi)
        issues = mi_issues(f)
        if issues:
            fail("retint did not verify: " + "; ".join(issues) + " (NOT saved)")
        if not unreal.EditorAssetLibrary.save_loaded_asset(mi, False):
            fail("could not save the retinted %s" % MI_PKG)
        m.setdefault("history", []).append(old)
        m.update({"sha256": sha(uasset(MI_PKG)), "value": RGB + [1.0], "facts": f, "retinted_utc": now()})
        rec["material"] = m
        write_json(receipt_file(TARGET), rec)
        REPORT.update({"result": "material-retinted", "material": m})
        return
    if uasset(MI_PKG).exists() or unreal.EditorAssetLibrary.does_asset_exist(MI_PKG):
        fail("%s already exists; it is never overwritten" % MI_PKG)
    parent_file = PROJECT / "Content/LevelPrototyping/Materials/M_FlatCol.uasset"
    p0, b0 = sha(parent_file), sha(uasset(BASE_MI_PKG)) if BASE_MI_PKG else None
    mi, facts = create_material()
    issues = mi_issues(facts)
    if issues:
        fail("the new material instance is wrong (%s); NOTHING was saved" % "; ".join(issues))
    if not unreal.EditorAssetLibrary.save_loaded_asset(mi, False) or not uasset(MI_PKG).is_file():
        fail("could not save %s" % MI_PKG)
    if sha(parent_file) != p0:
        fail("THE PARENT MATERIAL FILE CHANGED")
    if BASE_MI_PKG and sha(uasset(BASE_MI_PKG)) != b0:
        fail("THE BASE'S MATERIAL INSTANCE CHANGED")
    rec["material"] = {"package": MI_PKG, "object": obj(MI_PKG), "file": str(uasset(MI_PKG)),
                       "sha256": sha(uasset(MI_PKG)), "parent": PARENT, "parent_file_sha256": p0,
                       "parameter": PARAM, "value": RGB + [1.0], "facts": facts, "created_utc": now(),
                       "by": "ib_garrison_forecourt_finish.py material", "owned_by": TARGET}
    write_json(receipt_file(TARGET), rec)
    REPORT.update({"result": "material-created", "material": rec["material"]})


def preflight(plan, actors):
    problems = check_state(plan, actors, "clean") + planned_labels_in_use(actors, plan)
    assets = {}
    for p in plan["pieces"]:
        for key in ("mesh", "material"):
            path = p[key]
            if path not in assets:
                assets[path] = unreal.EditorAssetLibrary.load_asset(path)
                if assets[path] is None:
                    problems.append("cannot load %s %s" % (key, path))
    for asg in plan["assignments"]:
        if asg["to"] not in assets:
            assets[asg["to"]] = unreal.EditorAssetLibrary.load_asset(asg["to"])
            if assets[asg["to"]] is None:
                problems.append("cannot load %s" % asg["to"])
    return problems, assets


def ownership(plan, plan_sha, rec):
    """The FF1-owned set: what this candidate owns and what it changed in its copy of the base."""
    return {"candidate": TARGET, "material_instance": {"package": MI_PKG, "sha256": (rec.get("material") or {}).get("sha256")},
            "plan": {"file": PLAN, "sha256": plan_sha},
            "new_actors": {"count": len(plan["pieces"]), "tag": FF_TAG, "folder": plan["folder"],
                           "labels": [p["label"] for p in plan["pieces"]]},
            "ring_actors_reshaped": [{"label": e["label"], "actor_key": e["actor_key"], "segment": e["segment"]}
                                     for e in plan["ring"]["edits"]],
            "repainted_slots": len(plan["assignments"]),
            "never_written": [BASE, BASE_MI_PKG, LIVE, "every earlier preview and receipt", "shared MI_Landmass_* assets",
                              "M_FlatCol"]}


def stage_plan_check():
    guard_names(need_mi=True)
    rec = read_receipt(TARGET)
    last = target_state(rec)
    material_state(rec)
    plan, plan_sha = read_plan()
    load(TARGET)
    actors = live_actors(TARGET)
    if last["state"] == "applied":
        issues = check_state(plan, actors, "applied")
        REPORT.update({"result": "applied-state %s" % ("verified" if not issues else "DIFFERS"), "issues": issues[:40]})
        if issues:
            fail("%d difference(s) from the applied plan" % len(issues))
        return
    problems, _ = preflight(plan, actors)
    REPORT.update({"state": last["state"], "plan_sha256": plan_sha, "preflight_problems": problems[:60],
                   "counts": plan["counts"], "result": "preflight clean" if not problems else "preflight found problems"})
    if problems:
        fail("preflight found %d problem(s)" % len(problems))


def stage_apply(revert=False):
    guard_names(need_mi=True)
    rec = read_receipt(TARGET)
    last = target_state(rec)
    m = material_state(rec)
    plan, plan_sha = read_plan()
    f = mi_facts(load_mi())
    issues = mi_issues(f)
    if issues:
        fail("material instance: " + "; ".join(issues))
    REPORT["material_facts"] = f
    load(TARGET)
    actors = live_actors(TARGET)
    if revert:
        if last.get("state") != "applied":
            fail("nothing to revert: the last state is %s" % last.get("state"))
        if last.get("plan_sha256") != plan_sha:
            fail("the target was applied with a different plan")
        before = last.get("ring_before")
        if not before or len(before) != len(plan["ring"]["edits"]):
            fail("no complete captured ring state to restore; refusing to revert")
        conflicts = check_state(plan, actors, "applied")
        if conflicts:
            for c in conflicts[:30]:
                unreal.log_error("GARRISON FF1: revert conflict: " + c)
            fail("REVERT REFUSED: %d conflict(s) with the applied plan; nothing was changed" % len(conflicts))
        bad = []
        for lab, rows in ff_actors(actors).items():
            for k, a in rows:
                if not EAS.destroy_actor(a):
                    bad.append("could not remove %s" % lab)
        for e in plan["ring"]["edits"]:
            b = before[e["actor_key"]]
            set_transform(actors[e["actor_key"]], b["loc"], b["rot"], b["scale"])
        base_mi = unreal.EditorAssetLibrary.load_asset(plan["base_material_object"])
        for asg in plan["assignments"]:
            component_of(actors[asg["actor_key"]], asg["component"]).set_material(asg["slot"], base_mi)
        actors = live_actors(TARGET)
        for e in plan["ring"]["edits"]:
            a = actors[e["actor_key"]]
            loc, rot, scale = actor_transform(a)
            b = before[e["actor_key"]]
            if not (vec_close(loc, b["loc"], 1e-3) and rot_close(rot, b["rot"], 1e-4) and vec_close(scale, b["scale"], 1e-6)):
                bad.append("%s: not restored exactly (%s)" % (e["label"], [loc, rot, scale]))
        bad += check_state(plan, actors, "clean")
        if bad:
            for b in bad[:30]:
                unreal.log_error("GARRISON FF1: " + b)
            fail("the revert did not verify (%d issue(s)); NOT saved" % len(bad))
        after = save_target()
        rec["history"].append({"state": "reverted", "sha256": after, "plan_sha256": plan_sha, "material_sha256": m["sha256"],
                               "removed": len(plan["pieces"]), "ring_restored": len(before),
                               "slots_restored": len(plan["assignments"]), "utc": now(),
                               "by": "ib_garrison_forecourt_finish.py revert"})
        write_json(receipt_file(TARGET), rec)
        REPORT.update({"result": "reverted-verified", "saved": True, "sha256": after})
        return
    if last.get("state") == "applied":
        if last.get("plan_sha256") != plan_sha:
            fail("the target was applied with a different plan")
        problems = check_state(plan, actors, "applied")
        if problems:
            fail("the receipt says applied but %d thing(s) differ; nothing changed" % len(problems))
        REPORT.update({"result": "already-applied-verified", "saved": False, "sha256": last["sha256"]})
        return
    if last.get("state") not in ("created", "reverted"):
        fail("cannot apply from state %s" % last.get("state"))
    problems, assets = preflight(plan, actors)
    if problems:
        for p in problems[:40]:
            unreal.log_error("GARRISON FF1: " + p)
        fail("preflight found %d problem(s); NOTHING was changed" % len(problems))
    ring_before = {}
    for e in plan["ring"]["edits"]:
        loc, rot, scale = actor_transform(actors[e["actor_key"]])
        ring_before[e["actor_key"]] = {"label": e["label"], "loc": loc, "rot": rot, "scale": scale}
    bad, stage = [], "pieces"
    for spec in plan["pieces"]:
        rot = unreal.Rotator(roll=spec["rotation"]["roll"], pitch=spec["rotation"]["pitch"], yaw=spec["rotation"]["yaw"])
        a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*spec["location"]), rot)
        if a is None:
            bad.append("spawn failed for " + spec["label"])
            break
        smc = a.static_mesh_component
        if not smc.set_static_mesh(assets[spec["mesh"]]):
            bad.append("%s: set_static_mesh returned False" % spec["label"])
        smc.set_material(0, assets[spec["material"]])
        a.set_actor_scale3d(unreal.Vector(*spec["scale"]))
        a.set_actor_rotation(rot, False)
        smc.set_collision_profile_name(spec["collision"])
        a.set_actor_label(spec["label"])
        a.set_editor_property("tags", list(spec["tags"]))
        a.set_folder_path(spec["folder"])
    actors = live_actors(TARGET)
    if not bad:
        ff = ff_actors(actors)
        for spec in plan["pieces"]:
            got = ff.get(spec["label"], [])
            if len(got) != 1:
                bad.append("%s: %d FF1 actor(s) after spawning" % (spec["label"], len(got)))
            else:
                bad += piece_issues(got[0][1], spec)
    if not bad:
        stage = "ring"
        for e in plan["ring"]["edits"]:
            to = e["to"]
            set_transform(actors[e["actor_key"]], to["loc"], to["rot"], to["scale"])
        for e in plan["ring"]["edits"]:
            bad += ring_issues(actors, e, "to")
    if not bad:
        stage = "paint"
        mi = assets[plan["material_object"]] if plan["material_object"] in assets else load_mi()
        for asg in plan["assignments"]:
            component_of(actors[asg["actor_key"]], asg["component"]).set_material(asg["slot"], mi)
        bad += sum((assignment_issues(actors, asg, True) for asg in plan["assignments"]), [])
    if not bad:
        stage = "final"
        bad += check_state(plan, live_actors(TARGET), "applied")
    if bad:
        for b in bad[:40]:
            unreal.log_error("GARRISON FF1: " + b)
        fail("%d operation(s) did not verify at stage '%s'; NOT saved (a commandlet discards the level on exit)"
             % (len(bad), stage))
    after = save_target()
    rec["ownership"] = ownership(plan, plan_sha, rec)
    rec["history"].append({"state": "applied", "sha256": after, "plan_sha256": plan_sha, "material_sha256": m["sha256"],
                           "pieces": len(plan["pieces"]), "ring_edits": len(plan["ring"]["edits"]),
                           "assignments": len(plan["assignments"]), "ring_before": ring_before, "utc": now(),
                           "by": "ib_garrison_forecourt_finish.py apply"})
    write_json(receipt_file(TARGET), rec)
    write_json(OUT / "ownership_manifest.json", rec["ownership"])
    REPORT.update({"result": "applied-verified", "saved": True, "sha256": after, "pieces": len(plan["pieces"]),
                   "ring_edits": len(plan["ring"]["edits"]), "assigned": len(plan["assignments"]),
                   "ownership_manifest": str(OUT / "ownership_manifest.json"),
                   "ownership_manifest_sha256": sha(OUT / "ownership_manifest.json")})


def stage_verify():
    guard_names(need_mi=True)
    rec = read_receipt(TARGET)
    last = target_state(rec)
    m = material_state(rec)
    plan, plan_sha = read_plan()
    f = mi_facts(load_mi())
    REPORT["material_facts"] = f
    issues = ["material instance: " + i for i in mi_issues(f)]
    if sha(umap(BASE)) != rec["source_sha256"]:
        issues.append("the base changed since the copy")
    if BASE_MI_PKG and sha(uasset(BASE_MI_PKG)) != (rec.get("source_material") or {}).get("sha256"):
        issues.append("the base's material instance changed since the copy")
    applied = last.get("state") == "applied"
    if applied and last.get("plan_sha256") != plan_sha:
        issues.append("the applied state used a different plan")
    bfp = read_base_fp()
    load(TARGET)
    actors = live_actors(TARGET)
    state_issues = check_state(plan, actors, "applied" if applied else "clean")
    tfp = fingerprint(TARGET)
    unreal.SystemLibrary.collect_garbage()
    cmp_ = compare(bfp, tfp, plan, applied)
    cmp_["editor_only_components_skipped_in_target"] = EDITOR_ONLY["count"]
    REPORT.update({"state": last.get("state"), "target_sha256": last["sha256"], "plan_sha256": plan_sha,
                   "state_issues": state_issues[:30], "comparison": cmp_, "material_sha256": m["sha256"]})
    issues += state_issues
    if cmp_["unexpected_count"] or cmp_["expected_missing"]:
        issues.append("comparison with the base: %d unexpected, %d planned changes missing"
                      % (cmp_["unexpected_count"], cmp_["expected_missing"]))
    if sha(umap(TARGET)) != last["sha256"]:
        issues.append("the target changed while it was being verified")
    REPORT["issues"] = issues
    if issues:
        fail("verify found %d issue(s): %s" % (len(issues), "; ".join(issues[:4])))
    REPORT["result"] = "verified"


STAGES = {"base-fingerprint": stage_base_fingerprint, "copy": stage_copy, "copy-verify": stage_copy_verify,
          "material": stage_material, "plan-check": stage_plan_check, "apply": stage_apply,
          "revert": lambda: stage_apply(revert=True), "verify": stage_verify}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if STAGE not in STAGES:
        fail("IB_GARRISON_FF_STAGE must be one of %s" % ", ".join(STAGES))
    live0 = sha(umap(LIVE))
    base0 = sha(umap(BASE)) if BASE.startswith("/Game/") else None
    bmi0 = sha(uasset(BASE_MI_PKG)) if BASE_MI_PKG.startswith("/Game/") else None
    STAGES[STAGE]()
    if sha(umap(LIVE)) != live0:
        fail("THE LIVE MAP CHANGED during this stage")
    if base0 is not None and sha(umap(BASE)) != base0:
        fail("THE BASE MAP CHANGED during this stage")
    if bmi0 is not None and sha(uasset(BASE_MI_PKG)) != bmi0:
        fail("THE BASE'S MATERIAL INSTANCE CHANGED during this stage")
    REPORT["live_sha256"] = live0
    REPORT["status"] = "complete"


try:
    main()
except Exception:
    REPORT["status"] = "failed"
    REPORT["error"] = traceback.format_exc()[-1500:]
    unreal.log_error("GARRISON FF1 FAILED\n" + traceback.format_exc())
    raise
finally:
    REPORT["finished_utc"] = now()
    try:
        write_json(OUT / ("ff_%s.json" % (STAGE or "none")), REPORT)
    except Exception:
        pass
