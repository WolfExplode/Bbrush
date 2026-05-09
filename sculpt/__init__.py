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

    # Blender 5.1+: Shift holds secondary brush slot; release restores primary (brush.asset_activate).
    shift_secondary_active = False
    shift_primary_saved_ref = None  # snapshot when Shift pressed
    shift_secondary_brush_ref = None  # remembered secondary asset triple (updated if user changes brush while Shift held)


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


def unregister():
    brush.unregister()
    unregister_class()
