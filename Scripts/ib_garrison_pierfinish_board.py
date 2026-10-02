"""Comparison board for the PF1 pier-finish candidate (a review image, not game UI). Plain Python + Pillow.

    python Scripts/ib_garrison_pierfinish_board.py --plan-image <plan render png> --shots <shots dir>
           --checks <pierfinish_checks.json> --out <board.png> [--shots-r1 <r1 shots dir>] [--title <text>]
           [--material-probe <material_probe.json from Scripts/ib_probe_marking_material.py>]

Top: the approved reference, today's map and the PF1 plan (annotated by the renderer). With --shots-r1,
the same overhead crop from the superseded r1 capture and from this one, side by side. Then the
candidate as captured in the EDITOR, then the GAMEPLAY (PIE, player camera) captures, each labelled
as such. The footer is generated from the checks file; no result is typed by hand.
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


EDITOR = [
    ("overhead-reference", "Overhead framed like the reference"),
    ("overhead-topdown", "Top-down"),
    ("pier-lane-ground", "Pier service lane from the pier end (raised)"),
    ("pier-lane-eye", "Pier service lane at eye height"),
    ("pier-channel-quay", "Quay coping + fascia along the channel"),
    ("control-pad-edge", "Control platform and pad edges"),
    ("spine-control-join", "Spine / control seam at Mess_Hall's door bar"),
]
GAMEPLAY = [
    ("pie-pier-lane-from-forecourt", "Pier lane from the forecourt"),
    ("pie-pier-lane-from-pier-end", "Pier lane from the pier end"),
    ("pie-control-apron-to-command", "Control apron toward Command's door"),
]


def grid(board_w, tiles, shots, d, y0, title, colour, f1, f2, tag):
    tw = board_w // 3
    th = int(tw * 9 / 16)
    d.text((14, y0), title, fill=colour, font=f1)
    y0 += 40
    k = 0
    placed = []
    for name, cap in tiles:
        p = shots / (name + ".png")
        if not p.is_file():
            continue
        x, y = (k % 3) * tw + 4, y0 + (k // 3) * (th + 46)
        placed.append((p, x, y, tw, th, "%s  [%s]" % (cap, tag)))
        k += 1
    rows = (k + 2) // 3
    return placed, y0 + rows * (th + 46)


CROP = (700, 270, 1200, 860)   # overhead-reference: spine, control platform, pad and pier (same camera in r1 and r2)


def footer_lines(c):
    out, green, amber = [], (160, 220, 160), (255, 207, 138)
    if not c:
        return out
    ls = c.get("lane_scan") or {}
    if ls.get("summary"):
        out.append(("Pier lane scan (engine sweeps, Pawn profile): " + ls["summary"], green))
    sw = (c.get("sweeps") or {}).get("routes") or []
    if sw:
        bad = [s["name"].split(":")[0] for s in sw if not s.get("clear")]
        out.append(("Pawn-profile route sweeps: %d of %d clear%s" % (len(sw) - len(bad), len(sw),
                                                                   ("; not clear: " + "; ".join(bad)) if bad else ""),
                    green if not bad else amber))
    wk = c.get("walks") or []
    if wk:
        ok = [w for w in wk if w.get("result") == "reached"]
        bad = ["%s (%s)" % (w["name"].split(":")[0], w.get("result")) for w in wk if w.get("result") != "reached"]
        out.append(("Scripted PIE walks (the real pawn driven by movement input; not a person playing): %d of %d reached%s"
                    % (len(ok), len(wk), ("; " + "; ".join(bad)) if bad else ""), green if not bad else amber))
    ps = c.get("pie_shots") or []
    if ps:
        out.append(("Gameplay captures: %d of %d written during PIE from the player's camera"
                    % (sum(1 for s in ps if s.get("file_written")), len(ps)), green))
    return out


def main():
    plan_img = Image.open(arg("--plan-image")).convert("RGB")
    shots = Path(arg("--shots"))
    c = None
    if arg("--checks") and Path(arg("--checks")).is_file():
        c = json.loads(Path(arg("--checks")).read_text(encoding="utf-8"))
    W = 2400
    top = plan_img.resize((W, int(W * plan_img.height / plan_img.width)))
    scratch = Image.new("RGB", (W, 10))
    d0 = ImageDraw.Draw(scratch)
    f1, f2 = font(22), font(17)
    r1 = Path(arg("--shots-r1")) if arg("--shots-r1") else None
    pair = []
    yc = top.height
    if r1 and (r1 / "overhead-reference.png").is_file() and (shots / "overhead-reference.png").is_file():
        cw = W // 2 - 8
        for k, (src, cap) in enumerate(((r1 / "overhead-reference.png", "r1 (superseded): 20 cm lines, 30 cm dashes"),
                                        (shots / "overhead-reference.png", "r2 (this candidate): 40 cm lines and dashes"))):
            im = Image.open(src).convert("RGB").crop(CROP)
            im = im.resize((cw, int(cw * im.height / im.width)), Image.LANCZOS)
            pair.append((im, 4 + k * (W // 2), top.height + 50, "%s  [EDITOR view, same camera]" % cap))
        yc = top.height + 50 + pair[0][0].height + 36
    ed, y1 = grid(W, EDITOR, shots, d0, yc + 10, "", None, f1, f2, "EDITOR view")
    gp, y2 = grid(W, GAMEPLAY, shots, d0, y1 + 10, "", None, f1, f2, "GAMEPLAY, PIE")
    lines = []
    mp = json.loads(Path(arg("--material-probe")).read_text(encoding="utf-8")) if arg("--material-probe") else None
    extra = []
    if mp:
        over = ", ".join("'%s' %s" % (o["name"], o["value"][:3]) for o in mp.get("instance_vector_overrides", []))
        eff = mp.get("instance_effective_vector_parameters") or {}
        exposed = mp.get("instance_overrides_exposed_by_base") or {}
        extra.append(("Marking material (engine probe): %s overrides %s on %s, which exposes only %s -> effective %s. "
                      "The markings render GREY, not yellow (parameter-name mismatch; a material decision, see the result doc)."
                      % (mp["instance"].split(".")[-1], over, mp.get("base_material", "?").split(".")[-1],
                         list(eff.keys()), "; ".join("%s %s" % (k, v[:3]) for k, v in eff.items()))
                      if not all(exposed.values()) else "Marking material: overrides exposed by the parent",
                      (255, 150, 120) if not all(exposed.values()) else (160, 220, 160)))
    for text, colour in footer_lines(c) + extra:
        row = ""
        for word in text.split(" "):
            trial = (row + " " + word).strip()
            if row and d0.textlength(trial, font=f2) > W - 40:
                lines.append((row, colour))
                row = "    " + word
            else:
                row = trial if not row.startswith("    ") else row + " " + word
        lines.append((row, colour))
    H = y2 + 20 + 30 * len(lines) + 10
    board = Image.new("RGB", (W, H), (14, 26, 36))
    board.paste(top, (0, 0))
    d = ImageDraw.Draw(board)
    title = arg("--title") or "PF1"
    if pair:
        d.text((14, top.height + 10), "Markings, overhead crop: r1 against r2 (the only visual change besides the trucks' 75 cm shift)",
               fill=(255, 207, 138), font=f1)
        for im, x, y, cap in pair:
            board.paste(im, (x, y))
            d.text((x + 4, y + im.height + 6), cap, fill=(220, 230, 240), font=f2)
    d.text((14, yc + 10), "%s candidate in the EDITOR (CarrowGateGarrison_PierFinish1; world lighting unchanged)" % title,
           fill=(255, 207, 138), font=f1)
    if gp:
        d.text((14, y1 + 10), "%s candidate in GAMEPLAY (scripted PIE, the player's own camera)" % title, fill=(255, 207, 138), font=f1)
    for p, x, y, tw, th, cap in ed + gp:
        im = Image.open(p).convert("RGB").resize((tw - 8, th - 8))
        board.paste(im, (x, y))
        d.text((x + 4, y + th - 4), cap, fill=(220, 230, 240), font=f2)
    for k, (text, colour) in enumerate(lines):
        d.text((14, y2 + 20 + 30 * k), text, fill=colour, font=f2)
    board.save(arg("--out"))
    print("wrote " + arg("--out"))


if __name__ == "__main__":
    main()
