import bpy, bmesh
import time, struct, os, io
from pathlib import Path
from mathutils import Color, Quaternion, Vector
import math
import re

SCALE_CONVERSION:float = 1.0/100.0

PIXEL_SCALE = {
    "pixel": 25.0,
    "pixel2": 25.0,
    "tpixel": 10.0,
}

MESH_CACHE = {}

# https://docs.blender.org/api/current/bpy.types.Material.html
# https://docs.blender.org/api/current/bpy.types.MaterialSlot.html
# https://docs.blender.org/api/current/bpy.types.Object.html

def load_file(filepath, context) -> (str,str):
    """
    loads the n8 png into a string with the PNG data removed
    """
    print(f"importing n8png. filepath: {filepath.lower()}")

    data = ""
    version = "UNKNOWN"
    with open(filepath.lower(), mode='r', errors='ignore') as n8file:
        data = n8file.read()

        # trim everything before StartData (the png data)
        index = data.find("StartData")
        version = "StartData"
        # if we don't have StartData in the file it's going to be the other format, BEGIN!
        if index == -1:
            index = data.find('BEGIN!')
            version = "BEGIN!"
        if index == -1:
            print("This file format isn't supported")
            return
            
        data = data[index:]

    return data, version

class N8Mesh():
    model:str = None
    mesh = None
    pivot = None

    def __init__(self, model:str):
        self.model = model
        self.create()

    def set_name(self, name:str):
        self.mesh.name = name
        self.pivot.name = f"{name} Pivot"

    def set_position(self, vector:tuple):
        self.pivot.location = vector

    def set_offset(self, vector:tuple):
        self.mesh.location = vector

    def set_scale(self, vector:tuple):
        self.mesh.scale = vector
        #bpy.ops.object.select_all(action='DESELECT')
        #self.mesh.select_set(True)
        #bpy.context.view_layer.objects.active = self.mesh
        #bpy.ops.object.transform_apply(location = False, scale = True, rotation = False)
        #bpy.ops.object.select_all(action='DESELECT')

    def set_rotation(self, quat:Quaternion):
        self.pivot.rotation_quaternion = quat

    def set_local_rotation(self, quat:Quaternion):
        self.mesh.rotation_quaternion = quat

    def set_parent(self, target):
        self.pivot.parent = target

    def get_pivot(self):
        return self.pivot

    def create(self, model:str=None):
        if model:
            self.model = model

        self.pivot = bpy.data.objects.new( "empty", None )
        bpy.context.collection.objects.link(self.pivot)
        self.pivot.empty_display_size = .1
        self.pivot.empty_display_type = 'PLAIN_AXES'

        bpy.ops.object.select_all(action='DESELECT')

        filepath = os.path.dirname(os.path.realpath(__file__))
        filepath = str(Path(filepath) / "librarypixel.blend")
        with bpy.data.libraries.load(filepath=filepath, link=False) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name == self.model]

        for obj in data_to.objects:
            if obj is not None:
                bpy.context.collection.objects.link(obj)
                self.mesh = obj

        self.mesh.parent = self.pivot

        self.mesh.rotation_mode = "QUATERNION"
        self.pivot.rotation_mode = "QUATERNION"

        return self.pivot, self.mesh

class N8Pixel():
    id:str = None
    parent_id:int = None
    diffuse:Color = None
    diffuse_alpha:float = None
    emission:Color = None
    emission_alpha:float = None
    shader:str = None
    texture:Path = None
    model:str = None
    mesh:N8Mesh = None
    position:tuple = None
    rotation:Quaternion = None
    scale:tuple = None
    bones:dict = None

    def __init__(self, id:int):
        self.id = id
        self.shader = ""
        self.parent_id = 0 #root
        self.diffuse_alpha = 1
        self.emission_alpha = 1
        self.bones = {}
        self.position = (0,0,0)
        self.rotation = Quaternion()
        self.scale = (1,1,1)

    def __repr__(self):
        return f"""Pixel ID({self.id}) | {self.position}, {self.rotation}, {self.scale}
        {self.bones}
        """

class N8Bone():
    name:str = None
    position:tuple = None
    rotation:Quaternion = None
    scale:tuple = None

    def __init__(self, name:str):
        self.name = name.lower()
        self.rotation = Quaternion()
        self.scale = (1,1,1)
        self.position = (1,1,1)
    
    def __repr__(self):
        return f"""Bone({self.name}) | {self.position}, {self.rotation}, {self.scale}"""

    def set_position(self, vector:tuple):
        self.position= vector

    def set_rotation(self, quat:Quaternion):
        self.rotation = quat
    
    def set_scale(self, vector:tuple):
        self.scale = vector


class N8Parser():
    data = ""
    pixels = None
    display_name = "N8Block"
    block_origin = None
    block_scale = None

    def __init__(self, data:str):
        pass

    def parse(self):
        pass

    def create(self):
        self.create_pixels()

        return self.block_origin

    def join(self):
        self.join_pixels()

    def create_pixels(self):
        print("CREATING PIXELS NOW")
        # ensure all of the pixels are created first
        self.block_origin = bpy.data.objects.new( self.display_name, None )
        bpy.context.collection.objects.link(self.block_origin)
        self.block_origin.empty_display_size = 2
        self.block_origin.empty_display_type = 'ARROWS'
        self.block_origin.rotation_mode = "QUATERNION"

        for pixel in self.pixels:
            if self.pixels[pixel].mesh != None:
                bpy.ops.object.delete({"selected_objects": self.pixels[pixel].mesh.mesh})
            
            mesh:N8Mesh = N8Mesh(self.pixels[pixel].model)
            self.pixels[pixel].mesh = mesh
            mesh.set_name(f"Pixel{self.pixels[pixel].id}")

            mat = self.create_material(self.pixels[pixel])
        
        for pixel in self.pixels:
            mesh = self.pixels[pixel].mesh

            # parent the pivot to the parent pivot
            if self.pixels[pixel].parent_id != "0":
                mesh.set_parent(self.pixels[self.pixels[pixel].parent_id].mesh.get_pivot())
            else:
                mesh.set_parent(self.block_origin)

            mesh.set_position(self.pixels[pixel].position)
            mesh.set_offset(self.pixels[pixel].bones["bone02"].position)
            mesh.set_rotation(self.pixels[pixel].rotation)
            mesh.set_local_rotation(self.pixels[pixel].bones["bone02"].rotation)
            mesh.set_scale(self.pixels[pixel].bones["bone02"].scale)

        return self.block_origin
    
    def convert_texture_name(self, name:str):
        image_path = re.sub(r"\.dds$", ".png", name.lower().strip())
        image_path = re.sub(r"\\", "/", image_path)
        return image_path

    def create_particle(self):
        #bpy.ops.object.particle_system_add()
        pass

    def load_texture(self, original_path:str):
        
        path_full = os.path.dirname(os.path.realpath(__file__))

        image_path = self.convert_texture_name(original_path)
        image_path = str(Path(path_full) / "textures" / Path(image_path))
        bpy.data.images.load(image_path, check_existing=True)
        filename = Path(image_path).stem + Path(image_path).suffix
        image = bpy.data.images[filename]
        image.pack()
        return image

    def create_material(self, pixel:N8Pixel):
        mat = pixel.mesh.mesh.active_material
        
        # viewport display in solid modes
        mat.diffuse_color = (pixel.diffuse.r, pixel.diffuse.g, pixel.diffuse.b, pixel.diffuse_alpha)

        # actual shader logic below
        nodes = mat.node_tree.nodes

        node_diffuse = nodes.get("Diffuse")
        node_diffuse.outputs["Color"].default_value = (pixel.diffuse.r, pixel.diffuse.g, pixel.diffuse.b, 1)

        node_diffuse_alpha = nodes.get("DiffuseAlpha")
        node_diffuse_alpha.outputs["Value"].default_value = pixel.diffuse_alpha

        node_diffuse = nodes.get("Emission")
        node_diffuse.outputs["Color"].default_value = (pixel.emission.r, pixel.emission.g, pixel.emission.b, pixel.emission_alpha)

        
        if pixel.diffuse_alpha != 1 or self.is_image_alpha(pixel.texture):
            mat.blend_method = "BLEND"
        else:
            mat.blend_method = 'OPAQUE'
        
        node_texture = nodes.get("ImagePattern")
        node_texture.image = self.load_texture(pixel.texture)
        node_texture.interpolation = 'Closest'


        return mat

    def join_pixels(self):
        meshes = [self.pixels[x].mesh.mesh for x in self.pixels]
        pivots = [self.pixels[x].mesh.pivot for x in self.pixels]

        bpy.ops.object.select_all(action='DESELECT')
        for mesh in meshes:
            mesh.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        ctx_mesh = bpy.context.copy()

        bpy.ops.object.select_all(action='DESELECT')
        for pivot in pivots:
            pivot.select_set(True)
        bpy.context.view_layer.objects.active = pivots[0]
        ctx_pivot = bpy.context.copy()

        bpy.ops.object.select_all(action='DESELECT')

        bpy.ops.object.parent_clear(ctx_mesh, type='CLEAR_KEEP_TRANSFORM')

        for mesh in meshes:
            mesh.parent = self.block_origin

        bpy.ops.object.join(ctx_mesh)
        bpy.ops.object.delete(ctx_pivot)

        temp_cursor_loc = bpy.context.scene.cursor.location
        bpy.context.scene.cursor.location = (0,0,0)
        bpy.ops.object.origin_set(ctx_mesh, type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.context.scene.cursor.location = temp_cursor_loc

        pass

    def is_image_alpha(self, name:str):
        # unfortunately i don't have a way to detect this so i'm just manually specifying
        image_path = self.convert_texture_name(name)
        alpha_tex = [
            "n8/alphasquare.png",
            "n8/squarealpha.png",
            "n8/stainedglass.png",
            "n8/grate.png",
            "n8/grassy.png",
            "n8/grassy2.png",
            "n8/feather.png",
            "n8/ice.png",
            "n8/chibi.png",
            "n8/zombie.png",
            "n8/zoom.png",
            "n8/megajump.png",

            "particles/acircle.png",
            "particles/asquare.png",
            "particles/bat.png",
            "particles/bubble.png",
            "particles/circle.png",
            "particles/cloud.png",
            "particles/fluff.png",
            "particles/gear.png",
            "particles/kapow.png",
            "particles/plus.png",
            "particles/radio.png",
            "particles/skull.png",
            "particles/square.png",
            "particles/star.png",

            "symbols/!.png",
            "symbols/%.png",
            "symbols/@.png",
            "symbols/0.png",
            "symbols/1.png",
            "symbols/2.png",
            "symbols/3.png",
            "symbols/4.png",
            "symbols/5.png",
            "symbols/6.png",
            "symbols/7.png",
            "symbols/8.png",
            "symbols/9.png",
            "symbols/$.png",
            "symbols/a.png",
            "symbols/b.png",
            "symbols/c.png",
            "symbols/d.png",
            "symbols/e.png",
            "symbols/f.png",
            "symbols/g.png",
            "symbols/h.png",
            "symbols/heart.png",
            "symbols/i.png",
            "symbols/j.png",
            "symbols/k.png",
            "symbols/l.png",
            "symbols/lessthan.png",
            "symbols/m.png",
            "symbols/n.png",
            "symbols/num.png",
            "symbols/o.png",
            "symbols/p.png",
            "symbols/q.png",
            "symbols/question.png",
            "symbols/r.png",
            "symbols/s.png",
            "symbols/t.png",
            "symbols/team.png",
            "symbols/teamblue.png",
            "symbols/teamgreen.png",
            "symbols/teamred.png",
            "symbols/u.png",
            "symbols/v.png",
            "symbols/w.png",
            "symbols/x.png",
            "symbols/y.png",
            "symbols/z.png",
        ]
        if image_path in alpha_tex:
            return True
        else:
            return False


class StartData(N8Parser):
    """
    Defines the startdata file format
    """
    def __init__(self, data:str):
        super().__init__(self)

        self.data = data[len("StartData\n"):]

    def parse(self):
        split = self.data.split(sep="~")

        self.display_name = split[0].strip()
        author = split[1].strip()
        filetype = split[2].strip()
        
        print(f"Filetype is {filetype}")

        if filetype.lower() == "block":
            filetype = "stuff"

        if filetype.lower() == "stuff":
            self.block_scale = split[5].strip()
        if filetype.lower() == "monster":
            idk = split[5].strip() # {8000,0} is on fishman; otherwise it's just a blank comma field.....
            self.block_scale = split[6].strip()
        if filetype.lower() == "hat":
            self.block_scale = 1.0
            hold_or_wear = split[5].strip()

            if hold_or_wear.lower() == "false":
                hold_or_wear = "wear"
            elif hold_or_wear.lower() == "0":
                hold_or_wear = "sword" # or hat
            elif hold_or_wear.lower() == "1":
                hold_or_wear = "shield" # or torso
            elif hold_or_wear.lower() == "2":
                hold_or_wear = "gun" # never implemented originally
        
        # there's a bug in n8maker that saves without scale if you don't explicitly set press enter on the field
        # so some of the files don't have it set. the default was 2 i guess.
        if self.block_scale == "":
            self.block_scale = 2.0
        else:
            self.block_scale = float(self.block_scale)

        # the default scale is 2.0 so we divide everything by 2.0
        # since we assume a unit scale of 1 not 2....
        self.block_scale = self.block_scale / 2.0

        self.pixels = self.parse_objects(split[3].strip())
        animations = split[4].strip()
    
    def parse_objects(self, data:str) -> dict:
        pixels = {}

        with io.StringIO(data, newline="\n") as file:
            num_pixels = int(file.readline())

            print(f"Found {num_pixels} pixels to parse in the file")
            
            for pixel_id in range(0, num_pixels):
                pixel = N8Pixel(file.readline().strip())
                pixel.parent_id = file.readline().strip()
                
                # strip out the .tva etc
                pixel.model = Path(file.readline().strip()).stem.lower()

                material_params = file.readline().strip()
                material_params = material_params.split("/")

                diffuse = material_params[0].split(":")
                pixel.diffuse = Color((
                    float(diffuse[0]), float(diffuse[1]), float(diffuse[2])
                ))
                pixel.diffuse_alpha = float(diffuse[3])

                emission = material_params[1].split(":")
                pixel.emission = Color((
                    float(emission[0]), float(emission[1]), float(emission[2])
                ))
                pixel.emission_alpha = float(emission[3])

                # Certain older files don't have the shader specified; assuming false
                if len(material_params) > 2:
                    pixel.shader = material_params[2]
                else:
                    pixel.shader = "False"

                pixel.texture = file.readline().strip()

                position = file.readline().strip()
                position = position.split(":")
                pixel.position = tuple(
                    x*SCALE_CONVERSION*self.block_scale for x in 
                    (float(position[0]), float(position[2]), float(position[1]))
                )

                rotation = file.readline().strip()
                rotation = rotation.split(":")
                # Blender expects WXYZ, but it's stored XYZW?
                    # Y in n8 is up, Z in blender is up, therefore we switch Z and Y
                pixel.rotation = Quaternion((
                    float(rotation[3]), -float(rotation[0]), -float(rotation[2]), -float(rotation[1])
                ))
                # add 90 degrees to the X rotation because lmao fuck this format
                #pixel.rotation += Quaternion((0, 1.0, 0.0), math.radians(90.0))

                scale = file.readline().strip()
                scale = scale.split(":")
                pixel.scale = tuple(
                    PIXEL_SCALE[pixel.model]*x*SCALE_CONVERSION*self.block_scale for x in 
                    (float(scale[0]), float(scale[2]), float(scale[1]))
                )

                num_bones = int(file.readline().strip())

                for bone_id in range(0, num_bones):
                    bone = N8Bone(file.readline().strip())
                    bone_pos = file.readline().strip().split(":")
                    bone_rot = file.readline().strip().split(":")
                    bone_sca = file.readline().strip().split(":")

                    bone.set_position(tuple(
                        x*SCALE_CONVERSION*self.block_scale for x in 
                        (float(bone_pos[0]), float(bone_pos[2]), float(bone_pos[1]))
                    ))
                    # Blender expects WXYZ, but it's stored XYZW?
                    # Y in n8 is up, Z in blender is up, therefore we switch Z and Y
                    bone.set_rotation(
                        Quaternion((
                            float(bone_rot[3]), float(bone_rot[0]), float(bone_rot[2]), float(bone_rot[1])
                        )) 
                        #+ Quaternion((0, 0, 1.0), math.radians(-90.0))
                    )
                    bone.set_scale(tuple(
                        PIXEL_SCALE[pixel.model]*x*SCALE_CONVERSION*self.block_scale for x in 
                        (float(bone_sca[0]), float(bone_sca[2]), float(bone_sca[1]))
                    ))
                    pixel.bones[bone.name] = bone

                pixels[pixel.id] = pixel
            
            num_particles = int(file.readline().strip())

            print(f"Found {num_particles} particles to parse in the file")

            for particle_id in range(0, num_particles):
                print("UNSUPPORTED PARTICLES", particle_id)
        
        return pixels

    


def load(context, filepath:str, scale:float = 1.0, join:bool = False):
    #if mesh_name in MESH_CACHE:
    #    self.mesh = MESH_CACHE[self.mesh_name].copy()
    #    new_obj.data = src_obj.data.copy()
    #    bpy.context.collection.objects.link(self.mesh)

    block_name = Path(filepath).stem
    block = None
    parser = None
    #if block_name in MESH_CACHE:
        #print(f"Found {block_name} in the cache")
        #block = MESH_CACHE[block_name]
        # select block and all children
        #bpy.ops.object.select_all(action='DESELECT')
        #block.select_set(True)
        #bpy.ops.object.select_grouped(type='CHILDREN_RECURSIVE')
        #bpy.context.view_layer.objects.active = block
    #else:
    data, version = load_file(filepath, context)

    if version == "StartData":
        parser = StartData(data)
    elif version == "BEGIN!":
        print("Begin Data!!!")
    else:
        return {'FINISHED'}

    if parser:

        parser.parse()
        block = parser.create()
        if join:
            parser.join()
    
        MESH_CACHE[block_name] = block

    return {'FINISHED'}, block