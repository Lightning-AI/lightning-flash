#!/usr/bin/env python
import os

# Always prefer setuptools over distutils
from setuptools import find_packages, setup

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

# https://packaging.python.org/guides/single-sourcing-package-version/
# http://blog.ionelmc.ro/2014/05/25/python-packaging/

PATH_ROOT = os.path.dirname(__file__)
builtins.__LIGHTNING_FLASH_SETUP__ = True

import pl_flash  # noqa: E402


def _load_requirements(path_dir: str = PATH_ROOT, comment_char: str = "#") -> str:
    with open(os.path.join(path_dir, "requirements", "install.txt"), "r") as file:
        lines = [ln.strip() for ln in file.readlines()]
    reqs = [ln[: ln.index(comment_char)] if comment_char in ln else ln for ln in lines]
    reqs = [ln for ln in reqs if ln]
    return reqs


def _load_long_describtion() -> str:
    # https://github.com/PyTorchLightning/pytorch-lightning/raw/master/docs/source/_images/lightning_module/pt_to_pl.png
    url = os.path.join(pl_flash.__homepage__, "raw", pl_flash.__version__, "docs")
    text = open("README.md", encoding="utf-8").read()
    # replace relative repository path to absolute link to the release
    text = text.replace("](docs", f"]({url}")
    # SVG images are not readable on PyPI, so replace them  with PNG
    text = text.replace(".svg", ".png")
    return text


# https://packaging.python.org/discussions/install-requires-vs-requirements /
# keep the meta-data here for simplicity in reading this file... it's not obvious
# what happens and to non-engineers they won't know to look in init ...
# the goal of the project is simplicity for researchers, don't want to add too much
# engineer specific practices
setup(
    name="pytorch-lightning-flash",
    version=pl_flash.__version__,
    description=pl_flash.__docs__,
    author=pl_flash.__author__,
    author_email=pl_flash.__author_email__,
    url=pl_flash.__homepage__,
    download_url="https://github.com/PyTorchLightning/pytorch-lightning-flash",
    license=pl_flash.__license__,
    packages=find_packages(exclude=["tests", "docs"]),
    long_description=_load_long_describtion(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    zip_safe=False,
    keywords=["deep learning", "pytorch", "AI"],
    python_requires=">=3.6",
    setup_requires=[],
    install_requires=_load_requirements(PATH_ROOT),
    project_urls={
        "Bug Tracker": "https://github.com/PyTorchLightning/pytorch-lightning-flash/issues",
        "Documentation": "https://pytorch-lightning-flash.rtfd.io/en/latest/",
        "Source Code": "https://github.com/PyTorchLightning/pytorch-lightning-flash",
    },
    classifiers=[
        "Environment :: Console",
        "Natural Language :: English",
        # How mature is this project? Common values are
        #   3 - Alpha, 4 - Beta, 5 - Production/Stable
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Scientific/Engineering :: Information Analysis",
        # Pick your license as you wish
        # 'License :: OSI Approved :: BSD License',
        "Operating System :: OS Independent",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
