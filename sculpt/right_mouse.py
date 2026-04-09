import bpy

from ..utils import check_mouse_in_depth_map_area, get_pref
from ..utils.manually_manage_events import ManuallyManageEvents


class RightMouse(bpy.types.Operator, ManuallyManageEvents):
    bl_idname = "sculpt.bbrush_right_mouse"
    bl_label = "Sculpt"
    bl_description = "RightMouse"

    def invoke(self, context, event):

        from . import UpdateBrushShelf
        UpdateBrushShelf.update_brush_shelf(context, event)

        if check_mouse_in_depth_map_area(event):
            bpy.ops.sculpt.bbrush_depth_move("INVOKE_DEFAULT")
            return {"FINISHED"}
        try:
            if getattr(get_pref(), "debug", False):
                print(self.bl_idname)
        except Exception:
            ...

        context.window_manager.modal_handler_add(self)
        self.start_manually_manage_events(event)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        from . import UpdateBrushShelf
        UpdateBrushShelf.update_brush_shelf(context, event)

        is_moving = self.check_is_moving(event)
        is_release = event.value == "RELEASE"
        if is_release:
            try:
                bpy.ops.wm.call_panel("INVOKE_DEFAULT", name="VIEW3D_PT_sculpt_context_menu")
            finally:  # 反直觉写法
                return {"FINISHED"}
        elif is_moving:  # 不能使用PASSTHROUGH,需要手动指定事件
            # Removed features:
            # - RMB drag rotates view
            # - Ctrl+RMB drag zooms view
            # Let Blender handle any default behavior instead.
            return {"PASS_THROUGH"}
        return {"RUNNING_MODAL"}
