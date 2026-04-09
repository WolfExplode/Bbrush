import time

from mathutils import Vector


class ManuallyManageEvents:
    """由于5.0版本的拖动事件触发不灵敏,所以需要手动管理
    但是这个没有处理长按的状态
    """

    def start_manually_manage_events(self, event):
        # 开始手动管理事件（仅实例属性，避免与类属性共享状态）
        self.start_time = time.time()
        self.start_mouse = Vector((event.mouse_x, event.mouse_y))

    @property
    def event_running_time(self) -> float:
        start_time = getattr(self, "start_time", None)
        if start_time is None:
            return 0.0
        return time.time() - start_time

    def check_is_moving(self, event) -> bool:
        start_mouse = getattr(self, "start_mouse", None)
        if start_mouse is None:
            return event.type == "MOUSEMOVE"
        now_mouse = Vector((event.mouse_x, event.mouse_y))
        return event.type == "MOUSEMOVE" or now_mouse != start_mouse
