import bpy

from .click import BrushClick
from .depth import BrushDepthScale, BrushDepthMove
from .shape import BrushShape

# 通过行为来区分手势内容
brush = [
    BrushShape,
    BrushClick,

    BrushDepthScale,
    BrushDepthMove,
]

register_class, unregister_class = bpy.utils.register_classes_factory(brush)


def register():
    register_class()


def unregister():
    unregister_class()
