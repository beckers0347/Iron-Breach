"""
Iron Breach -- real harbor water (Water plugin), AGGRESSIVE storm sea. Headless, idempotent, reversible.
Run:  py ib_build_harbor_water.py     (Water plugin must be enabled in the .uproject; editor + game CLOSED)
Replaces Shane's flat 'Water_Placeholder' slab (surface z=-35) with a WaterBodyLake over the same 3 km
footprint at the same height, driven by instanced Gerstner storm waves + the plugin's OCEAN material.
Placeholder is HIDDEN not deleted -- unhide it and delete 'Sea_Harbor' + 'WaterZone_Harbor' to revert.

v2 lessons (5.8 Python):
  * the spline lives on the actor as 'spline_comp'; 'water_waves' is set on the ACTOR (sea.set_water_waves)
  * editing GerstnerWaterWaveGeneratorSimple params does NOT recompute the wave set -- re-assign the
    generator on the GerstnerWaterWaves object afterwards (PostEditChange -> RecomputeWaves)
  * the body only regenerates its info meshes / collision / render data on a SHAPE change -- poke the
    spline (closed_loop) + the component transform after the spline points are in, or nothing renders in -game
"""
import unreal, os
def log(m): unreal.log(f"IBPY: {m}")
LEVEL = os.environ.get("IB_LEVEL", "/Game/LevelPrototyping/CarrowGateGarrison")
log(f"=== harbor water v2 -> {LEVEL} ===")
for cls in ("WaterBodyLake","WaterZone","GerstnerWaterWaves","GerstnerWaterWaveGeneratorSimple","WaterBodyComponent","WaterSplineComponent"):
    log(f"  plugin class {cls}: {'OK' if hasattr(unreal, cls) else 'MISSING'}")
if not hasattr(unreal, "WaterBodyLake"):
    raise RuntimeError("Water plugin classes not available -- enable the plugin in the .uproject")
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = EAS.get_all_level_actors()
def sett(o,p,v,quiet=False):
    try: o.set_editor_property(p,v); return True
    except Exception as e:
        if not quiet: log(f"  [skip] {p}: {str(e)[:100]}")
        return False
def methods(o, keys):
    return sorted(n for n in dir(o) if not n.startswith("_") and any(k in n.lower() for k in keys))

# ---- footprint from Shane's placeholder slab -------------------------------------------------------
ph = next((a for a in actors if a.get_actor_label()=="Water_Placeholder"), None)
if ph:
    o, ext = ph.get_actor_bounds(False)
    CX, CY, HX, HY, SURF_Z = o.x, o.y, ext.x, ext.y, o.z + ext.z
else:
    CX, CY, HX, HY, SURF_Z = 10000.0, -4000.0, 150000.0, 150000.0, -35.0
    log("  placeholder not found; using recorded geometry")
log(f"  water line z={SURF_Z}  footprint center=({CX},{CY}) half=({HX},{HY})")

# ---- water zone --------------------------------------------------------------------------------------
zone = next((a for a in actors if isinstance(a, unreal.WaterZone)), None)
if not zone:
    zone = EAS.spawn_actor_from_class(unreal.WaterZone, unreal.Vector(CX, CY, SURF_Z), unreal.Rotator(0,0,0))
    zone.set_actor_label("WaterZone_Harbor"); log("  spawned WaterZone")
sett(zone, "zone_extent", unreal.Vector2D(HX*2.2, HY*2.2))
sett(zone, "render_target_resolution", unreal.IntPoint(2048, 2048))   # 3.3 km zone -> ~1.6 m/texel shoreline depth
log("  zone methods: " + ", ".join(methods(zone, ("update","rebuild","mark","dirty"))))

# ---- water body --------------------------------------------------------------------------------------
sea = next((a for a in actors if a.get_actor_label()=="Sea_Harbor"), None)
if not sea:
    sea = EAS.spawn_actor_from_class(unreal.WaterBodyLake, unreal.Vector(CX, CY, SURF_Z), unreal.Rotator(0,0,0))
    sea.set_actor_label("Sea_Harbor"); log("  spawned WaterBodyLake 'Sea_Harbor'")
spline = None
for getter in (lambda: sea.get_editor_property("spline_comp"), lambda: sea.get_component_by_class(unreal.WaterSplineComponent)):
    try:
        spline = getter()
        if spline: break
    except Exception: pass
wbc = None
for getter in (lambda: sea.get_editor_property("water_body_component"), lambda: sea.get_component_by_class(unreal.WaterBodyComponent)):
    try:
        wbc = getter()
        if wbc: break
    except Exception: pass
if not spline or not wbc:
    raise RuntimeError(f"Sea_Harbor missing parts: spline={spline} body={wbc}")
log("  body methods:  " + ", ".join(methods(wbc, ("update","rebuild","reshape","mark","dirty","wave","zone"))))
log("  actor methods: " + ", ".join(methods(sea, ("update","rebuild","reshape","mark","dirty","wave"))))
log("  spline methods:" + ", ".join(methods(spline, ("update","rebuild","mark","dirty","closed"))))

def mesh_state(tag):
    for c in sea.get_components_by_class(unreal.StaticMeshComponent):
        try: sm = c.static_mesh
        except Exception: sm = None
        log(f"  [{tag}] {c.get_class().get_name()} '{c.get_name()}' mesh={sm.get_name() if sm else None} "
            f"visible={c.get_editor_property('visible')} hidden_in_game={c.get_editor_property('hidden_in_game')}")
mesh_state("before")

# spline = footprint rectangle at the water line
spline.clear_spline_points(True)
for (x,y) in ((CX-HX, CY-HY),(CX+HX, CY-HY),(CX+HX, CY+HY),(CX-HX, CY+HY)):
    spline.add_spline_point(unreal.Vector(x, y, SURF_Z), unreal.SplineCoordinateSpace.WORLD, True)
spline.set_closed_loop(True, True)
try: spline.update_spline()
except Exception: pass
log("  spline set to footprint (4 pts, closed)")

# ---- storm waves (instanced on the actor) ------------------------------------------------------------
ww = None
for getter in (lambda: sea.get_editor_property("water_waves"), lambda: wbc.get_water_waves()):
    try:
        ww = getter()
        if ww is not None: break
    except Exception: pass
if ww is None or not isinstance(ww, unreal.GerstnerWaterWaves):
    ww = unreal.GerstnerWaterWaves(outer=wbc)
    attached = False
    for setter in (lambda: sea.set_water_waves(ww), lambda: sea.set_editor_property("water_waves", ww)):
        try: setter(); attached = True; break
        except Exception as e: last = str(e)[:90]
    log(f"  waves attached: {attached}" + ("" if attached else f" (last err: {last})"))
gen = None
try: gen = ww.get_editor_property("gerstner_wave_generator")
except Exception: pass
if gen is None or not isinstance(gen, unreal.GerstnerWaterWaveGeneratorSimple):
    gen = unreal.GerstnerWaterWaveGeneratorSimple(outer=ww)
# AGGRESSIVE: 20 octaves, long swells + short chop, 2.8 m max amplitude, steep crests, wind from the open sea (west -> +X)
STORM = dict(num_waves=20, seed=7, randomness=0.35,
             min_wavelength=450.0, max_wavelength=16000.0, wavelength_falloff=1.1,
             min_amplitude=12.0,  max_amplitude=280.0,   amplitude_falloff=1.2,
             wind_angle_deg=0.0,  direction_angular_spread_deg=55.0,
             small_wave_steepness=0.9, large_wave_steepness=0.75, steepness_falloff=1.0)
for k,v in STORM.items(): sett(gen, k, v)
sett(ww, "gerstner_wave_generator", gen)      # (re)assign AFTER params -> PostEditChange -> RecomputeWaves
try:
    gw = list(ww.get_editor_property("gerstner_waves"))
    w0 = gw[0] if gw else None
    log(f"  wave set recomputed: {len(gw)} waves (want {STORM['num_waves']}); longest={w0.wave_length if w0 else None} amp={w0.amplitude if w0 else None}")
except Exception as e: log(f"  wave set check: {str(e)[:100]}")

# ---- materials (ocean look) ---------------------------------------------------------------------------
for mp in ("/Water/Materials/WaterSurface/Water_Material_Ocean.Water_Material_Ocean",):
    m = unreal.load_object(None, mp)
    if m:
        sett(wbc, "water_material", m); log(f"  water material -> {mp.split('/')[-1]}"); break

# ---- FORCE a shape update so the body regenerates info meshes / collision / render data ------------------
for name, fn in (("update_all", lambda: wbc.update_all()),
                 ("spline.closed_loop", lambda: spline.set_editor_property("closed_loop", True)),
                 ("body.relative_location", lambda: wbc.set_editor_property("relative_location", unreal.Vector(CX, CY, SURF_Z))),
                 ("actor.location", lambda: sea.set_actor_location(unreal.Vector(CX, CY, SURF_Z), False, False))):
    try: fn(); log(f"  poke {name}: ok")
    except Exception as e: log(f"  poke {name}: {str(e)[:100]}")
mesh_state("after")
try: log(f"  max wave height now: {wbc.get_max_wave_height()}")
except Exception: pass

# ---- retire the placeholder slab (hidden, not deleted) ----------------------------------------------------
if ph:
    ph.set_actor_hidden_in_game(True)
    try: ph.set_is_temporarily_hidden_in_editor(True)
    except Exception: pass
    log("  Water_Placeholder hidden (not deleted)")

saved=False
try: saved = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
except Exception as e: log(f"  save level: {str(e)[:80]}")
log(f"=== HARBOR WATER v2 DONE (saved={saved}) ===")
