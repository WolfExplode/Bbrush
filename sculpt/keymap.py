import bpy

from ..debug import debug_log

keys: list[tuple["bpy.types.KeyMap", "bpy.types.KeyMapItem"]] = []

# PRESS: switch shelf as soon as Ctrl / Shift / Alt are held (e.g. mask or hide shelf).
# RELEASE: restore shelf when modifiers are let go — no mouse modal is running then.
_MODIFIER_SHELF_SYNC_KEYS = (
    "LEFT_CTRL",
    "RIGHT_CTRL",
    "LEFT_SHIFT",
    "RIGHT_SHIFT",
    "LEFT_ALT",
    "RIGHT_ALT",
)


class BbrushSyncBrushShelfModifiers(bpy.types.Operator):
    bl_idname = "sculpt.bbrush_sync_brush_shelf_modifiers"
    bl_label = "Sync brush shelf (modifiers)"
    bl_description = "Update Bbrush tool shelf when Ctrl, Shift, or Alt is pressed or released"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.mode == "SCULPT"

    def invoke(self, context, event):
        from .update_brush_shelf import UpdateBrushShelf

        UpdateBrushShelf.update_brush_shelf(context, event)
        return {"PASS_THROUGH"}


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
                pass
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

        # -1 = ignore modifier state. Defaults (0) mean "modifier must be off", so e.g.
        # LEFT_SHIFT+PRESS would not match while Ctrl is held — breaks Ctrl then Shift.
        _any_mod = dict(shift=-1, ctrl=-1, alt=-1, oskey=-1, hyper=-1)
        for mod_key in _MODIFIER_SHELF_SYNC_KEYS:
            for evt_value in ("PRESS", "RELEASE"):
                kmi = km.keymap_items.new(
                    BbrushSyncBrushShelfModifiers.bl_idname,
                    mod_key,
                    evt_value,
                    **_any_mod,
                )
                keys.append((km, kmi))

        debug_log("addon keymaps registered", len(keys))
