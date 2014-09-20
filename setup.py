from setuptools import setup, find_packages
import sys
from setuptools.command.test import test as TestCommand

import sjson

class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import tox
        errcode = tox.cmdline(self.test_args)
        sys.exit(errcode)

setup(
    name = "SJSON",
    version = sjson.__version__,
    packages = find_packages (exclude=['*.test', 'test.*', '*.test.*']),

    test_suite = 'sjson.test',
    tests_require=['tox'],
    cmdclass = {'test' : Tox},

    install_requires = [],

    author = "Matthäus G. Chajdas",
    author_email = "dev@anteru.net",
    description = "SJSON serializer/deserializer for Python",
    license = "BSD",
    keywords = [],
    url = "http://shelter13.net/projects/SJSON",

    classifiers=[
        'Development Status :: 6 - Mature',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',

    ]
)
