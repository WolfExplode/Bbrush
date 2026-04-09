import bpy

from ..debug import debug_log
from ..utils import check_mouse_in_depth_map_area, refresh_ui
from ..utils.manually_manage_events import ManuallyManageEvents

# Match Blender sculpt / unified paint size limits (px); clamp so we never write invalid RNA values.
_MASK_BRUSH_SIZE_MIN = 1
_MASK_BRUSH_SIZE_MAX = 10000


def _clamp_sculpt_brush_size(value: int) -> int:
    return max(_MASK_BRUSH_SIZE_MIN, min(int(value), _MASK_BRUSH_SIZE_MAX))


def _sculpt_unified_paint_settings(context):
    """Blender 5+: on Paint (tool_settings.sculpt); older: on ToolSettings."""
    ts = context.tool_settings
    sculpt = getattr(ts, "sculpt", None)
    if sculpt is not None:
        ups = getattr(sculpt, "unified_paint_settings", None)
        if ups is not None:
            return ups
    return getattr(ts, "unified_paint_settings", None)


def _apply_sculpt_brush_pixel_size(context, size: int) -> None:
    s = _clamp_sculpt_brush_size(size)
    ts = context.tool_settings
    sculpt = ts.sculpt
    br = sculpt.brush if sculpt else None
    if br is not None:
        br.size = s
    ups = _sculpt_unified_paint_settings(context)
    if ups is not None and getattr(ups, "use_unified_size", False):
        ups.size = s


def _effective_sculpt_brush_pixel_size(context) -> "int|None":
    ts = context.tool_settings
    sculpt = ts.sculpt
    br = sculpt.brush if sculpt else None
    if br is None:
        return None
    ups = _sculpt_unified_paint_settings(context)
    if ups is not None and getattr(ups, "use_unified_size", False):
        return int(ups.size)
    return int(br.size)


class RightMouse(bpy.types.Operator, ManuallyManageEvents):
    bl_idname = "sculpt.bbrush_right_mouse"
    bl_label = "Sculpt"
    bl_description = "RightMouse"

    @classmethod
    def poll(cls, context):
        return context.mode == "SCULPT"

    def invoke(self, context, event):

        from . import UpdateBrushShelf
        UpdateBrushShelf.update_brush_shelf(context, event)

        if check_mouse_in_depth_map_area(event):
            bpy.ops.sculpt.bbrush_depth_move("INVOKE_DEFAULT")
            return {"FINISHED"}
        debug_log(self.bl_idname)

        self._rmb_size_at_press = _effective_sculpt_brush_pixel_size(context)
        self._rmb_resizing = False

        context.window_manager.modal_handler_add(self)
        self.start_manually_manage_events(event)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        from . import UpdateBrushShelf
        from . import brush_runtime

        UpdateBrushShelf.update_brush_shelf(context, event)

        is_moving = self.check_is_moving(event)
        is_release = event.value == "RELEASE" and event.type == "RIGHTMOUSE"

        if getattr(self, "_rmb_resizing", False):
            if is_release:
                self._rmb_resizing = False
                return {"FINISHED"}
            if self._rmb_size_at_press is not None:
                delta_x = event.mouse_x - self.start_mouse.x
                _apply_sculpt_brush_pixel_size(
                    context, self._rmb_size_at_press + delta_x,
                )
                refresh_ui(context)
            return {"RUNNING_MODAL"}

        if is_release:
            try:
                bpy.ops.wm.call_panel("INVOKE_DEFAULT", name="VIEW3D_PT_sculpt_context_menu")
            finally:  # 反直觉写法
                return {"FINISHED"}

        if (
            brush_runtime.brush_mode == "MASK"
            and event.ctrl
            and is_moving
        ):
            ts = context.tool_settings.sculpt
            br = ts.brush if ts else None
            if br is not None and self._rmb_size_at_press is not None:
                self._rmb_resizing = True
                delta_x = event.mouse_x - self.start_mouse.x
                _apply_sculpt_brush_pixel_size(
                    context, self._rmb_size_at_press + delta_x,
                )
                refresh_ui(context)
                return {"RUNNING_MODAL"}

        if is_moving:  # 不能使用PASSTHROUGH,需要手动指定事件
            # Removed features:
            # - RMB drag rotates view
            # - Ctrl+RMB drag zooms view (replaced by mask brush resize when mask shelf is active)
            return {"PASS_THROUGH"}
        return {"RUNNING_MODAL"}
