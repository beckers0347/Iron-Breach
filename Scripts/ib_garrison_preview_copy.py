"""Make a DISPOSABLE preview copy of the garrison map for layout lifecycle tests.

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script="Scripts/ib_garrison_preview_copy.py"   (stage copy)
    ...same with IB_GARRISON_COPY_STAGE=verify, in a NEW process                                 (stage verify)

Copies /Game/LevelPrototyping/CarrowGateGarrison to a clearly named package under
/Game/_GarrisonPreview_Disposable/ through the engine's own asset duplication (so
the world is renamed properly), saves ONLY that new package, checks that the
source map file is byte-identical before and after, checks that every actor of
the source exists in the copy under the same object name (so layout identities
can be remapped deliberately), and writes the copy's receipt:

    Saved/GarrisonRestructure/receipts/Game___GarrisonPreview_Disposable__<name>.json
    {"target_package", "source_package", "source_sha256", "history": [{"state": "created", "sha256", ...}]}

Scripts/ib_layout_garrison.py writes only maps that carry such a receipt.

Environment:
    IB_GARRISON_PREVIEW_LEVEL  target package
                               (default /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_CB1Preview3)
    IB_GARRISON_OUT            folder for preview_copy.json (default Saved/GarrisonRestructure/preview)

Refuses a target outside /Game/_GarrisonPreview_Disposable/, a target that
already exists, and the source map itself. Delete the whole
Content/_GarrisonPreview_Disposable/ folder when the review is over; it is not
for commit.
"""
import unreal, json, os, hashlib, datetime, traceback
from pathlib import Path

SOURCE = "/Game/LevelPrototyping/CarrowGateGarrison"
PREVIEW_ROOT = "/Game/_GarrisonPreview_Disposable/"
TARGET = (os.environ.get("IB_GARRISON_PREVIEW_LEVEL")
          or PREVIEW_ROOT + "CarrowGateGarrison_CB1Preview3").strip().rstrip("/")
PROJECT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = Path(os.environ.get("IB_GARRISON_OUT") or str(PROJECT / "Saved/GarrisonRestructure/preview"))
RECEIPTS = PROJECT / "Saved/GarrisonRestructure/receipts"


def log(m):
    unreal.log("GARRISON PREVIEW COPY: " + str(m))


def fail(m):
    raise RuntimeError("GARRISON PREVIEW COPY REFUSED: " + str(m))


def umap(pkg):
    return PROJECT / "Content" / (pkg[len("/Game/"):] + ".umap")


def sha(path):
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def world_package():
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    except Exception:
        w = unreal.EditorLevelLibrary.get_editor_world()
    return w.get_path_name().split(".")[0] if w else None


def snapshot(pkg):
    """Actors of a loaded map keyed by object name (the part after PersistentLevel.)."""
    unreal.EditorLoadingAndSavingUtils.load_map(pkg)
    if world_package() != pkg:
        fail("loading %s left %s loaded" % (pkg, world_package()))
    prefix = "%s.%s:PersistentLevel." % (pkg, pkg.split("/")[-1])
    out = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        path = a.get_path_name()
        if not path.startswith(prefix):
            continue
        l, r = a.get_actor_location(), a.get_actor_rotation()
        out[path[len(prefix):]] = (a.get_actor_label(), a.get_class().get_name(),
                                   (round(l.x, 2), round(l.y, 2), round(l.z, 2)),
                                   (round(r.roll, 3), round(r.pitch, 3), round(r.yaw, 3)))
    a = None
    unreal.SystemLibrary.collect_garbage()
    return out


STAGE = os.environ.get("IB_GARRISON_COPY_STAGE", "copy").lower()


def main():
    """Two stages in two processes. The duplicated world is a standalone asset that
    stays in memory, and the editor's map loader treats any extra world alive at
    load time as a leak and aborts ("World Memory Leaks") -- which is exactly how
    the first two attempts died. So the COPY stage only duplicates and saves, and
    the VERIFY stage (a fresh process) loads the source, then the copy, compares
    them actor for actor and only then writes the 'created' receipt."""
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"tool": "ib_garrison_preview_copy", "stage": STAGE, "source": SOURCE, "target": TARGET,
              "started_utc": datetime.datetime.utcnow().isoformat() + "Z"}
    if not TARGET.startswith(PREVIEW_ROOT) or TARGET == SOURCE:
        fail("the target must be a new package under %s" % PREVIEW_ROOT)
    receipt = RECEIPTS / (TARGET.strip("/").replace("/", "__") + ".json")
    pending = OUT / "preview_copy_pending.json"
    if STAGE == "copy":
        if umap(TARGET).exists() or unreal.EditorAssetLibrary.does_asset_exist(TARGET):
            fail("%s already exists; pick a new name (disposable previews are never overwritten)" % TARGET)
        if receipt.exists():
            fail("a receipt for %s already exists (%s) without its map; move it aside deliberately" % (TARGET, receipt))
        src_before = sha(umap(SOURCE))
        dup = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, TARGET)
        if dup is None:
            fail("duplicate_asset returned nothing for %s" % TARGET)
        saved = unreal.EditorAssetLibrary.save_asset(TARGET, only_if_is_dirty=False)
        dup = None
        if not saved or not umap(TARGET).is_file():
            fail("duplicated %s but could not save it" % TARGET)
        src_after = sha(umap(SOURCE))
        if src_after != src_before:
            fail("THE SOURCE MAP FILE CHANGED during the copy")
        report.update({"method": "EditorAssetLibrary.duplicate_asset + save_asset", "source_sha256": src_before,
                       "target_file": str(umap(TARGET)), "target_sha256": sha(umap(TARGET)), "status": "copied",
                       "next": "run again with IB_GARRISON_COPY_STAGE=verify (a new process)"})
        pending.write_bytes(json.dumps(report, indent=1).encode("utf-8"))
        log("COPIED %s (%s); verify it in a new process before use" % (TARGET, report["target_sha256"][:12]))
        return
    if STAGE != "verify":
        fail("IB_GARRISON_COPY_STAGE must be copy or verify")
    if receipt.exists():
        fail("%s already has a receipt; nothing to verify" % TARGET)
    if not pending.is_file():
        fail("no %s: only a copy made by the copy stage can be verified" % pending)
    pend = json.loads(pending.read_text(encoding="utf-8"))
    if pend.get("target") != TARGET:
        fail("the pending copy is %s, not %s" % (pend.get("target"), TARGET))
    tgt_sha, src_sha = sha(umap(TARGET)), sha(umap(SOURCE))
    if tgt_sha != pend.get("target_sha256"):
        fail("the copy changed since it was made (%s... != %s...)" % (tgt_sha[:12], str(pend.get("target_sha256"))[:12]))
    if src_sha != pend.get("source_sha256"):
        fail("the source map changed since the copy was made")
    src = snapshot(SOURCE)
    tgt = snapshot(TARGET)
    missing = sorted(k for k in src if k not in tgt)
    extra = sorted(k for k in tgt if k not in src)
    differ = sorted(k for k in src if k in tgt and src[k] != tgt[k])
    report.update({"source_actors": len(src), "target_actors": len(tgt), "missing_in_copy": missing[:20],
                   "extra_in_copy": extra[:20], "differing": differ[:20], "method": pend.get("method")})
    if missing or extra or differ:
        fail("the copy does not mirror the source actor for actor (%d missing, %d extra, %d differ)"
             % (len(missing), len(extra), len(differ)))
    if sha(umap(SOURCE)) != src_sha or sha(umap(TARGET)) != tgt_sha:
        fail("a map file changed while it was being verified")
    now = datetime.datetime.utcnow().isoformat() + "Z"
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    rec = {"target_package": TARGET, "target_file": str(umap(TARGET)), "source_package": SOURCE,
           "source_sha256": src_sha, "method": pend.get("method"), "disposable": True,
           "history": [{"state": "created", "sha256": tgt_sha, "utc": now, "by": "ib_garrison_preview_copy.py",
                        "actors": len(tgt), "verified_actor_for_actor": True}]}
    receipt.write_bytes(json.dumps(rec, indent=1).encode("utf-8"))
    report.update({"target_file": str(umap(TARGET)), "target_sha256": tgt_sha, "source_sha256": src_sha,
                   "receipt": str(receipt), "status": "complete", "finished_utc": now})
    (OUT / "preview_copy.json").write_bytes(json.dumps(report, indent=1).encode("utf-8"))
    log("VERIFIED %s: %d actors mirror %s actor for actor; receipt written" % (TARGET, len(tgt), SOURCE))


try:
    main()
except Exception:
    unreal.log_error("GARRISON PREVIEW COPY FAILED\n" + traceback.format_exc())
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "preview_copy_failed.txt").write_bytes(traceback.format_exc().encode("utf-8"))
    except Exception:
        pass
    raise
