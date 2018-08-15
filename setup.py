#!/usr/bin/env python
"""Create setup script for pip installation"""
########################################################################
# File: setup.py
#  executable: setup.py
#
# Author: Andrew Bailey
# History: Created 08/12/18
########################################################################

import sys
from timeit import default_timer as timer
from setuptools import setup


def main():
    """Main docstring"""
    start = timer()

    setup(
        name="robinhood2quicken",
        version='0.0.1',
        description='Download and convert dividend and trade information into a csv document which can be imported '
                    'into Mac Quicken 2018',
        url='https://github.com/adbailey4/Robinhood2Quicken',
        author='Andrew Bailey',
        author_email='bailey.andrew4@gmail.com',
        packages=['robinhood2quicken'],
        install_requires=["numpy>=1.9.2",
                          "pip>=9.0.1"],
        zip_safe=True
    )

    stop = timer()
    print("setup.py took {} seconds".format(stop-start), file=sys.stderr)


if __name__ == "__main__":
    main()
    raise SystemExit
