# -*- coding: utf-8 -*-
"""python -m calibrator ... を verify と同様に許す。"""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
