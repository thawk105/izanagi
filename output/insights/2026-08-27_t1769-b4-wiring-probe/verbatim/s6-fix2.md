## G1 / G2 の対応表

|項目|状態|対応|
|---|---|---|
|G1|partial（実装済み・formal 未実走）|resolver 由来の site を使用し、拒否時は `status: not_measured`・`site`・逐語の `reason` を記録。計測時は `status: measured`。合否は raw cfg を維持。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1769-b4-wiring-probe/orchestrator/campaign/p3_b4_wiring_probe.py:1651)、[拒否側テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1769-b4-wiring-probe/orchestrator/tests/test_p3_b4_wiring_probe.py:523)、[計測側テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1769-b4-wiring-probe/orchestrator/tests/test_p3_b4_wiring_probe.py:559)|
|G2|partial（実装済み・formal 未実走）|seal 時に `sys.excepthook = sys.__excepthook__` を設定。import 遮断は維持。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1769-b4-wiring-probe/orchestrator/campaign/p3_b4_wiring_probe.py:574)、[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1769-b4-wiring-probe/orchestrator/tests/test_p3_b4_wiring_probe.py:601)|

## 実走した検査

正式 runner は通常・`--force-dispatch` の双方で `qstat -Q preflight rc=1`、`child_started=false`、`rc=16` でした。以下はすべて未実走です。

- `test_trigger_site_projection_records_resolver_site_and_verbatim_refusal`
- `test_trigger_site_projection_is_measured_when_production_accepts_site`
- `test_seal_uses_import_free_excepthook_and_preserves_primary_exception`
- `test_actual_main_positive_baseline_all_drivers[trigger]`

全 test file と `test_plain_runner_coverage.py` も未実走です。

補助診断では、import 遮断が発火することを確認後、未処理例外が `RuntimeError: PRIMARY_EXCEPTION_REPORT` として報告され、二次 `Error in sys.excepthook` は出ませんでした。両ファイルの AST parse・空白検査は成功しています。

## 恒真でないことの根拠

- 拒否側テストは resolver を固有 site に差し替え、その値が production admission に渡され、同じ site と逐語 reason が記録されることを要求します。site の固定値化や常時 `measured` は赤になります。
- 計測側テストは拒否しない site を模し、admission 1 回・site projection 2 回の実呼出しと contract identity、`status: measured`、実 identity 分離を要求します。常時 `not_measured` や射影処理の省略は赤になります。

## 総括

- G1/G2 は許可された 2 ファイルだけに実装しました。
- base/sort の分岐は変更していません。
- formal pytest は dispatch infrastructure failure のため未実走です。
- runner が dispatch receipt を自動生成しましたが、`output/` は編集・削除していません。
- commit・add・stash・branch 操作は行っていません。