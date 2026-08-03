#!/usr/bin/env python3
"""Fail closed unless the interpreter can run the T-361 probe."""

import sys


if sys.version_info < (3, 10):
    raise SystemExit(1)

raise SystemExit(0)
