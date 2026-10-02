"""NEXT PROPOSAL (plan only, never applied): a truly rear hangar reserve and a
populated left control platform, using complete existing assemblies.

    python Scripts/ib_garrison_rear_proposal.py --plan <baseline plan.json> --inventory <inventory dir> --out <dir>

The building-preserving baseline keeps every building where it is, so its hangar
reserve can only sit in front of Command and Mess_Hall (25.7 m deep) and its
control platform is empty. The approved reference has the hangar ON the rear edge
and a tower plus a low block on the control platform. This computes the smallest
concrete change that gets there:

  * Command (the site's tower) moves, with its door, onto the control platform,
    turned 90 degrees so its door faces the spine;
  * Mess_Hall moves, with its door, to a rear-left slot beside the hangar, door
    still facing the forecourt;
  * the hangar reserve then runs from the rear edge, centred on the spine axis.

An assembly is moved only if it is COMPLETE: the inventory must show nothing
inside or attached to the building except its own door (explicit label). The
Barracks' Cube/Cube2/Cube3 association is unresolved, so the Barracks never moves.
Every check here is geometric (the plan's own deck polygons); nothing is applied.
"""
import json, math, sys
from pathlib import Path


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


PLAN = Path(arg("--plan"))
INV = Path(arg("--inventory"))
OUT = Path(arg("--out", str(PLAN.parent / "proposal")))
MOVE = ("Command", "Mess_Hall")
CLEAR_BUILDING, CLEAR_ANCHOR, DOOR_APPROACH = 600.0, 300.0, 600.0


def obb(cx, cy, hx, hy, yaw):
    a = math.radians(yaw)
    c, s = math.cos(a), math.sin(a)
    return [(cx + sx * hx * c - sy * hy * s, cy + sx * hx * s + sy * hy * c) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def inside(x, y, P):
    h = False
    for i in range(len(P)):
        x1, y1 = P[i - 1]
        x2, y2 = P[i]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            h = not h
    return h


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def poly_dist(P, Q):
    if any(inside(x, y, Q) for x, y in P) or any(inside(x, y, P) for x, y in Q):
        return 0.0
    best = float("inf")
    for (x, y) in P:
        for j in range(len(Q)):
            best = min(best, seg_dist(x, y, Q[j - 1][0], Q[j - 1][1], Q[j][0], Q[j][1]))
    for (x, y) in Q:
        for i in range(len(P)):
            best = min(best, seg_dist(x, y, P[i - 1][0], P[i - 1][1], P[i][0], P[i][1]))
    return best


def rot(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def on_deck(poly, decks, step=50.0):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    n = m = 0
    x = min(xs) + 5
    while x < max(xs):
        y = min(ys) + 5
        while y < max(ys):
            if inside(x, y, poly):
                n += 1
                m += any(inside(x, y, d) for d in decks)
            y += step
        x += step
    for (px, py) in poly:
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        dd = math.hypot(cx - px, cy - py) or 1.0
        qx, qy = px + (cx - px) * 5 / dd, py + (cy - py) * 5 / dd
        n += 1
        m += any(inside(qx, qy, d) for d in decks)
    return m / float(n or 1)


def main():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    el = json.loads((INV / "elements.json").read_text(encoding="utf-8"))
    rows = json.loads((INV / "actors.json").read_text(encoding="utf-8"))
    d = plan["design"]
    decks = [d["forecourt"]["polygon"]]
    cp = d["control_platform"]
    ctrl = [(cp["x"][0], cp["y"][0]), (cp["x"][1], cp["y"][0]), (cp["x"][1], cp["y"][1] - cp["chamfer"]),
            (cp["x"][1] - cp["chamfer"], cp["y"][1]), (cp["x"][0], cp["y"][1])]
    sp = d["spine"]
    spine = [(sp["x"][0], sp["y"][0]), (sp["x"][1], sp["y"][0]), (sp["x"][1], sp["y"][1]), (sp["x"][0], sp["y"][1])]
    all_decks = decks + [ctrl, spine]
    axis = sp["axis_y"]
    B = {b["label"]: b for b in el["buildings"]}
    problems, notes = [], []

    # -- completeness of each assembly to move ---------------------------------
    completeness = {}
    for lab in MOVE:
        b = B[lab]
        f = b["footprint"]
        poly = obb(f["centre"][0], f["centre"][1], f["half"][0] + 150, f["half"][1] + 150, f["yaw"])
        found = []
        for r in rows:
            if r["path"] == b["path"]:
                continue
            o = r.get("origin") or r.get("loc")
            if not o or max((r.get("extent") or [0, 0, 0])[:2]) > 20000:
                continue
            if (inside(o[0], o[1], poly) and o[2] < f["z_max"] + 200 and o[2] > f["z_min"] - 200) or \
                    r.get("attach_parent") == b["path"]:
                found.append(r["label"])
        door = (b.get("door") or {}).get("label")
        extra = [x for x in found if x != door]
        completeness[lab] = {"inside_or_attached": found, "door": door, "complete": not extra and door in found}
        if extra or door not in found:
            problems.append("%s is not a complete assembly: %s" % (lab, extra or "door missing"))

    # -- moves: (target footprint centre, rotation delta) ----------------------------
    def plan_move(lab, centre, delta):
        b = B[lab]
        f, dr = b["footprint"], b["door"]
        c = (f["centre"][0] - b["loc"][0], f["centre"][1] - b["loc"][1])
        c2 = rot(c, delta)
        pivot = (centre[0] - c2[0], centre[1] - c2[1])
        o = rot((dr["loc"][0] - b["loc"][0], dr["loc"][1] - b["loc"][1]), delta)
        door = (pivot[0] + o[0], pivot[1] + o[1])
        yaw = f["yaw"] + delta
        fp = obb(centre[0], centre[1], f["half"][0], f["half"][1], yaw)
        out = (door[0] - centre[0], door[1] - centre[1])
        n = math.hypot(*out) or 1.0
        approach = (door[0] + out[0] / n * DOOR_APPROACH, door[1] + out[1] / n * DOOR_APPROACH)
        return {"label": lab, "identity": b["path"], "door_identity": dr["path"], "door_label": dr["label"],
                "from": {"loc": b["loc"], "yaw": b["rot"]["yaw"], "door_loc": dr["loc"], "door_yaw": dr["rot"]["yaw"]},
                "to": {"loc": [round(pivot[0], 1), round(pivot[1], 1), b["loc"][2]],
                       "yaw": round(b["rot"]["yaw"] + delta, 4),
                       "door_loc": [round(door[0], 1), round(door[1], 1), dr["loc"][2]],
                       "door_yaw": round(dr["rot"]["yaw"] + delta, 4)},
                "rotation_delta": delta, "footprint": [[round(x, 1), round(y, 1)] for x, y in fp],
                "door_approach": [round(approach[0], 1), round(approach[1], 1)]}

    # Command onto the control platform, centred, turned so its door faces the spine (-Y).
    cmd = plan_move("Command", ((cp["x"][0] + cp["x"][1]) / 2.0, (cp["y"][0] + cp["y"][1]) / 2.0), -90.0)
    # -- the rear hangar reserve: rear edge, centred on the spine axis ----------------
    fore = d["forecourt"]["polygon"]
    gate = B["SM_MainGate_Tripo"]["footprint"]
    gpoly = obb(gate["centre"][0], gate["centre"][1], gate["half"][0], gate["half"][1], gate["yaw"])
    g_ymax = max(p[1] for p in gpoly)
    y0 = g_ymax + CLEAR_BUILDING
    y1 = axis + (axis - y0)
    ps = next(r for r in rows if r["label"] == "PlayerStart")
    x0 = fore[0][0]
    x1 = ps["loc"][0] - CLEAR_ANCHOR
    reserve = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    res = {"x": [round(x0, 1), round(x1, 1)], "y": [round(y0, 1), round(y1, 1)], "depth": round(x1 - x0, 1),
           "width": round(y1 - y0, 1), "centred_on_axis": axis,
           "width_limited_by": "SM_MainGate_Tripo (+%.0f): the gate holds the rear edge up to y=%.0f" % (CLEAR_BUILDING, g_ymax),
           "depth_limited_by": "PlayerStart (+%.0f)" % CLEAR_ANCHOR, "rear_edge": "x=%.0f, the forecourt's rear edge" % x0}

    # Mess_Hall to the rear-left slot beside the reserve, door still facing the forecourt,
    # pushed seaward only as far as the rear-left chamfer requires.
    mh_f = B["Mess_Hall"]["footprint"]
    hx_w, hy_w = mh_f["half"][1], mh_f["half"][0]     # yaw -90: world x-half = local y-half
    mh_y0 = y1 + CLEAR_BUILDING
    x, mh = x0 + 300.0, None
    while x < x0 + 4000.0:
        fp = obb(x + hx_w, mh_y0 + hy_w, mh_f["half"][0], mh_f["half"][1], mh_f["yaw"])
        if on_deck(fp, decks) >= 0.99999:
            mh = plan_move("Mess_Hall", (x + hx_w, mh_y0 + hy_w), 0.0)
            break
        x += 25.0
    if mh is None:
        problems.append("no rear-left slot for Mess_Hall")
        mh = plan_move("Mess_Hall", (mh_f["centre"][0], mh_f["centre"][1]), 0.0)
    moved = {"Command": cmd, "Mess_Hall": mh}

    # -- checks ---------------------------------------------------------------------
    checks = {}
    polys = {}
    for b in el["buildings"]:
        if b["label"] in moved:
            polys[b["label"]] = moved[b["label"]]["footprint"]
        else:
            f = b["footprint"]
            polys[b["label"]] = obb(f["centre"][0], f["centre"][1], f["half"][0], f["half"][1], f["yaw"])
    checks["reserve_on_deck"] = round(on_deck(reserve, decks), 4)
    checks["reserve_clearance_to_buildings"] = {k: round(poly_dist(reserve, v), 1) for k, v in polys.items()}
    for k, v in checks["reserve_clearance_to_buildings"].items():
        if v < CLEAR_BUILDING - 1:
            problems.append("reserve within %.0f cm of %s" % (v, k))
    anchors = {"PlayerStart": ps["loc"][:2]}
    rack = next(r for r in rows if r["label"] == "BP_WeaponRack")
    anchors["BP_WeaponRack"] = rack["loc"][:2]
    for lab, mv in moved.items():
        anchors[mv["door_label"] + " approach"] = mv["door_approach"]
    for b in el["buildings"]:
        if b["label"] not in moved and b.get("door"):
            f = b["footprint"]
            dl = b["door"]["loc"]
            ox, oy = dl[0] - f["centre"][0], dl[1] - f["centre"][1]
            n = math.hypot(ox, oy) or 1.0
            if b["label"] != "SM_MainGate_Tripo":
                anchors[b["door"]["label"] + " approach"] = [dl[0] + ox / n * DOOR_APPROACH, dl[1] + oy / n * DOOR_APPROACH]
    ac = {}
    for k, (ax_, ay_) in anchors.items():
        dmin = 0.0 if inside(ax_, ay_, reserve) else min(seg_dist(ax_, ay_, reserve[i - 1][0], reserve[i - 1][1],
                                                                  reserve[i][0], reserve[i][1]) for i in range(4))
        ac[k] = round(dmin, 1)
        if dmin < CLEAR_ANCHOR - 1:
            problems.append("reserve within %.0f cm of %s" % (dmin, k))
    checks["reserve_clearance_to_anchors"] = ac
    for lab, mv in moved.items():
        fp = mv["footprint"]
        cov = on_deck(fp, all_decks)
        mv["footprint_on_deck"] = round(cov, 4)
        if cov < 0.999:
            problems.append("%s target footprint only %.1f%% on deck" % (lab, 100 * cov))
        a = mv["door_approach"]
        mv["door_approach_on_deck"] = any(inside(a[0], a[1], dd) for dd in all_decks)
        if not mv["door_approach_on_deck"]:
            problems.append("%s door approach is off the deck" % lab)
        others = {k: round(poly_dist(fp, v), 1) for k, v in polys.items() if k != lab}
        mv["clearance_to_buildings"] = others
        for k, v in others.items():
            if v < CLEAR_BUILDING - 1:
                problems.append("%s within %.0f cm of %s" % (lab, v, k))
        mv["inside_reserve"] = poly_dist(fp, reserve) == 0.0
        if mv["inside_reserve"]:
            problems.append("%s overlaps the hangar reserve" % lab)
    checks["baseline_reserve"] = plan.get("hangar_reserve", {}).get("x"), plan.get("hangar_reserve", {}).get("y")
    notes.append("Unresolved and untouched: Cube/Cube2/Cube3 inside Barracks (Barracks does not move); "
                 "BP_WeaponRack (no association, stays); the three empty placeholders.")
    notes.append("Alternative P2: a ~59 m wide rear hangar is possible only off the spine axis (y %.0f-%.0f, "
                 "centre %.0f) or by moving the spine axis about +10 m, which puts Medical at the spine's mouth; "
                 "both are layout decisions for Connor." % (y0, y0 + 5864, y0 + 2932))
    notes.append("Alternative P3: Command AND Mess_Hall both on the control platform (the reference's tower plus low "
                 "block): they fit stacked with a 7 m walkway between them, leaving the rear-left open.")
    result = {"schema": "garrison-rear-proposal/2026-09-30", "plan_only": True, "baseline_plan": str(PLAN),
              "hangar_reserve": res, "moves": moved, "completeness": completeness, "checks": checks,
              "problems": problems, "notes": notes}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "proposal.json").write_bytes(json.dumps(result, indent=1).encode("utf-8"))
    print(json.dumps({"reserve": res, "Command": {k: cmd[k] for k in ("to", "footprint_on_deck", "door_approach",
                                                                      "door_approach_on_deck")},
                      "Mess_Hall": {k: mh[k] for k in ("to", "footprint_on_deck", "door_approach",
                                                       "door_approach_on_deck")},
                      "completeness": completeness, "problems": problems}, indent=1))


if __name__ == "__main__":
    main()
