# LayMix

## Description:

**LayMix** - cli utility to mix image layers into all possible results. It should
be useful for artists who need to produce few slightly-different versions of same
image (say, same character but with different hairstyles). Originally I've made
it for some web visual novel, but then I've got permission to release the sources
and further extend it.

## Image Requirements:

- All images must have the same (x, y) size
- All images must be in png (for now).
- Images that represent layers must have transparent background
- All images (for now) must follow same naming convention, in order to automatically
distinguish layers (see "Usage")

## Dependencies:

- Pillow==8.2.0

## Installation:

- `pip install -r requirements.txt`

## Usage:

- Open terminal of your choice in tool's directory
- `laymix_cli --prefixes first_layer second_layer third_layer` (and so on)
Where "{number}_layer" is either full name of layer or part of it.
You can optionally pass `path_to_dir_with_images` before --prefixes - then tool
will look for specific place where your files are located. Else it attempts to
search for images in "./images" directory.
Passing `--savedir path_to_dir` will set custom directory to save images into.
Default is "./results"

Say, you have image with character's head drawn on it. And you want final images
to have all custom hairstyles and facial expessions you've made. For this task,
you will need (aside from base image) 2 image groups: one for hairs, other for
facial expressions.
You save these layers as separate images and name them like that:
`{background}_{name_of_layer}_{number}.png` (without brakes)
In case of our example, your images directory should look like that:
`lilu.png`
`lilu_face_1.png`
`lilu_face_2.png`
`lilu_face_3.png`
`lilu_hair_1.png`
`lilu_hair_2.png`
and so on.

Then you run tool like `./laymix_cli --prefixes face hair`
If everything has been done correctly - you will get 6 different images in
"results" directory.
But what if original image has already included some hair or facial expression?
Just add `--include-background` after command above - and you will keep them all
(and amount of generated images will (in case of our example) increase to 11)

## License:

[GPLv3](LICENSE)

This **only affects this utility itself and not projects you use it in** - you
are free to produce pics under whatever license you want and use them in whatever
projects you want, will they be FOSS or proprietary
