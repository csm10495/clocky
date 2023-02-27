import pathlib
import sys

from setuptools import setup

THIS_FOLDER = pathlib.Path(__file__).parent
MODULE_FOLDER = THIS_FOLDER / THIS_FOLDER.name

sys.path.append(str(MODULE_FOLDER))

from __init__ import __version__

req = ["psutil"]

setup(
    name="clocky",
    author="csm10495",
    author_email="csm10495@gmail.com",
    url="http://github.com/csm10495/clocky",
    version=__version__,
    packages=["clocky"],
    license="MIT License",
    python_requires=">=3.8",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    entry_points={"console_scripts": ["clocky = clocky.__main__:main"]},
    include_package_data=True,
    install_requires=req,
)
