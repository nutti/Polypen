# <pep8-80 compliant>

import bpy
import bgl
import bmesh
from mathutils import Vector
from bpy_extras import view3d_utils

from pprint import pprint


class Properties:
    running = False


class Renderer:
    __handle = None

    @staticmethod
    def handle_add(obj, context):
        Renderer.__handle = bpy.types.SpaceView3D.draw_handler_add(
            Renderer.draw, (obj, context), 'WINDOW', 'POST_PIXEL'
        )

    @staticmethod
    def handle_remove():
        if Renderer.__handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                Renderer.__handle, 'WINDOW'
            )
            Renderer.__handle = None

    @staticmethod
    def draw(obj, context):
        props = context.scene.polypen_props.point_mode

        if not props.running:
            return

        # draw point
        bgl.glPointSize(4)
        bgl.glBegin(bgl.GL_POINTS)
        bgl.glColor4f(1.0, 1.0, 1.0, 0.8)
        for p in obj.points:
            bgl.glVertex2f(p.x, p.y)
        bgl.glEnd()

        if len(obj.points) <= 1:
            return

        bgl.glEnable(bgl.GL_BLEND)

        # draw line
        bgl.glLineWidth(2)
        bgl.glBegin(bgl.GL_LINE_LOOP)
        bgl.glColor4f(1.0, 1.0, 1.0, 0.5)
        for p in obj.points:
            bgl.glVertex2f(p.x, p.y)
        bgl.glEnd()

        # draw current line
        bgl.glLineWidth(2)
        bgl.glBegin(bgl.GL_LINES)
        bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
        p0 = obj.points[0]
        p1 = obj.points[-1]
        bgl.glVertex2f(p0.x, p0.y)
        bgl.glVertex2f(p1.x, p1.y)
        if len(obj.points) > 2:
            p2 = obj.points[-2]
            bgl.glVertex2f(p1.x, p1.y)
            bgl.glVertex2f(p2.x, p2.y)
        bgl.glEnd()

        if len(obj.points) == 2:
            bgl.glDisable(bgl.GL_BLEND)
            return

        # draw face
        bgl.glBegin(bgl.GL_TRIANGLE_FAN)
        bgl.glColor4f(1.0, 1.0, 1.0, 0.2)
        for p in obj.points:
            bgl.glVertex2f(p.x, p.y)
        bgl.glEnd()

        bgl.glDisable(bgl.GL_BLEND)


def get_space(context, area_type, region_type, space_type):

    area = None
    region = None
    space = None

    for area in context.screen.areas:
        if area.type == area_type:
            break
    else:
        return (None, None, None)
    for region in area.regions:
        if region.type == region_type:
            break
    for space in area.spaces:
        if space.type == space_type:
            break

    return (area, region, space)


class GeneratePolygon(bpy.types.Operator):

    bl_idname = "mesh.polypen_generate_polygon"
    bl_label = "Generate Polygon"
    bl_description = "Generate polygon"
    bl_option = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return not context.edit_object

    def __init__(self):
        self.points = []
        self.stroking = False

    def __build_mesh(self, context, region, space):
        print("build mesh")
        if len(self.points) < 3:
            return

        # mouse to view3d
        vcos = [
            view3d_utils.region_2d_to_location_3d(
                region, space.region_3d, p, Vector((0.0, 0.0, 0.0))
            ) for p in self.points
        ]

        # generate new object
        me = bpy.data.meshes.new("Polypen_Mesh")
        obj = bpy.data.objects.new("Polypen", me)
        sc = context.scene
        sc.objects.link(obj)

        # select only new object, and activate it
        for o in bpy.data.objects:
            o.select = False
        sc.objects.active = obj
        obj.select = True

        # generate mesh from polypen
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data)

        verts = []
        for vco in vcos:
            verts.append(bm.verts.new((vco.x, vco.y, vco.z)))

        verts_group = []
        idx = 2
        while True:
            if len(verts[idx:]) == 0:
                break
            group = [verts[0], verts[idx - 1]]
            if len(verts[idx:]) <= (sc.polypen_pm_ngon - 2):
                group.extend(verts[idx:])
                verts_group.append(group)
                break
            if len(verts[idx:]) <= sc.polypen_pm_ngon:
                group.extend(verts[idx:])
                verts_group.append(group)
                break
            group.extend(verts[idx:idx + sc.polypen_pm_ngon - 2])
            verts_group.append(group)
            idx = idx + sc.polypen_pm_ngon - 2
            if len(verts[idx:]) <= 0:
                print("Unexpected error")
                break

        for g in verts_group:
            bm.faces.new(g)
        print(verts_group)

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')

    def modal(self, context, event):
        props = context.scene.polypen_props.point_mode

        mco = Vector((event.mouse_region_x, event.mouse_region_y))

        if not props.running:
            return {'FINISHED'}

        area, region, space = get_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
        if not space:
            return {'FINISHED'}

        # out viewport
        if mco.x < 0 or mco.x > area.width or mco.y < 0 or mco.y > area.height:
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                # start stroking
                if not self.stroking:
                    self.points = []
                    Renderer.handle_add(self, context)
                    self.stroking = True
                    print("stroking started")
                self.points.append(mco.copy())
                return {'RUNNING_MODAL'}
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'PRESS':
                # end stroking
                if self.stroking:
                    pprint(self.points)
                    self.__build_mesh(context, region, space)
                    Renderer.handle_remove()
                    self.stroking = False
                    print("stroking ended")
                return {'RUNNING_MODAL'}
        elif event.type == 'MOUSEMOVE':
            if self.stroking:
                self.points[-1] = mco.copy()

        if context.area:
            context.area.tag_redraw()

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        props = context.scene.polypen_props.point_mode

        if props.running:
            props.running = False
            return {'FINISHED'}
        else:
            props.running = True
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
