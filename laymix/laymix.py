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
        # avoiding the issue with invalid directory path
        try:
            directory_content = listdir(pathtodir)
        except Exception as e:
            log.error(f"Unable to process {pathtodir}: {e}")
            directory_content = []

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
            item_name = str(basename(item)).lower()
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
        self,
        files: list,
        include_background: bool = False,
        ignore_masks: bool = False,
        exact_match: bool = False,
    ) -> ImageParts:
        """Create image constructors to use with self.build_images()"""
        # Determining if certain images are prefixes, based on their names
        raw_items = {}
        for prefix in self.prefixes:
            items = self.filter_by_mask(
                files=files,
                mask=prefix,
                exact_match=exact_match,
            )
            raw_items[prefix] = items

        # Determining if certain images are backgrounds or layers, based on if
        # their names are in prefixes storage or not. Probably possible to do
        # with listcomp in way prettier manner, but for now it will do #TODO
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

        # Creating image constructors - storages of images that have layers to add
        constructors = []
        for item in backgrounds:
            pic_name = basename(splitext(item)[0])
            pic_parts = {}
            valid_parts_counter = 0
            for part in raw_items:
                # making it possible to add layers (say, watermark) to all imgs
                # for now its only done globally - maybe I should add per-prefix
                # toggle for that? #TODO
                if ignore_masks:
                    items = [i for i in raw_items[part] if (i != item)]
                    pic_parts[part] = items
                else:
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

    def build_images(self, constructor: ImageParts) -> int:
        """Build all possible image variants out of provided constructor"""
        log.debug(f"Building {constructor.name}")

        img_parts = []
        for part in constructor.parts:
            # fixing issue with product returning [] on non-existing lists
            if constructor.parts[part]:
                img_parts.append(constructor.parts[part])

        # getting all possible parts variations:
        variations = list(product(*img_parts))

        # dumping layer images into storage to avoid reopening
        layer_imgs = {}
        for part in img_parts:
            for path in part:
                # doing this to avoid crash with --include-background flag,
                # since it adds None object as one of valid parts
                if path:
                    layer_imgs[path] = Image.open(path)

        img_counter = -1
        with Image.open(constructor.image) as background:
            for sequence in variations:
                layered_img = background
                for path in sequence:
                    # same as the comment above
                    if not path:
                        continue
                    layered_img = Image.alpha_composite(layered_img, layer_imgs[path])

                img_counter += 1
                filepath = join(self.savedir, f"{constructor.name}_{img_counter}")
                # #TODO: add support for other save formats
                filename = f"{filepath}.png"
                layered_img.save(filename)
                layered_img.close()

        # closing layers - there is no point in keeping them in memory
        for key in list(layer_imgs):
            layer_imgs[key].close()

        # increasing by 1 coz first img was 0
        img_counter += 1
        log.debug(f"{constructor.name} has made {img_counter} images total")

        return img_counter
