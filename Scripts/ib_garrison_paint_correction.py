"""YM1: preview-local YELLOW DECK PAINT for the generated garrison markings.

The markings on the PF1 candidate use MI_Landmass_HelipadMarking, whose only override is a
'Color' parameter that its parent M_FlatCol does not have; the parent's 'Base Color' default
(0.18 grey) therefore shows. This tool makes a NEW disposable candidate from a verified base
candidate, creates a NEW material instance in a clearly named subfolder of the disposable
preview folder (parent M_FlatCol, untouched; 'Base Color' set), and assigns it ONLY to the
generated, candidate-owned marking pieces, by explicit actor / component / material-slot
identity, with every original value recorded for an exact revert. Shared MI_Landmass assets,
the live map, the base candidate and every earlier preview are never written.

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script="Scripts/ib_garrison_paint_correction.py"

Stages (IB_GARRISON_PAINT_STAGE), each in its own process:
  smoke        read-only rehearsal: loads the base, fingerprints it, checks the markings' current
               material, creates the material instance IN MEMORY ONLY (never saved) and assigns it
               to a transient component. Writes nothing but its report.
  copy         duplicate the verified base candidate to the NEW target; saves only the target
  base-fingerprint  (new process) loads ONLY the base and records its fingerprint (every actor's
               transform, flags, tags, folder and every non-editor-only primitive component's mesh,
               materials, override list and collision) with the base's file SHA256
  copy-verify  (new process) both files unchanged since the copy; loads ONLY the target and compares it
               with the recorded base fingerprint; writes the target's receipt ('created').
               Each map is fingerprinted as the FIRST map loaded in its own process: a commandlet that
               loaded the base and then its duplicate reported the duplicate's water profile and the
               door frames' editor-sprite names differently (job 152), while each map loaded first
               reports them identically (probe job 154).
  material     create the material instance (never overwrites an existing package); save only it;
               record it (file SHA256, parent, overrides, effective values) in the target's receipt
  plan         read-only: the explicit assignment list from the base layout plan's generated
               marking pieces -> assignments.json (+ the inherited live-map users of the shared MI,
               which are left untouched)
  apply        preflight every assignment (identity, mesh, NoCollision, current material and override
               list == the recorded originals) -> set slot 0 -> verify -> save the target only ->
               receipt 'applied'. A repeat on the verified applied state changes and saves nothing.
  revert       exact restore of every recorded original (material and override list) -> verify ->
               save -> receipt 'reverted'
  verify       (new process) receipt state == file bytes; the material instance's effective
               parameters; every assignment; and an actor-for-actor, component-for-component
               comparison with the recorded base fingerprint in which ONLY the assigned slots may differ

Environment:
  IB_GARRISON_BASE            the verified base candidate (e.g. .../CarrowGateGarrison_PierFinish1)
  IB_GARRISON_BASE_SHA256     its expected map SHA256 (must equal its receipt's last 'applied' state)
  IB_GARRISON_TARGET_LEVEL    the NEW candidate (under /Game/_GarrisonPreview_Disposable/)
  IB_GARRISON_PLAN            the base's layout plan.json (names the generated marking pieces)
  IB_GARRISON_PAINT_MI        the new material instance package, in a SUBFOLDER of the disposable folder
  IB_GARRISON_PAINT_RGB       linear Base Color, default 0.95,0.82,0.15
  IB_GARRISON_ASSIGNMENTS     assignments.json (apply / revert / verify)
  IB_GARRISON_BASE_FINGERPRINT  base_fingerprint.json from the base-fingerprint stage (copy-verify / verify)
  IB_GARRISON_OUT             output folder for the stage report
"""
import unreal, json, os, hashlib, datetime, traceback, re
from pathlib import Path

PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
LIVE = "/Game/LevelPrototyping/CarrowGateGarrison"
PARENT = "/Game/LevelPrototyping/Materials/M_FlatCol.M_FlatCol"
SHARED_MARK = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_HelipadMarking.MI_Landmass_HelipadMarking"
PARAM = "Base Color"
TOL = 1e-4
STAGE = (os.environ.get("IB_GARRISON_PAINT_STAGE") or "").strip().lower()
BASE = (os.environ.get("IB_GARRISON_BASE") or "").strip().rstrip("/")
BASE_SHA = (os.environ.get("IB_GARRISON_BASE_SHA256") or "").strip().upper()
TARGET = (os.environ.get("IB_GARRISON_TARGET_LEVEL") or "").strip().rstrip("/")
LAYOUT_PLAN = os.environ.get("IB_GARRISON_PLAN")
MI_PKG = (os.environ.get("IB_GARRISON_PAINT_MI") or "").strip().rstrip("/").split(".")[0]
RGB = [float(v) for v in (os.environ.get("IB_GARRISON_PAINT_RGB") or "0.95,0.82,0.15").split(",")]
ASSIGN = os.environ.get("IB_GARRISON_ASSIGNMENTS")
BASE_FP = os.environ.get("IB_GARRISON_BASE_FINGERPRINT")
PROJECT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = Path(os.environ.get("IB_GARRISON_OUT") or str(PROJECT / "Saved/GarrisonRestructure/paint"))
RECEIPTS = PROJECT / "Saved/GarrisonRestructure/receipts"
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary
REPORT = {"tool": "ib_garrison_paint_correction", "stage": STAGE, "base": BASE, "target": TARGET,
          "material_instance": MI_PKG, "rgb": RGB, "started_utc": datetime.datetime.utcnow().isoformat() + "Z"}


def log(m):
    unreal.log("GARRISON PAINT: " + str(m))


def fail(m):
    raise RuntimeError("GARRISON PAINT REFUSED: " + str(m))


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
    """Asset paths stay as they are; a subobject of the level itself (e.g. a construction-script
    material instance) is made package-independent so base and copy compare equal."""
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
    """Every actor of the loaded level: transform, flags, tags, folder and every primitive component
    that exists in game (editor-only components such as the door frames' sprites are counted, not compared)."""
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


def compare(base_fp, tgt_fp, assignments, applied):
    """Only the assigned slots may differ, and only from -> to (applied) or not at all (clean)."""
    allowed = {}
    if applied:
        for a in assignments:
            allowed[(a["actor_key"], a["component"])] = a
    unexpected, expected = [], 0
    for k in sorted(set(base_fp) | set(tgt_fp)):
        b, t = base_fp.get(k), tgt_fp.get(k)
        if b is None or t is None:
            unexpected.append({"actor": k, "issue": "missing in target" if t is None else "extra in target"})
            continue
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
            asg = allowed.get((k, cn))
            if asg and x and y:
                want = dict(x, materials=[asg["to"]] + x["materials"][1:],
                            overrides=[asg["to"]] + x["overrides"][1:])
                if (x.get("materials") or [None])[0] == asg["from"] and x.get("overrides") == asg["from_overrides"] \
                        and y == want:
                    expected += 1
                    continue
            unexpected.append({"actor": k, "label": b.get("label"), "component": cn, "base": x, "target": y})
    missing_expected = (len(assignments) - expected) if applied else 0
    return {"actors_base": len(base_fp), "actors_target": len(tgt_fp),
            "identical_actors": sum(1 for k in base_fp if tgt_fp.get(k) == base_fp[k]),
            "expected_slot_changes": expected, "expected_slot_changes_missing": missing_expected,
            "unexpected": unexpected[:60], "unexpected_count": len(unexpected)}


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
    """The new instance, IN MEMORY: nothing is written until the caller has checked it and saves it."""
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


def smoke_component(mi):
    """A transient component, never in any level: set the new MI on slot 0 and read it back."""
    smc = unreal.new_object(unreal.StaticMeshComponent)
    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    smc.set_static_mesh(cube)
    shared = unreal.EditorAssetLibrary.load_asset(SHARED_MARK)
    smc.set_material(0, shared)
    before = (mat_list(smc, "-"), override_list(smc, "-"))
    smc.set_material(0, mi)
    after = (mat_list(smc, "-"), override_list(smc, "-"))
    smc.set_material(0, shared)
    back = (mat_list(smc, "-"), override_list(smc, "-"))
    return {"before": before, "after": after, "restored": back}


# ---------------------------------------------------------------------------------------- guards

def guard_names(need_base=True, need_mi=False):
    if not TARGET.startswith(PREVIEW_ROOT) or TARGET in (LIVE, BASE):
        fail("the target must be a NEW package under %s (not the live map or the base)" % PREVIEW_ROOT)
    if need_base and (not BASE.startswith(PREVIEW_ROOT) or BASE == TARGET):
        fail("the base must be a verified candidate under %s" % PREVIEW_ROOT)
    if need_mi:
        rest = MI_PKG[len(PREVIEW_ROOT):] if MI_PKG.startswith(PREVIEW_ROOT) else ""
        if "/" not in rest or not rest.split("/")[-1]:
            fail("the material instance must be in a SUBFOLDER of %s, got %r" % (PREVIEW_ROOT, MI_PKG))


def base_facts():
    """The base must be byte-identical to the expected hash and to its receipt's last 'applied' state."""
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
    return {"package": BASE, "file": str(umap(BASE)), "sha256": cur, "receipt": str(receipt_file(BASE)),
            "receipt_sha256": sha(receipt_file(BASE)), "receipt_last": last,
            "lineage": {"source_package": rec.get("source_package"), "source_sha256": rec.get("source_sha256")}}


def read_base_fp():
    """The base fingerprint recorded by the base-fingerprint stage, if it is of these exact base bytes."""
    if not BASE_FP or not Path(BASE_FP).is_file():
        fail("IB_GARRISON_BASE_FINGERPRINT must name the base-fingerprint stage's base_fingerprint.json")
    d = json.loads(Path(BASE_FP).read_text(encoding="utf-8"))
    cur = sha(umap(BASE))
    if d.get("package") != BASE or d.get("sha256") != cur or cur != BASE_SHA:
        fail("the recorded base fingerprint is of %s at %s..., not of %s at its current %s..."
             % (d.get("package"), str(d.get("sha256"))[:12], BASE, str(cur)[:12]))
    return d["fingerprint"]


def target_state(rec):
    """The receipt's last state, if and only if the target file is byte-identical to it."""
    if rec is None:
        fail("no receipt for %s; create it with the copy stages first" % TARGET)
    if rec.get("kind") != "YM1 paint correction candidate" or rec.get("source_package") != BASE:
        fail("the receipt does not describe a YM1 candidate made from %s" % BASE)
    cur = sha(umap(TARGET))
    last = rec["history"][-1]
    if cur != last.get("sha256"):
        fail("STALE TARGET: its file (%s...) is not its last recorded state '%s' (%s...)"
             % (str(cur)[:12], last.get("state"), str(last.get("sha256"))[:12]))
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


def load_mi():
    mi = unreal.EditorAssetLibrary.load_asset(obj(MI_PKG))
    if mi is None:
        fail("%s did not load" % MI_PKG)
    return mi


def read_assignments():
    if not ASSIGN or not Path(ASSIGN).is_file():
        fail("IB_GARRISON_ASSIGNMENTS must name the plan stage's assignments.json")
    data = json.loads(Path(ASSIGN).read_text(encoding="utf-8"))
    if data.get("target") != TARGET or data.get("to") != obj(MI_PKG):
        fail("assignments.json was made for %s -> %s" % (data.get("target"), data.get("to")))
    return data, sha(ASSIGN)


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


def assignment_issues(actors, asg, expect_to):
    """Everything about one assignment that must hold before (expect_to False) or after it."""
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
        out.append("%s: collision profile is %s (paint must stay NoCollision)"
                   % (asg["label"], safe(lambda: str(c.get_collision_profile_name()))))
    mats, ovs = mat_list(c, TARGET), override_list(c, TARGET)
    want_m = asg["to"] if expect_to else asg["from"]
    want_o = [asg["to"]] + asg["from_overrides"][1:] if expect_to else asg["from_overrides"]
    if len(mats) != asg["slots"] or (mats[asg["slot"]] if len(mats) > asg["slot"] else None) != want_m:
        out.append("%s: slot %d is %s, expected %s" % (asg["label"], asg["slot"], mats, want_m))
    if ovs != want_o:
        out.append("%s: override list %s, expected %s" % (asg["label"], ovs, want_o))
    return out


# ---------------------------------------------------------------------------------------- stages

def stage_smoke():
    guard_names(need_mi=True)
    REPORT["base_facts"] = base_facts()
    plan = json.loads(Path(LAYOUT_PLAN).read_text(encoding="utf-8"))
    labels = sorted(p["label"] for p in plan["pieces"] if p.get("material") == SHARED_MARK)
    fp = snapshot(BASE)
    by_label = {}
    for k, v in fp.items():
        if plan["run_tag"] in v["tags"]:
            by_label.setdefault(v["label"], []).append((k, v))
    comps = sum(len(v["components"]) for v in fp.values())
    marks = {}
    for l in labels:
        rows = by_label.get(l, [])
        marks[l] = [{"key": k, "components": v["components"]} for k, v in rows]
    REPORT["base_fingerprint"] = {"actors": len(fp), "primitive_components": comps,
                                  "marking_labels_in_plan": len(labels),
                                  "marking_actors_found": sum(1 for l in labels if len(marks[l]) == 1),
                                  "example": marks[labels[0]] if labels else None,
                                  "slot0_counts": {}}
    for l in labels:
        for row in marks[l]:
            for cn, c in row["components"].items():
                m0 = (c.get("materials") or [None])[0]
                REPORT["base_fingerprint"]["slot0_counts"][m0] = REPORT["base_fingerprint"]["slot0_counts"].get(m0, 0) + 1
    exists = unreal.EditorAssetLibrary.does_asset_exist(MI_PKG) or uasset(MI_PKG).exists()
    REPORT["material_package_exists_before"] = bool(exists)
    if not exists:
        mi, facts = create_material()
        REPORT["in_memory_material"] = facts
        REPORT["in_memory_material_issues"] = mi_issues(facts)
        REPORT["transient_component"] = smoke_component(mi)
        mi = None
    REPORT["material_package_on_disk_after"] = uasset(MI_PKG).exists()
    REPORT["dirty_packages"] = [p.get_name() for p in (safe(lambda: unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()) or [])] \
        + [p.get_name() for p in (safe(lambda: unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()) or [])]
    REPORT["result"] = "rehearsed; nothing saved"


def stage_base_fingerprint():
    guard_names()
    REPORT["base_facts"] = base_facts()
    fp = snapshot(BASE)
    if sha(umap(BASE)) != BASE_SHA:
        fail("the base changed while it was being fingerprinted")
    data = {"package": BASE, "sha256": BASE_SHA, "actors": len(fp),
            "components": sum(len(v["components"]) for v in fp.values()), "editor_only_components_skipped": EDITOR_ONLY["count"],
            "loaded_first_in_process": True, "utc": now(), "fingerprint": fp}
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
                   "next": "IB_GARRISON_PAINT_STAGE=copy-verify in a NEW process"})


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
    cmp_ = compare(bfp, tfp, [], applied=False)
    cmp_["editor_only_components_skipped_in_target"] = EDITOR_ONLY["count"]
    REPORT["comparison"] = cmp_
    if cmp_["unexpected_count"]:
        fail("the copy does not mirror the base (%d differences)" % cmp_["unexpected_count"])
    if sha(umap(TARGET)) != tgt_sha or sha(umap(BASE)) != facts["sha256"]:
        fail("a map file changed while it was being verified")
    plan_sha = sha(LAYOUT_PLAN) if LAYOUT_PLAN else None
    rec = {"target_package": TARGET, "target_file": str(umap(TARGET)), "kind": "YM1 paint correction candidate",
           "base_fingerprint": {"file": BASE_FP, "sha256": sha(BASE_FP)},
           "disposable": True, "source_package": BASE, "source_sha256": facts["sha256"],
           "source_receipt": {"file": facts["receipt"], "sha256": facts["receipt_sha256"], "last": facts["receipt_last"]},
           "source_lineage": facts["lineage"], "layout_plan": {"file": LAYOUT_PLAN, "sha256": plan_sha},
           "method": pend.get("method"), "material": None,
           "history": [{"state": "created", "sha256": tgt_sha, "utc": now(), "by": "ib_garrison_paint_correction.py copy",
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
        # retint the candidate's OWN instance (the markings reference it by path; no map changes)
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
    p0 = sha(parent_file)
    mi, facts = create_material()
    issues = mi_issues(facts)
    if issues:
        fail("the new material instance is wrong (%s); NOTHING was saved" % "; ".join(issues))
    if not unreal.EditorAssetLibrary.save_loaded_asset(mi, False) or not uasset(MI_PKG).is_file():
        fail("could not save %s" % MI_PKG)
    if sha(parent_file) != p0:
        fail("THE PARENT MATERIAL FILE CHANGED")
    rec["material"] = {"package": MI_PKG, "object": obj(MI_PKG), "file": str(uasset(MI_PKG)),
                       "sha256": sha(uasset(MI_PKG)), "parent": PARENT, "parent_file_sha256": p0,
                       "parameter": PARAM, "value": RGB + [1.0], "facts": facts, "created_utc": now(),
                       "by": "ib_garrison_paint_correction.py material", "owned_by": TARGET}
    write_json(receipt_file(TARGET), rec)
    REPORT.update({"result": "material-created", "material": rec["material"]})


def stage_plan():
    guard_names(need_mi=True)
    rec = read_receipt(TARGET)
    last = target_state(rec)
    m = material_state(rec)
    plan = json.loads(Path(LAYOUT_PLAN).read_text(encoding="utf-8"))
    pieces = {p["label"]: p for p in plan["pieces"] if p.get("material") == SHARED_MARK}
    load(TARGET)
    actors = live_actors(TARGET)
    by_label, inherited = {}, []
    for k, a in actors.items():
        tg = tags_of(a)
        lab = safe(lambda: a.get_actor_label())
        if plan["run_tag"] in tg and lab in pieces:
            by_label.setdefault(lab, []).append((k, a))
        else:
            for c in (safe(lambda: a.get_components_by_class(unreal.MeshComponent)) or []):
                if SHARED_MARK in mat_list(c, TARGET):
                    inherited.append({"actor_key": k, "label": lab, "component": c.get_name(),
                                      "materials": mat_list(c, TARGET)})
    problems, rows = [], []
    for lab in sorted(pieces):
        found = by_label.get(lab, [])
        if len(found) != 1:
            problems.append("%s: %d generated actors" % (lab, len(found)))
            continue
        k, a = found[0]
        smc = safe(lambda: a.static_mesh_component)
        if smc is None:
            problems.append("%s: no static mesh component" % lab)
            continue
        mats, ovs = mat_list(smc, TARGET), override_list(smc, TARGET)
        mesh = safe(lambda: smc.get_editor_property("static_mesh"))
        row = {"label": lab, "actor_key": k, "actor": level_prefix(TARGET) + k, "class": a.get_class().get_name(),
               "run_tag": plan["run_tag"], "tags": tags_of(a), "component": smc.get_name(), "slot": 0,
               "slots": len(mats), "mesh": mesh.get_path_name() if mesh else None,
               "collision_profile": safe(lambda: str(smc.get_collision_profile_name())),
               "from": mats[0] if mats else None, "from_overrides": ovs, "to": m["object"],
               "zone": pieces[lab].get("zone"), "kind": pieces[lab].get("kind"),
               "origin": "PF1" if "IB_GarrisonPierFinish" in (pieces[lab].get("tags") or []) else "P3"}
        if row["from"] != SHARED_MARK or ovs != [SHARED_MARK] or row["slots"] != 1:
            problems.append("%s: slot 0 %s, overrides %s" % (lab, row["from"], ovs))
        if row["collision_profile"] != "NoCollision":
            problems.append("%s: collision %s" % (lab, row["collision_profile"]))
        if row["mesh"] != pieces[lab].get("mesh"):
            problems.append("%s: mesh %s" % (lab, row["mesh"]))
        rows.append(row)
    data = {"target": TARGET, "target_sha256_at_plan": last["sha256"], "base": BASE, "layout_plan": LAYOUT_PLAN,
            "layout_plan_sha256": sha(LAYOUT_PLAN), "from": SHARED_MARK, "to": m["object"],
            "material_sha256": m["sha256"], "assignments": rows, "count": len(rows),
            "by_origin": {o: sum(1 for r in rows if r["origin"] == o) for o in ("P3", "PF1")},
            "by_kind": {}, "left_untouched_inherited_users_of_shared_mi": inherited, "problems": problems,
            "made_utc": now()}
    for r in rows:
        key = "%s %s %s" % (r["origin"], r["zone"], r["kind"])
        data["by_kind"][key] = data["by_kind"].get(key, 0) + 1
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "assignments.json", data)
    REPORT.update({"result": "planned" if not problems else "planned-with-problems", "assignments": len(rows),
                   "assignments_file": str(OUT / "assignments.json"), "assignments_sha256": sha(OUT / "assignments.json"),
                   "inherited_users": len(inherited), "problems": problems})
    if problems:
        fail("%d problem(s) in the assignment plan: %s" % (len(problems), "; ".join(problems[:5])))


def stage_apply(revert=False):
    guard_names(need_mi=True)
    rec = read_receipt(TARGET)
    last = target_state(rec)
    m = material_state(rec)
    data, asg_sha = read_assignments()
    if data.get("problems"):
        fail("the assignment plan has problems")
    f = mi_facts(load_mi())
    issues = mi_issues(f)
    if issues:
        fail("material instance: " + "; ".join(issues))
    REPORT["material_facts"] = f
    rows = data["assignments"]
    load(TARGET)
    actors = live_actors(TARGET)
    if revert:
        if last.get("state") != "applied":
            fail("nothing to revert: the last state is %s" % last.get("state"))
        if last.get("assignments_sha256") != asg_sha:
            fail("the target was applied with a different assignment plan")
        problems = sum((assignment_issues(actors, r, True) for r in rows), [])
        if problems:
            for p in problems[:30]:
                unreal.log_error("GARRISON PAINT: revert conflict: " + p)
            fail("REVERT REFUSED: %d conflict(s); nothing was changed" % len(problems))
        originals = {}
        for r in rows:
            originals[r["from"]] = originals.get(r["from"]) or unreal.EditorAssetLibrary.load_asset(r["from"])
        for r in rows:
            component_of(actors[r["actor_key"]], r["component"]).set_material(r["slot"], originals[r["from"]])
        bad = sum((assignment_issues(actors, r, False) for r in rows), [])
        if bad:
            for b in bad[:30]:
                unreal.log_error("GARRISON PAINT: " + b)
            fail("the revert did not verify (%d issue(s)); NOT saved" % len(bad))
        after = save_target()
        rec["history"].append({"state": "reverted", "sha256": after, "assignments_sha256": asg_sha,
                               "material_sha256": m["sha256"], "restored": len(rows), "utc": now(),
                               "by": "ib_garrison_paint_correction.py revert"})
        write_json(receipt_file(TARGET), rec)
        REPORT.update({"result": "reverted-verified", "saved": True, "sha256": after, "restored": len(rows)})
        return
    if last.get("state") == "applied":
        if last.get("assignments_sha256") != asg_sha:
            fail("the target was applied with a different assignment plan")
        problems = sum((assignment_issues(actors, r, True) for r in rows), [])
        if problems:
            fail("the receipt says applied but %d assignment(s) differ; nothing changed" % len(problems))
        REPORT.update({"result": "already-applied-verified", "saved": False, "sha256": last["sha256"]})
        return
    if last.get("state") not in ("created", "reverted"):
        fail("cannot apply from state %s" % last.get("state"))
    if data.get("target_sha256_at_plan") not in [h["sha256"] for h in rec["history"] if h["state"] in ("created", "reverted")]:
        fail("assignments.json was planned on a state this receipt does not record as clean")
    problems = sum((assignment_issues(actors, r, False) for r in rows), [])
    if problems:
        for p in problems[:30]:
            unreal.log_error("GARRISON PAINT: " + p)
        fail("preflight found %d problem(s); NOTHING was changed" % len(problems))
    mi = load_mi()
    for r in rows:
        component_of(actors[r["actor_key"]], r["component"]).set_material(r["slot"], mi)
    bad = sum((assignment_issues(actors, r, True) for r in rows), [])
    if bad:
        for b in bad[:30]:
            unreal.log_error("GARRISON PAINT: " + b)
        fail("%d issue(s) after assigning; NOT saved (a commandlet discards the level on exit)" % len(bad))
    after = save_target()
    rec["history"].append({"state": "applied", "sha256": after, "assignments_sha256": asg_sha,
                           "material_sha256": m["sha256"], "assignments": len(rows), "utc": now(),
                           "by": "ib_garrison_paint_correction.py apply"})
    write_json(receipt_file(TARGET), rec)
    REPORT.update({"result": "applied-verified", "saved": True, "sha256": after, "assigned": len(rows)})


def stage_verify():
    guard_names(need_mi=True)
    rec = read_receipt(TARGET)
    last = target_state(rec)
    m = material_state(rec)
    data, asg_sha = read_assignments()
    f = mi_facts(load_mi())
    REPORT["material_facts"] = f
    issues = ["material instance: " + i for i in mi_issues(f)]
    if sha(umap(BASE)) != rec["source_sha256"]:
        issues.append("the base changed since the copy")
    applied = last.get("state") == "applied"
    if applied and last.get("assignments_sha256") != asg_sha:
        issues.append("the applied state used a different assignment plan")
    bfp = read_base_fp()
    load(TARGET)
    actors = live_actors(TARGET)
    slot_issues = sum((assignment_issues(actors, r, applied) for r in data["assignments"]), [])
    tfp = fingerprint(TARGET)
    unreal.SystemLibrary.collect_garbage()
    cmp_ = compare(bfp, tfp, data["assignments"], applied)
    cmp_["editor_only_components_skipped_in_target"] = EDITOR_ONLY["count"]
    REPORT.update({"state": last.get("state"), "target_sha256": last["sha256"], "assignments": len(data["assignments"]),
                   "assignment_issues": slot_issues[:30], "comparison": cmp_, "material_sha256": m["sha256"]})
    issues += slot_issues
    if cmp_["unexpected_count"] or cmp_["expected_slot_changes_missing"]:
        issues.append("comparison with the base: %d unexpected, %d expected changes missing"
                      % (cmp_["unexpected_count"], cmp_["expected_slot_changes_missing"]))
    if sha(umap(TARGET)) != last["sha256"]:
        issues.append("the target changed while it was being verified")
    REPORT["issues"] = issues
    if issues:
        fail("verify found %d issue(s): %s" % (len(issues), "; ".join(issues[:4])))
    REPORT["result"] = "verified"


STAGES = {"smoke": stage_smoke, "base-fingerprint": stage_base_fingerprint, "copy": stage_copy,
          "copy-verify": stage_copy_verify, "material": stage_material,
          "plan": stage_plan, "apply": stage_apply, "revert": lambda: stage_apply(revert=True), "verify": stage_verify}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if STAGE not in STAGES:
        fail("IB_GARRISON_PAINT_STAGE must be one of %s" % ", ".join(STAGES))
    live0 = sha(umap(LIVE))
    STAGES[STAGE]()
    if sha(umap(LIVE)) != live0:
        fail("THE LIVE MAP CHANGED during this stage")
    REPORT["live_sha256"] = live0
    REPORT["status"] = "complete"


try:
    main()
except Exception:
    REPORT["status"] = "failed"
    REPORT["error"] = traceback.format_exc()[-1500:]
    unreal.log_error("GARRISON PAINT FAILED\n" + traceback.format_exc())
    raise
finally:
    REPORT["finished_utc"] = now()
    try:
        write_json(OUT / ("paint_%s.json" % (STAGE or "none")), REPORT)
    except Exception:
        pass
