

import bpy

from . import point_mode


class OBJECT_PT_PolyPen(bpy.types.Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Polypen"
    bl_category = "Polypen"
    bl_context = 'objectmode'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.polypen_props
        sc = context.scene

        if not props.point_mode.running:
            layout.operator(point_mode.GeneratePolygon.bl_idname,
                            text="Start", icon='PLAY')
        else:
            layout.operator(point_mode.GeneratePolygon.bl_idname,
                            text="End", icon='PAUSE')

        layout.prop(sc, "polypen_pm_ngon")
