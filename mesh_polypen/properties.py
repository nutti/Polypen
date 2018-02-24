from bpy.props import IntProperty

from . import point_mode


class Properties:
    point_mode = None

    def __init__(self):
        self.point_mode = point_mode.Properties()


def init_props(scene):
    scene.polypen_props = Properties()

    scene.polypen_pm_ngon = IntProperty(
        name="N-gon",
        default=3,
        min=3,
        max=1000000
    )


def clear_props(scene):
    del scene.polypen_props
