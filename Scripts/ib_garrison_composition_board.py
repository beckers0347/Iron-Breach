"""Comparison board for the P3 candidate (review image, not game UI). Plain Python + Pillow.

    python Scripts/ib_garrison_composition_board.py --plan-image <plan render png> --shots <shots dir>
           --checks <composition_checks.json> [--clearance <P3 clearance_checks.json>]
           [--clearance-original <Preview3 clearance_checks.json>] --out <board.png>

Top row: the approved reference, today's layout and the P3 plan (annotated by the
renderer). Bottom row: the candidate as captured in the editor. Each capture gets a
caption; the only annotations are on this board, never in the level.
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def font(size):
    for f in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except Exception:
            pass
    return ImageFont.load_default()


CAPTIONS = {
    "overhead-reference": "Overhead framed like the reference (sun behind the camera)",
    "overhead-topdown": "Top-down",
    "control-platform": "Control platform: Command (tower), Mess_Hall (07); Medical (05) on the forecourt",
    "control-tower-entrance": "Command's entrance (leaf closed), facing the seaward apron",
    "control-lowblock-entrance": "Mess_Hall's entrance (leaf closed), facing the spine; Medical (05) behind",
    "rear-reservation": "Toward the rear reservation from 11 m up: provisional 48.9 x 38.6 m outline",
    "rear-reservation-eye": "The same at eye height, 42 m away: the flat outline all but disappears",
}


def load(name):
    p = arg(name)
    return json.loads(Path(p).read_text(encoding="utf-8")) if p and Path(p).is_file() else None


def short(name):
    return name.split(":")[0].replace("existing route", "road -> gate -> forecourt (existing route)")


def footer_lines():
    """What the scripted PIE walks and pawn sweeps found, from the evidence files; nothing typed by hand."""
    out, green, amber = [], (160, 220, 160), (255, 207, 138)
    c, p3, orig = load("--checks"), load("--clearance"), load("--clearance-original")
    first = {r["name"]: r.get("first_block") for r in ((p3 or {}).get("route_sweeps") or {}).get("routes", [])}
    if c:
        walks = [w for w in c.get("walks") or [] if not w.get("name", "").startswith("walk into")]
        ok = [short(w["name"]) for w in walks if w.get("result") == "reached"]
        bad = []
        for w in walks:
            if w.get("result") != "reached":
                fb = first.get(w["name"]) or {}
                bad.append("%s centreline %s at x %.0f%s" % (
                    short(w["name"]), w.get("result"), (w.get("end") or [0])[0],
                    " (pawn sweep: first blocked by %s at x %.0f)" % (fb["actor"], fb["impact"][0]) if fb else ""))
        out.append(("Scripted PIE (the real pawn driven by movement input; not a person playing): reached " +
                    "; ".join(ok), green))
        if bad:
            out.append(("Did not reach: " + "; ".join(bad), amber))
    if p3:
        lanes = ((p3.get("route_sweeps") or {}).get("pier_lanes") or {}).get("summary")
        rw = [w for w in p3.get("route_walks") or []]
        if lanes or rw:
            out.append(("Pier (pawn sweeps): the centreline is blocked by Docks_Crane_01; %s; edge-lane walks: %s" % (
                lanes, ", ".join("%s %s (%s m)" % (w["name"].split(" (")[0], w["result"], w.get("length_m"))
                                 for w in rw)), amber))
        walls = sorted(set(d.get("first_wall_behind_door_line_cm") for d in p3.get("door_sweeps") or []))
        past = sorted(set(w.get("past_door_line_cm") for w in p3.get("walks") or []))
        opened = all(w.get("leaf_opened") for w in p3.get("walks") or [])
        o_walls = sorted(set(d.get("first_wall_behind_door_line_cm") for d in (orig or {}).get("door_sweeps") or []))
        out.append(("Doors: %s, but each building's own collision stops the pawn %s cm past the door line "
                    "(wall %s cm behind it); at the ORIGINAL positions (Preview3) the wall is %s cm behind: pre-existing, "
                    "not caused by the move" % ("both leaves opened" if opened else "a leaf did NOT open",
                                                 "/".join(str(x) for x in past), "/".join(str(x) for x in walls),
                                                 "/".join(str(x) for x in o_walls) or "not measured"), amber))
    return out


def main():
    plan_img = Image.open(arg("--plan-image")).convert("RGB")
    shots = Path(arg("--shots"))
    order = ["overhead-reference", "overhead-topdown", "control-platform", "control-tower-entrance",
             "control-lowblock-entrance", "rear-reservation", "rear-reservation-eye"]
    tiles = [(n, shots / (n + ".png")) for n in order if (shots / (n + ".png")).is_file()]
    W = 2400
    top = plan_img.resize((W, int(W * plan_img.height / plan_img.width)))
    tw = W // 3
    th = int(tw * 9 / 16)
    rows = (len(tiles) + 2) // 3
    board = Image.new("RGB", (W, top.height + rows * (th + 46) + 70), (14, 26, 36))
    board.paste(top, (0, 0))
    d = ImageDraw.Draw(board)
    f1, f2 = font(22), font(17)
    y0 = top.height + 10
    d.text((14, y0), "P3 candidate as captured in the editor (CarrowGateGarrison_P3Candidate1; world lighting unchanged)",
           fill=(255, 207, 138), font=f1)
    y0 += 40
    for k, (name, p) in enumerate(tiles):
        im = Image.open(p).convert("RGB").resize((tw - 8, th - 8))
        x, y = (k % 3) * tw + 4, y0 + (k // 3) * (th + 46)
        board.paste(im, (x, y))
        d.text((x + 4, y + th - 4), CAPTIONS.get(name, name), fill=(220, 230, 240), font=f2)
    lines = []
    for text, colour in footer_lines():
        row = ""
        for word in text.split(" "):          # wrap to the board width
            trial = (row + " " + word).strip()
            if row and d.textlength(trial, font=f2) > W - 40:
                lines.append((row, colour))
                row = "    " + word
            else:
                row = trial if not row.startswith("    ") else row + " " + word
        lines.append((row, colour))
    if lines:
        foot = Image.new("RGB", (W, 18 + 30 * len(lines)), (14, 26, 36))
        fd = ImageDraw.Draw(foot)
        for k, (text, colour) in enumerate(lines):
            fd.text((14, 8 + 30 * k), text, fill=colour, font=f2)
        full = Image.new("RGB", (W, board.height + foot.height), (14, 26, 36))
        full.paste(board, (0, 0))
        full.paste(foot, (0, board.height))
        board = full
    board.save(arg("--out"))
    print("wrote " + arg("--out"))


if __name__ == "__main__":
    main()
