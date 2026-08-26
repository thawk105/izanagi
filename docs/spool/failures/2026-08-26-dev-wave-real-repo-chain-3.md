---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-real-repo-chain
seq: 3
---

## 新規

### {{F:ambient-output-dir-red-in-fresh-worktree}}. 作業ツリーに実在する ignore 対象 dir を前提にしたテストが、新しい worktree で落ちる [テスト代表性]

- 事象: `test_real_repo_serialization.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes`
  が新規 worktree で `assert 'runs' in ('pegasus-dispatch',)` により落ちる。
  本 wave で 2 回踏んだ — 焦点走の 1 回目と、変異 harness の baseline
  (`baseline が緑でないため production write を開始しない: status=FAILED` で全 10 走が中止)。
- 根本原因: 判定器 `orchestrator/tests/output_snapshot_ignores.py` の
  `git_ignored_output_prefixes` は
  `git ls-files -o -i --exclude-standard --directory -- output/` を撃つ。これは
  **`.gitignore` に列挙された path ではなく、作業ツリーに実在する ignored entry だけ**を返す。
  当該テストは `"runs"` が返ることを前提条件として assert するが、`output/runs/` は
  ignore 対象なので commit されず、**新しい worktree には存在しない**。
  main の checkout には過去の campaign 実行で作られた実体があるため、そこでは通る。
  すなわち通るかどうかが**その checkout の履歴という ambient な状態**に依存している。
- 恒久対応: 未実施。本 wave では環境側で `output/runs/` を作って前提を満たし、
  変異 harness の baseline では当該 1 node を `DW-C01` の
  「既存赤は根拠を台帳へ書き `--deselect`」に従って除外した。
  **どちらもテストを直しておらず、次の wave も同じ赤を踏む。**
  恒久対応の候補は (a) テストが必要な ignored dir を自分で作ってから判定する、
  (b) 判定器を「実在する entry」ではなく `git check-ignore` による判定へ変える、
  (c) 前提条件が満たせない環境では明示 skip する、のいずれか。
  **判定と対処はユーザー裁定へ返す** — `docs/decisions.md` の保留規律により、
  成長比例でも flaky でもない環境依存の赤を独断で恒久 skip へ落とさない。
- 再発検知: 新規 worktree で焦点走または変異 baseline を走らせた時点で必ず出る。
  fresh worktree を作る全 wave が対象であり、頻度は高い。
