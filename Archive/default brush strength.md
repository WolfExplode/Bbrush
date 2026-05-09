# Archived: Default brush strength by input source

Source commit: `665e6d8d833b53303544d1b59dec24ae4e16f80a`

## Why archived

This implementation set default sculpt brush strength based on detected input source (mouse vs tablet), but it could overwrite user-adjusted values later. The behavior did not reliably preserve manual strength changes, so the feature was removed from runtime code for now.

## What was removed

- Input source detection from sculpt events (mouse/tablet classification using pressure/tilt/is_tablet).
- Smooth strength defaults tied to input source:
  - Mouse: `0.1`
  - Tablet: `0.7`
- Draw strength default on mouse:
  - Mouse: `0.15`
- Event-driven hooks that reapplied those defaults from left-mouse invoke/modal and shift-smooth paths.
- Shift-release top-bar restore helper that was introduced in the same commit as part of this behavior package.

## Removed symbols and paths

- `sculpt/__init__.py`
  - `BrushRuntime.input_source`
  - `BrushRuntime.active_brush_name`
  - `_detect_input_source_from_event()`
  - `_apply_smooth_default_strength_for_source()`
  - `_apply_draw_default_strength_for_source()`
  - `ensure_shift_smooth_default_strength()`
  - `handle_input_source_event()`
  - sculpt-enter default application call inside `activate_sculpt_brush_shelf()`
- `sculpt/left_mouse.py`
  - `handle_input_source_event()` calls in `invoke()` and `modal()`
  - `ensure_shift_smooth_default_strength()` calls in `execute_brush_stroke()`
- `sculpt/update_brush_shelf.py`
  - `_restore_active_tool_ui()`
  - Shift-release UI resync block that called the helper

## Reimplementation note

If this feature is revisited, the new design should distinguish between programmatic updates and user edits before applying defaults.
