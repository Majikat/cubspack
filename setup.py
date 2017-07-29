# -*- coding: utf-8 -*-
# Copyright 2017 Majikat

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup

long_description = """A collection of heuristic algorithms for solving the 3D
knapsack problem, also known as the bin packing problem. In essence packing a
set of cuboids into the smallest number of bins."""

setup(
    name='cubspack',
    version='0.1',
    description=long_description,

    # Main homepage
    url='https://github.com/Majikat/cubspack',

    # Extra info and author details
    author='Majikat',

    keywords=['knapsack', 'cuboid', 'packing 3D', 'bin', 'binpacking'],

    license='GPLv2',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
    ],

    # package
    packages=['cubspack'],
    install_requires=['nose', 'unittest2'],
    zip_safe=False,

    # Tests
    test_suite='nose.collector',
    tests_require=['nose'],
)
