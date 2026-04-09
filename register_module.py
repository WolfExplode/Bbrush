import bpy
from bpy.app.handlers import persistent

from . import depth_map, preferences, topbar, sculpt, src
from .utils import register_submodule_factory

model_tuple = (
    src,
    topbar,
    sculpt,
    depth_map,
    preferences,
)

register_module, unregister_module = register_submodule_factory(model_tuple)

owner = object()


def sync_sculpt_tool_shelf():
    """Swap Bbrush sculpt shelf in/out when entering or leaving sculpt mode."""
    context = bpy.context
    try:
        if context.mode == "SCULPT":
            sculpt.activate_sculpt_brush_shelf(context, None)
        else:
            sculpt.deactivate_sculpt_brush_shelf(context)
    except Exception as e:
        from .debug import debug_log
        import traceback
        debug_log("sync_sculpt_tool_shelf failed:", repr(e))
        debug_log(traceback.format_exc())


def object_mode_sync_sculpt_shelf():
    sync_sculpt_tool_shelf()


def load_subscribe():
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.Object, "mode"),
        owner=owner,
        args=(),
        notify=object_mode_sync_sculpt_shelf,
        options={"PERSISTENT"},
    )


@persistent
def load_post(_args):
    bpy.msgbus.clear_by_owner(owner)
    load_subscribe()
    # Global brush_shelf survives file load; clear so ORIGINAL matches this .blend.
    sculpt.deactivate_sculpt_brush_shelf(bpy.context)
    sync_sculpt_tool_shelf()


def register():
    register_module()

    sculpt.BrushKeymap.start_key(bpy.context)

    load_subscribe()
    bpy.app.handlers.load_post.append(load_post)

    sync_sculpt_tool_shelf()


def unregister():
    try:
        sculpt.unregister_addon_runtime(bpy.context)
    except Exception as e:
        import traceback
        print("BBrush: unregister_addon_runtime during unregister failed:", repr(e))
        traceback.print_exc()

    bpy.msgbus.clear_by_owner(owner)
    if load_post in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post)

    unregister_module()
