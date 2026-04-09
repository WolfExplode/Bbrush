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

# Must match what register_addon_keymaps adds (LMB/RMB + modifier PRESS/RELEASE pairs).
_EXPECTED_BBRUSH_KEY_ITEM_COUNT = 2 + len(_MODIFIER_SHELF_SYNC_KEYS) * 2


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


_BBRUSH_KMI_IDNAMES = frozenset(
    {
        "sculpt.bbrush_left_mouse",
        "sculpt.bbrush_right_mouse",
        BbrushSyncBrushShelfModifiers.bl_idname,
    }
)


def _purge_orphan_bbrush_addon_keyitems():
    """Remove any BBrush keymap items still in the add-on keyconfig (stale refs, partial unregister)."""
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return
    for km in kc.keymaps:
        for kmi in list(km.keymap_items):
            if kmi.idname not in _BBRUSH_KMI_IDNAMES:
                continue
            try:
                km.keymap_items.remove(kmi)
            except Exception as e:
                debug_log(
                    "purge orphan bbrush keyitem failed:",
                    repr(e),
                    kmi.idname,
                )


def _clear_tracked_bbrush_keyitems():
    global keys
    for km, kmi in list(keys):
        try:
            km.keymap_items.remove(kmi)
        except Exception as e:
            debug_log("unregister_addon_keymaps: tracked remove failed:", repr(e))
    keys.clear()
    _purge_orphan_bbrush_addon_keyitems()


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
        _clear_tracked_bbrush_keyitems()

    @staticmethod
    def register_addon_keymaps(context=None):
        """Add keymap items into wm.keyconfigs.addon (does not touch user's preset)."""
        global keys

        if keys:
            if len(keys) == _EXPECTED_BBRUSH_KEY_ITEM_COUNT:
                return
            debug_log(
                "register_addon_keymaps: stale key tracking, clearing before register",
                len(keys),
                "expected",
                _EXPECTED_BBRUSH_KEY_ITEM_COUNT,
            )
            _clear_tracked_bbrush_keyitems()

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
