#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
        name = "gien",
        version = "0.4.1",
        packages = ["gien"],

        install_requires = [
                "PyGithub",
                "markdown",
                "progressbar",
                "pygit2",
                "requests"
        ],

        entry_points = {
                "console_scripts": [
                        "gien = gien:main"
                ]
        },

        author = "Jens John",
        author_email = "jjohn@2ion.de",
        description = "Export Github issue tracker and wiki contents to local email storage",
        license = "GPL3",
        keywords = "github backup cloning migration",
        url = "https://github.com/2ion/gien"
)

