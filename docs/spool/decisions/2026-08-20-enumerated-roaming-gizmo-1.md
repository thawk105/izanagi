---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: enumerated-roaming-gizmo
seq: 1
---

## {{D:accept-chain-copytree-hardlink-no-gain}}. 受入 real-repo 鎖の per-test snapshot コピーの hardlink 化は効果が無いと実測した

**決定:** `orchestrator/tests/test_codex_reasoning_ab.py` の `benchmark_snapshots` 由来 snapshot
を各テストが `shutil.copytree(..., copy_function=shutil.copy2)` で複製している 8 箇所について、
`.git` (root・submodule marker とも) および既知の書込み対象 path 以外を hardlink 化する案を
実測し、**採用しない。** D531/D532 が正本とする「real-repo 鎖の短縮」(D532 (a)) の具体案として
このコピー手段を選ばない。

**理由:**
- 対象 snapshot 1 個 (POS、82.67MB、4726 file) を実際に構築し (`test_snapshot_submodule_object_store_is_recursive`
  を単独実走、bounded local、24.89 秒)、pytest の basetemp と同じ filesystem (`/`、XFS、`/dev/md0`)
  上で `cp -a` (copy2 相当) と `cp -al` (hardlink 相当) を実測した。**`cp -a` = 0.158 秒、
  `cp -al` = 0.043 秒。差はわずか 0.115 秒であり、対象 8 箇所すべてに適用しても短縮は
  高々 1 秒程度**で、鎖長 77.5〜94.9 秒 (D531) や当該テスト個々の所要 (19〜22 秒) に対し
  無視できる。pytest の一時領域が高速なローカル disk 上にあるため、コピーの raw I/O は
  そもそも支配的ではない。
- 段2 codex プランと段3 敵対相談 2 レンズが、対象 8 箇所の in-place 書込み・submodule `.git`
  marker (ディレクトリでなく `gitdir: ...` を書いた通常ファイル)・symlinks 引数の意味論の
  差異など、実装すれば必ず踏む欠陥を独立に複数検出した (段6 相当の敵対レビューを待たず、
  実測ゲートの時点で採否が決着した)。
- D315 (docs/decisions.md:14373) が守る clone/seal コア (`--no-hardlinks`、
  `_seal_git_object_closure` 系) には触れていない。今回不採用と決めたのは、
  D315 の範囲外である per-test copytree の方であり、D315 の適用範囲を変えるものではない。

**却下した選択肢:**
- 8 箇所専用の copier を実装する — 実測で得られる短縮 (高々 1 秒) が、8 箇所の in-place 書込み
  監査・submodule marker 対応・symlinks 意味論保持という実装・監査コストに見合わない。
- 効果測定なしに実装へ進む — 段3 レンズB (整合性・実効性) が BLOCKER として指摘し、
  段5 実装子 (workspace-write) 自身に測定させる設計にしたが、Codex 子は sandbox が
  scheduler (`qstat`) 呼出しを拒むため測定不能だった (`ESYSCAL`/`EACCTAUTH: Unknown user-id`)。
  親が代わりに `tools/run_tests.py` 経由の bounded local 実行で測定し直した。
