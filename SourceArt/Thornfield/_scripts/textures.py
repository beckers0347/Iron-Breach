"""Procedural tileable PBR textures for the Thornfield Garrison kit.
Outputs per material: T_<name>_BC.png (base color), T_<name>_N.png (normal, OpenGL +Y),
T_<name>_ORM.png (R=AO, G=Roughness, B=Metallic).  All tile at 2 m x 2 m unless noted.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

RES = int(os.environ.get("TEX_RES", "2048"))
SEED = 1337


def fft_noise(res, beta=2.0, seed=0, stretch=(1.0, 1.0)):
    """Tileable noise with 1/f^beta spectrum, normalised to 0..1. stretch>1 elongates features on that axis."""
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((res, res))
    F = np.fft.fft2(w)
    fy = np.fft.fftfreq(res)[:, None] * stretch[0]
    fx = np.fft.fftfreq(res)[None, :] * stretch[1]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1.0
    F = F / (f ** (beta / 2.0))
    F[0, 0] = 0
    n = np.real(np.fft.ifft2(F))
    n -= n.min()
    n /= max(n.max(), 1e-9)
    return n


def fbm(res, seed, octaves=(1.6, 2.2, 2.8), weights=(0.5, 0.3, 0.2), stretch=(1, 1)):
    out = np.zeros((res, res))
    for i, (b, wt) in enumerate(zip(octaves, weights)):
        out += wt * fft_noise(res, b, seed + i * 17, stretch)
    out -= out.min()
    out /= out.max()
    return out


def blur(a, s):
    return ndi.gaussian_filter(a, s, mode="wrap")


def normal_from_height(h, strength=6.0):
    gx = np.roll(h, -1, 1) - np.roll(h, 1, 1)
    gy = np.roll(h, -1, 0) - np.roll(h, 1, 0)
    nx = -gx * strength
    ny = gy * strength  # OpenGL (+Y up)
    nz = np.ones_like(h)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / l, ny / l, nz / l], -1)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def save_set(outdir, name, color, height, rough, metal=None, ao=None, nstrength=6.0):
    os.makedirs(outdir, exist_ok=True)
    color = np.clip(color, 0, 1)
    if ao is None:
        ao = np.clip(0.55 + 0.45 * blur(height, 3) / max(height.max(), 1e-6) * 0 + 0.45 * (1 - np.clip(blur(height, 6) - height, 0, 1) * 4), 0, 1)
    if metal is None:
        metal = np.zeros_like(height)
    Image.fromarray((color * 255).astype(np.uint8)).save(os.path.join(outdir, f"T_{name}_BC.png"))
    Image.fromarray(normal_from_height(height, nstrength)).save(os.path.join(outdir, f"T_{name}_N.png"))
    orm = np.stack([np.clip(ao, 0, 1), np.clip(rough, 0, 1), np.clip(metal, 0, 1)], -1)
    Image.fromarray((orm * 255).astype(np.uint8)).save(os.path.join(outdir, f"T_{name}_ORM.png"))
    print("wrote", name)


def lerp(a, b, t):
    return a + (b - a) * t[..., None] if np.ndim(t) == 2 else a + (b - a) * t


def concrete(outdir, name="Concrete", base=(0.46, 0.46, 0.44), dark=0.62, seed=SEED):
    r = RES
    big = fbm(r, seed, (2.4, 2.8, 3.0), (0.5, 0.3, 0.2))
    mid = fft_noise(r, 1.2, seed + 5)
    fine = fft_noise(r, 0.4, seed + 9)
    stain = fbm(r, seed + 40, (2.8, 3.0), (0.6, 0.4), stretch=(0.15, 1.0))  # vertical streaks
    pores = (fine > 0.86).astype(float)
    pores = blur(pores, 1.2)
    col = np.array(base)[None, None, :] * (0.78 + 0.45 * big[..., None])
    col *= (1 - 0.35 * (stain[..., None] > 0.62) * (stain[..., None] - 0.62) * 3)
    col *= (1 - 0.35 * pores[..., None])
    col[..., 0] *= 1.0 + 0.03 * (mid - 0.5)
    col[..., 2] *= 1.0 + 0.04 * (big - 0.5)
    # form-tie holes + panel joint lines every 1m
    h = 0.5 * big + 0.25 * mid + 0.25 * fine
    yy, xx = np.mgrid[0:r, 0:r] / r
    joint = (np.abs((xx * 2 % 1) - 0.0) < 0.002) | (np.abs((yy * 2 % 1) - 0.0) < 0.002) | (np.abs((xx * 2 % 1) - 1.0) < 0.002)
    h = np.where(joint, h - 0.25, h)
    col = np.where(joint[..., None], col * 0.6, col)
    ties = np.zeros((r, r))
    for gy in np.arange(0.125, 2, 0.5):
        for gx in np.arange(0.25, 2, 0.5):
            cy, cx = int(gy / 2 * r), int(gx / 2 * r)
            ties[max(cy - 6, 0):cy + 6, max(cx - 6, 0):cx + 6] = 1
    ties = blur(ties, 2.0)
    h -= 0.35 * ties
    col *= (1 - 0.5 * ties[..., None])
    rough = np.clip(0.82 + 0.15 * (fine - 0.5) - 0.1 * (stain > 0.7), 0.3, 1)
    save_set(outdir, name, col, h, rough, nstrength=8)


def steel(outdir, name="Steel", base=(0.30, 0.33, 0.33), seed=SEED + 100):
    """Painted charcoal steel with 1 m panels, seams, rivets and edge wear."""
    r = RES
    big = fbm(r, seed, (2.4, 2.8), (0.6, 0.4))
    fine = fft_noise(r, 0.6, seed + 3)
    scr = fbm(r, seed + 8, (0.8, 1.0), (0.6, 0.4), stretch=(0.05, 1.0))
    yy, xx = np.mgrid[0:r, 0:r] / r
    ps = 1.0  # panel size in tile units (tile = 2 m -> 1 m panels)
    u = (xx * 2) % 1.0
    v = (yy * 2) % 1.0
    edge = np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v))  # distance to panel edge (0..0.5)
    seam = edge < 0.006
    bevel = np.clip(1 - edge / 0.03, 0, 1)
    height = 0.55 + 0.1 * (fine - 0.5) - 0.35 * seam + 0.05 * (1 - bevel)
    # rivets 12 cm inset
    riv = np.zeros((r, r))
    n = 8
    for k in range(n):
        t = (k + 0.5) / n
        for (cx, cy) in [(t, 0.07), (t, 0.93), (0.07, t), (0.93, t)]:
            for px in range(2):
                for py in range(2):
                    X = int(((cx + px) / 2.0) * r) % r
                    Y = int(((cy + py) / 2.0) * r) % r
                    riv[max(Y - 5, 0):Y + 5, max(X - 5, 0):X + 5] = 1
    riv = blur(riv, 1.5)
    riv = np.clip(riv * 3, 0, 1)
    height += 0.4 * riv
    wear = np.clip((0.55 - edge * 12) + (big - 0.5) * 0.8 + (scr - 0.55) * 0.7, 0, 1)
    wear = np.where(fine > 0.55, wear, wear * 0.5)
    wear = np.clip(wear, 0, 1)
    metal_col = np.array((0.55, 0.56, 0.58))
    rust = np.clip((fbm(r, seed + 70, (2.8, 3.0), (0.6, 0.4), stretch=(0.2, 1.0)) - 0.62) * 3, 0, 1)
    col = np.array(base)[None, None, :] * (0.85 + 0.5 * big[..., None])
    col = lerp(col, metal_col[None, None, :], np.clip(wear, 0, 1) * 0.8)
    col = lerp(col, np.array((0.28, 0.14, 0.07))[None, None, :], rust * 0.55)
    col = col * (1 - 0.35 * seam[..., None])
    rough = np.clip(0.52 + 0.2 * (fine - 0.5) - 0.2 * wear + 0.2 * rust, 0.2, 1)
    metal = np.clip(wear * 0.9, 0, 1)
    save_set(outdir, name, col, height, rough, metal, nstrength=7)


def hazard(outdir, name="Hazard", seed=SEED + 200):
    r = RES
    yy, xx = np.mgrid[0:r, 0:r] / r
    k = 8  # stripes per tile
    s = ((xx + yy) * k) % 1.0
    band = s < 0.5
    big = fbm(r, seed, (2.4, 2.8), (0.6, 0.4))
    fine = fft_noise(r, 0.5, seed + 2)
    yel = np.array((0.78, 0.55, 0.05))
    blk = np.array((0.04, 0.04, 0.045))
    col = np.where(band[..., None], yel[None, None, :], blk[None, None, :]) * (0.7 + 0.5 * big[..., None])
    worn = np.clip((fbm(r, seed + 9, (2.0, 2.8), (0.6, 0.4)) - 0.55) * 3, 0, 1)
    conc = np.array((0.4, 0.4, 0.38))[None, None, :] * (0.7 + 0.5 * fine[..., None])
    col = lerp(col, conc, worn * 0.8)
    h = 0.5 + 0.1 * fine
    rough = np.clip(0.55 + 0.35 * worn + 0.1 * (fine - 0.5), 0.2, 1)
    save_set(outdir, name, col, h, rough, nstrength=3)


def moss(outdir, name="MossEarth", seed=SEED + 300):
    r = RES
    big = fbm(r, seed, (2.2, 2.6, 3.0), (0.5, 0.3, 0.2))
    mid = fft_noise(r, 1.4, seed + 3)
    fine = fft_noise(r, 0.3, seed + 6)
    soil = fbm(r, seed + 20, (2.6, 3.0), (0.6, 0.4))
    moss_a = np.array((0.20, 0.27, 0.08))
    moss_b = np.array((0.33, 0.40, 0.14))
    grass = np.array((0.28, 0.33, 0.09))
    dirt = np.array((0.16, 0.12, 0.08))
    col = lerp(moss_a[None, None, :], moss_b[None, None, :], big)
    col = lerp(col, grass[None, None, :], np.clip((mid - 0.5) * 3, 0, 1) * 0.6)
    col = lerp(col, dirt[None, None, :], np.clip((soil - 0.62) * 4, 0, 1))
    col *= (0.75 + 0.5 * fine[..., None])
    h = 0.35 * big + 0.35 * mid + 0.3 * fine
    rough = np.clip(0.85 + 0.1 * (fine - 0.5), 0.5, 1)
    save_set(outdir, name, col, h, rough, nstrength=10)


def floor_concrete(outdir, name="FloorConcrete", seed=SEED + 400):
    r = RES
    big = fbm(r, seed, (2.4, 2.8, 3.0), (0.5, 0.3, 0.2))
    fine = fft_noise(r, 0.5, seed + 4)
    stain = fbm(r, seed + 11, (2.4, 2.8), (0.6, 0.4))
    yy, xx = np.mgrid[0:r, 0:r] / r
    jx = np.abs(((xx * 1) % 1.0) - 0.0) < 0.003  # 2 m slabs
    jy = np.abs(((yy * 1) % 1.0) - 0.0) < 0.003
    joint = jx | jy
    col = np.array((0.30, 0.30, 0.29))[None, None, :] * (0.7 + 0.5 * big[..., None])
    col *= (1 - 0.45 * np.clip((stain - 0.6) * 3, 0, 1)[..., None])
    col = np.where(joint[..., None], col * 0.45, col)
    h = 0.5 * big + 0.2 * fine - 0.3 * joint
    rough = np.clip(0.7 + 0.2 * (fine - 0.5) - 0.25 * np.clip((stain - 0.6) * 3, 0, 1), 0.15, 1)
    save_set(outdir, name, col, h, rough, nstrength=5)


def banner(outdir, name="Banner", w=1024, h=2048):
    """Dark blue banner with white winged emblem (non-tiling)."""
    rng = np.random.default_rng(5)
    img = Image.new("RGB", (w, h), (20, 36, 78))
    d = ImageDraw.Draw(img)
    cx, cy = w // 2, int(h * 0.42)
    white = (232, 236, 242)
    d.polygon([(cx, cy - 170), (cx + 38, cy - 90), (cx + 24, cy + 150), (cx, cy + 210), (cx - 24, cy + 150), (cx - 38, cy - 90)], fill=white)
    d.polygon([(cx, cy - 250), (cx + 34, cy - 190), (cx, cy - 150), (cx - 34, cy - 190)], fill=white)
    for sgn in (1, -1):
        for k in range(5):
            bx, by = cx + sgn * 34, cy - 70 + k * 48
            tx, ty = cx + sgn * (400 - k * 62), cy - 330 + k * 62
            d.polygon([(bx, by), (tx, ty), (tx - sgn * 8, ty + 70), (bx, by + 52)], fill=white)
        # tail fan
        for k in range(3):
            d.polygon([(cx + sgn * 6, cy + 150), (cx + sgn * (70 + k * 55), cy + 330 + k * 25),
                       (cx + sgn * (30 + k * 55), cy + 345 + k * 25), (cx, cy + 190)], fill=white)
    d.rectangle([30, 30, w - 30, h - 30], outline=(190, 198, 215), width=10)
    d.rectangle([0, h - 120, w, h], fill=(12, 22, 50))
    arr = np.array(img).astype(float)
    arr *= (0.9 + 0.15 * rng.random((h, w, 1)) * 0 + 0.1 * fft_noise(512, 1.6, 3).repeat(h // 512, 0).repeat(w // 512, 1)[..., None] * 1.0)
    arr += (rng.random((h, w, 1)) - 0.5) * 8
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    os.makedirs(outdir, exist_ok=True)
    img.save(os.path.join(outdir, f"T_{name}_BC.png"))
    g = np.array(img.convert("L")).astype(float) / 255
    g = blur(g, 1.0)
    Image.fromarray(normal_from_height(g, 2.0)).save(os.path.join(outdir, f"T_{name}_N.png"))
    orm = np.stack([np.ones((h, w)), np.full((h, w), 0.9), np.zeros((h, w))], -1)
    Image.fromarray((orm * 255).astype(np.uint8)).save(os.path.join(outdir, f"T_{name}_ORM.png"))
    print("wrote", name)


def make_all(outdir):
    concrete(outdir)
    concrete(outdir, "ConcreteDark", base=(0.30, 0.30, 0.29), seed=SEED + 11)
    steel(outdir)
    hazard(outdir)
    moss(outdir)
    floor_concrete(outdir)
    banner(outdir)


if __name__ == "__main__":
    make_all(sys.argv[1] if len(sys.argv) > 1 else "tex")
