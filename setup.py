# -*- coding: utf-8 -*-
#
# This file is part of REANA.
# Copyright (C) 2017, 2018, 2019, 2020 CERN.
#
# REANA is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""REANA-Workflow-Engine-Yadage."""

from __future__ import absolute_import, print_function

import os
import re

from setuptools import find_packages, setup

readme = open("README.rst").read()
history = open("CHANGES.rst").read()

tests_require = [
    "pytest-reana>=0.7.2,<0.8.0",
]

extras_require = {
    "debug": ["wdb", "ipdb", "Flask-DebugToolbar",],
    "docs": ["Sphinx>=1.5.1", "sphinx-rtd-theme>=0.1.9",],
    "tests": tests_require,
    "jq": ["jq==0.1.7",],
}

extras_require["all"] = []
for key, reqs in extras_require.items():
    if ":" == key[0]:
        continue
    extras_require["all"].extend(reqs)


setup_requires = [
    "pytest-runner>=2.7",
]

install_requires = [
    "adage==0.10.1",  # FIXME remove once yadage-schemas solves yadage deps.
    "graphviz>=0.12",  # FIXME needed only if yadage visuale=True.
    "networkx==1.11",
    "packtivity==0.14.21",
    "pydot2>=1.0.33",  # FIXME needed only if yadage visuale=True.
    "pydotplus>=2.0.2",  # FIXME needed only if yadage visuale=True.
    "pygraphviz>=1.5",  # FIXME needed only if yadage visuale=True.
    "pyOpenSSL==19.0.0",  # FIXME remove once yadage-schemas solves deps.
    "reana-commons>=0.7.5,<0.8.0",
    "requests==2.22.0",
    "rfc3987==1.3.8",  # FIXME remove once yadage-schemas solves yadage deps.
    "strict-rfc3339==0.7",  # FIXME remove once yadage-schemas solves deps.
    "yadage==0.20.1",
    "yadage-schemas==0.10.6",
    "webcolors==1.9.1",  # FIXME remove once yadage-schemas solves yadage deps.
    "checksumdir>=1.1.4,<1.2",
    "mock>=3.0,<4",
]

packages = find_packages()


# Get the version string. Cannot be done with import!
with open(os.path.join("reana_workflow_engine_yadage", "version.py"), "rt") as f:
    version = re.search(r'__version__\s*=\s*"(?P<version>.*)"\n', f.read()).group(
        "version"
    )

setup(
    name="reana-workflow-engine-yadage",
    version=version,
    description=__doc__,
    long_description=readme + "\n\n" + history,
    author="REANA",
    author_email="info@reana.io",
    url="https://github.com/reanahub/reana-workflow-engine-yadage",
    packages=["reana_workflow_engine_yadage",],
    zip_safe=False,
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "run-yadage-workflow="
            "reana_workflow_engine_yadage.cli:run_yadage_workflow",
        ]
    },
    extras_require=extras_require,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
