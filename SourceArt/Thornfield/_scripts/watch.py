import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import kit
from kit import box, cylinder, uv_box
import kit2
from kit2 import Ctx, tower, finish, strut

NAME = "SM_WatchTower"


def build(M):
    c = Ctx(NAME); c.M = M; P = c.P
    slab = box("slab", (-7, -9, -0.3), (7, 7, 0), M["floor"], bev=0.03); uv_box(slab); P(slab)
    c.uc((-7, -9, -0.3), (7, 7, 0))
    info = tower(c, 0.0, 0.0, 6.0, 12.0, f"{NAME}_")
    top = info["top"]
    # searchlight on cabin roof
    base = cylinder("sl_base", (-2.2, 2.0, top + 0.2), 0.3, 0.4, M["steel"]); P(base)
    lamp = box("sl", (-2.6, 1.7, top + 0.4), (-1.8, 2.6, top + 0.9), M["olive"], bev=0.03); uv_box(lamp); P(lamp)
    lens = box("sll", (-2.5, 1.65, top + 0.5), (-1.9, 1.7, top + 0.8), M["white"]); P(lens)
    # railing on cabin roof edge
    for s in (-1, 1):
        for q in range(-3, 4):
            po = box("po", (s * 4.4 - .03, q * 1.0 - .03, top), (s * 4.4 + .03, q * 1.0 + .03, top + 0.9), M["steel"]); P(po)
            po2 = box("po", (q * 1.0 - .03, s * 4.4 - .03, top), (q * 1.0 + .03, s * 4.4 + .03, top + 0.9), M["steel"]); P(po2)
        r1 = box("rl", (s * 4.4 - .03, -4.4, top + 0.85), (s * 4.4 + .03, 4.4, top + 0.9), M["steel"]); P(r1)
        r2 = box("rl", (-4.4, s * 4.4 - .03, top + 0.85), (4.4, s * 4.4 + .03, top + 0.9), M["steel"]); P(r2)
    # banner on front
    for q in kit2.banner_obj(-0.9, 0.9, 4.0, 8.0, -3.5, M, "banner"):
        P(q)
    return c


def main(outdir):
    kit.reset()
    M = kit.std_materials()
    c = build(M)
    cams = [dict(name="front", loc=(-20, -26, 14), target=(0, 0, 8), lens=34, frame=1),
            dict(name="tower_int", loc=(0, -1.0, 1.5), target=(0, 1.5, 7.0), lens=22, frame=1,
                 pls=[(0, 0, 2.5, 800), (0, 0, 6.0, 800), (0, 0, 9.5, 800)]),
            dict(name="cabin_int", loc=(0, -1.5, 13.4), target=(0, 3.0, 13.6), lens=22, frame=1, pls=[(0, 0, 14.8, 600)])]
    finish(c, outdir, cams)


if __name__ == "__main__":
    main(sys.argv[1])
