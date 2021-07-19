## laymix - utility to mix image layers into all possible results
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

from os import listdir, makedirs
from os.path import isfile, isdir, join, splitext, basename, dirname
from PIL import Image
from itertools import product
from dataclasses import dataclass
import logging

log = logging.getLogger(__name__)


@dataclass
class ImageParts:
    name: str
    image: str
    parts: dict


class LayerMixer:
    def __init__(self, prefixes: list, savedir: str):
        self.prefixes = prefixes
        self.savedir = savedir
        makedirs(self.savedir, exist_ok=True)

    def get_files(self, pathtodir: str) -> list:
        """Get list of files in directory"""
        files = []
        if isfile(pathtodir):
            log.debug(f"{pathtodir} itself is a file, returning")
            files.append(pathtodir)
            return files

        log.debug(f"Attempting to parse directory {pathtodir}")
        directory_content = listdir(pathtodir)
        log.debug(f"Uncategorized content inside is: {directory_content}")

        for item in directory_content:
            log.debug(f"Processing {item}")
            itempath = join(pathtodir, item)
            if isdir(itempath):
                log.debug(f"{itempath} leads to directory, processing its content")
                # looping over this very function for all subdirectories
                files += self.get_files(itempath)
            else:
                # assuming that everything that isnt directory is file
                log.debug(f"{itempath} leads to file, adding to list")
                files.append(itempath)

        log.debug(f"Got following files in total: {files}")
        return files

    def filter_by_mask(self, files: list, mask: str, exact_match: bool = False) -> list:
        """Get items that has provided mask in them"""
        filtered = []

        for item in files:
            # TODO: maybe make case-insensetivity an option
            item_name = str(item).lower()
            mask = mask.lower()
            if exact_match:
                if (item_name == mask) or (splitext(item_name)[0] == mask):
                    filtered.append(item)
                continue
            if mask in item_name:
                filtered.append(item)

        log.debug(f"Got following items matching mask {mask}: {filtered}")
        return filtered

    def make_constructors(
        self, files: list, include_background: bool = False
    ) -> ImageParts:
        """Create image constructors to use with self.build_images()"""
        raw_items = {}
        for prefix in self.prefixes:
            items = self.filter_by_mask(
                files=files,
                mask=prefix,
            )
            raw_items[prefix] = items

        backgrounds = []
        for f in files:
            exists = False

            for part in raw_items:
                if f in raw_items[part]:
                    exists = True
                    break

            if not exists:
                log.debug(f"Threating {f} as background")
                backgrounds.append(f)

        constructors = []
        for item in backgrounds:
            pic_name = basename(splitext(item)[0])
            pic_parts = {}
            valid_parts_counter = 0
            for part in raw_items:
                items = self.filter_by_mask(
                    files=raw_items[part],
                    mask=pic_name,
                )
                pic_parts[part] = items
                if items:
                    valid_parts_counter += 1

            if not valid_parts_counter:
                log.warning(f"{item} doesnt seem to have any layers, skipping")
                continue

            if include_background:
                for part in pic_parts:
                    pic_parts[part].append(None)

            image_constructor = ImageParts(
                name=pic_name,
                image=item,
                parts=pic_parts,
            )

            constructors.append(image_constructor)

        log.debug(f"Got following image constructors: {constructors}")
        return constructors

    def build_images(self, constructor: ImageParts) -> list:
        """Build all possible image variants out of provided constructor"""
        log.debug(f"Building {constructor.name}")

        def add_image_layer(image, layer):
            img = Image.alpha_composite(image, layer)
            return img

        images = []

        background = Image.open(constructor.image)

        img_parts = []
        for part in constructor.parts:
            # fixing issue with product returning [] on non-existing lists
            if constructor.parts[part]:
                img_parts.append(constructor.parts[part])

        # getting all possible parts variations:
        variations = list(product(*img_parts))

        for sequence in variations:
            layered_img = background
            for path in sequence:
                if not path:
                    continue

                layer = Image.open(path)
                layered_img = add_image_layer(layered_img, layer)

            images.append(layered_img)

        log.debug(f"Got {len(images)} images total")

        return images

    def save(self, images: list, name_mask: str, close_after_done: bool = True):
        """Save specified images on disk"""
        for number, item in enumerate(images):
            filepath = join(self.savedir, f"{name_mask}_{number}")
            filename = f"{filepath}.png"
            item.save(filename)
            log.debug(f"Successfully saved {filename} to disk")
            if close_after_done:
                item.close()
