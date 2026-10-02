"""Draw a garrison layout plan next to the approved reference. Plain Python + matplotlib.

    python Scripts/ib_render_garrison_plan.py --plan <layout>/plan.json --inventory <inventory dir>
           [--reference References/GarrisonTargets/garrison-overhead-approved-2026-09-23.png]
           [--out <file.png>]

Panels: the reference (if given), the site as it is now, and the plan. Both site
panels are drawn the way the reference is framed: land and the rear at the top,
the sea at the bottom, the docks side (-Y) on the right. So a world point (x, y)
is drawn at (-y, -x). Reads files only; changes nothing.
"""
import json, sys, math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def P(pts):
    return [(-y, -x) for x, y in pts]


def obb(cx, cy, hx, hy, yaw):
    a = math.radians(yaw)
    c, s = math.cos(a), math.sin(a)
    return [(cx + sx * hx * c - sy * hy * s, cy + sx * hx * s + sy * hy * c)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def outlines(faces_json, platform_path):
    tris = []
    for a in faces_json.get("actors", []):
        if a.get("path") == platform_path:
            tris = a.get("triangles", [])
    return [t for t in tris if t.get("up")]


def draw_site(ax, el, tris, plan, after):
    ax.set_facecolor("#16324a")
    # The old platform, face by face (upper deck, slopes, apron).
    for t in tris:
        zs = [p[2] for p in t["v"]]
        if min(zs) < -100:
            continue
        z = sum(zs) / 3.0
        col = "#8d949c" if z > 380 else ("#6f7780" if z > 100 else "#5c6670")
        if after:
            ax.add_patch(MPoly(P([(p[0], p[1]) for p in t["v"]]), closed=True, fill=False, ec="#9fb3c8",
                               lw=0.3, ls=(0, (2, 3)), alpha=0.6))
        else:
            ax.add_patch(MPoly(P([(p[0], p[1]) for p in t["v"]]), closed=True, fc=col, ec=col, lw=0.2))
    if after:
        zc = {"forecourt": "#9aa1a8", "land_ramp": "#9aa1a8", "spine": "#a9b0b6", "pad": "#b3b9be",
              "control_platform": "#a3aab0", "pier": "#a0a6ab"}
        for p in plan["pieces"]:
            if p["kind"] in ("deck", "ramp", "filler"):
                ax.add_patch(MPoly(P(p["footprint"]), closed=True, fc=zc.get(p["zone"], "#999"),
                                   ec="#4b5157" if p["kind"] != "filler" else "#c77d2a", lw=0.5))
        for p in plan["pieces"]:
            if p["kind"] == "marking":
                col = "#ff9d2e" if p["zone"] == "hangar_reserve" else "#f2d03b"
                ax.add_patch(MPoly(P(p["footprint"]), closed=True, fc=col, ec=col, lw=0.3))
        ln = plan.get("pier_lane")
        if ln:      # PF1: the pier's service lane, drawn under its lines
            ax.add_patch(MPoly(P([(ln["x"][0], ln["y"][0]), (ln["x"][1], ln["y"][0]), (ln["x"][1], ln["y"][1]),
                                  (ln["x"][0], ln["y"][1])]), closed=True, fc="#8fe38f", ec="none", alpha=0.35))
            ax.text(-(ln["y"][0] + ln["y"][1]) / 2.0, -(ln["x"][0] + ln["x"][1]) / 2.0 + 1800.0,
                    "SERVICE LANE %.1f m\n(clear band %.1f m)" % (ln["width"] / 100.0, ln["clear_width"] / 100.0),
                    color="#0d3b12", ha="center", va="center", fontsize=4.5, weight="bold", rotation=90)
        for p in plan["pieces"]:
            if p["kind"] == "coping":
                ax.add_patch(MPoly(P(p["footprint"]), closed=True, fc="#4f565d", ec="#4f565d", lw=0.2))
            elif p["kind"] in ("edge_line", "lane_line", "route_dash", "door_bar"):
                ax.add_patch(MPoly(P(p["footprint"]), closed=True, fc="#f2d03b", ec="#f2d03b", lw=0.2))
        r = plan.get("hangar_reserve")
        if r:
            ax.add_patch(MPoly(P(r["polygon"]), closed=True, fill=False, ec="#ff9d2e", lw=1.4, hatch="//"))
            cx, cy = sum(r["x"]) / 2.0, sum(r["y"]) / 2.0
            if plan.get("composition"):
                ax.text(-cy, -cx, "HANGAR RESERVATION\n(provisional; Connor's)\n%.1f m deep x %.1f m wide"
                        % (r["depth"] / 100.0, r["width"] / 100.0),
                        color="#ffcf8a", ha="center", va="center", fontsize=6.5, weight="bold")
                y0r, y1r = r["y"]
                ax.annotate("", xy=(-y0r, -r["x"][0] + 250), xytext=(-y1r, -r["x"][0] + 250),
                            arrowprops=dict(arrowstyle="<->", color="#ffcf8a", lw=0.8))
                ax.text(-(y0r + y1r) / 2, -r["x"][0] + 700, "width: gate + 6 m, mirrored on the axis",
                        color="#ffcf8a", ha="center", fontsize=5)
                ax.annotate("", xy=(-y1r - 350, -r["x"][0]), xytext=(-y1r - 350, -r["x"][1]),
                            arrowprops=dict(arrowstyle="<->", color="#ffcf8a", lw=0.8))
                ax.text(-y1r - 550, -(r["x"][0] + r["x"][1]) / 2, "depth: rear edge to\nPlayerStart - 3 m",
                        color="#ffcf8a", ha="right", va="center", fontsize=5)
            else:
                ax.text(-cy, -cx, "HANGAR RESERVE\n(Connor)\n%.0f x %.0f m" % (r["width"] / 100, r["depth"] / 100),
                        color="#ffcf8a", ha="center", va="center", fontsize=7, weight="bold")
        for g in plan["checks"].get("gaps", []):
            xs = [q[0] for q in g["polygon"]]
            ys = [q[1] for q in g["polygon"]]
            ax.text(-(min(ys) + max(ys)) / 2, -(min(xs) + max(xs)) / 2, "water\n%.0f m" % (g["width"] / 100),
                    color="#bfe3ff", ha="center", va="center", fontsize=6, rotation=0)
        d = plan["design"]
        for key, name in (("spine", "SPINE"), ("control_platform", "CONTROL\nPLATFORM"), ("pier", "PIER")):
            z = d[key]
            lx, ly = (z["x"][0] + z["x"][1]) / 2, (z["y"][0] + z["y"][1]) / 2
            occupied = [b for b in el.get("buildings", []) if b.get("footprint")
                        and z["x"][0] <= b["footprint"]["centre"][0] <= z["x"][1]
                        and z["y"][0] <= b["footprint"]["centre"][1] <= z["y"][1]]
            if occupied:    # a building stands on this zone: label its sea-side edge, clear of the building
                lx = z["x"][1] - 250.0
            ax.text(-ly, -lx, name.replace("\n", " ") if occupied else name, color="#202428",
                    ha="center", va="center", fontsize=6.5 if not occupied else 5.5, weight="bold",
                    rotation=90 if key in ("spine", "pier") else 0)
        pc = d["pad"]["centre"]
        ax.text(-pc[1], -pc[0] - 1600, "PAD", color="#202428", ha="center", va="center", fontsize=7, weight="bold")
    if after and plan.get("routes"):
        for rt in plan["routes"]:
            pts = rt.get("waypoints") or []
            if len(pts) >= 2:
                ax.plot([-q[1] for q in pts], [-q[0] for q in pts], ls=(0, (3, 2)), lw=0.9,
                        color="#3fd0ff" if rt.get("crosses") == "entrance" else "#8fe38f", alpha=0.9)
    # Buildings, doors, anchors (P3: Command and Mess_Hall drawn where the plan puts them).
    for b in el.get("buildings", []):
        f = b.get("footprint")
        if not f:
            continue
        ax.add_patch(MPoly(P(obb(f["centre"][0], f["centre"][1], f["half"][0], f["half"][1], f["yaw"])),
                           closed=True, fc="#7a4f35", ec="#2b1a10", lw=0.8))
        ax.text(-f["centre"][1], -f["centre"][0], b["label"].replace("SM_MainGate_Tripo", "GATE"),
                color="white", ha="center", va="center", fontsize=6.5, weight="bold")
        d = b.get("door")
        if d and d.get("loc"):
            ax.plot([-d["loc"][1]], [-d["loc"][0]], "o", ms=3.5, mfc="#ffd400", mec="black", mew=0.5)
            n = b.get("door_normal")
            if n:
                ax.annotate("", xy=(-(d["loc"][1] + n[1] * 700), -(d["loc"][0] + n[0] * 700)),
                            xytext=(-d["loc"][1], -d["loc"][0]),
                            arrowprops=dict(arrowstyle="->", color="#ffd400", lw=1.0))
    for o in el.get("others_in_scope", []):
        lab, loc = o["label"], o.get("loc")
        if not loc:
            continue
        if lab == "PlayerStart":
            ax.plot([-loc[1]], [-loc[0]], "*", ms=10, color="#46d160", mec="black", mew=0.5)
        elif lab == "BP_WeaponRack":
            ax.plot([-loc[1]], [-loc[0]], "s", ms=4, color="#d62d2d", mec="black", mew=0.5)
        elif lab in ("Cube", "Cube2", "Cube3"):
            ax.plot([-loc[1]], [-loc[0]], "x", ms=3, color="#ffffff")
    # Props: where they are now, and (plan panel) where they go.
    moves = {m["identity"]: m for m in plan.get("moves", [])} if after else {}
    for o in el.get("others_in_scope", []):
        if o["label"] in ("Docks_Ship_Hull", "Docks_Crane_01", "Helicopter") or o["label"].startswith("SM_Truck"):
            m = moves.get(o["path"])
            if m and m.get("target_footprint"):
                ax.add_patch(MPoly(P(m["target_footprint"]), closed=True, fc="#3c6e91", ec="#0d1b26", lw=0.6,
                                   alpha=0.85))
                tx = sum(q[0] for q in m["target_footprint"]) / 4.0
                ty = sum(q[1] for q in m["target_footprint"]) / 4.0
                ax.text(-ty, -tx, o["label"].replace("Docks_", "").replace("SM_Truck_Cargo", "T"), color="white",
                        ha="center", va="center", fontsize=5)
            elif not after:
                ax.plot([-o["loc"][1]], [-o["loc"][0]], "D", ms=4, color="#3c6e91", mec="white", mew=0.4)
                ax.text(-o["loc"][1], -o["loc"][0] - 350, o["label"].replace("Docks_", "")
                        .replace("SM_Truck_Cargo", "T"), color="#cfe6ff", ha="center", fontsize=5)
    for w in el.get("seawalls", []) or []:
        o, e = w.get("origin"), w.get("extent")
        if o and e:
            ax.add_patch(MPoly(P([(o[0] - e[0], o[1] - e[1]), (o[0] + e[0], o[1] - e[1]),
                                  (o[0] + e[0], o[1] + e[1]), (o[0] - e[0], o[1] + e[1])]),
                               closed=True, fc="#3a3f44", ec="#222", lw=0.5))
    ax.set_aspect("equal")
    ax.set_xlim(-12500, 9000)
    ax.set_ylim(-22500, 4200)
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    plan = json.loads(Path(arg("--plan")).read_text(encoding="utf-8"))
    inv = Path(arg("--inventory"))
    el = json.loads((inv / "elements.json").read_text(encoding="utf-8"))
    if not el.get("seawalls"):
        rows = json.loads((inv / "actors.json").read_text(encoding="utf-8"))
        el["seawalls"] = [r for r in rows if str(r.get("label", "")).startswith("Seawall_")]
    tris = outlines(json.loads((inv / "support_faces.json").read_text(encoding="utf-8")),
                    plan["frame"].get("platform_path"))
    ref = arg("--reference")
    prop = json.loads(Path(arg("--proposal")).read_text(encoding="utf-8")) if arg("--proposal") else None
    panels = (3 if ref else 2) + (1 if prop else 0)
    fig, axes = plt.subplots(1, panels, figsize=(7.2 * panels, 9.0), facecolor="#0e1a24")
    i = 0
    if ref:
        img = plt.imread(ref)
        axes[0].imshow(img)
        axes[0].set_title("approved reference (oblique; rear at top)", color="white", fontsize=10)
        axes[0].axis("off")
        i = 1
    draw_site(axes[i], el, tris, plan, after=False)
    axes[i].set_title("now: map %s..." % str(plan["map"]["sha256"])[:8], color="white", fontsize=10)
    el_plan = el
    comp = plan.get("composition")
    if comp:
        el_plan = json.loads(json.dumps(el))
        for b in el_plan["buildings"]:
            mv = comp["buildings"].get(b["label"])
            if not mv:
                continue
            f = b["footprint"]
            b["footprint"] = dict(f, centre=mv["to"]["footprint_centre"], yaw=f["yaw"] + mv["rotation_delta"])
            b["door"] = dict(b.get("door") or {}, loc=mv["to"]["door_loc"])
            b["door_normal"] = mv["door_normal"]
    draw_site(axes[i + 1], el_plan, tris, plan, after=True)
    axes[i + 1].set_title(("PF1 CANDIDATE (plan): clear pier service lane, quay coping + yellow edge/route lines"
                           if plan.get("finish") else
                           "P3 CANDIDATE (plan): tower + low block on the control platform, rear reservation"
                           if comp else "plan (%s mode): nothing of Shane's moves" % plan.get("platform_mode")),
                          color="#ffcf8a" if comp else "white", fontsize=10)
    if prop:
        el2 = json.loads(json.dumps(el))
        for b in el2["buildings"]:
            mv = prop["moves"].get(b["label"])
            if not mv:
                continue
            xs = [q[0] for q in mv["footprint"]]
            ys = [q[1] for q in mv["footprint"]]
            f = b["footprint"]
            yaw = f["yaw"] + mv["rotation_delta"]
            b["footprint"] = {"centre": [sum(xs) / 4.0, sum(ys) / 4.0], "half": f["half"], "yaw": yaw}
            b["door"]["loc"] = mv["to"]["door_loc"]
        plan2 = json.loads(json.dumps(plan))
        r = prop["hangar_reserve"]
        plan2["hangar_reserve"] = dict(plan2.get("hangar_reserve") or {}, x=r["x"], y=r["y"], depth=r["depth"],
                                       width=r["width"], polygon=[[r["x"][0], r["y"][0]], [r["x"][1], r["y"][0]],
                                                                  [r["x"][1], r["y"][1]], [r["x"][0], r["y"][1]]])
        plan2["pieces"] = [p for p in plan2["pieces"] if p["zone"] != "hangar_reserve"]
        draw_site(axes[i + 2], el2, tris, plan2, after=True)
        axes[i + 2].set_title("NEXT PROPOSAL (plan only): rear hangar, Command on the control platform",
                              color="#ffcf8a", fontsize=10)
    for ax in axes[i:]:
        ax.text(0.01, 0.99, "land / rear (-X) at top\nsea (+X) at bottom\ndocks side (-Y) at right",
                transform=ax.transAxes, va="top", color="#c8d6e5", fontsize=7)
    fig.tight_layout()
    out = arg("--out", str(Path(arg("--plan")).with_name("plan.png")))
    # bbox_inches="tight" keeps the panel titles inside the image (equal-aspect axes can push them past the top)
    fig.savefig(out, dpi=130, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.3)
    print("wrote " + out)


if __name__ == "__main__":
    main()
