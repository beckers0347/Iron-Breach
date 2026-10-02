"""READ-ONLY: compare a disposable garrison candidate with its source map, actor for actor.

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script="Scripts/ib_garrison_candidate_diff.py"

Environment:
    IB_GARRISON_PLAN          the plan.json the candidate was applied with
    IB_GARRISON_TARGET_LEVEL  the candidate package (must be under /Game/_GarrisonPreview_Disposable/)
    IB_GARRISON_OUT           folder for candidate_diff.json

Loads the source map, then the candidate, and never saves either. Every actor is
recorded by object name: label, class, location, rotation, scale, hidden flag,
actor collision, root component collision profile/state/visibility, static mesh,
attach parent, tags and outliner folder. Each difference is classified against
the plan:
  - a planned move is expected only when the actor sits at the plan's target
    transform (0.5 cm / 0.05 deg, the layout tool's tolerances) and nothing else
    about it changed;
  - the planned platform treatment is expected only for its four treated flags,
    at their treated values (plus the collision profile name becoming "Custom",
    which the engine does whenever collision is set on a preset profile);
  - an actor that exists only in the candidate is expected only when it carries
    the run tag, a planned piece label and the run folder;
  - anything else is UNEXPECTED and listed.
Both map files must be byte-identical before and after the run.
"""
import unreal, json, os, hashlib, datetime, math, traceback
from pathlib import Path

SOURCE = "/Game/LevelPrototyping/CarrowGateGarrison"
PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
PROJECT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
PLAN = os.environ.get("IB_GARRISON_PLAN")
TARGET = (os.environ.get("IB_GARRISON_TARGET_LEVEL") or "").strip().rstrip("/")
OUT = Path(os.environ.get("IB_GARRISON_OUT") or str(PROJECT / "Saved/GarrisonRestructure/diff"))
LOC_TOL, ROT_TOL = 0.5, 0.05
TREATED = {"visible": False, "hidden": True, "collision_enabled": "NO_COLLISION", "actor_collision": False}


def log(m):
    unreal.log("GARRISON DIFF: " + str(m))


def fail(m):
    raise RuntimeError("GARRISON DIFF REFUSED: " + str(m))


def umap(pkg):
    return PROJECT / "Content" / (pkg[len("/Game/"):] + ".umap")


def sha(path):
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def enum_name(v):
    s = str(v).strip()
    if s.startswith("<") and ":" in s:
        s = s[1:].split(":")[0]
    return s.split(".")[-1].strip("<> ")


def world_package():
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    except Exception:
        w = unreal.EditorLevelLibrary.get_editor_world()
    return w.get_path_name().split(".")[0] if w else None


def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def record(a):
    l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    rc = safe(lambda: a.get_editor_property("root_component"))
    rec = {"label": a.get_actor_label(), "class": a.get_class().get_name(),
           "loc": [round(l.x, 2), round(l.y, 2), round(l.z, 2)],
           "rot": [round(r.roll, 3), round(r.pitch, 3), round(r.yaw, 3)],
           "scale": [round(s.x, 4), round(s.y, 4), round(s.z, 4)],
           "hidden": safe(lambda: bool(a.get_editor_property("hidden"))),
           "actor_collision": safe(lambda: bool(a.get_actor_enable_collision())),
           "root_class": safe(lambda: rc.get_class().get_name()) if rc else None,
           "visible": safe(lambda: bool(rc.is_visible())) if rc else None,
           "profile": None, "collision_enabled": None, "mesh": None,
           "attach_parent": None, "tags": sorted(str(t) for t in (safe(lambda: a.get_editor_property("tags")) or [])),
           "folder": safe(lambda: str(a.get_folder_path()), "")}
    if rc is not None and isinstance(rc, unreal.PrimitiveComponent):
        rec["profile"] = safe(lambda: str(rc.get_collision_profile_name()))
        rec["collision_enabled"] = safe(lambda: enum_name(rc.get_collision_enabled()))
    smc = safe(lambda: a.static_mesh_component)
    if smc is not None:
        m = safe(lambda: smc.get_editor_property("static_mesh"))
        rec["mesh"] = m.get_path_name() if m else None
    p = safe(lambda: a.get_attach_parent_actor())
    if p is not None:
        rec["attach_parent"] = p.get_path_name().split("PersistentLevel.")[-1]
    return rec


def snapshot(pkg):
    unreal.EditorLoadingAndSavingUtils.load_map(pkg)
    if world_package() != pkg:
        fail("loading %s left %s loaded" % (pkg, world_package()))
    prefix = "%s.%s:PersistentLevel." % (pkg, pkg.split("/")[-1])
    out = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        path = a.get_path_name()
        if path.startswith(prefix):
            out[path[len(prefix):]] = record(a)
    a = None
    unreal.SystemLibrary.collect_garbage()
    return out


def rot_axes(roll, pitch, yaw):
    p, y, ro = math.radians(pitch), math.radians(yaw), math.radians(roll)
    cp, sp, cy, sy, cr, sr = math.cos(p), math.sin(p), math.cos(y), math.sin(y), math.cos(ro), math.sin(ro)
    return ((cp * cy, cp * sy, sp),
            (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp),
            (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp))


def rot_close(a, b):
    A, B = rot_axes(*a), rot_axes(*b)
    c = math.cos(math.radians(ROT_TOL))
    return all(sum(A[i][k] * B[i][k] for k in range(3)) >= c - 1e-12 for i in range(3))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.utcnow().isoformat() + "Z"
    if not TARGET.startswith(PREVIEW_ROOT) or TARGET == SOURCE:
        fail("IB_GARRISON_TARGET_LEVEL must be a candidate under %s, got %r" % (PREVIEW_ROOT, TARGET))
    if not PLAN or not Path(PLAN).is_file():
        fail("IB_GARRISON_PLAN must name the plan.json the candidate was applied with")
    plan = json.loads(Path(PLAN).read_text(encoding="utf-8"))
    src_file, tgt_file = umap(SOURCE), umap(TARGET)
    src0, tgt0 = sha(src_file), sha(tgt_file)
    obj = lambda identity: identity.split("PersistentLevel.")[-1]
    moves = {obj(m["identity"]): m for m in plan.get("moves", [])}
    plat = plan.get("platform_treatment") or {}
    plat_obj = obj(plat["identity"]) if plat.get("identity") else None
    pieces = {p["label"]: p for p in plan.get("pieces", [])}
    run_tag, run_folder = plan.get("run_tag"), plan.get("run_folder")

    src = snapshot(SOURCE)
    tgt = snapshot(TARGET)

    unexpected, expected_moves, expected_platform, identical = [], [], [], 0
    for k in sorted(src):
        if k not in tgt:
            unexpected.append({"actor": k, "label": src[k]["label"], "issue": "missing in the candidate"})
            continue
        a, b = src[k], tgt[k]
        changed = sorted(f for f in a if a[f] != b[f])
        if not changed:
            identical += 1
            continue
        if k in moves:
            m, bad = moves[k], []
            if not all(abs(b["loc"][i] - m["to"]["loc"][i]) <= LOC_TOL for i in range(3)):
                bad.append("location %s, planned %s" % (b["loc"], m["to"]["loc"]))
            to_r = m["to"]["rot"]
            if not rot_close(b["rot"], (to_r["roll"], to_r["pitch"], to_r["yaw"])):
                bad.append("rotation %s, planned %s" % (b["rot"], to_r))
            bad += ["%s changed %r -> %r" % (f, a[f], b[f]) for f in changed if f not in ("loc", "rot")]
            row = {"actor": k, "label": b["label"], "role": m.get("role"), "from": {"loc": a["loc"], "rot": a["rot"]},
                   "now": {"loc": b["loc"], "rot": b["rot"]}, "planned": m["to"], "changed": changed}
            if bad:
                row["issue"] = "; ".join(bad)
                unexpected.append(row)
            else:
                expected_moves.append(row)
            continue
        if k == plat_obj:
            # set_collision_enabled on a preset profile renames it to the engine's "Custom" (the revert
            # restores the recorded profile first); any other profile change is unexpected
            bad = ["%s changed %r -> %r" % (f, a[f], b[f]) for f in changed
                   if f not in TREATED and not (f == "profile" and b[f] == "Custom")]
            bad += ["%s is %r, treated value %r" % (f, b[f], v) for f, v in TREATED.items() if b[f] != v]
            row = {"actor": k, "label": b["label"], "changed": changed, "before": {f: a[f] for f in TREATED},
                   "now": {f: b[f] for f in TREATED}}
            if bad:
                row["issue"] = "; ".join(bad)
                unexpected.append(row)
            else:
                expected_platform.append(row)
            continue
        unexpected.append({"actor": k, "label": b["label"], "issue": "changed: " + ", ".join(
            "%s %r -> %r" % (f, a[f], b[f]) for f in changed)})
    extra_expected = []
    for k in sorted(t for t in tgt if t not in src):
        b = tgt[k]
        ok = run_tag in b["tags"] and b["label"] in pieces and b["folder"] == run_folder
        if ok:
            p = pieces[b["label"]]
            ok = all(abs(b["loc"][i] - p["location"][i]) <= LOC_TOL for i in range(3)) and b["mesh"] == p["mesh"]
        (extra_expected if ok else unexpected).append(
            {"actor": k, "label": b["label"]} if ok else {"actor": k, "label": b["label"],
                                                          "issue": "only in the candidate and not a planned piece"})
    missing_pieces = sorted(set(pieces) - set(x["label"] for x in extra_expected))
    for lab in missing_pieces:
        unexpected.append({"actor": None, "label": lab, "issue": "planned piece not found in the candidate"})
    held = []
    for h in plan.get("held", []):
        k = obj(h["identity"])
        held.append({"label": h["label"], "actor": k, "in_both": k in src and k in tgt,
                     "identical": k in src and k in tgt and src[k] == tgt[k],
                     "loc": tgt.get(k, {}).get("loc"), "rot": tgt.get(k, {}).get("rot")})
    assemblies = {}
    for k, m in moves.items():
        if (m.get("role") or "").startswith("assembly"):
            assemblies[m["label"]] = {"actor": k, "attach_parent": tgt.get(k, {}).get("attach_parent"),
                                      "children_attached": sorted(x for x in tgt if tgt[x]["attach_parent"] == k)}
    src1, tgt1 = sha(src_file), sha(tgt_file)
    report = {"tool": "ib_garrison_candidate_diff", "kind": "engine, read-only: both maps loaded, neither saved",
              "source": SOURCE, "target": TARGET, "plan": PLAN, "plan_sha256": sha(PLAN),
              "source_sha256_before": src0, "source_sha256_after": src1,
              "target_sha256_before": tgt0, "target_sha256_after": tgt1,
              "files_unchanged": src0 == src1 and tgt0 == tgt1,
              "source_actors": len(src), "target_actors": len(tgt),
              "identical": identical, "expected_moves": len(expected_moves),
              "expected_platform": len(expected_platform), "expected_generated": len(extra_expected),
              "unexpected": len(unexpected), "unexpected_rows": unexpected[:200],
              "planned": {"moves": len(moves), "platform": 1 if plat_obj else 0, "pieces": len(pieces)},
              "moves": expected_moves, "platform": expected_platform, "held": held,
              "held_identical": sum(1 for h in held if h["identical"]), "held_total": len(held),
              "assemblies_in_candidate": assemblies,
              "fields": ["label", "class", "loc", "rot", "scale", "hidden", "actor_collision", "root_class", "visible",
                         "profile", "collision_enabled", "mesh", "attach_parent", "tags", "folder"],
              "started_utc": started, "finished_utc": datetime.datetime.utcnow().isoformat() + "Z"}
    (OUT / "candidate_diff.json").write_bytes(json.dumps(report, indent=1).encode("utf-8"))
    log("%s vs %s: %d/%d actors; identical %d; expected: %d moves, %d platform, %d generated; UNEXPECTED %d; "
        "held %d/%d identical; map files unchanged %s"
        % (TARGET, SOURCE, len(tgt), len(src), identical, len(expected_moves), len(expected_platform),
           len(extra_expected), len(unexpected), report["held_identical"], len(held), report["files_unchanged"]))
    if not report["files_unchanged"]:
        fail("a map file changed during a read-only comparison")


try:
    main()
except Exception:
    unreal.log_error("GARRISON DIFF FAILED\n" + traceback.format_exc())
    raise
