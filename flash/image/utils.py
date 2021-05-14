from typing import List, Tuple, Union

from flash.core.utilities.imports import _IMAGE_AVAILABLE

if _IMAGE_AVAILABLE:
    from PIL import Image
else:

    class Image:
        Image = None


def pil_loader(sample: Union[List, Tuple, str]) -> Union[Image.Image, list]:
    # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)

    if isinstance(sample, (tuple, list)):
        path = sample[0]
        sample = list(sample)
    else:
        path = sample

    with open(path, "rb") as f, Image.open(f) as img:
        img = img.convert("RGB")

    if isinstance(sample, list):
        sample[0] = img
        return sample

    return img
