"""Read-only inventory of the Blueprint title/menu widgets."""
import unreal
for path in ['/Game/UI/WBP_BootScreen', '/Game/UI/WBP_MainMenu']:
    bp = unreal.load_asset(path)
    unreal.log('IBMENU ASSET ' + path)
    tree = unreal.find_object(bp, 'WidgetTree')
    unreal.log('IBMENU TREE ' + str(tree))
    if not tree:
        continue
    try:
        for widget in unreal.ObjectIterator(unreal.Widget):
            if widget.get_outer() != tree:
                continue
            unreal.log('IBMENU WIDGET ' + widget.get_name() + ' ' + widget.get_class().get_name())
            if isinstance(widget, unreal.TextBlock):
                unreal.log('IBMENU TEXT ' + str(widget.get_text()))
    except Exception as error:
        unreal.log('IBMENU ERROR ' + str(error))
