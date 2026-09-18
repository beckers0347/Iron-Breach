"""
IBPY: ib_geoscript_probe4.py

READ-ONLY, tiny final probe. Just need
GeometryScriptBooleanOutputSpace's enum value names before writing the
real carving script -- guessing wrong here would put the boolean result in
the wrong coordinate space (e.g. world space instead of the asset's own
local/object space), which would silently corrupt the saved mesh rather
than throw an obvious error. Touches nothing.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_geoscript_probe4.py"
"""

import unreal


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    for name in ["GeometryScriptBooleanOutputSpace", "GeometryScriptLODType", "GeometryScriptPrimitiveOriginMode"]:
        cls = getattr(unreal, name, None)
        log(f"---- {name}: {'FOUND' if cls else 'NOT FOUND'} ----")
        if cls:
            log([e for e in dir(cls) if not e.startswith("_")])
    log("Done.")


main()
