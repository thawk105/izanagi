## 実装した内容

実装前に停止しました。ファイル変更はありません。

A-2 の必須要件と、変更禁止の既存テスト期待値が直接矛盾しています。

- [test_p3_s4_loop.py:6078](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-unit-a/orchestrator/tests/test_p3_s4_loop.py:6078) は manifest あり・coder role なしの `--run-iteration` 成功を要求しています。
- [test_p3_s4_loop.py:6762](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2182-unit-a/orchestrator/tests/test_p3_s4_loop.py:6762) も同じ入力の成功を明示的に要求しています。

A-2 を実装すると両テストが赤になります。一方、依頼は既存期待値の変更を禁止し、期待値が誤りなら実装を変えず報告して停止するよう指定しています。

## 新設したテストと実走結果

新設なし、未実走です。矛盾を発見した時点で停止したため、`closed` とは申告しません。

## 受理・拒否の含意

現状は `--run-iteration` で manifest のみを指定した入力を拒否できません。

要求された変更後はその入力を拒否し、manifest と coder role の両方を指定した入力は通ります。ただし、その変更は上記2件の既存正例を破ります。

## 波及可能性

直接波及する既存 consumer test は上記2件です。A-1 の condition gate 配線、`condition_meaning_gate.py`、`buildcache.py`、共有 fixtureには変更を加えていません。

## 総括

親側で、上記既存正例を改訂してよいという明示的な裁定、または A-2 の要件変更が必要です。現行指示のままでは、A-2 と「既存テスト期待値を変更せず全緑」を同時に満たせません。