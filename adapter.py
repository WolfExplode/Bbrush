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


def _attribute_has_nonzero_mask_values(attr, count: int) -> bool:
    """True if any mask element is non-zero (FLOAT or BOOLEAN sculpt_mask)."""
    if count <= 0:
        return False
    data_type = getattr(attr, "data_type", "FLOAT")

    if data_type == "BOOLEAN":
        try:
            import numpy as np

            buf = np.zeros(count, dtype=np.bool_)
            attr.data.foreach_get("value", buf)
            return bool(buf.any())
        except Exception:
            for i in range(count):
                try:
                    if bool(attr.data[i].value):
                        return True
                except (AttributeError, TypeError, ValueError, IndexError):
                    continue
            return False

    try:
        import numpy as np

        buf = np.zeros(count, dtype=np.float32)
        attr.data.foreach_get("value", buf)
        if float(np.max(np.abs(buf))) > 1e-6:
            return True
    except Exception:
        pass
    for i in range(count):
        try:
            if abs(float(attr.data[i].value)) > 1e-6:
                return True
        except (AttributeError, TypeError, ValueError, IndexError):
            continue
    return False


def sculpt_mesh_has_nonzero_mask(context) -> bool:
    """True if sculpt_mask has any non-zero weight (anything masked)."""
    obj = context.sculpt_object
    if not obj or obj.type != "MESH":
        return False
    mesh = obj.data
    if type(mesh).__name__ != "Mesh":
        return False
    try:
        context.view_layer.update()
    except Exception:
        pass

    attr = _get_sculpt_mask_attribute(mesh)
    if attr is None:
        return False
    try:
        n = len(attr.data)
    except Exception:
        n = len(mesh.vertices)
    return _attribute_has_nonzero_mask_values(attr, n)


def _get_sculpt_mask_attribute(mesh):
    return mesh.attributes.get(".sculpt_mask") or mesh.attributes.get("sculpt_mask")


def _read_sculpt_mask_values(mesh, vert_count: int):
    """Read per-vertex sculpt mask weights as float32 in [0, 1], or None if no mask attribute."""
    mask_attr = _get_sculpt_mask_attribute(mesh)
    if mask_attr is None:
        return None

    data_type = getattr(mask_attr, "data_type", "FLOAT")
    if data_type == "BOOLEAN":
        try:
            import numpy as np

            buf = np.zeros(vert_count, dtype=np.bool_)
            mask_attr.data.foreach_get("value", buf)
            return buf.astype(np.float32)
        except Exception:
            values = []
            for i in range(vert_count):
                try:
                    values.append(1.0 if bool(mask_attr.data[i].value) else 0.0)
                except (AttributeError, TypeError, ValueError, IndexError):
                    values.append(0.0)
            return values

    try:
        import numpy as np

        buf = np.zeros(vert_count, dtype=np.float32)
        mask_attr.data.foreach_get("value", buf)
        np.clip(buf, 0.0, 1.0, out=buf)
        return buf
    except Exception:
        values = []
        for i in range(vert_count):
            try:
                values.append(min(1.0, max(0.0, float(mask_attr.data[i].value))))
            except (AttributeError, TypeError, ValueError, IndexError):
                values.append(0.0)
        return values


def _ensure_sculpt_mask_attribute(mesh):
    """Return the mesh sculpt-mask attribute, creating a FLOAT point attribute if needed."""
    mask_attr = _get_sculpt_mask_attribute(mesh)
    if mask_attr is not None:
        return mask_attr
    for name in (".sculpt_mask", "sculpt_mask"):
        try:
            return mesh.attributes.new(name, "FLOAT", "POINT")
        except RuntimeError:
            continue
    return None


def sculpt_mask_from_active_vertex_group(context) -> set:
    """Set sculpt mask weights from the object's active vertex group."""
    obj = context.sculpt_object
    if not obj or obj.type != "MESH":
        return {"CANCELLED"}

    vg = obj.vertex_groups.active
    if vg is None:
        return {"CANCELLED"}

    mesh = obj.data
    if type(mesh).__name__ != "Mesh":
        return {"CANCELLED"}

    vert_count = len(mesh.vertices)
    if vert_count == 0:
        return {"CANCELLED"}

    try:
        context.view_layer.update()
    except Exception:
        pass

    mask_attr = _ensure_sculpt_mask_attribute(mesh)
    if mask_attr is None:
        return {"CANCELLED"}

    vg_index = vg.index
    data_type = getattr(mask_attr, "data_type", "FLOAT")

    if data_type == "BOOLEAN":
        values = []
        for i in range(vert_count):
            try:
                values.append(vg.weight(i) > 0.0)
            except RuntimeError:
                values.append(False)
        try:
            import numpy as np

            mask_attr.data.foreach_set("value", np.array(values, dtype=np.bool_))
        except Exception:
            for i, val in enumerate(values):
                mask_attr.data[i].value = val
    else:
        try:
            import numpy as np

            weights = np.zeros(vert_count, dtype=np.float32)
            for i in range(vert_count):
                try:
                    weights[i] = vg.weight(i)
                except RuntimeError:
                    pass
            np.clip(weights, 0.0, 1.0, out=weights)
            mask_attr.data.foreach_set("value", weights)
        except Exception:
            for i in range(vert_count):
                try:
                    mask_attr.data[i].value = min(1.0, max(0.0, float(vg.weight(i))))
                except RuntimeError:
                    mask_attr.data[i].value = 0.0

    mesh.update_tag()
    return {"FINISHED"}


def _vertex_group_assign_mask_weights(vg, weights, *, mode: str, vert_count: int):
    """Assign per-vertex mask weights to a vertex group (mode: REPLACE or ADD)."""
    threshold = 1e-6
    try:
        import numpy as np

        if isinstance(weights, np.ndarray):
            if mode == "ADD":
                for i in range(vert_count):
                    w = float(weights[i])
                    if w > threshold:
                        vg.add([i], w, mode)
            else:
                for i in range(vert_count):
                    vg.add([i], float(weights[i]), mode)
            return
    except ImportError:
        pass

    if mode == "ADD":
        for i in range(vert_count):
            w = float(weights[i])
            if w > threshold:
                vg.add([i], w, mode)
    else:
        for i in range(vert_count):
            vg.add([i], float(weights[i]), mode)


def sculpt_vertex_group_from_mask(context, *, new_group: bool) -> set:
    """Write sculpt mask into a new vertex group (REPLACE) or add into the active group."""
    obj = context.sculpt_object
    if not obj or obj.type != "MESH":
        return {"CANCELLED"}

    mesh = obj.data
    if type(mesh).__name__ != "Mesh":
        return {"CANCELLED"}

    vert_count = len(mesh.vertices)
    if vert_count == 0:
        return {"CANCELLED"}

    try:
        context.view_layer.update()
    except Exception:
        pass

    weights = _read_sculpt_mask_values(mesh, vert_count)
    if weights is None:
        return {"CANCELLED"}

    if new_group:
        vg = obj.vertex_groups.new(name="Mask")
        obj.vertex_groups.active_index = vg.index
        _vertex_group_assign_mask_weights(vg, weights, mode="REPLACE", vert_count=vert_count)
    else:
        vg = obj.vertex_groups.active
        if vg is None:
            return {"CANCELLED"}
        _vertex_group_assign_mask_weights(vg, weights, mode="ADD", vert_count=vert_count)

    mesh.update_tag()
    return {"FINISHED"}


def sculpt_face_sets_create_zbrush_ctrl_w(context) -> set:
    """ZBrush Ctrl+W: if masked → Face Set from Masked, then clear mask; else Face Set from Visible."""
    try:
        if sculpt_mesh_has_nonzero_mask(context):
            res = bpy.ops.sculpt.face_sets_create("EXEC_DEFAULT", True, mode="MASKED")
            if res != {"FINISHED"}:
                return res
            # Second Ctrl+W should see no mask → VISIBLE path (ZBrush parity).
            return bpy.ops.paint.mask_flood_fill(
                "EXEC_DEFAULT", True, mode="VALUE", value=0.0
            )
        return bpy.ops.sculpt.face_sets_create("EXEC_DEFAULT", True, mode="VISIBLE")
    except RuntimeError:
        return {"CANCELLED"}


def _get_sculpt_face_set_attribute(mesh):
    return mesh.attributes.get(".sculpt_face_set") or mesh.attributes.get("sculpt_face_set")


def _view3d_context_from_event(context, event):
    """(area, region, space, mouse_region) for raycast / face_set_edit, or Nones."""
    if event is None:
        return None, None, None, None

    area = getattr(context, "area", None)
    region = getattr(context, "region", None)
    region_data = getattr(context, "region_data", None)
    if (
        area is not None
        and area.type == "VIEW_3D"
        and region is not None
        and region.type == "WINDOW"
        and region_data is not None
    ):
        space = area.spaces.active
        if space is not None and space.type == "VIEW_3D":
            return area, region, space, (event.mouse_region_x, event.mouse_region_y)

    from .utils import find_mouse_in_area

    area = find_mouse_in_area(context, event)
    if area is None or area.type != "VIEW_3D":
        return None, None, None, None

    region = None
    for reg in area.regions:
        if reg.type == "WINDOW":
            region = reg
            break
    if region is None:
        return None, None, None, None

    space = area.spaces.active
    if space is None or space.type != "VIEW_3D":
        return None, None, None, None

    # Screen/window coords → region-local (only when context.region is not already set).
    mouse = (
        event.mouse_x - area.x - region.x,
        event.mouse_y - area.y - region.y,
    )
    return area, region, space, mouse


def _view3d_override_for_event(context, event):
    """Build temp_override dict + mouse for sculpt ops in the 3D view under the cursor."""
    area, region, space, mouse = _view3d_context_from_event(context, event)
    if area is None:
        return None, None

    obj = getattr(context, "sculpt_object", None)
    override = {
        "window": context.window,
        "screen": context.screen,
        "area": area,
        "region": region,
        "space_data": space,
        "region_data": space.region_3d,
        "scene": context.scene,
        "view_layer": context.view_layer,
    }
    if obj is not None:
        override["active_object"] = obj
        override["object"] = obj
    return override, mouse


def _read_face_set_id_at_poly(mesh, attr, poly_index: int) -> int | None:
    domain = getattr(attr, "domain", "FACE")
    try:
        if domain == "FACE":
            if poly_index < 0 or poly_index >= len(attr.data):
                return None
            return int(attr.data[poly_index].value)
        if domain == "POINT":
            if poly_index < 0 or poly_index >= len(mesh.polygons):
                return None
            vert_index = mesh.polygons[poly_index].vertices[0]
            if vert_index >= len(attr.data):
                return None
            return int(attr.data[vert_index].value)
    except (AttributeError, TypeError, ValueError, IndexError):
        pass
    return None


def sculpt_face_set_pick_under_cursor(context, event):
    """Ray hit under cursor in the 3D view: (poly_index, face_set_id) or (None, None)."""
    from .utils import object_ray_cast

    area, _region, _space, mouse = _view3d_context_from_event(context, event)
    if area is None or mouse is None:
        return None, None

    obj = getattr(context, "sculpt_object", None)
    if obj is None or obj.type != "MESH":
        return None, None

    override, _ = _view3d_override_for_event(context, event)
    if override is None:
        return None, None

    with context.temp_override(**override):
        depsgraph = context.evaluated_depsgraph_get()
        object_eval = obj.evaluated_get(depsgraph)
        result, _location, _normal, index = object_ray_cast(object_eval, context, mouse)

    if not result or index is None or index < 0:
        return None, None

    mesh = object_eval.data
    attr = _get_sculpt_face_set_attribute(mesh) or _get_sculpt_face_set_attribute(obj.data)
    if attr is None:
        return index, None

    return index, _read_face_set_id_at_poly(mesh, attr, index)


def sculpt_face_set_id_under_cursor(context, event) -> int | None:
    """Face set ID under the cursor, or None if not over a painted face set (id > 0)."""
    _poly_index, face_set_id = sculpt_face_set_pick_under_cursor(context, event)
    if _poly_index is None or face_set_id is None or face_set_id <= 0:
        return None
    return face_set_id


def sculpt_face_set_grow_shrink(context, event, mode: str, *, face_set_id: int | None = None) -> set:
    """Grow or shrink the face set under the cursor (mode: GROW or SHRINK)."""
    override, _mouse = _view3d_override_for_event(context, event)
    if override is None:
        return {"CANCELLED"}

    try:
        with context.temp_override(**override):
            res = bpy.ops.sculpt.face_set_edit("INVOKE_DEFAULT", mode=mode)
            if "FINISHED" in res:
                return res
            if face_set_id is not None:
                return bpy.ops.sculpt.face_set_edit(
                    "EXEC_DEFAULT",
                    True,
                    active_face_set=face_set_id,
                    mode=mode,
                )
            return res
    except RuntimeError:
        return {"CANCELLED"}


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
