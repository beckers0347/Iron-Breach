"""PS1: PAD-RING PAINT STABILITY on a NEW disposable candidate made from the accepted FF1 candidate.

Derived from Scripts/ib_garrison_forecourt_finish.py (FF1, SHA256 66BC7889..., left unchanged): the same base / copy /
fingerprint / receipt machinery. The one change it makes is a declared ring REPRESENTATION swap (ps1_plan.json):

  suppress   the 96 generated pad-ring geometry segments (P3's IBGC_Pad_Ring_00..31, reshaped by FF1, and FF1's
             IBGC_FF_Pad_Ring96_00..63): the visibility of each one's StaticMeshComponent0 is turned off (they stay
             in the level, NoCollision, same transform, mesh and material), with each prior value captured at apply
             time and restored by revert
  decal      ONE new DecalActor (tagged IB_GarrisonCB1 + IB_GarrisonPaintStability) at the pad centre projecting
             the candidate-owned deferred-decal material, which draws the same ring (18.9 m centre-line radius,
             40 cm wide, FF1's Base Color) analytically with a box-filtered coverage (Scripts/ib_garrison_ring_decal.py)
  material   the NEW candidate-owned Material in the candidate's own subfolder (never overwrites a package)

The base candidate, its material instance and receipt, the live map and every earlier preview are never written.
Only the target map and the new material are ever saved.

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script="Scripts/ib_garrison_ring_stability.py"

Stages (IB_PS_STAGE), each in its own process:
  base-fingerprint  loads ONLY the base (first map in the process) and records its fingerprint (primitive AND
                    decal components)
  copy              duplicate the verified base to the NEW target; saves only the target
  copy-verify       (new process) loads ONLY the target; compares it with the base fingerprint; receipt 'created'
  material          create the NEW decal material (never overwrites; verifies domain, blend, pins, parameters)
  plan-check        read-only: the plan's preconditions against the loaded target (exactly the apply preflight)
  apply             preflight -> hide the 96 segments -> spawn the decal -> whole-state check -> save -> 'applied'.
                    A repeat on the verified applied state changes and saves nothing.
  revert            the level must be exactly the applied state (else REFUSED) -> remove the decal -> restore each
                    segment's captured visibility -> verify clean -> save -> 'reverted'
  verify            (new process) receipt state == file bytes; the material's facts; and an actor-for-actor,
                    component-for-component comparison with the base fingerprint in which ONLY the 96 visibility
                    flags and the one decal actor may differ (applied) or nothing may (clean)

Environment:
  IB_PS_BASE, IB_PS_BASE_SHA256    the accepted base (FF1) and its map SHA256
  IB_PS_TARGET                     the NEW candidate under /Game/_GarrisonPreview_Disposable/
  IB_PS_PLAN                       ps1_plan.json (plan-check / apply / revert / verify)
  IB_PS_MATERIAL                   the NEW decal material (in a subfolder)
  IB_PS_BASE_MI                    the base's paint instance (FF1), never written
  IB_PS_BASE_FINGERPRINT           base_fingerprint.json from the base-fingerprint stage
  IB_PS_OUT                        output folder for the stage report (ps_<stage>.json)
"""
import unreal, json, os, hashlib, datetime, traceback, re, math, sys
from pathlib import Path

PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
LIVE = "/Game/LevelPrototyping/CarrowGateGarrison"
RUN_TAG = "IB_GarrisonCB1"
PS_TAG = "IB_GarrisonPaintStability"
KIND = "PS1 paint stability candidate"
LOC_TOL, ROT_TOL, SCALE_TOL = 0.5, 0.05, 1e-4
STAGE = (os.environ.get("IB_PS_STAGE") or "").strip().lower()
BASE = (os.environ.get("IB_PS_BASE") or "").strip().rstrip("/")
BASE_SHA = (os.environ.get("IB_PS_BASE_SHA256") or "").strip().upper()
TARGET = (os.environ.get("IB_PS_TARGET") or "").strip().rstrip("/")
PLAN = os.environ.get("IB_PS_PLAN")
MAT_PKG = (os.environ.get("IB_PS_MATERIAL") or "").strip().rstrip("/").split(".")[0]
BASE_MI_PKG = (os.environ.get("IB_PS_BASE_MI") or "").strip().rstrip("/").split(".")[0]
BASE_FP = os.environ.get("IB_PS_BASE_FINGERPRINT")
PROJECT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = Path(os.environ.get("IB_PS_OUT") or str(PROJECT / "Saved/GarrisonRestructure/ps1"))
RECEIPTS = PROJECT / "Saved/GarrisonRestructure/receipts"
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ib_garrison_ring_decal as ringdecal  # noqa: E402

REPORT = {"tool": "ib_garrison_ring_stability", "stage": STAGE, "base": BASE, "target": TARGET, "material": MAT_PKG,
          "started_utc": datetime.datetime.utcnow().isoformat() + "Z"}


def log(m):
    unreal.log("GARRISON PS1: " + str(m))


def fail(m):
    raise RuntimeError("GARRISON PS1 REFUSED: " + str(m))


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


def decal_record(c, pkg):
    m = safe(lambda: c.get_decal_material())
    s = safe(lambda: c.get_editor_property("decal_size"))
    return {"class": c.get_class().get_name(), "visible": safe(lambda: bool(c.is_visible())),
            "material": norm_path(m.get_path_name(), pkg) if m else None,
            "decal_size": [round(s.x, 3), round(s.y, 3), round(s.z, 3)] if s else None,
            "fade_screen_size": safe(lambda: round(float(c.get_editor_property("fade_screen_size")), 6)),
            "sort_order": safe(lambda: int(c.get_editor_property("sort_order")))}


EDITOR_ONLY = {"count": 0}


def fingerprint(pkg):
    """FF1's fingerprint (every actor's transform, flags, tags, folder and every in-game primitive component;
    editor-only components counted, not compared), extended with every DECAL component."""
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
        for c in (safe(lambda: a.get_components_by_class(unreal.DecalComponent)) or []):
            comps[c.get_name()] = decal_record(c, pkg)
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


# ---------------------------------------------------------------------------------------- guards

def guard_names(need_mat=False):
    if not TARGET.startswith(PREVIEW_ROOT) or TARGET in (LIVE, BASE):
        fail("the target must be a NEW package under %s (not the live map or the base)" % PREVIEW_ROOT)
    if not BASE.startswith(PREVIEW_ROOT) or BASE == TARGET:
        fail("the base must be a verified candidate under %s" % PREVIEW_ROOT)
    if need_mat:
        rest = MAT_PKG[len(PREVIEW_ROOT):] if MAT_PKG.startswith(PREVIEW_ROOT) else ""
        if "/" not in rest or not rest.split("/")[-1]:
            fail("the material must be in a SUBFOLDER of %s, got %r" % (PREVIEW_ROOT, MAT_PKG))
        if MAT_PKG == BASE_MI_PKG or MAT_PKG.split("/")[:-1] == BASE_MI_PKG.split("/")[:-1]:
            fail("the new material must live in the candidate's own subfolder, not the base's")


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
        fail("IB_PS_BASE_FINGERPRINT must name the base-fingerprint stage's base_fingerprint.json")
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
        fail("the receipt does not describe a PS1 candidate made from %s" % BASE)
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
        fail("no material recorded for %s; run the material stage" % TARGET)
    if m.get("package") != MAT_PKG:
        fail("the receipt's material is %s, not %s" % (m.get("package"), MAT_PKG))
    cur = sha(uasset(MAT_PKG))
    if cur != m.get("sha256"):
        fail("the material file changed since it was recorded (%s... != %s...)" % (str(cur)[:12], str(m.get("sha256"))[:12]))
    return m


def load_mat():
    m = unreal.EditorAssetLibrary.load_asset(obj(MAT_PKG))
    if m is None:
        fail("%s did not load" % MAT_PKG)
    return m


def read_plan():
    if not PLAN or not Path(PLAN).is_file():
        fail("IB_PS_PLAN must name the reviewed ps1_plan.json")
    plan = json.loads(Path(PLAN).read_text(encoding="utf-8"))
    if plan.get("base") != BASE or plan.get("target") != TARGET:
        fail("the plan is for %s -> %s" % (plan.get("base"), plan.get("target")))
    if plan.get("material_object") != obj(MAT_PKG) or plan["decal"].get("material") != obj(MAT_PKG):
        fail("the plan draws with %s" % plan.get("material_object"))
    if plan.get("base_sha256") != BASE_SHA:
        fail("the plan was made for other base bytes")
    if len(plan.get("suppress") or []) != 96:
        fail("the plan must suppress exactly the 96 ring segments (has %d)" % len(plan.get("suppress") or []))
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

def suppress_issues(actors, s, which):
    """One ring segment: identity, run tag, mesh, NoCollision, material, and visibility (clean: visible;
    applied: hidden). Nothing else of the segment may change."""
    a = actors.get(s["actor_key"])
    if a is None:
        return ["%s: actor %s missing" % (s["label"], s["actor_key"])]
    out = []
    if safe(lambda: a.get_actor_label()) != s["label"]:
        out.append("%s: label is %r" % (s["label"], safe(lambda: a.get_actor_label())))
    if RUN_TAG not in tags_of(a):
        out.append("%s: run tag missing" % s["label"])
    c = component_of(a, s["component"])
    if c is None:
        return out + ["%s: component %s missing" % (s["label"], s["component"])]
    m = safe(lambda: c.get_editor_property("static_mesh"))
    if (m.get_path_name() if m else None) != s["mesh"]:
        out.append("%s: mesh is %s" % (s["label"], m.get_path_name() if m else None))
    if safe(lambda: str(c.get_collision_profile_name())) != "NoCollision":
        out.append("%s: collision profile is %s" % (s["label"], safe(lambda: str(c.get_collision_profile_name()))))
    if mat_list(c, TARGET) != [s["material"]]:
        out.append("%s: materials %s" % (s["label"], mat_list(c, TARGET)))
    want = s["from_visible"] if which == "clean" else s["to_visible"]
    if bool(c.is_visible()) != want:
        out.append("%s: visible is %s, expected %s" % (s["label"], bool(c.is_visible()), want))
    if bool(safe(lambda: a.get_editor_property("hidden"), False)):
        out.append("%s: actor hidden flag set" % s["label"])
    return out


def ps_actors(actors):
    out = {}
    for k, a in actors.items():
        if PS_TAG in tags_of(a):
            out.setdefault(safe(lambda: a.get_actor_label()), []).append((k, a))
    return out


def decal_components(a):
    return safe(lambda: a.get_components_by_class(unreal.DecalComponent)) or []


def decal_issues(a, spec):
    out = []
    if a.get_class().get_name() != "DecalActor":
        out.append("class %s" % a.get_class().get_name())
    if safe(lambda: a.get_actor_label()) != spec["label"]:
        out.append("label is %r" % safe(lambda: a.get_actor_label()))
    if tags_of(a) != sorted(spec["tags"]):
        out.append("tags %s" % tags_of(a))
    if safe(lambda: str(a.get_folder_path()), "") != spec["folder"]:
        out.append("folder %s" % safe(lambda: str(a.get_folder_path())))
    loc, rot, scale = actor_transform(a)
    out += transform_ok(loc, rot, scale, {"loc": spec["location"], "rot": spec["rotation"], "scale": spec["scale"]})
    if bool(a.get_editor_property("hidden")):
        out.append("actor hidden")
    dcs = decal_components(a)
    if len(dcs) != 1:
        return ["%s: %s" % (spec["label"], x) for x in out + ["%d decal components" % len(dcs)]]
    r = decal_record(dcs[0], TARGET)
    want = {"class": "DecalComponent", "visible": True, "material": spec["material"],
            "decal_size": [round(v, 3) for v in spec["decal_size"]], "fade_screen_size": round(spec["fade_screen_size"], 6),
            "sort_order": spec["sort_order"]}
    for k, v in want.items():
        if r.get(k) != v:
            out.append("decal %s is %s, expected %s" % (k, r.get(k), v))
    return ["%s: %s" % (spec["label"], x) for x in out]


def check_state(plan, actors, which):
    issues = []
    ps = ps_actors(actors)
    if which == "clean":
        if ps:
            issues.append("%d PS1 actor(s) present: %s" % (sum(len(v) for v in ps.values()), sorted(ps)[:6]))
    else:
        spec = plan["decal"]
        got = ps.get(spec["label"], [])
        if len(got) != 1:
            issues.append("%s: %d PS1 actor(s) carry this label" % (spec["label"], len(got)))
        else:
            issues += decal_issues(got[0][1], spec)
        extra = sorted(l for l in ps if l != spec["label"])
        if extra:
            issues.append("PS1 actor(s) the plan does not contain: %s" % extra[:6])
    for s in plan["suppress"]:
        issues += suppress_issues(actors, s, which)
    return issues


def compare(base_fp, tgt_fp, plan, applied):
    """Actor for actor against the base: clean -> identical; applied -> ONLY the 96 segments' component visibility
    (True -> False, every other field equal) and exactly one extra actor, the planned decal."""
    sup = {(s["actor_key"], s["component"]): s for s in plan["suppress"]} if applied else {}
    unexpected, expected = [], {"suppressed": 0, "decal": 0}
    extra = [k for k in tgt_fp if k not in base_fp]
    for k in sorted(set(base_fp) - set(tgt_fp)):
        unexpected.append({"actor": k, "issue": "missing in target"})
    for k in sorted(set(base_fp) & set(tgt_fp)):
        b, t = base_fp[k], tgt_fp[k]
        if b == t:
            continue
        for f in b:
            if f != "components" and b[f] != t.get(f):
                unexpected.append({"actor": k, "label": b.get("label"), "field": f, "base": b[f], "target": t.get(f)})
        bc, tc = b["components"], t["components"]
        for cn in sorted(set(bc) | set(tc)):
            x, y = bc.get(cn), tc.get(cn)
            if x == y:
                continue
            s = sup.get((k, cn))
            if s and x and y and x.get("visible") is True and y.get("visible") is False and dict(x, visible=False) == y:
                expected["suppressed"] += 1
                continue
            unexpected.append({"actor": k, "label": b.get("label"), "component": cn, "base": x, "target": y})
    spec = plan["decal"] if applied else None
    for k in extra:
        t = tgt_fp[k]
        if spec is None or t["label"] != spec["label"]:
            unexpected.append({"actor": k, "label": t["label"], "issue": "extra actor not in the plan"})
            continue
        bad = []
        want = {"class": "DecalActor", "hidden": False, "tags": sorted(spec["tags"]), "folder": spec["folder"]}
        for f, v in want.items():
            if t.get(f) != v:
                bad.append("%s %s (expected %s)" % (f, t.get(f), v))
        bad += transform_ok(t["loc"], t["rot"], t["scale"], {"loc": spec["location"], "rot": spec["rotation"], "scale": spec["scale"]})
        wc = {"class": "DecalComponent", "visible": True, "material": spec["material"],
              "decal_size": [round(v, 3) for v in spec["decal_size"]], "fade_screen_size": round(spec["fade_screen_size"], 6),
              "sort_order": spec["sort_order"]}
        dcs = [v for v in t["components"].values() if v.get("class") == "DecalComponent"]
        others = [v for v in t["components"].values() if v.get("class") != "DecalComponent"]
        if len(dcs) != 1 or dcs[0] != wc or others:
            bad.append("components %s" % t["components"])
        if bad:
            unexpected.append({"actor": k, "label": t["label"], "decal": bad})
        else:
            expected["decal"] += 1
    want_total = (len(plan["suppress"]) + 1) if applied else 0
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
            "decal_components": sum(1 for v in fp.values() for c in v["components"].values() if c.get("class") == "DecalComponent"),
            "loaded_first_in_process": True, "utc": now(), "by": "ib_garrison_ring_stability.py base-fingerprint",
            "fingerprint": fp}
    write_json(OUT / "base_fingerprint.json", data)
    REPORT.update({"result": "fingerprinted", "actors": data["actors"], "components": data["components"],
                   "decal_components": data["decal_components"], "editor_only_components_skipped": EDITOR_ONLY["count"],
                   "file": str(OUT / "base_fingerprint.json"), "file_sha256": sha(OUT / "base_fingerprint.json")})


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
                   "next": "IB_PS_STAGE=copy-verify in a NEW process"})


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
    empty = {"suppress": [], "decal": None}
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
           "history": [{"state": "created", "sha256": tgt_sha, "utc": now(), "by": "ib_garrison_ring_stability.py copy",
                        "actors": len(tfp), "verified_against_base": "actor for actor, component for component (%d)"
                        % sum(len(v["components"]) for v in tfp.values())}]}
    write_json(receipt_file(TARGET), rec)
    REPORT.update({"result": "created-verified", "target_sha256": tgt_sha, "receipt": str(receipt_file(TARGET))})


def create_material():
    folder, name = MAT_PKG.rsplit("/", 1)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())
    if m is None:
        fail("create_asset returned nothing for %s" % MAT_PKG)
    pre = safe(lambda: MEL.get_num_material_expressions(m), 0)
    MEL.delete_all_material_expressions(m)          # e.g. a default Substrate slab: the ring uses the legacy pins
    conn = ringdecal.build(m)
    MEL.recompile_material(m)
    f = ringdecal.facts(m)
    f["connections"] = conn
    f["expressions_from_factory_removed"] = pre
    return m, f


def stage_material():
    guard_names(need_mat=True)
    rec = read_receipt(TARGET)
    target_state(rec)
    if rec.get("material"):
        material_state(rec)
        f = ringdecal.facts(load_mat())
        iss = ringdecal.issues(f)
        if iss:
            fail("the recorded material no longer verifies: " + "; ".join(iss))
        REPORT.update({"result": "already-created-verified", "material": rec["material"], "facts": f})
        return
    if uasset(MAT_PKG).exists() or unreal.EditorAssetLibrary.does_asset_exist(MAT_PKG):
        fail("%s already exists; it is never overwritten" % MAT_PKG)
    b0 = sha(uasset(BASE_MI_PKG)) if BASE_MI_PKG else None
    m, f = create_material()
    iss = ringdecal.issues(f)
    if iss:
        fail("the new material is wrong (%s); NOTHING was saved" % "; ".join(iss))
    if not unreal.EditorAssetLibrary.save_loaded_asset(m, False) or not uasset(MAT_PKG).is_file():
        fail("could not save %s" % MAT_PKG)
    if BASE_MI_PKG and sha(uasset(BASE_MI_PKG)) != b0:
        fail("THE BASE'S MATERIAL INSTANCE CHANGED")
    rec["material"] = {"package": MAT_PKG, "object": obj(MAT_PKG), "file": str(uasset(MAT_PKG)),
                       "sha256": sha(uasset(MAT_PKG)), "kind": "deferred decal material (analytic ring coverage)",
                       "module": {"file": str(Path(ringdecal.__file__)), "sha256": sha(ringdecal.__file__)},
                       "facts": f, "created_utc": now(), "by": "ib_garrison_ring_stability.py material", "owned_by": TARGET}
    write_json(receipt_file(TARGET), rec)
    REPORT.update({"result": "material-created", "material": rec["material"]})


def preflight(plan, actors):
    problems = check_state(plan, actors, "clean")
    for k, a in actors.items():
        if safe(lambda: a.get_actor_label()) == plan["decal"]["label"] and PS_TAG not in tags_of(a):
            problems.append("label %s is already used by %s" % (plan["decal"]["label"], k))
    if unreal.EditorAssetLibrary.load_asset(plan["decal"]["material"]) is None:
        problems.append("cannot load %s" % plan["decal"]["material"])
    return problems


def ownership(plan, plan_sha, rec):
    return {"candidate": TARGET, "material": {"package": MAT_PKG, "sha256": (rec.get("material") or {}).get("sha256")},
            "plan": {"file": PLAN, "sha256": plan_sha},
            "new_actor": {"label": plan["decal"]["label"], "class": "DecalActor", "tags": plan["decal"]["tags"],
                          "folder": plan["decal"]["folder"]},
            "suppressed_segments": [{"label": s["label"], "actor_key": s["actor_key"], "component": s["component"]}
                                    for s in plan["suppress"]],
            "never_written": [BASE, BASE_MI_PKG, LIVE, "every earlier preview and receipt", "shared MI_Landmass_* assets",
                              "M_FlatCol", "Concrete_Mat", "engine content", "project rendering configuration"]}


def stage_plan_check():
    guard_names(need_mat=True)
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
    problems = preflight(plan, actors)
    REPORT.update({"state": last["state"], "plan_sha256": plan_sha, "preflight_problems": problems[:60],
                   "suppress": len(plan["suppress"]), "result": "preflight clean" if not problems else "preflight found problems"})
    if problems:
        fail("preflight found %d problem(s)" % len(problems))


def stage_apply(revert=False):
    guard_names(need_mat=True)
    rec = read_receipt(TARGET)
    last = target_state(rec)
    m = material_state(rec)
    plan, plan_sha = read_plan()
    f = ringdecal.facts(load_mat())
    iss = ringdecal.issues(f)
    if iss:
        fail("material: " + "; ".join(iss))
    REPORT["material_facts"] = f
    load(TARGET)
    actors = live_actors(TARGET)
    if revert:
        if last.get("state") != "applied":
            fail("nothing to revert: the last state is %s" % last.get("state"))
        if last.get("plan_sha256") != plan_sha:
            fail("the target was applied with a different plan")
        before = last.get("visible_before")
        if not before or len(before) != len(plan["suppress"]):
            fail("no complete captured visibility state to restore; refusing to revert")
        conflicts = check_state(plan, actors, "applied")
        if conflicts:
            for c in conflicts[:30]:
                unreal.log_error("GARRISON PS1: revert conflict: " + c)
            fail("REVERT REFUSED: %d conflict(s) with the applied plan; nothing was changed" % len(conflicts))
        bad = []
        for lab, rows in ps_actors(actors).items():
            for k, a in rows:
                if not EAS.destroy_actor(a):
                    bad.append("could not remove %s" % lab)
        for s in plan["suppress"]:
            c = component_of(actors[s["actor_key"]], s["component"])
            c.modify()
            c.set_visibility(bool(before[s["actor_key"]]), False)
        actors = live_actors(TARGET)
        for s in plan["suppress"]:
            c = component_of(actors[s["actor_key"]], s["component"])
            if bool(c.is_visible()) != bool(before[s["actor_key"]]):
                bad.append("%s: visibility not restored" % s["label"])
        bad += check_state(plan, actors, "clean")
        if bad:
            for b in bad[:30]:
                unreal.log_error("GARRISON PS1: " + b)
            fail("the revert did not verify (%d issue(s)); NOT saved" % len(bad))
        after = save_target()
        rec["history"].append({"state": "reverted", "sha256": after, "plan_sha256": plan_sha, "material_sha256": m["sha256"],
                               "decal_removed": 1, "visibility_restored": len(before), "utc": now(),
                               "by": "ib_garrison_ring_stability.py revert"})
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
    problems = preflight(plan, actors)
    if problems:
        for p in problems[:40]:
            unreal.log_error("GARRISON PS1: " + p)
        fail("preflight found %d problem(s); NOTHING was changed" % len(problems))
    visible_before = {}
    for s in plan["suppress"]:
        visible_before[s["actor_key"]] = bool(component_of(actors[s["actor_key"]], s["component"]).is_visible())
    bad, stage = [], "suppress"
    for s in plan["suppress"]:
        c = component_of(actors[s["actor_key"]], s["component"])
        c.modify()
        c.set_visibility(False, False)
    for s in plan["suppress"]:
        bad += suppress_issues(actors, s, "applied")
    if not bad:
        stage = "decal"
        spec = plan["decal"]
        rot = unreal.Rotator(roll=spec["rotation"]["roll"], pitch=spec["rotation"]["pitch"], yaw=spec["rotation"]["yaw"])
        a = EAS.spawn_actor_from_class(unreal.DecalActor, unreal.Vector(*spec["location"]), rot)
        if a is None:
            bad.append("decal spawn failed")
        else:
            a.set_actor_scale3d(unreal.Vector(*spec["scale"]))
            a.set_actor_rotation(rot, False)
            a.set_actor_label(spec["label"])
            a.set_editor_property("tags", list(spec["tags"]))
            a.set_folder_path(spec["folder"])
            dcs = decal_components(a)
            if len(dcs) != 1:
                bad.append("the spawned decal has %d decal components" % len(dcs))
            else:
                dc = dcs[0]
                dc.set_decal_material(unreal.EditorAssetLibrary.load_asset(spec["material"]))
                dc.set_editor_property("decal_size", unreal.Vector(*spec["decal_size"]))
                dc.set_editor_property("fade_screen_size", float(spec["fade_screen_size"]))
                dc.set_editor_property("sort_order", int(spec["sort_order"]))
    if not bad:
        stage = "final"
        bad += check_state(plan, live_actors(TARGET), "applied")
    if bad:
        for b in bad[:40]:
            unreal.log_error("GARRISON PS1: " + b)
        fail("%d operation(s) did not verify at stage '%s'; NOT saved (a commandlet discards the level on exit)" % (len(bad), stage))
    after = save_target()
    rec["ownership"] = ownership(plan, plan_sha, rec)
    rec["history"].append({"state": "applied", "sha256": after, "plan_sha256": plan_sha, "material_sha256": m["sha256"],
                           "suppressed": len(plan["suppress"]), "decal": plan["decal"]["label"],
                           "visible_before": visible_before, "utc": now(), "by": "ib_garrison_ring_stability.py apply"})
    write_json(receipt_file(TARGET), rec)
    write_json(OUT / "ownership_manifest.json", rec["ownership"])
    REPORT.update({"result": "applied-verified", "saved": True, "sha256": after, "suppressed": len(plan["suppress"]),
                   "decal": plan["decal"]["label"], "ownership_manifest": str(OUT / "ownership_manifest.json"),
                   "ownership_manifest_sha256": sha(OUT / "ownership_manifest.json")})


def stage_verify():
    guard_names(need_mat=True)
    rec = read_receipt(TARGET)
    last = target_state(rec)
    m = material_state(rec)
    plan, plan_sha = read_plan()
    f = ringdecal.facts(load_mat())
    REPORT["material_facts"] = f
    issues = ["material: " + i for i in ringdecal.issues(f)]
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
        fail("IB_PS_STAGE must be one of %s" % ", ".join(STAGES))
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
    unreal.log_error("GARRISON PS1 FAILED\n" + traceback.format_exc())
    raise
finally:
    REPORT["finished_utc"] = now()
    try:
        write_json(OUT / ("ps_%s.json" % (STAGE or "none")), REPORT)
    except Exception:
        pass
