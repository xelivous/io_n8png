# io_n8png

This is an import plugin for Blender that implements the Neverdaunt:8Bit* PNG model format.

I plan to eventually support ncd (the cell file format) as well for loading full scenes since it's not that much additional work.

The included `librarypixel.blend` is used as a model library for when the blocks find meshes they need, instead of the alternative of manually specify the data in the code directly. Additional mesh presets can be created by just creating a root level mesh with the name of your choice. Currently only tpixel and pixel2 are in there. You can change the tpixel and pixel2 to be any shape you want and it will change the resulting imported objects (for example, monkeys instead of cubes).

Most of this code is just haphazardly thrown about since it took a while to remember how this file format worked so i'll likely refactor it a ton in the upcoming commits.

## Extra Data Files + License Stuff

I put the code itself under MIT but everything else is unlicensed.

I've included most of the data, saves, and textures from the game that i was aware of for testing and so you don't have to supply them yourself. They're licensed under whatever they're licensed under, and there's no guarantee you can use any of the models generated from this tool for anything else without getting the permission of the creator of N8*. I personally made a lot of the models and i'm fine with them being re-used wherever, but i didn't make most of the textures.

## Implemented Features

* Able to load hats/stuff/monsters in the StartData format, assuming they only use pixel2 and tpixel
* Option to join the imported pixels into a single mesh automatically instead of having to manually select them
    * By default they're all parented to pivot points for easy editing, similar to their representations in the maker
    * I don't actually expose this option in the plugin at the moment; it's just commented out near the bottom of import_n8png.py

## Planned Features

* Re-use materials of the same color/texture so there's not a bunch of duplicate textures.
* Implement an atlas and pallete map so that there's only 1 material per imported model.
    * Most engines support 2 UV maps although you usually have to create a custom shader yourself to utilize them both properly, so i'll likely implement it that way. I have basic support for palettes in the `librarypixel.blend` as a test but it's a little janky.
    * Would be useful to add roughness/emission/specular mapping to the textures as well which could use the first UV map.

## Currently Unsupported Features

* `Begin Data` format
    * Most of the items use the `StartData` format, so this mostly affects the mine block pack and everything made around that time.
    * Requires just subclassing a new parser and providing the correct data.
* `Pixel.tva` 
    * `Pixel.tva` can be converted to `pixel2.tva` using my old n8convert program
    * i'll look into implementing that old convert program into this import plugin at a later date.
* `Normish.tva` (both of them)
    * This is the model file for the player character which can be referenced as an actual model and posed inside of the maker
    * i'll need to recreate it along with handle all of the bone information. Will likely require a lot of refactoring to do so.
* Team items/blocks
    * Team colors/etc are unsupported
    * Team blocks usually reference the `hat` png models as actual textures but it can't find them since I don't include them by default, so it just errors out.
* Particles
    * skipped at the moment since i'm not all too familiar with blender's particle system to be able to properly convert them.
    * Not sure how much use they'd be when exporting to gltf/etc for use in game engines in the first place since most have their own systems.
* Animations
    * N8 animations work by assuming there's a bone for every individual `pixel` and then saving their state each frame
    * Will need to add a skeleton and bones for each pixel then assign the pixels to the bones
    * Will also need to add all of the animation actions