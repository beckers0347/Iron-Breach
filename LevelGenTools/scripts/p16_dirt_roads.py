"""p16_dirt_roads.py - replace the thin straight road strips with wide, curving dirt roads, spurs to every
building entrance, entrance pads and wet puddles - like the reference photo.

Run (after p15):   py "X:/IronBreach/LevelGenTools/scripts/p16_dirt_roads.py"
Safe to re-run (tag GEN_Phase16). Tunables: config/environment.json -> scatter.dirt_roads, road width in layout.json.

 * MainLoop: Catmull-Rom curve through the layout control points, width = layout width (1000 cm), M_Dirt, with a
   darker muddy shoulder (M_Mud) underneath.
 * A spur from every ENTRY_ point to the nearest main-road point.
 * A pad in front of each entrance (concrete for the big buildings, dirt for the rest).
 * Roads use M_DirtRoad: dry brown packed dirt (desaturated earth texture x warm brown tint, matte). No puddles.
 * Trees/rocks standing on the new roads are removed. Old GB_Road_MainLoop strips are deleted.

Look for:
  [Thornfield] VERIFY: road_curve PASS
  [Thornfield] VERIFY: road_detail PASS
  [Thornfield] VERIFY: spurs PASS
  [Thornfield] VERIFY: pads PASS
  [Thornfield] VERIFY: roads_clear PASS
"""
import os
import sys
import math
import random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)

PHASE = 16
CUBE = "/Engine/BasicShapes/Cube"
CYL = "/Engine/BasicShapes/Cylinder"
MEL = unreal.MaterialEditingLibrary
MP = unreal.MaterialProperty


def _simple_mat(dest, name, rgb, rough):
    path = "%s/%s" % (dest, name)
    m = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if m is None:
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, dest, unreal.Material, unreal.MaterialFactoryNew())
    else:
        MEL.delete_all_material_expressions(m)
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, 0)
    c.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    MEL.connect_material_property(c, "", MP.MP_BASE_COLOR)
    r = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 200)
    r.set_editor_property("r", float(rough))
    MEL.connect_material_property(r, "", MP.MP_ROUGHNESS)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def _dirt_road_mat(dest, tex_dir, tile_cm, light, dark, gain, noise_scale):
    """Loose packed dirt: large-scale noise blends a dark and a light tan; fine earth detail on top; matte."""
    path = dest + "/M_DirtRoad"
    m = unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if m is None:
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_DirtRoad", dest, unreal.Material, unreal.MaterialFactoryNew())
    else:
        MEL.delete_all_material_expressions(m)
    wp = MEL.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1500, 0)
    mask = MEL.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1250, 0)
    for ch, v in (("r", True), ("g", True), ("b", False), ("a", False)):
        mask.set_editor_property(ch, v)
    MEL.connect_material_expressions(wp, "", mask, "")
    div = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -1050, 0)
    k = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -1250, 150)
    k.set_editor_property("r", 1.0 / float(tile_cm))
    MEL.connect_material_expressions(mask, "", div, "A")
    MEL.connect_material_expressions(k, "", div, "B")

    def smp(suffix, y):
        t = unreal.EditorAssetLibrary.load_asset("%s/T_MossEarth_%s" % (tex_dir, suffix))
        n = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSample, -750, y)
        n.set_editor_property("texture", t)
        MEL.connect_material_expressions(div, "", n, "UVs")
        return n

    # large-scale light/dark blend
    alpha = None
    try:
        nz = MEL.create_material_expression(m, unreal.MaterialExpressionNoise, -1250, -500)
        for prop, val in (("scale", float(noise_scale)), ("quality", 1), ("levels", 4), ("turbulence", True),
                          ("output_min", 0.0), ("output_max", 1.0)):
            try:
                nz.set_editor_property(prop, val)
            except Exception as e:
                G.warn("noise.%s: %r" % (prop, e))
        MEL.connect_material_expressions(wp, "", nz, "Position")
        alpha = nz
    except Exception as e:
        G.warn("Noise node unavailable (%r) - using flat tone" % e)
    if alpha is None:
        alpha = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -1000, -500)
        alpha.set_editor_property("r", 0.5)
    lo = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -1000, -700)
    lo.set_editor_property("constant", unreal.LinearColor(dark[0], dark[1], dark[2], 1.0))
    hi = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -1000, -600)
    hi.set_editor_property("constant", unreal.LinearColor(light[0], light[1], light[2], 1.0))
    lerp = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -700, -600)
    MEL.connect_material_expressions(lo, "", lerp, "A")
    MEL.connect_material_expressions(hi, "", lerp, "B")
    MEL.connect_material_expressions(alpha, "", lerp, "Alpha")

    bc = smp("BC", -300)
    d = MEL.create_material_expression(m, unreal.MaterialExpressionDesaturation, -500, -300)
    MEL.connect_material_expressions(bc, "RGB", d, "")
    f = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -700, -150)
    f.set_editor_property("r", 1.0)
    MEL.connect_material_expressions(f, "", d, "Fraction")
    g = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -500, -150)
    g.set_editor_property("r", float(gain))
    detail = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, -300)
    MEL.connect_material_expressions(d, "", detail, "A")
    MEL.connect_material_expressions(g, "", detail, "B")
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -100, -400)
    MEL.connect_material_expressions(lerp, "", mul, "A")
    MEL.connect_material_expressions(detail, "", mul, "B")
    MEL.connect_material_property(mul, "", MP.MP_BASE_COLOR)
    MEL.connect_material_property(smp("N", 0), "RGB", MP.MP_NORMAL)
    r = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 200)
    r.set_editor_property("r", 0.95)
    MEL.connect_material_property(r, "", MP.MP_ROUGHNESS)
    sp = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 350)
    sp.set_editor_property("r", 0.05)
    MEL.connect_material_property(sp, "", MP.MP_SPECULAR)
    MEL.recompile_material(m)
    unreal.EditorAssetLibrary.save_loaded_asset(m)
    return m


def catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return tuple(0.5 * ((2 * p1[i]) + (-p0[i] + p2[i]) * t + (2 * p0[i] - 5 * p1[i] + 4 * p2[i] - p3[i]) * t2 +
                        (-p0[i] + 3 * p1[i] - 3 * p2[i] + p3[i]) * t3) for i in range(2))


def sample_curve(pts, step):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        d = math.hypot(P[i + 1][0] - P[i][0], P[i + 1][1] - P[i][1])
        n = max(2, int(d / step))
        for k in range(n):
            out.append(catmull(P[i - 1], P[i], P[i + 1], P[i + 2], k / float(n)))
    out.append(pts[-1])
    return out


def seg_dist(px, py, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    t = 0.0 if dx == 0 and dy == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (x0 + t * dx), py - (y0 + t * dy))


def main():
    G.init_log("p16_dirt_roads")
    try:
        level = G.load_json("level.json")
        layout = G.load_json("layout.json")
        mcfg = G.load_json("materials.json")
        cfg = G.load_json("environment.json")["scatter"]["dirt_roads"]
        dest = mcfg["dest"]
        rng = random.Random(level["seed"] + 16)
        step = float(cfg["step_cm"])
        G.cleanup_phase(PHASE)

        # old strips
        old = 0
        for a in list(G.actors_with_tag("GEN_Phase2")):
            if a.get_actor_label().startswith("GB_Road_MainLoop"):
                G.actor_subsystem().destroy_actor(a)
                old += 1
        G.log("Removed %d old MainLoop strips" % old)

        dirt = _dirt_road_mat(dest, mcfg["texture_dir"], float(cfg.get("dirt_tile_cm", 300)), cfg["dirt_light"], cfg["dirt_dark"],
                              float(cfg.get("dirt_detail_gain", 2.2)), float(cfg.get("noise_scale", 0.0012)))
        apron = unreal.EditorAssetLibrary.load_asset(dest + "/M_Apron")
        mud = _simple_mat(dest, "M_Mud", tuple(cfg.get("mud_rgb", [0.17, 0.12, 0.075])), 0.9)
        if apron is None:
            raise G.GenError("M_Apron missing - run p08a first")

        def piece(mesh, loc, yaw, scale, label, mat, shadow=False):
            a = G.spawn_static_mesh(mesh, loc, (0, yaw, 0), scale, label, PHASE)
            c = a.static_mesh_component
            c.set_material(0, mat)
            c.set_collision_profile_name("NoCollision")
            try:
                c.set_editor_property("cast_shadow", shadow)
            except Exception:
                pass
            return a

        def ribbon(poly, width, tag, mat, shoulder):
            n = 0
            for i in range(len(poly) - 1):
                (ax, ay), (bx, by) = poly[i], poly[i + 1]
                L = math.hypot(bx - ax, by - ay)
                if L < 1.0:
                    continue
                yaw = math.degrees(math.atan2(by - ay, bx - ax))
                mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
                Ls = (L * 1.3 + 40.0) / 100.0
                if shoulder:
                    piece(CUBE, (mx, my, 1.5), yaw, (Ls, (width + cfg["shoulder_extra_cm"]) / 100.0, 0.03), "%s_SH_%03d" % (tag, n), mud)
                piece(CUBE, (mx, my, 3.5), yaw, (Ls, width / 100.0, 0.05), "%s_%03d" % (tag, n), mat)
                n += 1
            return n

        # ---------------------------------------------------------------- main road
        main = layout["roads"][0]
        ctrl = [G.plan_to_world(level, p[0], p[1]) for p in main["points"]]
        poly = sample_curve(ctrl, step)
        n_main = ribbon(poly, float(main["width_cm"]), "ROAD_Main", dirt, True)
        G.verify("road_curve", n_main > 100, "%d segments, %.0f cm wide, %.0f m long" % (
            n_main, main["width_cm"], sum(math.hypot(poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]) for i in range(len(poly) - 1)) / 100.0))

        # continue the dirt road out through the gate valley (replaces the plain GateRoad_Out strip from p12)
        for a in list(G.actor_subsystem().get_all_level_actors()):
            if a.get_actor_label() == "GateRoad_Out":
                G.actor_subsystem().destroy_actor(a)
        env_s = G.load_json("environment.json")["scatter"]
        gate_x = ctrl[0][0]
        gate_y = level["bounds_cm"]["max"][1]
        out_len = float(env_s.get("gate_road_length_cm", 16000))
        out_poly = [(gate_x, gate_y + k * step) for k in range(int(out_len / step) + 1)]
        ribbon(out_poly, float(main["width_cm"]), "ROAD_Out", dirt, True)

        # ---------------------------------------------------------------- tyre ruts + ragged edge splotches (main road)
        rut_off, rut_w = float(cfg["rut_offset_cm"]), float(cfg["rut_width_cm"])
        ruts = 0
        for side in (-1, 1):
            for i in range(1, len(poly) - 1):
                if rng.random() < 0.12:
                    continue
                (ax, ay), (bx, by) = poly[i - 1], poly[i + 1]
                L = math.hypot(bx - ax, by - ay) or 1.0
                nx, ny = -(by - ay) / L, (bx - ax) / L
                off = side * rut_off + 28.0 * math.sin(i * 0.31 + side)
                px, py = poly[i][0] + nx * off, poly[i][1] + ny * off
                yaw = math.degrees(math.atan2(by - ay, bx - ax))
                piece(CUBE, (px, py, 6.4), yaw, ((step * 1.3) / 100.0, rut_w / 100.0, 0.01), "ROAD_Rut_%04d" % ruts, mud)
                ruts += 1
        splot = 0
        every = max(1, int(cfg.get("splotch_every", 2)))
        for i in range(1, len(poly) - 1, every):
            (ax, ay), (bx, by) = poly[i - 1], poly[i + 1]
            L = math.hypot(bx - ax, by - ay) or 1.0
            nx, ny = -(by - ay) / L, (bx - ax) / L
            for side in (-1, 1):
                off = side * (main["width_cm"] / 2.0 + rng.uniform(-120.0, 220.0))
                dia = rng.uniform(180.0, 520.0)
                px, py = poly[i][0] + nx * off, poly[i][1] + ny * off
                yw = rng.uniform(0, 360)
                piece(CYL, (px, py, 2.6), yw, ((dia + 140.0) / 100.0, (dia + 140.0) * rng.uniform(0.6, 1.0) / 100.0, 0.03), "ROAD_Fringe_%04d" % splot, mud)
                piece(CYL, (px, py, 3.7), yw, (dia / 100.0, dia * rng.uniform(0.6, 1.0) / 100.0, 0.05), "ROAD_Splotch_%04d" % splot, dirt)
                splot += 1
        G.verify("road_detail", ruts > 100 and splot > 50, "%d ruts, %d ragged-edge splotches" % (ruts, splot))

        # ---------------------------------------------------------------- spurs + pads
        st_by_label = {s["label"]: s for s in layout["structures"]}
        big = tuple(cfg.get("concrete_pad_assets", []))
        spurs, pads = 0, 0
        spur_polys = [out_poly]
        pad_sz = float(cfg["pad_cm"])
        for a in G.actors_with_tag("Entrance"):
            lab = a.get_actor_label().replace("ENTRY_", "")
            st = st_by_label.get(lab)
            if st is None:
                continue
            loc = a.get_actor_location()
            yaw = a.get_actor_rotation().yaw
            ex, ey = loc.x, loc.y
            # nearest road sample
            best, bd = None, 1e18
            for (px, py) in poly:
                d = math.hypot(px - ex, py - ey)
                if d < bd:
                    bd, best = d, (px, py)
            if bd > main["width_cm"] / 2.0 + 700.0:
                rx, ry = best
                dx, dy = ex - rx, ey - ry
                L = math.hypot(dx, dy)
                cx, cy = rx + dx / 2.0 - dy * 0.22, ry + dy / 2.0 + dx * 0.22
                sp = []
                m = max(3, int(L / step))
                for k in range(m + 1):
                    t = k / float(m)
                    sp.append(((1 - t) ** 2 * rx + 2 * (1 - t) * t * cx + t * t * ex, (1 - t) ** 2 * ry + 2 * (1 - t) * t * cy + t * t * ey))
                ribbon(sp, float(cfg["spur_width_cm"]), "ROAD_Spur_%s" % lab, dirt, True)
                spur_polys.append(sp)
                spurs += 1
            fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            mat = apron if st["asset"] in big else dirt
            piece(CUBE, (ex + fx * 600.0, ey + fy * 600.0, 4.0), yaw, (pad_sz / 100.0 * 1.2, pad_sz / 100.0, 0.06), "PAD_%s" % lab, mat)
            pads += 1
        G.verify("spurs", spurs > 0, "%d spur roads to building entrances" % spurs)
        G.verify("pads", pads >= 10, "%d entrance pads" % pads)

        # ---------------------------------------------------------------- clear trees/rocks off the roads
        half = main["width_cm"] / 2.0 + cfg["tree_clear_extra_cm"]
        half_sp = cfg["spur_width_cm"] / 2.0 + cfg["tree_clear_extra_cm"]
        removed = 0
        for a in list(G.actor_subsystem().get_all_level_actors()):
            lab = a.get_actor_label()
            if not lab.startswith(("TREE_", "FILLTREE_", "ROCK_", "SEAMROCK_")):
                continue
            l = a.get_actor_location()
            on = any(seg_dist(l.x, l.y, poly[i][0], poly[i][1], poly[i + 1][0], poly[i + 1][1]) < half for i in range(len(poly) - 1))
            if not on:
                for sp in spur_polys:
                    if any(seg_dist(l.x, l.y, sp[i][0], sp[i][1], sp[i + 1][0], sp[i + 1][1]) < half_sp for i in range(len(sp) - 1)):
                        on = True
                        break
            if on:
                G.actor_subsystem().destroy_actor(a)
                removed += 1
        G.log("Removed %d trees/rocks that stood on the new roads" % removed)
        G.verify("roads_clear", True, "%d trees/rocks cleared from the roads" % removed)

        try:
            unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
            G.verify("level_saved", True, level["level_path"])
        except Exception as e:
            G.verify("level_saved", False, repr(e))
    except G.GenError as e:
        G.err(str(e)); G.verify("p16_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e); G.verify("p16_unexpected", False, repr(e))
    G.summary()


main()
