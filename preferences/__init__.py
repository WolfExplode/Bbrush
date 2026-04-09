import bpy

from .depth_map import DepthMap
from .. import __package__ as base_name


class BBRUSH_OT_rebuild_keyconfig(bpy.types.Operator):
    bl_idname = "bbrush.rebuild_keyconfig"
    bl_label = "Rebuild BBrush Keymap"
    bl_description = "Rebuild the add-on keymap overlay from current addon preferences"
    bl_options = {"REGISTER"}

    def execute(self, context):
        try:
            from ..sculpt.keymap import BrushKeymap
            BrushKeymap.unregister_addon_keymaps()
            BrushKeymap.register_addon_keymaps(context)
        except Exception as e:
            self.report({"ERROR"}, f"Failed to rebuild keymap: {getattr(e, 'args', [str(e)])[0]}")
            return {"CANCELLED"}

        self.report({"INFO"}, "BBrush keymap rebuilt.")
        return {"FINISHED"}


class BBRUSH_OT_debug_toggle_console(bpy.types.Operator):
    bl_idname = "bbrush.debug_toggle_console"
    bl_label = "System Console"
    bl_description = "Show or hide Blender's system console (Windows; logs appear here when Debug is on)"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.console_toggle()
        self.report({"INFO"}, "Toggled system console.")
        return {"FINISHED"}


class BBRUSH_OT_debug_print_state(bpy.types.Operator):
    bl_idname = "bbrush.debug_print_state"
    bl_label = "Print State"
    bl_description = "Print current Bbrush runtime state to the system console"
    bl_options = {"REGISTER"}

    def execute(self, context):
        from ..sculpt import brush_runtime
        from ..sculpt import keymap as bbrush_keymap
        from ..sculpt.update_brush_shelf import brush_shelf

        lines = (
            f"context.mode={context.mode!r}",
            f"brush_runtime={brush_runtime!r}",
            f"addon_keymap_items={len(bbrush_keymap.keys)}",
            f"brush_shelf_keys={list(brush_shelf.keys())}",
        )
        for line in lines:
            print("BBrush debug:", line)
        self.report({"INFO"}, "State printed to system console.")
        return {"FINISHED"}


class Preferences(
    bpy.types.AddonPreferences,

    DepthMap,
):
    bl_idname = base_name

    depth_ray_size: bpy.props.IntProperty(
        name="Depth ray check size(px)",
        description="Check if the mouse is placed over the model, mouse cursor range size",
        default=50,
        min=10,
        max=300)

    enabled_drag_offset_compensation: bpy.props.BoolProperty(name="Enabled drag offset compensation", default=False)
    drag_offset_compensation: bpy.props.FloatProperty(
        name="Drag offset compensation",
        description="Compensate for mouse position movement during drawing",
        min=0.1,
        default=0.5,
        max=2
    )

    refresh_fps: bpy.props.IntProperty(name="Refresh FPS", default=1, min=1, max=120)
    debug: bpy.props.BoolProperty(
        name="Debug logging",
        description="Print Bbrush diagnostic messages to the system console",
        default=False,
    )

    @property
    def refresh_interval(self):
        return 1 / self.refresh_fps

    def draw(self, context):
        from ..sculpt import FixBbrushError
        layout = self.layout

        col = layout.column()
        col.use_property_split = True
        col.use_property_decorate = False

        box = col.box()
        box.label(text="Sculpt")
        box.prop(self, "refresh_fps")
        box.prop(self, "depth_ray_size")

        box.prop(self, "enabled_drag_offset_compensation")
        box.prop(self, "drag_offset_compensation")

        sub_col = box.column()
        sub_col.operator(FixBbrushError.bl_idname)

        dbg = col.box()
        dbg.label(text="Debug")
        dbg.prop(self, "debug")
        row = dbg.row(align=True)
        row.operator(BBRUSH_OT_debug_toggle_console.bl_idname)
        row.operator(BBRUSH_OT_debug_print_state.bl_idname)

        self.draw_depth(col)


def register():
    bpy.utils.register_class(BBRUSH_OT_rebuild_keyconfig)
    bpy.utils.register_class(BBRUSH_OT_debug_toggle_console)
    bpy.utils.register_class(BBRUSH_OT_debug_print_state)
    bpy.utils.register_class(Preferences)


def unregister():
    bpy.utils.unregister_class(Preferences)
    bpy.utils.unregister_class(BBRUSH_OT_debug_print_state)
    bpy.utils.unregister_class(BBRUSH_OT_debug_toggle_console)
    bpy.utils.unregister_class(BBRUSH_OT_rebuild_keyconfig)
