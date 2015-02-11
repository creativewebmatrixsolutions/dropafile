import os
import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

tests_path = os.path.join(os.path.dirname(__file__), 'tests')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        args = sys.argv[sys.argv.index('test')+1:]
        self.test_args = args
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

tests_require = [
    'pytest >= 2.0.3',
    'pytest-xdist',
    'pytest-cov',
    ]

docs_require = [
    'Sphinx',
    ]

setup(
    name="dropafile",
    version="0.1.dev0",
    author="Uli Fouquet",
    author_email="uli@gnufix.de",
    description=(
        "Drop me a file on a webpage."),
    license="MIT",
    keywords="web drop file wsgi",
    url="https://github.com/ulif/dropafile/",
    py_modules=['dropafile', ],
    packages=[],
    namespace_packages=[],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: CGI Tools/Libraries",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    tests_require=tests_require,
    extras_require=dict(
        tests=tests_require,
        docs=docs_require,
        ),
    cmdclass={'test': PyTest},
    entry_points={
        'console_scripts': [
            # 'dropafile = dropafile:main',
        ]
        }
)
