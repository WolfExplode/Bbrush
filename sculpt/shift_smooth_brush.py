"""Shift hold: swap active sculpt brush to Essentials Smooth; restore on release (Blender 5.1+)."""

import bpy

from ..debug import debug_log

# Probed from brush_asset_reference while Essentials Smooth is active (forward slashes).
_SMOOTH_ESSENTIALS_REF = (
    "ESSENTIALS",
    "",
    "brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth",
)


def _read_brush_asset_triple(context):
    ts = context.tool_settings.sculpt
    ref = ts.brush_asset_reference
    return (ref.asset_library_type, ref.asset_library_identifier, ref.relative_asset_identifier)


def _activate_brush_asset(context, triple):
    bpy.ops.brush.asset_activate(
        asset_library_type=triple[0],
        asset_library_identifier=triple[1],
        relative_asset_identifier=triple[2],
    )


def sync_shift_smooth_brush(context, event):
    """Call from modifier sync after UpdateBrushShelf — handles Shift press/release only."""
    if bpy.app.version < (5, 1, 0):
        return
    if event is None:
        return
    et = event.type
    if et not in {"LEFT_SHIFT", "RIGHT_SHIFT"}:
        return

    from . import brush_runtime

    if event.value == "RELEASE":
        if not event.shift and brush_runtime.shift_smooth_active:
            _activate_brush_asset(context, brush_runtime.shift_smooth_saved_ref)
            brush_runtime.shift_smooth_active = False
            debug_log("shift_smooth_restore", brush_runtime.shift_smooth_saved_ref)
        return

    # PRESS
    if event.ctrl or event.alt:
        return
    if brush_runtime.shift_smooth_active:
        return

    brush_runtime.shift_smooth_saved_ref = _read_brush_asset_triple(context)
    _activate_brush_asset(context, _SMOOTH_ESSENTIALS_REF)
    brush_runtime.shift_smooth_active = True
    debug_log("shift_smooth_activate", "saved=", brush_runtime.shift_smooth_saved_ref)


def clear_shift_smooth_override(context):
    """Restore previous brush if Shift swap was active (mode exit / teardown)."""
    if bpy.app.version < (5, 1, 0):
        return
    from . import brush_runtime

    if not getattr(brush_runtime, "shift_smooth_active", False):
        return
    _activate_brush_asset(context, brush_runtime.shift_smooth_saved_ref)
    brush_runtime.shift_smooth_active = False
