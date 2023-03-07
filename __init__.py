# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "n8png",
    "author" : "xelivous",
    "description" : "Implement's Neverdaunt:8Bit's png model file format.",
    "blender" : (3, 4, 1),
    "version" : (0, 0, 2),
    "location" : "",
    "warning" : "",
    "support": "COMMUNITY",
    "category" : "Import-Export"
}


import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )

class ImportN8PNG(bpy.types.Operator, ImportHelper):
    """Import from png and ncd file format (.png, .ncd)"""
    bl_idname = "import_n8.files"
    bl_label = 'Import N8* Files (*.png;*.ncd)'
    bl_options = {'UNDO'}

    filter_glob: StringProperty(default="*.png;*.ncd", options={'HIDDEN'})
        
    def execute(self, context):
        from pathlib import Path
        from . import import_n8png, import_n8ncd

        p = Path(self.filepath)
        filename = p.stem
        extension = p.suffix

        print('Selected file:', self.filepath)
        print('File name:', filename)
        print('File extension:', extension)
        if extension == ".png":
            import_n8png.load(context, self.filepath)
        elif extension == ".ncd":
            import_n8ncd.load(context, self.filepath)

        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(ImportN8PNG.bl_idname, text=ImportN8PNG.bl_label)

def register():
	from bpy.utils import register_class
	register_class(ImportN8PNG)
	bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
		
def unregister():
	from bpy.utils import unregister_class
	unregister_class(ImportN8PNG)
	bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()