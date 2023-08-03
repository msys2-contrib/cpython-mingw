import os

if os.name == "nt":
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.isdir(p):
            os.add_dll_directory(p)

from test.libregrtest import main
main()
