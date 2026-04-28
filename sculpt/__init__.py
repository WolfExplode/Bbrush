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
    # Default to mouse until tablet evidence appears in events.
    input_source = "MOUSE"
    # Track active brush name so we can apply per-brush defaults on brush switch only.
    active_brush_name = ""


def activate_sculpt_brush_shelf(context, event=None):
    """Build / refresh Bbrush tool shelf while in sculpt mode."""
    global brush_runtime
    if "ORIGINAL" not in brush_shelf:
        UpdateBrushShelf.start_brush_shelf(context)
    UpdateBrushShelf.update_brush_shelf(context, event)

    # Initialize sculpt-session defaults on mode entry so first Shift-smooth stroke
    # uses the intended per-input smooth strength (instead of Blender's previous value).
    if brush_runtime is not None:
        source = brush_runtime.input_source if brush_runtime.input_source in {"MOUSE", "TABLET"} else "MOUSE"
        if brush_runtime.input_source != source:
            brush_runtime.input_source = source
        _apply_smooth_default_strength_for_source(context, source, reason="sculpt_enter_init")

    refresh_ui(context)


def deactivate_sculpt_brush_shelf(context):
    """Restore Blender's default sculpt tool shelf when leaving sculpt mode."""
    if "ORIGINAL" in brush_shelf:
        UpdateBrushShelf.restore_brush_shelf()
    refresh_ui(context)


def _detect_input_source_from_event(event) -> str:
    """Best-effort event classifier tuned for pen tablets (Huion/Windows Ink)."""
    pressure = float(getattr(event, "pressure", 1.0))
    is_tablet = bool(getattr(event, "is_tablet", False))
    tilt = getattr(event, "tilt", (0.0, 0.0))
    tilt_x = float(tilt[0]) if isinstance(tilt, (tuple, list)) and len(tilt) > 0 else 0.0
    tilt_y = float(tilt[1]) if isinstance(tilt, (tuple, list)) and len(tilt) > 1 else 0.0

    # Tablet-like signals:
    # - explicit tablet flag
    # - pressure deviates from default mouse-like value
    # - tilt data present
    if is_tablet or abs(pressure - 1.0) > 0.001 or abs(tilt_x) > 0.001 or abs(tilt_y) > 0.001:
        return "TABLET"
    return "MOUSE"


def _apply_smooth_default_strength_for_source(context, source: str, reason: str = "source_switch"):
    """Apply Smooth brush default strength for the inferred input source."""
    target_smooth_strength = 0.1 if source == "MOUSE" else 0.7

    updated_count = 0
    active_updated = False

    # Update currently active sculpt brush if it is Smooth.
    try:
        sculpt_settings = getattr(getattr(context, "tool_settings", None), "sculpt", None)
        active_brush = getattr(sculpt_settings, "brush", None) if sculpt_settings else None
        if active_brush is not None and getattr(active_brush, "name", "") == "Smooth" and hasattr(active_brush, "strength"):
            active_brush.strength = target_smooth_strength
            active_updated = True
    except Exception as e:
        debug_log("input_profile active smooth apply failed:", repr(e))

    # Update every datablock named Smooth (some files contain duplicates).
    for brush_data in bpy.data.brushes:
        if getattr(brush_data, "name", "") != "Smooth":
            continue
        if not hasattr(brush_data, "strength"):
            continue
        try:
            brush_data.strength = target_smooth_strength
            updated_count += 1
        except Exception as e:
            debug_log("input_profile brush data smooth apply failed:", repr(e))

    debug_log(
        "input_profile_applied",
        source,
        "smooth_strength=", round(float(target_smooth_strength), 4),
        "active_updated=", active_updated,
        "smooth_brushes_updated=", updated_count,
        "reason=", reason,
    )


def _apply_draw_default_strength_for_source(context, source: str, reason: str = "brush_switch"):
    """Apply Draw brush default strength when using mouse."""
    if source != "MOUSE":
        return

    try:
        sculpt_settings = getattr(getattr(context, "tool_settings", None), "sculpt", None)
        active_brush = getattr(sculpt_settings, "brush", None) if sculpt_settings else None
        if active_brush is None or getattr(active_brush, "name", "") != "Draw":
            return
        if hasattr(active_brush, "strength"):
            active_brush.strength = 0.15
            debug_log("draw_profile_applied", "strength=", 0.15, "reason=", reason)
    except Exception as e:
        debug_log("draw_profile apply failed:", repr(e))


def ensure_shift_smooth_default_strength(context):
    """Before Shift-smoothing from any brush, enforce Smooth default by input source."""
    global brush_runtime
    if brush_runtime is None:
        return
    source = brush_runtime.input_source
    if source not in {"MOUSE", "TABLET"}:
        source = "MOUSE"
        brush_runtime.input_source = source
    _apply_smooth_default_strength_for_source(context, source, reason="shift_smooth")


def handle_input_source_event(context, event):
    """Detect current input source and update runtime + unified brush settings."""
    global brush_runtime
    if brush_runtime is None or context.mode != "SCULPT":
        return

    source = _detect_input_source_from_event(event)

    debug_log(
        "input_event",
        "src=", source,
        "type=", getattr(event, "type", None),
        "value=", getattr(event, "value", None),
        "is_tablet=", getattr(event, "is_tablet", None),
        "pressure=", getattr(event, "pressure", None),
        "tilt=", getattr(event, "tilt", None),
    )

    source_changed = brush_runtime.input_source != source
    if source_changed:
        prev = brush_runtime.input_source
        brush_runtime.input_source = source
        debug_log("input_source_switch", prev, "->", source)

    # Apply draw default when the active brush switches to Draw while using mouse.
    active_brush_name = ""
    try:
        sculpt_settings = getattr(getattr(context, "tool_settings", None), "sculpt", None)
        active_brush = getattr(sculpt_settings, "brush", None) if sculpt_settings else None
        active_brush_name = getattr(active_brush, "name", "") if active_brush else ""
    except Exception:
        active_brush_name = ""

    brush_changed = brush_runtime.active_brush_name != active_brush_name
    if brush_changed:
        prev_brush = brush_runtime.active_brush_name
        brush_runtime.active_brush_name = active_brush_name
        debug_log("active_brush_switch", prev_brush, "->", active_brush_name)

    if source == "MOUSE" and (brush_changed or source_changed) and active_brush_name == "Draw":
        _apply_draw_default_strength_for_source(context, source, reason="brush_or_source_switch")

    # Defaults behavior: only apply on first detection/source switch.
    # If the user manually edits strength afterward, do not force it back.
    if not source_changed:
        return

    _apply_smooth_default_strength_for_source(context, source, reason="source_switch")


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
