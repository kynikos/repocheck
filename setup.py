# repocheck - Check the status of code repositories under a root directory.
# Copyright (C) 2015 Dario Giovannetti <dev@dariogiovannetti.net>
#
# This file is part of repocheck.
#
# repocheck is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repocheck is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repocheck.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup

setup(
    name='repocheck',
    version='1.0.0',
    description='Check the status of code repositories under a root '
                'directory.',
    long_description='Check the status of code repositories under a root '
                     'directory.',
    author='Dario Giovannetti',
    author_email='dev@dariogiovannetti.net',
    url='https://github.com/kynikos/repocheck',
    license='GPLv3+',
    py_modules=['repocheck', ],
    entry_points={
        'console_scripts': ['repocheck = repocheck:main']
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Version Control',
        'Topic :: Software Development :: Version Control :: Git',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',  # noqa
        'Programming Language :: Python :: 3',
    ],
    keywords='git repository',
)
