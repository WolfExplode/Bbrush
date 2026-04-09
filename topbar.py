import bpy

from .utils import get_pref


def top_bar_draw(self, context):
    if context.mode != "SCULPT":
        return

    pref = get_pref()
    layout = self.layout

    row = layout.row(align=True)
    row.separator(factor=2)
    row.prop(pref, "depth_display_mode", emboss=True, text="")
    row.separator(factor=5)


def register():
    bpy.types.VIEW3D_MT_editor_menus.append(top_bar_draw)


def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(top_bar_draw)
