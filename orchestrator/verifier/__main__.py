# -*- coding: utf-8 -*-
"""`python -m verifier <trace_dir> ...` のエントリ。"""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
