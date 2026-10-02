"""Carrow Gate garrison: current-baseline structural layout. READ-ONLY BY DEFAULT.

    UnrealEditor-Cmd.exe <project> -run=pythonscript -script="Scripts/ib_layout_garrison.py"
    python Scripts/ib_layout_garrison.py --inventory <inventory dir> --out <dir>

The second form is plain Python with no engine: it derives the same plan and
runs every geometric check, and marks the engine-only checks (asset loads,
the live read-only preflight) as not run.

WHAT CHANGED (2026-09-30). Shane's rebuilt map (SHA256 FAFFD601...) has no
folder per building: the five Tripo service buildings carry no folder, their
doors share `Carrowgate Garrison/Doors`, and the main gate sits in the root
folder. The Sep-23 version of this script moved folder "assemblies" and took its
frame from a `Main Gate` folder; on this map that silently drops every building
and groups five unrelated doors together. This version:

  * reads buildings and doors by EXPLICIT IDENTITY (full actor path, resolved by
    the inventory from label + mesh; each door by its own label) and never
    groups anything by folder or proximity;
  * MOVES NONE OF SHANE'S WORK. All six buildings, their doors, PlayerStart,
    the weapon rack and Cube/Cube2/Cube3 keep their exact transforms. The plan
    fits the reference around them;
  * derives the ground from the platform mesh's own faces (support_faces.json),
    checks it against the geometry this plan was designed on, and refuses if the
    platform has changed;
  * RESERVES the rear hangar for Connor (outline only; nothing is built there).

THE PLAN, against References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png
(land is -X and the gate side; image-right is -Y, the side the docks are on):

  rear service forecourt  the existing upper deck at its existing height,
                          squared off along its seaward edge. It holds every
                          existing building, door and spawn unchanged.
  hangar reserve          the rearmost clear rectangle on the spine axis,
                          found by a checked search. Outline markings only.
  central spine           a causeway from the forecourt's seaward edge.
  forward chamfered pad   an octagon at the end of the spine.
  left control platform   off the spine's image-left side, with open water
                          between it and the forecourt.
  right pier and berth    parallel to the spine with a water channel between
                          them; the ship berths on its outboard side.

WATER GAPS ARE REAL, NOT PAINTED. In `replace` mode (the default) the old
platform GarrisonPlatform_New is hidden AND its collision is turned off, with its
prior state recorded for IB_GARRISON_REVERT. Every surface that stays walkable is
rebuilt as a new deck at its existing height (the forecourt and the land ramp
included) and verified point by point under every preserved actor and along the
gameplay paths. Nothing invisible and collidable is left across a gap. What a
player finds in a gap depends on the harbor surface mesh's own collision, which
the report states from the inventory instead of assuming.

`keep` mode leaves the platform untouched and only marks the hangar reserve;
it cannot produce the reference's gaps.

Environment:
    IB_GARRISON_INVENTORY  inventory folder (default Saved/GarrisonRestructure/inventory)
    IB_GARRISON_OUT        output folder (default Saved/GarrisonRestructure/layout)
    IB_GARRISON_PLAN       a reviewed plan.json; required by apply, verify and revert
    IB_GARRISON_PLATFORM_MODE  replace (default) | keep
    IB_GARRISON_TARGET_LEVEL   the map to verify/apply/revert, e.g.
                           /Game/_GarrisonPreview_Disposable/CarrowGateGarrison_CB1Preview.
                           Required; never guessed. The source map is refused.
    IB_GARRISON_VERIFY=1   read-only: check the target against its last recorded state
    IB_GARRISON_APPLY=1    perform the plan on the target (does not save)
    IB_GARRISON_SAVE=1     with APPLY, save the TARGET map: the only writing path
    IB_GARRISON_REVERT=1   with APPLY, undo instead
    IB_GARRISON_COMPOSITION  P3: move the Command and Mess_Hall assemblies (each building
                           with its own door frame, as one rigid unit) onto the control
                           platform and put the hangar reservation on the rear edge,
                           centred on the spine (provisional P1 envelope). Unset: the
                           building-preserving baseline, byte-identical to before.
    IB_GARRISON_AUDIT      audit.json from Scripts/ib_garrison_assembly_audit.py; P3
                           refuses to plan a move the audit has not shown complete.
    IB_GARRISON_FINISH     PF1 (with P3): turn the dock crane to lie along the pier against
                           its berth edge so one straight service lane runs the pier's
                           length past the crane and trucks, and give the NEW decks (spine,
                           control platform, pier, pad) a low quay coping, a concrete
                           fascia, yellow edge lines and route markings. Joins stay flush.
    IB_GARRISON_PIER_AUDIT the 'pier' identity audit (ib_garrison_assembly_audit.py with
                           IB_GARRISON_AUDIT_SET=pier); PF1 refuses to move a prop it has not
                           shown standalone.

LIFECYCLE AND GUARDS. A target map carries a receipt history in
Saved/GarrisonRestructure/receipts/<package>.json: 'created' (written by
Scripts/ib_garrison_preview_copy.py, with the source map's SHA256), then
'applied' / 'reverted' entries written by this tool after a verified save, each
with the target file's SHA256. A run is accepted only when the target file is
byte-identical to its LAST recorded state, so a saved apply can be repeated
(verified in place, nothing written) or reverted in a new process, and any edit
made outside this tool is refused instead of guessed at.

  apply   preflight on the clean state (every move at its exact source
          transform, platform flags equal to the plan's live capture, no
          generated or label-colliding actors, assets load), then pieces, each
          verified for label, tag, mesh, material, location, rotation, scale,
          visibility, component collision and actor-level collision; then moves
          (props, and for P3 the building assemblies), verified for location, rotation
          and scale; the old platform is retired LAST; the whole applied state is
          checked again; only then may it save. Any failure stops before the
          platform or the save.
  revert  read-only validation first: the level must be exactly the applied
          state. Any conflict (a moved prop, a changed or missing deck, an extra
          generated actor) refuses the whole revert and changes nothing. Then
          props return to their exact source transforms, generated actors are
          removed (each removal checked), and every captured platform flag
          (profile, collision, actor collision, visibility, hidden) is restored
          exactly; the clean state is verified before any save.

Every move carries the actor's absolute source and target transform keyed by
full source-map actor path, remapped deliberately to the target map. Output
files are written as LF bytes and the reported SHA256 is the file's own.

Writes: plan.json, manifest.csv, report.txt, tool_status.json (plan), or
lifecycle_<mode>.json (verify/apply/revert).
"""
import json, os, sys, math, hashlib, datetime, traceback, csv, io
from pathlib import Path

try:
    import unreal
except ImportError:
    unreal = None
ENGINE = unreal is not None

SCHEMA = "garrison-layout/2026-09-30"
LEVEL = "/Game/LevelPrototyping/CarrowGateGarrison"
MAP_FILE_REL = "Content/LevelPrototyping/CarrowGateGarrison.umap"
REFERENCE = "References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png"
RUN_TAG = "IB_GarrisonCB1"
RUN_FOLDER = "Carrowgate Garrison/Structure CB1"
LABEL_PREFIX = "IBGC_"
OLD_RUN_TAGS = ("IB_GarrisonPass1",)
OLD_LABEL_PREFIXES = ("IBG1_",)
STARTED = datetime.datetime.utcnow().isoformat() + "Z"


def _arg(name):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def _project_dir():
    if os.environ.get("IB_PROJECT_DIR"):
        return Path(os.environ["IB_PROJECT_DIR"])
    if ENGINE:
        return Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    return Path(__file__).resolve().parent.parent


PROJECT = _project_dir()
INV = Path(_arg("--inventory") or os.environ.get("IB_GARRISON_INVENTORY")
           or str(PROJECT / "Saved/GarrisonRestructure/inventory"))
OUT = Path(_arg("--out") or os.environ.get("IB_GARRISON_OUT")
           or str(PROJECT / "Saved/GarrisonRestructure/layout"))
PLAN_IN = os.environ.get("IB_GARRISON_PLAN")
APPLY = ENGINE and os.environ.get("IB_GARRISON_APPLY") == "1"
SAVE = APPLY and os.environ.get("IB_GARRISON_SAVE") == "1"
REVERT = APPLY and os.environ.get("IB_GARRISON_REVERT") == "1"
VERIFY = ENGINE and not APPLY and os.environ.get("IB_GARRISON_VERIFY") == "1"
TARGET_LEVEL = (os.environ.get("IB_GARRISON_TARGET_LEVEL") or "").strip().rstrip("/") or None
PLATFORM_MODE = (_arg("--mode") or os.environ.get("IB_GARRISON_PLATFORM_MODE", "replace")).lower()
COMPOSITION = (_arg("--composition") or os.environ.get("IB_GARRISON_COMPOSITION") or "").strip().upper() or None
AUDIT_IN = _arg("--audit") or os.environ.get("IB_GARRISON_AUDIT")
FINISH = (_arg("--finish") or os.environ.get("IB_GARRISON_FINISH") or "").strip().upper() or None
PIER_AUDIT_IN = _arg("--pier-audit") or os.environ.get("IB_GARRISON_PIER_AUDIT")

# ---------------------------------------------------------------------------
# Explicit identities. Buildings and doors come from the inventory's
# elements.json, which resolved each by label AND mesh and each door by its own
# label. Everything else is named here by label, class and (where it has one)
# mesh, and must resolve to exactly one actor.
# ---------------------------------------------------------------------------
BUILDING_LABELS = ("Medical", "Barracks", "Armory", "Command", "Mess_Hall", "SM_MainGate_Tripo")
GATE_LABEL = "SM_MainGate_Tripo"
PLATFORM_ID = ("GarrisonPlatform_New", "StaticMeshActor", "/Game/LevelPrototyping/Garrison/Geometries/Body2.Body2")
HARBOR_ID = ("IB_Harbor_Surface", "StaticMeshActor",
             "/Game/IronBreach/Environment/Bastion/SM_Bastion_Harbor.SM_Bastion_Harbor")
WATER_PLACEHOLDER_ID = ("Water_Placeholder", "StaticMeshActor", "/Engine/BasicShapes/Cube.Cube")
ANCHOR_IDS = [("PlayerStart", "PlayerStart", None), ("BP_WeaponRack", "BP_WeaponRack_C", None)]
CANDIDATE_IDS = [("Cube", "StaticMeshActor", "/Engine/BasicShapes/Cube.Cube"),
                 ("Cube2", "StaticMeshActor", "/Engine/BasicShapes/Cube.Cube"),
                 ("Cube3", "StaticMeshActor", "/Engine/BasicShapes/Cube.Cube")]
SHIP_ID = ("Docks_Ship_Hull", "StaticMeshActor", "/Game/LevelPrototyping/AIModels/SM_Ship_Hull.SM_Ship_Hull")
CRANE_ID = ("Docks_Crane_01", "StaticMeshActor", "/Game/LevelPrototyping/AIModels/SM_Dock_Crane.SM_Dock_Crane")
TRUCK_IDS = [("SM_Truck_Cargo" + s, "StaticMeshActor", "/Game/LevelPrototyping/AIModels/SM_Truck_Cargo.SM_Truck_Cargo")
             for s in ("", "2", "3", "4")]
HELI_ID = ("Helicopter", "StaticMeshActor", "/Game/TripoModels/Helicopter/Helicopter.Helicopter")
BROKEN_IDS = [("concrete_bunker_3d_model", "StaticMeshActor", None),
              ("harbor guard tower 3d model", "Actor", None),
              ("2026-09-04-10-03-41-983", "Actor", None)]
PROTECTED_CLASSES = {
    "RecastNavMesh", "NavMeshBoundsVolume", "DirectionalLight", "SkyLight", "SkyAtmosphere", "VolumetricCloud",
    "ExponentialHeightFog", "PostProcessVolume", "PlayerStart", "BP_DoorFrame_C", "BP_WeaponRack_C",
    "Act1BarracksDirector", "Act2EscalationDirector", "Act3ContactDirector", "Act4DeepWaterDirector",
    "Act5RetreatDirector", "BP_M1_KaijuSpawner_C",
}

# The platform geometry this plan was designed on (Body2 upper deck, clockwise
# from the rear image-left corner). The live outline is derived from the mesh
# faces and must match within GEOMETRY_TOLERANCE, or the plan refuses.
EXPECTED_UPPER = [(-500, 8000), (1182, 9993), (8382, 9993), (10182, 8193), (10182, 5256), (5239, -2500),
                  (-500, -2500), (-500, -1750), (-1250, -1000), (-1250, 500), (-500, 1250)]
EXPECTED_RAMP = {"x": (-3500.0, -1250.0), "y": (-1000.0, 500.0), "z": (10.0, 385.0)}
GEOMETRY_TOLERANCE = 5.0

# Lateral proportions measured off the approved reference as fractions of the
# forecourt width. The image is an oblique aerial, so only lateral widths are
# taken from it; lengths along the spine are functional and stated.
RATIO_SPINE_WIDTH = 0.31
RATIO_PAD_ACROSS = 0.43
RATIO_CONTROL_WIDTH = 0.37
RATIO_HANGAR_WIDTH = 0.48
RATIO_SPINE_LENGTH = 0.35
GAP_CONTROL = 900.0      # open water between the forecourt and the control platform
GAP_CHANNEL = 900.0      # open water between the spine/pad and the pier
PIER_WIDTH = 2200.0      # the dock crane's mesh box (20 m across at its yaw) fits with 1 m to spare
FENDER = 300.0           # berth clearance between the pier edge and the hull
SHIP_DRAFT = 300.0       # hull bottom below the waterline once it floats
CONTROL_CHAMFER = 1050.0
RESERVE_MIN_DEPTH = 2500.0
CLEAR_BUILDING = 600.0   # reserve clearance to any building footprint
CLEAR_ANCHOR = 300.0     # reserve clearance to spawn, rack and door approaches
DOOR_APPROACH = 600.0    # the ground in front of a door that must stay walkable
SEAWALL_CLEARANCE = 1500.0
FILL_DROP = 1.0          # chamfer fillers sit 1 cm under the main deck: no coplanar overlap
SUPPORT_TOLERANCE = 2.0  # cm a preserved actor's ground may differ after the change
SAMPLE = 50.0            # cm grid for footprint and path sampling
RAMP_THICKNESS = 800.0

# P3 composition (compose_p3). Complete two-actor assemblies onto the control platform.
P3_ASSEMBLIES = {"Command": "Command_DoorFrame", "Mess_Hall": "Mess_Hall_DoorFrame"}
P3_YAW = {"Command": -90.0,    # unchanged: the tower's door keeps facing +X, onto the open seaward apron
          "Mess_Hall": 180.0}  # turned 90 degrees: the low block's door faces the spine (-Y)
P3_REAR_MARGIN = 150.0   # the platform's control-gap edge to both buildings' rear faces
P3_SPINE_GAP = 100.0     # the spine seam to Mess_Hall's front face (its door opens onto the spine)
P3_WALKWAY = 700.0       # Mess_Hall's back to Command's side: the circulation space between them
ROUTE_STEP = 50.0        # routing grid (cm)
ROUTE_CLEAR = 60.0       # a pawn capsule (radius ~42) plus margin: routes keep this far from obstacles and edges
RESERVE_MARK_HALF = 40.0  # P3 reservation outline: 80 cm lines (the baseline's 30 cm lines did not read overhead)
RESERVE_INNER_INSET = 150.0
# PF1 pier finish
FINISH_TAG = "IB_GarrisonPierFinish"   # every finish piece carries it next to RUN_TAG
PF_CRANE_TURN = 135.0     # the crane's yaw -135 -> 0: its 20 m mesh box lies along the pier instead of across it
CRANE_EDGE_KEEP = 5.0     # the crane's box stops this far inboard of the outboard coping
PF_TRUCK_EDGE_KEEP = 175.0  # PF1: the trucks' boxes stop this far from the channel edge (P3: 250), so the 6 m lane's
                            # 40 cm lines keep ~50 cm from the crane and from the trucks
PF_REVISION = 2           # r1 had 20 cm lines, which did not read overhead (as the P3 baseline's 30 cm lines had not)
LANE_WIDTH = 600.0        # the marked service lane
LANE_BUFFER = 50.0        # lane edge to the nearest obstacle box, at least
LANE_MIN = 300.0          # below this the lane is refused as a walking route
LANE_LINE_KEEP = 25.0     # a pier lane line's outer edge to the crane / truck boxes, at least
COPING_IN, COPING_LIP = 50.0, 10.0      # coping: 50 cm on the deck, 10 cm over the quay face
COPING_RISE, COPING_DROP = 8.0, 30.0    # its top 8 cm above the deck (a walkable curb), its face 30 cm deep
COPING_STEP = 0.4         # coping tops that overlap at a corner differ by this much (no z-fighting)
FASCIA_OUT, FASCIA_IN = 6.0, 4.0        # fascia: 6 cm proud of the quay face, 4 cm into it
FASCIA_BELOW_WATER = 45.0
FASCIA_STEP = 0.4
EDGE_LINE_INSET = 100.0   # yellow edge line centre, inboard of the water edge
LINE_HALF = 20.0          # 40 cm lines, as wide as the P3 pad ring (r1's 20 cm did not read overhead)
MARK_STEP = 0.3           # overlapping markings get tops this far apart
DASH_LEN, DASH_HALF_W, DASH_PERIOD = 300.0, 20.0, 600.0
SPINE_LANE_HALF = 600.0   # spine lane lines either side of the axis
BASTION_CONCRETE = "/Game/IronBreach/Environment/Bastion/M_Bastion_Concrete.M_Bastion_Concrete"
COPING_MATERIAL = BASTION_CONCRETE   # the project's wall concrete (world-position mapped; used on its big walls)
FASCIA_MATERIAL = BASTION_CONCRETE

CUBE = "/Engine/BasicShapes/Cube.Cube"
DECK_MATERIAL = "/Game/Generated_Materials/Concrete_Mat.Concrete_Mat"   # the platform's own, world-aligned
MARK_MATERIAL = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_HelipadMarking.MI_Landmass_HelipadMarking"

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem) if ENGINE else None
TOOL_ERRORS = []


def log(m):
    if ENGINE:
        unreal.log("GARRISON LAYOUT: " + str(m))
    else:
        print("GARRISON LAYOUT: " + str(m))


def tool_error(what):
    TOOL_ERRORS.append({"what": what, "detail": traceback.format_exc()[-900:]})
    if ENGINE:
        unreal.log_warning("GARRISON LAYOUT: %s\n%s" % (what, TOOL_ERRORS[-1]["detail"]))


def fail(m):
    raise RuntimeError("GARRISON LAYOUT REFUSED: " + str(m))


def r1(v):
    return round(float(v), 1)


def r50(v):
    return 50.0 * round(float(v) / 50.0)


# ---------------------------------------------------------------------------
# Plane geometry. Polygons are lists of (x, y).
# ---------------------------------------------------------------------------

def rect(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def obb(cx, cy, hx, hy, yaw):
    a = math.radians(yaw)
    c, s = math.cos(a), math.sin(a)
    return [(cx + sx * hx * c - sy * hy * s, cy + sx * hx * s + sy * hy * c)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def area(poly):
    return 0.5 * sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))


def inside(x, y, poly):
    hit = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i - 1]
        x2, y2 = poly[i]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                hit = not hit
    return hit


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def segs_cross(a, b, c, d):
    d1, d2, d3, d4 = _cross(c, d, a), _cross(c, d, b), _cross(a, b, c), _cross(a, b, d)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def poly_dist(P, Q):
    """0 when the polygons touch or overlap, else the gap between them."""
    if any(inside(x, y, Q) for x, y in P) or any(inside(x, y, P) for x, y in Q):
        return 0.0
    for i in range(len(P)):
        for j in range(len(Q)):
            if segs_cross(P[i - 1], P[i], Q[j - 1], Q[j]):
                return 0.0
    best = float("inf")
    for (x, y) in P:
        for j in range(len(Q)):
            best = min(best, seg_dist(x, y, Q[j - 1][0], Q[j - 1][1], Q[j][0], Q[j][1]))
    for (x, y) in Q:
        for i in range(len(P)):
            best = min(best, seg_dist(x, y, P[i - 1][0], P[i - 1][1], P[i][0], P[i][1]))
    return best


def bbox(poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return min(xs), max(xs), min(ys), max(ys)


def samples_in(poly, step=SAMPLE, inset=5.0):
    """Grid points inside a polygon plus its corners pulled 5 cm inward, so a
    footprint's edges are tested, not only its middle."""
    x0, x1, y0, y1 = bbox(poly)
    pts = []
    nx, ny = max(1, int((x1 - x0) // step)), max(1, int((y1 - y0) // step))
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = x0 + (x1 - x0) * i / float(nx)
            y = y0 + (y1 - y0) * j / float(ny)
            if inside(x, y, poly):
                pts.append((x, y))
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    for x, y in poly:
        d = math.hypot(cx - x, cy - y) or 1.0
        pts.append((x + (cx - x) * inset / d, y + (cy - y) * inset / d))
    return pts


def polyline_samples(points, step=SAMPLE):
    out = []
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        n = max(1, int(math.hypot(bx - ax, by - ay) // step))
        for k in range(n):
            t = k / float(n)
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    out.append(points[-1])
    return out


def octagon(cx, cy, a):
    """Regular octagon, flats facing the axes, inradius a."""
    h = a * math.tan(math.radians(22.5))
    return [(cx - a, cy - h), (cx - h, cy - a), (cx + h, cy - a), (cx + a, cy - h),
            (cx + a, cy + h), (cx + h, cy + a), (cx - h, cy + a), (cx - a, cy + h)]


def chamfered(x0, x1, y0, y1, cuts):
    """Rectangle with 45-degree cuts; cuts maps 'll','lr','ur','ul' to leg length."""
    out = []
    ll, lr, ur, ul = (cuts.get(k, 0.0) for k in ("ll", "lr", "ur", "ul"))
    out += [(x0, y0 + ll), (x0 + ll, y0)] if ll else [(x0, y0)]
    out += [(x1 - lr, y0), (x1, y0 + lr)] if lr else [(x1, y0)]
    out += [(x1, y1 - ur), (x1 - ur, y1)] if ur else [(x1, y1)]
    out += [(x0 + ul, y1), (x0, y1 - ul)] if ul else [(x0, y1)]
    return out


def dedupe(poly, eps=0.5):
    out = []
    for p in poly:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > eps:
            out.append(p)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= eps:
        out.pop()
    return out


# ---------------------------------------------------------------------------
# Decomposition into disjoint boxes. A polygon whose edges are axis-aligned or
# 45-degree-ish chamfers becomes (a) axis-aligned rectangles that tile its
# rectilinear core without overlap, and (b) one rotated box per chamfer whose
# outer face lies on the chamfer. Fillers sit FILL_DROP under the main top, so
# where they run under a rectangle nothing is coplanar and nothing flickers.
# ---------------------------------------------------------------------------

def rectilinear_core(poly):
    core, fillers = [], []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        core.append(a)
        if abs(a[0] - b[0]) > 1.0 and abs(a[1] - b[1]) > 1.0:
            c1, c2 = (b[0], a[1]), (a[0], b[1])
            probe = lambda c: inside(c[0] + (0.5 * (a[0] + b[0]) - c[0]) * 0.01,
                                     c[1] + (0.5 * (a[1] + b[1]) - c[1]) * 0.01, poly)
            c = c1 if probe(c1) else c2
            core.append(c)
            fillers.append((a, b, c))
    return dedupe(core), fillers


def slabs(core, axis):
    """Tile a rectilinear polygon with rectangles along x (axis 0) or y (1)."""
    keys = sorted(set(round(p[axis], 3) for p in core))
    rects = []
    for k0, k1 in zip(keys, keys[1:]):
        if k1 - k0 < 1.0:
            continue
        mid = 0.5 * (k0 + k1)
        cuts = []
        for i in range(len(core)):
            a, b = core[i - 1], core[i]
            if abs(a[1 - axis] - b[1 - axis]) < 1e-6:           # edge parallel to the sweep axis
                lo, hi = min(a[axis], b[axis]), max(a[axis], b[axis])
                if lo < mid < hi:
                    cuts.append(a[1 - axis])
        cuts.sort()
        for j in range(0, len(cuts) - 1, 2):
            if axis == 0:
                rects.append([k0, k1, cuts[j], cuts[j + 1]])
            else:
                rects.append([cuts[j], cuts[j + 1], k0, k1])
    merged = []
    for rc in rects:              # join neighbours along the sweep with the same span
        for m in merged:
            if axis == 0 and abs(m[1] - rc[0]) < 1e-6 and abs(m[2] - rc[2]) < 1e-6 and abs(m[3] - rc[3]) < 1e-6:
                m[1] = rc[1]
                break
            if axis == 1 and abs(m[3] - rc[2]) < 1e-6 and abs(m[0] - rc[0]) < 1e-6 and abs(m[1] - rc[1]) < 1e-6:
                m[3] = rc[3]
                break
        else:
            merged.append(list(rc))
    return merged


def decompose(poly):
    core, fillers = rectilinear_core(poly)
    a, b = slabs(core, 0), slabs(core, 1)
    return (a if len(a) <= len(b) else b), fillers


class Catalogue(object):
    """Unit half-extents read from the inventory, not assumed."""

    def __init__(self, meshes):
        self.meshes = meshes or {}
        self.missing = []

    def half(self, path):
        e = (self.meshes.get(path) or {}).get("extent")
        if not e or any(v in (None, 0) for v in e):
            if path not in self.missing:
                self.missing.append(path)
            return [50.0, 50.0, 50.0]
        return [float(v) for v in e]


def box_piece(cat, label, zone, kind, cx, cy, hx, hy, top, bottom, yaw=0.0, material=DECK_MATERIAL,
              collision="BlockAll", footprint=None):
    unit = cat.half(CUBE)
    hz = (top - bottom) / 2.0
    return {"label": LABEL_PREFIX + label, "zone": zone, "kind": kind, "mesh": CUBE, "material": material,
            "location": [r1(cx), r1(cy), r1(bottom + hz)],
            "rotation": {"roll": 0.0, "pitch": 0.0, "yaw": round(yaw, 4)},
            "scale": [round(hx / unit[0], 5), round(hy / unit[1], 5), round(hz / unit[2], 5)],
            "half_extent": [r1(hx), r1(hy), r1(hz)], "top_z": r1(top), "bottom_z": r1(bottom),
            "collision": collision,
            "footprint": [[r1(x), r1(y)] for x, y in (footprint or obb(cx, cy, hx, hy, yaw))]}


def zone_pieces(cat, zone, poly, top, bottom, prefix):
    rects, fillers = decompose(poly)
    out = []
    for i, (x0, x1, y0, y1) in enumerate(sorted(rects)):
        out.append(box_piece(cat, "%s_Deck_%02d" % (prefix, i), zone, "deck", (x0 + x1) / 2.0, (y0 + y1) / 2.0,
                             (x1 - x0) / 2.0, (y1 - y0) / 2.0, top, bottom))
    for i, (a, b, c) in enumerate(fillers):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        h = abs(_cross(a, b, c)) / L
        mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
        nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        if (c[0] - mx) * nx + (c[1] - my) * ny < 0:
            nx, ny = -nx, -ny
        cx, cy = mx + nx * h / 2.0, my + ny * h / 2.0
        yaw = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        out.append(box_piece(cat, "%s_Chamfer_%02d" % (prefix, i), zone, "filler", cx, cy, L / 2.0, h / 2.0,
                             top - FILL_DROP, bottom, yaw=yaw))
    return out


def ramp_piece(cat, ramp, bottom_pad):
    (x0, x1), (y0, y1), (z0, z1) = ramp["x"], ramp["y"], ramp["z"]
    run, rise = x1 - x0, z1 - z0
    L = math.hypot(run, rise)
    p = math.atan2(rise, run)
    tx, ty, tz = (x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0
    nx, nz = -math.sin(p), math.cos(p)
    cx, cz = tx - nx * RAMP_THICKNESS / 2.0, tz - nz * RAMP_THICKNESS / 2.0
    unit = cat.half(CUBE)
    return {"label": LABEL_PREFIX + "Ramp_Deck_00", "zone": "land_ramp", "kind": "ramp", "mesh": CUBE,
            "material": DECK_MATERIAL, "location": [r1(cx), r1(ty), r1(cz)],
            "rotation": {"roll": 0.0, "pitch": round(math.degrees(p), 4), "yaw": 0.0},
            "scale": [round(L / 2.0 / unit[0], 5), round((y1 - y0) / 2.0 / unit[1], 5),
                      round(RAMP_THICKNESS / 2.0 / unit[2], 5)],
            "half_extent": [r1(L / 2.0), r1((y1 - y0) / 2.0), r1(RAMP_THICKNESS / 2.0)],
            "plane": {"x0": x0, "z0": z0, "slope": rise / run}, "top_z": r1(z1), "bottom_z": r1(bottom_pad),
            "collision": "BlockAll", "footprint": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]}


def mark_piece(cat, label, zone, cx, cy, hx, hy, deck_top, yaw=0.0):
    return box_piece(cat, label, zone, "marking", cx, cy, hx, hy, deck_top + 1.5, deck_top - 0.5, yaw=yaw,
                     material=MARK_MATERIAL, collision="NoCollision")


def surface_z(pieces, x, y):
    """Top of the walkable new decks at (x, y), or None."""
    best = None
    for p in pieces:
        if p["collision"] != "BlockAll":
            continue
        if not inside(x, y, p["footprint"]):
            continue
        if p["kind"] == "ramp":
            pl = p["plane"]
            z = pl["z0"] + (x - pl["x0"]) * pl["slope"]
        else:
            z = p["top_z"]
        best = z if best is None else max(best, z)
    return best


class Faces(object):
    """The existing platform surface, straight from its mesh triangles."""

    def __init__(self, tris):
        self.tris = []
        for t in tris:
            if not t.get("up"):
                continue
            v = t["v"]
            xs, ys = [p[0] for p in v], [p[1] for p in v]
            self.tris.append((v, min(xs), max(xs), min(ys), max(ys)))

    def z(self, x, y):
        best = None
        for v, x0, x1, y0, y1 in self.tris:
            if x < x0 - 0.01 or x > x1 + 0.01 or y < y0 - 0.01 or y > y1 + 0.01:
                continue
            (ax, ay, az), (bx, by, bz), (cx, cy, cz) = v
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-9:
                continue
            w0 = ((by - cy) * (x - cx) + (cx - bx) * (y - cy)) / den
            w1 = ((cy - ay) * (x - cx) + (ax - cx) * (y - cy)) / den
            w2 = 1.0 - w0 - w1
            if min(w0, w1, w2) < -1e-6:
                continue
            z = w0 * az + w1 * bz + w2 * cz
            best = z if best is None else max(best, z)
        return best


def flat_outline(tris, z0, tol=3.0):
    """Outer loop of the flat faces at one height, from edges used exactly once."""
    count = {}
    for t in tris:
        if abs(t["nz"]) < 0.99 or any(abs(p[2] - z0) > tol for p in t["v"]):
            continue
        P = [(round(p[0]), round(p[1])) for p in t["v"]]
        for i in range(3):
            key = tuple(sorted((P[i], P[(i + 1) % 3])))
            count[key] = count.get(key, 0) + 1
    adj = {}
    for (a, b), c in count.items():
        if c == 1:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
    if not adj or any(len(v) != 2 for v in adj.values()):
        return None
    loops, seen = [], set()
    for start in adj:
        if start in seen:
            continue
        loop, prev, cur = [start], None, start
        seen.add(start)
        while True:
            nxt = [q for q in adj[cur] if q != prev]
            if not nxt or nxt[0] == start or nxt[0] in seen:
                break
            prev, cur = cur, nxt[0]
            loop.append(cur)
            seen.add(cur)
        simple = []
        for i in range(len(loop)):
            a, b, c = loop[i - 1], loop[i], loop[(i + 1) % len(loop)]
            if abs(_cross(a, b, c)) > 10.0 * math.hypot(c[0] - a[0], c[1] - a[1]):
                simple.append((float(b[0]), float(b[1])))
        loops.append(simple)
    loops.sort(key=lambda L: -abs(area(L)))
    return loops


def align_loop(loop, expected, tol):
    """The derived loop in the expected vertex order, or None if no rotation or
    direction of it matches every expected vertex within tol."""
    if not loop or len(loop) != len(expected):
        return None, None
    n, best = len(loop), (None, float("inf"))
    for direction in (1, -1):
        seq = loop if direction == 1 else list(reversed(loop))
        for s in range(n):
            cand = seq[s:] + seq[:s]
            err = max(math.hypot(cand[i][0] - expected[i][0], cand[i][1] - expected[i][1]) for i in range(n))
            if err < best[1]:
                best = (cand, err)
    return (best[0], best[1]) if best[1] <= tol else (None, best[1])


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

def read_json(path):
    if not path.is_file():
        fail("missing %s -- run Scripts/ib_inventory_garrison.py first" % path)
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path):
    try:
        h = hashlib.sha256()
        with open(str(path), "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest().upper()
    except Exception:
        return None


def package_file(asset_path):
    """'/Game/A/B.B' -> <project>/Content/A/B.uasset (engine assets: None)."""
    if not asset_path or not asset_path.startswith("/Game/"):
        return None
    pkg = asset_path.split(".")[0][len("/Game/"):]
    return PROJECT / "Content" / (pkg + ".uasset")


def resolve(rows, label, cls, mesh=None):
    found = [r for r in rows if r.get("label") == label and r.get("class") == cls
             and (mesh is None or r.get("mesh") == mesh)]
    return (found[0] if len(found) == 1 else None), len(found)


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

def norm_yaw(a):
    a = (a + 180.0) % 360.0 - 180.0
    return 180.0 if abs(a + 180.0) < 1e-9 else a


def rot2(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def world_half(half, yaw):
    a = math.radians(yaw)
    c, s_ = abs(math.cos(a)), abs(math.sin(a))
    return (half[0] * c + half[1] * s_, half[0] * s_ + half[1] * c)


def read_audit(path, inv_sha, buildings, problems):
    """The identity audit must show each P3 assembly complete (building + its own door,
    nothing attached, inside or referencing them) on THIS map, before anything is planned."""
    if not path:
        problems.append("P3 needs IB_GARRISON_AUDIT (Scripts/ib_garrison_assembly_audit.py): assemblies are moved "
                        "only when an identity audit of this map shows them complete")
        return None
    f = Path(path)
    if not f.is_file():
        problems.append("audit file %s not found" % f)
        return None
    a = json.loads(f.read_text(encoding="utf-8"))
    out = {"file": str(f), "sha256": file_sha256(f), "status": a.get("status"),
           "source_sha256": a.get("source_sha256_after"), "assemblies": {}}
    if a.get("status") != "complete":
        problems.append("audit %s did not complete" % f)
    if a.get("source_sha256_after") != inv_sha or a.get("source_sha256_before") != inv_sha:
        problems.append("audit was made on map %s..., not the planned map %s..."
                        % (str(a.get("source_sha256_after"))[:8], str(inv_sha)[:8]))
    out["zones"] = {z: [r.get("label") for r in rows] for z, rows in (a.get("zones") or {}).items()}
    out["references_checked"] = {"t3d_actor_blocks": (a.get("t3d") or {}).get("actor_blocks"),
                                 "actors_in_level": a.get("actors_in_level")}
    for lab, door_lab in P3_ASSEMBLIES.items():
        v = (a.get("verdict") or {}).get(lab) or {}
        t, td = (a.get("targets") or {}).get(lab) or {}, (a.get("targets") or {}).get(door_lab) or {}
        b = buildings.get(lab) or {}
        same = (t.get("path") == b.get("path") and td.get("path") == (b.get("door") or {}).get("path")
                and t.get("label_matches") and td.get("label_matches"))
        out["assemblies"][lab] = {"members": [lab, door_lab], "complete": bool(v.get("complete_two_actor_assembly")),
                                  "identities_match_inventory": bool(same),
                                  "other_actors_overlapping": v.get("other_actors_overlapping"),
                                  "attached": v.get("attached_children"), "attach_parents": v.get("attach_parents"),
                                  "referenced_by": v.get("referenced_by_other_actors")}
        if not v.get("complete_two_actor_assembly"):
            problems.append("audit: %s is not a complete two-actor assembly (%s)" % (lab, json.dumps(v)[:300]))
        if not same:
            problems.append("audit: %s / %s identities differ from the inventory's" % (lab, door_lab))
    return out


def compose_p3(buildings, by_path, design, problems):
    """P3 on the left control platform, read like the reference: the TOWER (Command)
    at the platform's rear-outer corner, its door still facing +X onto the open
    seaward apron; the LOW BLOCK (Mess_Hall) along the platform's spine edge, turned
    so its door faces the spine; P3_WALKWAY of clear space between them. Each
    building moves with its own door frame as one rigid assembly: both are turned
    about the building's pivot by the same angle, so the door keeps its exact place
    in the facade. Returns (composition record, relocated building elements, moves)."""
    cp = design["control_platform"]
    x0, y0, y1 = cp["x"][0], cp["y"][0], cp["y"][1]
    rec, relocated, moves = {"name": "P3", "buildings": {}}, {}, []

    def target_centre(lab, yaw, placed):
        wx, wy = world_half(buildings[lab]["footprint"]["half"], yaw)
        cx = x0 + P3_REAR_MARGIN + wx
        if lab == "Mess_Hall":
            cy = y0 + P3_SPINE_GAP + wy
        else:
            m = placed["Mess_Hall"]
            cy = m["centre"][1] + m["world_half"][1] + P3_WALKWAY + wy
        return (cx, cy), (wx, wy)

    placed = {}
    for lab in ("Mess_Hall", "Command"):
        b = buildings.get(lab)
        if not b or not b.get("door") or not b["door"].get("loc"):
            problems.append("P3: %s or its door is missing from the inventory elements" % lab)
            return None, {}, []
        f, d = b["footprint"], b["door"]
        yaw_to = P3_YAW[lab]
        delta = norm_yaw(yaw_to - b["rot"]["yaw"])
        centre, wh = target_centre(lab, yaw_to, placed)
        c_off = rot2((f["centre"][0] - b["loc"][0], f["centre"][1] - b["loc"][1]), delta)
        pivot = (centre[0] - c_off[0], centre[1] - c_off[1])
        d_off = rot2((d["loc"][0] - b["loc"][0], d["loc"][1] - b["loc"][1]), delta)
        door = (pivot[0] + d_off[0], pivot[1] + d_off[1])
        # The door sits in the building's local +Y (front) half: that side is its entrance.
        local_door = rot2((d["loc"][0] - f["centre"][0], d["loc"][1] - f["centre"][1]), -f["yaw"])
        if local_door[1] < 0.5 * f["half"][1]:
            problems.append("P3: %s's door is not in its local +Y facade (local %s); entrance side unknown"
                            % (lab, [r1(v) for v in local_door]))
        normal = rot2((0.0, 1.0), yaw_to)
        nb = json.loads(json.dumps(b))
        nb["loc"] = [r1(pivot[0]), r1(pivot[1]), b["loc"][2]]
        nb["rot"] = dict(b["rot"], yaw=round(norm_yaw(b["rot"]["yaw"] + delta), 4))
        nb["footprint"] = dict(f, centre=[r1(centre[0]), r1(centre[1])], yaw=round(norm_yaw(f["yaw"] + delta), 4))
        nb["door"] = dict(d, loc=[r1(door[0]), r1(door[1]), d["loc"][2]],
                          rot=dict(d.get("rot") or {}, yaw=round(norm_yaw((d.get("rot") or {}).get("yaw", 0.0) + delta), 4)))
        nb["door_normal"] = [round(normal[0], 6), round(normal[1], 6)]
        nb["relocated"] = {"composition": "P3", "rotation_delta": delta}
        relocated[lab] = nb
        placed[lab] = {"centre": centre, "world_half": wh}
        if centre[1] + wh[1] > y1 + 0.5 or centre[0] + wh[0] > cp["x"][1] + 0.5:
            problems.append("P3: %s does not fit on the control platform (reaches x %.0f, y %.0f; platform to "
                            "x %.0f, y %.0f)" % (lab, centre[0] + wh[0], centre[1] + wh[1], cp["x"][1], y1))
        for row_path, to_loc, to_yaw, role in ((b["path"], nb["loc"], nb["rot"]["yaw"], "building"),
                                                (d["path"], nb["door"]["loc"], nb["door"]["rot"]["yaw"], "door")):
            row = by_path.get(row_path)
            if row is None:
                problems.append("P3: %s not in actors.json" % row_path)
                continue
            rot_to = dict(row["rot"])
            rot_to["yaw"] = to_yaw
            moves.append({"identity": row["path"], "label": row["label"], "class": row["class"],
                          "role": "assembly " + role, "assembly": lab,
                          "from": {"loc": row["loc"], "rot": row["rot"], "scale": row["scale"]},
                          "to": {"loc": list(to_loc), "rot": rot_to, "scale": row["scale"]},
                          "why": ("P3: %s moves to the control platform as one rigid assembly with %s "
                                  "(turned %+.0f deg about the building pivot)" % (lab, P3_ASSEMBLIES[lab], delta)),
                          "target": "deck"})
        rec["buildings"][lab] = {
            "door_label": d["label"], "rotation_delta": delta,
            "from": {"loc": b["loc"], "yaw": b["rot"]["yaw"], "footprint_centre": f["centre"],
                     "door_loc": d["loc"], "door_yaw": (d.get("rot") or {}).get("yaw")},
            "to": {"loc": nb["loc"], "yaw": nb["rot"]["yaw"], "footprint_centre": nb["footprint"]["centre"],
                   "door_loc": nb["door"]["loc"], "door_yaw": nb["door"]["rot"]["yaw"]},
            "door_normal": nb["door_normal"],
            "footprint": [[r1(x), r1(y)] for x, y in obb(centre[0], centre[1], f["half"][0], f["half"][1],
                                                        nb["footprint"]["yaw"])],
            "threshold": {"outside": [r1(door[0] + normal[0] * 150.0), r1(door[1] + normal[1] * 150.0)],
                          "inside": [r1(door[0] - normal[0] * 150.0), r1(door[1] - normal[1] * 150.0)]},
            "height_m": r1((f.get("z_max", 0.0) - f.get("z_min", 0.0)) / 100.0),
            "reads_as": "tower" if lab == "Command" else "low block"}
    rec["rules"] = {"Command": "rear-outer corner, yaw %.0f (door +X onto the seaward apron)" % P3_YAW["Command"],
                    "Mess_Hall": "along the spine edge, yaw %.0f (door -Y onto the spine)" % P3_YAW["Mess_Hall"],
                    "rear_margin_cm": P3_REAR_MARGIN, "spine_gap_cm": P3_SPINE_GAP, "walkway_cm": P3_WALKWAY}
    return rec, relocated, moves


# -- routing: a pawn-width path over the deck union, around obstacles ---------------------

class RouteGrid(object):
    """Cells of ROUTE_STEP over the union of the walkable decks, eroded by ROUTE_CLEAR
    from the deck edges, with every obstacle footprint inflated by ROUTE_CLEAR. A
    route found here keeps a pawn's width from every listed obstacle and deck edge;
    the engine sweeps then test what is really there."""

    def __init__(self, walk_polys, obstacles, clear=ROUTE_CLEAR, step=ROUTE_STEP):
        xs = [p[0] for P in walk_polys for p in P]
        ys = [p[1] for P in walk_polys for p in P]
        self.step, self.x0, self.y0 = step, min(xs), min(ys)
        self.nx = int((max(xs) - self.x0) // step) + 1
        self.ny = int((max(ys) - self.y0) // step) + 1
        inside_ = [bytearray(self.nx) for _ in range(self.ny)]
        for j in range(self.ny):
            y = self.y0 + j * step
            row = inside_[j]
            for P in walk_polys:
                xc = []
                for i in range(len(P)):
                    (xa, ya), (xb, yb) = P[i - 1], P[i]
                    if (ya > y) != (yb > y):
                        xc.append(xa + (y - ya) * (xb - xa) / (yb - ya))
                xc.sort()
                for k in range(0, len(xc) - 1, 2):
                    i0 = max(0, int(math.ceil((xc[k] - self.x0) / step - 1e-9)))
                    i1 = min(self.nx - 1, int(math.floor((xc[k + 1] - self.x0) / step + 1e-9)))
                    for i in range(i0, i1 + 1):
                        row[i] = 1
        k = int(math.ceil(clear / step))
        hor = [bytearray(self.nx) for _ in range(self.ny)]
        for j in range(self.ny):
            src, dst = inside_[j], hor[j]
            for i in range(self.nx):
                if i - k >= 0 and i + k < self.nx and all(src[i - k:i + k + 1]):
                    dst[i] = 1
        self.walk = [bytearray(self.nx) for _ in range(self.ny)]
        for j in range(k, self.ny - k):
            for i in range(self.nx):
                if all(hor[jj][i] for jj in range(j - k, j + k + 1)):
                    self.walk[j][i] = 1
        self.obstacles = obstacles
        for name, poly in obstacles:
            bx0, bx1, by0, by1 = bbox(poly)
            for j in range(max(0, self.j(by0 - clear)), min(self.ny - 1, self.j(by1 + clear)) + 1):
                for i in range(max(0, self.i(bx0 - clear)), min(self.nx - 1, self.i(bx1 + clear)) + 1):
                    if self.walk[j][i]:
                        x, y = self.x(i), self.yv(j)
                        if inside(x, y, poly) or min(seg_dist(x, y, poly[q - 1][0], poly[q - 1][1], poly[q][0],
                                                              poly[q][1]) for q in range(len(poly))) <= clear:
                            self.walk[j][i] = 0

    def i(self, x):
        return int(round((x - self.x0) / self.step))

    def j(self, y):
        return int(round((y - self.y0) / self.step))

    def x(self, i):
        return self.x0 + i * self.step

    def yv(self, j):
        return self.y0 + j * self.step

    def ok(self, i, j):
        return 0 <= i < self.nx and 0 <= j < self.ny and self.walk[j][i]

    def snap(self, pt, reach=400.0):
        i0, j0 = self.i(pt[0]), self.j(pt[1])
        if self.ok(i0, j0):
            return (i0, j0), 0.0
        best, r = None, int(reach // self.step)
        for j in range(j0 - r, j0 + r + 1):
            for i in range(i0 - r, i0 + r + 1):
                if self.ok(i, j):
                    d = math.hypot(self.x(i) - pt[0], self.yv(j) - pt[1])
                    if d <= reach and (best is None or d < best[1]):
                        best = ((i, j), d)
        return best if best else (None, None)

    def visible(self, a, b):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / (self.step / 2.0)))
        return all(self.ok(self.i(a[0] + (b[0] - a[0]) * t / n), self.j(a[1] + (b[1] - a[1]) * t / n))
                   for t in range(n + 1))

    def route(self, start, goal):
        import heapq
        (s, ds), (g, dg) = self.snap(start), self.snap(goal)
        if s is None or g is None:
            return None, {"snap_start": ds, "snap_goal": dg, "why": "start or goal has no walkable cell within 4 m"}
        openq, came, cost = [(0.0, s)], {s: None}, {s: 0.0}
        nb = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
              (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
        while openq:
            _, c = heapq.heappop(openq)
            if c == g:
                break
            for di, dj, w in nb:
                n = (c[0] + di, c[1] + dj)
                if not self.ok(*n) or (di and dj and not (self.ok(c[0] + di, c[1]) and self.ok(c[0], c[1] + dj))):
                    continue
                nc = cost[c] + w
                if nc < cost.get(n, 1e18):
                    cost[n], came[n] = nc, c
                    heapq.heappush(openq, (nc + math.hypot(n[0] - g[0], n[1] - g[1]), n))
        if g not in came:
            return None, {"snap_start": ds, "snap_goal": dg, "why": "no pawn-width route over the decks"}
        cells, c = [], g
        while c is not None:
            cells.append((self.x(c[0]), self.yv(c[1])))
            c = came[c]
        cells.reverse()
        pts = [cells[0]]
        k = 0
        while k < len(cells) - 1:
            far = k + 1
            for m in range(len(cells) - 1, k, -1):
                if self.visible(cells[k], cells[m]):
                    far = m
                    break
            pts.append(cells[far])
            k = far
        full = [tuple(start)] + pts + [tuple(goal)]
        return [[r1(x), r1(y)] for x, y in full], {"snap_start": r1(ds), "snap_goal": r1(dg)}

    def clearance(self, pts):
        """The smallest distance from the route's samples to any listed obstacle footprint."""
        best = (float("inf"), None)
        for x, y in polyline_samples([tuple(p) for p in pts], step=self.step):
            for name, poly in self.obstacles:
                d = 0.0 if inside(x, y, poly) else min(
                    seg_dist(x, y, poly[q - 1][0], poly[q - 1][1], poly[q][0], poly[q][1]) for q in range(len(poly)))
                if d < best[0]:
                    best = (d, name)
        return best


# ---------------------------------------------------------------------------
# Pier finish (PF1). On top of P3: one straight, clear service lane along the
# pier (the dock crane turned to lie along the pier against its berth edge),
# and a restrained quay finish on the NEW decks only -- spine, control platform,
# pier, pad: a low coping along every water edge, a concrete fascia on the quay
# face, a yellow edge line inset from the edge, lane lines along the pier's
# service lane and the spine, sparse route dashes to the control-platform
# entrances and the passage between its buildings, and a threshold bar in front
# of each relocated door. Joins between decks get no coping, so every join
# stays flush. Every piece carries the run tag (and FINISH_TAG) and goes through
# the same verified apply / exact revert as the decks.
# ---------------------------------------------------------------------------

FINISH_ZONES = ("spine", "control_platform", "pier", "pad")
FINISH_PREFIX = {"spine": "Spine", "control_platform": "Control", "pier": "Pier", "pad": "Pad"}


def ccw(poly):
    return list(poly) if area(poly) > 0 else list(reversed(poly))


def _edge(P, i):
    a, b = P[i], P[(i + 1) % len(P)]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    return a, b, L, (ux, uy), (uy, -ux)          # outward normal of a counter-clockwise outline


def _zone_at(x, y, shapes, skip):
    for z, s in shapes.items():
        if z != skip and inside(x, y, s):
            return z
    return None


def water_runs(zone, shapes, step=5.0):
    """The stretches of one deck's outline that face open water rather than another
    deck: edge index, [t0, t1] along the edge (refined to ~0.3 mm), and the edge frame."""
    P = ccw(shapes[zone])
    runs = []
    for i in range(len(P)):
        a, b, L, u, nn = _edge(P, i)
        if L < 1.0:
            continue

        def wet(t):
            t = min(max(t, 0.0), L)
            return _zone_at(a[0] + u[0] * t + nn[0] * 3.0, a[1] + u[1] * t + nn[1] * 3.0, shapes, zone) is None

        ts = [k * step for k in range(int(L // step) + 1)]
        if L - ts[-1] > 0.01:
            ts.append(L)
        w = [wet(t) for t in ts]
        k = 0
        while k < len(ts):
            if not w[k]:
                k += 1
                continue
            j = k
            while j + 1 < len(ts) and w[j + 1]:
                j += 1
            t0, t1 = ts[k], ts[j]
            if k > 0:
                lo, hi = ts[k - 1], ts[k]
                for _ in range(14):
                    mid = (lo + hi) / 2.0
                    lo, hi = (lo, mid) if wet(mid) else (mid, hi)
                t0 = hi
            if j < len(ts) - 1:
                lo, hi = ts[j], ts[j + 1]
                for _ in range(14):
                    mid = (lo + hi) / 2.0
                    lo, hi = (mid, hi) if wet(mid) else (lo, mid)
                t1 = lo
            if t1 - t0 >= 1.0:
                runs.append({"zone": zone, "edge": i, "t0": t0, "t1": t1, "L": L, "a": a, "u": u, "n": nn})
            k = j + 1
    return runs


def _pt(r, t, inboard=0.0):
    return (r["a"][0] + r["u"][0] * t - r["n"][0] * inboard, r["a"][1] + r["u"][1] * t - r["n"][1] * inboard)


def _meet(p, u, q, v):
    """Parameter s of p + u*s where it meets the line q + v*r; None if parallel."""
    den = u[0] * v[1] - u[1] * v[0]
    if abs(den) < 1e-9:
        return None
    return ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / den


def _turn(u, v):
    return math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1])))


def strip_piece(cat, label, zone, kind, r, s0, s1, c0, c1, top, bottom, material, collision, tags):
    """A box along run r's edge: s0..s1 along it, c0..c1 across it (negative = inboard)."""
    a, u, n = r["a"], r["u"], r["n"]
    cx = a[0] + u[0] * (s0 + s1) / 2.0 + n[0] * (c0 + c1) / 2.0
    cy = a[1] + u[1] * (s0 + s1) / 2.0 + n[1] * (c0 + c1) / 2.0
    p = box_piece(cat, label, zone, kind, cx, cy, (s1 - s0) / 2.0, (c1 - c0) / 2.0, top, bottom,
                  yaw=math.degrees(math.atan2(u[1], u[0])), material=material, collision=collision)
    p["tags"] = list(tags)
    return p


def line_piece(cat, label, zone, kind, p0, p1, half_w, top, bottom, tags):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    p = box_piece(cat, label, zone, kind, (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0, L / 2.0, half_w, top, bottom,
                  yaw=math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])), material=MARK_MATERIAL,
                  collision="NoCollision")
    p["tags"] = list(tags)
    return p


def obb_overlap(P, Q, eps=0.5):
    """True when two convex footprints overlap by more than eps on every separating axis
    (touching or merely adjacent pieces do not count)."""
    for poly in (P, Q):
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i - 1], poly[i]
            ax, ay = -(y2 - y1), x2 - x1
            L = math.hypot(ax, ay) or 1.0
            ax, ay = ax / L, ay / L
            pa = [x * ax + y * ay for x, y in P]
            pb = [x * ax + y * ay for x, y in Q]
            if min(max(pa), max(pb)) - max(min(pa), min(pb)) <= eps:
                return False
    return True


def stagger(group, fixed=()):
    """Level per piece: the lowest one no overlapping piece of the group already uses,
    so no two overlapping pieces ever share a face height (no z-fighting)."""
    placed = [(q, 0) for q in fixed]
    out = {}
    for p in group:
        used = set(lv for q, lv in placed if obb_overlap(p["footprint"], q["footprint"]))
        lv = 0
        while lv in used:
            lv += 1
        out[p["label"]] = lv
        placed.append((p, lv))
    return out


def service_lane(pier, obstacles, keep):
    """The widest straight band along the pier (x) that no obstacle box enters, inside
    [y0 + keep, y1 - keep] (keep = the coping). Returns (y_lo, y_hi, bounded_lo, bounded_hi)."""
    x0, x1, y0, y1 = bbox(pier)
    lo, hi = y0 + keep, y1 - keep
    iv = []
    for lab, fp in obstacles:
        fx0, fx1, fy0, fy1 = bbox(fp)
        if fx1 <= x0 or fx0 >= x1 or fy1 <= lo or fy0 >= hi:
            continue
        iv.append((max(fy0, lo), min(fy1, hi), lab))
    iv.sort()
    gaps, y, who = [], lo, "outboard coping"
    for a, b, lab in iv:
        if a > y:
            gaps.append((y, a, who, lab))
        if b > y:
            y, who = b, lab
    if y < hi:
        gaps.append((y, hi, who, "inboard coping"))
    return max(gaps, key=lambda g: g[1] - g[0]) if gaps else None


def build_finish(cat, shapes, deck_top, water_z, lane, spine, ctrl_route, doors, existing_marks):
    """Every finish piece, plus the runs they were built from (for the report)."""
    tags = [FINISH_TAG]
    runs = []
    for z in FINISH_ZONES:
        runs += water_runs(z, shapes)
    for r in runs:
        r["prev"] = r["next"] = None
    for r in runs:
        e1 = _pt(r, r["t1"])
        for q in runs:
            if q is not r:
                s0 = _pt(q, q["t0"])
                if math.hypot(e1[0] - s0[0], e1[1] - s0[1]) < 2.0:
                    r["next"], q["prev"] = q, r
    count = {}

    def label(zone, kind):
        count[(zone, kind)] = count.get((zone, kind), -1) + 1
        return "%s_%s_%02d" % (FINISH_PREFIX[zone], kind, count[(zone, kind)])

    coping, fascia, marks = [], [], []
    for r in runs:
        ends = {}
        for end, q in (("t0", r["prev"]), ("t1", r["next"])):
            if q is None:
                ends[end] = {"kind": "join", "phi": 0.0, "q": None}
            else:
                ends[end] = {"kind": "corner" if q["zone"] == r["zone"] else "neighbour", "phi": _turn(r["u"], q["u"]),
                             "q": q}
        r["ends"] = {e: {"kind": v["kind"], "turn_deg": r1(math.degrees(v["phi"]))} for e, v in ends.items()}

        def ext(end, amount):
            v = ends[end]
            return amount * math.tan(v["phi"] / 2.0) + 0.5 if v["kind"] == "corner" and v["phi"] > 1e-3 else 0.0

        s0, s1 = r["t0"] - ext("t0", COPING_LIP), r["t1"] + ext("t1", COPING_LIP)
        coping.append(strip_piece(cat, label(r["zone"], "Coping"), r["zone"], "coping", r, s0, s1, -COPING_IN,
                                  COPING_LIP, deck_top + COPING_RISE, deck_top - COPING_DROP, COPING_MATERIAL,
                                  "BlockAll", tags))
        s0, s1 = r["t0"] - ext("t0", FASCIA_OUT), r["t1"] + ext("t1", FASCIA_OUT)
        fascia.append(strip_piece(cat, label(r["zone"], "Fascia"), r["zone"], "fascia", r, s0, s1, -FASCIA_IN,
                                  FASCIA_OUT, deck_top - COPING_DROP + 1.0, water_z - FASCIA_BELOW_WATER,
                                  FASCIA_MATERIAL, "NoCollision", tags))
        # the edge line: inset EDGE_LINE_INSET, meeting its neighbours' lines at the inset corners
        p0 = _pt(r, 0.0, EDGE_LINE_INSET)
        ss = {}
        for end in ("t0", "t1"):
            v = ends[end]
            s = r[end]
            if v["q"] is not None and (v["kind"] == "corner" or math.degrees(v["phi"]) <= 95.0):
                q = v["q"]
                m = _meet(p0, r["u"], _pt(q, 0.0, EDGE_LINE_INSET), q["u"])
                if m is not None:
                    s = m + (LINE_HALF * math.tan(v["phi"] / 2.0) if v["phi"] > 1e-3 else 0.0) * (1 if end == "t1" else -1)
            ss[end] = s
        if ss["t1"] - ss["t0"] > LINE_HALF:      # r1 used 2 x its 10 cm half-width; keeps the 28.6 cm stub continuing a collinear line
            marks.append(line_piece(cat, label(r["zone"], "EdgeLine"), r["zone"], "edge_line",
                                    _pt(r, ss["t0"], EDGE_LINE_INSET), _pt(r, ss["t1"], EDGE_LINE_INSET), LINE_HALF,
                                    deck_top + 1.5, deck_top - 0.5, tags))
    # pier service lane: two lines whose inner edges bound the lane exactly
    if lane:
        for k, y in enumerate((lane["y"][0] - LINE_HALF, lane["y"][1] + LINE_HALF)):
            marks.append(line_piece(cat, label("pier", "LaneLine"), "pier", "lane_line", (lane["x"][0], y),
                                    (lane["x"][1], y), LINE_HALF, deck_top + 1.5, deck_top - 0.5, tags))
    # spine lane lines, stopping short of the seaward edge line
    if spine:
        for y in spine["y"]:
            marks.append(line_piece(cat, label("spine", "LaneLine"), "spine", "lane_line", (spine["x"][0], y),
                                    (spine["x"][1], y), LINE_HALF, deck_top + 1.5, deck_top - 0.5, tags))
    # route dashes on the control platform
    for leg in ctrl_route or []:
        (ax, ay), (bx, by) = leg
        L = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / L, (by - ay) / L
        s = DASH_LEN / 2.0
        while s + DASH_LEN / 2.0 <= L:
            c = (ax + ux * s, ay + uy * s)
            marks.append(line_piece(cat, label("control_platform", "RouteDash"), "control_platform", "route_dash",
                                    (c[0] - ux * DASH_LEN / 2.0, c[1] - uy * DASH_LEN / 2.0),
                                    (c[0] + ux * DASH_LEN / 2.0, c[1] + uy * DASH_LEN / 2.0), DASH_HALF_W,
                                    deck_top + 1.5, deck_top - 0.5, tags))
            s += DASH_PERIOD
    # threshold bars in front of the relocated doors
    for d in doors or []:
        marks.append(line_piece(cat, label(d["zone"], "DoorBar"), d["zone"], "door_bar", d["p0"], d["p1"], LINE_HALF,
                                deck_top + 1.5, deck_top - 0.5, tags))
    # no coplanar overlaps: stagger coping tops and mark tops where pieces overlap
    lv = stagger(coping)
    coping = [dict(p, **_restack(cat, p, top=deck_top + COPING_RISE + COPING_STEP * lv[p["label"]]))
              if lv[p["label"]] else p for p in coping]
    lv = stagger(marks, fixed=existing_marks)
    marks = [dict(p, **_restack(cat, p, top=deck_top + 1.5 + MARK_STEP * lv[p["label"]]))
             if lv[p["label"]] else p for p in marks]
    lvf = stagger(fascia)
    fascia = [_refascia(cat, p, lvf[p["label"]]) if lvf[p["label"]] else p for p in fascia]
    return runs, coping, fascia, marks


def _restack(cat, p, top):
    """The same box with a new top (bottom kept)."""
    bottom = p["bottom_z"]
    unit = cat.half(CUBE)
    hz = (top - bottom) / 2.0
    loc = list(p["location"])
    loc[2] = r1(bottom + hz)
    sc = list(p["scale"])
    sc[2] = round(hz / unit[2], 5)
    he = list(p["half_extent"])
    he[2] = r1(hz)
    return {"location": loc, "scale": sc, "half_extent": he, "top_z": r1(top)}


def _refascia(cat, p, level):
    """A fascia whose outer face sits FASCIA_STEP*level closer to the wall, so two fascias
    that overlap at a corner never share a face plane."""
    d = FASCIA_STEP * level
    yaw = math.radians(p["rotation"]["yaw"])
    nx, ny = math.sin(yaw), -math.cos(yaw)            # outward normal of the run the piece was built on
    unit = cat.half(CUBE)
    hy = p["half_extent"][1] - d / 2.0
    loc = [r1(p["location"][0] - nx * d / 2.0), r1(p["location"][1] - ny * d / 2.0), p["location"][2]]
    q = dict(p)
    q["location"] = loc
    q["scale"] = [p["scale"][0], round(hy / unit[1], 5), p["scale"][2]]
    q["half_extent"] = [p["half_extent"][0], r1(hy), p["half_extent"][2]]
    q["footprint"] = [[r1(x), r1(y)] for x, y in obb(loc[0], loc[1], p["half_extent"][0], hy, p["rotation"]["yaw"])]
    return q


def read_pier_audit(path, inv_sha, problems):
    """PF1 refuses to move a pier prop the identity audit has not shown standalone."""
    if not path:
        problems.append("PF1 needs IB_GARRISON_PIER_AUDIT (Scripts/ib_garrison_assembly_audit.py with "
                        "IB_GARRISON_AUDIT_SET=pier)")
        return None
    try:
        a = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as error:
        problems.append("pier audit unreadable: %s" % error)
        return None
    if a.get("status") != "complete" or a.get("set") != "pier":
        problems.append("pier audit is not a complete 'pier' audit (status %s, set %s)" % (a.get("status"), a.get("set")))
    if a.get("source_sha256_before") != inv_sha or a.get("source_sha256_after") != inv_sha:
        problems.append("pier audit was made on another map (%s...)" % str(a.get("source_sha256_before"))[:12])
    out = {"file": str(path), "sha256": file_sha256(Path(path)), "status": a.get("status"), "props": {}}
    for lab in [CRANE_ID[0]] + [t[0] for t in TRUCK_IDS]:
        v = (a.get("verdict") or {}).get(lab) or {}
        out["props"][lab] = {"standalone": v.get("standalone_prop"), "attached": v.get("attached_children"),
                             "attach_parents": v.get("attach_parents"),
                             "referenced_by": v.get("referenced_by_other_actors"),
                             "overlapping_bounds_at_source": v.get("other_actors_overlapping")}
        if v.get("standalone_prop") is not True:
            problems.append("pier audit has not shown %s standalone; it is not moved" % lab)
    return out


def build_plan(inv, facts=None):
    facts = facts or {}
    meta, el, rows, meshes = inv["meta"], inv["elements"], inv["rows"], inv["meshes"]
    problems, decisions, notes = [], [], []
    cat = Catalogue(meshes)
    by_path = {r["path"]: r for r in rows}

    # -- map identity -----------------------------------------------------
    inv_sha = (meta.get("map_file") or {}).get("sha256")
    if not meta.get("map_unchanged"):
        problems.append("the inventory run did not confirm the map unchanged during its own run")
    map_path = PROJECT / MAP_FILE_REL
    live_sha = file_sha256(map_path) if map_path.is_file() else None
    if live_sha is None:
        notes.append("map file not found at %s; the stale-map check runs where the project is" % map_path)
    elif live_sha != inv_sha:
        problems.append("STALE: the map on disk (%s...) is not the map the inventory read (%s...). "
                        "Re-run the inventory." % (live_sha[:8], (inv_sha or "?")[:8]))

    # -- explicit identities ---------------------------------------------
    ident = {}

    def need(key, spec, required=True):
        row, n = resolve(rows, *spec)
        if row is None and required:
            problems.append("identity %s: %d actor(s) match label %r class %s mesh %s"
                            % (key, n, spec[0], spec[1], spec[2]))
        ident[key] = row
        return row

    platform = need("platform", PLATFORM_ID)
    harbor = need("harbor", HARBOR_ID)
    need("water_placeholder", WATER_PLACEHOLDER_ID)
    ship, crane, heli = need("ship", SHIP_ID), need("crane", CRANE_ID), need("helicopter", HELI_ID)
    trucks = [need("truck_%d" % i, spec) for i, spec in enumerate(TRUCK_IDS)]
    anchors = [need(spec[0], spec) for spec in ANCHOR_IDS]
    candidates = [need(spec[0], spec, required=False) for spec in CANDIDATE_IDS]
    broken = [need(spec[0], spec, required=False) for spec in BROKEN_IDS]

    buildings = {}
    for b in el.get("buildings", []):
        if b.get("label") in BUILDING_LABELS:
            if not b.get("resolved") or not b.get("footprint"):
                problems.append("building %s unresolved in the inventory" % b.get("label"))
                continue
            if not b.get("door") or not b["door"].get("consistent"):
                problems.append("building %s has no consistent door by explicit label" % b["label"])
            row = by_path.get(b["path"])
            if row is None or row.get("label") != b["label"]:
                problems.append("building %s path %s not in actors.json" % (b["label"], b.get("path")))
            buildings[b["label"]] = b
    for lab in BUILDING_LABELS:
        if lab not in buildings:
            problems.append("building %s missing from elements.json" % lab)
    if problems and not buildings:
        return {"schema": SCHEMA, "problems": problems, "decisions": decisions, "notes": notes}

    def fp_poly(b):
        f = b["footprint"]
        return obb(f["centre"][0], f["centre"][1], f["half"][0], f["half"][1], f["yaw"])

    bpoly = {lab: fp_poly(b) for lab, b in buildings.items()}

    # -- the platform surface, from its own faces --------------------------
    tris = []
    for a in (inv["faces"].get("actors") or []):
        if platform and a.get("path") == platform["path"]:
            tris = a.get("triangles") or []
    if not tris:
        problems.append("support_faces.json has no triangles for %s" % (platform or {}).get("path"))
        return {"schema": SCHEMA, "problems": problems, "decisions": decisions, "notes": notes}
    faces = Faces(tris)
    flat = {}
    for t in tris:
        if abs(t["nz"]) > 0.99:
            z = round(sum(p[2] for p in t["v"]) / 3.0)
            flat[z] = flat.get(z, 0.0) + abs(area([(p[0], p[1]) for p in t["v"]]))
    levels = sorted(flat)
    deck_top = float(levels[-1])
    apron_z = float(max([z for z in levels if z < deck_top - 100] or [deck_top]))
    bottom = float(min(p[2] for t in tris for p in t["v"]))
    loops = flat_outline(tris, deck_top)
    upper, err = align_loop(loops[0] if loops else None, EXPECTED_UPPER, GEOMETRY_TOLERANCE)
    if upper is None:
        problems.append("the platform's upper deck outline no longer matches the geometry this plan was "
                        "designed on (worst vertex %s cm; tolerance %.0f). Review before planning."
                        % (None if err is None else round(err, 1), GEOMETRY_TOLERANCE))
        return {"schema": SCHEMA, "problems": problems, "decisions": decisions, "notes": notes}
    ramp_tris = [t for t in tris if t.get("up") and 0.9 < abs(t["nz"]) < 0.995
                 and max(p[0] for p in t["v"]) <= min(q[0] for q in upper) + 1.0]
    ramp = None
    if ramp_tris:
        pts = [p for t in ramp_tris for p in t["v"]]
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
        y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
        z_lo = [p[2] for p in pts if abs(p[0] - x0) < 1.0]
        z_hi = [p[2] for p in pts if abs(p[0] - x1) < 1.0]
        ramp = {"x": (x0, x1), "y": (y0, y1), "z": (sum(z_lo) / len(z_lo), sum(z_hi) / len(z_hi))}
        residual = max(abs(p[2] - (ramp["z"][0] + (p[0] - x0) * (ramp["z"][1] - ramp["z"][0]) / (x1 - x0)))
                       for p in pts)
        off = max(abs(ramp[k][i] - EXPECTED_RAMP[k][i]) for k in ("x", "y", "z") for i in (0, 1))
        if residual > 2.0 or off > GEOMETRY_TOLERANCE:
            problems.append("the land ramp is not the planar ramp this plan was designed on "
                            "(residual %.1f cm, offset %.1f cm)" % (residual, off))
    else:
        problems.append("no land ramp faces found landward of the upper deck")
    water_z = float(harbor["loc"][2]) if harbor else None
    if water_z is None:
        problems.append("no harbor surface: the waterline is unknown")
        water_z = -35.0

    # -- frame (validated, not assumed) ------------------------------------
    # Landward is the side the land ramp leaves from (the road in from the city),
    # and the gate must stand on that edge. Image-right is the side the docks are
    # on, because the reference draws the dock and ship on the right.
    gate = buildings.get(GATE_LABEL)
    a2 = area(upper)
    centre = [sum((upper[i - 1][0] + upper[i][0]) * _cross((0, 0), upper[i - 1], upper[i])
                  for i in range(len(upper))) / (6.0 * a2),
              sum((upper[i - 1][1] + upper[i][1]) * _cross((0, 0), upper[i - 1], upper[i])
                  for i in range(len(upper))) / (6.0 * a2)]
    frame_ok = True
    if gate and ship and crane and ramp:
        rx, ry = (ramp["x"][0] + ramp["x"][1]) / 2.0, (ramp["y"][0] + ramp["y"][1]) / 2.0
        dx, dy = rx - centre[0], ry - centre[1]
        land = (-1.0, 0.0) if (abs(dx) >= abs(dy) and dx < 0) else None
        gate_on_edge = abs(gate["footprint"]["centre"][0] - upper[0][0]) < 1500.0
        dock_y = (ship["loc"][1] + crane["loc"][1]) / 2.0
        right = (0.0, -1.0) if dock_y < centre[1] else (0.0, 1.0)
        if land != (-1.0, 0.0) or right != (0.0, -1.0) or not gate_on_edge:
            frame_ok = False
            problems.append("frame: the land ramp, gate and docks no longer put land at -X (gate on that edge) "
                            "and the docks at -Y; the plan's world coordinates would be mirrored or turned")
    else:
        frame_ok = False
        problems.append("frame: the gate, ship, crane or land ramp is missing")

    # -- design -------------------------------------------------------------
    V = upper
    x_rear, x_sea = V[0][0], V[3][0]
    y_min, y_max = V[6][1], V[1][1]
    width = y_max - y_min
    forecourt = dedupe([V[0], V[1], V[2], V[3], (V[3][0], V[6][1]), V[6], V[7], V[8], V[9], V[10]])
    axis_y = r50(y_min + width / 2.0)
    spine_w = r50(RATIO_SPINE_WIDTH * width)
    spine_len = r50(RATIO_SPINE_LENGTH * width)
    pad_a = r50(RATIO_PAD_ACROSS * width / 2.0)
    y_sp0, y_sp1 = axis_y - spine_w / 2.0, axis_y + spine_w / 2.0
    x_sp1 = x_sea + spine_len
    pad_c = (x_sp1 + pad_a, y_sp0 + pad_a)       # the pad's image-right flat continues the channel wall
    spine = rect(x_sea, x_sp1, y_sp0, y_sp1)
    pad = octagon(pad_c[0], pad_c[1], pad_a)
    ctrl_w = r50(RATIO_CONTROL_WIDTH * width)
    x_c0 = x_sea + GAP_CONTROL
    ctrl = chamfered(x_c0, x_sp1, y_sp1, y_sp1 + ctrl_w, {"ur": CONTROL_CHAMFER})
    y_p1 = y_sp0 - GAP_CHANNEL
    y_p0 = y_p1 - PIER_WIDTH
    x_p1 = r50(pad_c[0] + pad_a / 2.0)
    pier = rect(x_sea, x_p1, y_p0, y_p1)
    shapes = {"forecourt": forecourt, "spine": spine, "pad": pad, "control_platform": ctrl, "pier": pier}
    design = {
        "forecourt": {"polygon": forecourt, "seaward_edge_x": x_sea, "width": width,
                      "note": "the existing upper deck at %.0f cm; its diagonal seaward edge is squared off "
                              "at x=%.0f (the old terrace slope becomes deck)" % (deck_top, x_sea)},
        "spine": {"x": [x_sea, x_sp1], "y": [y_sp0, y_sp1], "width": spine_w, "length": spine_len,
                  "axis_y": axis_y},
        "pad": {"centre": list(pad_c), "inradius": pad_a, "across_flats": 2 * pad_a,
                "offset_from_axis": pad_c[1] - axis_y,
                "note": "offset to image-left like the reference, so its image-right flat continues the "
                        "spine's channel wall"},
        "control_platform": {"x": [x_c0, x_sp1], "y": [y_sp1, y_sp1 + ctrl_w], "chamfer": CONTROL_CHAMFER,
                             "gap_to_forecourt": GAP_CONTROL},
        "pier": {"x": [x_sea, x_p1], "y": [y_p0, y_p1], "width": PIER_WIDTH, "channel_to_spine": GAP_CHANNEL},
        "ratios": {"spine_width": RATIO_SPINE_WIDTH, "pad_across": RATIO_PAD_ACROSS,
                   "control_width": RATIO_CONTROL_WIDTH, "hangar_width": RATIO_HANGAR_WIDTH,
                   "spine_length": RATIO_SPINE_LENGTH,
                   "basis": "lateral widths as fractions of the forecourt width, measured off the reference"},
    }

    # -- composition (P3): complete building assemblies onto the control platform -----
    composition, assembly_moves, audit = None, [], None
    if COMPOSITION:
        if COMPOSITION != "P3":
            problems.append("unknown IB_GARRISON_COMPOSITION %r (P3)" % COMPOSITION)
        elif PLATFORM_MODE != "replace":
            problems.append("P3 needs the replace platform mode (the control platform must exist)")
        else:
            audit = read_audit(AUDIT_IN, inv_sha, buildings, problems)
            composition, relocated, assembly_moves = compose_p3(buildings, by_path, design, problems)
            if composition:
                composition["audit"] = audit
                for lab, nb in relocated.items():
                    buildings[lab] = nb
                bpoly = {lab: fp_poly(b) for lab, b in buildings.items()}

    # -- PF1: pier finish on top of P3 ---------------------------------------------
    pier_audit = None
    if FINISH:
        if FINISH != "PF1":
            problems.append("unknown IB_GARRISON_FINISH %r (PF1)" % FINISH)
        elif not composition or PLATFORM_MODE != "replace":
            problems.append("PF1 builds on the P3 composition in replace mode (set IB_GARRISON_COMPOSITION=P3)")
        else:
            pier_audit = read_pier_audit(PIER_AUDIT_IN, inv_sha, problems)

    # -- anchors, doors and what must stay walkable ------------------------------
    anchor_pts = []
    preserved = []           # (name, identity path, polygon, kind)
    for lab, b in sorted(buildings.items()):
        pre = "relocated_" if b.get("relocated") else ""
        preserved.append((lab, b["path"], bpoly[lab], pre + "building"))
        d = b.get("door") or {}
        if d.get("loc"):
            dx, dy = d["loc"][0] - b["footprint"]["centre"][0], d["loc"][1] - b["footprint"]["centre"][1]
            n = math.hypot(dx, dy) or 1.0
            sides = [1.0, -1.0] if lab == GATE_LABEL else [1.0]
            dyaw = (d.get("rot") or {}).get("yaw", 0.0)
            preserved.append((d["label"], d["path"], obb(d["loc"][0], d["loc"][1], 150, 150, dyaw), pre + "door"))
            if lab == GATE_LABEL:
                # A pass-through: its two approaches are along the land road, either side of the gate.
                gx0, gx1, _, _ = bbox(bpoly[lab])
                approaches = [(gx1 + 300.0, d["loc"][1]), (gx0 - 300.0, d["loc"][1])]
            elif b.get("door_normal"):
                # A relocated door: straight out of its facade, along the building's front normal.
                approaches = [(d["loc"][0] + b["door_normal"][0] * DOOR_APPROACH,
                               d["loc"][1] + b["door_normal"][1] * DOOR_APPROACH)]
            else:
                approaches = [(d["loc"][0] + dx / n * DOOR_APPROACH, d["loc"][1] + dy / n * DOOR_APPROACH)]
            for k, (ax, ay) in enumerate(approaches):
                name = "%s approach%s" % (d["label"], "" if len(approaches) == 1 else " %d" % k)
                preserved.append((name, d["path"], rect(ax - 150, ax + 150, ay - 150, ay + 150), pre + "approach"))
                anchor_pts.append((name, ax, ay))
    for row in anchors + [c for c in candidates if c]:
        if not row:
            continue
        o, e = row.get("origin") or row["loc"], row.get("extent") or [100, 100, 100]
        hx, hy = max(e[0], 100.0), max(e[1], 100.0)
        preserved.append((row["label"], row["path"], rect(o[0] - hx, o[0] + hx, o[1] - hy, o[1] + hy),
                          "anchor" if row in anchors else "candidate"))
        if row in anchors:
            anchor_pts.append((row["label"], row["loc"][0], row["loc"][1]))

    # -- hangar reserve: the rearmost clear rectangle on the spine axis ---------
    res_w = r50(RATIO_HANGAR_WIDTH * width)
    ry0, ry1 = axis_y - res_w / 2.0, axis_y + res_w / 2.0
    reserve_basis = None
    if composition and GATE_LABEL in bpoly:
        # P1's safe envelope (provisional, not Connor's hangar size): as wide as the main
        # gate allows (its footprint + CLEAR_BUILDING), mirrored about the spine axis.
        gy1 = bbox(bpoly[GATE_LABEL])[3]
        ry0 = r1(gy1 + CLEAR_BUILDING)
        ry1 = r1(2.0 * axis_y - ry0)
        res_w = r1(ry1 - ry0)
        reserve_basis = {"width": "the main gate's footprint reaches y=%.1f; +%.0f cm clearance gives y=%.1f, "
                                  "mirrored about the spine axis y=%.0f (the reservation stays centred)"
                                  % (gy1, CLEAR_BUILDING, ry0, axis_y),
                         "depth": "from the forecourt's rear edge to PlayerStart - %.0f cm (the spawn point is "
                                  "unchanged in this pass)" % CLEAR_ANCHOR,
                         "status": "PROVISIONAL candidate envelope (P1's safe envelope), not Connor's chosen "
                                   "hangar dimensions; the actual hangar building is Connor's"}
    gate_row = buildings.get(GATE_LABEL)
    gate_door = (gate_row or {}).get("door") or {}
    corridor = None
    if gate_row and gate_door.get("loc"):
        gx1 = bbox(bpoly[GATE_LABEL])[1]
        corridor = rect(gx1, x_sea, gate_door["loc"][1] - 600.0, gate_door["loc"][1] + 600.0)
    blocks = []
    for lab, poly in bpoly.items():
        x0, x1, y0, y1 = bbox(poly)
        blocks.append((lab + " (building + %.0f)" % CLEAR_BUILDING, x0 - CLEAR_BUILDING, x1 + CLEAR_BUILDING,
                       y0 - CLEAR_BUILDING, y1 + CLEAR_BUILDING))
    for name, ax, ay in anchor_pts:
        blocks.append((name + " (+%.0f)" % CLEAR_ANCHOR, ax - CLEAR_ANCHOR, ax + CLEAR_ANCHOR,
                       ay - CLEAR_ANCHOR, ay + CLEAR_ANCHOR))
    if corridor:
        x0, x1, y0, y1 = bbox(corridor)
        blocks.append(("gate road corridor", x0, x1, y0, y1))
    band = [b for b in blocks if b[3] < ry1 and b[4] > ry0]
    step = 10.0
    free = []
    x = x_rear + 1.0
    while x < x_sea:
        clear = all(not (b[1] <= x <= b[2]) for b in band)
        on_deck = all(inside(x, y, forecourt) for y in (ry0 + 1.0, axis_y, ry1 - 1.0))
        if clear and on_deck:
            if free and abs(free[-1][1] - (x - step)) < 1e-6:
                free[-1][1] = x
            else:
                free.append([x, x])
        x += step
    options = []
    for x0, x1 in free:
        # Snap to the exact edge of whatever stopped the sweep.
        e0 = [b for b in band if x0 - step - 1e-6 <= b[2] <= x0 + 1e-6]
        e1 = [b for b in band if x1 - 1e-6 <= b[1] <= x1 + step + 1e-6]
        if e0:
            x0 = max(b[2] for b in e0)
        if e1:
            x1 = min(b[1] for b in e1)
        depth = x1 - x0
        lim0 = [b[0] for b in e0] or ["forecourt edge"]
        lim1 = [b[0] for b in e1] or ["forecourt edge"]
        options.append({"x": [r1(x0), r1(x1)], "y": [ry0, ry1], "depth": r1(depth), "width": res_w,
                        "rear_limited_by": lim0, "front_limited_by": lim1})
    good = [o for o in options if o["depth"] >= RESERVE_MIN_DEPTH]
    reserve = good[0] if good else None
    if reserve and composition and reserve["x"][0] <= x_rear + step + 1e-6:
        # The free run starts at the first sample; the reservation starts at the edge itself.
        reserve["x"][0] = r1(x_rear)
        reserve["depth"] = r1(reserve["x"][1] - reserve["x"][0])
        reserve["rear_limited_by"] = ["the forecourt's rear edge (x=%.0f)" % x_rear]
    if reserve and reserve_basis:
        reserve["basis"] = reserve_basis
        reserve["provisional"] = True
    if reserve is None:
        problems.append("no clear hangar reserve of depth >= %.0f cm on the spine axis" % RESERVE_MIN_DEPTH)
    else:
        rp = rect(reserve["x"][0], reserve["x"][1], ry0, ry1)
        reserve["polygon"] = rp
        reserve["clearances"] = {lab: r1(poly_dist(rp, poly)) for lab, poly in bpoly.items()}
        reserve["anchor_clearances"] = {n: r1(min(seg_dist(ax, ay, rp[i - 1][0], rp[i - 1][1], rp[i][0], rp[i][1])
                                                  for i in range(4)) if not inside(ax, ay, rp) else 0.0)
                                        for n, ax, ay in anchor_pts}
        bad = [lab for lab, d in reserve["clearances"].items() if d < CLEAR_BUILDING - 1]
        bad += [n for n, d in reserve["anchor_clearances"].items() if d < CLEAR_ANCHOR - 1]
        if bad:
            problems.append("hangar reserve violates clearance to: " + ", ".join(bad))
        reserve["alternatives"] = [o for o in good if o is not reserve]
        reserve["mouth"] = "+X (seaward), on the spine axis y=%.0f" % axis_y

    # -- pieces -------------------------------------------------------------
    pieces = []
    replace = PLATFORM_MODE == "replace"
    if PLATFORM_MODE not in ("replace", "keep"):
        problems.append("unknown IB_GARRISON_PLATFORM_MODE %r (replace | keep)" % PLATFORM_MODE)
    if replace:
        pieces += zone_pieces(cat, "forecourt", forecourt, deck_top, bottom, "Forecourt")
        if ramp:
            pieces.append(ramp_piece(cat, ramp, bottom))
        pieces += zone_pieces(cat, "spine", spine, deck_top, bottom, "Spine")
        pieces += zone_pieces(cat, "pad", pad, deck_top, bottom, "Pad")
        pieces += zone_pieces(cat, "control_platform", ctrl, deck_top, bottom, "Control")
        pieces += zone_pieces(cat, "pier", pier, deck_top, bottom, "Pier")
    marks = []
    if reserve:
        rx0, rx1 = reserve["x"]
        hw = RESERVE_MARK_HALF if composition else 15
        for k, (cx, cy, hx, hy) in enumerate((((rx0 + rx1) / 2, ry0 + hw, (rx1 - rx0) / 2, hw),
                                              ((rx0 + rx1) / 2, ry1 - hw, (rx1 - rx0) / 2, hw),
                                              (rx0 + hw, axis_y, hw, res_w / 2), (rx1 - hw, axis_y, hw, res_w / 2))):
            marks.append(mark_piece(cat, "Reserve_Edge_%d" % k, "hangar_reserve", cx, cy, hx, hy, deck_top))
        if composition:
            # A second, thinner line inside the first: reads as a reserved bay from the air.
            ins, ih = RESERVE_INNER_INSET + 2 * hw, 20.0
            ix0, ix1, iy0, iy1 = rx0 + ins, rx1 - ins, ry0 + ins, ry1 - ins
            for k, (cx, cy, hx, hy) in enumerate((((ix0 + ix1) / 2, iy0 + ih, (ix1 - ix0) / 2, ih),
                                                  ((ix0 + ix1) / 2, iy1 - ih, (ix1 - ix0) / 2, ih),
                                                  (ix0 + ih, axis_y, ih, (iy1 - iy0) / 2),
                                                  (ix1 - ih, axis_y, ih, (iy1 - iy0) / 2))):
                marks.append(mark_piece(cat, "Reserve_Inner_%d" % k, "hangar_reserve", cx, cy, hx, hy, deck_top))
    if replace:
        run0 = reserve["x"][1] + 600.0 if reserve else x_rear + 3000.0
        run1 = pad_c[0] - pad_a - 300.0
        n = max(1, int((run1 - run0) // 600.0))
        for k in range(n):
            cx = run0 + (k + 0.5) * (run1 - run0) / n
            marks.append(mark_piece(cat, "Spine_Dash_%02d" % k, "spine", cx, axis_y, 150, 25, deck_top))
        ring_r, segs = 0.7 * pad_a, 32
        chord = 2 * math.pi * ring_r / segs
        for k in range(segs):
            a = 2 * math.pi * k / segs
            marks.append(mark_piece(cat, "Pad_Ring_%02d" % k, "pad", pad_c[0] + ring_r * math.cos(a),
                                    pad_c[1] + ring_r * math.sin(a), chord * 0.55, 20, deck_top,
                                    yaw=math.degrees(a) + 90.0))
    decks = [p for p in pieces if p["collision"] == "BlockAll"]

    # -- piece integrity: no coplanar overlaps, fillers stay inside --------------
    checks = {}
    tier0 = [p for p in decks if p["kind"] == "deck"]
    overl = []
    for i in range(len(tier0)):
        for j in range(i + 1, len(tier0)):
            a0, a1, b0, b1 = bbox(tier0[i]["footprint"])
            c0, c1, d0, d1 = bbox(tier0[j]["footprint"])
            ox, oy = min(a1, c1) - max(a0, c0), min(b1, d1) - max(b0, d0)
            if ox > 0.5 and oy > 0.5:
                overl.append("%s/%s %.0fx%.0f" % (tier0[i]["label"], tier0[j]["label"], ox, oy))
    fill = [p for p in decks if p["kind"] == "filler"]
    union = [shapes[z] for z in ("forecourt", "spine", "pad", "control_platform", "pier")] if replace else []
    fill_out = []
    for p in fill:
        pts = samples_in(p["footprint"], step=100.0, inset=3.0)
        outside = [pt for pt in pts if not any(inside(pt[0], pt[1], u) for u in union)]
        if outside:
            fill_out.append("%s: %d sample(s) outside the design" % (p["label"], len(outside)))
    for i in range(len(fill)):
        for j in range(i + 1, len(fill)):
            if poly_dist(fill[i]["footprint"], fill[j]["footprint"]) == 0.0:
                pts = samples_in(fill[i]["footprint"], step=100.0, inset=3.0)
                if any(inside(x, y, fill[j]["footprint"]) for x, y in pts):
                    fill_out.append("%s overlaps %s" % (fill[i]["label"], fill[j]["label"]))
    cover_miss, cover_extra = 0, 0
    if replace:
        for name, poly in shapes.items():
            for x, y in samples_in(poly, step=100.0, inset=3.0):
                if surface_z(decks, x, y) is None:
                    cover_miss += 1
        allx = [p[0] for s in shapes.values() for p in s]
        ally = [p[1] for s in shapes.values() for p in s]
        for gx in range(int(min(allx)) - 200, int(max(allx)) + 200, 150):
            for gy in range(int(min(ally)) - 200, int(max(ally)) + 200, 150):
                if not any(inside(gx, gy, s) for s in shapes.values()) and \
                        (ramp is None or not (ramp["x"][0] <= gx <= ramp["x"][1] and ramp["y"][0] <= gy <= ramp["y"][1])):
                    z = surface_z(decks, gx, gy)
                    if z is not None:
                        near = min(min(seg_dist(gx, gy, s[i - 1][0], s[i - 1][1], s[i][0], s[i][1])
                                       for i in range(len(s))) for s in shapes.values())
                        if near > 5.0:
                            cover_extra += 1
    checks["pieces"] = {"tier0_overlaps": overl, "fillers": fill_out, "design_samples_uncovered": cover_miss,
                        "samples_covered_outside_design": cover_extra}
    if overl:
        problems.append("coplanar deck pieces overlap: " + "; ".join(overl[:6]))
    if fill_out:
        problems.append("chamfer fillers: " + "; ".join(fill_out[:6]))
    if cover_miss or cover_extra:
        problems.append("decks do not tile the design exactly (%d uncovered, %d outside)"
                        % (cover_miss, cover_extra))

    # -- preservation: every preserved actor keeps its ground ------------------
    # Samples on the old flat deck must keep that exact height. Samples that hung
    # over the old terrace slope (just below the deck) are reported separately:
    # they gain flat support, which is a change but not a loss.
    foot_rows = []
    for name, path, poly, kind in preserved:
        pts = samples_in(poly)
        if kind.startswith("relocated_"):
            # A relocated assembly must stand wholly on the NEW decks, at deck height.
            after = [surface_z(decks, x, y) for x, y in pts]
            full = sum(1 for z in after if z is not None and abs(z - deck_top) <= 0.5)
            on = [z for z in after if z is not None]
            foot_rows.append({"name": name, "identity": path, "kind": kind,
                              "polygon": [[r1(x), r1(y)] for x, y in poly], "samples": len(pts),
                              "supported_after": full, "supported_pct": r1(100.0 * full / float(len(pts) or 1)),
                              "max_dz_to_deck": r1(max(abs(z - deck_top) for z in on)) if on else None})
            if full < len(pts):
                problems.append("relocated %s: %d of %d samples have no deck at z %.0f"
                                % (name, len(pts) - full, len(pts), deck_top))
            continue
        before = [faces.z(x, y) for x, y in pts]
        after = [surface_z(decks, x, y) for x, y in pts] if replace else before
        on_before = [i for i, z in enumerate(before) if z is not None and z >= deck_top - 0.5]
        over_slope = [i for i, z in enumerate(before) if z is None or z < deck_top - 0.5]
        cover = sum(1 for i in on_before if after[i] is not None) / float(len(on_before) or 1)
        dz = max([abs(after[i] - before[i]) for i in on_before if after[i] is not None] or [0.0])
        lost = len(on_before) - sum(1 for i in on_before if after[i] is not None)
        gained = [after[i] for i in over_slope if after[i] is not None]
        row = {"name": name, "identity": path, "kind": kind, "polygon": [[r1(x), r1(y)] for x, y in poly],
               "samples": len(pts),
               "on_deck_before": len(on_before), "kept": r1(100 * cover), "max_dz": r1(dz),
               "lost_samples": lost, "off_deck_before": len(over_slope),
               "off_deck_before_now_supported": len(gained),
               "off_deck_before_z": [r1(min(before[i] for i in over_slope if before[i] is not None)),
                                     r1(max(before[i] for i in over_slope if before[i] is not None))]
               if any(before[i] is not None for i in over_slope) else None}
        foot_rows.append(row)
        if lost or dz > SUPPORT_TOLERANCE:
            problems.append("preservation: %s loses ground (%d of %d deck samples) or moves %.1f cm"
                            % (name, lost, len(on_before), dz))
        if over_slope and kind == "building":
            notes.append("%s: %d of %d footprint samples were not on the old flat deck (old surface %s); "
                         "%d of them are on the new deck at %.0f" % (name, len(over_slope), len(pts),
                                                                   row["off_deck_before_z"], len(gained),
                                                                   deck_top))
    checks["footprints"] = foot_rows
    # Everything that stood on the old deck must still be on deck: new decks must
    # not cut into a preserved footprint either (seaward pieces only).
    intr = []
    for p in decks:
        if p["zone"] in ("forecourt", "land_ramp"):
            continue
        for name, path, poly, kind in preserved:
            if kind in ("building", "anchor", "candidate") and poly_dist(p["footprint"], poly) == 0.0:
                intr.append("%s overlaps %s" % (p["label"], name))
    if intr:
        problems.append("new decks overlap preserved actors: " + "; ".join(intr[:6]))

    # -- paths ---------------------------------------------------------------
    gdoor = gate_door.get("loc") or [0.0, 0.0]
    gx0, gx1 = (bbox(bpoly[GATE_LABEL])[:2]) if GATE_LABEL in bpoly else (0.0, 0.0)
    ps = anchors[0]["loc"] if anchors and anchors[0] else [x_rear + 5000.0, axis_y]
    hub = ((reserve["x"][1] if reserve else x_rear) + x_sea) / 2.0
    paths = [
        ("city road -> land ramp -> gate", [(ramp["x"][0] + 50 if ramp else -3450.0, gdoor[1]),
                                            (gx0 - 300.0, gdoor[1]), (gdoor[0], gdoor[1])]),
        ("gate -> forecourt -> spine -> pad", [(gdoor[0], gdoor[1]), (gx1 + 300.0, gdoor[1]),
                                               (hub, gdoor[1]), (hub, axis_y), (x_sea, axis_y), pad_c]),
        ("hangar mouth -> spine", [((reserve["x"][1] if reserve else hub) + 50.0, axis_y), (x_sp1, axis_y)]),
        ("PlayerStart -> spine", [(ps[0], ps[1]), (x_sea + 1000.0, ps[1])]),
        ("spine -> control platform", [((x_c0 + x_sp1) / 2.0, axis_y), ((x_c0 + x_sp1) / 2.0,
                                                                       y_sp1 + ctrl_w / 2.0)]),
        ("forecourt -> pier -> end", [(x_sea - 1500.0, (y_p0 + y_p1) / 2.0), (x_p1 - 300.0, (y_p0 + y_p1) / 2.0)]),
    ]
    if not replace:
        # keep mode builds no seaward structure, so only forecourt paths apply
        paths = [p for p in paths if p[0].startswith("city road")]
    relocated_names = set(n for n, _, _, k in preserved if k == "relocated_approach")
    for name, ax, ay in anchor_pts:
        if name in relocated_names:
            continue          # routed over the spine below; never a stale path to an old door
        paths.append(("forecourt -> " + name, [(hub, axis_y), (hub, ay), (ax, ay)]))
    path_rows = []
    for name, pts in paths:
        smp = polyline_samples(pts)
        after = [surface_z(decks, x, y) for x, y in smp] if replace else [faces.z(x, y) for x, y in smp]
        before = [faces.z(x, y) for x, y in smp]
        missing = sum(1 for z in after if z is None)
        steps = [abs(after[i] - after[i - 1]) for i in range(1, len(after))
                 if after[i] is not None and after[i - 1] is not None]
        bsteps = [abs(before[i] - before[i - 1]) for i in range(1, len(before))
                  if before[i] is not None and before[i - 1] is not None]
        row = {"path": name, "points": [[r1(x), r1(y)] for x, y in pts], "samples": len(smp),
               "no_ground_after": missing,
               "max_step_after": r1(max(steps or [0.0])), "max_step_before": r1(max(bsteps or [0.0])),
               "z_after": [r1(min(z for z in after if z is not None)) if missing < len(after) else None,
                           r1(max(z for z in after if z is not None)) if missing < len(after) else None],
               "z_before": [r1(min(z for z in before if z is not None)) if any(before) else None,
                            r1(max(z for z in before if z is not None)) if any(before) else None]}
        path_rows.append(row)
        if missing or row["max_step_after"] > 10.0:
            problems.append("path '%s': %d sample(s) without ground, largest step %.1f cm"
                            % (name, missing, row["max_step_after"]))
    checks["paths"] = path_rows

    # -- gaps: open water, nothing standing in it -------------------------------
    gaps = []
    if replace:
        gap_specs = [
            ("channel (spine/pad <-> pier)", rect(x_sea + 1.0, x_p1, y_p1 + 1.0, y_sp0 - 1.0)),
            ("control gap (forecourt <-> control platform)",
             rect(x_sea + 1.0, x_c0 - 1.0, y_sp1 + 1.0, y_sp1 + ctrl_w)),
        ]
        moved_paths = set(r["path"] for r in [ship, crane, heli] + trucks if r)
        skip = set(r["path"] for r in (platform, harbor, ident.get("water_placeholder")) if r) | moved_paths
        for name, poly in gap_specs:
            deck_hits = sum(1 for x, y in samples_in(poly, step=100.0) if surface_z(decks, x, y) is not None)
            old = sum(1 for x, y in samples_in(poly, step=100.0) if faces.z(x, y) is not None
                      and faces.z(x, y) > water_z)
            intruders = []
            gx0_, gx1_, gy0_, gy1_ = bbox(poly)
            for r in rows:
                if r["path"] in skip or str(r.get("hidden")) == "True":
                    continue
                o, e = r.get("origin"), r.get("extent")
                if not o or not e or max(e) <= 0 or max(e[:2]) > 50000:
                    continue
                if o[2] + e[2] <= water_z + 1.0:
                    continue
                if o[0] + e[0] > gx0_ and o[0] - e[0] < gx1_ and o[1] + e[1] > gy0_ and o[1] - e[1] < gy1_:
                    intruders.append("%s (%s)" % (r["label"], r["path"].split(".")[-1]))
            gaps.append({"gap": name, "polygon": poly, "width": r1(min(bbox(poly)[1] - bbox(poly)[0],
                                                                        bbox(poly)[3] - bbox(poly)[2])),
                         "new_deck_samples": deck_hits, "old_platform_samples_above_water": old,
                         "actors_standing_in_it": intruders})
            if deck_hits:
                problems.append("gap %s has deck in it" % name)
            if intruders:
                problems.append("gap %s has actors in it: %s" % (name, ", ".join(intruders[:6])))
    checks["gaps"] = gaps

    # Water behaviour, from the harbor mesh's own collision geometry. A mesh set
    # to CTF_USE_DEFAULT inherits the project's DefaultShapeComplexity, which only
    # the engine can resolve (plain Python leaves it unknown). What happens to a
    # player is EXPECTED behaviour from code and data until it is seen in play.
    hmc, hcol = None, None
    for w in el.get("water", []) or []:
        if harbor and w.get("path") == harbor["path"]:
            hmc, hcol = w.get("mesh_collision") or {}, w.get("collision") or {}
    hmc = hmc or {}
    own_flag = str(hmc.get("collision_trace_flag") or "")
    own = own_flag.split(".")[-1].split(":")[0].strip("<> ") if own_flag else None
    default = facts.get("default_shape_complexity")
    effective = (default if own == "CTF_USE_DEFAULT" else own) if own else None
    count = hmc.get("simple_collision_count")
    count_ok = isinstance(count, int) and not isinstance(count, bool) and count >= 0
    comp_blocks = "ECR_BLOCK" in str(hcol.get("response_pawn")) and "NO_COLLISION" not in str(hcol.get("enabled"))
    basis = "own flag %s%s, %s simple shape(s)" % (own, (" -> project default %s" % default)
                                                   if own == "CTF_USE_DEFAULT" else "", count if count_ok else "unknown")
    if not comp_blocks:
        blocks = False
    elif effective == "CTF_USE_COMPLEX_AS_SIMPLE":
        blocks = True
    elif effective in ("CTF_USE_SIMPLE_AND_COMPLEX", "CTF_USE_SIMPLE_AS_COMPLEX") and count_ok:
        blocks = count > 0
    else:
        blocks = None
    if blocks is True:
        water = ("EXPECTED WALKABLE WATER (%s): %s blocks pawn sweeps at z %.0f, so a player who steps into a gap "
                 "would land on the water plane %.0f cm below the deck and Drown() (capsule centre below %.0f) "
                 "would not fire. Not observed in play." % (basis, HARBOR_ID[0], water_z, deck_top - water_z,
                                                           water_z))
    elif blocks is False:
        water = ("EXPECTED REAL WATER (%s): pawn sweeps pass through %s, so a player who steps into a gap is "
                 "expected to fall through the plane and be snapped back by Drown() once the capsule centre "
                 "passes z %.0f. Expected from code and collision data; not yet observed in play."
                 % (basis, HARBOR_ID[0], water_z))
    else:
        water = ("UNKNOWN (%s): whether %s stops a walking pawn depends on %s. A gap is proposed appearance, "
                 "not verified behaviour." % (basis, HARBOR_ID[0],
                                              "the project's DefaultShapeComplexity, unresolved without the engine"
                                              if own == "CTF_USE_DEFAULT" and not default else
                                              "collision data this inventory could not read"))
    checks["water_behaviour"] = water
    checks["water_collision"] = {"own_flag": own, "project_default": default, "effective": effective,
                                 "simple_shapes": count if count_ok else None, "component_blocks_pawn": comp_blocks,
                                 "blocks_pawn_sweeps": blocks}

    # -- moves: site props that would otherwise float --------------------------
    moves = []
    prop_targets = []

    def local_box(row):
        mc = (el.get("site_prop_meshes") or {}).get(row.get("mesh")) or {}
        lo, hi = mc.get("local_min"), mc.get("local_max")
        return (lo, hi) if lo and hi else (None, None)

    def world_fp(row, loc, yaw):
        lo, hi = local_box(row)
        if lo is None:
            return None
        s = row["scale"]
        cx, cy = (lo[0] + hi[0]) / 2.0 * s[0], (lo[1] + hi[1]) / 2.0 * s[1]
        hx, hy = (hi[0] - lo[0]) / 2.0 * abs(s[0]), (hi[1] - lo[1]) / 2.0 * abs(s[1])
        a = math.radians(yaw)
        wx = loc[0] + cx * math.cos(a) - cy * math.sin(a)
        wy = loc[1] + cx * math.sin(a) + cy * math.cos(a)
        return obb(wx, wy, hx, hy, yaw)

    def add_move(row, role, to_loc, to_yaw, why, target_kind):
        rot = dict(row["rot"])
        rot["yaw"] = round(to_yaw, 4)
        moves.append({"identity": row["path"], "label": row["label"], "class": row["class"], "role": role,
                      "from": {"loc": row["loc"], "rot": row["rot"], "scale": row["scale"]},
                      "to": {"loc": [r1(v) for v in to_loc], "rot": rot, "scale": row["scale"]},
                      "why": why, "target": target_kind})

    if replace and frame_ok:
        ship_fp = None
        if ship:
            lo, hi = local_box(ship)
            if lo is None:
                problems.append("ship: no local mesh bounds in the inventory (its world box is inflated by "
                                "its 45-degree yaw), so the hull cannot be berthed without guessing. Re-run "
                                "Scripts/ib_inventory_garrison.py (revision 2 records them).")
            else:
                s = ship["scale"]
                hx, hy = (hi[0] - lo[0]) / 2.0 * s[0], (hi[1] - lo[1]) / 2.0 * s[1]
                long_x = hx >= hy
                yaw = 0.0 if long_x else -90.0          # long axis parallel to the pier, nearest current yaw
                half_len, half_beam = (hx, hy) if long_x else (hy, hx)
                cx_w = x_p1 - 600.0 - half_len
                cy_w = y_p0 - FENDER - half_beam
                a = math.radians(yaw)
                lcx, lcy = (lo[0] + hi[0]) / 2.0 * s[0], (lo[1] + hi[1]) / 2.0 * s[1]
                locx = cx_w - (lcx * math.cos(a) - lcy * math.sin(a))
                locy = cy_w - (lcx * math.sin(a) + lcy * math.cos(a))
                locz = water_z - SHIP_DRAFT - lo[2] * s[2]
                add_move(ship, "berth", [locx, locy, locz], yaw,
                         "sat on the old concrete apron (bottom at z %.0f, %.0f cm above the water); berthed "
                         "outboard of the pier, long axis along it, hull bottom %.0f cm below the waterline "
                         "(draft is a visual call)" % (ship["loc"][2] + lo[2] * s[2],
                                                        ship["loc"][2] + lo[2] * s[2] - water_z, SHIP_DRAFT),
                         "water")
                ship_fp = world_fp(ship, [locx, locy, locz], yaw)
                decisions.append("Ship draft: hull bottom set %.0f cm under the waterline; the hull mesh's "
                                 "real waterline is unknown. Adjust z after a look." % SHIP_DRAFT)
        if crane:
            lo, hi = local_box(crane)
            if FINISH:
                yaw = crane["rot"]["yaw"] + PF_CRANE_TURN     # PF1: its long mesh box along the pier
            else:
                yaw = crane["rot"]["yaw"] + 45.0      # the dock line turns from -45 to 0; keep the crane square to it
            if lo is None:
                problems.append("crane: no local mesh bounds in the inventory; re-run the inventory")
            else:
                s = crane["scale"]
                along = [m for m in moves if m["label"] == SHIP_ID[0]]
                cx_t = along[0]["to"]["loc"][0] if along else (x_sea + x_p1) / 2.0
                fp0 = world_fp(crane, [0.0, 0.0, 0.0], yaw)
                fx0, fx1, fy0, fy1 = bbox(fp0)
                span = fy1 - fy0
                if FINISH:
                    ty = y_p0 + COPING_IN + CRANE_EDGE_KEEP - fy0   # against the berth edge's coping
                elif span <= PIER_WIDTH - 200.0:
                    ty = y_p0 + 100.0 - fy0            # 1 m inside the outboard (berth) edge
                else:
                    ty = (y_p0 + y_p1) / 2.0 - (fy0 + fy1) / 2.0
                    if span > PIER_WIDTH:
                        decisions.append("Crane: its mesh box is %.0f cm across the pier (pier %.0f); it is "
                                         "centred and overhangs both edges. Check its legs in the viewport."
                                         % (span, PIER_WIDTH))
                tx = cx_t - (fx0 + fx1) / 2.0
                add_move(crane, "pier crane", [tx, ty, deck_top + (crane["loc"][2] - apron_z)], yaw,
                         ("stood on the old apron; PF1: on the pier abreast of the berthed ship, turned to lie along "
                          "the pier (yaw %.0f) against its berth edge, so one straight service lane runs past it"
                          % yaw) if FINISH else
                         "stood on the old apron; re-homed onto the pier abreast of the berthed ship, turned "
                         "with the dock line (+45)", "deck")
        # Trucks: same yaw, same order along x, in a row on the pier's inboard half,
        # in the first slots from the pier root that keep 3 m clear of the crane.
        crane_fp = None
        for m in moves:
            if m["label"] == CRANE_ID[0]:
                crane_fp = world_fp(crane, m["to"]["loc"], m["to"]["rot"]["yaw"])
        live_trucks = sorted([t for t in trucks if t], key=lambda t: t["loc"][0])
        slot = 0
        for t in live_trucks:
            e = t.get("extent") or [277.0, 141.0, 140.0]
            while True:
                to = [x_sea + 1200.0 + 800.0 * slot, y_p1 - (PF_TRUCK_EDGE_KEEP if FINISH else 250.0) - e[1],
                      deck_top + (t["loc"][2] - apron_z)]
                slot += 1
                fp_t = rect(to[0] - e[0], to[0] + e[0], to[1] - e[1], to[1] + e[1])
                if to[0] + e[0] > x_p1 - 300.0:
                    problems.append("no room on the pier for %s" % t["label"])
                    to = None
                    break
                if crane_fp is None or poly_dist(fp_t, crane_fp) >= 300.0:
                    break
            if to:
                add_move(t, "pier dressing", to, t["rot"]["yaw"],
                         "stood on the old apron at z %.0f, which becomes water; re-homed onto the pier, "
                         "same yaw, same height above its deck%s"
                         % (apron_z, (", its box %.0f cm from the channel edge (P3: 250) to widen the service lane"
                                      % PF_TRUCK_EDGE_KEEP) if FINISH else ""), "deck")
        if heli:
            o = heli.get("origin") or heli["loc"]
            dx, dy = pad_c[0] - o[0], pad_c[1] - o[1]
            add_move(heli, "pad", [heli["loc"][0] + dx, heli["loc"][1] + dy,
                                   heli["loc"][2] + (deck_top - apron_z)], heli["rot"]["yaw"],
                     "stood on the old apron lobe at z %.0f; centred on the new pad and raised %.0f cm to its "
                     "deck, rotation kept (it has roll %.1f in the map)" % (apron_z, deck_top - apron_z,
                                                                           heli["rot"].get("roll", 0.0)),
                     "deck")
        if heli:
            roll = float(heli["rot"].get("roll", 0.0))
            lo, hi = local_box(heli)
            if abs(roll) > 2.0 or (lo and heli["loc"][2] < apron_z - 100.0):
                decisions.append("Helicopter: roll %.1f deg and pivot z %.0f, %.0f cm below the apron it stands on "
                                 "(part of it sits inside the old platform). Deliberately downed prop or a "
                                 "misplaced import? The plan keeps its pose relative to its deck; owner call."
                                 % (roll, heli["loc"][2], apron_z - heli["loc"][2]))
        # Target checks.
        for m in moves:
            row = by_path.get(m["identity"])
            if m["label"] == HELI_ID[0]:
                o, e = row.get("origin"), row.get("extent")
                d = [m["to"]["loc"][k] - m["from"]["loc"][k] for k in range(3)]
                fp = rect(o[0] + d[0] - e[0], o[0] + d[0] + e[0], o[1] + d[1] - e[1], o[1] + d[1] + e[1])
            else:
                fp = world_fp(row, m["to"]["loc"], m["to"]["rot"]["yaw"])
                if fp is None and row.get("extent"):
                    e = row["extent"]
                    fp = rect(m["to"]["loc"][0] - e[0], m["to"]["loc"][0] + e[0],
                              m["to"]["loc"][1] - e[1], m["to"]["loc"][1] + e[1])
            m["target_footprint"] = [[r1(x), r1(y)] for x, y in fp] if fp else None
            if not fp:
                continue
            pts = samples_in(fp)
            zs = [surface_z(decks, x, y) for x, y in pts]
            on = sum(1 for z in zs if z is not None)
            m["target_support_pct"] = r1(100.0 * on / len(pts))
            if m["target"] == "deck" and m["label"] != CRANE_ID[0] and on < len(pts):
                problems.append("%s target is not fully on deck (%.0f%%)" % (m["label"], m["target_support_pct"]))
            if m["target"] == "deck" and m["label"] == CRANE_ID[0] and m["target_support_pct"] < 60.0:
                problems.append("crane target has too little deck under it (%.0f%%)" % m["target_support_pct"])
            if m["target"] == "water" and on:
                problems.append("%s target overlaps deck (%d samples)" % (m["label"], on))
            for name, path, poly, kind in preserved:
                if kind in ("building", "anchor", "candidate", "relocated_building") and poly_dist(fp, poly) == 0.0:
                    problems.append("%s target overlaps %s" % (m["label"], name))
            prop_targets.append((m["label"], fp))
        for i in range(len(prop_targets)):
            for j in range(i + 1, len(prop_targets)):
                if poly_dist(prop_targets[i][1], prop_targets[j][1]) == 0.0:
                    pair = (prop_targets[i][0], prop_targets[j][0])
                    if CRANE_ID[0] in pair and SHIP_ID[0] in pair:
                        decisions.append("Crane and ship boxes overlap in plan (a crane boom over a berthed "
                                         "ship is normal); confirm visually")
                    else:
                        problems.append("targets overlap: %s / %s" % pair)

    # -- PF1: the pier's service lane (between the crane and the trucks, from their boxes) --
    pier_lane = None
    if FINISH == "PF1" and composition and replace:
        pier_props = [CRANE_ID[0]] + [t[0] for t in TRUCK_IDS]
        g = service_lane(pier, [(lab, fp) for lab, fp in prop_targets if lab in pier_props], COPING_IN)
        if g is None:
            problems.append("PF1: no straight lane along the pier")
        else:
            gw = g[1] - g[0]
            w = min(LANE_WIDTH, gw - 2.0 * LANE_BUFFER)
            c = (g[0] + g[1]) / 2.0
            pier_lane = {"x": [r1(x_sea), r1(x_p1 - EDGE_LINE_INSET - LINE_HALF)], "y": [r1(c - w / 2.0), r1(c + w / 2.0)],
                         "width": r1(w), "centre_y": r1(c), "clear_band": [r1(g[0]), r1(g[1])], "clear_width": r1(gw),
                         "bounded_by": [g[2], g[3]], "buffers": [r1(c - w / 2.0 - g[0]), r1(g[1] - c - w / 2.0)],
                         "to_pier_edges": [r1(c - w / 2.0 - y_p0), r1(y_p1 - c - w / 2.0)],
                         "basis": "obstacle boxes (mesh bounds at the target transforms), conservative; the engine "
                                  "lane scan measures the real collision"}
            if w < LANE_MIN:
                problems.append("PF1: the pier lane is only %.0f cm wide (< %.0f): %s / %s" % (w, LANE_MIN, g[2], g[3]))

    # -- P3: pawn routes and the composition's own checks -------------------------------
    routes = None
    if composition:
        moves += assembly_moves
        walk_polys = [shapes[z] for z in ("forecourt", "spine", "pad", "control_platform", "pier")]
        obstacles = [(lab, poly) for lab, poly in bpoly.items()] + [(lab, fp) for lab, fp in prop_targets]
        for row in [anchors[1] if len(anchors) > 1 else None] + [c for c in candidates if c]:
            if row:       # the weapon rack and the unresolved Cube actors; PlayerStart is a spawn point
                o, e = row.get("origin") or row["loc"], row.get("extent") or [100, 100, 100]
                hx, hy = max(e[0], 100.0), max(e[1], 100.0)
                obstacles.append((row["label"], rect(o[0] - hx, o[0] + hx, o[1] - hy, o[1] + hy)))
        grid = RouteGrid(walk_polys, obstacles)
        cpz = design["control_platform"]
        appr = {n: (ax, ay) for n, ax, ay in anchor_pts}
        mh_fp = composition["buildings"]["Mess_Hall"]["footprint"]
        mh_x1 = max(q[0] for q in mh_fp)
        spine_entry = (x_sea + 800.0, axis_y)
        apron_goal = ((mh_x1 + cpz["x"][1]) / 2.0, cpz["y"][0] + 600.0)
        pad_goals = [(pad_c[0] + 0.62 * pad_a * math.cos(a), pad_c[1] + 0.62 * pad_a * math.sin(a))
                     for a in (math.pi / 2, -math.pi / 2, 0.0, math.pi / 4, -math.pi / 4)]
        pier_y = (y_p0 + y_p1) / 2.0
        specs = [
            ("forecourt|spine: PlayerStart -> spine", "forecourt|spine", (ps[0], ps[1]), [spine_entry]),
            ("spine|pad: spine -> pad deck beside the helicopter", "spine|pad", spine_entry, pad_goals),
        ]
        if pier_lane:
            ly = pier_lane["centre_y"]
            specs += [("forecourt|pier: forecourt -> pier end along the service lane", "forecourt|pier",
                       (x_sea - 1500.0, ly), [(x_p1 - 300.0, ly)]),
                      ("pier|forecourt: pier end -> forecourt along the service lane", "pier|forecourt",
                       (x_p1 - 300.0, ly), [(x_sea - 1500.0, ly)])]
        else:
            specs.append(("forecourt|pier: forecourt -> pier end past the crane and trucks", "forecourt|pier",
                          (x_sea - 1500.0, pier_y), [(x_p1 - 300.0, pier_y)]))
        specs += [
            ("spine|control: spine -> control platform apron", "spine|control", spine_entry, [apron_goal]),
            ("spine -> Command_DoorFrame approach", "entrance", spine_entry, [appr.get("Command_DoorFrame approach")]),
            ("spine -> Mess_Hall_DoorFrame approach", "entrance", spine_entry,
             [appr.get("Mess_Hall_DoorFrame approach")]),
            ("hangar reservation mouth -> spine", "reserve", ((reserve or {}).get("x", [0, x_rear + 3000.0])[1] + 400.0,
                                                               axis_y), [spine_entry]),
        ]
        routes = []
        for name, kind, start, goals in specs:
            pts, info, used = None, {}, None
            for goal in goals:
                if goal is None:
                    continue
                pts, info = grid.route(start, goal)
                if pts:
                    used = goal
                    break
            row = {"name": name, "crosses": kind, "start": [r1(start[0]), r1(start[1])],
                   "goal": [r1(used[0]), r1(used[1])] if used else None, "waypoints": pts, "routing": info}
            if pts:
                smp = polyline_samples([tuple(q) for q in pts])
                zs = [surface_z(decks, x, y) for x, y in smp]
                d, near = grid.clearance(pts)
                row.update({"length_m": r1(sum(math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1])
                                               for k in range(1, len(pts))) / 100.0),
                            "samples": len(smp), "no_ground": sum(1 for z in zs if z is None),
                            "z": [r1(min(z for z in zs if z is not None)), r1(max(z for z in zs if z is not None))]
                            if any(z is not None for z in zs) else None,
                            "min_clearance_to_obstacles_cm": r1(d), "nearest_obstacle": near})
                if row["no_ground"]:
                    problems.append("route '%s': %d sample(s) without deck" % (name, row["no_ground"]))
            elif kind in ("entrance", "spine|control"):
                problems.append("route '%s': %s" % (name, info.get("why")))
            else:
                # Bounding boxes are conservative (a gantry crane's box includes the space between its
                # legs): keep the straight line and let the engine sweeps and PIE report what is there.
                goal = [g for g in goals if g][0]
                row["waypoints"] = [[r1(start[0]), r1(start[1])], [r1(goal[0]), r1(goal[1])]]
                row["goal"] = row["waypoints"][-1]
                row["routing"] = dict(info, fallback="straight line: the planning grid (bounding boxes inflated "
                                                     "by %.0f cm) finds no way past; tested in the engine" % ROUTE_CLEAR)
                smp = polyline_samples([tuple(q) for q in row["waypoints"]])
                row["samples"] = len(smp)
                row["no_ground"] = sum(1 for x, y in smp if surface_z(decks, x, y) is None)
                d, near = grid.clearance(row["waypoints"])
                row["min_clearance_to_obstacles_cm"], row["nearest_obstacle"] = r1(d), near
                row["length_m"] = r1(math.hypot(goal[0] - start[0], goal[1] - start[1]) / 100.0)
                decisions.append("'%s': no pawn-width way past the obstacles' bounding boxes on the plan grid; the "
                                 "straight line is tested with the pawn profile in the engine instead." % name)
            routes.append(row)
        # Composition checks: support, spacing, margins, entrances, the reservation's apron.
        comp = composition
        for lab in ("Command", "Mess_Hall"):
            b = comp["buildings"][lab]
            fp = bpoly[lab]
            fr = next((r for r in foot_rows if r["name"] == lab), {})
            others = {o: r1(poly_dist(fp, q)) for o, q in bpoly.items() if o != lab}
            b["supported_pct"] = fr.get("supported_pct")
            b["clearance_to_buildings"] = others
            b["platform_edge_margins"] = {"rear (control gap)": r1(min(q[0] for q in fp) - cpz["x"][0]),
                                          "seaward": r1(cpz["x"][1] - max(q[0] for q in fp)),
                                          "spine seam": r1(min(q[1] for q in fp) - cpz["y"][0]),
                                          "outer": r1(cpz["y"][1] - max(q[1] for q in fp))}
            a = appr.get(b["door_label"] + " approach")
            b["approach"] = [r1(a[0]), r1(a[1])] if a else None
            b["approach_on_deck"] = bool(a) and surface_z(decks, a[0], a[1]) is not None
            b["approach_clear_for_a_pawn"] = bool(a) and bool(grid.ok(grid.i(a[0]), grid.j(a[1])))
            b["door_faces"] = {(1.0, 0.0): "+X (seaward apron)", (0.0, -1.0): "-Y (the spine)",
                               (-1.0, 0.0): "-X (control gap)", (0.0, 1.0): "+Y (outer edge)"}.get(
                (round(b["door_normal"][0]), round(b["door_normal"][1])), str(b["door_normal"]))
            for o, dd in others.items():
                if o not in P3_ASSEMBLIES and dd < CLEAR_BUILDING - 1:
                    problems.append("P3: %s within %.0f cm of %s" % (lab, dd, o))
            if not b["approach_on_deck"] or not b["approach_clear_for_a_pawn"]:
                problems.append("P3: %s's door approach %s is not clear deck for a pawn" % (lab, b["approach"]))
        walk = r1(poly_dist(bpoly["Mess_Hall"], bpoly["Command"]))
        comp["walkway"] = {"between": ["Mess_Hall (back)", "Command (side)"], "width_cm": walk,
                           "target_cm": P3_WALKWAY}
        if walk < P3_WALKWAY - 1:
            problems.append("P3: walkway between Mess_Hall and Command is %.0f cm (< %.0f)" % (walk, P3_WALKWAY))
        if reserve:
            ax0, ax1 = reserve["x"][1], x_sea
            narrow, intr = None, {}
            x = ax0
            while x <= ax1:
                cuts = []
                for lab, poly in bpoly.items():
                    ys = []
                    for q in range(len(poly)):
                        (xa, ya), (xb, yb) = poly[q - 1], poly[q]
                        if (xa > x) != (xb > x):
                            ys.append(ya + (x - xa) * (yb - ya) / (xb - xa))
                    if len(ys) >= 2 and max(ys) > ry0 and min(ys) < ry1:
                        cuts.append((max(min(ys), ry0), min(max(ys), ry1)))
                        intr[lab] = intr.get(lab, 0) + 1
                free, yy = [], ry0
                for c0, c1 in sorted(cuts):
                    if c0 > yy:
                        free.append(c0 - yy)
                    yy = max(yy, c1)
                if yy < ry1:
                    free.append(ry1 - yy)
                w = max(free) if free else 0.0
                if narrow is None or w < narrow[0]:
                    narrow = (w, x)
                x += 100.0
            comp["reserve_apron"] = {
                "band": {"x": [r1(ax0), r1(ax1)], "y": [ry0, ry1]},
                "meaning": "the straight approach from the reservation's mouth to the spine, as wide as the reservation",
                "buildings_reaching_into_it": sorted(intr), "narrowest_clear_width_cm": r1(narrow[0]) if narrow else None,
                "narrowest_at_x": r1(narrow[1]) if narrow else None,
                "spawn_point_in_it": "PlayerStart at %s, %.0f cm in front of the mouth (unchanged; not an obstacle)"
                                     % ([r1(v) for v in ps[:2]], ps[0] - reserve["x"][1])}
            comp["reserve"] = {"x": reserve["x"], "y": [ry0, ry1], "depth_m": r1(reserve["depth"] / 100.0),
                               "width_m": r1(res_w / 100.0), "basis": reserve.get("basis"),
                               "occupants_before_the_move": (audit or {}).get("zones", {}).get("provisional rear reserve")}
        if pier_lane:
            # the route Codex walked through the 7 m passage (fixed waypoints, not planned)
            pts = [[10982.0, 3750.0], [13900.0, 5850.0], [14100.0, 7300.0], [11300.0, 7300.0]]
            smp = polyline_samples([tuple(q) for q in pts])
            zs = [surface_z(decks, x, y) for x, y in smp]
            d, near = grid.clearance(pts)
            routes.append({"name": "passage: spine -> apron -> 7 m passage (Codex's waypoints)", "crosses": "passage",
                           "start": pts[0], "goal": pts[-1], "waypoints": pts, "routing": {"fixed": True},
                           "length_m": r1(sum(math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1])
                                              for k in range(1, len(pts))) / 100.0),
                           "samples": len(smp), "no_ground": sum(1 for z in zs if z is None),
                           "z": [r1(min(z for z in zs if z is not None)), r1(max(z for z in zs if z is not None))],
                           "min_clearance_to_obstacles_cm": r1(d), "nearest_obstacle": near})
            if routes[-1]["no_ground"]:
                problems.append("PF1: Codex's passage route leaves the deck")
        comp["routes"] = [r["name"] for r in routes]
        for r in routes:
            if r.get("waypoints"):
                smp = polyline_samples([tuple(q) for q in r["waypoints"]])
                zs = [surface_z(decks, x, y) for x, y in smp]
                steps_ = [abs(zs[k] - zs[k - 1]) for k in range(1, len(zs)) if zs[k] is not None and zs[k - 1] is not None]
                checks["paths"].append({"path": "route: " + r["name"], "points": r["waypoints"], "samples": len(smp),
                                        "no_ground_after": sum(1 for z in zs if z is None),
                                        "max_step_after": r1(max(steps_ or [0.0])), "max_step_before": None,
                                        "z_after": r.get("z"), "z_before": None})

    # -- PF1: quay finish on the new decks and its checks ---------------------------------
    finish, finish_pieces = None, []
    if FINISH == "PF1" and composition and replace and routes is not None:
        comp = composition
        mh_fp, cmd_fp = comp["buildings"]["Mess_Hall"]["footprint"], comp["buildings"]["Command"]["footprint"]
        cpz = design["control_platform"]
        xa = (max(q[0] for q in mh_fp) + cpz["x"][1]) / 2.0                 # the apron between Mess_Hall and the sea
        y_pass = (max(q[1] for q in mh_fp) + min(q[1] for q in cmd_fp)) / 2.0
        cmd = comp["buildings"]["Command"]
        y_cmd = cmd["to"]["door_loc"][1]
        x_cmd_face = max(q[0] for q in cmd_fp)
        ctrl_route = [((xa, cpz["y"][0] + 100.0), (xa, y_cmd)), ((xa, y_cmd), (x_cmd_face + 180.0, y_cmd)),
                      ((xa, y_pass), (cpz["x"][0] + 300.0, y_pass))]
        doors = []
        for lab in ("Mess_Hall", "Command"):
            b = comp["buildings"][lab]
            dl, nn = b["to"]["door_loc"], b["door_normal"]
            face = max((q[0] - dl[0]) * nn[0] + (q[1] - dl[1]) * nn[1] for q in b["footprint"])
            cx, cy = dl[0] + nn[0] * (face + 50.0), dl[1] + nn[1] * (face + 50.0)
            px, py = -nn[1], nn[0]
            doors.append({"zone": "control_platform", "building": lab,
                          "p0": (cx - px * 150.0, cy - py * 150.0), "p1": (cx + px * 150.0, cy + py * 150.0)})
        spine_lines = {"x": [x_sea, x_sp1 - EDGE_LINE_INSET - 2.0 * LINE_HALF],
                       "y": [axis_y - SPINE_LANE_HALF, axis_y + SPINE_LANE_HALF]}
        fshapes = {z: shapes[z] for z in ("forecourt", "spine", "pad", "control_platform", "pier")}
        runs, cop, fas, fmarks = build_finish(cat, fshapes, deck_top, water_z, pier_lane, spine_lines, ctrl_route,
                                              doors, marks)
        pier_props_all = [CRANE_ID[0]] + [t[0] for t in TRUCK_IDS]
        finish_pieces = cop + fas + fmarks
        fchk = {}
        # 1. every coping sits on its deck (inboard strip) with its lip over water; every marking on a deck
        bad_cop = []
        for p, r in zip(cop, runs):
            mid = (r["t0"] + r["t1"]) / 2.0
            on = _pt(r, mid, COPING_IN / 2.0)
            off = _pt(r, mid, -COPING_LIP / 2.0)
            if not inside(on[0], on[1], shapes[r["zone"]]) or any(inside(off[0], off[1], sh) for sh in fshapes.values()):
                bad_cop.append(p["label"])
        off_deck = []
        for p in fmarks:
            for x, y in samples_in(p["footprint"], step=100.0, inset=2.0):
                if not any(inside(x, y, sh) for sh in fshapes.values()):
                    off_deck.append(p["label"])
                    break
        fchk["coping_on_deck"] = {"pieces": len(cop), "not_on_deck_or_lip_not_over_water": bad_cop}
        fchk["markings_on_deck"] = {"pieces": len(fmarks), "off_deck": off_deck}
        if bad_cop or off_deck:
            problems.append("PF1: finish off its deck: %s" % ", ".join((bad_cop + off_deck)[:6]))
        # 2. joins stay flush: coping (the only raised finish) only where a join meets the water
        wet_segs = [(_pt(r, r["t0"]), _pt(r, r["t1"])) for r in runs]
        joins = {}
        for z in FINISH_ZONES:
            PP = ccw(shapes[z])
            for i in range(len(PP)):
                a, b, L, u, nn = _edge(PP, i)
                t = 5.0
                while t < L:
                    x, y = a[0] + u[0] * t, a[1] + u[1] * t
                    other = _zone_at(x + nn[0] * 3.0, y + nn[1] * 3.0, fshapes, z)
                    if other:
                        key = " | ".join(sorted((z, other)))
                        j = joins.setdefault(key, {"samples": 0, "under_coping": 0, "under_coping_away_from_water": 0})
                        j["samples"] += 1
                        px, py = x - nn[0] * 1.0, y - nn[1] * 1.0
                        if any(inside(px, py, p["footprint"]) for p in cop):
                            j["under_coping"] += 1
                            dw = min(seg_dist(px, py, s0[0], s0[1], s1[0], s1[1]) for s0, s1 in wet_segs)
                            if dw > COPING_IN + COPING_LIP + 1.0:
                                j["under_coping_away_from_water"] += 1
                    t += 10.0
        fchk["joins"] = joins
        away = sum(j["under_coping_away_from_water"] for j in joins.values())
        if away:
            problems.append("PF1: coping crosses a deck join away from the water (%d samples)" % away)
        # 3. doors and their approaches, routes, lane, helicopter
        blockers = [p for p in finish_pieces if p["collision"] == "BlockAll"]
        near_doors = []
        for name, path, poly, kind in preserved:
            if kind.endswith("approach") or kind.endswith("door"):
                for p in blockers:
                    if poly_dist(p["footprint"], poly) == 0.0:
                        near_doors.append("%s / %s" % (p["label"], name))
        fchk["door_approaches_clear_of_coping"] = not near_doors
        if near_doors:
            problems.append("PF1: coping in a door or its approach: " + "; ".join(near_doors[:6]))
        rclear = []
        for r in routes:
            if not r.get("waypoints"):
                continue
            dmin, who = float("inf"), None
            for x, y in polyline_samples([tuple(q) for q in r["waypoints"]], step=25.0):
                for p in blockers:
                    fp = p["footprint"]
                    d = 0.0 if inside(x, y, fp) else min(seg_dist(x, y, fp[q - 1][0], fp[q - 1][1], fp[q][0], fp[q][1])
                                                         for q in range(len(fp)))
                    if d < dmin:
                        dmin, who = d, p["label"]
            rclear.append({"route": r["name"], "min_distance_to_coping_cm": r1(dmin), "nearest": who})
        fchk["routes_vs_coping"] = rclear
        lane_poly = rect(pier_lane["x"][0], pier_lane["x"][1], pier_lane["y"][0], pier_lane["y"][1]) if pier_lane else None
        if lane_poly:
            obst = [(lab, fp) for lab, fp in prop_targets] + [(p["label"], p["footprint"]) for p in blockers]
            ld = sorted((r1(poly_dist(lane_poly, fp)), lab) for lab, fp in obst)
            fchk["lane_clearances_cm"] = ld[:8]
            if ld and ld[0][0] < LANE_BUFFER - 1.0:
                problems.append("PF1: the lane is %.0f cm from %s (< %.0f)" % (ld[0][0], ld[0][1], LANE_BUFFER))
            # the lane's own painted lines (outside the lane) keep clear of the props too
            lines = [p for p in fmarks if p["kind"] == "lane_line" and p["zone"] == "pier"]
            lcl = sorted((r1(poly_dist(p["footprint"], fp)), p["label"], lab) for p in lines
                         for lab, fp in prop_targets if lab in pier_props_all)
            fchk["lane_line_clearances_cm"] = lcl[:6]
            if lcl and lcl[0][0] < LANE_LINE_KEEP:
                problems.append("PF1: lane line %s is %.0f cm from %s (< %.0f)" % (lcl[0][1], lcl[0][0], lcl[0][2],
                                                                                   LANE_LINE_KEEP))
        heli_fp = [fp for lab, fp in prop_targets if lab == HELI_ID[0]]
        if heli_fp:
            fchk["helicopter_to_nearest_coping_cm"] = r1(min(poly_dist(p["footprint"], heli_fp[0]) for p in blockers))
        bfp = {lab: poly for lab, poly in bpoly.items()}
        fchk["buildings_to_nearest_coping_cm"] = {lab: r1(min(poly_dist(p["footprint"], poly) for p in blockers))
                                                  for lab, poly in sorted(bfp.items())}
        hit_b = [lab for lab, dd in fchk["buildings_to_nearest_coping_cm"].items() if dd == 0.0]
        if hit_b:
            problems.append("PF1: coping touches " + ", ".join(hit_b))
        # 4. no coplanar overlaps left (coping tops, marking tops incl. P3's markings, fascia faces)
        def coplanar(group, key, fixed=()):
            out = []
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    if abs(key(group[i]) - key(group[j])) < 0.05 and obb_overlap(group[i]["footprint"], group[j]["footprint"]):
                        out.append("%s/%s" % (group[i]["label"], group[j]["label"]))
            for p in group:
                for q in fixed:
                    if abs(key(p) - key(q)) < 0.05 and obb_overlap(p["footprint"], q["footprint"]):
                        out.append("%s/%s" % (p["label"], q["label"]))
            return out
        cp = coplanar(cop, lambda p: p["top_z"]) + coplanar(fmarks, lambda p: p["top_z"], fixed=marks)
        cp += coplanar(fas, lambda p: p["half_extent"][1])
        fchk["coplanar_overlaps"] = cp
        fchk["preexisting_p3_marking_overlaps"] = coplanar(marks, lambda p: p["top_z"])
        if cp:
            problems.append("PF1: coplanar overlaps: " + "; ".join(cp[:6]))
        kinds = {}
        for p in finish_pieces:
            k = "%s %s" % (p["zone"], p["kind"])
            kinds[k] = kinds.get(k, 0) + 1
        finish = {"name": "PF1", "revision": PF_REVISION, "tag": FINISH_TAG, "pier_audit": pier_audit, "lane": pier_lane,
                  "revision_note": "r2: markings 40 cm (r1: 20 cm lines, 30 cm dashes, unreadable overhead); trucks' "
                                   "boxes %.0f cm from the channel edge (r1/P3: 250) so the lane lines keep clear of "
                                   "the crane and trucks" % PF_TRUCK_EDGE_KEEP,
                  "materials": {"coping": COPING_MATERIAL, "fascia": FASCIA_MATERIAL, "markings": MARK_MATERIAL},
                  "collision": {"coping": "BlockAll: a walkable curb %.0f cm high (under the pawn's %.0f cm step)"
                                          % (COPING_RISE, 45.0),
                                "fascia": "NoCollision: facing on the quay wall below the deck (the deck box blocks)",
                                "markings": "NoCollision: paint"},
                  "dimensions": {"coping": "%.0f cm on the deck + %.0f cm lip over the face, top +%.0f cm, face %.0f cm"
                                           % (COPING_IN, COPING_LIP, COPING_RISE, COPING_DROP + COPING_RISE),
                                 "fascia": "%.0f cm proud of the quay face, from %.0f cm below the waterline to the "
                                           "coping" % (FASCIA_OUT, FASCIA_BELOW_WATER),
                                 "edge_line": "%.0f cm, centred %.0f cm inboard of every water edge"
                                              % (2 * LINE_HALF, EDGE_LINE_INSET),
                                 "lane_lines": "%.0f cm; inner edges on the lane's edges" % (2 * LINE_HALF),
                                 "route_dashes": "%.0f x %.0f cm every %.0f cm" % (DASH_LEN, 2 * DASH_HALF_W, DASH_PERIOD),
                                 "door_bars": "300 x %.0f cm, centred 50 cm in front of each relocated building's "
                                              "door face" % (2 * LINE_HALF)},
                  "water_edges": [{"zone": r["zone"], "edge": r["edge"],
                                   "from": [r1(v) for v in _pt(r, r["t0"])], "to": [r1(v) for v in _pt(r, r["t1"])],
                                   "length_cm": r1(r["t1"] - r["t0"]), "ends": r["ends"]} for r in runs],
                  "control_route": [[[r1(v) for v in a], [r1(v) for v in b]] for a, b in ctrl_route],
                  "door_bars": [{"building": d["building"], "p0": [r1(v) for v in d["p0"]], "p1": [r1(v) for v in d["p1"]]}
                                for d in doors],
                  "spine_lines_y": spine_lines["y"],
                  "counts": kinds, "pieces": len(finish_pieces), "checks": fchk}

    # -- seawalls and the harbor limits ---------------------------------------
    walls = el.get("seawalls") or [
        {"label": r["label"], "path": r["path"], "origin": r.get("origin"), "extent": r.get("extent")}
        for r in rows if r["class"] == "StaticMeshActor" and str(r["label"]).startswith("Seawall_")]
    wall_d = []
    for w in walls:
        o, e = w.get("origin"), w.get("extent")
        if not o or not e:
            continue
        wp = rect(o[0] - e[0], o[0] + e[0], o[1] - e[1], o[1] + e[1])
        d = min([poly_dist(p["footprint"], wp) for p in decks] + [poly_dist(fp, wp) for _, fp in prop_targets]
                or [float("inf")])
        wall_d.append({"seawall": w["label"], "min_clearance": r1(d) if d != float("inf") else None})
        if d < SEAWALL_CLEARANCE:
            problems.append("new work within %.0f cm of %s" % (d, w["label"]))
    checks["seawalls"] = wall_d

    # -- leftovers from older passes -------------------------------------------
    left = [r["label"] for r in rows if any(str(r.get("label", "")).startswith(p) for p in OLD_LABEL_PREFIXES)
            or any(t in str(r.get("tags")) for t in OLD_RUN_TAGS)]
    ours = [r["label"] for r in rows if RUN_TAG in str(r.get("tags"))]
    if left:
        problems.append("actors from an older layout pass are in the map: " + ", ".join(left[:8]))
    checks["existing_generated"] = {"older_pass": left, "this_pass": ours}

    # -- the old platform -----------------------------------------------------
    treatment = None
    if replace and platform:
        pc = (el.get("platform") or {}).get("collision") or {}
        live_before = facts.get("platform_live")
        if live_before:
            inv_before = {"component_visible": pc.get("visible"), "actor_hidden": str(platform.get("hidden")) == "True",
                          "profile": pc.get("profile"),
                          "collision_enabled": str(pc.get("enabled")).split(".")[-1].split(":")[0].strip("<> ")}
            drift = ["%s: inventory %s, live %s" % (k, inv_before[k], live_before.get(k)) for k in inv_before
                     if inv_before[k] != live_before.get(k)]
            if drift:
                problems.append("platform state differs from the inventory: " + "; ".join(drift))
        treatment = {
            "identity": platform["path"], "label": platform["label"],
            "before": {"component_visible": pc.get("visible"), "actor_hidden": platform.get("hidden"),
                       "collision_enabled": pc.get("enabled"), "profile": pc.get("profile")},
            "before_live": live_before,
            "after": {"component_visible": False, "actor_hidden": True, "collision_enabled": "NO_COLLISION",
                      "actor_collision": False},
            "why": "the new decks are the ground; the old slab would fill every gap the reference shows, "
                   "and hiding it with collision left on would leave an invisible platform across them",
            "revert": "IB_GARRISON_APPLY=1 IB_GARRISON_REVERT=1 on the same target restores every captured flag "
                      "exactly, after a read-only check that nothing has changed since the apply",
            "order": "applied LAST, after every new deck has been created and verified",
        }
        apron_loops = flat_outline(tris, apron_z) or []
        apron_area = sum(abs(area(L)) for L in apron_loops)
        notes.append("old platform: upper deck %.0f m2 at z %.0f and apron %.0f m2 at z %.0f. New decks: "
                     "%.0f m2, all at z %.0f; everything else inside the old outline becomes open water"
                     % (abs(area(V)) / 1e4, deck_top, apron_area / 1e4, apron_z,
                        sum(abs(area(s)) for s in shapes.values()) / 1e4, deck_top))

    # -- held, with reasons -----------------------------------------------------
    held = []
    for lab, b in sorted(buildings.items()):
        if b.get("relocated"):
            continue          # moved with its door as one assembly (see moves)
        held.append({"identity": b["path"], "label": lab, "why": "Shane's building: unchanged transform; stays "
                     "on the forecourt at its own height"})
        if b.get("door"):
            held.append({"identity": b["door"]["path"], "label": b["door"]["label"],
                         "why": "door of %s by its own label; unchanged" % lab})
    for row in anchors:
        if row:
            held.append({"identity": row["path"], "label": row["label"], "why": "gameplay anchor; unchanged"})
    for row in candidates:
        if row:
            held.append({"identity": row["path"], "label": row["label"],
                         "why": "inside Barracks' footprint with no label/folder/attachment tying it to the "
                                "building: association unresolved, so it is neither moved nor adopted"})
    for row in broken:
        if row:
            held.append({"identity": row["path"], "label": row["label"],
                         "why": "renders nothing (no mesh or no bounds): owner decision; left where it is"})
    for row in (harbor, ident.get("water_placeholder")):
        if row:
            held.append({"identity": row["path"], "label": row["label"], "why": "water; unchanged"})
    for w in walls:
        held.append({"identity": w["path"], "label": w["label"], "why": "harbor seawall; unchanged"})
    if not replace:
        for row in [ship, crane, heli] + trucks:
            if row:
                held.append({"identity": row["path"], "label": row["label"], "why": "keep mode: ground unchanged"})

    # -- decisions for Connor / owners -----------------------------------------
    if reserve:
        decisions.append("Hangar reserve is %.0f x %.0f cm (depth x width), limited at the rear by %s and at the "
                         "front by %s. Moving PlayerStart forward would let it run to %s."
                         % (reserve["depth"], reserve["width"], ", ".join(reserve["rear_limited_by"]),
                            ", ".join(reserve["front_limited_by"]),
                            ("x=%.0f" % reserve["alternatives"][0]["x"][1]) if reserve.get("alternatives")
                            else "the next obstacle"))
    if composition:
        decisions.append("P3 candidate: the hangar RESERVATION now runs from the rear edge, centred on the spine "
                         "(%s). Its size is P1's safe envelope, provisional: the gate sets the width, PlayerStart "
                         "the depth. The actual hangar building and its dimensions are Connor's; nothing is built."
                         % ("%.1f m deep x %.1f m wide" % (reserve["depth"] / 100.0, res_w / 100.0) if reserve else "none"))
    else:
        decisions.append("The reference's rear hangar sits on the rear edge; here Command and Mess_Hall already hold "
                         "the rear edge, so the reserve is directly in front of them, on the spine axis.")
    decisions.append("The land road enters at the hangar's image-right (the gate's existing position); the "
                     "reference draws it at image-left. Kept, because the gate is Shane's.")
    if composition:
        decisions.append("P3 candidate: Command (the tower, %.0f m) stands at the control platform's rear-outer corner "
                         "with its door still facing the seaward apron; Mess_Hall (the low block, %.0f m) lines the "
                         "platform's spine edge, turned so its door opens onto the spine; %.0f m between them. Both "
                         "moved as complete assemblies with their own door frames (identity audit: nothing else "
                         "attached, inside or referencing them). A layout proposal for Connor, and Shane's buildings."
                         % (composition["buildings"]["Command"]["height_m"],
                            composition["buildings"]["Mess_Hall"]["height_m"], P3_WALKWAY / 100.0))
    else:
        decisions.append("The reference's control platform carries a tower and a low block. Command is the site's "
                         "tower but stays in the forecourt; the platform is built empty for whatever Connor puts there.")
    decisions.append("Walkability of water gaps: see water_behaviour. Changing it (a drown volume, edge rails, or "
                     "the harbor mesh's collision) is a gameplay decision outside this pass.")
    decisions.append("No NavMeshBoundsVolume/RecastNavMesh exists in this level before or after the pass.")

    mapping = [
        {"reference": "rear hangar (top centre, mech in the bay)",
         "plan": "RESERVED, not built: %s" % ("x %s y %s, mouth +X on the spine axis" % (reserve["x"], reserve["y"])
                                               if reserve else "no clear site"),
         "existing": ("P3: Command and Mess_Hall moved to the control platform; the rear edge is the reservation's"
                      if composition else "nothing moved; Command and Mess_Hall stay on the rear edge behind it")},
        {"reference": "rear service forecourt with service buildings",
         "plan": "the existing upper deck at z %.0f, seaward edge squared at x=%.0f" % (deck_top, x_sea),
         "existing": ("Barracks (image-right), Armory and Medical (image-left), SM_MainGate_Tripo (land gate, rear "
                      "image-right), PlayerStart, BP_WeaponRack: unchanged; Command and Mess_Hall moved (P3)"
                      if composition else
                      "Barracks (image-right), Armory and Medical (image-left), Command and Mess_Hall (rear), "
                      "SM_MainGate_Tripo (land gate, rear image-right), PlayerStart, BP_WeaponRack: all unchanged")},
        {"reference": "land road entering beside the hangar",
         "plan": "the existing land ramp, rebuilt at its exact slope" if replace else "unchanged",
         "existing": "city ramp -> SM_MainGate_Tripo; enters at the hangar's image-right, the reference's "
                     "image-left (kept: the gate is Shane's)"},
        {"reference": "central spine", "plan": "x %s y %s" % ([x_sea, x_sp1], [y_sp0, y_sp1]),
         "existing": "none (old terrace slope and apron become water or deck)"},
        {"reference": "forward chamfered pad", "plan": "octagon centre %s, %.0f across flats"
                                                       % ([r1(v) for v in pad_c], 2 * pad_a),
         "existing": "Helicopter re-homed onto it (it stood on the old round apron lobe)"},
        {"reference": "left control platform (tower + low block)",
         "plan": "x %s y %s, %.0f cm of water to the forecourt" % ([x_c0, x_sp1], [y_sp1, y_sp1 + ctrl_w],
                                                                   GAP_CONTROL),
         "existing": ("P3: Command (tower, rear-outer corner, door to the seaward apron) and Mess_Hall (low block "
                      "along the spine edge, door to the spine), %.0f m walkway between them" % (P3_WALKWAY / 100.0)
                      if composition else "built empty; Command (the tower) stays in the forecourt")},
        {"reference": "right pier with the ship berthed outboard",
         "plan": "x %s y %s, %.0f cm channel to the spine" % ([x_sea, x_p1], [y_p0, y_p1], GAP_CHANNEL),
         "existing": "Docks_Ship_Hull berthed outboard; Docks_Crane_01 and the four trucks re-homed onto it"},
        {"reference": "water between the pier, spine and control platform",
         "plan": "real gaps (old platform hidden with collision off)" if replace else "NOT produced in keep mode",
         "existing": "see water_behaviour for what a player finds there"},
    ]
    frame = {"deep": [-1.0, 0.0], "right": [0.0, -1.0], "depth": r1(pad_c[0] + pad_a - x_rear),
             "width": r1(width), "front": [r1(pad_c[0] + pad_a), axis_y],
             "centre": [r1((pad_c[0] + pad_a + x_rear) / 2.0), axis_y], "landward": "-X",
             "handedness": "image-right = -Y (docks side)", "seaward": "+X",
             "platform_path": (platform or {}).get("path")}
    hashes = {}
    for key, row in (("platform", platform), ("ship", ship), ("crane", crane), ("helicopter", heli)):
        f = package_file((row or {}).get("mesh"))
        if f is not None and f.is_file():
            hashes[row["mesh"]] = file_sha256(f)
    for lab, b in buildings.items():
        f = package_file(b.get("mesh"))
        if f is not None and f.is_file():
            hashes[b["mesh"]] = file_sha256(f)

    plan = {
        "schema": SCHEMA, "level": LEVEL, "reference": REFERENCE, "run_tag": RUN_TAG, "run_folder": RUN_FOLDER,
        "engine_facts": facts,
        "platform_mode": PLATFORM_MODE, "created_utc": STARTED, "engine": ENGINE,
        "map": {"sha256": inv_sha, "file_now": live_sha, "inventory": str(INV),
                "inventory_started_utc": meta.get("started_utc")},
        "package_hashes": hashes,
        "frame": frame, "deck_z": deck_top, "apron_z": apron_z, "bottom_z": bottom, "water_z": water_z,
        "site": {"upper_outline": V, "ramp": ramp, "levels_m2": {str(k): round(v / 1e4) for k, v in flat.items()}},
        "design": design, "reference_mapping": mapping, "hangar_reserve": reserve, "reserve_options": options,
        "pieces": pieces + marks + finish_pieces, "moves": moves, "platform_treatment": treatment, "held": held,
        "checks": checks, "decisions": decisions, "notes": notes, "problems": problems,
        "counts": {"deck_pieces": len([p for p in pieces if p["kind"] in ("deck", "ramp")]),
                   "filler_pieces": len([p for p in pieces if p["kind"] == "filler"]),
                   "markings": len(marks), "moves": len(moves), "held": len(held)},
    }
    if composition:
        plan["composition"] = composition
        plan["routes"] = routes
        plan["counts"]["assembly_moves"] = len(assembly_moves)
    if FINISH:
        plan["finish"] = finish
        plan["pier_lane"] = pier_lane
        plan["counts"]["finish_pieces"] = len(finish_pieces)
    return plan


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def fmt(v):
    if v is None:
        return ""
    if isinstance(v, dict):
        return "roll %.2f pitch %.2f yaw %.2f" % (v.get("roll", 0.0), v.get("pitch", 0.0), v.get("yaw", 0.0))
    return " ".join("%.1f" % float(x) for x in v)


def write_manifest(plan):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["op", "zone_or_role", "label", "identity", "class", "from_loc", "from_rot", "from_scale",
                "to_loc", "to_rot", "to_scale", "mesh", "material", "collision", "notes"])
    for p in plan.get("pieces", []):
        w.writerow(["create", p["zone"], p["label"], ("(generated, tags %s)" % ", ".join([RUN_TAG] + p["tags"]))
                    if p.get("tags") else "(generated, tag %s)" % RUN_TAG, "StaticMeshActor",
                    "", "", "", fmt(p["location"]), fmt(p["rotation"]), fmt(p["scale"]), p["mesh"],
                    p["material"], p["collision"], "%s; top %.1f bottom %.1f" % (p["kind"], p["top_z"], p["bottom_z"])])
    for m in plan.get("moves", []):
        w.writerow(["move", m["role"], m["label"], m["identity"], m["class"], fmt(m["from"]["loc"]),
                    fmt(m["from"]["rot"]), fmt(m["from"]["scale"]), fmt(m["to"]["loc"]), fmt(m["to"]["rot"]),
                    fmt(m["to"]["scale"]), "", "", "", m["why"]])
    t = plan.get("platform_treatment")
    if t:
        w.writerow(["hide+no-collision", "old platform", t["label"], t["identity"], "StaticMeshActor", "", "", "",
                    "", "", "", "", "", "NO_COLLISION", t["why"] + "; " + t["order"]])
    for h in plan.get("held", []):
        w.writerow(["hold", "", h["label"], h["identity"], "", "", "", "", "", "", "", "", "", "", h["why"]])
    return write_bytes(OUT / "manifest.csv", buf.getvalue())


def write_report(plan, engine_result=None):
    L = ["CARROW GATE GARRISON -- %s (%s)" % ("PF1 PIER FINISH CANDIDATE PLAN (on P3)" if plan.get("finish")
                                               else "P3 COMPOSITION CANDIDATE PLAN" if plan.get("composition")
                                               else "CURRENT-BASELINE STRUCTURAL PLAN", SCHEMA),
         "mode: %s, platform mode %s, %s" % (
             "REVERT" if REVERT else "APPLY + SAVE" if SAVE else "APPLY (no save)" if APPLY else "PLAN ONLY (read-only)",
             plan.get("platform_mode"), "engine" if ENGINE else "plain Python (engine checks not run)"),
         "reference: " + REFERENCE,
         "map sha256 (inventory): %s   on disk now: %s" % ((plan.get("map") or {}).get("sha256"),
                                                          (plan.get("map") or {}).get("file_now")), ""]
    if "design" not in plan:
        L += ["PLAN NOT BUILT"] + ["  " + p for p in plan.get("problems", [])]
        write_bytes(OUT / "report.txt", "\n".join(L) + "\n")
        return
    d, r = plan["design"], plan.get("hangar_reserve")
    L += ["FRAME  land -X, sea +X, image-right -Y (docks side); deck top %.0f, apron %.0f, water %.0f, bottom %.0f"
          % (plan["deck_z"], plan["apron_z"], plan["water_z"], plan["bottom_z"]), "",
          "STRUCTURE (world cm)",
          "  rear service forecourt  existing upper deck, seaward edge squared at x=%.0f, width %.0f"
          % (d["forecourt"]["seaward_edge_x"], d["forecourt"]["width"]),
          "  hangar reserve          %s" % ("x %s y %s (depth %.0f, width %.0f), mouth %s -- OUTLINE ONLY"
                                            % (r["x"], r["y"], r["depth"], r["width"], r["mouth"]) if r else "NONE"),
          "  central spine           x %s y %s (width %.0f, length %.0f)"
          % (d["spine"]["x"], d["spine"]["y"], d["spine"]["width"], d["spine"]["length"]),
          "  forward chamfered pad   octagon centre %s, %.0f across flats (offset %+.0f from the axis)"
          % ([r1(v) for v in d["pad"]["centre"]], d["pad"]["across_flats"], d["pad"]["offset_from_axis"]),
          "  left control platform   x %s y %s, %.0f water to the forecourt"
          % (d["control_platform"]["x"], d["control_platform"]["y"], d["control_platform"]["gap_to_forecourt"]),
          "  right pier              x %s y %s, %.0f channel to the spine"
          % (d["pier"]["x"], d["pier"]["y"], d["pier"]["channel_to_spine"]), ""]
    if plan.get("platform_mode") == "keep":
        L.append("  (keep mode: only the hangar reserve outline is built; the seaward structure above is the design")
        L.append("   the replace mode would build, shown for reference)")
        L.append("")
    L.append("REFERENCE -> PLAN -> EXISTING")
    for m in plan.get("reference_mapping", []):
        L.append("  %s" % m["reference"])
        L.append("      plan: %s" % m["plan"])
        L.append("      existing: %s" % m["existing"])
    L.append("")
    c = plan["counts"]
    L.append("PIECES  %d deck/ramp boxes, %d chamfer fillers (1 cm under), %d markings (no collision)"
             % (c["deck_pieces"], c["filler_pieces"], c["markings"]))
    pk = plan["checks"].get("pieces", {})
    L.append("  coplanar overlaps %d, filler issues %d, design samples uncovered %d, covered outside %d"
             % (len(pk.get("tier0_overlaps", [])), len(pk.get("fillers", [])),
                pk.get("design_samples_uncovered", 0), pk.get("samples_covered_outside_design", 0)))
    L += ["", "PRESERVED GROUND (before = old platform faces, after = new decks)"]
    for f in plan["checks"].get("footprints", []):
        if f["kind"].startswith("relocated_"):
            L.append("  %-30s %-18s on the new deck %5.1f%% of %4d samples, max dz to deck %s cm"
                     % (f["name"][:30], f["kind"], f["supported_pct"], f["samples"], f["max_dz_to_deck"]))
            continue
        L.append("  %-30s %-9s kept %5.1f%% of %4d deck samples, max dz %.1f cm"
                 % (f["name"][:30], f["kind"], f["kept"], f["on_deck_before"], f["max_dz"]))
    L += ["", "PATHS (after: ground at every 50 cm sample, largest step)"]
    for p in plan["checks"].get("paths", []):
        if p["max_step_before"] is None:
            L.append("  %-44s missing %d  step %.1f  z after %s  (a P3 route; no 'before')"
                     % (p["path"][:44], p["no_ground_after"], p["max_step_after"], p["z_after"]))
            continue
        L.append("  %-44s missing %d  step %.1f  z after %s  (before %s, step %.1f)"
                 % (p["path"][:44], p["no_ground_after"], p["max_step_after"], p["z_after"], p["z_before"],
                    p["max_step_before"]))
    L += ["", "GAPS"]
    for g in plan["checks"].get("gaps", []):
        L.append("  %-46s width %.0f  new deck samples %d  old platform samples %d  actors in it: %s"
                 % (g["gap"], g["width"], g["new_deck_samples"], g["old_platform_samples_above_water"],
                    ", ".join(g["actors_standing_in_it"]) or "none"))
    L.append("  " + plan["checks"].get("water_behaviour", ""))
    L += ["", "MOVES (absolute source and target, keyed by full actor path)"]
    for m in plan.get("moves", []):
        L.append("  %-16s %-14s %s -> %s  yaw %.1f -> %.1f  support at target %s%%"
                 % (m["label"], m["role"], fmt(m["from"]["loc"]), fmt(m["to"]["loc"]), m["from"]["rot"]["yaw"],
                    m["to"]["rot"]["yaw"], m.get("target_support_pct")))
    t = plan.get("platform_treatment")
    if t:
        L += ["", "OLD PLATFORM  %s: hidden, collision off, %s" % (t["label"], t["order"]), "  " + t["why"],
              "  " + t["revert"]]
    comp = plan.get("composition")
    if comp:
        L += ["", "COMPOSITION P3 (candidate; a layout proposal, not reference acceptance)"]
        au = comp.get("audit") or {}
        L.append("  identity audit %s (sha256 %s...): %s" % (au.get("file"), str(au.get("sha256"))[:12],
                 "; ".join("%s complete=%s" % (k, v.get("complete")) for k, v in (au.get("assemblies") or {}).items())))
        for lab, b in comp["buildings"].items():
            L.append("  %-9s (%s, %.1f m) %s yaw %.1f -> %s yaw %.1f (turned %+.0f); door %s -> %s, faces %s"
                     % (lab, b["reads_as"], b["height_m"], fmt(b["from"]["loc"]), b["from"]["yaw"], fmt(b["to"]["loc"]),
                        b["to"]["yaw"], b["rotation_delta"], fmt(b["from"]["door_loc"]), fmt(b["to"]["door_loc"]),
                        b.get("door_faces")))
            L.append("            on deck %s%%; edge margins %s; approach %s (on deck %s, pawn-clear %s)"
                     % (b.get("supported_pct"), b.get("platform_edge_margins"), b.get("approach"),
                        b.get("approach_on_deck"), b.get("approach_clear_for_a_pawn")))
        w = comp.get("walkway") or {}
        L.append("  walkway %s: %.0f cm (target %.0f)" % (" / ".join(w.get("between", [])), w.get("width_cm", 0),
                                                           w.get("target_cm", 0)))
        rv, ap = comp.get("reserve") or {}, comp.get("reserve_apron") or {}
        if rv:
            L.append("  reservation x %s y %s = %.1f m deep x %.1f m wide -- %s"
                     % (rv["x"], rv["y"], rv["depth_m"], rv["width_m"], (rv.get("basis") or {}).get("status")))
            for k in ("width", "depth"):
                L.append("    %s: %s" % (k, (rv.get("basis") or {}).get(k)))
        if ap:
            L.append("  apron to the spine: narrowest clear %.0f cm at x %.0f; buildings reaching in: %s; %s"
                     % (ap["narrowest_clear_width_cm"], ap["narrowest_at_x"], ", ".join(ap["buildings_reaching_into_it"])
                        or "none", ap["spawn_point_in_it"]))
        L.append("  ROUTES (planning grid %.0f cm, obstacle boxes and deck edges kept %.0f cm away)"
                 % (ROUTE_STEP, ROUTE_CLEAR))
        for r in plan.get("routes") or []:
            L.append("    %-58s %5s m  clearance %s cm (%s)  %s"
                     % (r["name"][:58], r.get("length_m"), r.get("min_clearance_to_obstacles_cm"),
                        r.get("nearest_obstacle"), (r.get("routing") or {}).get("fallback", "")[:60]))
    fin = plan.get("finish")
    if fin:
        L += ["", "PIER FINISH PF1 (a candidate on the reviewed P3 base; not reference acceptance)"]
        if fin.get("revision"):
            L.append("  REVISION r%s: %s" % (fin["revision"], fin.get("revision_note", "")))
        pa = fin.get("pier_audit") or {}
        L.append("  pier identity audit %s (sha256 %s...): %s" % (pa.get("file"), str(pa.get("sha256"))[:12], "; ".join(
            "%s standalone=%s" % (k, v.get("standalone")) for k, v in (pa.get("props") or {}).items())))
        ln = fin.get("lane") or {}
        if ln:
            L.append("  SERVICE LANE  x %s y %s: %.0f cm wide, straight from the forecourt join to the pier-end edge line"
                     % (ln["x"], ln["y"], ln["width"]))
            L.append("    clear band between obstacle boxes y %s = %.0f cm (bounded by %s and %s); lane buffers %s cm; "
                     "lane to the pier edges %s cm" % (ln["clear_band"], ln["clear_width"], ln["bounded_by"][0],
                                                      ln["bounded_by"][1], ln["buffers"], ln["to_pier_edges"]))
            L.append("    " + ln["basis"])
        L.append("  PIECES %d (tag %s + %s): %s" % (fin["pieces"], RUN_TAG, fin["tag"], ", ".join(
            "%s %d" % kv for kv in sorted(fin["counts"].items()))))
        for k in ("coping", "fascia", "markings"):
            L.append("    %-8s %s; %s" % (k, fin["materials"][k].split("/")[-1], fin["collision"][k]))
        for k, v in fin["dimensions"].items():
            L.append("    %-12s %s" % (k, v))
        L.append("  WATER EDGES of the new decks (coping + fascia + edge line on each): %d" % len(fin["water_edges"]))
        for w in fin["water_edges"]:
            L.append("    %-16s %s -> %s  %7.0f cm  ends %s / %s" % (w["zone"], w["from"], w["to"], w["length_cm"],
                                                                    w["ends"]["t0"]["kind"], w["ends"]["t1"]["kind"]))
        ck = fin["checks"]
        L.append("  CHECKS")
        L.append("    coping on its deck with the lip over water: %d of %d; markings on deck: %d of %d"
                 % (ck["coping_on_deck"]["pieces"] - len(ck["coping_on_deck"]["not_on_deck_or_lip_not_over_water"]),
                    ck["coping_on_deck"]["pieces"], ck["markings_on_deck"]["pieces"] - len(ck["markings_on_deck"]["off_deck"]),
                    ck["markings_on_deck"]["pieces"]))
        for k, j in sorted(ck["joins"].items()):
            L.append("    join %-30s %4d samples, under coping %d (away from the water %d)"
                     % (k, j["samples"], j["under_coping"], j["under_coping_away_from_water"]))
        L.append("    doors and door approaches clear of coping: %s" % ck["door_approaches_clear_of_coping"])
        for r in ck["routes_vs_coping"]:
            L.append("    route %-58s nearest coping %s cm (%s)" % (r["route"][:58], r["min_distance_to_coping_cm"], r["nearest"]))
        L.append("    lane clearances (cm): %s" % ck.get("lane_clearances_cm"))
        L.append("    lane lines' outer edges to the pier props (cm): %s" % ck.get("lane_line_clearances_cm"))
        L.append("    helicopter to the nearest coping: %s cm; buildings: %s" % (ck.get("helicopter_to_nearest_coping_cm"),
                                                                              ck.get("buildings_to_nearest_coping_cm")))
        L.append("    coplanar overlaps among new pieces: %d; pre-existing among P3's own markings (unchanged): %d"
                 % (len(ck["coplanar_overlaps"]), len(ck["preexisting_p3_marking_overlaps"])))
    L += ["", "HELD UNCHANGED: %d actors (see manifest.csv)" % len(plan.get("held", []))]
    L += ["", "DECISIONS / UNRESOLVED"] + ["  - " + x for x in plan.get("decisions", [])]
    if plan.get("notes"):
        L += ["", "NOTES"] + ["  - " + x for x in plan["notes"]]
    if engine_result:
        L += ["", "ENGINE CHECKS"] + ["  " + x for x in engine_result.get("lines", [])]
    L += ["", ("PROBLEMS -- apply refuses until these are resolved" if plan.get("problems")
               else "NO BLOCKING PROBLEMS")] + ["  " + p for p in plan.get("problems", [])]
    write_bytes(OUT / "report.txt", "\n".join(L) + "\n")


# ---------------------------------------------------------------------------
# Engine: read-only checks and the guarded apply / verify / revert lifecycle.
#
# Every write goes to an EXPLICIT target map (IB_GARRISON_TARGET_LEVEL) that
# carries a receipt history in Saved/GarrisonRestructure/receipts/. The receipt
# records the target's file SHA256 after each verified state ("created" by
# ib_garrison_preview_copy.py, then "applied"/"reverted" by this tool). A run
# is accepted only when the target file is byte-identical to its LAST recorded
# state, so a saved apply can be repeated or reverted in a new process, and any
# edit made outside this tool is refused. The source map is never written.
# ---------------------------------------------------------------------------

LIVE_WRITE_ENABLED = False     # writing the source map needs a reviewed change to this line
LOC_TOL = 0.5                  # cm
ROT_TOL = 0.05                 # degrees
SCALE_TOL = 1e-4               # relative
PLATFORM_TREATED = {"component_visible": False, "actor_hidden": True, "collision_enabled": "NO_COLLISION",
                    "actor_collision": False}
PLATFORM_KEYS = ("component_visible", "actor_hidden", "profile", "collision_enabled", "actor_collision")


def enum_name(v):
    s = str(v).strip()
    if s.startswith("<") and ":" in s:
        s = s[1:].split(":")[0]
    return s.split(".")[-1].strip("<> ")


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


def level_name(pkg):
    return pkg.rstrip("/").split("/")[-1]


def level_prefix(pkg):
    return "%s.%s:PersistentLevel." % (pkg, level_name(pkg))


SOURCE_PREFIX = level_prefix(LEVEL)


def remap(path, target):
    """A planned identity (always a source-map path) as the same actor in the target map."""
    if not path.startswith(SOURCE_PREFIX):
        raise RuntimeError("identity %s is not an actor of the planned source map" % path)
    return level_prefix(target) + path[len(SOURCE_PREFIX):]


def target_file(pkg):
    return PROJECT / "Content" / (pkg[len("/Game/"):] + ".umap")


RECEIPTS = PROJECT / "Saved/GarrisonRestructure/receipts"


def receipt_file(pkg):
    return RECEIPTS / (pkg.strip("/").replace("/", "__") + ".json")


def read_receipts(pkg):
    f = receipt_file(pkg)
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None


def append_receipt(pkg, entry):
    rec = read_receipts(pkg)
    rec["history"].append(entry)
    receipt_file(pkg).write_bytes(json.dumps(rec, indent=1).encode("utf-8"))


def now_utc():
    return datetime.datetime.utcnow().isoformat() + "Z"


def live_actors():
    out = {}
    for a in EAS.get_all_level_actors():
        try:
            out[a.get_path_name()] = a
        except Exception:
            pass
    return out


def tags_of(a):
    try:
        return [str(t) for t in (a.get_editor_property("tags") or [])]
    except Exception:
        return []


def tagged_index(live):
    out = {}
    for a in live.values():
        if RUN_TAG in tags_of(a):
            out.setdefault(a.get_actor_label(), []).append(a)
    return out


def actor_transform(a):
    l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    return [l.x, l.y, l.z], {"roll": r.roll, "pitch": r.pitch, "yaw": r.yaw}, [s.x, s.y, s.z]


def transform_issues(a, loc, rot, scale, what):
    here, r, sc = actor_transform(a)
    out = []
    if not vec_close(here, loc, LOC_TOL):
        out.append("%s location %s, expected %s" % (what, [round(v, 1) for v in here], loc))
    if not rot_close(r, rot):
        out.append("%s rotation %s, expected %s" % (what, {k: round(v, 3) for k, v in r.items()}, rot))
    if scale is not None and not vec_close(sc, scale, SCALE_TOL * max([1.0] + [abs(float(v)) for v in scale])):
        out.append("%s scale %s, expected %s" % (what, [round(v, 5) for v in sc], scale))
    return out


def piece_issues(a, spec):
    """Everything about one generated actor that must be exactly as planned."""
    out = []
    smc = a.static_mesh_component
    if a.get_actor_label() != spec["label"]:
        out.append("label is %r" % a.get_actor_label())
    if RUN_TAG not in tags_of(a):
        out.append("run tag missing")
    for t in spec.get("tags") or []:
        if t not in tags_of(a):
            out.append("tag %s missing" % t)
    mesh = smc.get_editor_property("static_mesh")
    if mesh is None or mesh.get_path_name() != spec["mesh"]:
        out.append("mesh is %s" % (mesh.get_path_name() if mesh else None))
    mat = smc.get_material(0)
    if mat is None or mat.get_path_name() != spec["material"]:
        out.append("material is %s" % (mat.get_path_name() if mat else None))
    out += transform_issues(a, spec["location"], spec["rotation"], spec["scale"], "")
    if not smc.is_visible():
        out.append("component not visible")
    if bool(a.get_editor_property("hidden")):
        out.append("actor hidden")
    if not bool(a.get_actor_enable_collision()):
        # a deck can look intact with actor-level collision off and still drop a pawn through it
        out.append("actor collision disabled")
    prof, ce = str(smc.get_collision_profile_name()), enum_name(smc.get_collision_enabled())
    want = "QUERY_AND_PHYSICS" if spec["collision"] == "BlockAll" else "NO_COLLISION"
    if prof != spec["collision"] or ce != want:
        out.append("collision %s/%s, expected %s/%s" % (prof, ce, spec["collision"], want))
    return ["%s:%s" % (spec["label"], x) for x in out]


def platform_capture(a):
    smc = a.static_mesh_component
    return {"component_visible": bool(smc.is_visible()), "actor_hidden": bool(a.get_editor_property("hidden")),
            "profile": str(smc.get_collision_profile_name()), "collision_enabled": enum_name(smc.get_collision_enabled()),
            "actor_collision": bool(a.get_actor_enable_collision())}


def platform_diff(state, want):
    return ["%s=%s (expected %s)" % (k, state.get(k), want[k]) for k in want if state.get(k) != want[k]]


def platform_treat(a):
    smc = a.static_mesh_component
    smc.set_visibility(False, True)
    a.set_actor_hidden_in_game(True)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.set_actor_enable_collision(False)


def platform_restore(a, before):
    """Every captured flag back exactly: the profile first (it resets collision
    enabled to the profile's own value), then the captured collision state."""
    smc = a.static_mesh_component
    smc.set_collision_profile_name(before["profile"])
    smc.set_collision_enabled(getattr(unreal.CollisionEnabled, before["collision_enabled"]))
    a.set_actor_enable_collision(bool(before["actor_collision"]))
    smc.set_visibility(bool(before["component_visible"]), True)
    a.set_actor_hidden_in_game(bool(before["actor_hidden"]))


def check_state(plan, target, live, which, platform_before=None):
    """Every difference between the live level and the state `which`:
    'clean' (the source layout) or 'applied' (this plan, exactly)."""
    issues = []
    tagged = tagged_index(live)
    want = {p["label"]: p for p in plan.get("pieces", [])}
    if which == "clean":
        if tagged:
            issues.append("%d generated actor(s) present: %s" % (sum(len(v) for v in tagged.values()),
                                                                 ", ".join(sorted(tagged)[:6])))
    else:
        for label, spec in sorted(want.items()):
            got = tagged.get(label, [])
            if len(got) != 1:
                issues.append("%s: %d actor(s) carry this label and the run tag" % (label, len(got)))
                continue
            issues += piece_issues(got[0], spec)
        extra = sorted(l for l in tagged if l not in want)
        if extra:
            issues.append("generated actor(s) this plan does not contain: " + ", ".join(extra[:6]))
    for m in plan.get("moves", []):
        a = live.get(remap(m["identity"], target))
        if a is None:
            issues.append("missing %s (%s)" % (m["label"], m["identity"].split(".")[-1]))
            continue
        if a.get_actor_label() != m["label"] or a.get_class().get_name() != m["class"]:
            issues.append("%s is now %s/%s" % (m["identity"].split(".")[-1], a.get_class().get_name(),
                                                a.get_actor_label()))
            continue
        end = m["from"] if which == "clean" else m["to"]
        issues += transform_issues(a, end["loc"], end["rot"], end["scale"], m["label"])
    t = plan.get("platform_treatment")
    if t:
        a = live.get(remap(t["identity"], target))
        if a is None:
            issues.append("platform %s missing" % t["identity"].split(".")[-1])
        else:
            st = platform_capture(a)
            if which == "clean":
                ref = platform_before or t.get("before_live")
                if not ref:
                    issues.append("platform: no complete recorded before-state to compare with")
                else:
                    issues += ["platform " + d for d in platform_diff(st, {k: ref[k] for k in PLATFORM_KEYS})]
            else:
                issues += ["platform " + d for d in platform_diff(st, PLATFORM_TREATED)]
    return issues


def label_collisions(plan, live):
    want = set(p["label"] for p in plan.get("pieces", []))
    out = []
    for path, a in live.items():
        try:
            if a.get_actor_label() in want and RUN_TAG not in tags_of(a):
                out.append("label %s is already used by the untagged actor %s" % (a.get_actor_label(), path))
        except Exception:
            pass
    return out


def load_assets(plan):
    assets, problems = {}, []
    for p in plan.get("pieces", []):
        for key in ("mesh", "material"):
            path = p.get(key)
            if path and path not in assets:
                assets[path] = unreal.load_asset(path)
                if assets[path] is None:
                    problems.append("cannot load %s %s" % (key, path))
    return assets, problems


def loaded_world_package():
    world = None
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    except Exception:
        world = unreal.EditorLevelLibrary.get_editor_world()
    return world.get_path_name().split(".")[0] if world else None


def validate_target(target):
    if not target or not target.startswith("/Game/"):
        fail("IB_GARRISON_TARGET_LEVEL must be a /Game/ package path, got %r" % target)
    if target.rstrip("/") == LEVEL and not LIVE_WRITE_ENABLED:
        fail("the target is the source map %s; this build never writes it (preview copies only)" % LEVEL)
    if not target_file(target).is_file():
        fail("target map file %s does not exist" % target_file(target))


def accepted_state(plan, plan_sha, target):
    """The target's last verified state, if and only if its file is byte-identical to it."""
    rec = read_receipts(target)
    if rec is None:
        return None, ("no receipt for %s: only a map created by Scripts/ib_garrison_preview_copy.py (and then "
                      "changed only by this tool) can be written" % target)
    if rec.get("target_package") != target:
        return None, "receipt file belongs to %s" % rec.get("target_package")
    src_sha = (plan.get("map") or {}).get("sha256")
    if rec.get("source_package") != LEVEL or rec.get("source_sha256") != src_sha:
        return None, ("the target was copied from %s at %s..., not from the planned %s at %s..."
                      % (rec.get("source_package"), str(rec.get("source_sha256"))[:12], LEVEL, str(src_sha)[:12]))
    cur = file_sha256(target_file(target))
    last = rec["history"][-1]
    if cur != last["sha256"]:
        older = [h["state"] for h in rec["history"][:-1] if h["sha256"] == cur]
        return None, ("STALE TARGET: its file (%s...) is not its last verified state '%s' (%s...). %s"
                      % (str(cur)[:12], last["state"], last["sha256"][:12],
                         ("It equals an older recorded state (%s); nothing is assumed about it." % older[-1])
                         if older else "It was changed outside this tool; nothing will be written."))
    if last["state"] == "applied" and last.get("plan_sha256") != plan_sha:
        return None, "the target was applied by a different plan (%s...)" % str(last.get("plan_sha256"))[:12]
    return last, None


def save_target(target):
    pkg = loaded_world_package()
    if pkg != target:
        fail("refusing to save: the loaded world is %s, not the target %s" % (pkg, target))
    if pkg == LEVEL and not LIVE_WRITE_ENABLED:
        fail("refusing to save the source map")
    before = file_sha256(target_file(target))
    ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    if not ok:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        ok = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, target))
    if not ok:
        fail("level save failed")
    after = file_sha256(target_file(target))
    if after == before:
        log("note: the save left the target file byte-identical")
    return after


def apply_plan(plan, plan_sha, target):
    live = live_actors()
    state, why = accepted_state(plan, plan_sha, target)
    if state is None:
        fail(why)
    if state["state"] == "applied":
        issues = check_state(plan, target, live, "applied")
        if issues:
            for i in issues[:30]:
                unreal.log_error("GARRISON LAYOUT: " + i)
            fail("the receipt says applied but the level differs in %d way(s); nothing changed" % len(issues))
        log("REPEAT: already applied by this plan and verified in place; nothing changed, nothing saved")
        return {"result": "already-applied-verified", "changed": 0, "saved": False, "state": "applied",
                "sha256": state["sha256"]}
    problems = check_state(plan, target, live, "clean")
    problems += label_collisions(plan, live)
    assets, ap = load_assets(plan)
    problems += ap
    problems += ["plan: " + p for p in plan.get("problems", [])]
    t = plan.get("platform_treatment")
    platform = live.get(remap(t["identity"], target)) if t else None
    if t and not t.get("before_live"):
        problems.append("the plan has no complete live before-state for the platform; regenerate it in the engine")
    if problems:
        for p in problems[:50]:
            unreal.log_error("GARRISON LAYOUT: " + p)
        fail("preflight found %d problem(s); NOTHING was changed and nothing was saved" % len(problems))
    captured = platform_capture(platform) if platform else None
    bad, stage = [], "pieces"
    for spec in plan["pieces"]:
        rot = unreal.Rotator(roll=spec["rotation"]["roll"], pitch=spec["rotation"]["pitch"],
                             yaw=spec["rotation"]["yaw"])
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
        a.set_editor_property("tags", [RUN_TAG] + list(spec.get("tags") or []))
        a.set_folder_path(RUN_FOLDER)
    if not bad:
        live = live_actors()
        tagged = tagged_index(live)
        for spec in plan["pieces"]:
            got = tagged.get(spec["label"], [])
            if len(got) != 1:
                bad.append("%s: %d generated actor(s) after spawning" % (spec["label"], len(got)))
            else:
                bad += piece_issues(got[0], spec)
    if not bad:
        stage = "moves"
        for m in plan.get("moves", []):
            a, to = live.get(remap(m["identity"], target)), m["to"]
            a.set_actor_location(unreal.Vector(*to["loc"]), False, False)
            a.set_actor_rotation(unreal.Rotator(roll=to["rot"]["roll"], pitch=to["rot"]["pitch"],
                                                yaw=to["rot"]["yaw"]), False)
        for m in plan.get("moves", []):
            a = live.get(remap(m["identity"], target))
            bad += transform_issues(a, m["to"]["loc"], m["to"]["rot"], m["to"]["scale"], m["label"])
    if not bad and platform:
        stage = "platform"
        platform_treat(platform)
        bad += ["platform " + d for d in platform_diff(platform_capture(platform), PLATFORM_TREATED)]
    if not bad:
        stage = "final"
        bad += check_state(plan, target, live_actors(), "applied")
    if bad:
        for b in bad[:40]:
            unreal.log_error("GARRISON LAYOUT: " + b)
        fail("%d operation(s) did not verify at stage '%s'; the old platform was %s and the level was NOT "
             "saved. A commandlet discards the level on exit; in the editor, discard it (or revert in this "
             "session)." % (len(bad), stage, "treated" if stage in ("platform", "final") else "left untouched"))
    result = {"result": "applied-verified", "changed": len(plan["pieces"]) + len(plan.get("moves", [])) + 1,
              "saved": False, "state": "applied", "platform_before": captured}
    if SAVE:
        sha = save_target(target)
        append_receipt(target, {"state": "applied", "sha256": sha, "plan_sha256": plan_sha,
                                "platform_before": captured, "pieces": len(plan["pieces"]),
                                "moves": len(plan.get("moves", [])), "utc": now_utc(),
                                "by": "ib_layout_garrison.py apply"})
        result.update({"saved": True, "sha256": sha})
        log("APPLY verified and saved: %s -> %s" % (target, sha))
    else:
        log("APPLY verified; NOT saved (IB_GARRISON_SAVE=1 saves the TARGET map only)")
    return result


def revert_plan(plan, plan_sha, target):
    live = live_actors()
    state, why = accepted_state(plan, plan_sha, target)
    if state is None:
        fail(why)
    t = plan.get("platform_treatment")
    if state["state"] == "applied":
        before = state.get("platform_before")
    else:
        if not check_state(plan, target, live, "clean"):
            fail("nothing to revert: %s is in its clean state" % target)
        before = (t or {}).get("before_live")          # an unsaved apply in this same session
    if t and (not before or any(k not in before for k in PLATFORM_KEYS)):
        fail("no complete captured platform state to restore; refusing to revert")
    conflicts = check_state(plan, target, live, "applied")
    if conflicts:
        for c in conflicts[:40]:
            unreal.log_error("GARRISON LAYOUT: revert conflict: " + c)
        fail("REVERT REFUSED: %d conflict(s) between the level and the applied plan; nothing was changed, so "
             "later edits are not overwritten" % len(conflicts))
    bad = []
    for m in plan.get("moves", []):
        a, fr = live.get(remap(m["identity"], target)), m["from"]
        a.set_actor_location(unreal.Vector(*fr["loc"]), False, False)
        a.set_actor_rotation(unreal.Rotator(roll=fr["rot"]["roll"], pitch=fr["rot"]["pitch"],
                                            yaw=fr["rot"]["yaw"]), False)
    for label, actors in tagged_index(live).items():
        for a in actors:
            if not EAS.destroy_actor(a):
                bad.append("could not remove %s" % label)
    if t:
        platform_restore(live.get(remap(t["identity"], target)), before)
    bad += check_state(plan, target, live_actors(), "clean", platform_before=before)
    if bad:
        for b in bad[:40]:
            unreal.log_error("GARRISON LAYOUT: " + b)
        fail("revert did not verify (%d issue(s)); NOT saved" % len(bad))
    result = {"result": "reverted-verified", "saved": False, "state": "reverted"}
    if SAVE:
        sha = save_target(target)
        append_receipt(target, {"state": "reverted", "sha256": sha, "plan_sha256": plan_sha,
                                "platform_restored": before, "utc": now_utc(), "by": "ib_layout_garrison.py revert"})
        result.update({"saved": True, "sha256": sha})
        log("REVERT verified and saved: %s -> %s" % (target, sha))
    else:
        log("REVERT verified; NOT saved")
    return result


def verify_target(plan, plan_sha, target):
    live = live_actors()
    state, why = accepted_state(plan, plan_sha, target)
    if state is None:
        fail(why)
    which = "applied" if state["state"] == "applied" else "clean"
    before = None
    if which == "clean":
        prior = [h for h in read_receipts(target)["history"] if h["state"] == "applied"]
        before = prior[-1].get("platform_before") if prior else None
    issues = check_state(plan, target, live, which, platform_before=before)
    log("VERIFY %s: recorded state '%s' (%s), %d difference(s)" % (target, state["state"], state["sha256"],
                                                                  len(issues)))
    for i in issues[:40]:
        unreal.log_error("GARRISON LAYOUT: " + i)
    if issues:
        fail("VERIFY FAILED: the level does not match its recorded state")
    return {"result": "verified", "state": state["state"], "sha256": state["sha256"], "differences": 0,
            "generated": sum(len(v) for v in tagged_index(live).values())}


def engine_facts():
    """Facts only the engine can give, captured read-only before planning."""
    facts = {}
    try:
        ps = unreal.PhysicsSettings.get_default_object()
        facts["default_shape_complexity"] = enum_name(ps.get_editor_property("default_shape_complexity"))
    except Exception as error:
        facts["default_shape_complexity"] = None
        facts["default_shape_complexity_error"] = str(error).strip().splitlines()[-1][:200]
    live = live_actors()
    rows = [a for p, a in live.items() if p.startswith(SOURCE_PREFIX) and a.get_actor_label() == PLATFORM_ID[0]]
    if len(rows) == 1:
        facts["platform_live"] = platform_capture(rows[0])
    return facts


def engine_checks(plan):
    """Read-only, on the loaded source map: assets, deck collision, generated
    leftovers and the apply preflight exactly as an apply would run it."""
    lines = []
    result = {"lines": lines}
    live = live_actors()
    lines.append("level loaded: %d actors (%s)" % (len(live), loaded_world_package()))
    cube = unreal.load_asset(CUBE)
    try:
        body = cube.get_editor_property("body_setup")
        agg = body.get_editor_property("agg_geom")
        parts = {}
        for name in ("sphere_elems", "box_elems", "sphyl_elems", "convex_elems", "tapered_capsule_elems"):
            try:
                parts[name] = len(agg.get_editor_property(name) or [])
            except Exception:
                pass
        n = sum(parts.values())
        flag = enum_name(body.get_editor_property("collision_trace_flag"))
        blocks = n > 0
        result["deck_mesh_collision"] = {"simple_shapes": n, "parts": parts, "trace_flag": flag, "blocks_pawns": blocks}
        lines.append("deck mesh %s: %d simple shape(s), %s -> decks block pawns: %s"
                     % (CUBE, n, flag, "yes" if blocks else "NO"))
        if not blocks:
            plan["problems"].append("the deck mesh has no simple collision; decks would not hold a player")
    except Exception as error:
        result["deck_mesh_collision"] = "unreadable: %s" % str(error).splitlines()[-1][:160]
        lines.append("deck mesh collision UNREADABLE (%s)" % str(error).splitlines()[-1][:160])
    tagged = tagged_index(live)
    lines.append("actors already carrying run tag %s: %d" % (RUN_TAG, sum(len(v) for v in tagged.values())))
    problems = check_state(plan, LEVEL, live, "clean") + label_collisions(plan, live)
    assets, ap = load_assets(plan)
    problems += ap + ["plan: " + p for p in plan.get("problems", [])]
    lines.append("assets: %d of %d load" % (sum(1 for v in assets.values() if v is not None), len(assets)))
    lines.append("apply preflight on the source layout (read-only): %s"
                 % ("CLEAN" if not problems else "%d problem(s)" % len(problems)))
    for p in problems[:30]:
        lines.append("  preflight: " + p)
    result["preflight_problems"] = problems
    return result


def write_bytes(path, text):
    """LF bytes, so the SHA256 a tool reports is the SHA256 of the file on disk."""
    data = text.encode("utf-8")
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest().upper()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mode = "revert" if REVERT else "apply" if APPLY else "verify" if VERIFY else "plan"
    status = {"tool": "ib_layout_garrison", "schema": SCHEMA, "started_utc": STARTED, "engine": ENGINE,
              "mode": mode, "target": TARGET_LEVEL, "saved_packages": 0}
    try:
        if mode != "plan":
            if not ENGINE:
                fail("%s needs the engine" % mode)
            if not PLAN_IN:
                fail("%s executes a reviewed plan file: set IB_GARRISON_PLAN" % mode)
            if not TARGET_LEVEL:
                fail("set IB_GARRISON_TARGET_LEVEL to the map to %s; this tool never guesses its target" % mode)
            validate_target(TARGET_LEVEL)
            plan = read_json(Path(PLAN_IN))
            plan_sha = file_sha256(Path(PLAN_IN))
            status.update({"plan": PLAN_IN, "plan_sha256": plan_sha,
                           "source_map_sha256_before": file_sha256(PROJECT / MAP_FILE_REL),
                           "target_sha256_before": file_sha256(target_file(TARGET_LEVEL))})
            if loaded_world_package() != TARGET_LEVEL:
                # Already open (an editor session, or a test that changed it in memory):
                # use it as it is, unsaved edits included, so a revert sees them.
                unreal.EditorLoadingAndSavingUtils.load_map(TARGET_LEVEL)
            if loaded_world_package() != TARGET_LEVEL:
                fail("loaded world is %s, not %s" % (loaded_world_package(), TARGET_LEVEL))
            fn = {"apply": apply_plan, "revert": revert_plan, "verify": verify_target}[mode]
            result = fn(plan, plan_sha, TARGET_LEVEL)
            status.update(result)
            status["saved_packages"] = 1 if result.get("saved") else 0
            status["target_sha256_after"] = file_sha256(target_file(TARGET_LEVEL))
            status["source_map_sha256_after"] = file_sha256(PROJECT / MAP_FILE_REL)
            if status["source_map_sha256_after"] != status["source_map_sha256_before"]:
                fail("THE SOURCE MAP CHANGED during this run")
        else:
            facts = None
            if PLAN_IN:
                plan = read_json(Path(PLAN_IN))
                log("using reviewed plan " + PLAN_IN)
            else:
                if ENGINE:
                    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
                    facts = engine_facts()
                inv = {"meta": read_json(INV / "inventory_meta.json"), "elements": read_json(INV / "elements.json"),
                       "rows": read_json(INV / "actors.json"), "faces": read_json(INV / "support_faces.json"),
                       "meshes": read_json(INV / "meshes.json")}
                plan = build_plan(inv, facts)
            engine_result = None
            if ENGINE:
                if PLAN_IN:
                    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
                engine_result = engine_checks(plan)
                plan["engine_checks"] = {k: v for k, v in engine_result.items()}
            if not PLAN_IN:
                status["plan_sha256"] = write_bytes(OUT / "plan.json", json.dumps(plan, indent=1))
            status["manifest_sha256"] = write_manifest(plan) if "design" in plan else None
            write_report(plan, engine_result)
            status["problems"] = len(plan.get("problems", []))
            log("plan -> %s ; report -> %s ; %d blocking problem(s)" % (OUT / "plan.json", OUT / "report.txt",
                                                                        status["problems"]))
            log("READ-ONLY run; nothing changed and no package saved.")
        status["status"] = "complete"
    except Exception:
        tool_error("layout run")
        status["status"] = "failed"
        raise
    finally:
        status["tool_errors"] = len(TOOL_ERRORS)
        status["errors"] = TOOL_ERRORS[:20]
        status["finished_utc"] = now_utc()
        try:
            name = "tool_status.json" if mode == "plan" else "lifecycle_%s.json" % mode
            write_bytes(OUT / name, json.dumps(status, indent=1))
        except Exception:
            pass
        log("COMPLETE" if status.get("status") == "complete" else "FAILED")


try:
    main()
except Exception:
    if ENGINE:
        unreal.log_error("GARRISON LAYOUT FAILED\n" + traceback.format_exc())
    raise
