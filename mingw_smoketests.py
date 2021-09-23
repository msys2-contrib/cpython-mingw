#!/usr/bin/env python3
# Copyright 2017 Christoph Reiter
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""The goal of this test suite is collect tests for update regressions
and to test msys2 related modifications like for path handling.
Feel free to extend.
"""

import os
import unittest
import sysconfig

if "MSYSTEM" in os.environ:
    SEP = "/"
else:
    SEP = "\\"

_UCRT = "clang" in sysconfig.get_platform() or "ucrt" in sysconfig.get_platform()


class Tests(unittest.TestCase):

    def test_zoneinfo(self):
        # https://github.com/msys2-contrib/cpython-mingw/issues/32
        import zoneinfo
        self.assertTrue(any(os.path.exists(p) for p in zoneinfo.TZPATH))
        zoneinfo.ZoneInfo("America/Sao_Paulo")

    def test_userdir_path_sep(self):
        # Make sure os.path and pathlib use the same path separators
        from unittest import mock
        from os.path import expanduser
        from pathlib import Path

        profiles = ["C:\\foo", "C:/foo"]
        for profile in profiles:
            with mock.patch.dict(os.environ, {"USERPROFILE": profile}):
                self.assertEqual(expanduser("~"), os.path.normpath(expanduser("~")))
                self.assertEqual(str(Path("~").expanduser()), expanduser("~"))
                self.assertEqual(str(Path.home()), expanduser("~"))

    def test_sysconfig_schemes(self):
        # https://github.com/msys2/MINGW-packages/issues/9319
        import sysconfig
        from distutils.dist import Distribution
        from distutils.command.install import install

        names = ['scripts', 'purelib', 'platlib', 'data', 'include']
        for scheme in ["nt", "nt_user"]:
            for name in names:
                c = install(Distribution({"name": "foobar"}))
                c.user = (scheme == "nt_user")
                c.finalize_options()
                if name == "include":
                    dist_path = os.path.dirname(getattr(c, "install_" + "headers"))
                else:
                    dist_path = getattr(c, "install_" + name)
                sys_path = sysconfig.get_path(name, scheme)
                self.assertEqual(dist_path, sys_path, (scheme, name))

    def test_ctypes_find_library(self):
        from ctypes.util import find_library
        from ctypes import cdll
        self.assertTrue(cdll.msvcrt)
        if _UCRT:
            self.assertIsNone(find_library('c'))
        else:
            self.assertEqual(find_library('c'), 'msvcrt.dll')

    def test_ctypes_dlopen(self):
        import ctypes
        import sys
        self.assertEqual(ctypes.RTLD_GLOBAL, 0)
        self.assertEqual(ctypes.RTLD_GLOBAL,  ctypes.RTLD_LOCAL)
        self.assertFalse(hasattr(sys, 'setdlopenflags'))
        self.assertFalse(hasattr(sys, 'getdlopenflags'))
        self.assertFalse([n for n in dir(os) if n.startswith("RTLD_")])

    def test_time_no_unix_stuff(self):
        import time
        self.assertFalse([n for n in dir(time) if n.startswith("clock_")])
        self.assertFalse([n for n in dir(time) if n.startswith("CLOCK_")])
        self.assertFalse([n for n in dir(time) if n.startswith("pthread_")])
        self.assertFalse(hasattr(time, 'tzset'))

    def test_strftime(self):
        import time
        with self.assertRaises(ValueError):
            time.strftime('%Y', (12345,) + (0,) * 8)

    def test_sep(self):
        self.assertEqual(os.sep, SEP)

    def test_module_file_path(self):
        import asyncio
        import zlib
        self.assertEqual(zlib.__file__, os.path.normpath(zlib.__file__))
        self.assertEqual(asyncio.__file__, os.path.normpath(asyncio.__file__))

    def test_importlib_frozen_path_sep(self):
        import importlib._bootstrap_external
        self.assertEqual(importlib._bootstrap_external.path_sep, SEP)

    def test_os_commonpath(self):
        self.assertEqual(
            os.path.commonpath(
                [os.path.join("C:", os.sep, "foo", "bar"),
                 os.path.join("C:", os.sep, "foo")]),
                 os.path.join("C:", os.sep, "foo"))

    def test_pathlib(self):
        import pathlib

        p = pathlib.Path("foo") / pathlib.Path("foo")
        self.assertEqual(str(p), os.path.normpath(p))

    def test_modules_import(self):
        import sqlite3
        import ssl
        import ctypes
        import curses

    def test_c_modules_import(self):
        import _decimal

    def test_socket_inet_ntop(self):
        import socket
        self.assertTrue(hasattr(socket, "inet_ntop"))

    def test_socket_inet_pton(self):
        import socket
        self.assertTrue(hasattr(socket, "inet_pton"))

    def test_multiprocessing_queue(self):
        from multiprocessing import Queue
        Queue(0)

    #def test_socket_timout_normal_error(self):
    #    import urllib.request
    #    from urllib.error import URLError

    #    try:
    #        urllib.request.urlopen(
    #            'http://localhost', timeout=0.0001).close()
    #    except URLError:
    #        pass

    def test_threads(self):
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(1) as pool:
            for res in pool.map(lambda *x: None, range(10000)):
                pass

    def test_sysconfig(self):
        import sysconfig
        # This should be able to execute without exceptions
        sysconfig.get_config_vars()

    def test_sqlite_enable_load_extension(self):
        # Make sure --enable-loadable-sqlite-extensions is used
        import sqlite3
        self.assertTrue(sqlite3.Connection.enable_load_extension)

    def test_venv_creation(self):
        import tempfile
        import venv
        import subprocess
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            builder = venv.EnvBuilder()
            builder.create(tmp)
            assert os.path.exists(os.path.join(tmp, "bin", "activate"))
            assert os.path.exists(os.path.join(tmp, "bin", "python.exe"))
            assert os.path.exists(os.path.join(tmp, "bin", "python3.exe"))
            subprocess.check_call([shutil.which("bash.exe"), os.path.join(tmp, "bin", "activate")])

    def test_has_mktime(self):
        from time import mktime, gmtime
        mktime(gmtime())

    def test_platform_things(self):
        import sys
        import sysconfig
        import platform
        import importlib.machinery
        self.assertEqual(sys.implementation.name, "cpython")
        self.assertEqual(sys.platform, "win32")
        self.assertTrue(sysconfig.get_platform().startswith("mingw"))
        self.assertTrue(sysconfig.get_config_var('SOABI').startswith("cpython-"))
        ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
        self.assertTrue(ext_suffix.endswith(".pyd"))
        self.assertTrue("mingw" in ext_suffix)
        self.assertEqual(sysconfig.get_config_var('SHLIB_SUFFIX'), ".pyd")
        ext_suffixes = importlib.machinery.EXTENSION_SUFFIXES
        self.assertTrue(ext_suffix in ext_suffixes)
        self.assertTrue(".pyd" in ext_suffixes)
        self.assertEqual(sys.winver, ".".join(map(str, sys.version_info[:2])))
        self.assertEqual(platform.python_implementation(), "CPython")
        self.assertEqual(platform.system(), "Windows")
        self.assertTrue(isinstance(sys.api_version, int) and sys.api_version > 0)

    def test_c_ext_build(self):
        import tempfile
        import sys
        import subprocess
        import textwrap
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmppro:
            subprocess.check_call([sys.executable, "-m", "ensurepip", "--user"])
            with Path(tmppro, "setup.py").open("w") as f:
                f.write(
                    textwrap.dedent(
                        """\
                                    from setuptools import setup, Extension

                                    setup(
                                        name='cwrapper',
                                        version='1.0',
                                        ext_modules=[
                                            Extension(
                                                'cwrapper',
                                                sources=['cwrapper.c']),
                                        ],
                                    )
                                """
                    )
                )
            with Path(tmppro, "cwrapper.c").open("w") as f:
                f.write(
                    textwrap.dedent(
                        """\
                                    #include <Python.h>
                                    static PyObject *
                                    helloworld(PyObject *self, PyObject *args)
                                    {
                                        printf("Hello World\\n");
                                        Py_RETURN_NONE;
                                    }
                                    static PyMethodDef
                                    myMethods[] = {
                                        { "helloworld", helloworld, METH_NOARGS, "Prints Hello World" },
                                        { NULL, NULL, 0, NULL }
                                    };
                                    static struct PyModuleDef cwrapper = {
                                        PyModuleDef_HEAD_INIT,
                                        "cwrapper",
                                        "Test Module",
                                        -1,
                                        myMethods
                                    };

                                    PyMODINIT_FUNC
                                    PyInit_cwrapper(void)
                                    {
                                        return PyModule_Create(&cwrapper);
                                    }
                                """
                    )
                )
            subprocess.check_call(
                [sys.executable, "-c", "import struct"],
            )
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "wheel",
                ],
            )
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    tmppro,
                ],
            )
            subprocess.check_call(
                [sys.executable, "-c", "import cwrapper"],
            )



def suite():
    return unittest.TestLoader().loadTestsFromName(__name__)


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
