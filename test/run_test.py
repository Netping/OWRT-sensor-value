#!/usr/bin/python3
import os
import sys




if __name__ == "__main__":
    os.system("pytest --capture=no -v test_api.py")
    sys.exit(0)
