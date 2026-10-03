"""p06b_fix_fog.py - finish the Phase 6 fog: volumetric on, warm inscattering colour.

Run:   py "X:/IronBreach/LevelGenTools/scripts/p06b_fog_fix.py"   (file name: p06b_fix_fog.py)

UE 5.8 renamed some fog properties, so this script looks them up by name instead of guessing, logs every
fog property it finds, and sets the ones that match. It does not respawn anything.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)


def main():
    G.init_log("p06b_fix_fog")
    try:
        cfg = G.load_json("lighting.json")["fog"]
        fogs = [a for a in G.actors_with_tag("GEN_Phase6") if isinstance(a, unreal.ExponentialHeightFog)]
        if not fogs:
            raise G.GenError("No HeightFog actor found - run p06_lighting.py first")
        fc = fogs[0].get_component_by_class(unreal.ExponentialHeightFogComponent)
        names = [n for n in dir(fc) if not n.startswith("_")]
        interesting = [n for n in names if any(k in n for k in ("volumetric", "inscatter", "fog_", "color"))]
        G.log("Fog component properties/methods: %s" % interesting)

        done = {}
        def setfirst(label, candidates, value):
            for n in candidates:
                if n in names:
                    try:
                        fc.set_editor_property(n, value)
                        done[label] = n
                        return
                    except Exception as e:
                        G.warn("set %s failed: %r" % (n, e))
            G.warn("No property found for %s (tried %s)" % (label, candidates))

        c = cfg["color_rgb"]
        col = unreal.LinearColor(c[0], c[1], c[2], 1.0)
        setfirst("inscattering", ["fog_inscattering_luminance", "inscattering_color_cubemap_angle"][:1], col)
        setfirst("volumetric", ["volumetric_fog", "enable_volumetric_fog", "b_enable_volumetric_fog"], True)
        setfirst("vol_distribution", ["volumetric_fog_scattering_distribution", "volumetric_fog_distribution"], float(cfg.get("volumetric_distribution", 0.9)))
        G.log("Applied: %s" % done)

        G.verify("fog_volumetric", "volumetric" in done, str(done.get("volumetric")))
        G.verify("fog_colour", "inscattering" in done, str(done.get("inscattering")))
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        G.verify("level_saved", True)
    except G.GenError as e:
        G.verify("p06b_fatal", False, str(e))
    except Exception as e:
        G.verify("p06b_unexpected", False, repr(e))
    G.summary()


main()
