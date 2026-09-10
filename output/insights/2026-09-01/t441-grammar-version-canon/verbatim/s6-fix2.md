## 直した内容

[orchestrator/tests/test_p3_s4_loop.py:3371](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-fix2/orchestrator/tests/test_p3_s4_loop.py:3371) の `_seed_b4_admitted_history()` を修正しました。

`record_diff_reject()` へ `cfg.search_config` の文法版を `backoff_grammar_version=` で明示しています。版なしの sort fixture も同じ分岐を通るため、`.get()` により明示 `None` を渡して従来挙動を維持しました。production gate・lock・assert・期待値は変更していません。

## 同型の探索

`orchestrator/tests` 配下の `record_diff_reject()` direct call 40件・7ファイルを検索し、AST で lock writer helper を含む参照関係と呼出順を照合しました。

lock 書込み後に reject を記録する関係は6件あり、修正後は6件すべてが `backoff_grammar_version` を明示しています。同型の版省略 fixture の残件は **0件**です。

## 実走した検査

指定された以下4 nodeidは、いずれも**実装済み・未実走**です。

- `test_b4_nonempty_admitted_history_rejects_bootstrap_claim_m1`
- `test_b4_nonempty_admitted_history_allows_valid_continuation`
- `test_b4_driver_rejects_bootstrap_claim_over_nonempty_admitted_history[base-deleted]`
- `test_b4_driver_rejects_bootstrap_claim_over_nonempty_admitted_history[base-zero]`

`tools/run_tests.py` で3回試行しましたが、managed sandbox が local admission ledger を read-only としたため dispatch へ回り、`qstat -Q preflight rc=1`、`child_started=false` で停止しました。collect-only も同じ理由で未実行です。

静的検査は `git diff --check` と対象ファイルの `ast.parse` が成功していますが、テストを緑とは報告しません。

## 波及可能性

helper の実行消費者は次の8 nodeidです。

- 直接呼出し2件：指定された単体テスト2件
- base driver 2件：`base-deleted`、`base-zero`
- sort driver 2件：`sort-deleted`、`sort-zero`。明示 `None` となり従来挙動を維持
- trigger driver 2件：`trigger-deleted`、`trigger-zero`。trigger 専用分岐のため変更箇所を通らない

`test_b4_true_bootstrap_reaches_synthesis_for_all_drivers` は同じ driver helper を使いますが、seed 呼出しより前に return するため波及しません。

受理の含意: 版付き lock の base fixture は、宣言版を明示して BUILD_START と ABORT を書き、`diffq-` variantを返す既存経路を通ります。  
拒否の含意: 版付き lock に対する版省略・別値は、引き続き `AttemptTopologyError` で停止します。

## 総括

- 変更は test fixture の1呼出しだけです。
- 同型の版省略 fixture は残り0件です。
- docs・production・期待値には触れず、commitもしていません。
- 指定4 nodeidは環境上 child 未起動のため、実装済み・未実走です。