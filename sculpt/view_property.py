import bpy

from ..debug import DEBUG_VIEW_PREF


class ViewProperty:
    """Previously swapped Blender input/view prefs while in Bbrush mode (removed with view navigation)."""

    @staticmethod
    def start_view_property(context):
        if DEBUG_VIEW_PREF:
            print("start_view_property (no-op)")

    @staticmethod
    def restore_view_property(context, save_user_pref=False):
        if save_user_pref:
            bpy.ops.wm.save_userpref()
        if DEBUG_VIEW_PREF:
            print("restore_view_property (no-op)", save_user_pref)


def try_restore_view_property():
    if DEBUG_VIEW_PREF:
        print("try_restore_view_property (no-op)")
