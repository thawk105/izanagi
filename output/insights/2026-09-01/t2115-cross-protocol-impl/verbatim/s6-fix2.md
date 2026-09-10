## 対応表

| 項目 | 判定 | 根拠 |
|---|---|---|
| P-7 | closed | `#if` / `#ifdef` / `#ifndef` の深さを行単位で追跡し、literal `#if 0` から対応する `#endif` までを除外。[between_run_floor.py:167](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:167) 入れ子再現の負例も追加。[test_between_run_floor.py:368](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:368) |

## 変更内容

変更は次の 2 file だけです。

- [between_run_floor.py:114](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:114)
  - docstring に条件評価を行わず、literal `#if 0` だけを除外する契約を明記。
  - 非貪欲 regex を深さ走査へ置換。
  - `#else` / `#elif` を評価せず、dead block 全体を捨てる理由をコメント化。
- [test_between_run_floor.py:368](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:368)
  - 入れ子の `#if TRACE ... #endif` より後ろに dead hook がある負例を追加。

## 実走結果

実走済み test nodeid: なし。実装済み・未実走です。

以下の nodeid を `tools/run_tests.py` で起動しましたが、`qstat -Q` preflight が失敗し、子テストは開始されませんでした。

- `orchestrator/tests/test_between_run_floor.py::test_trace_hook_admission_rejects_hook_after_nested_if_inside_if_zero`
- `orchestrator/tests/test_between_run_floor.py::test_trace_hook_admission_accepts_listed_source`
- `orchestrator/tests/test_between_run_floor.py::test_trace_hook_admission_is_bound_to_source_facts`

代替確認:

- 両変更 file の AST parse: 成功
- 実 submodule の silo に production helper を直接適用: `True`
- `git diff --check`: 成功

silo probe は実際の `CMakeLists.txt` の `SOURCES` を解決して検査するため、列挙 source の実フックが引き続き受理されることを確認しています。既存の合成正例 test も変更・削除していません。

## 未完・懸念

- pytest 実走だけがインフラ都合で未完です。
- runner が生成した今回分の `output/pegasus-dispatch/...` は全ファイルと directory を除去し、禁止範囲に変更を残していません。
- commit、add、stash などは禁止された Git 操作は実行していません。

## 総括

P-7 は closed。入れ子 dead block の後半を証拠として数える穴を閉じました。  
変更は指定された 2 file のみです。  
実 silo 正例は `True`、構文確認と差分検査も成功しました。  
pytest nodeid は Pegasus preflight 障害により未実走です。