"""Before/after board and colour statistics for the YM1 yellow-markings correction (a review image,
not game UI). Plain Python + Pillow; reads PNGs and JSON, writes only --out and --stats.

    python Scripts/ib_garrison_yellow_board.py --before <before shots dir> --after <after shots dir>
           --out <board.png> --stats <stats.json> [--verify <paint_verify.json>] [--assignments <assignments.json>]

For every capture present in both folders (same camera, same world lighting, same capture timing),
pixels are compared: 'changed' = any channel moved by more than 24 levels; 'paint' = changed pixels
whose AFTER colour is yellow-hued (hue 25..70 deg, saturation >= 0.25). The mean sRGB and hue /
saturation / value of the paint pixels are reported before and after, so the colour change is
measured, not asserted. Water, clouds and PIE subtitles also move between runs; the hue gate keeps
them out of the paint figures (they are counted in 'changed').
"""
import json, sys, colorsys
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


PAIRS = [  # (file stem, caption, kind)
    ("overhead-reference", "Overhead framed like the reference", "EDITOR view"),
    ("pier-lane-ground", "Pier service lane from the pier end (raised)", "EDITOR view"),
    ("pier-lane-eye", "Pier service lane at eye height", "EDITOR view"),
    ("control-pad-edge", "Control platform and pad edges", "EDITOR view"),
    ("pad-ring", "Pad ring and pad edge lines from over the sea", "EDITOR view"),
    ("spine-control-join", "Spine / control seam at Mess_Hall's door bar", "EDITOR view"),
    ("pie-pier-lane-from-forecourt", "Pier lane from the forecourt", "GAMEPLAY, PIE player camera"),
    ("pie-pier-lane-from-pier-end", "Pier lane from the pier end", "GAMEPLAY, PIE player camera"),
    ("pie-control-apron-to-command", "Control apron toward Command's door", "GAMEPLAY, PIE player camera"),
    ("pie-pad-ring", "Across the pad ring toward the helicopter", "GAMEPLAY, PIE player camera"),
]
CROP = ("overhead-reference", (700, 270, 1200, 860), "Overhead crop: spine, control platform, pad, pier")


def stats(b, a):
    """Pixel statistics of one before/after pair (same size)."""
    pb, pa = b.load(), a.load()
    w, h = a.size
    changed = paint = 0
    sb, sa = [0, 0, 0], [0, 0, 0]
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            cb, ca = pb[x, y], pa[x, y]
            if max(abs(cb[0] - ca[0]), abs(cb[1] - ca[1]), abs(cb[2] - ca[2])) <= 24:
                continue
            changed += 1
            hh, ss, vv = colorsys.rgb_to_hsv(ca[0] / 255.0, ca[1] / 255.0, ca[2] / 255.0)
            if 25.0 <= hh * 360.0 <= 70.0 and ss >= 0.25:
                paint += 1
                for k in range(3):
                    sb[k] += cb[k]
                    sa[k] += ca[k]
    total = ((w + 1) // 2) * ((h + 1) // 2)
    out = {"sampled_px": total, "changed_px": changed, "changed_pct": round(100.0 * changed / total, 2),
           "paint_px": paint, "paint_pct": round(100.0 * paint / total, 2)}
    if paint:
        mb = [round(v / paint) for v in sb]
        ma = [round(v / paint) for v in sa]
        out["paint_mean_srgb_before"], out["paint_mean_srgb_after"] = mb, ma
        for tag, m in (("before", mb), ("after", ma)):
            hh, ss, vv = colorsys.rgb_to_hsv(m[0] / 255.0, m[1] / 255.0, m[2] / 255.0)
            out["paint_mean_hsv_" + tag] = [round(hh * 360.0, 1), round(ss, 3), round(vv, 3)]
    return out


def main():
    before, after = Path(arg("--before")), Path(arg("--after"))
    W, gap = 2400, 8
    tw = (W - 3 * gap) // 2
    th = int(tw * 9 / 16)
    f1, f2 = font(24), font(18)
    rows, st = [], {}
    for stem, cap, kind in PAIRS:
        fb, fa = before / (stem + ".png"), after / (stem + ".png")
        if not (fb.is_file() and fa.is_file()):
            continue
        b, a = Image.open(fb).convert("RGB"), Image.open(fa).convert("RGB")
        if b.size != a.size:
            st[stem] = {"error": "size differs %s %s" % (b.size, a.size)}
            continue
        st[stem] = dict(stats(b, a), kind=kind, before_file=str(fb), after_file=str(fa))
        rows.append((stem, cap, kind, b, a))
    crop = None
    if CROP[0] in [r[0] for r in rows]:
        b, a = [(r[3], r[4]) for r in rows if r[0] == CROP[0]][0]
        crop = (b.crop(CROP[1]), a.crop(CROP[1]))
    lines = []
    vr = json.loads(Path(arg("--verify")).read_text(encoding="utf-8")) if arg("--verify") and Path(arg("--verify")).is_file() else None
    asg = json.loads(Path(arg("--assignments")).read_text(encoding="utf-8")) if arg("--assignments") and Path(arg("--assignments")).is_file() else None
    if vr:
        f = vr.get("material_facts") or {}
        lines.append("Material (engine, after reload): %s, parent %s, overrides %s -> effective Base Color %s; Metallic %s, Roughness %s"
                     % (str(f.get("object")).split(".")[-1], str(f.get("parent")).split(".")[-1],
                        [o["name"] for o in f.get("vector_overrides") or []], f.get("effective_base_color"),
                        (f.get("effective_scalars") or {}).get("Metallic"), (f.get("effective_scalars") or {}).get("Roughness")))
        c = vr.get("comparison") or {}
        lines.append("Candidate vs PF1, actor for actor and component for component: %s expected slot changes, %s unexpected"
                     % (c.get("expected_slot_changes"), c.get("unexpected_count")))
    if asg:
        lines.append("Assignments: %d generated markings (P3 %d, PF1 %d), slot 0 of each StaticMeshComponent0, MI_Landmass_HelipadMarking -> new MI; "
                     "%d inherited live-map users of the shared MI left untouched"
                     % (asg["count"], asg["by_origin"].get("P3", 0), asg["by_origin"].get("PF1", 0),
                        len(asg.get("left_untouched_inherited_users_of_shared_mi") or [])))
    for stem, s in st.items():
        if "paint_mean_srgb_after" in s:
            lines.append("%s: paint pixels %.2f%% of the frame; mean sRGB %s -> %s (hue/sat %s -> %s)"
                         % (stem, s["paint_pct"], s["paint_mean_srgb_before"], s["paint_mean_srgb_after"],
                            s["paint_mean_hsv_before"][:2], s["paint_mean_hsv_after"][:2]))
    H = 70 + len(rows) * (th + 52) + (0 if crop is None else int(tw * crop[0].height / crop[0].width) + 60) + 30 * len(lines) + 40
    board = Image.new("RGB", (W, H), (14, 26, 36))
    d = ImageDraw.Draw(board)
    d.text((14, 16), "YM1 yellow markings: BEFORE (PF1 base, left) and AFTER (YM1 candidate, right); same cameras, same world lighting",
           fill=(255, 207, 138), font=f1)
    y = 60
    if crop:
        ch = int(tw * crop[0].height / crop[0].width)
        for k, im in enumerate(crop):
            board.paste(im.resize((tw, ch), Image.LANCZOS), (gap + k * (tw + gap), y))
        d.text((gap + 4, y + ch + 6), CROP[2] + "  [EDITOR view] before", fill=(220, 230, 240), font=f2)
        d.text((2 * gap + tw + 4, y + ch + 6), CROP[2] + "  [EDITOR view] after", fill=(220, 230, 240), font=f2)
        y += ch + 50
    for stem, cap, kind, b, a in rows:
        board.paste(b.resize((tw, th), Image.LANCZOS), (gap, y))
        board.paste(a.resize((tw, th), Image.LANCZOS), (2 * gap + tw, y))
        d.text((gap + 4, y + th + 6), "%s  [%s] before" % (cap, kind), fill=(220, 230, 240), font=f2)
        d.text((2 * gap + tw + 4, y + th + 6), "%s  [%s] after" % (cap, kind), fill=(220, 230, 240), font=f2)
        y += th + 52
    for k, t in enumerate(lines):
        d.text((14, y + 10 + 30 * k), t[:230], fill=(160, 220, 160), font=f2)
    board.save(arg("--out"))
    Path(arg("--stats")).write_text(json.dumps(st, indent=1), encoding="utf-8")
    print("wrote %s (%d pairs) and %s" % (arg("--out"), len(rows), arg("--stats")))


if __name__ == "__main__":
    main()
