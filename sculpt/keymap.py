import bpy

from ..debug import debug_log

keys: list[tuple["bpy.types.KeyMap", "bpy.types.KeyMapItem"]] = []


class BrushKeymap:
    @classmethod
    def start_key(cls, context):
        """Register add-on overlay keymaps (Hard Ops style)."""
        cls.register_addon_keymaps(context)

    @staticmethod
    def restore_key(context):
        BrushKeymap.unregister_addon_keymaps()

    @staticmethod
    def unregister_addon_keymaps():
        """Remove add-on overlay keymaps."""
        global keys
        for km, kmi in keys:
            try:
                km.keymap_items.remove(kmi)
            except Exception:
                ...
        keys.clear()

    @staticmethod
    def register_addon_keymaps(context=None):
        """Add keymap items into wm.keyconfigs.addon (does not touch user's preset)."""
        global keys

        # Ensure idempotency: don't duplicate registrations.
        if keys:
            return

        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        if not kc:
            debug_log("keyconfig unavailable (batch mode?), no keybinding items registered")
            return

        # Primary BBrush mouse handlers (core sculpting behavior).
        km = kc.keymaps.new(name="Sculpt", space_type="EMPTY", region_type="WINDOW")

        kmi = km.keymap_items.new("sculpt.bbrush_left_mouse", "LEFTMOUSE", "PRESS", any=True)
        keys.append((km, kmi))

        kmi = km.keymap_items.new("sculpt.bbrush_right_mouse", "RIGHTMOUSE", "PRESS", any=True)
        keys.append((km, kmi))

        debug_log("addon keymaps registered", len(keys))


def try_restore_keymap():
    """在不是Bbrush模式时
    快捷键任未复位
    尝试修复"""
    context = bpy.context
    from ..utils import is_bbrush_mode
    if not is_bbrush_mode():
        BrushKeymap.unregister_addon_keymaps()
        debug_log("try_restore_keymap ok")
