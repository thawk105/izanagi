## 総括

R1 と R2 を指定の 2 ファイルで修正しました。実装済み・未実走です。

## 変更内容 (file:line)

- [p3_s4_loop_policy.py:673](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix1/orchestrator/campaign/p3_s4_loop_policy.py:673): `stopped-before` の stdout に `measurement_campaign_id` を付ける代入を削除。
- [test_p3_s4_loop_policy.py:672](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix1/orchestrator/tests/test_p3_s4_loop_policy.py:672): 停止結果を独立した literal と比較。
- [test_p3_s4_loop_policy.py:843](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix1/orchestrator/tests/test_p3_s4_loop_policy.py:843): digest の全文一致を、候補の証跡を含み stock の証跡を含まない検査に変更。

## R1 の判定語の選び方と、(b) が恒真でない根拠

2 本目の候補と stock の `STAGE_BUILD_START` 記録から、それぞれの `genome` 表記を判定語として取ります。stock の判定語が **stock 実行後の admitted view から作った digest には含まれる**ことを先に検査し、系列 digest には含まれないことを検査します。時刻・pid・hash の値は固定していません。

## 実走した検査と結果 (未実走はそう書く)

`python3 -m py_compile`（両ファイル）と `git diff --check` は通過しました。pytest と `tools/run_tests.py` は未実走です。

## 所有外への波及 (静的列挙)

変更は指定の 2 ファイルだけです。R1 はテストのみ、R2 は停止時の stdout の field のみを変更しました。claim・計測・履歴への変更はありません。

## 未解決・判断が要る点

親による計算ノードでの焦点走結果を待ちます。