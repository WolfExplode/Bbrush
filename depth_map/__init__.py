import bpy
from mathutils import Vector

from .gpu_buffer import draw_gpu_buffer
from ..debug import debug_log
from ..utils import get_pref, get_region_height, get_region_width, check_display_mode_is_draw

handel = None

depth_buffer_check = {
    # "wh": ((x1, x2), (y1, y2)),
    # "translate":w, -h, 0
    # "draw_error": "ERROR INFO"
}


def check_depth_map_is_draw(context):
    """检查深度图是否需要绘制"""
    pref = get_pref()
    mode = pref.depth_display_mode
    return check_display_mode_is_draw(context, mode)


def draw_depth():
    global depth_buffer_check
    context = bpy.context

    if check_depth_map_is_draw(context):
        filling_data(context)

        if draw_error := draw_gpu_buffer(context, depth_buffer_check):
            debug_log(draw_error)
            depth_buffer_check["draw_error"] = draw_error
    elif depth_buffer_check:
        depth_buffer_check = {}


def filling_data(context):
    global depth_buffer_check
    pref = get_pref()
    depth_scale = pref.depth_scale

    width = context.region.width
    height = context.region.height
    draw_width = int(width * depth_scale)
    draw_height = int(height * depth_scale)
    draw_size = Vector((draw_width, draw_height))

    depth_offset = Vector(pref.depth_offset)

    header_height = get_region_height(context, "HEADER") + get_region_height(context, "TOOL_HEADER")
    tools_width = get_region_width(context, "TOOLS")

    area_offset = Vector((tools_width, -header_height))

    location = depth_offset + area_offset + Vector((0, height - draw_height))

    # 限制位置
    ui_width = get_region_width(context, "UI")
    asset_shelf_height = get_region_height(context, "ASSET_SHELF") + get_region_height(context, "ASSET_SHELF_HEADER")
    limit_x = max(tools_width, min(width - ui_width - draw_width, location.x))
    limit_y = max(asset_shelf_height, min(height - header_height - draw_height, location.y))
    limitation = Vector((limit_x, limit_y))

    x1, y1 = limitation
    x2, y2 = limitation + draw_size

    # 添加坐标 存起来笔刷的操作符判断鼠标有没有放在深度图上使用
    depth_buffer_check["area_points"] = (x1, x2), (y1, y2)
    depth_buffer_check["draw_box"] = x1, x2, y1, y2
    depth_buffer_check["text_location"] = x1, y1

    # 修改为符合gpu绘制的坐标
    w = 1 / width * x1
    h = 1 / height * (y1 + draw_height)
    depth_buffer_check["translate"] = w, h, 0


def register():
    global handel
    handel = bpy.types.SpaceView3D.draw_handler_add(draw_depth, (), "WINDOW", "POST_PIXEL")


def unregister():
    global handel
    if handel:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(handel, "WINDOW")
        except Exception as e:
            debug_log("draw_handler_remove failed:", repr(e))
        handel = None
