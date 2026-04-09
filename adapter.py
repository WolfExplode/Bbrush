import bpy

is_3_6_up_version = bpy.app.version >= (3, 6, 0)
is_4_1_up_version = bpy.app.version >= (4, 1, 0)
is_5_0_up_version = bpy.app.version >= (5, 0, 0)


def sculpt_mesh_has_hidden_geometry(context) -> bool:
    """True if the sculpt mesh has any hidden vertices (partial visibility)."""
    obj = context.sculpt_object
    if not obj or obj.type != "MESH":
        return False
    mesh = obj.data
    if type(mesh).__name__ != "Mesh" or not mesh.vertices:
        return False
    return any(v.hide for v in mesh.vertices)


def _face_set_change_visibility_invoke(context, mode: str) -> set:
    try:
        if context.area and context.region:
            with context.temp_override(
                window=context.window,
                area=context.area,
                region=context.region,
                scene=context.scene,
            ):
                return bpy.ops.sculpt.face_set_change_visibility(
                    "INVOKE_DEFAULT", True, mode=mode
                )
        return bpy.ops.sculpt.face_set_change_visibility(
            "INVOKE_DEFAULT", True, mode=mode
        )
    except RuntimeError:
        return {"CANCELLED"}


def sculpt_face_set_ctrl_shift_click_invoke(context) -> set:
    """ZBrush-style Ctrl+Shift+click on face set.

    Fully visible mesh: Blender Shift+H (TOGGLE) — isolate face set under cursor.
    Already partial hide: Blender H (HIDE_ACTIVE) — hide that face set too.
    """
    if sculpt_mesh_has_hidden_geometry(context):
        return _face_set_change_visibility_invoke(context, "HIDE_ACTIVE")
    return _face_set_change_visibility_invoke(context, "TOGGLE")


def sculpt_invert_hide_face():
    """反转可见面
    放置雕刻操作符
    统一各版本操作符不同带来的bug
    """
    if is_5_0_up_version:
        bpy.ops.paint.visibility_invert()
    elif is_4_1_up_version:
        bpy.ops.paint.visibility_invert()
    elif is_3_6_up_version:
        bpy.ops.sculpt.face_set_invert_visibility()
    else:
        bpy.ops.sculpt.face_set_change_visibility('EXEC_DEFAULT', True, mode='INVERT')


def operator_invoke_confirm(self, event, context, title, message) -> set:
    """4.1版本以上需要多传参数
    更改了显示模式,新版本将显示两个按钮"""
    if bpy.app.version >= (4, 1, 0):
        return context.window_manager.invoke_confirm(
            **{
                "operator": self,
                "event": event,
                'title': title,
                'message': message,
            }
        )
    else:
        return context.window_manager.invoke_confirm(self, event)
