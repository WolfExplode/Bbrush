"""Blender 5.1+: Shift+LMB sculpt uses a secondary brush slot; Shift release restores primary.

Secondary is not activated on Shift alone (so Shift+F and other Shift shortcuts stay on the primary brush).
"""

import bpy

from ..debug import debug_log

# Default secondary when slot has never been set: try custom asset, then Essentials Smooth.
_DEFAULT_SECONDARY_CUSTOM_REF = (
    "CUSTOM",
    "User Library",
    r"Saved\Brushes\BBrush_Smooth.asset.blend/Brush/BBrush_Smooth",
)

_FALLBACK_ESSENTIALS_SMOOTH_REF = (
    "ESSENTIALS",
    "",
    "brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth",
)


def _read_brush_asset_triple(context):
    ts = context.tool_settings.sculpt
    ref = ts.brush_asset_reference
    return (ref.asset_library_type, ref.asset_library_identifier, ref.relative_asset_identifier)


def _activate_brush_asset(context, triple) -> bool:
    try:
        ret = bpy.ops.brush.asset_activate(
            asset_library_type=triple[0],
            asset_library_identifier=triple[1],
            relative_asset_identifier=triple[2],
        )
        return "FINISHED" in ret
    except RuntimeError:
        return False


def _activate_default_secondary_chain(context) -> bool:
    if _activate_brush_asset(context, _DEFAULT_SECONDARY_CUSTOM_REF):
        return True
    if _activate_brush_asset(context, _FALLBACK_ESSENTIALS_SMOOTH_REF):
        return True
    return False


def _shift_only(event) -> bool:
    return event.shift and not event.ctrl and not event.alt


def ensure_shift_secondary_for_sculpt(context, event) -> bool:
    """Activate secondary before the first sculpt stroke (Shift+LMB, not Shift alone)."""
    if bpy.app.version < (5, 1, 0):
        return False
    if event is None or not _shift_only(event):
        return False

    from . import brush_runtime

    if brush_runtime.shift_secondary_active:
        return True

    brush_runtime.shift_primary_saved_ref = _read_brush_asset_triple(context)

    ok = False
    if brush_runtime.shift_secondary_brush_ref is not None:
        ok = _activate_brush_asset(context, brush_runtime.shift_secondary_brush_ref)
    if not ok:
        ok = _activate_default_secondary_chain(context)

    if ok:
        brush_runtime.shift_secondary_active = True
        debug_log("shift_secondary_activate")
    else:
        debug_log("shift_secondary_activate_failed", brush_runtime.shift_primary_saved_ref)
    return ok


def mark_shift_secondary_sculpt_used():
    if bpy.app.version < (5, 1, 0):
        return
    from . import brush_runtime

    if brush_runtime.shift_secondary_active:
        brush_runtime.shift_secondary_used_for_sculpt = True


def restore_shift_secondary_brush(context, *, remember_secondary: bool = False):
    if bpy.app.version < (5, 1, 0):
        return
    from . import brush_runtime

    if not brush_runtime.shift_secondary_active:
        return

    if remember_secondary and brush_runtime.shift_secondary_used_for_sculpt:
        brush_runtime.shift_secondary_brush_ref = _read_brush_asset_triple(context)

    _activate_brush_asset(context, brush_runtime.shift_primary_saved_ref)
    brush_runtime.shift_secondary_active = False
    brush_runtime.shift_secondary_used_for_sculpt = False
    debug_log(
        "shift_secondary_restore",
        "remembered=",
        remember_secondary,
        "slot=",
        brush_runtime.shift_secondary_brush_ref,
    )


def sync_shift_secondary_brush(context, event):
    """Shift release only: restore primary (defer activation to LMB sculpt)."""
    if bpy.app.version < (5, 1, 0):
        return
    if event is None:
        return
    if event.type not in {"LEFT_SHIFT", "RIGHT_SHIFT"}:
        return
    if event.value != "RELEASE" or event.shift:
        return

    from . import brush_runtime

    if not brush_runtime.shift_secondary_active:
        return

    restore_shift_secondary_brush(
        context,
        remember_secondary=brush_runtime.shift_secondary_used_for_sculpt,
    )


def clear_shift_secondary_override(context):
    if bpy.app.version < (5, 1, 0):
        return
    from . import brush_runtime

    if not getattr(brush_runtime, "shift_secondary_active", False):
        return
    restore_shift_secondary_brush(
        context,
        remember_secondary=getattr(brush_runtime, "shift_secondary_used_for_sculpt", False),
    )
