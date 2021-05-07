from setuptools import setup, find_packages
import pathlib


def get_version(version_file):
    locls = {}
    exec(open(version_file).read(), {}, locls)
    return locls["__version__"]


here = pathlib.Path(__file__).parent.resolve()
readme_file = here / "README.md"
version_file = here / "src" / "ksl" / "version.py"


setup(
    name="ksl",
    version=get_version(version_file),
    description="Kaleb's S****y LISP",
    long_description=readme_file.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/ktbarrett/ksl",
    author="Kaleb Barrett",
    author_email="dev.ktbarrett@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Software Development :: Compilers",
        "Programming Language :: Lisp",
        "Programming Language :: Python :: 3",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={"ksl": ["py.typed"]},
    python_requires=">=3.6, <4",
    install_requires=[],
    entry_points={},
    zip_safe=False
)
