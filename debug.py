"""Addon debug output: controlled by Preferences → Debug."""


def is_debug_enabled() -> bool:
    try:
        import bpy

        pkg = __package__
        if not pkg:
            return False
        addon = bpy.context.preferences.addons.get(pkg)
        if addon is None:
            return False
        return bool(getattr(addon.preferences, "debug", False))
    except Exception:
        return False


def debug_log(*args, **kwargs) -> None:
    """Print to the system console when Debug is enabled in add-on preferences."""
    if is_debug_enabled():
        print("BBrush:", *args, **kwargs)
