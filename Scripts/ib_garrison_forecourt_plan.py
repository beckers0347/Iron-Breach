"""FF1 FORECOURT FINISH -- the plan (pure Python; no engine, reads and writes JSON only).

    python Scripts/ib_garrison_forecourt_plan.py --site <site.json> --basefp <base_fingerprint.json>
           --pf1-plan <PF1 plan2/plan.json> --out <dir> [--mi <new MI package>] [--base-mi <YM1 MI package>]

Continues the accepted lower-deck treatment (PF1: quay coping, concrete fascia, 40 cm inset edge line)
around the EXISTING generated forecourt's open-water perimeter, and lays out the forecourt's painted
circulation in the PF1 vocabulary (40 cm lane lines, 300 x 40 cm route dashes, 300 x 40 cm door bars):

  axis road     the spine's two lane lines continued across the forecourt to the hangar reservation's
                front outline (the P3 spine dashes are its centre line already)
  gate road     the pier's 6 m service-lane lines continued back across the forecourt to the land gate
                (the verified city road -> gate -> forecourt and forecourt -> pier routes lie in it)
  cross-road    a transverse road along the seaward edge where the spine enters: a landward line 8 m
                inboard of the edge line, broken where the gate road and the axis road pass through,
                with centre dashes; its seaward side is the new edge line (open at the pier and spine
                joins); it runs from the image-right (-Y) edge line to Medical's corner
  door routes   route dashes from the roads to the Barracks, Armory and Medical doors, and a door bar
                in front of each of those doors

and refines the P3 pad ring into a thin, smooth 96-segment ring of the same radius and width (the 32
existing ring actors become every third segment, modified in place with their originals recorded; 64
new segments fill in). Every generated marking -- the 91 existing and every new paint piece -- gets the
NEW candidate-owned paint instance.

Geometry comes from the ACTUAL engine state (ff1_site_probe.py on YM1): the forecourt outline is checked
against the generated deck pieces' real transforms, open water against real vertical traces, and the
buildings against their real collision faces. Nothing here moves a building, prop, door, spawn or deck.
The PF1 helpers below (runs, strips, lines, staggering) are copied from Scripts/ib_layout_garrison.py
(SHA256 C0DB217B...) so that the finish is the same treatment, not a new one.

Writes ff1_plan.json (pieces to create, ring edits with original values, material assignments, checks,
corridors, local constraints, problems), ff1_plan_report.txt and ff1_plan.png (a top view for review).
"""
import json, math, sys, hashlib, datetime
from pathlib import Path

RUN_TAG = "IB_GarrisonCB1"
FF_TAG = "IB_GarrisonForecourtFinish"
FOLDER = "Carrowgate Garrison/Forecourt FF1"
LABEL_PREFIX = "IBGC_FF_"
CUBE = "/Engine/BasicShapes/Cube.Cube"
CUBE_HALF = 50.0
BASTION_CONCRETE = "/Game/IronBreach/Environment/Bastion/M_Bastion_Concrete.M_Bastion_Concrete"
SHARED_MARK = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_HelipadMarking.MI_Landmass_HelipadMarking"
DEFAULT_MI = "/Game/_GarrisonPreview_Disposable/ForecourtFinish1_Materials/MI_FF1_DeckPaintAmber"
DEFAULT_BASE_MI = "/Game/_GarrisonPreview_Disposable/YellowMarkings1_Materials/MI_YM1_DeckPaintYellow"
BASE_PKG = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_YellowMarkings1"
TARGET_PKG = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ForecourtFinish1"

# PF1's treatment, unchanged (ib_layout_garrison.py)
COPING_IN, COPING_LIP = 50.0, 10.0
COPING_RISE, COPING_DROP = 8.0, 30.0
COPING_STEP = 0.4
FASCIA_OUT, FASCIA_IN = 6.0, 4.0
FASCIA_BELOW_WATER = 45.0
FASCIA_STEP = 0.4
EDGE_LINE_INSET = 100.0
LINE_HALF = 20.0
MARK_STEP = 0.3
DASH_LEN, DASH_HALF_W, DASH_PERIOD = 300.0, 20.0, 600.0
DOOR_BAR_LEN, DOOR_BAR_FRONT = 300.0, 50.0

# FF1 layout
CROSS_ROAD_CLEAR = 800.0      # clear width between the cross-road's landward line and the edge line
BUILDING_LINE_KEEP = 100.0    # an edge line stops this far short of a building's visual footprint
ROUTE_CLEAR = 60.0            # a route dash keeps this far from any obstacle (a pawn capsule + margin)
LANE_BUFFER = 50.0            # a painted road keeps this far from any obstacle
RESERVE_KEEP = 100.0          # no coping or edge line within this of the hangar reservation on the rear edge
RING_SEGMENTS = 96
RING_TOP_EVEN, RING_TOP_ODD, RING_BOTTOM = 0.5, 0.6, -1.5   # relative to the deck: 0.5 / 0.6 cm proud (thin paint,
# neighbours 1 mm apart where their inner corners overlap); the bottom is embedded in the pad's chamfer fillers too,
# whose tops are 1 cm below the deck (about a fifth of the ring lies over them)
NEW_MARK_BOTTOM = -1.5        # new paint is embedded in the 1 cm lower chamfer fillers as well as in the decks
MIN_ISOLATED = 600.0          # an isolated curb or edge-line fragment shorter than this is not laid

DECK_Z = 385.0
EXISTING_MARK_TOP = DECK_Z + 1.5


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def r1(v):
    return round(float(v), 1)


def sha(path):
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest().upper()


# ---------------------------------------------------------------- plane geometry (from ib_layout_garrison.py)

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


def obb_overlap(P, Q, eps=0.5):
    """True when two convex footprints overlap by more than eps on every separating axis."""
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


def ccw(poly):
    return list(poly) if area(poly) > 0 else list(reversed(poly))


# ---------------------------------------------------------------- pieces

def box_piece(label, zone, kind, cx, cy, hx, hy, top, bottom, yaw, material, collision):
    hz = (top - bottom) / 2.0
    return {"label": LABEL_PREFIX + label, "zone": zone, "kind": kind, "mesh": CUBE, "material": material,
            "location": [r1(cx), r1(cy), round(bottom + hz, 2)],
            "rotation": {"roll": 0.0, "pitch": 0.0, "yaw": round(yaw, 4)},
            "scale": [round(hx / CUBE_HALF, 5), round(hy / CUBE_HALF, 5), round(hz / CUBE_HALF, 5)],
            "half_extent": [round(hx, 2), round(hy, 2), round(hz, 3)], "top_z": round(top, 2), "bottom_z": round(bottom, 2),
            "collision": collision, "tags": [RUN_TAG, FF_TAG], "folder": FOLDER,
            "footprint": [[round(x, 2), round(y, 2)] for x, y in obb(cx, cy, hx, hy, yaw)]}


def restack(p, top):
    q = dict(p)
    bottom = p["bottom_z"]
    hz = (top - bottom) / 2.0
    q["location"] = [p["location"][0], p["location"][1], round(bottom + hz, 2)]
    q["scale"] = [p["scale"][0], p["scale"][1], round(hz / CUBE_HALF, 5)]
    q["half_extent"] = [p["half_extent"][0], p["half_extent"][1], round(hz, 3)]
    q["top_z"] = round(top, 2)
    return q


def refascia(p, level):
    d = FASCIA_STEP * level
    yaw = math.radians(p["rotation"]["yaw"])
    nx, ny = math.sin(yaw), -math.cos(yaw)
    hy = p["half_extent"][1] - d / 2.0
    q = dict(p)
    q["location"] = [r1(p["location"][0] - nx * d / 2.0), r1(p["location"][1] - ny * d / 2.0), p["location"][2]]
    q["scale"] = [p["scale"][0], round(hy / CUBE_HALF, 5), p["scale"][2]]
    q["half_extent"] = [p["half_extent"][0], round(hy, 2), p["half_extent"][2]]
    q["footprint"] = [[round(x, 2), round(y, 2)] for x, y in obb(q["location"][0], q["location"][1],
                                                                  p["half_extent"][0], hy, p["rotation"]["yaw"])]
    return q


def line_piece(label, zone, kind, p0, p1, half_w, material, top=None):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    return box_piece(label, zone, kind, (p0[0] + p1[0]) / 2.0, (p0[1] + p1[1]) / 2.0, L / 2.0, half_w,
                     top if top is not None else EXISTING_MARK_TOP, DECK_Z + NEW_MARK_BOTTOM,
                     math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])), material, "NoCollision")


def stagger(group, fixed):
    """Level per piece: the lowest level no overlapping piece (new or fixed) already uses."""
    placed = list(fixed)
    out = {}
    for p in group:
        used = set(lv for q, lv in placed if obb_overlap(p["footprint"], q["footprint"]))
        lv = 0
        while lv in used:
            lv += 1
        out[p["label"]] = lv
        placed.append((p, lv))
    return out


# ---------------------------------------------------------------- runs along the forecourt's water edges

def edge_frame(P, i):
    a, b = P[i], P[(i + 1) % len(P)]
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    return a, b, L, u, (u[1], -u[0])


def pt(r, t, inboard=0.0):
    return (r["a"][0] + r["u"][0] * t - r["n"][0] * inboard, r["a"][1] + r["u"][1] * t - r["n"][1] * inboard)


def meet(p, u, q, v):
    den = u[0] * v[1] - u[1] * v[0]
    if abs(den) < 1e-9:
        return None
    return ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / den


def turn(u, v):
    return math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1])))


def subtract(iv, cuts):
    """Interval [a, b] minus a list of intervals."""
    out = [list(iv)]
    for c0, c1 in cuts:
        nxt = []
        for a, b in out:
            if c1 <= a or c0 >= b:
                nxt.append([a, b])
                continue
            if c0 > a:
                nxt.append([a, c0])
            if c1 < b:
                nxt.append([c1, b])
        out = nxt
    return [x for x in out if x[1] - x[0] > 1.0]


def interval_on_edge(r, poly, margin_in, margin_out, step=5.0):
    """The parts of run r's edge whose strip [-margin_in, +margin_out] across it touches poly."""
    hits = []
    t = 0.0
    L = r["L"]
    while t <= L + 1e-6:
        touch = False
        for c in (-margin_in, -margin_in / 2.0, 0.0, margin_out):
            x, y = r["a"][0] + r["u"][0] * t + r["n"][0] * c, r["a"][1] + r["u"][1] * t + r["n"][1] * c
            if inside(x, y, poly):
                touch = True
                break
        hits.append((t, touch))
        t += step
    out, cur = [], None
    for t, touch in hits:
        if touch and cur is None:
            cur = [max(0.0, t - step), t]
        elif touch:
            cur[1] = t
        elif cur is not None:
            out.append([cur[0], min(L, t)])
            cur = None
    if cur is not None:
        out.append([cur[0], L])
    return out


# ---------------------------------------------------------------- main plan

def build(site, basefp, pf1, mi_pkg, base_mi_pkg):
    problems, notes, constraints = [], [], []
    mi_obj = "%s.%s" % (mi_pkg, mi_pkg.split("/")[-1])
    base_mi_obj = "%s.%s" % (base_mi_pkg, base_mi_pkg.split("/")[-1])
    design = pf1["design"]
    fore = ccw([tuple(p) for p in design["forecourt"]["polygon"]])
    spine = rect(design["spine"]["x"][0], design["spine"]["x"][1], design["spine"]["y"][0], design["spine"]["y"][1])
    pier = rect(design["pier"]["x"][0], design["pier"]["x"][1], design["pier"]["y"][0], design["pier"]["y"][1])
    reserve = pf1["hangar_reserve"]
    rx0, rx1 = reserve["x"]
    ry0, ry1 = reserve["y"]
    reserve_poly = rect(rx0, rx1, ry0, ry1)
    axis_y = design["spine"]["axis_y"]
    x_sea = design["forecourt"]["seaward_edge_x"]

    # ---- actual engine state: decks, actors, faces ------------------------------------------------
    by_label = {}
    for a in site["actors"]:
        by_label.setdefault(a["label"], []).append(a)

    def one(label):
        rows = by_label.get(label) or []
        if len(rows) != 1:
            problems.append("site: %d actor(s) labelled %s" % (len(rows), label))
            return None
        return rows[0]

    def box_of(label, key="bounds_all", grow=0.0):
        a = one(label)
        if not a or not a.get(key) or not any(a[key]["extent"]):
            return None
        o, e = a[key]["origin"], a[key]["extent"]
        return rect(o[0] - e[0] - grow, o[0] + e[0] + grow, o[1] - e[1] - grow, o[1] + e[1] + grow)

    decks = site["forecourt_decks"]
    deck_polys = [[tuple(p) for p in d["footprint"]] for d in decks]
    # the design outline against the decks' real transforms: 5 cm inside every edge is deck, 5 cm outside is not
    worst_in, worst_out = 0, 0
    P = fore
    for i in range(len(P)):
        a, b, L, u, n = edge_frame(P, i)
        t = 10.0
        while t < L - 10.0:
            x, y = a[0] + u[0] * t, a[1] + u[1] * t
            if not any(inside(x - n[0] * 5, y - n[1] * 5, dp) for dp in deck_polys):
                worst_in += 1
            if any(inside(x + n[0] * 5, y + n[1] * 5, dp) for dp in deck_polys):
                worst_out += 1
            t += 50.0
    outline_check = {"samples_not_on_deck_5cm_inside": worst_in, "samples_on_forecourt_deck_5cm_outside": worst_out,
                     "decks": [d["label"] for d in decks]}
    if worst_in or worst_out:
        problems.append("the design outline does not match the generated forecourt decks' actual transforms "
                        "(%d / %d samples)" % (worst_in, worst_out))

    # what the probe found outside each edge
    probe_edges = site["edges"]

    def probe_class(ex, ey):
        """Classification of the probe sample nearest to (ex, ey) on the outline."""
        best, cls = None, None
        for e in probe_edges:
            for s in e["samples"]:
                d = math.hypot(s["x"] - ex, s["y"] - ey)
                if best is None or d < best:
                    hs = [h for h in s["outside"]["30"] if not h.get("overlap")]
                    lab = hs[0]["actor"] if hs else None
                    best, cls = d, ("water" if lab == "IB_Harbor_Surface" else "none" if lab is None else "land_join"
                                    if (lab or "").startswith("IBGC_Ramp") else "deck_join")
        return cls, best

    # geometric runs (open water = outside the forecourt and not in the spine, pier or ramp) ...
    ramp = pf1["site"]["ramp"]
    ramp_poly = rect(ramp["x"][0], ramp["x"][1], ramp["y"][0], ramp["y"][1])
    others = {"spine": spine, "pier": pier, "ramp": ramp_poly}
    runs = []
    for i in range(len(P)):
        a, b, L, u, n = edge_frame(P, i)
        ts = [k * 5.0 for k in range(int(L // 5.0) + 1)]
        if L - ts[-1] > 0.01:
            ts.append(L)

        def wet(t):
            x, y = a[0] + u[0] * t + n[0] * 3.0, a[1] + u[1] * t + n[1] * 3.0
            return not any(inside(x, y, poly) for poly in others.values())
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
                for _ in range(16):
                    mid = (lo + hi) / 2.0
                    lo, hi = (lo, mid) if wet(mid) else (mid, hi)
                t0 = hi
            if j < len(ts) - 1:
                lo, hi = ts[j], ts[j + 1]
                for _ in range(16):
                    mid = (lo + hi) / 2.0
                    lo, hi = (mid, hi) if wet(mid) else (lo, mid)
                t1 = lo
            if t1 - t0 >= 1.0:
                runs.append({"edge": i, "t0": round(t0, 2), "t1": round(t1, 2), "L": L, "a": a, "u": u, "n": n})
            k = j + 1
    # ... checked against the probe's real traces: every probe sample more than 30 cm from a run end must be
    # water where the geometry says water, and a join where it says join
    agree, disagree = 0, []
    for e in probe_edges:
        for smp in e["samples"]:
            hs = [h for h in smp["outside"]["30"] if not h.get("overlap")]
            lab = hs[0]["actor"] if hs else None
            probe_water = lab == "IB_Harbor_Surface"
            geo, near_end = False, False
            for r in runs:
                x0, y0 = pt(r, r["t0"])
                x1, y1 = pt(r, r["t1"])
                if seg_dist(smp["x"], smp["y"], x0, y0, x1, y1) < 1.0:
                    geo = True
                    if min(math.hypot(smp["x"] - x0, smp["y"] - y0), math.hypot(smp["x"] - x1, smp["y"] - y1)) < 30.0:
                        near_end = True
            if near_end:
                continue
            if geo == probe_water:
                agree += 1
            else:
                disagree.append([smp["x"], smp["y"], lab, "geometry says %s" % ("water" if geo else "join")])
    water_check = {"probe_samples_agreeing": agree, "disagreements": disagree[:20], "disagreement_count": len(disagree)}
    if disagree:
        problems.append("%d outline sample(s) where the probe's traces and the geometric water runs disagree" % len(disagree))

    # ---- keep-outs --------------------------------------------------------------------------------
    gate_box = box_of("SM_MainGate_Tripo")
    medical_box, barracks_box, armory_box = box_of("Medical"), box_of("Barracks"), box_of("Armory")
    buildings = {"Medical": medical_box, "Barracks": barracks_box, "Armory": armory_box, "SM_MainGate_Tripo": gate_box}

    def grow(poly, g):
        x0, x1, y0, y1 = bbox(poly)
        return rect(x0 - g, x1 + g, y0 - g, y1 + g)

    def depth_to(r, t, poly, limit):
        """How far inboard from the edge at t the strip may reach before it meets poly (limit if it never does)."""
        c = 0.0
        while c <= limit:
            if inside(*pt(r, t, c), poly):
                return c
            c += 1.0
        return None
    for r in runs:
        r["coping_cuts"], r["line_cuts"], r["coping_in"], r["why"] = [], [], COPING_IN, []
        mx, my = pt(r, (r["t0"] + r["t1"]) / 2.0)
        if mx < -500.0 - 1.0:
            # the rear protrusion around the land ramp: its flanks lie under the gatehouse's visual box
            r["coping_cuts"].append([0.0, r["L"]])
            r["line_cuts"].append([0.0, r["L"]])
            r["why"].append("gatehouse flank beside the land ramp: fascia only")
            continue
        # the hangar reservation's rear outline lies on the rear edge: no curb or edge line along it
        kp = rect(rx0 - RESERVE_KEEP, rx1, ry0 - RESERVE_KEEP, ry1 + RESERVE_KEEP)
        for iv in interval_on_edge(r, kp, COPING_IN, COPING_LIP):
            r["coping_cuts"].append(iv)
            r["line_cuts"].append(iv)
            if iv[1] > r["t0"] and iv[0] < r["t1"]:
                r["why"].append("hangar reservation's rear outline on the edge: fascia only for t %s" % [r1(v) for v in iv])
        # buildings: a curb stays 5 cm clear of a building's VISUAL box (narrower if it must, never under 30 cm);
        # an edge line stops 1 m short of it
        for labx, bp in buildings.items():
            if not bp:
                continue
            gp = grow(bp, 5.0)
            t, depth = r["t0"], None
            while t <= r["t1"] + 1e-6:
                dd = depth_to(r, t, gp, COPING_IN)
                if dd is not None:
                    depth = dd if depth is None else min(depth, dd)
                t += 10.0
            if depth is not None:
                if depth >= 30.0:
                    r["coping_in"] = min(r["coping_in"], math.floor(depth))
                    r["why"].append("curb narrowed to %.0f cm along the run: %s's visual box is %.0f cm from the edge"
                                    % (r["coping_in"], labx, depth - 0.0 + 5.0))
                else:
                    for iv in interval_on_edge(r, gp, COPING_IN, COPING_LIP):
                        r["coping_cuts"].append(iv)
                    r["why"].append("no curb where %s's visual box is under 35 cm from the edge" % labx)
            for iv in interval_on_edge(r, grow(bp, BUILDING_LINE_KEEP), EDGE_LINE_INSET + LINE_HALF, 0.0):
                r["line_cuts"].append(iv)
                if iv[1] > r["t0"] and iv[0] < r["t1"]:
                    r["why"].append("edge line stops 1 m short of %s for t %s" % (labx, [r1(v) for v in iv]))
    for r in runs:
        r["coping_parts"] = subtract([r["t0"], r["t1"]], r["coping_cuts"])
        r["line_parts"] = subtract([r["t0"], r["t1"]], r["line_cuts"])

    # existing PF1 finish pieces (all present in YM1): copings, fascias, marks
    pf_pieces = pf1["pieces"]
    ex_coping = [p for p in pf_pieces if p["kind"] == "coping"]
    ex_fascia = [p for p in pf_pieces if p["kind"] == "fascia"]
    ex_marks = [p for p in pf_pieces if p["material"] == SHARED_MARK]
    ex_ring = [p for p in ex_marks if p["label"].startswith("IBGC_Pad_Ring_")]
    ex_marks_nonring = [p for p in ex_marks if p not in ex_ring]

    # neighbours at the concave join corners: the pier's and spine's own water runs (PF1 pieces)
    def pf_line_at(y_centre):
        for p in ex_marks_nonring:
            if p["kind"] == "edge_line":
                x0, x1, y0, y1 = bbox(p["footprint"])
                if abs((y0 + y1) / 2.0 - y_centre) < 1.0 and abs(x0 - x_sea) < 1.0:
                    return p
        return None

    def pf_coping_at(y_edge):
        for p in ex_coping:
            x0, x1, y0, y1 = bbox(p["footprint"])
            if abs(x0 - x_sea) < 1.0 and (abs(y0 + COPING_LIP - y_edge) < 1.0 or abs(y1 - COPING_LIP - y_edge) < 1.0):
                return p
        return None

    def pf_fascia_at(y_edge):
        for p in ex_fascia:
            x0, x1, y0, y1 = bbox(p["footprint"])
            if abs(x0 - x_sea) < 1.0 and (abs(y0 + FASCIA_OUT - y_edge) < 1.0 or abs(y1 - FASCIA_OUT - y_edge) < 1.0):
                return p
        return None

    joins = []  # concave corners on the seaward edge where a water run meets a pier/spine water edge
    for zone, poly in (("pier", pier), ("spine", spine)):
        _, _, y0, y1 = bbox(poly)
        for y_edge, inboard in ((y0, +1.0), (y1, -1.0)):
            joins.append({"zone": zone, "y_edge": y_edge, "inboard": inboard,
                          "line": pf_line_at(y_edge + inboard * EDGE_LINE_INSET),
                          "coping": pf_coping_at(y_edge), "fascia": pf_fascia_at(y_edge)})

    def join_at(r, end):
        x, y = pt(r, r[end])
        if abs(x - x_sea) > 1.0:
            return None
        for j in joins:
            if abs(y - j["y_edge"]) < 1.0:
                return j
        return None

    # link consecutive runs of the forecourt at convex corners (same outline vertex)
    for r in runs:
        r["prev"] = r["next"] = None
    for r in runs:
        e1 = pt(r, r["t1"])
        for q in runs:
            if q is not r and math.hypot(e1[0] - pt(q, q["t0"])[0], e1[1] - pt(q, q["t0"])[1]) < 2.0:
                r["next"], q["prev"] = q, r

    def has_part(q, parts_key, end):
        """Does run q's coping / line reach its own end `end`?"""
        return any(abs((p0 if end == "t0" else p1) - q[end]) < 1e-6 for p0, p1 in q[parts_key])

    def neighbour(r, end, parts_key):
        """The adjoining run at this end if it carries the same treatment up to the shared corner."""
        q = r["prev"] if end == "t0" else r["next"]
        if q is None:
            return None
        return q if has_part(q, parts_key, "t1" if end == "t0" else "t0") else None

    count = {}

    def lab(kind):
        count[kind] = count.get(kind, -1) + 1
        return "Fore_%s_%02d" % (kind, count[kind])

    coping, fascia, lines, stubs = [], [], [], []
    run_report = []
    for r in runs:
        r["fascia_parts"] = [[r["t0"], r["t1"]]]
    for r in runs:
        a_, u_, n_ = r["a"], r["u"], r["n"]

        def strip(label, kind, s0, s1, c0, c1, top, bottom, material, collision, a_=a_, u_=u_, n_=n_):
            cx = a_[0] + u_[0] * (s0 + s1) / 2.0 + n_[0] * (c0 + c1) / 2.0
            cy = a_[1] + u_[1] * (s0 + s1) / 2.0 + n_[1] * (c0 + c1) / 2.0
            return box_piece(label, "forecourt", kind, cx, cy, (s1 - s0) / 2.0, (c1 - c0) / 2.0, top, bottom,
                             math.degrees(math.atan2(u_[1], u_[0])), material, collision)

        def mitre(end, amount, parts_key, r=r):
            q = neighbour(r, end, parts_key)
            if q is None:
                return 0.0
            phi = turn(r["u"], q["u"])
            return amount * math.tan(phi / 2.0) + 0.5 if phi > 1e-3 else 0.0

        def join_t(y_target, r=r):
            return (y_target - r["a"][1]) / r["u"][1]
        rep = {"edge": r["edge"], "from": [r1(v) for v in pt(r, r["t0"])], "to": [r1(v) for v in pt(r, r["t1"])],
               "length": r1(r["t1"] - r["t0"]), "coping_in": r["coping_in"], "coping_parts": [], "line_parts": [],
               "fascia": None, "ends": {}, "notes": r["why"]}
        for end in ("t0", "t1"):
            q = r["prev"] if end == "t0" else r["next"]
            j = join_at(r, end)
            rep["ends"][end] = ("corner %.0f deg" % math.degrees(turn(r["u"], q["u"]))) if q is not None else \
                ("join with the %s (existing PF1 finish)" % j["zone"]) if j is not None else "free end"
        # fascia
        s0, s1 = r["t0"] - mitre("t0", FASCIA_OUT, "fascia_parts"), r["t1"] + mitre("t1", FASCIA_OUT, "fascia_parts")
        for end in ("t0", "t1"):
            j = join_at(r, end)
            if j is not None and j["fascia"] is not None:
                y_face = j["y_edge"] - j["inboard"] * FASCIA_OUT
                if end == "t0":
                    s0 = join_t(y_face) + 0.5
                else:
                    s1 = join_t(y_face) - 0.5
        fascia.append(strip(lab("Fascia"), "fascia", s0, s1, -FASCIA_IN, FASCIA_OUT, DECK_Z - COPING_DROP + 1.0,
                            -35.0 - FASCIA_BELOW_WATER, BASTION_CONCRETE, "NoCollision"))
        rep["fascia"] = [r1(s0), r1(s1)]
        # coping: the water runs minus the keep-outs; an isolated short piece is not laid
        for (c0_, c1_) in r["coping_parts"]:
            s0, s1 = c0_, c1_
            at0, at1 = abs(c0_ - r["t0"]) < 1e-6, abs(c1_ - r["t1"]) < 1e-6
            linked0 = at0 and (neighbour(r, "t0", "coping_parts") is not None or
                               (join_at(r, "t0") or {}).get("coping") is not None)
            linked1 = at1 and (neighbour(r, "t1", "coping_parts") is not None or
                               (join_at(r, "t1") or {}).get("coping") is not None)
            if not linked0 and not linked1 and c1_ - c0_ < MIN_ISOLATED:
                constraints.append("curb fragment on edge %d (%.0f cm) not laid: isolated between keep-outs (%s)"
                                   % (r["edge"], c1_ - c0_, "; ".join(r["why"]) or "free ends"))
                continue
            if at0:
                s0 = c0_ - mitre("t0", COPING_LIP, "coping_parts")
            if at1:
                s1 = c1_ + mitre("t1", COPING_LIP, "coping_parts")
            for end in ("t0", "t1"):
                j = join_at(r, end)
                if j is not None and j["coping"] is not None and (at0 if end == "t0" else at1):
                    y_in = j["y_edge"] + j["inboard"] * COPING_IN       # the neighbour curb's inboard face
                    if end == "t0":
                        s0 = join_t(y_in) + 0.5
                    else:
                        s1 = join_t(y_in) - 0.5
            if s1 - s0 > 1.0:
                coping.append(strip(lab("Coping"), "coping", s0, s1, -r["coping_in"], COPING_LIP, DECK_Z + COPING_RISE,
                                    DECK_Z - COPING_DROP, BASTION_CONCRETE, "BlockAll"))
                rep["coping_parts"].append([r1(s0), r1(s1)])
        # edge line: inset 100 cm; meets a neighbour's line at the inset corner (PF1); at a join it stops at
        # the existing pier/spine edge line, to which a short stub on the forecourt connects it
        p0 = pt(r, 0.0, EDGE_LINE_INSET)
        for (c0_, c1_) in r["line_parts"]:
            ss = {"t0": c0_, "t1": c1_}
            linked = {"t0": False, "t1": False}
            for end in ("t0", "t1"):
                if abs(ss[end] - r[end]) > 1e-6:
                    continue                     # a cut end: stop where the keep-out begins
                q = neighbour(r, end, "line_parts")
                j = join_at(r, end)
                if q is not None:
                    phi = turn(r["u"], q["u"])
                    m = meet(p0, r["u"], pt(q, 0.0, EDGE_LINE_INSET), q["u"])
                    if m is not None:
                        ss[end] = m + (LINE_HALF * math.tan(phi / 2.0) if phi > 1e-3 else 0.0) * (1 if end == "t1" else -1)
                        linked[end] = True
                elif j is not None and j["line"] is not None:
                    y_c = j["y_edge"] + j["inboard"] * EDGE_LINE_INSET          # the existing line's centre
                    tt = join_t(y_c)
                    ss[end] = tt - LINE_HALF if end == "t1" else tt + LINE_HALF  # its near edge
                    x_line = x_sea - EDGE_LINE_INSET
                    stubs.append(line_piece(lab("EdgeStub"), "forecourt", "edge_stub", (x_line - LINE_HALF, y_c),
                                            (x_sea, y_c), LINE_HALF, mi_obj))
                    linked[end] = True
            L = ss["t1"] - ss["t0"]
            if L <= LINE_HALF:
                continue
            if not linked["t0"] and not linked["t1"] and L < MIN_ISOLATED:
                constraints.append("edge-line fragment on edge %d (%.0f cm) not laid: isolated between keep-outs" % (r["edge"], L))
                continue
            lines.append(line_piece(lab("EdgeLine"), "forecourt", "edge_line", pt(r, ss["t0"], EDGE_LINE_INSET),
                                    pt(r, ss["t1"], EDGE_LINE_INSET), LINE_HALF, mi_obj))
            rep["line_parts"].append([r1(ss["t0"]), r1(ss["t1"])])
        run_report.append(rep)

    # ---- roads and routes ---------------------------------------------------------------------------
    marks = []
    spine_lines = sorted([p for p in ex_marks_nonring if p["kind"] == "lane_line" and p["zone"] == "spine"],
                         key=lambda p: bbox(p["footprint"])[2])
    pier_lines = sorted([p for p in ex_marks_nonring if p["kind"] == "lane_line" and p["zone"] == "pier"],
                        key=lambda p: bbox(p["footprint"])[2])
    axis_ys = [(bbox(p["footprint"])[2] + bbox(p["footprint"])[3]) / 2.0 for p in spine_lines]
    gate_ys = [(bbox(p["footprint"])[2] + bbox(p["footprint"])[3]) / 2.0 for p in pier_lines]
    if len(axis_ys) != 2 or len(gate_ys) != 2:
        problems.append("expected two spine and two pier lane lines in the PF1 plan, found %d and %d"
                        % (len(axis_ys), len(gate_ys)))
    gate_door = one("BP_MainGateDoor")
    gate_x0 = (gate_box and bbox(gate_box)[1] or 744.0) + 300.0           # 3 m inside the gatehouse's visual box
    axis_x0 = rx1                                                           # the reservation's front outline
    for k, y in enumerate(axis_ys):
        marks.append(line_piece("Fore_AxisLine_%02d" % k, "forecourt", "axis_line", (axis_x0, y), (x_sea, y),
                                LINE_HALF, mi_obj))
    for k, y in enumerate(gate_ys):
        marks.append(line_piece("Fore_GateLine_%02d" % k, "forecourt", "gate_line", (gate_x0, y), (x_sea, y),
                                LINE_HALF, mi_obj))
    # cross-road: its landward line, 8 m clear of the edge line
    x_edge_line_in = x_sea - EDGE_LINE_INSET - LINE_HALF
    x_cross = x_edge_line_in - CROSS_ROAD_CLEAR - LINE_HALF
    y_start = -2500.0 + EDGE_LINE_INSET - LINE_HALF                         # meets the -Y edge line
    y_end = (bbox(medical_box)[2] if medical_box else 5000.0) - 100.0      # 1 m short of Medical's corner
    gaps = [[min(gate_ys) - LINE_HALF, max(gate_ys) + LINE_HALF], [min(axis_ys) - LINE_HALF, max(axis_ys) + LINE_HALF]]
    segs = subtract([y_start, y_end], gaps)
    for k, (a, b) in enumerate(segs):
        marks.append(line_piece("Fore_CrossLine_%02d" % k, "forecourt", "cross_line", (x_cross, a), (x_cross, b),
                                LINE_HALF, mi_obj))
    # centre dashes of the cross-road, not across the two through roads
    x_mid = (x_cross + LINE_HALF + x_edge_line_in) / 2.0
    dash_segs = subtract([y_start + LINE_HALF * 2, y_end], [[g0 - 100.0, g1 + 100.0] for g0, g1 in gaps])
    nd = 0
    for a, b in dash_segs:
        L = b - a
        n = int((L - DASH_LEN) // DASH_PERIOD) + 1 if L >= DASH_LEN else 0
        if n <= 0:
            continue
        span = DASH_LEN + (n - 1) * DASH_PERIOD
        s = a + (L - span) / 2.0 + DASH_LEN / 2.0
        for _ in range(n):
            marks.append(line_piece("Fore_CrossDash_%02d" % nd, "forecourt", "cross_dash", (x_mid, s - DASH_LEN / 2.0),
                                    (x_mid, s + DASH_LEN / 2.0), DASH_HALF_W, mi_obj))
            nd += 1
            s += DASH_PERIOD
    # door bars and route dashes to the three forecourt buildings' doors
    doors = []
    for dlab, blab, side in (("Barracks_DoorFrame", "Barracks", "+Y"), ("Armory_DoorFrame", "Armory", "-Y"),
                             ("Medical_DoorFrame", "Medical", "-X")):
        d = one(dlab)
        if not d:
            continue
        o, e = d["bounds_all"]["origin"], d["bounds_all"]["extent"]
        if side == "+Y":
            face, c, bar = o[1] + e[1], o[0], None
            y = face + DOOR_BAR_FRONT
            bar = ((c - DOOR_BAR_LEN / 2.0, y), (c + DOOR_BAR_LEN / 2.0, y))
            out_pt = (c, y + LINE_HALF)
        elif side == "-Y":
            face, c = o[1] - e[1], o[0]
            y = face - DOOR_BAR_FRONT
            bar = ((c - DOOR_BAR_LEN / 2.0, y), (c + DOOR_BAR_LEN / 2.0, y))
            out_pt = (c, y - LINE_HALF)
        else:
            face, c = o[0] - e[0], o[1]
            x = face - DOOR_BAR_FRONT
            bar = ((x, c - DOOR_BAR_LEN / 2.0), (x, c + DOOR_BAR_LEN / 2.0))
            out_pt = (x - LINE_HALF, c)
        doors.append({"door": dlab, "building": blab, "side": side, "face": r1(face), "centre": r1(c),
                      "bar": [[r1(v) for v in bar[0]], [r1(v) for v in bar[1]]], "out": [r1(v) for v in out_pt]})
        marks.append(line_piece("Fore_DoorBar_%s" % blab, "forecourt", "door_bar", bar[0], bar[1], LINE_HALF, mi_obj))
    routes = []
    gate_line_neg = min(gate_ys) - LINE_HALF          # the gate road's -Y line, outer edge
    axis_line_pos = max(axis_ys) + LINE_HALF          # the axis road's +Y line, outer edge
    for d in doors:
        ox, oy = d["out"]
        if d["building"] == "Barracks":
            legs = [((ox, gate_line_neg), (ox, oy))]
        elif d["building"] == "Armory":
            legs = [((ox, axis_line_pos), (ox, oy))]
        else:
            x_leg = ox - 596.0                         # one 300 cm dash fits the last leg with equal gaps
            legs = [((x_leg, axis_line_pos), (x_leg, oy)), ((x_leg, oy), (ox, oy))]
        routes.append({"to": d["door"], "legs": [[[r1(v) for v in p0], [r1(v) for v in p1]] for p0, p1 in legs]})
    nr = 0
    for rt in routes:
        for (ax_, ay_), (bx_, by_) in rt["legs"]:
            L = math.hypot(bx_ - ax_, by_ - ay_)
            ux, uy = (bx_ - ax_) / L, (by_ - ay_) / L
            n = int((L - DASH_LEN) // DASH_PERIOD) + 1 if L >= DASH_LEN else 0
            if n <= 0:
                constraints.append("route leg to %s is %.0f cm: too short for a 300 cm dash; left unmarked" % (rt["to"], L))
                continue
            span = DASH_LEN + (n - 1) * DASH_PERIOD
            s = (L - span) / 2.0 + DASH_LEN / 2.0
            for _ in range(n):
                cx_, cy_ = ax_ + ux * s, ay_ + uy * s
                marks.append(line_piece("Fore_RouteDash_%02d" % nr, "forecourt", "route_dash",
                                        (cx_ - ux * DASH_LEN / 2.0, cy_ - uy * DASH_LEN / 2.0),
                                        (cx_ + ux * DASH_LEN / 2.0, cy_ + uy * DASH_LEN / 2.0), DASH_HALF_W, mi_obj))
                nr += 1
                s += DASH_PERIOD

    # ---- the pad ring: 96 thin segments, same radius and width ----------------------------------------
    pad_c = design["pad"]["centre"]
    ring_r = 0.7 * design["pad"]["inradius"]
    ring_w = 2.0 * 20.0
    fp_by_label = {}
    for key, v in basefp.items():
        fp_by_label.setdefault(v["label"], []).append((key, v))
    ring_edits, ring_new = [], []
    half_len = (ring_r + ring_w / 2.0) * math.sin(math.pi / RING_SEGMENTS)     # outer corners meet exactly
    for s in range(RING_SEGMENTS):
        a = 2.0 * math.pi * s / RING_SEGMENTS
        top = DECK_Z + (RING_TOP_EVEN if s % 2 == 0 else RING_TOP_ODD)
        bottom = DECK_Z + RING_BOTTOM
        cx, cy = pad_c[0] + ring_r * math.cos(a), pad_c[1] + ring_r * math.sin(a)
        yaw = math.degrees(a) + 90.0
        spec = box_piece("Pad_Ring96_%02d" % s, "pad", "ring_segment", cx, cy, half_len, ring_w / 2.0, top, bottom,
                         yaw, mi_obj, "NoCollision")
        if s % 3 == 0:
            old_label = "IBGC_Pad_Ring_%02d" % (s // 3)
            rows = fp_by_label.get(old_label) or []
            if len(rows) != 1:
                problems.append("base fingerprint: %d actor(s) labelled %s" % (len(rows), old_label))
                continue
            key, v = rows[0]
            old_plan = [p for p in ex_ring if p["label"] == old_label]
            to = {"loc": spec["location"], "rot": spec["rotation"], "scale": spec["scale"]}
            fr = {"loc": v["loc"], "rot": {"roll": v["rot"][0], "pitch": v["rot"][1], "yaw": v["rot"][2]}, "scale": v["scale"]}
            if old_plan:
                op = old_plan[0]
                if math.hypot(op["location"][0] - spec["location"][0], op["location"][1] - spec["location"][1]) > 0.2:
                    problems.append("%s: the new segment centre is %.1f cm from the old one" % (old_label, math.hypot(
                        op["location"][0] - spec["location"][0], op["location"][1] - spec["location"][1])))
            ring_edits.append({"label": old_label, "actor_key": key, "segment": s, "from": fr, "to": to,
                               "footprint_to": spec["footprint"], "top_z_to": spec["top_z"], "bottom_z_to": spec["bottom_z"],
                               "half_extent_to": spec["half_extent"]})
        else:
            ring_new.append(spec)

    # ---- material assignments: every generated marking of the base -> the new instance ---------------
    assignments, inherited = [], []
    for key, v in sorted(basefp.items()):
        comps = v.get("components") or {}
        for cn, c in comps.items():
            mats = c.get("materials") or []
            if base_mi_obj in mats:
                if RUN_TAG not in (v.get("tags") or []):
                    problems.append("%s carries the base paint but not the run tag" % v["label"])
                    continue
                assignments.append({"label": v["label"], "actor_key": key, "run_tag": RUN_TAG, "component": cn, "slot": 0,
                                    "slots": len(mats), "mesh": c.get("mesh"), "collision_profile": c.get("profile"),
                                    "from": mats[0], "from_overrides": c.get("overrides"), "to": mi_obj})
            elif SHARED_MARK in mats:
                inherited.append({"label": v["label"], "actor_key": key, "component": cn})
    if len(assignments) != 91:
        problems.append("expected the 91 generated markings on %s, found %d" % (base_mi_obj, len(assignments)))
    for a in assignments:
        if a["from"] != base_mi_obj or a["from_overrides"] != [base_mi_obj] or a["slots"] != 1:
            problems.append("%s: slot 0 %s, overrides %s" % (a["label"], a["from"], a["from_overrides"]))
        if a["collision_profile"] != "NoCollision":
            problems.append("%s: collision %s" % (a["label"], a["collision_profile"]))

    # ---- no coplanar overlaps -------------------------------------------------------------------------
    fixed_marks = [(p, int(round((p["top_z"] - EXISTING_MARK_TOP) / MARK_STEP))) for p in ex_marks_nonring]
    new_marks = lines + stubs + marks
    lv = stagger(new_marks, fixed_marks)
    new_marks = [restack(p, EXISTING_MARK_TOP + MARK_STEP * lv[p["label"]]) if lv[p["label"]] else p for p in new_marks]
    fixed_cop = [(p, int(round((p["top_z"] - (DECK_Z + COPING_RISE)) / COPING_STEP))) for p in ex_coping]
    lvc = stagger(coping, fixed_cop)
    coping = [restack(p, DECK_Z + COPING_RISE + COPING_STEP * lvc[p["label"]]) if lvc[p["label"]] else p for p in coping]
    fixed_f = [(p, 0) for p in ex_fascia]
    lvf = stagger(fascia, fixed_f)
    fascia = [refascia(p, lvf[p["label"]]) if lvf[p["label"]] else p for p in fascia]

    pieces = coping + fascia + new_marks + ring_new
    # ---- checks ---------------------------------------------------------------------------------------
    checks = {"outline_vs_actual_decks": outline_check, "water_runs_vs_probe": water_check}
    labels = [p["label"] for p in pieces]
    if len(set(labels)) != len(labels):
        problems.append("duplicate labels in the plan")
    existing_labels = set(v["label"] for v in basefp.values())
    clash = sorted(set(labels) & existing_labels)
    if clash:
        problems.append("labels already used in the base: %s" % clash[:5])
    # every paint piece and every curb's deck part lies on deck (forecourt, spine or pier; the ring on the pad)
    deck_union = [fore, spine, pier]
    pc, pa = design["pad"]["centre"], design["pad"]["inradius"]
    ph = pa * math.tan(math.radians(22.5))
    pad_poly = [(pc[0] - pa, pc[1] - ph), (pc[0] - ph, pc[1] - pa), (pc[0] + ph, pc[1] - pa), (pc[0] + pa, pc[1] - ph),
                (pc[0] + pa, pc[1] + ph), (pc[0] + ph, pc[1] + pa), (pc[0] - ph, pc[1] + pa), (pc[0] - pa, pc[1] + ph)]
    off_deck = []
    for p in new_marks + ring_new:
        polys = deck_union if p["zone"] != "pad" else [pad_poly] if pad_poly else deck_union
        for x, y in p["footprint"]:
            cx_, cy_ = p["location"][0], p["location"][1]
            xi, yi = x + (cx_ - x) * 0.02, y + (cy_ - y) * 0.02
            if not any(poly and inside(xi, yi, poly) for poly in polys):
                off_deck.append(p["label"])
                break
    checks["paint_off_deck"] = off_deck
    if off_deck:
        problems.append("%d paint piece(s) not on deck: %s" % (len(off_deck), off_deck[:5]))
    # obstacles: every building's visual box, door frames, props, spawn, the reservation for curbs
    obstacles = {}
    for labx in ("Medical", "Barracks", "Armory", "SM_MainGate_Tripo", "Medical_DoorFrame", "Barracks_DoorFrame",
                 "Armory_DoorFrame", "BP_MainGateDoor", "BP_WeaponRack", "PlayerStart", "Cube", "Cube2", "Cube3",
                 "Helicopter", "Docks_Crane_01", "SM_Truck_Cargo", "SM_Truck_Cargo2", "SM_Truck_Cargo3", "SM_Truck_Cargo4",
                 "Docks_Ship_Hull"):
        b = box_of(labx)
        if b:
            obstacles[labx] = b
    zr = {}
    for labx in obstacles:
        a = one(labx)
        o, e = a["bounds_all"]["origin"], a["bounds_all"]["extent"]
        zr[labx] = (o[2] - e[2], o[2] + e[2])
    hits = []
    for p in pieces:
        for labx, b in obstacles.items():
            if p["kind"] == "door_bar" and labx.endswith("DoorFrame"):
                continue
            if labx == "PlayerStart" and p["kind"] in ("axis_line",):
                continue
            if labx == "Helicopter" and p["kind"] == "ring_segment":
                continue
            # a 3D test: plan-view overlap AND overlapping heights (the gatehouse starts at z 376; the fascia
            # below it ends at z 356)
            if obb_overlap(p["footprint"], b, eps=0.0) and p["bottom_z"] < zr[labx][1] and p["top_z"] > zr[labx][0]:
                hits.append("%s overlaps %s" % (p["label"], labx))
    checks["overlaps_with_actors"] = hits
    if hits:
        problems.append("%d new piece(s) overlap existing actors: %s" % (len(hits), hits[:5]))
    # nothing of the curb or paint sits across the land ramp, the pier entrance or the spine entrance
    blocking = [p for p in coping]
    # the open spans: the land ramp's whole width; the pier and spine entrances between their own existing
    # curbs' inboard faces (those curbs already turn the corners on the pier and spine side)
    open_joins = {"land ramp": rect(-1250.0 - 1.0, -1250.0 + 1.0, -1000.0, 500.0),
                  "pier entrance": rect(x_sea - 1.0, x_sea + 1.0, bbox(pier)[2] + COPING_IN, bbox(pier)[3] - COPING_IN),
                  "spine entrance": rect(x_sea - 1.0, x_sea + 1.0, bbox(spine)[2] + COPING_IN, bbox(spine)[3] - COPING_IN)}
    across = []
    for p in blocking:
        for nm, jp in open_joins.items():
            if obb_overlap(p["footprint"], jp, eps=0.0):
                across.append("%s crosses the %s" % (p["label"], nm))
    checks["curbs_across_openings"] = across
    if across:
        problems.append("; ".join(across))
    # route and road clearances from obstacles (buildings, door frames except at their own bar, props)
    clear = {}
    for p in new_marks:
        if p["kind"] not in ("route_dash", "door_bar", "cross_line", "cross_dash", "axis_line", "gate_line"):
            continue
        best, who = None, None
        for labx, b in obstacles.items():
            if labx in ("PlayerStart",) or (p["kind"] == "door_bar" and labx.endswith("DoorFrame")):
                continue
            d = poly_dist(p["footprint"], b)
            if best is None or d < best:
                best, who = d, labx
        clear[p["label"]] = [r1(best), who]
    checks["paint_clearance_to_obstacles"] = clear
    tight = {k: v for k, v in clear.items() if v[0] < ROUTE_CLEAR and not k.endswith(("DoorBar_Barracks", "DoorBar_Armory",
                                                                                         "DoorBar_Medical"))}
    if tight:
        problems.append("paint closer than %.0f cm to an obstacle: %s" % (ROUTE_CLEAR, list(tight.items())[:4]))
    # curbs' clearance to building faces (actual collision faces from the probe)
    face_gap = {}
    for p in coping:
        best, who = None, None
        for labx in ("Medical", "Barracks", "Armory"):
            b = obstacles.get(labx)
            if b:
                d = poly_dist(p["footprint"], b)
                if best is None or d < best:
                    best, who = d, labx
        face_gap[p["label"]] = [r1(best), who]
    checks["coping_gap_to_building_visual_box"] = face_gap
    # corridors (painted, geometric; the engine lane scan measures the real ones)
    def band_clear(x0, x1, y0, y1, axis):
        """Nearest obstacle box to a road band [x0,x1] x [y0,y1] (inside it means 0)."""
        band = rect(x0, x1, y0, y1)
        res = []
        for labx, b in obstacles.items():
            if labx == "PlayerStart":
                continue
            res.append((r1(poly_dist(band, b)), labx))
        res.sort()
        return res[:3]
    gy0, gy1 = min(gate_ys) + LINE_HALF, max(gate_ys) - LINE_HALF
    ay0, ay1 = min(axis_ys) + LINE_HALF, max(axis_ys) - LINE_HALF
    corridors = {
        "axis_road": {"x": [axis_x0, x_sea], "y": [ay0, ay1], "painted_clear_width": r1(ay1 - ay0),
                      "nearest_obstacles": band_clear(axis_x0, x_sea, ay0, ay1, "x"),
                      "continues": "the spine's lane lines (y %s) from x %.0f" % ([r1(v) for v in axis_ys], x_sea)},
        "gate_road": {"x": [gate_x0, x_sea], "y": [gy0, gy1], "painted_clear_width": r1(gy1 - gy0),
                      "nearest_obstacles": band_clear(gate_x0, x_sea, gy0, gy1, "x"),
                      "continues": "the pier's 6 m service-lane lines (y %s) from x %.0f" % ([r1(v) for v in gate_ys], x_sea)},
        "cross_road": {"x": [x_cross + LINE_HALF, x_edge_line_in], "y": [y_start, y_end],
                       "painted_clear_width": r1(x_edge_line_in - x_cross - LINE_HALF),
                       "nearest_obstacles": band_clear(x_cross + LINE_HALF, x_edge_line_in, y_start, y_end, "y")},
    }
    for c in corridors.values():
        if c["nearest_obstacles"] and c["nearest_obstacles"][0][0] < LANE_BUFFER:
            problems.append("a road band is within %.0f cm of %s" % (LANE_BUFFER, c["nearest_obstacles"][0][1]))
    # the ring: radius, width and clearance to the helicopter preserved
    heli = obstacles.get("Helicopter")
    ring_check = {"segments": RING_SEGMENTS, "radius": r1(ring_r), "width": ring_w, "segment_length": round(2 * half_len, 2),
                  "tops": [DECK_Z + RING_TOP_EVEN, DECK_Z + RING_TOP_ODD], "bottom": DECK_Z + RING_BOTTOM,
                  "old": {"segments": len(ex_ring), "top": ex_ring[0]["top_z"] if ex_ring else None,
                          "bottom": ex_ring[0]["bottom_z"] if ex_ring else None,
                          "segment_length": round(2 * ex_ring[0]["half_extent"][0], 2) if ex_ring else None,
                          "width": round(2 * ex_ring[0]["half_extent"][1], 2) if ex_ring else None},
                  "edits": len(ring_edits), "new": len(ring_new)}
    if heli:
        ring_check["helicopter_box_to_ring_min_cm"] = r1(min(poly_dist([tuple(v) for v in p["footprint"]], heli)
                                                             for p in ring_new + [{"footprint": e["footprint_to"]} for e in ring_edits]))
        ring_check["helicopter_box_to_old_ring_min_cm"] = r1(min(poly_dist([tuple(v) for v in p["footprint"]], heli)
                                                                 for p in ex_ring)) if ex_ring else None
    checks["ring"] = ring_check
    # inner-edge overlaps between neighbouring ring segments get different heights; outer corners meet
    ring_all = ring_new + [dict(label=e["label"], footprint=e["footprint_to"], top_z=e["top_z_to"]) for e in ring_edits]
    coplanar = []
    for i in range(len(ring_all)):
        for j in range(i + 1, len(ring_all)):
            p, q = ring_all[i], ring_all[j]
            if abs(p["top_z"] - q["top_z"]) < 0.05 and obb_overlap(p["footprint"], q["footprint"]):
                coplanar.append("%s/%s" % (p["label"], q["label"]))
    for p in new_marks:
        for q, lvq in fixed_marks:
            if abs(p["top_z"] - q["top_z"]) < 0.05 and obb_overlap(p["footprint"], q["footprint"]):
                coplanar.append("%s/%s" % (p["label"], q["label"]))
    for i in range(len(new_marks)):
        for j in range(i + 1, len(new_marks)):
            p, q = new_marks[i], new_marks[j]
            if abs(p["top_z"] - q["top_z"]) < 0.05 and obb_overlap(p["footprint"], q["footprint"]):
                coplanar.append("%s/%s" % (p["label"], q["label"]))
    for p in ring_all:
        for q in new_marks + [x for x, _ in fixed_marks]:
            if obb_overlap(p["footprint"], q["footprint"]):
                coplanar.append("ring %s touches %s" % (p["label"], q["label"]))
    checks["coplanar_overlaps"] = coplanar
    if coplanar:
        problems.append("%d coplanar overlap(s): %s" % (len(coplanar), coplanar[:4]))
    cop_all = coping + [p for p, _ in fixed_cop]
    cc = []
    for i in range(len(cop_all)):
        for j in range(i + 1, len(cop_all)):
            p, q = cop_all[i], cop_all[j]
            if abs(p["top_z"] - q["top_z"]) < 0.05 and obb_overlap(p["footprint"], q["footprint"]):
                cc.append("%s/%s" % (p["label"], q["label"]))
    checks["coplanar_coping_overlaps"] = cc
    if cc:
        problems.append("coplanar coping overlaps: %s" % cc[:4])
    # the gate road and the verified routes: the verified walks run inside the painted roads
    checks["verified_routes_inside_roads"] = {
        "forecourt -> pier (y 78.3..100)": gy0 <= 78.3 and 100.0 <= gy1,
        "city road -> gate -> forecourt (y -251, to x 1848)": "the gate road starts at x %.0f; the verified route runs at y -251, "
                                                               "%.0f cm from its -Y line" % (gate_x0, abs(-251.0 - min(gate_ys))),
        "PlayerStart / reservation mouth -> spine (y 3750..4024)": ay0 <= 3750.0 and 4024.0 <= ay1,
    }
    counts = {"coping": len(coping), "fascia": len(fascia), "edge_lines": len(lines), "edge_stubs": len(stubs),
              "axis_lines": sum(1 for p in new_marks if p["kind"] == "axis_line"),
              "gate_lines": sum(1 for p in new_marks if p["kind"] == "gate_line"),
              "cross_lines": sum(1 for p in new_marks if p["kind"] == "cross_line"),
              "cross_dashes": sum(1 for p in new_marks if p["kind"] == "cross_dash"),
              "route_dashes": sum(1 for p in new_marks if p["kind"] == "route_dash"),
              "door_bars": sum(1 for p in new_marks if p["kind"] == "door_bar"),
              "ring_new": len(ring_new), "ring_edits": len(ring_edits), "assignments": len(assignments),
              "pieces": len(pieces)}
    return {"schema": "ff1-forecourt-finish-plan/2026-09-30", "base": BASE_PKG, "target": TARGET_PKG,
            "material_instance": mi_pkg, "material_object": mi_obj, "base_material_object": base_mi_obj,
            "run_tag": RUN_TAG, "finish_tag": FF_TAG, "folder": FOLDER,
            "deck_z": DECK_Z, "water_z": -35.0,
            "dimensions": {"coping": "50 cm on the deck + 10 cm lip, top +8 cm (PF1)", "fascia": "6 cm proud, to 45 cm below water (PF1)",
                           "edge_line": "40 cm, centre 100 cm inboard (PF1)", "lines": "40 cm", "dashes": "300 x 40 cm every 600 cm",
                           "door_bars": "300 x 40 cm, centred 50 cm in front of the door frame",
                           "cross_road": "landward line 8 m clear of the edge line", "ring": "96 x %.1f cm segments, 40 cm wide, "
                           "0.5 / 0.6 cm proud (was 32 x %.1f cm, 1.5 cm proud)" % (2 * half_len, 2 * ex_ring[0]["half_extent"][0] if ex_ring else 0)},
            "runs": run_report, "doors": doors, "routes": routes, "corridors": corridors, "checks": checks,
            "pieces": pieces, "ring": {"edits": ring_edits, "new_labels": [p["label"] for p in ring_new]},
            "assignments": assignments, "inherited_users_left_untouched": inherited,
            "local_constraints": constraints, "notes": notes, "problems": problems, "counts": counts,
            "made_utc": datetime.datetime.utcnow().isoformat() + "Z"}


def render(plan, pf1, path, site=None):
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None
    x0, x1, y0, y1 = -1800.0, 19500.0, -3200.0, 10800.0
    S = 0.075                                     # px per cm
    W, H = int((y1 - y0) * S), int((x1 - x0) * S)
    img = Image.new("RGB", (W, H), (22, 44, 60))
    d = ImageDraw.Draw(img)

    def tp(x, y):                                 # reference framing: land at the top, image-right = -Y
        return ((y1 - y) * S, (x - x0) * S)

    def poly(pts, fill=None, outline=None, width=1):
        d.polygon([tp(x, y) for x, y in pts], fill=fill, outline=outline)
    des = pf1["design"]
    for p in pf1["pieces"]:
        if p["kind"] in ("deck", "filler", "ramp"):
            poly([tuple(v) for v in p["footprint"]], fill=(120, 120, 124))
    for p in pf1["pieces"]:
        if p["material"] == SHARED_MARK and not p["label"].startswith("IBGC_Pad_Ring_"):
            poly([tuple(v) for v in p["footprint"]], fill=(150, 130, 60))
        elif p["kind"] in ("coping",):
            poly([tuple(v) for v in p["footprint"]], fill=(170, 170, 170))
    if site:
        for a in site["actors"]:
            if a["label"] in ("Medical", "Barracks", "Armory", "SM_MainGate_Tripo", "Command", "Mess_Hall", "Helicopter",
                              "BP_WeaponRack", "PlayerStart") and a.get("bounds_all"):
                o, e = a["bounds_all"]["origin"], a["bounds_all"]["extent"]
                poly(rect(o[0] - e[0], o[0] + e[0], o[1] - e[1], o[1] + e[1]), outline=(230, 90, 90))
    for p in plan["pieces"]:
        col = (235, 170, 40) if p["material"].endswith("Amber") else (220, 220, 220)
        if p["kind"] == "fascia":
            col = (90, 200, 255)
        poly([tuple(v) for v in p["footprint"]], fill=col)
    for e in plan["ring"]["edits"]:
        poly([tuple(v) for v in e["footprint_to"]], fill=(255, 120, 40))
    img.save(path)
    return path


def main():
    site = json.loads(Path(arg("--site")).read_text(encoding="utf-8"))
    bfp_doc = json.loads(Path(arg("--basefp")).read_text(encoding="utf-8"))
    pf1 = json.loads(Path(arg("--pf1-plan")).read_text(encoding="utf-8"))
    out = Path(arg("--out"))
    out.mkdir(parents=True, exist_ok=True)
    mi = (arg("--mi") or DEFAULT_MI).split(".")[0]
    base_mi = (arg("--base-mi") or DEFAULT_BASE_MI).split(".")[0]
    basefp = bfp_doc["fingerprint"]
    plan = build(site, basefp, pf1, mi, base_mi)
    plan["inputs"] = {"site": {"file": arg("--site"), "sha256": sha(arg("--site")), "level": site.get("level"),
                               "level_sha256": site.get("sha256_before")},
                      "base_fingerprint": {"file": arg("--basefp"), "sha256": sha(arg("--basefp")),
                                           "package": bfp_doc.get("package"), "package_sha256": bfp_doc.get("sha256")},
                      "pf1_plan": {"file": arg("--pf1-plan"), "sha256": sha(arg("--pf1-plan"))},
                      "planner_sha256": sha(__file__)}
    if bfp_doc.get("package") != BASE_PKG:
        plan["problems"].append("the base fingerprint is of %s, not %s" % (bfp_doc.get("package"), BASE_PKG))
    if site.get("level") != BASE_PKG or site.get("sha256_before") != bfp_doc.get("sha256"):
        plan["problems"].append("the site probe (%s at %s...) is not of the fingerprinted base bytes (%s...)"
                                % (site.get("level"), str(site.get("sha256_before"))[:12], str(bfp_doc.get("sha256"))[:12]))
    data = json.dumps(plan, indent=1).encode("utf-8")
    (out / "ff1_plan.json").write_bytes(data)
    lines = ["FF1 forecourt finish plan", "base %s (%s...)" % (BASE_PKG, str(bfp_doc.get("sha256"))[:12]),
             "counts: %s" % json.dumps(plan["counts"]), "problems: %d" % len(plan["problems"])]
    lines += ["  PROBLEM " + p for p in plan["problems"]]
    lines += ["local constraint: " + c for c in plan["local_constraints"]]
    for r in plan["runs"]:
        lines.append("run edge %d %s -> %s (%.0f cm): coping %s, line %s, ends %s" % (
            r["edge"], r["from"], r["to"], r["length"], r["coping_parts"], r["line_parts"], r["ends"]))
    for k, c in plan["corridors"].items():
        lines.append("corridor %s: %s" % (k, json.dumps(c)))
    lines.append("ring: %s" % json.dumps(plan["checks"]["ring"]))
    (out / "ff1_plan_report.txt").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    render(plan, pf1, str(out / "ff1_plan.png"), site)
    print("\n".join(lines[:12]))
    print("plan sha256", hashlib.sha256(data).hexdigest().upper())
    return 0 if not plan["problems"] else 2


if __name__ == "__main__":
    sys.exit(main())
