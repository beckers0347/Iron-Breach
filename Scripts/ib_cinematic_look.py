"""
Iron Breach -- cinematic look, PRE-DAWN edition (headless, idempotent, REVERSIBLE).
Run via the build watcher:  py ib_cinematic_look.py     (IB_LEVEL env overrides target)

CarrowGateGarrison is authored as a pre-dawn scene (DirLight_PreDawn, dim skylight,
two fog volumes, 19 practical lamps) to match M1 LANDFALL's opening. This does NOT
flatten that into daylight -- it makes the pre-dawn read cinematic:
  * volumetric fog ON in the existing fog volumes -> god-rays off the low sun
  * VolumetricCloud added -> clouds lit from underneath at dawn
  * sun kept low + dim as authored, nudged warmer; skylight real-time for Lumen bounce
  * exposure: constrained histogram auto (min -4 / max 6 EV100, bias -0.7) on THIS layer only,
    because the author's manual EV was tuned for different lighting and can't follow the new fog/sky
  * a NEW unbound PostProcessVolume "PPV_IB_CinematicLook" at priority 10 layers a
    restrained filmic grade over the author's own PPV (only overridden props apply,
    so delete that one actor to revert everything).
Restraint is deliberate: heavy vignette/grain/fringe reads amateur; subtle reads AAA.
"""
import unreal, os

def log(m): unreal.log(f"IBPY: {m}")
LEVEL = os.environ.get("IB_LEVEL", "/Game/LevelPrototyping/CarrowGateGarrison")
log(f"=== cinematic look (pre-dawn) -> {LEVEL} ===")
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
EAS = unreal.EditorActorSubsystem()
actors = EAS.get_all_level_actors()

def sett(obj, prop, value, quiet=False):
    try: obj.set_editor_property(prop, value); return True
    except Exception as e:
        if not quiet: log(f"  [skip] {prop}: {str(e)[:90]}")
        return False
def gett(obj, prop, default=None):
    try: return obj.get_editor_property(prop)
    except Exception: return default
def spawn(cls, loc=(0,0,0)):
    a = EAS.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(0,0,0))
    log(f"  spawned {cls.__name__}"); return a

# ---------------------------------------------------------------- BASELINE (what the author built)
log("--- baseline ---")
for a in actors:
    if isinstance(a, unreal.PostProcessVolume):
        log(f"  PPV '{a.get_actor_label()}' unbound={gett(a,'unbound')} priority={gett(a,'priority')} enabled={gett(a,'enabled')}")
    elif isinstance(a, unreal.ExponentialHeightFog):
        c = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
        vf = gett(c,'enable_volumetric_fog', gett(c,'volumetric_fog','?'))
        log(f"  Fog '{a.get_actor_label()}' volumetric={vf} density={gett(c,'fog_density')} falloff={gett(c,'fog_height_falloff')} start={gett(c,'start_distance')}")

# ---------------------------------------------------------------- SUN: keep the author's pre-dawn, make it read as a sun
suns = [a for a in actors if isinstance(a, unreal.DirectionalLight)]
sun = suns[0] if suns else spawn(unreal.DirectionalLight, (0,0,1000))
sc = sun.get_component_by_class(unreal.DirectionalLightComponent)
sun.set_actor_rotation(unreal.Rotator(pitch=-6.0, yaw=180.0, roll=0.0), False)  # sunrise moment: keep author yaw, drop to horizon
if sc:
    sett(sc, "use_temperature", True)
    sett(sc, "temperature", 4500.0)        # golden at the horizon; at 6 deg it only RIMS surfaces, cannot orange-wash
    sett(sc, "light_source_angle", 0.7)    # soft disc low on the horizon
    sett(sc, "atmosphere_sun_light", True) # drives SkyAtmosphere + cloud lighting
    sett(sc, "cast_cloud_shadows", True)
    sett(sc, "cast_shadows", True)
    sett(sc, "dynamic_shadow_distance_movable_light", 40000.0)
    sett(sc, "volumetric_scattering_intensity", 0.6)  # modest: sun is an accent, not the fill
log(f"sun '{sun.get_actor_label()}' warmed, kept low (intensity left as authored: {gett(sc,'intensity')})")

# ---------------------------------------------------------------- SKY / CLOUDS / SKYLIGHT
if not any(isinstance(a, unreal.SkyAtmosphere) for a in actors): spawn(unreal.SkyAtmosphere)
if not any(isinstance(a, unreal.VolumetricCloud) for a in actors):
    spawn(unreal.VolumetricCloud)          # dawn clouds lit from beneath = free drama
skys = [a for a in actors if isinstance(a, unreal.SkyLight)]
sky = skys[0] if skys else spawn(unreal.SkyLight, (0,0,1200))
kc = sky.get_component_by_class(unreal.SkyLightComponent)
if kc:
    sett(kc, "mobility", unreal.ComponentMobility.MOVABLE, quiet=True)
    sett(kc, "real_time_capture", True)    # Lumen-friendly, tracks the sky as it is
    cur = gett(kc, "intensity", 0.3)
    sett(kc, "intensity", max(cur, 1.6))   # blue counterpoint: overhead sky fills the shadows cool
    sett(kc, "volumetric_scattering_intensity", 2.0)  # and the sky lights the fog -> cool blue haze
    try: kc.recapture_sky()
    except Exception: pass
log("sky / clouds / skylight tuned")

# ---------------------------------------------------------------- VOLUMETRIC FOG (the big one)
fogs = [a for a in actors if isinstance(a, unreal.ExponentialHeightFog)]
if not fogs: fogs = [spawn(unreal.ExponentialHeightFog, (0,0,0))]
for f in fogs:
    fc = f.get_component_by_class(unreal.ExponentialHeightFogComponent)
    if not fc: continue
    on = sett(fc, "enable_volumetric_fog", True, quiet=True) or sett(fc, "volumetric_fog", True)
    sett(fc, "volumetric_fog_scattering_distribution", 0.15)  # gentle shafts, no blowout
    sett(fc, "volumetric_fog_extinction_scale", 0.8)          # authored densities were for non-volumetric; thin it
    sett(fc, "volumetric_fog_albedo", unreal.Color(190, 205, 235, 255))  # cool blue pre-dawn haze
    sett(fc, "volumetric_fog_distance", 12000.0)
    if gett(fc, "fog_density", 0) < 0.008:  # only lift genuinely-empty fog; respect authored density
        sett(fc, "fog_density", 0.012)
    log(f"  fog '{f.get_actor_label()}' volumetric={'ON' if on else 'unchanged'} density={gett(fc,'fog_density')}")
log("volumetric fog tuned")

# ---------------------------------------------------------------- LAYERED POST-PROCESS (reversible)
NAME = "PPV_IB_CinematicLook"
ppv = next((a for a in actors if isinstance(a, unreal.PostProcessVolume) and a.get_actor_label()==NAME), None)
if not ppv:
    ppv = spawn(unreal.PostProcessVolume, (0,0,0))
    ppv.set_actor_label(NAME)
sett(ppv, "unbound", True); sett(ppv, "priority", 10.0); sett(ppv, "enabled", True)
s = ppv.get_editor_property("settings")
def ov(flag, prop, value): sett(s, flag, True, quiet=True); sett(s, prop, value)

# Exposure: the author's MANUAL EV was calibrated for THEIR lighting. With fog/clouds/skylight
# changed, that EV no longer matches (pass 2 went orange, 3-4 went black). So this layer runs a
# CONSTRAINED histogram auto-exposure: it adapts to the real light so the scene is readable,
# the max cap keeps it from ever blowing out to daylight, and a negative bias holds the mood.
# (ExtendDefaultLuminanceRange is on in DefaultEngine.ini -> min/max are EV100.)
ov("override_auto_exposure_method", "auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM)
ov("override_auto_exposure_min_brightness", "auto_exposure_min_brightness", -4.0)  # may adapt to a very dark scene
ov("override_auto_exposure_max_brightness", "auto_exposure_max_brightness", 6.0)   # ...but never brighter than dusk
ov("override_auto_exposure_bias", "auto_exposure_bias", -0.35)                      # a touch below mid-grey: mood, but readable
ov("override_auto_exposure_speed_up", "auto_exposure_speed_up", 3.0)
ov("override_auto_exposure_speed_down", "auto_exposure_speed_down", 1.0)
ov("override_auto_exposure_low_percent", "auto_exposure_low_percent", 75.0)
ov("override_auto_exposure_high_percent", "auto_exposure_high_percent", 92.0)
ov("override_local_exposure_highlight_contrast_scale", "local_exposure_highlight_contrast_scale", 0.75)
ov("override_local_exposure_shadow_contrast_scale", "local_exposure_shadow_contrast_scale", 0.6)    # open the shadows: buildings must READ

# Bloom: the 19 lamps + the low sun get a soft glow.
ov("override_bloom_intensity", "bloom_intensity", 0.45)
ov("override_bloom_threshold", "bloom_threshold", -1.0)

# Blue-hour grade: cool, slightly desaturated shadows; warm highlights; a hair of contrast.
ov("override_white_temp", "white_temp", 7000.0)                                   # cool base; sky is now naturally blue
ov("override_color_saturation", "color_saturation", unreal.Vector4(1.06, 1.06, 1.06, 1.0))   # rich, not crushed
ov("override_color_contrast", "color_contrast", unreal.Vector4(1.08, 1.08, 1.08, 1.0))
ov("override_color_saturation_shadows", "color_saturation_shadows", unreal.Vector4(0.95, 1.0, 1.12, 1.0))
ov("override_color_gain_shadows", "color_gain_shadows", unreal.Vector4(0.90, 0.96, 1.14, 1.0))    # blue-grey shadows vs gold sky
ov("override_color_gain_highlights", "color_gain_highlights", unreal.Vector4(1.02, 1.0, 0.98, 1.0))
ov("override_color_grading_intensity", "color_grading_intensity", 1.0)

# Texture: fine and quiet.
ov("override_film_grain_intensity", "film_grain_intensity", 0.15)
ov("override_vignette_intensity", "vignette_intensity", 0.32)
ov("override_scene_fringe_intensity", "scene_fringe_intensity", 0.0)  # CA off -- reads cheap
ov("override_motion_blur_amount", "motion_blur_amount", 0.25)

# Lumen quality bump (screenshot-grade; ease back for shipping perf if needed).
ov("override_lumen_scene_lighting_quality", "lumen_scene_lighting_quality", 2.0)
ov("override_lumen_scene_detail", "lumen_scene_detail", 2.0)
ov("override_lumen_final_gather_quality", "lumen_final_gather_quality", 2.0)
ov("override_lumen_scene_view_distance", "lumen_scene_view_distance", 20000.0)
ov("override_reflection_method", "reflection_method", unreal.ReflectionMethod.LUMEN)
ov("override_lumen_reflection_quality", "lumen_reflection_quality", 2.0)

ppv.set_editor_property("settings", s)
log(f"post-process layered as '{NAME}' (priority 10, unbound) -- delete that actor to revert")

# ---------------------------------------------------------------- SAVE
saved = False
for fn in ("save_current_level",):
    try: unreal.EditorLevelLibrary.save_current_level(); saved = True; break
    except Exception as e: log(f"  save via EditorLevelLibrary failed: {str(e)[:80]}")
if not saved:
    try: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True); saved = True
    except Exception as e: log(f"  save_dirty_packages failed: {str(e)[:80]}")
log(f"=== CINEMATIC LOOK DONE (saved={saved}) ===")
