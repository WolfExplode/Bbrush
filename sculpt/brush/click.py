import bpy

from ...debug import debug_log
from ...utils import check_mouse_in_model


class BrushClick(bpy.types.Operator):
    bl_idname = "sculpt.bbrush_click"
    bl_label = "Sculpt"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.mode == "SCULPT"

    def invoke(self, context, event):
        from .. import brush_runtime
        is_in_modal = check_mouse_in_model(context, event)

        debug_log(self.bl_idname, is_in_modal, brush_runtime.brush_mode)
        if brush_runtime.brush_mode == "MASK":
            if is_in_modal:
                if event.alt and event.ctrl:
                    bpy.ops.sculpt.mask_filter(filter_type='SHARPEN')
                else:
                    bpy.ops.sculpt.mask_filter(filter_type='SMOOTH')
            else:
                bpy.ops.paint.mask_flood_fill(mode='INVERT')
            return {"FINISHED"}
        elif brush_runtime.brush_mode == "HIDE":
            if is_in_modal:
                bpy.ops.paint.visibility_invert()
            else:
                bpy.ops.paint.hide_show_all(action='SHOW')
            return {"FINISHED"}
        return {"PASS_THROUGH", "FINISHED"}


class BbrushMaskGrowShrinkHotkey(bpy.types.Operator):
    """Ctrl+= / Ctrl+-: grow/shrink mask over empty space, face set over a polygroup."""

    bl_idname = "sculpt.bbrush_mask_grow_shrink"
    bl_label = "Grow/Shrink Mask or Face Set"
    bl_options = {"REGISTER"}

    filter_type: bpy.props.EnumProperty(
        name="Filter",
        items=(
            ("GROW", "Grow", "Grow mask or face set"),
            ("SHRINK", "Shrink", "Shrink mask or face set"),
        ),
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "SCULPT"

    def invoke(self, context, event):
        from ...adapter import sculpt_face_set_grow_shrink, sculpt_face_set_id_under_cursor

        if event is None:
            return {"CANCELLED"}
        if not (event.ctrl and not event.alt and not event.shift):
            return {"PASS_THROUGH"}

        face_set_id = sculpt_face_set_id_under_cursor(context, event)
        if face_set_id is not None:
            sculpt_face_set_grow_shrink(
                context, event, self.filter_type, face_set_id=face_set_id,
            )
            return {"FINISHED"}

        if check_mouse_in_model(context, event):
            return {"PASS_THROUGH"}

        bpy.ops.sculpt.mask_filter(filter_type=self.filter_type)
        return {"FINISHED"}
