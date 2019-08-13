import io

import grin
from setuptools import setup

# Read the long description from the README.txt
with io.open("README.rst", "rt") as f:
    long_description = f.read()


setup(
    name="grin3",
    version=grin.__version__,
    author=grin.__author__,
    author_email=grin.__author_email__,
    maintainer=grin.__maintainer__,
    maintainer_email=grin.__maintainer_email__,
    description="A grep program configured the way I like it. (python3 port)",
    long_description=long_description,
    license="BSD",
    url="https://bitbucket.org/rsalmaso/grin3",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Utilities",
    ],
    py_modules=["grin"],
    entry_points=dict(
        console_scripts=["grin = grin:grin_main", "grind = grin:grind_main"]
    ),
    tests_require=["nose >= 0.10"],
    test_suite="nose.collector",
)
