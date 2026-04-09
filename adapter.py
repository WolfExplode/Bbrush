import bpy

from .utils import object_ray_cast
from .debug import debug_log

is_3_6_up_version = bpy.app.version >= (3, 6, 0)
is_4_1_up_version = bpy.app.version >= (4, 1, 0)
is_5_0_up_version = bpy.app.version >= (5, 0, 0)


def sculpt_face_set_id_under_cursor(context, event):
    """Integer face-set id for the face under the cursor, or None.

    Important: we try to resolve the id on the same mesh we later modify (`obj.data`)
    to avoid mismatches between evaluated mesh topology/attributes and the sculpt mesh.
    """
    obj = context.sculpt_object
    if not obj or obj.type != "MESH":
        debug_log("faceset_pick:no_obj", bool(obj), getattr(obj, "type", None))
        return None
    if context.region is None or context.region_data is None:
        debug_log("faceset_pick:no_region", bool(context.region), bool(context.region_data))
        return None

    depsgraph = context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.data
    if type(mesh_eval).__name__ != "Mesh" or not mesh_eval.polygons:
        debug_log("faceset_pick:no_eval_mesh", type(mesh_eval).__name__)
        return None

    mouse = (event.mouse_region_x, event.mouse_region_y)
    # Prefer raycast on the *base* sculpt mesh so face index aligns with sculpt_face_set.
    hit, _loc, _normal, face_i = object_ray_cast(obj, context, mouse)
    if not hit or face_i is None or face_i < 0 or face_i >= len(mesh_eval.polygons):
        debug_log(
            "faceset_pick:ray_miss_or_bad_index",
            hit,
            face_i,
            "eval_polys",
            len(getattr(mesh_eval, "polygons", ())),
        )
        return None

    try:
        mesh = obj.data
        debug_log(
            "faceset_pick:ray_hit",
            "face_i",
            face_i,
            "base_polys",
            len(getattr(mesh, "polygons", ())),
            "eval_polys",
            len(getattr(mesh_eval, "polygons", ())),
        )

        # Prefer picking from the sculpt mesh if possible.
        attr = getattr(mesh, "attributes", None) and mesh.attributes.get("sculpt_face_set")
        debug_log(
            "faceset_pick:base_attr",
            bool(attr),
            getattr(attr, "domain", None),
            getattr(attr, "data_type", None),
        )
        if attr is not None and attr.domain == "FACE" and face_i < len(mesh.polygons):
            fs_id = int(attr.data[face_i].value)
            # Sanity: ensure the id actually exists on this mesh.
            for p in mesh.polygons:
                if int(attr.data[p.index].value) == fs_id:
                    debug_log("faceset_pick:base_fs_id", fs_id)
                    return fs_id
            debug_log("faceset_pick:base_fs_id_not_found", fs_id)

        # Fallback: pick from evaluated mesh attributes.
        attr_eval = mesh_eval.attributes.get("sculpt_face_set")
        debug_log(
            "faceset_pick:eval_attr",
            bool(attr_eval),
            getattr(attr_eval, "domain", None) if attr_eval else None,
            getattr(attr_eval, "data_type", None) if attr_eval else None,
        )
        if attr_eval is None or attr_eval.domain != "FACE":
            return None
        fs_id = int(attr_eval.data[face_i].value)
        debug_log("faceset_pick:eval_fs_id", fs_id)
        return fs_id
    except (AttributeError, TypeError, ValueError, IndexError):
        debug_log("faceset_pick:exception", "face_i", face_i)
        return None


def _isolate_face_set_vertex_hide(mesh, target_fs: int) -> bool:
    """Hide verts that only belong to faces outside target_fs (approx. face-set isolate)."""
    attr = mesh.attributes.get("sculpt_face_set")
    if attr is None or attr.domain != "FACE":
        return False

    n_v = len(mesh.vertices)
    if n_v == 0:
        return False

    touch_target = [False] * n_v
    touch_other = [False] * n_v
    found_target = False
    for p in mesh.polygons:
        try:
            fs = int(attr.data[p.index].value)
        except (AttributeError, TypeError, ValueError, IndexError):
            return False
        for vi in p.vertices:
            if fs == target_fs:
                touch_target[vi] = True
                found_target = True
            else:
                touch_other[vi] = True

    # If the requested face set doesn't exist on this mesh, don't hide everything.
    if not found_target:
        return False

    changed = False
    for vi in range(n_v):
        hide = touch_other[vi] and not touch_target[vi]
        vert = mesh.vertices[vi]
        if bool(vert.hide) != hide:
            vert.hide = hide
            changed = True
    if changed:
        mesh.update_tag()
    return changed


def sculpt_face_set_try_isolate_under_cursor(context, event) -> bool:
    """Hide every face set except the one hit by the cursor (ray + mesh attribute).

    Uses ``active_face_set`` when the Blender build exposes it; otherwise
    ``INVOKE_DEFAULT`` (uses WM mouse) or a vertex-hide fallback from the resolved id.
    """
    obj = context.sculpt_object
    if not obj:
        return False

    fs_id = sculpt_face_set_id_under_cursor(context, event)
    if fs_id is None:
        debug_log("faceset_isolate:no_fs_id")
        return False

    try:
        try:
            res = bpy.ops.sculpt.face_set_change_visibility(
                "EXEC_DEFAULT", True, mode="TOGGLE", active_face_set=fs_id
            )
            if res == {"FINISHED"}:
                debug_log("faceset_isolate:op_exec_active_ok", fs_id)
                return True
            debug_log("faceset_isolate:op_exec_active_not_finished", res, fs_id)
        except TypeError:
            debug_log("faceset_isolate:op_no_active_param")
            pass  # active_face_set not in this Blender version
        except Exception as e:
            debug_log("faceset_isolate:op_exec_active_exception", repr(e), fs_id)

        # Apply visibility from the picked id when EXEC cannot take active_face_set.
        mesh = obj.data
        if type(mesh).__name__ == "Mesh" and mesh.polygons:
            if _isolate_face_set_vertex_hide(mesh, fs_id):
                debug_log("faceset_isolate:vertex_hide_ok", fs_id)
                return True
            debug_log("faceset_isolate:vertex_hide_no_change", fs_id)

        res = bpy.ops.sculpt.face_set_change_visibility(
            "INVOKE_DEFAULT", True, mode="TOGGLE"
        )
        debug_log("faceset_isolate:op_invoke_toggle", res, fs_id)
        return res == {"FINISHED"}
    except (RuntimeError, TypeError, ReferenceError):
        debug_log("faceset_isolate:exception", fs_id)
        return False


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
