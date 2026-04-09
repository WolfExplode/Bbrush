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


class BrushRuntime:
    left_mouse = Vector((0, 0))  # 偏移䃼尝用

    # SCULPT,SMOOTH,HIDE,MASK,ORIGINAL
    brush_mode = "NONE"


def activate_sculpt_brush_shelf(context, event=None):
    """Build / refresh Bbrush tool shelf while in sculpt mode."""
    if "ORIGINAL" not in brush_shelf:
        UpdateBrushShelf.start_brush_shelf(context)
    UpdateBrushShelf.update_brush_shelf(context, event)
    refresh_ui(context)


def deactivate_sculpt_brush_shelf(context):
    """Restore Blender's default sculpt tool shelf when leaving sculpt mode."""
    if "ORIGINAL" in brush_shelf:
        UpdateBrushShelf.restore_brush_shelf()
    refresh_ui(context)


def unregister_addon_runtime(context):
    """Full teardown when the add-on is disabled (keymaps + shelf)."""
    debug_log("unregister_addon_runtime")
    try:
        BrushKeymap.restore_key(context)
    except Exception as e:
        debug_log("unregister_addon_runtime: restore_key failed:", repr(e))
    try:
        UpdateBrushShelf.restore_brush_shelf()
    except Exception as e:
        debug_log("unregister_addon_runtime: restore_brush_shelf failed:", repr(e))
    refresh_ui(context)


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
