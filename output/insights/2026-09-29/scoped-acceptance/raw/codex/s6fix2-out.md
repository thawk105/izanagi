## 所見ごとの対応

[scoped_acceptance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/scoped-acc-author/tools/scoped_acceptance.py:25) に fix2 の 3 点を実装しました。insight の鍵は深さ 3 から作り、純粋な日付の祖先 path・名前と GENERIC 名を除外します。点検済み reader 7 path を閉じた定数に置き、一覧外の production candidate が対応する入れ物文字列を持つ場合は `container-reader:<file>` で不適格にします。spool fragment の変更時は、`docs/spool` を含む test file をすべて選びます。

## 変えた新 test の期待

既存 test と本 wave の新 test の期待値は変更していません。[test_scoped_acceptance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/scoped-acc-author/orchestrator/tests/test_scoped_acceptance.py:228) に MF4〜MF6 の単一理由の例と、点検済み reader の正例などを追加しました。

## 実走結果

`tools/run_tests.py` は qstat 事前確認で rc=16 となり、pytest 子は起動していません。**pytest の緑は未確認です。** 代替の直接呼び出しでは分類器 test 22 関数・パラメータ 19 ケース、指定の forward-main 4 件などが通過しました。MF4〜MF6、fix1 の MF1〜MF3・MS5・MS6・MS9 は、それぞれの一時変異で赤化しました。`check_codex_agents.py`、`check_docs.py`、構文チェック、`git diff --check` は通過しました。

## 所有外への波及

静的に確認した caller は `scoped_acceptance_launcher.py`、`dev_wave_land.py`、`dev_wave_wait.py`、`run_tests.py` です。共有 fixture は `orchestrator/tests/conftest.py` の inventory と `test_dev_wave_land.py` の合成 repo、consumer test は同 land test の forward-main 系および固定選択対象の `test_check_docs.py`、`test_spool_fold.py`、`test_p3_b4_wiring_probe.py` です。所有外 file は編集していません。

## 総括

変更は許可された 2 file のみで、commit は作成していません。行数は本体 323／上限 500、test 402／上限 600 です。残る検証は pytest の実走です。