"""
Pull the actual reflected docstrings for the IK Rig API calls we need,
instead of continuing to guess constructor/property signatures one failed
round-trip at a time. Unreal's Python bindings auto-generate docstrings with
real parameter info from the engine's reflection system -- this prints them
directly.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/introspect_ikrig_api.py"
"""

import unreal

unreal.log("[Introspect] === unreal.BoneChain.__doc__ ===")
unreal.log(str(unreal.BoneChain.__doc__))

unreal.log("[Introspect] === unreal.BoneReference.__doc__ ===")
unreal.log(str(unreal.BoneReference.__doc__))

unreal.log("[Introspect] === unreal.IKRigController.add_retarget_chain.__doc__ ===")
unreal.log(str(unreal.IKRigController.add_retarget_chain.__doc__))

unreal.log("[Introspect] === dir(unreal.IKRigController) (methods only, no dunders) ===")
methods = [m for m in dir(unreal.IKRigController) if not m.startswith("_")]
unreal.log(str(methods))
