#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""calibrator のエントリポイント (verify.py と同型)。

  python orchestrator/calibrate.py --binary <ycsb_*.exe> --env-tag linux-baremetal --threads 16
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calibrator.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
