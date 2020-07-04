import os, io
import bpy
from pathlib import Path
from mathutils import Color, Quaternion

SCALE_CONVERSION:float = 1.0/100.0

class CellBlock:
    mesh_name = None
    mesh = None
    name = None
    position = None
    rotation = None

    def __init__(self, mesh_name, name, position, rotation):
        self.mesh_name = mesh_name
        self.name = name
        self.position = position
        self.rotation = rotation

    def __repr__(self):
        return f"mesh_name: {self.mesh_name} | name: {self.name} | position: {self.position} | rotation: {self.rotation}"

    def load_mesh(self, context):
        from . import import_n8png

        filepath = os.path.dirname(os.path.realpath(__file__))
        filepath = str(Path(filepath) / "data" / "Stuff" / self.mesh_name) + ".png"
        result, block = import_n8png.load(context, filepath)

        if block:
            self.mesh = block
            self.mesh.location = self.position
            self.mesh.rotation_quaternion = self.rotation
            return True
        else:
            return False

    def set_parent(self, parent):
        self.mesh.parent = parent.mesh
        self.mesh.location = self.position
        self.mesh.rotation_quaternion = self.rotation

class N8Cell:
    blocks = None
    tronics = None

    def __init__(self):
        self.blocks = {}
        self.tronics = {}

    def add_block(self, index, block):
        self.blocks[index] = block

    def load(self, context, filepath):
        current_parse = "blocks"
        with open(filepath, mode='r', errors='ignore') as n8file:
            for line in n8file:
                stripped = line.strip()

                if stripped == "tronics":
                    current_parse = stripped
                    continue
                if stripped == "attach":
                    current_parse = stripped
                    continue
                if stripped == "wire":
                    current_parse = stripped
                    continue

                if current_parse == "blocks":
                    block, index = self.parse_block(stripped)
                    if block.load_mesh(context):
                        block.mesh.name = f"{index} - {block.mesh_name}"
                
                if current_parse =="attach":
                    self.parse_attach(stripped)

                if current_parse == "tronics":
                    pass
                    
                if current_parse == "wire":
                    pass

    def parse_block(self, block_line):
        # 185:landmega:landmega:-1600,0,1600:0.7071068,1.545522E-08,-0.7071067,1.545522E-08:0
        split = block_line.split(sep=":")
        index = split[0]
        mesh_name = split[1]
        name = split[2]
        position = split[3].split(sep=",")
        position = tuple(
            x*SCALE_CONVERSION for x in 
            (float(position[0]), float(position[2]), float(position[1]))
        )
        rotation = split[4].split(sep=",")
        rotation = Quaternion((
            float(rotation[0]), -float(rotation[1]), -float(rotation[3]), -float(rotation[2])
        ))

        # the 5th index won't always exist and i think it's shader, for like null blocks

        b = CellBlock(
            mesh_name, name,
            position, rotation
        )
        self.add_block(index, b)

        return b, index

    def parse_attach(self, data:str):
        #377952:377948
        split = data.split(sep=":")
        child = split[0]
        parent = split[1]

        if child in self.blocks and parent in self.blocks:
            self.blocks[child].set_parent(self.blocks[parent])
        else:
            print(f"Tried to attach {child} to {parent} but one of them didn't exist?")


    def parse_tronic(self, data:str):
        pass

    def parse_wire(self, data:str):
        pass

def load(context, filepath:str, scale:float = 1.0):
    cell = N8Cell()
    cell.load(context, filepath)