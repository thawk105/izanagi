# [T-1303] `--base-digest` 変異台帳

対象 commit: `bb9283f51b3903b5767a545f064abc9c528ea2c1`
実行方式: 手動 (`DW-O19` 手順、`tools/mutation_harness.py` の dispatch 経路は使わず、
`Edit` で単一置換 → `python3 tools/run_tests.py orchestrator/tests/test_spool_fold.py -k
base_digest -v` → `git checkout -- tools/spool_fold.py` で復元、を1件ずつ直列実行)。
spec は `mutation/mutation-spec.json` (`izanagi-dev-wave-mutation-spec/v1`) に事前登録済み。

## baseline

変異前 (commit `bb9283f5` 単独): `-k base_digest` で 10 passed (新設8件 + 既存2件
`test_n10_stale_base_digest_is_rejected`、`test_parallel_new_then_existing_update_uses_substantive_base_digest`)、
0 failed。

## 結果

| id | 概要 | 期待 KILLED node 数 | 実測 | 判定 |
|---|---|---|---|---|
| t1303.m01-task-re-invert | `_task_id_arg` の `TASK_RE` 検証を反転 | 8 | 8 failed (新設8件全部)、既存2件は無傷 | KILLED、完全一致 |
| t1303.m02-item-none-invert | `_resolve_base_digest` の not-found 分岐を反転 | 6 | 6 failed (conflict/malformed の2件はこのコードへ未到達のため無傷)、うち1件は `AttributeError` 由来の `JSONDecodeError` | KILLED、完全一致 |
| t1303.m03-drop-dry-run-conflict | `--base-digest`+`--dry-run` 併用拒否を無効化 | 1 | 1 failed (`assert 0 == 2`) | KILLED、完全一致 |
| t1303.m04-break-archive-glob | `_load_base_digest_sources` の archive glob を空集合化 | 2 | 2 failed (archive依存の carry chain / real corpus のみ) | KILLED、完全一致 |
| t1303.m05-break-stdout-format | 成功時 stdout を JSON へ変形 | 5 | 5 failed (stdout exact-match系のみ、エラー系3件は無傷) | KILLED、完全一致 |

**5/5 KILLED、SURVIVED 0、MISMATCH 0。** 全件で観測 node 集合が事前登録した `expected_nodes` と
完全一致した (DW-M08)。各変異後は `git diff HEAD | wc -l` = 0 で bytes 復元を確認した。

## 単一理由性・マスク層の確認 (DW-M01)

- m01: `_task_id_arg` は canonical ID 検証の唯一の関所。他層 (argparse choices 等) に同じ入力を
  拒否する層はない。
- m02: not-found 判定は `_resolve_base_digest` 内の唯一の分岐。conflict/malformed の2テストは
  この分岐より前 (argparse・mode-conflict チェック) で止まるため対象外、という「前段の関所」の
  存在を逆に確認する形になった。
- m03: `--dry-run` 併用拒否は該当 `if` 文1箇所のみ。他の2ケース (`--show-diff`/`--fold-date`)
  は独立した `if` 文で無傷だった。
- m04: archive 読み込みは `_load_base_digest_sources` 内の1箇所。`plan_fold()` 側の独立した
  archive glob (別 loader) は無変更のまま — 段4裁定どおり両者が完全に独立していることの
  副次的な実証にもなった。
- m05: 成功時の `print()` はこの1箇所のみ。エラー系の出力 (`parser.error`/JSON stderr) は
  別経路で無傷。

## 落とし穴

`tools/mutation_harness.py` の dispatch 経路 (`--runner-mode dispatch --force-dispatch`) は
未使用。T-1361 等の先行 precedent が「codex 子の pytest 実走不能と同じ infrastructure 不調を
harness dispatch も踏む蓋然性が高い」として手動運用を選んだのに倣った。本 wave では親自身の
`tools/run_tests.py` 直接呼び出しが安定して機能した (焦点走・変異とも rc 通り、10 秒未満/回)
ため、5 件の直列手動変異はコスト面でも妥当だった。
