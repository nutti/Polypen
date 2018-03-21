# <pep8-80 compliant>

import bpy
import bgl
import bmesh
from mathutils import Vector, kdtree
from bpy_extras import view3d_utils

from pprint import pprint


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


class Properties:
    running = False


class OpBase:
    def init(self, context, event):
        raise NotImplemented

    def fini(self, context, event):
        raise NotImplemented

    def do_modal(self, context, event):
        raise NotImplemented


class BuildMeshOp(OpBase):
    __handle = None

    @staticmethod
    def handle_add(obj, context):
        BuildMeshOp.__handle = bpy.types.SpaceView3D.draw_handler_add(
            BuildMeshOp.draw, (obj, context), 'WINDOW', 'POST_PIXEL'
        )

    @staticmethod
    def handle_remove():
        if BuildMeshOp.__handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                BuildMeshOp.__handle, 'WINDOW'
            )
            BuildMeshOp.__handle = None

    @staticmethod
    def draw(obj, context):
        props = context.scene.polypen_props.point_mode

        if not props.running:
            return

        # draw point
        bgl.glPointSize(3)
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

    def __add_mesh(self, context, region, space):
        print("add mesh")
        if len(self.points) < 3:
            return

        # mouse to view3d
        vcos = [
            view3d_utils.region_2d_to_location_3d(
                region, space.region_3d, p, Vector((0.0, 0.0, 0.0))
            ) for p in self.points
        ]

        obj = context.active_object
        sc = context.scene
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

    def __init__(self):
        self.points = []

    def init(self, context, event):
        mco = Vector((event.mouse_region_x, event.mouse_region_y))
        BuildMeshOp.handle_add(self, context)
        self.points.append(mco.copy())

        return 'RUNNING_MODAL'

    def fini(self, context, event):
        area, region, space = get_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')
        pprint(self.points)
        if context.edit_object:
            self.__add_mesh(context, region, space)
        else:
            self.__build_mesh(context, region, space)
        BuildMeshOp.handle_remove()

    def do_modal(self, context, event):
        mco = Vector((event.mouse_region_x, event.mouse_region_y))

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                self.points.append(mco.copy())
        elif event.type == 'MOUSEMOVE':
            self.points[-1] = mco.copy()
        elif event.type == 'RIGHTMOUSE':
            if event.value == 'PRESS':
                return 'FINISHED'

        return 'RUNNING_MODAL'


class DividePolygonOp(OpBase):
    __handle = None

    @staticmethod
    def handle_add(obj, context):
        DividePolygonOp.__handle = bpy.types.SpaceView3D.draw_handler_add(
            DividePolygonOp.draw, (obj, context), 'WINDOW', 'POST_PIXEL'
        )

    @staticmethod
    def handle_remove():
        if DividePolygonOp.__handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                DividePolygonOp.__handle, 'WINDOW'
            )
            DividePolygonOp.__handle = None

    @staticmethod
    def draw(obj, context):
        pass

    def __init__(self):
        self.src_vert = None
        self.tgt_edge = None
        self.sel_status = {}

    def __save_bmesh_status(self, bm):
        self.sel_status["sel_verts"] = [v for v in bm.verts if v.select]
        self.sel_status["sel_edges"] = [e for e in bm.edges if e.select]
        self.sel_status["sel_faces"] = [f for f in bm.faces if f.select]

    def __restore_bmesh_status(self, bm):
        # clear selection
        for v in bm.verts:
            v.select = False
        for e in bm.edges:
            e.select = False
        for f in bm.faces:
            f.select = True

        # restore selection
        for v in self.sel_status["sel_verts"]:
            v.select = True
        for e in self.sel_status["sel_edges"]:
            e.select = True
        for f in self.sel_status["sel_faces"]:
            f.select = True

    def __get_nearest_vert(self, bm, mco, region, space):

        print("save")
        #self.__save_bmesh_status(bm)

        kd = kdtree.KDTree(len(bm.verts))
        for i, v in enumerate(bm.verts):
            kd.insert(v.co[:], i)
        kd.balance()

        # mouse to view3d
        mco_3d = view3d_utils.region_2d_to_location_3d(
            region, space.region_3d, mco, Vector((0.0, 0.0, 0.0))
        )

        vco, vidx, vdist = kd.find(mco_3d)

        print(vco)
        print(vidx)
        print(vdist)

        # ret = bpy.ops.view3d.select(extend=True, location=mco)
        # if ret == {'PASS_THROUGH'}:
        #     return None


        print("restore")
        #self.__restore_bmesh_status(bm)

        return bm.verts[vidx]

    def __get_nearest_edge(self, bm, mco):
        pass
        #self.__save_bmesh_status(bm)

        # ret = bpy.ops.view3d.select(extend=True, location=mco)
        # if ret == {'PASS_THROUGH'}:
        #     return None
        #
        # try:
        #     geom = bm.select.history[-1]
        # except IndexError:
        #     return None

        #self.__restore_bmesh_status(bm)

        #if isinstance(geom, bmesh.types.BMVert):
        #    return geom

    def init(self, context, event):
        if not context.edit_object:
            return 'CANCELLED'

        mco = Vector((event.mouse_region_x, event.mouse_region_y))
        area, region, space = get_space(context, 'VIEW_3D', 'WINDOW', 'VIEW_3D')

        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)

        print("__get_nearest_vert")

        nv = self.__get_nearest_vert(bm, mco, region, space)
        if nv:
            self.src_vert = nv

        BuildMeshOp.handle_add(self, context)

        return 'RUNNING_MODAL'

    def fini(self, context, event):
        if not context.edit_object:
            return

        if not self.src_vert:
            return
        mco = Vector((event.mouse_region_x, event.mouse_region_y))

        obj = context.active_object
        bm = bmesh.from_edit_mesh(obj.data)

        ne = self.__get_nearest_edge(bm, mco)
        if ne:
            self.src_vert = ne

        BuildMeshOp.handle_remove()

    def do_modal(self, context, event):
        if context.edit_object:
            return 'CANCELLED'

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                return 'FINISHED'

        return 'RUNNING_MODAL'

        # mco = Vector((event.mouse_region_x, event.mouse_region_y))
        #
        # if event.type == 'LEFTMOUSE':
        #     if event.value == 'PRESS':
        #         self.points.append(mco.copy())
        # elif event.type == 'MOUSEMOVE':
        #     self.points[-1] = mco.copy()


class GeneratePolygon(bpy.types.Operator):

    bl_idname = "mesh.polypen_generate_polygon"
    bl_label = "Generate Polygon"
    bl_description = "Generate polygon"
    bl_option = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.stroking = False
        self.op = None

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
                    if event.shift:
                        print("DividePolygon")
                        self.op = DividePolygonOp()
                    else:
                        print("BuildMesh")
                        self.op = BuildMeshOp()
                    ret = self.op.init(context, event)
                    # [TODO] ret
                    self.stroking = True
                    print("stroking started")

        if self.op:
            ret = self.op.do_modal(context, event)
            if ret != 'RUNNING_MODAL':
                if self.stroking:
                    self.op.fini(context, event)
                    self.op = None
                    self.stroking = False
                return {'FINISHED'}

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
