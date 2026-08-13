実装済みです。変更は [_require_materialized_trigger_axis_predicate の docstring](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/campaign/build_admission.py:170) だけです。実行コード、テスト、docs は変更せず、commit もしていません。

変更前後の差分:

```diff
-    R6 の epilogue 直後への dangling ``else`` 付加による常時 backoff 化も残る。
+    R6 の epilogue 直後への dangling ``else`` 付加による常時 backoff 化、R7 の block と epilogue を
+    逐語一致させたまま行う call target／引数の名前解決差し替え（宣言と BEGIN の間等での
+    ``Backoff`` や ``FLAGS_clocks_per_us`` の local shadowing）も残る。
+    source が存在しない場合（``FileNotFoundError``）と、BEGIN/END marker も skeleton token も無い
+    source の場合、この検査は発火せず受理する。
```

検査結果:

- `ast.parse`：成功
- docstring の NFC 正規化、U+0300〜U+036F 不在：成功
- `git diff --check`：成功
- pytest：`tools/run_tests.py` 経由で以下を投入しましたが、`qstat -Q` preflight が `rc=16` となり未実走です。

指定した nodeid:

- `test_trigger_axis_semantic_admission_accepts_pristine_frozen_block`
- `test_trigger_axis_semantic_admission_does_not_freeze_bytes_after_epilogue`
- `test_trigger_axis_semantic_admission_rejects_noncanonical_epilogue`
- `test_trigger_axis_import_and_gateway_call_constraints`

したがって状態は「実装済み・pytest 未実走」です。

docstring 制約 test は `orchestrator/tests/**/*.py` を限定検索しました。当該 docstring や `__doc__` を直接 assert するテストはありません。当該関数名の唯一の参照は [test_build_admission.py:665](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1048-trigger-freeze-epilogue/orchestrator/tests/test_build_admission.py:665) で、関数の呼出数を AST で検査する制約 test です。

## 総括

- 非発火境界として source 不在時の受理を明記しました。
- marker と skeleton token が共に無い source の受理も明記しました。
- R7 として call target／引数の名前解決差し替えを追加しました。
- 既存の R1/R3/R4/R5/R6 は維持しました。
- 実行コード、テスト、docs は変更していません。
- 静的検査は成功し、pytest は環境要因により未実走です。
- commit は作成していません。