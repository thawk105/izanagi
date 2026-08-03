#!/usr/bin/env python3
"""Fail closed unless the candidate interpreter is supported."""

from __future__ import annotations

import sys


if sys.version_info < (3, 10):
    raise SystemExit(1)
raise SystemExit(0)
