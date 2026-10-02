"""Focused lifecycle tests on the DISPOSABLE garrison preview map. Never the source map.

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script="Scripts/ib_garrison_preview_tests.py"

IB_GARRISON_TEST selects one test:

  external-edit     loads the preview, nudges an unrelated actor (Water_Placeholder,
                    +1 cm z) and SAVES the preview: an edit made outside the layout
                    tool. The next layout run on it must refuse.
  revert-conflict   loads the (applied) preview, moves SM_Truck_Cargo3 by +10 m IN
                    MEMORY, runs the layout revert in this same process, and checks
                    that the revert refuses and that nothing else changed. Never saves.
  session-roundtrip loads the (clean) preview, runs layout apply (no save) and then
                    layout revert (no save) and layout verify in this process; the
                    level must end exactly clean. Never saves.

Environment: IB_GARRISON_TEST, IB_GARRISON_TARGET_LEVEL, IB_GARRISON_PLAN,
IB_GARRISON_OUT (results: test_<name>.json).
"""
import unreal, json, os, runpy, hashlib, datetime, traceback
from pathlib import Path

PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
SOURCE = "/Game/LevelPrototyping/CarrowGateGarrison"
TEST = os.environ.get("IB_GARRISON_TEST", "")
TARGET = (os.environ.get("IB_GARRISON_TARGET_LEVEL") or "").strip().rstrip("/")
PROJECT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = Path(os.environ.get("IB_GARRISON_OUT") or str(PROJECT / "Saved/GarrisonRestructure/preview/tests"))
LAYOUT = str(PROJECT / "Scripts/ib_layout_garrison.py")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LAYOUT_ENV = ("IB_GARRISON_APPLY", "IB_GARRISON_SAVE", "IB_GARRISON_REVERT", "IB_GARRISON_VERIFY")


def log(m):
    unreal.log("GARRISON PREVIEW TEST: " + str(m))


def sha(path):
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def umap(pkg):
    return PROJECT / "Content" / (pkg[len("/Game/"):] + ".umap")


def world_package():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    return w.get_path_name().split(".")[0] if w else None


def by_label(label):
    found = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == label]
    if len(found) != 1:
        raise RuntimeError("%d actors labelled %s" % (len(found), label))
    return found[0]


def fingerprint():
    """Everything a refused operation must leave untouched."""
    rows = {}
    for a in EAS.get_all_level_actors():
        l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
        entry = [a.get_actor_label(), round(l.x, 2), round(l.y, 2), round(l.z, 2), round(r.roll, 3),
                 round(r.pitch, 3), round(r.yaw, 3), round(s.x, 5), round(s.y, 5), round(s.z, 5)]
        if isinstance(a, unreal.StaticMeshActor):
            smc = a.static_mesh_component
            entry += [bool(smc.is_visible()), str(smc.get_collision_enabled()), bool(a.get_actor_enable_collision())]
        rows[a.get_path_name()] = entry
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest().upper(), len(rows)


def run_layout(**env):
    for k in LAYOUT_ENV:
        os.environ.pop(k, None)
    os.environ.update({k: str(v) for k, v in env.items()})
    try:
        runpy.run_path(LAYOUT, run_name="__main__")
        return "ok", None
    except Exception as error:
        return "raised", str(error).strip().splitlines()[-1][:400]
    finally:
        for k in LAYOUT_ENV:
            os.environ.pop(k, None)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"test": TEST, "target": TARGET, "started_utc": datetime.datetime.utcnow().isoformat() + "Z",
           "source_sha256_before": sha(umap(SOURCE)), "target_sha256_before": sha(umap(TARGET))}
    if not TARGET.startswith(PREVIEW_ROOT):
        raise RuntimeError("tests run only on a map under %s" % PREVIEW_ROOT)
    unreal.EditorLoadingAndSavingUtils.load_map(TARGET)
    if world_package() != TARGET:
        raise RuntimeError("could not load %s" % TARGET)
    if TEST == "external-edit":
        a = by_label("Water_Placeholder")
        l = a.get_actor_location()
        a.set_actor_location(unreal.Vector(l.x, l.y, l.z + 1.0), False, False)
        if world_package() != TARGET or not TARGET.startswith(PREVIEW_ROOT):
            raise RuntimeError("refusing to save anything but the preview")
        ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        res.update({"edited": "Water_Placeholder z +1 cm", "saved": bool(ok)})
        res["pass"] = bool(ok)
    elif TEST == "revert-conflict":
        truck = by_label("SM_Truck_Cargo3")
        l = truck.get_actor_location()
        truck.set_actor_location(unreal.Vector(l.x + 1000.0, l.y, l.z), False, False)
        before, n = fingerprint()
        outcome, message = run_layout(IB_GARRISON_APPLY="1", IB_GARRISON_REVERT="1")
        after, n2 = fingerprint()
        res.update({"nudged": "SM_Truck_Cargo3 x +1000 cm in memory", "layout": outcome, "message": message,
                    "fingerprint_before": before, "fingerprint_after": after, "actors": [n, n2],
                    "unchanged": before == after})
        res["pass"] = outcome == "raised" and "REVERT REFUSED" in (message or "") and before == after
    elif TEST == "session-roundtrip":
        before, n = fingerprint()
        a1 = run_layout(IB_GARRISON_APPLY="1")
        mid, n_mid = fingerprint()
        a2 = run_layout(IB_GARRISON_APPLY="1", IB_GARRISON_REVERT="1")
        a3 = run_layout(IB_GARRISON_VERIFY="1")
        after, n2 = fingerprint()
        res.update({"apply": a1, "revert": a2, "verify": a3, "fingerprint_before": before,
                    "fingerprint_applied": mid, "fingerprint_after": after, "actors": [n, n_mid, n2],
                    "restored_exactly": before == after})
        res["pass"] = a1[0] == "ok" and a2[0] == "ok" and a3[0] == "ok" and before == after and mid != before
    else:
        raise RuntimeError("unknown IB_GARRISON_TEST %r" % TEST)
    res["target_sha256_after"] = sha(umap(TARGET))
    res["source_sha256_after"] = sha(umap(SOURCE))
    res["source_unchanged"] = res["source_sha256_after"] == res["source_sha256_before"]
    res["pass"] = bool(res.get("pass")) and res["source_unchanged"]
    res["finished_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    (OUT / ("test_%s.json" % TEST)).write_bytes(json.dumps(res, indent=1).encode("utf-8"))
    log("%s: %s" % (TEST, "PASS" if res["pass"] else "FAIL"))


try:
    main()
except Exception:
    unreal.log_error("GARRISON PREVIEW TEST FAILED\n" + traceback.format_exc())
    raise
