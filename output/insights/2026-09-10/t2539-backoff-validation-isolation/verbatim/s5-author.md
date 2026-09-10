## 実装

- [tools/check_silo_validation_isolation.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-author/tools/check_silo_validation_isolation.py)
  - unified diff の厳格解析と in-memory post-image 構築。
  - preprocess せず全 `#if` 枝を保持する raw-config union call closure。
  - BFS、深さ・caller・callsite、`std::sort` / `std::max` の implicit comparator edge。
  - CMake macro token 検査。
  - A1: `classified_edits` / `unconsumed_edits`。未消費時は `ERROR`。
  - A4: `owner_tus=["cc/silo/transaction.cc"]` と他 protocol 非保証。
  - A5: `analyze(repo_root, patch)` を CLI から分離。
  - B6: licence 非含意の三 verdict。
  - B1–B4: 非保証事項、anomaly 即 reject、`ERROR` 非通過を `claim_boundary` に収録。

- [orchestrator/tests/test_silo_validation_isolation.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2539-author/orchestrator/tests/test_silo_validation_isolation.py)
  - 実 patch 3 本、tmpdir の decoy / 深さ 2 patch、closure 包含・除外、fail-closed、claim boundary を検査。
  - 正例の全 6 edit span 分類・未消費 0 を固定。
  - `_run()` と `__main__` を含む 12-node 自走 harness。

## 実走結果

実行 node: `pegasus02`

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 orchestrator/tests/test_silo_validation_isolation.py
rc=0
ran 12 tests; failures=0
```

12 node すべて実走済みです。decoy は交差なし、iterator `unlockWriteSet` patch は深さ 2 で交差しました。

実 patch の checker 出力主要部:

```json
{"patch":"patches/silo-backoff-fixed.patch","rc":0,"verdict":"NO_STATIC_VALIDATION_CLOSURE_INTERSECTION","classified_edit_count":6,"unconsumed_edits":[],"cmake_macros":[{"macro":"BACKOFF_FIXED","closure_references":[]},{"macro":"BACKOFF_NOINLINE","closure_references":[]}],"intersections":[]}
{"patch":"patches/broken-silo-norw-validation.patch","rc":1,"verdict":"STATIC_VALIDATION_CLOSURE_INTERSECTION","unconsumed_edits":[],"intersections":[{"depth":0,"symbol":"TxExecutor::validationPhase/0"},{"depth":0,"symbol":"TxExecutor::validationPhase/0"}]}
{"patch":"patches/broken-silo-lockskip-validation.patch","rc":1,"verdict":"STATIC_VALIDATION_CLOSURE_INTERSECTION","unconsumed_edits":[],"intersections":[{"depth":1,"symbol":"TxExecutor::lockWriteSet/0"}]}
```

AST 構文検査、裸の `PASS` / `accepts`、U+0300–U+036F、行末空白の検査も rc 0。`pytest` / `tools/run_tests.py` と JUnit 台帳更新は指示どおり未実走・未変更です。

## 波及可能性

- 既存 caller は静的検索で見つからず、新 checker は未接続の単独 CLI。
- `external/ccbench/` 現物と既存 3 patch は読み取りのみ。古い fixture は未使用。
- 共有 `backoff.hh` の他 protocol owner は解析対象外であり、JSON でも非保証。
- 新 test は通常の test discovery 対象になる。受入所要台帳への登録は親の実走 JUnit 後に必要。
- 指定外ファイル、既存 patch、既存 gate、source digest、docs は未変更。

## 現行挙動との差

scope 前には本 checker が存在せず、該当 patch に対する独立した受理・拒否判定もありませんでした。既存 gate の受理集合は変更していません。新規 CLI を明示実行した場合だけ、静的非交差 rc 0、交差 rc 1、判定不能 rc 2 を返します。

## 総括

指定 2 ファイルだけを実装し、raw-config union による深さ 0・1・2 と decoy 対照を固定しました。  
12-node 自走 harness は `pegasus02` で全件成功。commit は作成していません。