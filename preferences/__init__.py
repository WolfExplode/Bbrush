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
    debug: bpy.props.BoolProperty(name="Debug", default=False)

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

        self.draw_depth(col)


def register():
    bpy.utils.register_class(BBRUSH_OT_rebuild_keyconfig)
    bpy.utils.register_class(Preferences)


def unregister():
    bpy.utils.unregister_class(Preferences)
    bpy.utils.unregister_class(BBRUSH_OT_rebuild_keyconfig)
