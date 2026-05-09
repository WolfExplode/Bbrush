"""Blender 5.1+: Shift holds a secondary brush slot (default: custom smooth → Essentials fallback); release restores primary."""

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


def sync_shift_secondary_brush(context, event):
    """Shift press/release: swap to secondary slot or restore primary."""
    if bpy.app.version < (5, 1, 0):
        return
    if event is None:
        return
    if event.type not in {"LEFT_SHIFT", "RIGHT_SHIFT"}:
        return

    from . import brush_runtime

    if event.value == "RELEASE":
        if not event.shift and brush_runtime.shift_secondary_active:
            # Whatever brush is active now (e.g. picked from Asset Shelf) becomes the remembered secondary.
            brush_runtime.shift_secondary_brush_ref = _read_brush_asset_triple(context)
            _activate_brush_asset(context, brush_runtime.shift_primary_saved_ref)
            brush_runtime.shift_secondary_active = False
            debug_log(
                "shift_secondary_restore",
                "saved_slot=",
                brush_runtime.shift_secondary_brush_ref,
                "primary=",
                brush_runtime.shift_primary_saved_ref,
            )
        return

    if event.ctrl or event.alt:
        return
    if brush_runtime.shift_secondary_active:
        return

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


def clear_shift_secondary_override(context):
    if bpy.app.version < (5, 1, 0):
        return
    from . import brush_runtime

    if not getattr(brush_runtime, "shift_secondary_active", False):
        return
    brush_runtime.shift_secondary_brush_ref = _read_brush_asset_triple(context)
    _activate_brush_asset(context, brush_runtime.shift_primary_saved_ref)
    brush_runtime.shift_secondary_active = False
