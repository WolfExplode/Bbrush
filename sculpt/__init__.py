import bpy
from mathutils import Vector

from . import brush
from .keymap import BrushKeymap
from .left_mouse import LeftMouse
from .right_mouse import RightMouse
from .update_brush_shelf import UpdateBrushShelf
from .view_property import ViewProperty
from ..debug import DEBUG_MODE_TOGGLE
from ..utils import refresh_ui

brush_runtime: "BrushRuntime|None" = None


class BrushRuntime:
    left_mouse = Vector((0, 0))  # 偏移䃼尝用

    # SCULPT,SMOOTH,HIDE,MASK,ORIGINAL
    brush_mode = "NONE"


def start_bbrush(context, event=None):
    """Activate Bbrush while in sculpt mode (no operator)."""
    global brush_runtime

    if DEBUG_MODE_TOGGLE:
        print("start_bbrush")

    if brush_runtime is not None:
        return

    brush_runtime = BrushRuntime()

    UpdateBrushShelf.start_brush_shelf(context)
    UpdateBrushShelf.update_brush_shelf(context, event)
    UpdateBrushShelf.update_brush_shelf(context, event)

    BrushKeymap.start_key(context)
    ViewProperty.start_view_property(context)
    refresh_ui(context)


def exit_bbrush(context, un_reg=False):
    """Tear down Bbrush runtime (leaving sculpt mode or disabling addon)."""
    global brush_runtime

    if brush_runtime is None:
        return

    if DEBUG_MODE_TOGGLE:
        print("exit_bbrush", un_reg)

    brush_runtime = None

    BrushKeymap.restore_key(context)
    UpdateBrushShelf.restore_brush_shelf()
    ViewProperty.restore_view_property(context, un_reg)

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


def refresh_depth_map():
    from ..depth_map.gpu_buffer import clear_gpu_cache
    clear_gpu_cache()


class_list = [
    FixBbrushError,
    LeftMouse,
    RightMouse,
    UpdateBrushShelf,
]

register_class, unregister_class = bpy.utils.register_classes_factory(class_list)


def register():
    brush.register()
    register_class()


def unregister():
    brush.unregister()
    unregister_class()
