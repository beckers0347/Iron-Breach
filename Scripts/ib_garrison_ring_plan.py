"""PS1 plan: the declared pad-ring representation swap, generated from the BASE FINGERPRINT (FF1 alone, loaded
first in its own process) and cross-checked against the read-only probe. Plain Python (no editor):

    python3 Scripts/ib_garrison_ring_plan.py --basefp <run1/basefp/base_fingerprint.json> --probe <probe/ps1_probe.json>
                                             --out <plan/ps1_plan.json>

suppress  every pad-ring geometry segment of the base (labels IBGC_Pad_Ring_* and IBGC_FF_Pad_Ring96_*): exactly 96,
          each a StaticMeshActor with the run tag, one in-game StaticMeshComponent0 (Cube, FF1's amber instance,
          NoCollision) that is visible in the base -> visible False in the candidate
decal     ONE DecalActor at the ring centre on the deck top, projecting straight down (pitch -90), half-size
          (10, 1950, 1950) cm: the candidate-owned material draws the 18.9 m / 40 cm ring analytically
Any deviation is written to 'problems' and the lifecycle tool refuses a plan with problems.
"""
import argparse
import hashlib
import json
from pathlib import Path

BASE = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_ForecourtFinish1"
TARGET = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_PaintStability1"
MAT_PKG = "/Game/_GarrisonPreview_Disposable/PaintStability1_Materials/M_PS1_PadRingDecal"
MAT_OBJ = MAT_PKG + ".M_PS1_PadRingDecal"
FF1_MI = "/Game/_GarrisonPreview_Disposable/ForecourtFinish1_Materials/MI_FF1_DeckPaintAmber.MI_FF1_DeckPaintAmber"
CUBE = "/Engine/BasicShapes/Cube.Cube"
PREFIXES = ("IBGC_Pad_Ring_", "IBGC_FF_Pad_Ring96_")
RUN_TAG = "IB_GarrisonCB1"
PS_TAG = "IB_GarrisonPaintStability"
CENTRE, DECK_Z, RADIUS, WIDTH = (17232.0, 4525.0), 385.0, 1890.0, 40.0
DECAL = {"label": "IBGC_PS1_PadRingDecal", "tags": [RUN_TAG, PS_TAG], "folder": "Carrowgate Garrison/Paint Stability PS1",
         "location": [CENTRE[0], CENTRE[1], DECK_Z], "rotation": {"roll": 0.0, "pitch": -90.0, "yaw": 0.0},
         "scale": [1.0, 1.0, 1.0], "decal_size": [10.0, 1950.0, 1950.0], "fade_screen_size": 0.0, "sort_order": 0,
         "material": MAT_OBJ}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--basefp", required=True)
    ap.add_argument("--probe", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    bfd = json.loads(Path(a.basefp).read_text(encoding="utf-8"))
    probe = json.loads(Path(a.probe).read_text(encoding="utf-8"))
    fp = bfd["fingerprint"]
    problems, suppress = [], []
    if bfd.get("package") != BASE:
        problems.append("the fingerprint is of %s, not %s" % (bfd.get("package"), BASE))
    for key in sorted(fp, key=lambda k: fp[k]["label"] or ""):
        v = fp[key]
        lab = v.get("label") or ""
        if not lab.startswith(PREFIXES):
            continue
        comps = v.get("components") or {}
        c = comps.get("StaticMeshComponent0")
        row = {"label": lab, "actor_key": key, "component": "StaticMeshComponent0", "mesh": CUBE, "material": FF1_MI,
               "from_visible": True, "to_visible": False}
        if v.get("class") != "StaticMeshActor":
            problems.append("%s: class %s" % (lab, v.get("class")))
        if RUN_TAG not in (v.get("tags") or []):
            problems.append("%s: no run tag" % lab)
        if v.get("hidden"):
            problems.append("%s: actor hidden in game" % lab)
        if set(comps) != {"StaticMeshComponent0"}:
            problems.append("%s: components %s" % (lab, sorted(comps)))
        if not c:
            problems.append("%s: no StaticMeshComponent0" % lab)
        else:
            if c.get("mesh") != CUBE:
                problems.append("%s: mesh %s" % (lab, c.get("mesh")))
            if c.get("materials") != [FF1_MI]:
                problems.append("%s: materials %s" % (lab, c.get("materials")))
            if c.get("profile") != "NoCollision":
                problems.append("%s: collision profile %s" % (lab, c.get("profile")))
            if c.get("visible") is not True:
                problems.append("%s: not visible in the base" % lab)
        suppress.append(row)
    if len(suppress) != 96:
        problems.append("%d ring segments in the base, expected 96" % len(suppress))
    pk = {s["label"]: s["key"] for s in (probe.get("ring_segments") or {}).get("all") or []}
    mine = {s["label"]: s["actor_key"] for s in suppress}
    if pk != mine:
        problems.append("the probe's ring segments differ from the base fingerprint's (%d vs %d; %d label/key mismatches)"
                        % (len(pk), len(mine), sum(1 for k in set(pk) | set(mine) if pk.get(k) != mine.get(k))))
    clash = [k for k, v in fp.items() if v.get("label") == DECAL["label"]]
    if clash:
        problems.append("the decal label is already used by %s" % clash)
    if any(PS_TAG in (v.get("tags") or []) for v in fp.values()):
        problems.append("the base already carries %s actors" % PS_TAG)
    if bfd.get("decal_components"):
        problems.append("the base already has %d decal components" % bfd.get("decal_components"))
    plan = {"schema": "ps1-plan-1", "base": BASE, "target": TARGET, "base_sha256": bfd.get("sha256"),
            "material_object": MAT_OBJ, "problems": problems,
            "ring": {"centre": list(CENTRE), "radius_cm": RADIUS, "width_cm": WIDTH, "deck_top_z": DECK_Z,
                     "representation_before": "96 Cube segments (StaticMeshComponent0 visible, NoCollision)",
                     "representation_after": "the 96 segments' visibility off + one DecalActor with the analytic ring material"},
            "suppress": suppress, "decal": DECAL,
            "counts": {"suppress": len(suppress), "new_actors": 1, "base_actors": len(fp)},
            "inputs": {"base_fingerprint": {"file": str(a.basefp), "sha256": sha(a.basefp), "package_sha256": bfd.get("sha256")},
                       "probe": {"file": str(a.probe), "sha256": sha(a.probe)}},
            "by": "Scripts/ib_garrison_ring_plan.py"}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=1), encoding="utf-8")
    print("plan: %d segments to suppress, %d problem(s) -> %s" % (len(suppress), len(problems), out))
    for p in problems[:20]:
        print("  PROBLEM " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
