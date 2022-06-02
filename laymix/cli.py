## laymix - utility to generate Cartesian products from sample of image data.
## Copyright (c) 2021 moonburnt
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see https://www.gnu.org/licenses/gpl-3.0.txt

import argparse
import laymix
from os.path import join
from sys import exit
import logging

SAVEDIR = join(".", "results")
IMGDIR = join(".", "images")

log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt="[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
handler.setFormatter(formatter)
log.addHandler(handler)

ap = argparse.ArgumentParser()
ap.add_argument(
    "items",
    nargs="*",
    help=(
        "Path(s) to process images from. If not set - will use "
        f"default path, which is {IMGDIR}"
    ),
)
ap.add_argument(
    "--savedir",
    help=(f"Directory to save results into. Default: {SAVEDIR}"),
)
ap.add_argument(
    "--prefixes",
    nargs="+",
    help=(
        "Prefixes used to split received images into layer groups."
        "Mask isnt regexp, but text that should be in file name."
    ),
    required="True",
)
ap.add_argument(
    "--include-background",
    action="store_true",
    help=(
        "If enabled, backgrounds will be also threated as 1st "
        "layer and added into constructors. Default = False"
    ),
)
ap.add_argument(
    "--debug",
    action="store_true",
    help="Show debug messages in log",
)
ap.add_argument(
    "--apply-to-all",
    action="store_true",
    help="Toggle ability to apply layers to all images",
)
ap.add_argument(
    "--exact-match",
    action="store_true",
    help="Toggle ability to only use layers with names matching prefixes exactly",
)
ap.add_argument(
    "--keep-names",
    action="store_true",
    help=("Toggle ability to include unique name parts of layers into final image."),
)
ap.add_argument(
    "--delimeter",
    nargs="?",
    const=1,
    default="_",
    type=str,
    help=(
        "Symbol that will be used to split name of background and mask in final "
        "image. Default - '_'"
    ),
)

args = ap.parse_args()
# TODO: maybe add ability to specify layer's files manually

if args.debug:
    log.setLevel(logging.DEBUG)

# TODO: add ability to specify prefixes in some sort of config file
prefixes = args.prefixes
log.debug(f"Got following prefixes to parse: {prefixes}")

mixer = laymix.LayerMixer(
    prefixes=prefixes,
    savedir=(args.savedir or SAVEDIR),
)
items = args.items or [IMGDIR]

files = []
for item in items:
    valid_files = mixer.get_files(item)
    files.extend(valid_files)

if not files:
    log.critical("Got no images! Run this tool with -h arg to find how to use it")
    exit(1)

log.info("Sorting images into layer groups by filenames")
constructors = mixer.make_constructors(
    files=files,
    include_background=args.include_background,
    ignore_masks=args.apply_to_all,
    exact_match=args.exact_match,
)

if not constructors:
    log.critical("None of provided images match provided prefixes!")
    exit(1)

log.info("Building images (it may take some time)")
img_amount = 0
for item in constructors:
    img_amount += mixer.build_images(
        constructor=item,
        keep_names=args.keep_names,
        delimeter=args.delimeter,
    )

log.info(f"Laymix has finished its work: made {img_amount} images total")
