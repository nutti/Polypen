# <pep8-80 compliant>

class GeneratePolygon(bpy.types.Operator):

    bl_idname = "mesh.polypen_generate_polygon"
    bl_label = "Generate Polygon"
    bl_description = "Generate polygon"
    bl_option = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}
