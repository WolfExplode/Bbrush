import bpy
from bpy.app.handlers import persistent

from . import depth_map, preferences, topbar, sculpt, src
from .utils import register_submodule_factory, get_pref, is_bbruse_mode

model_tuple = (
    src,
    topbar,
    sculpt,
    depth_map,
    preferences,
)

register_module, unregister_module = register_submodule_factory(model_tuple)

owner = object()


def sync_bbrush_sculpt_mode():
    """Bbrush is active whenever Blender is in sculpt mode."""
    context = bpy.context
    try:
        if context.mode == "SCULPT":
            if sculpt.brush_runtime is None:
                sculpt.start_bbrush(context, None)
        elif sculpt.brush_runtime is not None:
            sculpt.exit_bbrush(context, False)
    except Exception:
        pass


def object_mode_sync_bbrush():
    sync_bbrush_sculpt_mode()


def load_subscribe():
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "mode"),
        owner=owner,
        args=(),
        notify=object_mode_sync_bbrush,
        options={"PERSISTENT"},
    )


@persistent
def load_post(_args):
    bpy.msgbus.clear_by_owner(owner)
    load_subscribe()
    sync_bbrush_sculpt_mode()


def bbrush_timer():
    pref = get_pref()

    if not is_bbruse_mode():
        sculpt.keymap.try_restore_keymap()
        sculpt.view_property.try_restore_view_property()
        sculpt.update_brush_shelf.try_restore_brush_shelf()

    return pref.refresh_interval


def register():
    register_module()

    load_subscribe()
    bpy.app.handlers.load_post.append(load_post)

    bpy.app.timers.register(bbrush_timer, first_interval=1, persistent=True)
    sync_bbrush_sculpt_mode()


def unregister():
    sculpt.exit_bbrush(bpy.context, True)

    bpy.msgbus.clear_by_owner(owner)
    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)

    if bpy.app.timers.is_registered(bbrush_timer):
        bpy.app.timers.unregister(bbrush_timer)

    unregister_module()
