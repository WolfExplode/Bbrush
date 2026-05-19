import bpy
from mathutils import Vector

from . import brush
from .keymap import BbrushSyncBrushShelfModifiers, BrushKeymap
from .left_mouse import LeftMouse
from .right_mouse import RightMouse
from .update_brush_shelf import UpdateBrushShelf, brush_shelf
from ..debug import debug_log
from ..utils import refresh_ui

brush_runtime: "BrushRuntime|None" = None


def _first_space_view3d(context):
    """从当前上下文或屏幕中解析一个 SpaceView3D（operator 非 3D 区域调用时 space_data 可能为 None）。"""
    sd = getattr(context, "space_data", None)
    if sd is not None and getattr(sd, "type", None) == "VIEW_3D":
        return sd
    area = getattr(context, "area", None)
    if area is not None and area.type == "VIEW_3D":
        s = area.spaces.active
        if s is not None and getattr(s, "type", None) == "VIEW_3D":
            return s
    screen = getattr(context, "screen", None)
    if screen is None:
        return None
    for a in screen.areas:
        if a.type != "VIEW_3D":
            continue
        s = a.spaces.active
        if s is not None and getattr(s, "type", None) == "VIEW_3D":
            return s
    return None


class BrushRuntime:
    left_mouse = Vector((0, 0))  # 偏移䃼尝用

    # SCULPT,SMOOTH,HIDE,MASK,ORIGINAL
    brush_mode = "NONE"

    # Blender 5.1+: Shift+LMB sculpt uses secondary slot; Shift release restores primary.
    shift_secondary_active = False
    shift_secondary_used_for_sculpt = False  # set when a stroke used secondary this Shift hold
    shift_primary_saved_ref = None  # snapshot when secondary is activated for sculpt
    shift_secondary_brush_ref = None  # remembered secondary asset triple (updated after sculpt + Shift release)


def activate_sculpt_brush_shelf(context, event=None):
    """Build / refresh Bbrush tool shelf while in sculpt mode."""
    if "ORIGINAL" not in brush_shelf:
        UpdateBrushShelf.start_brush_shelf(context)
    UpdateBrushShelf.update_brush_shelf(context, event)

    refresh_ui(context)
    v3d = _first_space_view3d(context)
    if v3d is not None:
        v3d.overlay.show_floor = False

def deactivate_sculpt_brush_shelf(context):
    """Restore Blender's default sculpt tool shelf when leaving sculpt mode."""
    from .shift_secondary_brush import clear_shift_secondary_override

    clear_shift_secondary_override(context)
    if "ORIGINAL" in brush_shelf:
        UpdateBrushShelf.restore_brush_shelf()
    refresh_ui(context)


def unregister_addon_runtime(context):
    """Full teardown when the add-on is disabled (keymaps + shelf)."""
    from .shift_secondary_brush import clear_shift_secondary_override

    debug_log("unregister_addon_runtime")
    clear_shift_secondary_override(context)
    try:
        BrushKeymap.restore_key(context)
    except Exception as e:
        debug_log("unregister_addon_runtime: restore_key failed:", repr(e))
    try:
        UpdateBrushShelf.restore_brush_shelf()
    except Exception as e:
        debug_log("unregister_addon_runtime: restore_brush_shelf failed:", repr(e))
    refresh_ui(context)


def _draw_view3d_mask_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.menu("SCULPT_MT_bbrush_mask_to_vertex_group")
    layout.operator(
        "sculpt.bbrush_mask_from_active_vertex_group",
        text="Mask from Selected Vertex Group",
    )


class SCULPT_MT_bbrush_mask_to_vertex_group(bpy.types.Menu):
    bl_label = "Mask to Vertex Group"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "sculpt.bbrush_mask_to_vertex_group_new",
            text="New Vertex Group",
        )
        layout.operator(
            "sculpt.bbrush_mask_to_vertex_group_active",
            text="Add to Selected Vertex Group",
        )


class _MaskToVertexGroupPoll:
    @classmethod
    def poll(cls, context):
        from ..adapter import sculpt_mesh_has_nonzero_mask

        obj = context.sculpt_object
        return (
            context.mode == "SCULPT"
            and obj is not None
            and obj.type == "MESH"
            and sculpt_mesh_has_nonzero_mask(context)
        )


class MaskToVertexGroupNew(_MaskToVertexGroupPoll, bpy.types.Operator):
    bl_idname = "sculpt.bbrush_mask_to_vertex_group_new"
    bl_label = "Mask to New Vertex Group"
    bl_description = "Create a new vertex group and set its weights from the sculpt mask"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        from ..adapter import sculpt_vertex_group_from_mask

        res = sculpt_vertex_group_from_mask(context, new_group=True)
        if res == {"FINISHED"}:
            vg = context.sculpt_object.vertex_groups.active
            name = vg.name if vg else "Mask"
            self.report({"INFO"}, f"Created vertex group \"{name}\" from mask")
            refresh_ui(context)
            return {"FINISHED"}
        self.report({"WARNING"}, "Could not create vertex group from mask")
        return {"CANCELLED"}


class MaskToVertexGroupActive(_MaskToVertexGroupPoll, bpy.types.Operator):
    bl_idname = "sculpt.bbrush_mask_to_vertex_group_active"
    bl_label = "Mask to Selected Vertex Group"
    bl_description = (
        "Add sculpt mask weights onto the active vertex group "
        "(Object Data Properties > Vertex Groups)"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.sculpt_object
        return super().poll(context) and obj.vertex_groups.active is not None

    def execute(self, context):
        from ..adapter import sculpt_vertex_group_from_mask

        vg = context.sculpt_object.vertex_groups.active
        res = sculpt_vertex_group_from_mask(context, new_group=False)
        if res == {"FINISHED"}:
            self.report({"INFO"}, f"Added mask weights to vertex group \"{vg.name}\"")
            refresh_ui(context)
            return {"FINISHED"}
        self.report({"WARNING"}, "Could not add mask to vertex group")
        return {"CANCELLED"}


class MaskFromActiveVertexGroup(bpy.types.Operator):
    bl_idname = "sculpt.bbrush_mask_from_active_vertex_group"
    bl_label = "Mask from Selected Vertex Group"
    bl_description = (
        "Set the sculpt mask from the active vertex group "
        "(Object Data Properties > Vertex Groups)"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.sculpt_object
        return (
            context.mode == "SCULPT"
            and obj is not None
            and obj.type == "MESH"
            and obj.vertex_groups.active is not None
        )

    def execute(self, context):
        from ..adapter import sculpt_mask_from_active_vertex_group

        vg = context.sculpt_object.vertex_groups.active
        res = sculpt_mask_from_active_vertex_group(context)
        if res == {"FINISHED"}:
            self.report({"INFO"}, f"Mask set from vertex group \"{vg.name}\"")
            refresh_ui(context)
            return {"FINISHED"}
        self.report({"WARNING"}, "Could not set mask from vertex group")
        return {"CANCELLED"}


class FaceSetsCreateZbrushCtrlW(bpy.types.Operator):
    bl_idname = "sculpt.bbrush_face_sets_create_zbrush"
    bl_label = "Face Set from Mask or Visible"
    bl_description = (
        "ZBrush Ctrl+W: if masked, Face Set from Masked then clear mask; "
        "if not masked, Face Set from Visible (e.g. after partial hide)"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.mode == "SCULPT" and context.sculpt_object is not None

    def execute(self, context):
        from ..adapter import sculpt_face_sets_create_zbrush_ctrl_w

        res = sculpt_face_sets_create_zbrush_ctrl_w(context)
        return res if res == {"FINISHED"} else {"CANCELLED"}


class FixBbrushError(bpy.types.Operator):
    bl_idname = "sculpt.bbrush_fix"
    bl_label = "Reset BBrush Keymap & Tool Shelf"
    bl_description = (
        "Re-register this add-on's keymaps (left/right mouse sculpt handlers and "
        "Ctrl/Shift/Alt tool-shelf sync). Restore Blender's default sculpt tool list "
        "if needed, then rebuild BBrush's shelf while in sculpt mode. "
        "Use after odd behavior (e.g. file load or add-on reload), not for everyday sculpting."
    )
    bl_options = {"REGISTER"}

    def execute(self, context):
        BrushKeymap.unregister_addon_keymaps()
        BrushKeymap.register_addon_keymaps(context)
        if "ORIGINAL" in brush_shelf:
            UpdateBrushShelf.restore_brush_shelf()
        if context.mode == "SCULPT":
            activate_sculpt_brush_shelf(context, None)
        refresh_ui(context)
        self.report(
            {"INFO"},
            "BBrush keymaps and sculpt tool shelf were reset.",
        )
        return {"FINISHED"}


class_list = [
    SCULPT_MT_bbrush_mask_to_vertex_group,
    MaskToVertexGroupNew,
    MaskToVertexGroupActive,
    MaskFromActiveVertexGroup,
    FaceSetsCreateZbrushCtrlW,
    FixBbrushError,
    BbrushSyncBrushShelfModifiers,
    LeftMouse,
    RightMouse,
]

register_class, unregister_class = bpy.utils.register_classes_factory(class_list)


def register():
    global brush_runtime
    brush_runtime = BrushRuntime()
    brush.register()
    register_class()
    bpy.types.VIEW3D_MT_mask.append(_draw_view3d_mask_menu)


def unregister():
    bpy.types.VIEW3D_MT_mask.remove(_draw_view3d_mask_menu)
    brush.unregister()
    unregister_class()
