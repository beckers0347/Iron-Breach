"""Compile-check the Watch materials (headless): stats force a synchronous compile, so HLSL
errors in the Custom nodes show up here as LogMaterial errors instead of at game start."""
import unreal
MEL = unreal.MaterialEditingLibrary
for name in ["M_WatchMap", "M_WatchPlanet"]:
    mat = unreal.load_asset(f"/Game/IronBreach/Watch/{name}")
    if mat is None:
        unreal.log_error(f"IBPY: {name} MISSING")
        continue
    st = MEL.get_statistics(mat)
    unreal.log(f"IBPY: {name} stats: ps_instr={st.num_pixel_shader_instructions} vs_instr={st.num_vertex_shader_instructions} samplers={st.num_samplers}")
unreal.log("IBPY: VERIFY DONE")
