# 親が login で実走・確認した結果 (2026-09-29 JST、author-1 の成果物に対して)

- 成果物の退避: 子の木 /work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/ を job dir の author1-out/ へ写した。sha256 は author-1.md の表と 7 件一致 (patch 3・gate_check.py・test_gate_check.py・launch_gate_liveness.py・fmt_check.py)。
- 照合器の自走 test: `python3 /work/1/SFC/tanab/izanagi/.codex/worktrees/genopt-gl-author/genopt_gl_scratch/test_gate_check.py` → rc=0、Ran 13 tests、OK (parent-selftest.log)。
- patch の厳密適用 (pin の 3 file の写しに `git apply --check`、fuzz なし): [計装] rc=0、[計装 → B1] rc=0、[計装 → 修正] rc=0、[修正 単独] rc=0 (parent-applycheck.log)。
- 実装子の報告: tag `S` は既存の MOCC 計装 (`cc/mocc/transaction.cc` の `witness_<thid>.log`) で使用中。今回の `gate_<thid>.log` とは別 file だが、同名の識別子が 2 つの意味を持つ (D75)。

親が読んで気づいた点 (レビューで真偽と重大度を判定し、ほかにもあれば挙げよ):
- P-1: fix job は上流 CI 相当の全体 build (pin 単独・pin + 修正) を trace の走行より前に `check=True` で行う。CI 相当の build が落ちると例外で job が止まり、(d) の測定が失われる。
- P-2: CI 相当の build に `drv.STOCK_G.cmake_defines()` (Silo の genome の define) と `-DCCBENCH_TRACE=0` を渡している。上流 CI の手順 (external/ccbench/.github/workflows/ の build) は define なしの既定値なので意味が違う。
- P-3: run ごとの trace dir (trace-W-rmw/ など) を tar.gz にした後も out-dir に残す (容量が倍)。
