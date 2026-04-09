import bpy
from mathutils import Vector

from . import brush
from .keymap import BbrushSyncBrushShelfModifiers, BrushKeymap
from .left_mouse import LeftMouse
from .right_mouse import RightMouse
from .update_brush_shelf import UpdateBrushShelf
from ..debug import debug_log
from ..utils import refresh_ui

brush_runtime: "BrushRuntime|None" = None


class BrushRuntime:
    left_mouse = Vector((0, 0))  # 偏移䃼尝用

    # SCULPT,SMOOTH,HIDE,MASK,ORIGINAL
    brush_mode = "NONE"


def start_bbrush(context, event=None):
    """Activate Bbrush while in sculpt mode (no operator)."""
    global brush_runtime

    debug_log("start_bbrush")

    if brush_runtime is not None:
        return

    brush_runtime = BrushRuntime()

    UpdateBrushShelf.start_brush_shelf(context)
    # Historically update_brush_shelf was called twice in a row here. Removed duplicate;
    # if tool shelf / active tool ever mis-sync on Bbrush start, revisit—may have been
    # compensating for Blender tool-system timing or a one-frame stale state.
    UpdateBrushShelf.update_brush_shelf(context, event)

    BrushKeymap.start_key(context)
    refresh_ui(context)


def exit_bbrush(context, un_reg=False):
    """Tear down Bbrush runtime (leaving sculpt mode or disabling addon)."""
    global brush_runtime

    if brush_runtime is None:
        return

    debug_log("exit_bbrush", un_reg)

    brush_runtime = None

    BrushKeymap.restore_key(context)
    UpdateBrushShelf.restore_brush_shelf()

    refresh_ui(context)


class FixBbrushError(bpy.types.Operator):
    bl_idname = "sculpt.bbrush_fix"
    bl_label = "BBrush fix"
    bl_description = "Fix Bbrush error"
    bl_options = {"REGISTER"}

    def execute(self, context):
        exit_bbrush(context)
        if context.mode == "SCULPT":
            start_bbrush(context, None)
        return {"FINISHED"}

    @classmethod
    def draw_button(cls, layout):
        layout.operator(cls.bl_idname, text="", icon="EVENT_F")


class_list = [
    FixBbrushError,
    BbrushSyncBrushShelfModifiers,
    LeftMouse,
    RightMouse,
]

register_class, unregister_class = bpy.utils.register_classes_factory(class_list)


def register():
    brush.register()
    register_class()


def unregister():
    brush.unregister()
    unregister_class()
