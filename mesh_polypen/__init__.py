# <pep8-80 compliant>

bl_info = {
    "name": "Polypen",
    "author": "Nutti",
    "version": (0, 1, 0),
    "blender": (2, 79, 0),
    "location": "3D View > Tool shelf > Polypen",
    "description": "Polypen in Blender",
    "warning": "This is an experimental version",
    "support": "COMMUNITY",
    "wiki_url": "",
    "tracker_url": "https://github.com/nutti/Polypen",
    "category": "Mesh"
}

if "bpy" in locals():
    import importlib
    importlib.reload(point_mode)
else:
    from . import point_mode

import bpy


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
