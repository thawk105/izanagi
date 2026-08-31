## 総括

- `CANDIDATES` 由来の exact name/comparator 権威集合を実装し、重複を import 時に fail-closed 化した。
- freeze の生成 2 経路と schema 検証へ束縛を追加し、拒否を `FreezeError` へ変換した。
- 必須の正負テストと glob メタテスト対応の自走 harness を実装した。
- import/AST/diff 検査は `rc=0`。pytest は実行基盤 `rc=16` で child が起動せず、赤の有無は未判定。`closed` ではない。

## 変更した file

- [sort_comparator_authority.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/sort_comparator_authority.py:1)
  - 15 candidate から private index を機械導出。
  - name/implementation 重複検出と exact binding API を追加。

- [s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/campaign/s1_known_axes_freeze.py:87)
  - read-heavy/main 生成経路と `_validate_schema` に束縛を追加。

- [test_sort_comparator_authority.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_sort_comparator_authority.py:16)
  - 15 件の正例、二種類の重複、外側 whitespace、canonical mismatch を検査。

- [test_s1_known_axes_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2076-t493-sort-oracle-parent-reference/orchestrator/tests/test_s1_known_axes_freeze.py:145)
  - 実 freeze 3 entry、schema 負例、生成 2 経路の provenance 負例を追加。

禁止対象、docs、凍結 JSON は未変更。commit/add も未実施。

## 実走した検査

- authority test 全体 + S1 freeze test 全体: `rc=16`、`child_started=false`。nodeid は未実走。
- S1 freeze test 単独: `rc=16`、nodeid は未実走。
- `test_plain_runner_coverage.py` 単独: `rc=16`、nodeid は未実走。
- collect-only も `rc=16`。
- 原因:
  - user slice: `17,175,031,808 / 17,179,869,184 bytes`、14 GiB local 上限超過。
  - `qstat -Q`: `rc=1`、sandbox の socket 作成拒否。
- import smoke、4 file の AST parse、`git diff --check`: `rc=0`。
- 禁止対象の差分検査: `rc=0`、差分なし。

必須 node と consumer/meta test は実装済み・未実走。

## 波及の静的列挙

- 所有外 production caller:
  - `s1_measurement_freeze.py`
  - `s1_verify_extime_calibration.py`
  - `s8b_oracle_driver.py`
  - `t080_freeze_migration.py`

- 共有 fixture:
  - `output/s1-freeze/known_axes_freeze.json`
  - sort campaign provenance/WAL
  - `s1_expected_goldens.py`
  - growth-hold／real-repo serialization 台帳

- consumer test:
  - `test_s1_measurement_freeze.py`
  - `test_s1_verify_extime_calibration.py`
  - `test_s8b_oracle_driver.py`
  - `test_t080_freeze_migration.py`

- glob/meta test:
  - `test_plain_runner_coverage.py`
  - `test_pytest_collection_config.py`
  - `test_campaign_import_invariant.py`
  - `test_ccbench_spawn_sites.py`
  - `test_s8b_ratified_freeze.py`

いずれも同じ実行基盤理由で未実走。

## 未解決・親の裁定が要る点

T-493 の実装裁定に追加判断はない。親環境で上記必須 node・consumer/meta test の実走が必要。T-2076 は裁定どおり未変更。