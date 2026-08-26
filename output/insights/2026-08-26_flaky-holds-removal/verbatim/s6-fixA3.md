## 総括

生存変異を決定的に赤にする negative control を追加した。  
未検査だった rc=1 と rc=0 の異常出力 control も重複なく追加した。  
実装は `_check_rule_candidates()` を直接呼ぶため、後段 Git 処理による mask はない。  
`output_snapshot_ignores.py` は編集していない。  
テスト runner は dispatch 前処理で rc=16 となったため、実装済み・未実走。

## 既存の rc 分岐 control の棚卸し (どの枝が既に検査済みか)

変更前はいずれも専用 control が存在しなかった。

- rc が 0、1 以外: 未検査
- rc=1 かつ stdout 非空: 未検査
- rc=0 かつ不正な NUL 出力: 未検査

そのため3枝すべて追加した。

## 足した control と、mask されないことの追跡

- Git error control: `subprocess.run` を rc=128 に固定し、`AssertionError` を要求する。
- rc=1 control: 非空 stdout を返し、専用 `AssertionError` を要求する。
- rc=0 control: NUL 終端のない stdout を返し、専用 `AssertionError` を要求する。

生存変異を適用すると、Git error control では `matched_queries = frozenset()` となり、関数が空集合を正常返却する。その結果 `pytest.raises` が `DID NOT RAISE` で赤になる。

直接 `_check_rule_candidates()` を呼んでいるため、`_git_ignored_output_snapshot_rules()`、`git ls-files`、`_run_git_bytes()` には到達しない。別 assertion による mask はない。

## 新設した nodeid の一覧

- `orchestrator/tests/test_s8b_oracle_driver.py::test_check_rule_candidates_fails_closed_on_git_error`
- `orchestrator/tests/test_s8b_oracle_driver.py::test_check_rule_candidates_rejects_rc1_with_stdout`
- `orchestrator/tests/test_s8b_oracle_driver.py::test_check_rule_candidates_rejects_rc0_without_nul_terminator`

## 変更した file と行

- [test_s8b_oracle_driver.py:94](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/test_s8b_oracle_driver.py:94): private helper の import
- [test_s8b_oracle_driver.py:744](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-a/orchestrator/tests/test_s8b_oracle_driver.py:744): 3 control

`output_snapshot_ignores.py` は未編集。既存の staged 変更も保持しており、`git add` は実行していない。

## 実走したか (nodeid と範囲、または「実装済み・未実走」)

実装済み・未実走。

新設3 nodeidを `python3 tools/run_tests.py` で指定したが、テスト開始前に `qstat -Q preflight rc=1` となり、dispatch infrastructure failure、rc=16 で停止した。実行済み node は0件。

非テスト検査では以下を確認した。

- 対象ファイルの AST parse: PASS
- `git diff --check`: PASS

## 所有外への波及可能性

- `_check_rule_candidates()` の既存 caller `_git_ignored_output_snapshot_rules()` と、その公開 wrapper 3種には実装変更なし。
- 段4裁定上の consumer である `test_real_repo_serialization.py` には変更なし。
- `test_s8b_floor_campaign.py` は別構造の helper を持つため直接影響なし。
- module autouse fixture `_approved_spec_loader` は新設 nodeにも適用されるが、各 control は driver を呼ばない。
- `subprocess.run` の差し替えは各 test の context 内だけで、終了時に復元される。

## 未完・未確認

- 新設3 nodeidの pytest 実走
- 生存変異を適用した mutation matrix の再走
- runner が失敗時に生成した `output/pegasus-dispatch/85dde61435d1837d40bdfab56b4bd8a5/receipt.json` は、禁止範囲のため削除していない。