"""READ-ONLY identity audit of the building assemblies the P3 composition would move.

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script="Scripts/ib_garrison_assembly_audit.py"

Loads the SOURCE map (never saves anything) and, for Command, Mess_Hall and their
door frames -- found by object path, then checked by label and class -- records:

  * what each actor consists of: every component (class, relative transform,
    collision, mesh / child-actor class), so hidden sub-parts are seen;
  * attachment in both directions (attach parent, attached actors);
  * every other actor whose world bounds overlap the building's bounds (+50 cm),
    including hidden actors, volumes, lights, triggers and spawn points;
  * every property of every other actor in the level that references one of the
    four, found in a T3D export of the level's actors (object paths are text there);
  * the door actors' own exported properties (linked actors, stored positions);
  * everything standing inside the provisional rear reserve and on the control
    platform, so the candidate's claims about "clear" space are evidence-based.

Writes <OUT>/audit.json and <OUT>/actors.t3d. The source map file hash is
recorded before and after; a change fails the run.

Environment: IB_GARRISON_OUT (default Saved/GarrisonRestructure/20260930-claude-composition/audit)
             IB_GARRISON_AUDIT_SET  "assemblies" (default: the two P3 building assemblies) or "pier" (the
                                    dock crane and the four cargo trucks the pier-finish candidate may move,
                                    plus the berthed ship for context): each is audited as a single actor
"""
import unreal, json, os, re, hashlib, datetime, traceback
from pathlib import Path

SOURCE = "/Game/LevelPrototyping/CarrowGateGarrison"
PREFIX = SOURCE + ".CarrowGateGarrison:PersistentLevel."
PROJECT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
MAP_FILE = PROJECT / "Content/LevelPrototyping/CarrowGateGarrison.umap"
OUT = Path(os.environ.get("IB_GARRISON_OUT") or
           str(PROJECT / "Saved/GarrisonRestructure/20260930-claude-composition/audit"))
AUDIT_SET = (os.environ.get("IB_GARRISON_AUDIT_SET") or "assemblies").strip().lower()
if AUDIT_SET == "pier":
    TARGETS = {  # label -> (object name, class)
        "Docks_Crane_01": ("StaticMeshActor_138", "StaticMeshActor"),
        "SM_Truck_Cargo": ("StaticMeshActor_62", "StaticMeshActor"),
        "SM_Truck_Cargo2": ("StaticMeshActor_64", "StaticMeshActor"),
        "SM_Truck_Cargo3": ("StaticMeshActor_66", "StaticMeshActor"),
        "SM_Truck_Cargo4": ("StaticMeshActor_68", "StaticMeshActor"),
        "Docks_Ship_Hull": ("StaticMeshActor_137", "StaticMeshActor"),
    }
    ASSEMBLY = {label: [label] for label in TARGETS}
    ZONES = {"pier (planned deck)": (10182.0, 18600.0, -1275.0, 925.0)}
else:
    TARGETS = {  # label -> (object name, class)
        "Command": ("StaticMeshActor_58", "StaticMeshActor"),
        "Command_DoorFrame": ("BP_DoorFrame_C_3", "BP_DoorFrame_C"),
        "Mess_Hall": ("StaticMeshActor_60", "StaticMeshActor"),
        "Mess_Hall_DoorFrame": ("BP_DoorFrame_C_4", "BP_DoorFrame_C"),
    }
    ASSEMBLY = {"Command": ["Command", "Command_DoorFrame"], "Mess_Hall": ["Mess_Hall", "Mess_Hall_DoorFrame"]}
    ZONES = {  # x0, x1, y0, y1 (world cm): what already stands there
        "provisional rear reserve": (-500.0, 4390.0, 1819.4, 5680.6),
        "control platform": (11082.0, 14532.0, 5675.0, 10275.0),
    }
BIG = 20000.0          # actors wider than this (cm half-extent) are background: listed, never "inside"
GROUND = {  # structural actors every building stands on or near: reported as ground, not assembly members
    PREFIX + "StaticMeshActor_167": "GarrisonPlatform_New (the old platform slab the buildings stand on)",
}
R = {"tool": "ib_garrison_assembly_audit", "source": SOURCE, "set": AUDIT_SET,
     "started_utc": datetime.datetime.utcnow().isoformat() + "Z", "errors": []}


def log(m):
    unreal.log("GARRISON ASSEMBLY AUDIT: " + str(m))


def sha(p):
    h = hashlib.sha256()
    with open(str(p), "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest().upper()


def v3(v):
    return [round(v.x, 2), round(v.y, 2), round(v.z, 2)]


def rot(r):
    return {"roll": round(r.roll, 4), "pitch": round(r.pitch, 4), "yaw": round(r.yaw, 4)}


def enum(v):
    s = str(v)
    return s.split(".")[-1].split(":")[0].strip("<> ") if s.startswith("<") else s


def bounds(a):
    o, e = a.get_actor_bounds(False)
    return v3(o), v3(e)


def overlap(o1, e1, o2, e2, pad=0.0):
    return all(abs(o1[i] - o2[i]) <= e1[i] + e2[i] + pad for i in range(3))


def components(a):
    out = []
    for c in a.get_components_by_class(unreal.ActorComponent):
        row = {"name": c.get_name(), "class": c.get_class().get_name()}
        if isinstance(c, unreal.SceneComponent):
            try:
                row["relative_location"] = v3(c.get_editor_property("relative_location"))
                row["relative_rotation"] = rot(c.get_editor_property("relative_rotation"))
                row["relative_scale"] = v3(c.get_editor_property("relative_scale3d"))
                p = c.get_attach_parent()
                row["attach_parent"] = p.get_name() if p else None
                row["visible"] = bool(c.is_visible())
            except Exception as error:
                row["scene_error"] = str(error)[:160]
        if isinstance(c, unreal.PrimitiveComponent):
            try:
                row["collision_enabled"] = enum(c.get_collision_enabled())
                row["collision_profile"] = str(c.get_collision_profile_name())
            except Exception as error:
                row["collision_error"] = str(error)[:160]
        if isinstance(c, unreal.StaticMeshComponent):
            m = c.static_mesh
            row["mesh"] = m.get_path_name() if m else None
        if isinstance(c, unreal.ChildActorComponent):
            try:
                cls = c.get_editor_property("child_actor_class")
                row["child_actor_class"] = cls.get_path_name() if cls else None
                ch = c.get_editor_property("child_actor")
                row["child_actor"] = ch.get_path_name() if ch else None
            except Exception as error:
                row["child_error"] = str(error)[:160]
        out.append(row)
    return out


def export_t3d(world, path):
    """T3D of the whole level. (A selected-only export came out empty in a commandlet:
    the editor selection does not reach the exporter there. This level has no
    landscape, so the full export stays small.)"""
    task = unreal.AssetExportTask()
    task.object = world
    task.filename = str(path)
    task.selected = False
    task.replace_identical = True
    task.prompt = False
    task.automated = True
    ok = unreal.Exporter.run_asset_export_task(task)
    return bool(ok) and path.is_file()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = sha(MAP_FILE)
    R["source_sha256_before"] = before
    unreal.EditorLoadingAndSavingUtils.load_map(SOURCE)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if world.get_path_name().split(".")[0] != SOURCE:
        raise RuntimeError("loaded %s, not %s" % (world.get_path_name(), SOURCE))
    actors = list(unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors())
    by_path = {a.get_path_name(): a for a in actors}
    R["actors_in_level"] = len(actors)
    info = {}
    idx = []
    for a in actors:
        try:
            o, e = bounds(a)
        except Exception:
            o, e = [0, 0, 0], [0, 0, 0]
        par = a.get_attach_parent_actor()
        idx.append({"path": a.get_path_name(), "name": a.get_name(), "label": a.get_actor_label(),
                    "class": a.get_class().get_name(), "origin": o, "extent": e,
                    "hidden": bool(a.is_hidden_ed()) if hasattr(a, "is_hidden_ed") else None,
                    "attach_parent": par.get_path_name() if par else None})
    # -- the four actors, by identity ------------------------------------------------
    for label, (name, cls) in TARGETS.items():
        a = by_path.get(PREFIX + name)
        row = {"path": PREFIX + name, "found": a is not None}
        if a is None:
            R["errors"].append({"what": "missing", "detail": "%s (%s) not found" % (label, PREFIX + name)})
            info[label] = row
            continue
        row.update({"label": a.get_actor_label(), "class": a.get_class().get_name(),
                    "label_matches": a.get_actor_label() == label, "class_matches": a.get_class().get_name() == cls,
                    "location": v3(a.get_actor_location()), "rotation": rot(a.get_actor_rotation()),
                    "scale": v3(a.get_actor_scale3d()), "actor_collision": bool(a.get_actor_enable_collision()),
                    "components": components(a)})
        o, e = bounds(a)
        row["bounds"] = {"origin": o, "extent": e}
        par = a.get_attach_parent_actor()
        row["attach_parent"] = par.get_path_name() if par else None
        row["attached_actors"] = [c.get_path_name() for c in a.get_attached_actors()]
        info[label] = row
    R["targets"] = info
    # -- overlap: everything whose bounds touch each building's bounds (+50 cm) ----
    over = {}
    for bl, members in ASSEMBLY.items():
        b = info.get(bl) or {}
        if not b.get("found"):
            continue
        o, e = b["bounds"]["origin"], b["bounds"]["extent"]
        mine = set(info[m]["path"] for m in members if info.get(m, {}).get("found"))
        hits, background = [], []
        for r in idx:
            if r["path"] in mine:
                continue
            if max(r["extent"][:2]) > BIG or r["path"] in GROUND:
                if overlap(o, e, r["origin"], r["extent"]):
                    background.append(GROUND.get(r["path"]) or "%s (%s)" % (r["label"], r["class"]))
                continue
            if max(r["extent"]) <= 0.0:
                # zero-size actors (spawn points, directors, notes): inside test on their origin
                inside = all(abs(r["origin"][i] - o[i]) <= e[i] + 50.0 for i in range(3))
            else:
                inside = overlap(o, e, r["origin"], r["extent"], 50.0)
            if inside or r["attach_parent"] in mine:
                hits.append(r)
        over[bl] = {"bounds": b["bounds"], "overlapping_actors": hits, "background_actors": background}
    R["overlap"] = over
    # -- what stands in the reserve and on the control platform ------------------------
    zones = {}
    for zn, (x0, x1, y0, y1) in ZONES.items():
        rows = []
        for r in idx:
            if max(r["extent"][:2]) > BIG or r["class"] in ("WorldSettings", "Brush"):
                continue
            o, e = r["origin"], r["extent"]
            if o[0] + e[0] > x0 and o[0] - e[0] < x1 and o[1] + e[1] > y0 and o[1] - e[1] < y1 and o[2] + e[2] > 300:
                rows.append({k: r[k] for k in ("label", "class", "path", "origin", "extent", "hidden")})
        zones[zn] = rows
    R["zones"] = zones
    # -- references by identity: T3D of every actor except background/landscape --------
    t3d = OUT / "level.t3d"
    refs = {}
    try:
        ok = export_t3d(world, t3d)
        text_all = t3d.read_text(encoding="utf-8", errors="replace") if ok else ""
        R["t3d"] = {"file": str(t3d), "ok": ok, "bytes": t3d.stat().st_size if t3d.is_file() else 0,
                    "actor_blocks": text_all.count("Begin Actor ")}
        if ok and R["t3d"]["actor_blocks"] < len(actors) - 5:
            R["errors"].append({"what": "t3d incomplete", "detail": "%d actor blocks for %d actors"
                                % (R["t3d"]["actor_blocks"], len(actors))})
        if ok:
            text = text_all.splitlines()
            # Actor blocks sit inside Map/Level blocks: track the depth at which each
            # "Begin Actor" opened and close it on the matching "End".
            depth, owner, owner_depth = 0, None, None
            blocks = {}
            names = [n for n, _ in TARGETS.values()]
            # A reference may be a full path (...PersistentLevel.X) or a bare object name.
            pats = {lab: re.compile(r"(?<![0-9A-Za-z_])%s(?![0-9A-Za-z_])" % re.escape(n))
                    for lab, (n, _) in TARGETS.items()}
            for i, line in enumerate(text):
                s = line.strip()
                if s.startswith("Begin "):
                    if s.startswith("Begin Actor") and owner is None:
                        m = re.search(r'Name="?([^" ]+)', s)
                        owner, owner_depth = (m.group(1) if m else "?"), depth
                    depth += 1
                if owner in names:
                    blocks.setdefault(owner, []).append(line)
                for lab, p in pats.items():
                    if owner != TARGETS[lab][0] and p.search(line):
                        refs.setdefault(lab, []).append({"line": i + 1, "in_actor": owner, "text": s[:300]})
                if s.startswith("End "):
                    depth -= 1
                    if owner is not None and depth == owner_depth:
                        owner, owner_depth = None, None
            if AUDIT_SET == "pier":
                R["target_blocks"] = {lab: blocks.get(TARGETS[lab][0], [])[:120] for lab in TARGETS}
            else:
                R["door_blocks"] = {lab: blocks.get(TARGETS[lab][0], [])[:400] for lab in ("Command_DoorFrame",
                                                                                           "Mess_Hall_DoorFrame")}
            # Gameplay actors that could hold a building/door reference or a stored position.
            dirs = {}
            cur, keep = None, False
            for line in text:
                s2 = line.strip()
                m = re.match(r"Begin Actor Class=(\S+) Name=\"?([^\" ]+)", s2)
                if m:
                    keep = any(k in m.group(1) for k in ("Director", "Spawner", "BP_WeaponRack", "PlayerStart",
                                                        "LevelScriptActor", "GameMode"))
                    cur = m.group(2) if keep else None
                if keep and cur:
                    dirs.setdefault(cur, []).append(s2[:240])
                if s2.startswith("End Actor"):
                    keep, cur = False, None
            R["gameplay_actor_blocks"] = {k: v[:80] for k, v in dirs.items()}
            if AUDIT_SET != "pier":
                R["building_blocks"] = {lab: blocks.get(TARGETS[lab][0], [])[:120] for lab in ("Command", "Mess_Hall")}
    except Exception:
        R["errors"].append({"what": "t3d export", "detail": traceback.format_exc()[-600:]})
    R["references_from_other_actors"] = refs
    # -- the level script actor (level blueprint), best effort ---------------------------
    lsa = [a for a in actors if isinstance(a, unreal.LevelScriptActor)]
    R["level_script_actor"] = [{"path": a.get_path_name(), "class": a.get_class().get_path_name()} for a in lsa]
    after = sha(MAP_FILE)
    R["source_sha256_after"] = after
    if after != before:
        raise RuntimeError("THE SOURCE MAP FILE CHANGED during a read-only audit")
    # -- verdict per assembly ------------------------------------------------------------------
    verdict = {}
    for bl, members in ASSEMBLY.items():
        o = over.get(bl, {})
        extra = [r["label"] + " (" + r["class"] + ")" for r in o.get("overlapping_actors", [])]
        attached = [p for m in members for p in (info.get(m) or {}).get("attached_actors", [])]
        parents = [(info.get(m) or {}).get("attach_parent") for m in members if (info.get(m) or {}).get("attach_parent")]
        rf = {m: refs.get(m, []) for m in members}
        verdict[bl] = {"members": members, "other_actors_overlapping": extra, "attached_children": attached,
                       "attach_parents": parents,
                       "referenced_by_other_actors": {m: sorted(set(x["in_actor"] or "?" for x in v)) for m, v in rf.items()}}
        if AUDIT_SET == "pier":
            # A single prop: attachment and references decide whether it is standalone. Overlapping
            # bounds are listed for review (at their source spots on the old apron the props' world
            # boxes overlap each other and the 45-degree ship), not counted as membership.
            verdict[bl]["standalone_prop"] = not attached and not parents and not any(rf.values())
        else:
            verdict[bl]["complete_two_actor_assembly"] = (not extra and not attached and not parents
                                                          and not any(rf.values()))
    R["verdict"] = verdict
    R["finished_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    R["status"] = "complete"


try:
    main()
except Exception:
    R["status"] = "failed"
    R["errors"].append({"what": "run", "detail": traceback.format_exc()[-1500:]})
    unreal.log_error("GARRISON ASSEMBLY AUDIT FAILED\n" + traceback.format_exc())
finally:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "audit.json").write_bytes(json.dumps(R, indent=1).encode("utf-8"))
    log("%s -> %s" % (R.get("status"), OUT / "audit.json"))
