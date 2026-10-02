"""Apply the shared menu palette to authored title widgets; retain their input graph and logo."""
import unreal
eal = unreal.EditorAssetLibrary
bp = unreal.load_asset('/Game/UI/WBP_BootScreen')
tree = unreal.find_object(bp, 'WidgetTree')
prompt = unreal.find_object(tree, 'TextBlock_188')
assert isinstance(prompt, unreal.TextBlock)
font = prompt.get_editor_property('font')
font.set_editor_property('size', 18)
font.set_editor_property('letter_spacing', 80)
prompt.set_font(font)
prompt.set_text('PRESS ANY BUTTON TO START')
prompt.set_color_and_opacity(unreal.SlateColor(specified_color=unreal.LinearColor(.28,.78,.9,1)))
prompt.set_shadow_offset(unreal.Vector2D(0,0))
eal.save_loaded_asset(bp)
main = unreal.load_asset('/Game/UI/WBP_MainMenu')
main_tree = unreal.find_object(main, 'WidgetTree')
background = unreal.find_object(main_tree, 'Image_0')
if isinstance(background, unreal.Image):
    background.set_brush_from_texture(unreal.load_asset('/Game/IronBreach/UI/Hangar/T_MenuHangar'))
eal.save_loaded_asset(main)
unreal.log('IBMENU title and main menu saved; Blueprint input graphs retained')
