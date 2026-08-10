#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mini trace verifier のエントリポイント (orchestrator/README の verify.py)。

    python orchestrator/verify.py <trace_dir> [<trace_dir> ...] [--json]

本体ロジックは orchestrator/verifier/ パッケージにある。ここはどこから
実行されても package を import できるよう sys.path を通すだけの薄い wrapper。
verifier サブエージェント (.claude/agents/verifier.md) はこれを Bash で呼ぶ。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.verifier.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
