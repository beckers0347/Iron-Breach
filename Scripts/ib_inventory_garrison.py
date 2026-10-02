"""Read-only Carrow Gate garrison inventory. Changes nothing and saves nothing.

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script="Scripts/ib_inventory_garrison.py"

Current-baseline revision (2026-09-30). The map Shane rebuilt on Sep 18
(fed25b7, SHA256 FAFFD601...) no longer has one authored folder per building:
the five Tripo service buildings carry NO folder, their five doors share
`Carrowgate Garrison/Doors`, and the main gate sits in the root folder. Grouping
by folder therefore drops every building and lumps five unrelated doors into one
"assembly". This version identifies garrison elements by EXPLICIT IDENTITY
(label AND mesh, resolved to one actor path) and associates each door by its own
explicit label, never by proximity or shared folder. Anything that cannot be
associated that way is reported as unresolved rather than guessed.

Also recorded, because the layout pass cannot be trusted without them:
  * the map file's SHA256, so a plan made against another map version refuses
  * attachment (parent and children) for every garrison-scope actor
  * components of Blueprint actors (doors, rack, spawner) with their collision
  * collision of every garrison-scope primitive through the supported getter
    METHODS (get_collision_enabled / _profile_name / _object_type) -- the
    editor-property names used before do not exist on StaticMeshComponent
  * each placed mesh's body-setup collision flag and complex_collision_mesh,
    which is where Shane's carved-doorway collision lives
  * the world-space upward faces of the ground actors (support_faces.json), so
    the platform's real terraces, ramps and edges can be read, not guessed
  * reference properties of mission actors, DISCOVERED from the actor instead of
    read from a fixed name list that does not match these classes
  * a tool_status.json that separates this script's own errors from engine
    errors in the commandlet log (the GameFeatureData ensure is not ours)

Environment:
    IB_GARRISON_OUT       output folder (default Saved/GarrisonRestructure/inventory)
    IB_GARRISON_ROOT      folder prefix that IS the garrison (default "Carrowgate Garrison")
    IB_GARRISON_PLATFORM  label of the platform actor (default "GarrisonPlatform_New")
    IB_GARRISON_SUPPORT_MODE  mesh (default) | trace | both | off
    IB_GARRISON_SUPPORT_STEP  grid step in cm (default 400)
    IB_GARRISON_SUPPORT_ACTORS  comma-separated labels whose meshes ARE the ground
                              (default "GarrisonPlatform_New")
    IB_GARRISON_SCOPE_MARGIN  cm around the platform bounds that counts as garrison
                              scope for the extra per-actor records (default 5000)

Revision 2 (same day): water is identified by explicit label first and the
substring fallback no longer fires on walls, towers or directors (class is
checked before name); each water, seawall, platform and site-prop mesh records
its local bounds and whether its collision geometry can block a pawn at all.

Writes: actors.json, elements.json, assemblies.json, meshes.json, anchors.json,
support.json, support_faces.json, inventory_meta.json, tool_status.json,
summary.txt (clusters.json is kept only as a pointer for old readers).
"""
import unreal, json, os, traceback, hashlib, datetime, math
from pathlib import Path
from collections import Counter, defaultdict

SCHEMA = "garrison-inventory/2026-09-30"
LEVEL = "/Game/LevelPrototyping/CarrowGateGarrison"
MAP_FILE_REL = "LevelPrototyping/CarrowGateGarrison.umap"
OUT = Path(os.environ.get("IB_GARRISON_OUT",
                          str(Path(unreal.Paths.project_saved_dir()) / "GarrisonRestructure/inventory")))
ROOT = os.environ.get("IB_GARRISON_ROOT", "Carrowgate Garrison")
PLATFORM_LABEL = os.environ.get("IB_GARRISON_PLATFORM", "GarrisonPlatform_New")
SUPPORT_MODE = os.environ.get("IB_GARRISON_SUPPORT_MODE", "mesh").lower()
SUPPORT_STEP = float(os.environ.get("IB_GARRISON_SUPPORT_STEP", "400"))
SCOPE_MARGIN = float(os.environ.get("IB_GARRISON_SCOPE_MARGIN", "5000"))
# An allowlist, not a filter. The ground is the actors named here and nothing
# else, so a roof, a crate or a foliage card can never be mistaken for the deck.
SUPPORT_ACTORS = [t.strip() for t in os.environ.get(
    "IB_GARRISON_SUPPORT_ACTORS", "GarrisonPlatform_New").split(",") if t.strip()]

# Scenery around the site, never layout candidates.
EXCLUDE_FOLDER_PREFIXES = ("CG Mainland", "IronBreach/City", "IronBreach/Shoreline", "NavMesh", "Foam")

# ---------------------------------------------------------------------------
# EXPLICIT GARRISON ELEMENTS. Identity is label AND mesh, resolved to exactly one
# actor path; a door belongs to a building because its own label says so. These
# rows come from Codex's 2026-09-30 baseline review and the actual actors.json.
# Nothing here is inferred from distance or folder.
# ---------------------------------------------------------------------------
BUILDINGS = [
    # label,             mesh,                                              door label,            door class
    ("Medical",          "/Game/TripoModels/Medical/Medical.Medical",       "Medical_DoorFrame",   "BP_DoorFrame_C"),
    ("Barracks",         "/Game/TripoModels/Barracks/Barracks.Barracks",    "Barracks_DoorFrame",  "BP_DoorFrame_C"),
    ("Armory",           "/Game/TripoModels/Armory/Armory.Armory",          "Armory_DoorFrame",    "BP_DoorFrame_C"),
    ("Command",          "/Game/TripoModels/Command/Command.Command",       "Command_DoorFrame",   "BP_DoorFrame_C"),
    ("Mess_Hall",        "/Game/TripoModels/Mess_Hall/Mess_Hall.Mess_Hall", "Mess_Hall_DoorFrame", "BP_DoorFrame_C"),
    ("SM_MainGate_Tripo", "/Game/TripoModels/MainGate/MainGate.MainGate",   "BP_MainGateDoor",     "BP_DoorFrame_C"),
]
# Site props the layout may have to re-home if their ground changes. Identity by
# exact label (and class); listed so nothing is picked up by a loose match.
SITE_PROPS = [
    ("Docks_Ship_Hull", "StaticMeshActor"), ("Docks_Crane_01", "StaticMeshActor"),
    ("SM_Truck_Cargo", "StaticMeshActor"), ("SM_Truck_Cargo2", "StaticMeshActor"),
    ("SM_Truck_Cargo3", "StaticMeshActor"), ("SM_Truck_Cargo4", "StaticMeshActor"),
    ("Helicopter", "StaticMeshActor"),
    ("concrete_bunker_3d_model", "StaticMeshActor"), ("harbor guard tower 3d model", "Actor"),
]
GAMEPLAY_CLASSES = (
    "PlayerStart", "BP_WeaponRack_C", "BP_M1_KaijuSpawner_C", "BP_DoorFrame_C",
    "NavMeshBoundsVolume", "RecastNavMesh", "BlockingVolume", "TriggerBox", "TriggerVolume",
    "Act1BarracksDirector", "Act2EscalationDirector", "Act3ContactDirector",
    "Act4DeepWaterDirector", "Act5RetreatDirector",
)
ANCHOR_CLASSES = GAMEPLAY_CLASSES
WATER_LABEL_PARTS = ("harbor", "water", "sea", "foam", "surf", "ocean", "shallow")
# Water by explicit identity first. The substring test above is only a fallback
# for StaticMeshActors, and never for walls, towers or mission directors: the
# 2026-09-30 first run called Seawall_Main* ("sea"), Act4DeepWaterDirector
# ("water") and "harbor guard tower 3d model" ("harbor") water.
WATER_LABELS = ("IB_Harbor_Surface", "Water_Placeholder")
NOT_WATER_PARTS = ("seawall", "wall", "tower", "director", "bunker", "crane", "ship")
SEAWALL_PREFIX = "Seawall_"
# How far outside a building's own footprint its door may stand and still be
# called consistent. Informational only: the association is the label.
DOOR_SLACK = 300.0

TOOL_ERRORS = []
STARTED = datetime.datetime.utcnow().isoformat() + "Z"


def log(m):
    unreal.log("GARRISON INVENTORY: " + str(m))


def tool_error(what):
    """Every error this script swallows is recorded here and in tool_status.json,
    so a reader can separate tool failures from engine noise in the log."""
    detail = traceback.format_exc()[-900:]
    TOOL_ERRORS.append({"what": what, "detail": detail})
    unreal.log_warning("GARRISON INVENTORY: %s\n%s" % (what, detail))


def as_text(v):
    if v is None:
        return None
    try:
        if isinstance(v, (list, tuple)) or type(v).__name__ == "Array":
            return [as_text(x) for x in v]
        if hasattr(v, "get_path_name"):
            return v.get_path_name()
        return str(v)
    except Exception:
        return None


def vec(v):
    try:
        return [round(float(v.x), 2), round(float(v.y), 2), round(float(v.z), 2)]
    except Exception:
        return None


def prop_text(obj, name):
    try:
        return as_text(obj.get_editor_property(name))
    except Exception:
        return None


def rot_of(actor):
    try:
        r = actor.get_actor_rotation()
        return {"pitch": round(float(r.pitch), 4), "yaw": round(float(r.yaw), 4),
                "roll": round(float(r.roll), 4)}
    except Exception:
        return None


def bounds_of(actor):
    try:
        result = actor.get_actor_bounds(False)
        return vec(result[0]), vec(result[1])
    except Exception:
        return None, None


def map_sha256():
    try:
        content = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir())
        path = Path(content) / MAP_FILE_REL
        h = hashlib.sha256()
        with open(str(path), "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return {"path": str(path), "sha256": h.hexdigest().upper(), "bytes": path.stat().st_size}
    except Exception:
        tool_error("map hash")
        return {"path": None, "sha256": None}


def in_garrison_folder(folder):
    return bool(folder) and (folder == ROOT or folder.startswith(ROOT + "/"))


def excluded(folder):
    return bool(folder) and any(folder.startswith(p) for p in EXCLUDE_FOLDER_PREFIXES)


def looks_like_water(row):
    label = str(row.get("label") or "")
    if label in WATER_LABELS:
        return True
    if row.get("class") != "StaticMeshActor":
        return False
    if any(p in label.lower() for p in NOT_WATER_PARTS):
        return False
    text = (label + " " + str(row.get("mesh") or "") + " "
            + " ".join(str(m) for m in (row.get("materials") or []) if m)).lower()
    return any(p in text for p in WATER_LABEL_PARTS)


def collision_of(component):
    """Collision through the getter METHODS that exist on PrimitiveComponent.
    The previous probe asked get_editor_property('collision_enabled'), which is
    not a property name on StaticMeshComponent and failed every time."""
    out = {}
    for key, fn in (("enabled", lambda c: c.get_collision_enabled()),
                    ("profile", lambda c: c.get_collision_profile_name()),
                    ("object_type", lambda c: c.get_collision_object_type())):
        try:
            out[key] = str(fn(component))
        except Exception as error:
            out[key] = "unreadable: " + str(error).strip().splitlines()[-1][:120]
    for key, ch in (("visibility", "ECC_VISIBILITY"), ("pawn", "ECC_PAWN"), ("camera", "ECC_CAMERA")):
        try:
            out["response_" + key] = str(component.get_collision_response_to_channel(
                getattr(unreal.CollisionChannel, ch)))
        except Exception as error:
            out["response_" + key] = "unreadable: " + str(error).strip().splitlines()[-1][:120]
    try:
        out["affects_navigation"] = bool(component.get_editor_property("can_ever_affect_navigation"))
    except Exception:
        out["affects_navigation"] = None
    try:
        out["visible"] = bool(component.is_visible())
    except Exception:
        out["visible"] = None
    return out


AGG_LISTS = ("sphere_elems", "box_elems", "sphyl_elems", "convex_elems", "tapered_capsule_elems", "level_set_elems")


def simple_shapes(mesh):
    """Simple collision primitives in a mesh's BodySetup, counted directly."""
    body = mesh.get_editor_property("body_setup")
    if body is None:
        return 0, {"body_setup": None}
    agg = body.get_editor_property("agg_geom")
    parts = {}
    for name in AGG_LISTS:
        try:
            parts[name] = len(agg.get_editor_property(name) or [])
        except Exception:
            continue
    if not parts:
        raise RuntimeError("agg_geom element lists are not readable on this engine")
    return sum(parts.values()), parts


def mesh_collision(mesh):
    out = {}
    try:
        body = mesh.get_editor_property("body_setup")
        out["body_setup"] = bool(body)
        if body:
            out["collision_trace_flag"] = str(body.get_editor_property("collision_trace_flag"))
    except Exception as error:
        out["body_setup"] = "unreadable: " + str(error).strip().splitlines()[-1][:120]
    try:
        cc = mesh.get_editor_property("complex_collision_mesh")
        out["complex_collision_mesh"] = cc.get_path_name() if cc else None
    except Exception:
        out["complex_collision_mesh"] = "unreadable"
    try:
        bb = mesh.get_bounding_box()
        out["local_min"] = vec(bb.min)
        out["local_max"] = vec(bb.max)
    except Exception:
        out["local_min"] = out["local_max"] = None
    # Whether the mesh can block a walking pawn at all. Character movement sweeps
    # against SIMPLE collision; a mesh with no simple shapes blocks pawns only when
    # it is set to use complex collision as simple. BlockAll on the component says
    # nothing about this, so read the mesh's own BodySetup. (The editor subsystem's
    # GetSimpleCollisionCount returns -1 in a commandlet -- its "not in the editor"
    # code -- so it is recorded but never used as a count.)
    try:
        count, parts = simple_shapes(mesh)
        out["simple_collision_count"] = count
        out["simple_collision_parts"] = parts
    except Exception as error:
        out["simple_collision_count"] = "unreadable: " + str(error).strip().splitlines()[-1][:160]
    try:
        sme = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
        raw = sme.get_simple_collision_count(mesh)
        out["subsystem_simple_collision_count"] = (int(raw) if int(raw) >= 0
                                                   else "unavailable (subsystem returned %d)" % int(raw))
    except Exception as error:
        out["subsystem_simple_collision_count"] = "unreadable: " + str(error).strip().splitlines()[-1][:120]
    count, flag = out.get("simple_collision_count"), str(out.get("collision_trace_flag") or "")
    if "COMPLEX_AS_SIMPLE" in flag.upper():
        out["blocks_pawns_if_component_blocks"] = True
        out["pawn_blocking_basis"] = "mesh uses complex collision as simple"
    elif isinstance(count, int) and count > 0:
        out["blocks_pawns_if_component_blocks"] = True
        out["pawn_blocking_basis"] = "%d simple collision shape(s) in its BodySetup" % count
    elif isinstance(count, int) and count == 0 and "USE_DEFAULT" in flag.upper():
        out["blocks_pawns_if_component_blocks"] = None
        out["pawn_blocking_basis"] = ("no simple collision shapes; the mesh uses CTF_USE_DEFAULT, which inherits "
                                      "the project's DefaultShapeComplexity, so this depends on that setting "
                                      "(resolved by the layout run in the engine)")
    elif isinstance(count, int) and count == 0:
        out["blocks_pawns_if_component_blocks"] = False
        out["pawn_blocking_basis"] = ("no simple collision shapes and not complex-as-simple (%s): pawn "
                                      "sweeps pass through although the component profile blocks" % flag)
    else:
        out["blocks_pawns_if_component_blocks"] = None
        out["pawn_blocking_basis"] = "unknown: simple collision could not be read"
    return out


def components_of(actor):
    rows = []
    try:
        comps = actor.get_components_by_class(unreal.ActorComponent)
    except Exception:
        tool_error("components of " + actor.get_actor_label())
        return rows
    for c in comps or []:
        try:
            entry = {"name": c.get_name(), "class": c.get_class().get_name()}
            if isinstance(c, unreal.SceneComponent):
                entry["relative_location"] = vec(c.get_editor_property("relative_location"))
                try:
                    r = c.get_editor_property("relative_rotation")
                    entry["relative_yaw"] = round(float(r.yaw), 3)
                except Exception:
                    pass
            if isinstance(c, unreal.PrimitiveComponent):
                entry["collision"] = collision_of(c)
            if isinstance(c, unreal.StaticMeshComponent):
                m = c.get_editor_property("static_mesh")
                entry["mesh"] = m.get_path_name() if m else None
            rows.append(entry)
        except Exception:
            tool_error("component of " + actor.get_actor_label())
    return rows


def discover_references(actor):
    """Which other actors this one points at, found on the actor itself. The
    fixed name list used before (squad_npcs, spawn_volume...) does not exist on
    these classes, so every read came back 'unreadable' and said nothing."""
    found = {}
    for name in dir(actor):
        if name.startswith("_"):
            continue
        try:
            value = getattr(actor, name)
        except Exception:
            continue
        if callable(value):
            continue
        try:
            if isinstance(value, unreal.Actor):
                found[name] = value.get_path_name()
            elif type(value).__name__ == "Array" or isinstance(value, (list, tuple)):
                items = [v.get_path_name() for v in value if isinstance(v, unreal.Actor)]
                if items:
                    found[name] = items
            elif isinstance(value, unreal.SoftObjectPath):
                text = str(value)
                if "PersistentLevel" in text:
                    found[name] = text
        except Exception:
            continue
    return found


def collect():
    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    log("level actors: %d" % len(actors))
    rows, meshes, pairs = [], defaultdict(lambda: {"count": 0, "labels": [], "extent": None}), []
    for actor in actors:
        try:
            cls = actor.get_class().get_name()
            origin, extent = bounds_of(actor)
            try:
                folder = str(actor.get_folder_path())
            except Exception:
                folder = None
            if folder in ("None", ""):
                folder = None
            parent = None
            try:
                p = actor.get_attach_parent_actor()
                parent = p.get_path_name() if p else None
            except Exception:
                parent = "unreadable"
            row = {
                "path": actor.get_path_name(),
                "label": actor.get_actor_label(),
                "class": cls, "folder": folder,
                "loc": vec(actor.get_actor_location()),
                "rot": rot_of(actor),
                "scale": vec(actor.get_actor_scale3d()),
                "origin": origin, "extent": extent,
                "hidden": prop_text(actor, "hidden"),
                "tags": prop_text(actor, "tags"),
                "attach_parent": parent,
            }
            if isinstance(actor, unreal.StaticMeshActor):
                smc = actor.static_mesh_component
                mesh = smc.static_mesh if smc else None
                row["mesh"] = mesh.get_path_name() if mesh else None
                row["materials"] = [(smc.get_material(i).get_path_name() if smc.get_material(i) else None)
                                    for i in range(smc.get_num_materials())] if smc else []
                if row["mesh"]:
                    e = meshes[row["mesh"]]
                    e["count"] += 1
                    if len(e["labels"]) < 6:
                        e["labels"].append(row["label"])
                    if e["extent"] is None and extent and row["scale"]:
                        try:
                            e["extent"] = [round(extent[k] / row["scale"][k], 2)
                                           if abs(row["scale"][k]) > 1e-4 else None for k in range(3)]
                        except Exception:
                            e["extent"] = extent
            rows.append(row)
            pairs.append((actor, row))   # paired at append time; never zip() later
        except Exception:
            tool_error("skipped an actor")
    return pairs, rows, meshes


def _mesh_faces(actor):
    """World-space triangles of one actor's static mesh. No physics involved."""
    smc = actor.static_mesh_component
    mesh = smc.static_mesh if smc else None
    if not mesh:
        raise RuntimeError("actor has no static mesh")
    sections = mesh.get_num_sections(0)
    transform = actor.get_actor_transform()
    faces = []
    for section in range(sections):
        data = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, 0, section)
        verts, tris = data[0], data[1]
        world = [transform.transform_location(v) for v in verts]
        for i in range(0, len(tris) - 2, 3):
            faces.append((world[tris[i]], world[tris[i + 1]], world[tris[i + 2]]))
    return faces


def _normal(a, b, c):
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / length, ny / length, nz / length


def support_grid(platform_row, actors_by_label):
    """Ground height over the platform footprint (highest allowlisted surface per
    cell), plus the upward faces themselves for the layout's terrace analysis.
    Zero usable samples is 'no-data', never 'ok'."""
    result = {"mode": SUPPORT_MODE, "step": SUPPORT_STEP, "sources": [], "errors": []}
    faces_out = {"schema": SCHEMA, "note": "world-space triangles of the allowlisted ground actors; "
                 "'up' marks faces whose normal points upward (|n.z| > 0.5, either winding)",
                 "actors": []}
    if SUPPORT_MODE == "off" or not platform_row:
        result["status"] = "skipped" if SUPPORT_MODE == "off" else "no-platform"
        return result, faces_out
    o, e = platform_row["origin"], platform_row["extent"]
    x0, y0 = o[0] - e[0], o[1] - e[1]
    nx = int((2 * e[0]) // SUPPORT_STEP) + 1
    ny = int((2 * e[1]) // SUPPORT_STEP) + 1
    cells = [[None] * nx for _ in range(ny)]
    owner = [[None] * nx for _ in range(ny)]
    result.update({"x0": round(x0, 1), "y0": round(y0, 1), "nx": nx, "ny": ny})

    if SUPPORT_MODE in ("mesh", "both"):
        for index, label in enumerate(SUPPORT_ACTORS):
            actor = actors_by_label.get(label)
            if actor is None:
                result["errors"].append({"what": "support actor '%s'" % label, "detail": "not in the level"})
                continue
            try:
                faces = _mesh_faces(actor)
            except Exception:
                result["errors"].append({"what": "mesh faces of '%s'" % label,
                                         "detail": traceback.format_exc()[-800:]})
                continue
            result["sources"].append({"label": label, "triangles": len(faces)})
            tri_out = []
            for a, b, c in faces:
                ax, ay, az = float(a.x), float(a.y), float(a.z)
                bx, by, bz = float(b.x), float(b.y), float(b.z)
                cx, cy, cz = float(c.x), float(c.y), float(c.z)
                n = _normal((ax, ay, az), (bx, by, bz), (cx, cy, cz))
                tri_out.append({"v": [[round(ax, 1), round(ay, 1), round(az, 1)],
                                      [round(bx, 1), round(by, 1), round(bz, 1)],
                                      [round(cx, 1), round(cy, 1), round(cz, 1)]],
                                "nz": round(n[2], 4), "up": abs(n[2]) > 0.5})
                i0 = max(0, int((min(ax, bx, cx) - x0) // SUPPORT_STEP))
                i1 = min(nx - 1, int((max(ax, bx, cx) - x0) // SUPPORT_STEP))
                j0 = max(0, int((min(ay, by, cy) - y0) // SUPPORT_STEP))
                j1 = min(ny - 1, int((max(ay, by, cy) - y0) // SUPPORT_STEP))
                den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
                if abs(den) < 1e-9:
                    continue
                for j in range(j0, j1 + 1):
                    py = y0 + (j + 0.5) * SUPPORT_STEP
                    for i in range(i0, i1 + 1):
                        px = x0 + (i + 0.5) * SUPPORT_STEP
                        w0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
                        w1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
                        w2 = 1.0 - w0 - w1
                        if w0 < -1e-6 or w1 < -1e-6 or w2 < -1e-6:
                            continue
                        z = w0 * az + w1 * bz + w2 * cz
                        if cells[j][i] is None or z > cells[j][i]:
                            cells[j][i] = round(z, 1)
                            owner[j][i] = index
            faces_out["actors"].append({"label": label, "path": actor.get_path_name(),
                                        "triangles": tri_out})

    if SUPPORT_MODE in ("trace", "both"):
        result["errors"].append({"what": "trace mode",
                                 "detail": "trace support is diagnosed by ib_probe_garrison_support.py; "
                                           "this inventory only uses mesh support"})

    hits = sum(1 for row in cells for v in row if v is not None)
    result["hits"] = hits
    result["cells"] = cells
    result["owner"] = owner
    result["owner_names"] = SUPPORT_ACTORS
    result["status"] = "ok" if hits > 0 else "no-data"
    return result, faces_out


# ---------------------------------------------------------------------------
# Footprints: the building's own local mesh box, scaled and turned by its yaw.
# ---------------------------------------------------------------------------

def obb_of(row, mesh_info):
    """Oriented footprint from the mesh's LOCAL bounds, not the world AABB, so a
    rotated building is not inflated. Falls back to the AABB when local bounds
    are unreadable, and says so."""
    lo, hi = (mesh_info or {}).get("local_min"), (mesh_info or {}).get("local_max")
    yaw = ((row.get("rot") or {}).get("yaw") or 0.0)
    if lo and hi and row.get("scale"):
        s = row["scale"]
        lc = [(lo[k] + hi[k]) / 2.0 * s[k] for k in range(3)]
        half = [abs(hi[k] - lo[k]) / 2.0 * abs(s[k]) for k in range(3)]
        r = math.radians(yaw)
        cx = row["loc"][0] + lc[0] * math.cos(r) - lc[1] * math.sin(r)
        cy = row["loc"][1] + lc[0] * math.sin(r) + lc[1] * math.cos(r)
        return {"centre": [round(cx, 1), round(cy, 1)], "half": [round(half[0], 1), round(half[1], 1)],
                "yaw": round(yaw, 3), "z_min": round(row["loc"][2] + (lo[2] * s[2]), 1),
                "z_max": round(row["loc"][2] + (hi[2] * s[2]), 1), "from": "mesh local bounds"}
    if row.get("origin") and row.get("extent"):
        return {"centre": row["origin"][:2], "half": row["extent"][:2], "yaw": 0.0,
                "z_min": round(row["origin"][2] - row["extent"][2], 1),
                "z_max": round(row["origin"][2] + row["extent"][2], 1), "from": "world AABB (fallback)"}
    return None


def local_offset(obb, x, y):
    """(along, across) of a world point in an OBB's own frame, and the distance
    outside the box (0 when inside)."""
    r = math.radians(-obb["yaw"])
    dx, dy = x - obb["centre"][0], y - obb["centre"][1]
    lx = dx * math.cos(r) - dy * math.sin(r)
    ly = dx * math.sin(r) + dy * math.cos(r)
    ox = max(0.0, abs(lx) - obb["half"][0])
    oy = max(0.0, abs(ly) - obb["half"][1])
    return lx, ly, math.hypot(ox, oy)


def in_scope(row, frame):
    if excluded(row.get("folder")):
        return False
    if not frame:
        return in_garrison_folder(row.get("folder"))
    o, e = row.get("origin"), row.get("extent")
    if not o or not e:
        o, e = row.get("loc"), [0.0, 0.0, 0.0]
    if not o:
        return False
    return not (o[0] + e[0] < frame["min"][0] - SCOPE_MARGIN or o[0] - e[0] > frame["max"][0] + SCOPE_MARGIN
                or o[1] + e[1] < frame["min"][1] - SCOPE_MARGIN or o[1] - e[1] > frame["max"][1] + SCOPE_MARGIN)


def classify(row):
    """Class before name: a mission director or a guard tower is never 'water'
    because its label happens to contain the word."""
    label, cls = row["label"], row["class"]
    if label == PLATFORM_LABEL:
        return "ground"
    if cls in GAMEPLAY_CLASSES:
        return "gameplay"
    if cls in ("DirectionalLight", "SkyLight", "SkyAtmosphere", "VolumetricCloud", "ExponentialHeightFog",
               "PostProcessVolume", "PointLight", "SpotLight", "RectLight"):
        return "environment"
    if looks_like_water(row):
        return "water"
    if cls == "StaticMeshActor" and label.startswith(SEAWALL_PREFIX):
        return "seawall"
    if cls == "StaticMeshActor" and not row.get("mesh"):
        return "broken: no mesh"
    if (row.get("extent") in (None, [0.0, 0.0, 0.0])) and cls == "Actor":
        return "broken or empty actor: no bounds"
    return "prop"


def build_elements(pairs, rows, meshinfo, frame, meta):
    by_label = defaultdict(list)
    for actor, row in pairs:
        by_label[row["label"]].append((actor, row))
    unresolved, buildings, used = [], [], set()

    for label, mesh, door_label, door_class in BUILDINGS:
        cands = [(a, r) for a, r in by_label.get(label, []) if r.get("mesh") == mesh]
        entry = {"label": label, "mesh": mesh, "resolved": len(cands) == 1}
        if len(cands) != 1:
            unresolved.append({"what": "building %s" % label,
                               "why": "%d actor(s) match label AND mesh %s" % (len(cands), mesh)})
            buildings.append(entry)
            continue
        actor, row = cands[0]
        used.add(row["path"])
        mi = meshinfo.get(mesh) or {}
        obb = obb_of(row, mi)
        entry.update({"path": row["path"], "folder": row.get("folder"), "loc": row["loc"], "rot": row["rot"],
                      "scale": row["scale"], "footprint": obb, "mesh_collision": mi,
                      "attach_parent": row.get("attach_parent")})
        try:
            kids = actor.get_attached_actors()
            entry["attached_children"] = [k.get_path_name() for k in kids or []]
        except Exception:
            entry["attached_children"] = "unreadable"
        try:
            entry["collision"] = collision_of(actor.static_mesh_component)
        except Exception:
            tool_error("collision of " + label)
        doors = [(a, r) for a, r in by_label.get(door_label, []) if r["class"] == door_class]
        if len(doors) != 1:
            entry["door"] = None
            unresolved.append({"what": "door of %s" % label,
                               "why": "%d actor(s) labelled %s of class %s" % (len(doors), door_label, door_class)})
        else:
            da, dr = doors[0]
            used.add(dr["path"])
            lx, ly, outside = local_offset(obb, dr["loc"][0], dr["loc"][1]) if obb else (None, None, None)
            door = {"label": door_label, "path": dr["path"], "basis": "explicit label",
                    "folder": dr.get("folder"), "loc": dr["loc"], "rot": dr["rot"], "scale": dr["scale"],
                    "attach_parent": dr.get("attach_parent"),
                    "attached_to_building": dr.get("attach_parent") == row["path"],
                    "local_along": round(lx, 1) if lx is not None else None,
                    "local_across": round(ly, 1) if ly is not None else None,
                    "outside_footprint_cm": round(outside, 1) if outside is not None else None,
                    "components": components_of(da)}
            door["consistent"] = outside is not None and outside <= DOOR_SLACK
            if not door["consistent"]:
                unresolved.append({"what": "door %s" % door_label,
                                   "why": "stands %.0f cm outside %s's footprint; the label says it belongs, "
                                          "the position does not agree" % (outside or -1, label)})
            entry["door"] = door
        # Unfoldered static meshes whose ORIGIN lies inside this footprint are
        # candidates only -- reported, never adopted.
        cands_in = []
        if obb:
            for a2, r2 in pairs:
                if r2["path"] in used or r2["class"] != "StaticMeshActor" or r2.get("folder"):
                    continue
                if r2["label"] in [b[0] for b in BUILDINGS]:
                    continue
                o2 = r2.get("origin") or r2.get("loc")
                if not o2:
                    continue
                _, _, out2 = local_offset(obb, o2[0], o2[1])
                if out2 == 0.0 and obb["z_min"] - 50 <= o2[2] <= obb["z_max"] + 50:
                    cands_in.append({"label": r2["label"], "path": r2["path"], "mesh": r2.get("mesh"),
                                     "loc": r2["loc"], "scale": r2["scale"]})
        entry["inside_footprint_candidates"] = cands_in
        if cands_in:
            unresolved.append({"what": "%d unfoldered mesh(es) inside %s" % (len(cands_in), label),
                               "why": "no label, folder or attachment ties them to the building "
                                      "(%s); candidates only" % ", ".join(c["label"] for c in cands_in)})
        buildings.append(entry)

    # Everything else in scope, classified and located relative to the buildings.
    others = []
    footprints = [(b["label"], b.get("footprint")) for b in buildings if b.get("footprint")]
    for actor, row in pairs:
        if row["path"] in used or not in_scope(row, frame):
            continue
        kind = classify(row)
        nearest, nearest_d = None, None
        o = row.get("loc")
        if o:
            for lab, fp in footprints:
                _, _, d = local_offset(fp, o[0], o[1])
                if nearest_d is None or d < nearest_d:
                    nearest, nearest_d = lab, d
        item = {"label": row["label"], "path": row["path"], "class": row["class"], "kind": kind,
                "folder": row.get("folder"), "loc": row["loc"], "rot": row["rot"], "scale": row["scale"],
                "mesh": row.get("mesh"), "attach_parent": row.get("attach_parent"),
                "nearest_building": nearest,
                "distance_to_nearest_footprint_cm": round(nearest_d, 1) if nearest_d is not None else None,
                "association": "none (proximity is not association)"}
        if row["class"] not in ("StaticMeshActor",) or kind in ("ground", "water", "gameplay"):
            item["components"] = components_of(actor)
        else:
            try:
                item["collision"] = collision_of(actor.static_mesh_component)
            except Exception:
                tool_error("collision of " + row["label"])
        if kind == "gameplay":
            item["references"] = discover_references(actor)
        if kind.startswith("broken"):
            unresolved.append({"what": "%s (%s)" % (row["label"], row["class"]),
                               "why": kind + " -- placed on the map but renders nothing; owner decision"})
        others.append(item)

    site = []
    for label, cls in SITE_PROPS:
        found = [r for a, r in by_label.get(label, []) if r["class"] == cls]
        site.append({"label": label, "class": cls, "resolved": len(found) == 1,
                     "path": found[0]["path"] if len(found) == 1 else None})
        if len(found) != 1:
            unresolved.append({"what": "site prop %s" % label, "why": "%d match(es)" % len(found)})

    nav = [r for r in rows if r["class"] in ("NavMeshBoundsVolume", "RecastNavMesh")]
    if not nav:
        unresolved.append({"what": "navigation",
                           "why": "no NavMeshBoundsVolume or RecastNavMesh in the level -- AI has no navmesh "
                                  "here before or after any layout pass; restoring it is a separate decision"})
    return {"schema": SCHEMA, "map": meta, "buildings": buildings, "site_props": site,
            "others_in_scope": others, "navigation_actors": [r["path"] for r in nav],
            "unresolved": unresolved}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {"schema": SCHEMA, "level": LEVEL, "started_utc": STARTED}
    meta["map_file"] = map_sha256()
    pairs, rows, meshes = collect()

    meshinfo = {}
    # Local bounds and collision geometry for every mesh the layout reasons about:
    # buildings, the platform, the site props it may re-home (their world AABB is
    # inflated by rotation -- the ship's is square at yaw -45), water and seawalls.
    wanted = set(b[0] for b in BUILDINGS) | set(p[0] for p in SITE_PROPS) | set(WATER_LABELS) | {PLATFORM_LABEL}
    for actor, row in pairs:
        m = row.get("mesh")
        if m and m not in meshinfo and (row["label"] in wanted or row["label"].startswith(SEAWALL_PREFIX)):
            try:
                meshinfo[m] = mesh_collision(actor.static_mesh_component.static_mesh)
            except Exception:
                tool_error("mesh collision of " + m)
    for m, info in meshinfo.items():
        if m in meshes:
            meshes[m]["collision"] = info

    platform_row = next((r for r in rows if r["label"] == PLATFORM_LABEL), None)
    garrison_frame = None
    if platform_row and platform_row.get("origin") and platform_row.get("extent"):
        o, e = platform_row["origin"], platform_row["extent"]
        garrison_frame = {
            "source": "platform actor '%s'" % PLATFORM_LABEL,
            "path": platform_row["path"], "mesh": platform_row.get("mesh"),
            "centre": o, "half_extent": e,
            "min": [round(o[k] - e[k], 1) for k in range(3)],
            "max": [round(o[k] + e[k], 1) for k in range(3)],
            "size": [round(2 * e[k], 1) for k in range(3)],
            "bbox_top_z": round(o[2] + e[2], 1),
            "note": "bbox_top_z is the box, not the ground. Use support.json / support_faces.json.",
        }

    elements = build_elements(pairs, rows, meshinfo, garrison_frame, meta)
    # Platform, water and ground-adjacent actors: collision matters for what a
    # player can stand on once the layout changes what is visible.
    for actor, row in pairs:
        if row["label"] == PLATFORM_LABEL or (looks_like_water(row) and row["class"] == "StaticMeshActor"
                                              and not excluded(row.get("folder"))) or (
                row["class"] == "StaticMeshActor" and str(row["label"]).startswith(SEAWALL_PREFIX)):
            try:
                row["collision"] = collision_of(actor.static_mesh_component)
            except Exception:
                tool_error("collision of " + row["label"])
    if platform_row:
        elements["platform"] = {"label": PLATFORM_LABEL, "path": platform_row["path"],
                                "mesh": platform_row.get("mesh"), "collision": platform_row.get("collision"),
                                "mesh_collision": meshinfo.get(platform_row.get("mesh")),
                                "hidden": platform_row.get("hidden")}
    elements["water"] = [{"label": r["label"], "path": r["path"], "hidden": r.get("hidden"),
                          "loc": r["loc"], "extent": r["extent"], "collision": r.get("collision"),
                          "mesh": r.get("mesh"), "mesh_collision": meshinfo.get(r.get("mesh"))}
                         for r in rows if looks_like_water(r) and r["class"] == "StaticMeshActor"
                         and not excluded(r.get("folder"))]
    elements["seawalls"] = [{"label": r["label"], "path": r["path"], "loc": r["loc"], "rot": r["rot"],
                             "origin": r.get("origin"), "extent": r["extent"], "mesh": r.get("mesh"),
                             "collision": r.get("collision")}
                            for r in rows if r["class"] == "StaticMeshActor"
                            and str(r["label"]).startswith(SEAWALL_PREFIX)]
    elements["site_prop_meshes"] = {r.get("mesh"): meshinfo.get(r.get("mesh")) for r in rows
                                    if r["label"] in set(p[0] for p in SITE_PROPS) and r.get("mesh")}

    # Kept for older readers: folder assemblies, clearly marked as NOT buildings.
    assemblies = defaultdict(list)
    for r in rows:
        if in_garrison_folder(r.get("folder")):
            assemblies[r["folder"]].append(r)
    assembly_out = [{"folder": f, "actors": len(m), "labels": [x["label"] for x in m],
                     "paths": [x["path"] for x in m],
                     "note": "authored folder only; NOT a building assembly on this map -- use elements.json"}
                    for f, m in sorted(assemblies.items())]

    anchors = []
    for actor, row in pairs:
        if row["class"] in ANCHOR_CLASSES:
            entry = dict(row)
            entry["references"] = discover_references(actor)
            anchors.append(entry)

    actors_by_label = {}
    for actor, row in pairs:
        actors_by_label.setdefault(row["label"], actor)
    support, faces = support_grid(platform_row, actors_by_label)

    meta["finished_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
    meta["actors"] = len(rows)
    meta["map_file_after"] = map_sha256()
    meta["map_unchanged"] = meta["map_file"].get("sha256") == meta["map_file_after"].get("sha256")

    (OUT / "actors.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    (OUT / "elements.json").write_text(json.dumps(elements, indent=1), encoding="utf-8")
    (OUT / "assemblies.json").write_text(json.dumps(
        {"schema": SCHEMA, "root": ROOT, "garrison_frame": garrison_frame,
         "excluded_prefixes": list(EXCLUDE_FOLDER_PREFIXES), "assemblies": assembly_out,
         "note": "Folder groups are kept for reference only. Buildings are in elements.json."},
        indent=1), encoding="utf-8")
    (OUT / "meshes.json").write_text(json.dumps(
        {k: v for k, v in sorted(meshes.items(), key=lambda kv: -kv[1]["count"])}, indent=1), encoding="utf-8")
    (OUT / "anchors.json").write_text(json.dumps(anchors, indent=1), encoding="utf-8")
    (OUT / "support.json").write_text(json.dumps(support), encoding="utf-8")
    (OUT / "support_faces.json").write_text(json.dumps(faces), encoding="utf-8")
    (OUT / "inventory_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    (OUT / "clusters.json").write_text(json.dumps(
        {"superseded_by": "elements.json", "garrison_frame": garrison_frame}, indent=1), encoding="utf-8")

    L = ["CARROW GATE GARRISON INVENTORY (%s)" % SCHEMA, "level: " + LEVEL,
         "map sha256: %s (unchanged during run: %s)" % (meta["map_file"].get("sha256"), meta["map_unchanged"]),
         "actors: %d   distinct placed meshes: %d" % (len(rows), len(meshes)), ""]
    if garrison_frame:
        L.append("GARRISON FRAME from %s" % garrison_frame["source"])
        L.append("  min %s  max %s  size %s" % (garrison_frame["min"], garrison_frame["max"], garrison_frame["size"]))
    else:
        L.append("PLATFORM '%s' NOT FOUND -- the layout pass cannot run" % PLATFORM_LABEL)
    L.append("")
    L.append("SUPPORT GRID: %s   mode %s" % (support.get("status", "?"), support.get("mode")))
    for src in support.get("sources", []):
        L.append("  ground source '%s': %d triangle(s)" % (src["label"], src["triangles"]))
    if support.get("status") == "ok":
        total = support["nx"] * support["ny"]
        L.append("  %d x %d cells at %.0f cm, %d carry a height (%.0f%%)"
                 % (support["nx"], support["ny"], support["step"], support["hits"],
                    100.0 * support["hits"] / max(1, total)))
        flat = [z for row in support["cells"] for z in row if z is not None]
        terraces = Counter(int(round(z / 50.0)) * 50 for z in flat)
        L.append("  ground heights, commonest first: "
                 + ", ".join("%d cm x%d" % (z, n) for z, n in terraces.most_common(6)))
    for err in support.get("errors", [])[:4]:
        L.append("  error in %s: %s" % (err.get("what"), str(err.get("detail"))[-220:].replace("\n", " | ")))
    L.append("")
    L.append("BUILDINGS (explicit label + mesh; door by its own label)")
    for b in elements["buildings"]:
        if not b.get("resolved"):
            L.append("  %-18s UNRESOLVED" % b["label"])
            continue
        fp = b.get("footprint") or {}
        d = b.get("door") or {}
        L.append("  %-18s %s  centre %s half %s yaw %s (%s)"
                 % (b["label"], b["path"].split("PersistentLevel.")[-1], fp.get("centre"), fp.get("half"),
                    fp.get("yaw"), fp.get("from")))
        L.append("        door %-20s attached=%s outside_footprint=%s cm consistent=%s"
                 % (d.get("label"), d.get("attached_to_building"), d.get("outside_footprint_cm"), d.get("consistent")))
        mc = b.get("mesh_collision") or {}
        col = b.get("collision") or {}
        L.append("        collision %s/%s  trace flag %s  complex mesh %s"
                 % (col.get("enabled"), col.get("profile"), mc.get("collision_trace_flag"),
                    (mc.get("complex_collision_mesh") or "none").split("/")[-1]))
        if b.get("attached_children"):
            L.append("        attached children: %s" % b["attached_children"])
        if b.get("inside_footprint_candidates"):
            L.append("        inside footprint (candidates only): "
                     + ", ".join(c["label"] for c in b["inside_footprint_candidates"]))
    L.append("")
    if elements.get("platform"):
        p = elements["platform"]
        L.append("PLATFORM %s collision %s  mesh %s" % (p["label"], p.get("collision"), p.get("mesh_collision")))
    for w in elements.get("water", []):
        mc = w.get("mesh_collision") or {}
        L.append("WATER %-22s hidden=%s collision=%s" % (w["label"], w["hidden"], w.get("collision")))
        L.append("      mesh simple shapes=%s complexity=%s -> blocks pawns if the component blocks: %s (%s)"
                 % (mc.get("simple_collision_count"), mc.get("collision_complexity"),
                    mc.get("blocks_pawns_if_component_blocks"), mc.get("pawn_blocking_basis")))
    for w in elements.get("seawalls", []):
        L.append("SEAWALL %-20s loc %s extent %s" % (w["label"], w["loc"], w["extent"]))
    L.append("")
    L.append("OTHER ACTORS IN SCOPE (classified; none associated by proximity)")
    for o in sorted(elements["others_in_scope"], key=lambda x: (x["kind"], x["label"])):
        L.append("  %-26s %-30s %-20s nearest %-10s %s cm"
                 % (o["kind"][:26], o["label"][:30], o["class"][:20], o.get("nearest_building"),
                    o.get("distance_to_nearest_footprint_cm")))
        if o.get("references"):
            for k, v in o["references"].items():
                L.append("        ref %s -> %s" % (k, v))
    L.append("")
    L.append("UNRESOLVED (%d)" % len(elements["unresolved"]))
    for u in elements["unresolved"]:
        L.append("  - %s: %s" % (u["what"], u["why"]))
    L.append("")
    L.append("TOOL ERRORS: %d (engine errors elsewhere in the log are not this script's)" % len(TOOL_ERRORS))
    for t in TOOL_ERRORS[:10]:
        L.append("  - " + t["what"])
    (OUT / "summary.txt").write_text("\n".join(L) + "\n", encoding="utf-8")

    status = {"tool": "ib_inventory_garrison", "schema": SCHEMA, "status": "complete",
              "tool_errors": len(TOOL_ERRORS), "errors": TOOL_ERRORS[:40],
              "started_utc": STARTED, "finished_utc": meta["finished_utc"],
              "map_unchanged": meta["map_unchanged"], "saved_packages": 0}
    (OUT / "tool_status.json").write_text(json.dumps(status, indent=1), encoding="utf-8")
    log("COMPLETE; tool errors %d; nothing changed and no package saved -> %s" % (len(TOOL_ERRORS), OUT))


try:
    main()
except Exception:
    detail = traceback.format_exc()
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "tool_status.json").write_text(json.dumps(
            {"tool": "ib_inventory_garrison", "schema": SCHEMA, "status": "FAILED",
             "exception": detail[-3000:], "tool_errors": len(TOOL_ERRORS), "errors": TOOL_ERRORS[:40],
             "started_utc": STARTED}, indent=1), encoding="utf-8")
    except Exception:
        pass
    unreal.log_error("GARRISON INVENTORY FAILED\n" + detail)
    raise
