## 変更点

- [tools/check_acceptance_reds.py:920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:920)
  - `_replay_completed_output` と呼び出しを削除。
  - captured stdout / stderr を親へ出力しない。
  - `authoritative_stdout` による R5 の FAILED/ERROR 裏取りは維持。

- [test_check_acceptance_reds.py:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/orchestrator/tests/test_check_acceptance_reds.py:1387)
  - 偽 pytest summary を stdout / stderr の双方へ返す回帰テストを追加。
  - checker 出力が `status=non-attributable-only` のみで、架空 FAILED 行を含まないことを固定。

## 新設テスト

`orchestrator/tests/test_check_acceptance_reds.py::test_injected_rerun_output_is_not_replayed_to_checker_streams`

## 実走結果

指定の焦点走はテスト開始前に停止しました。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
rc=16
```

実装済み・未実走です。テスト assertion の赤は未観測で、残る赤は dispatch infrastructure rc=16 のみです。

静的検査は成功しました。

- AST parse
- U+0300〜U+036F 不在
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

## 波及可能性

- checker の stdout 契約である `status=` / `attributable=` 行は不変。
- R5、rc 分類、受理集合、指紋 gate、ignored artifact 検査は不変。
- 子 pytest の生出力に依存していた非契約の表示だけが消える。
- `tools/`・`orchestrator/` の Python 範囲に外部 caller／consumer は見つからなかった。
- 既存 fixture・期待値は変更なし。変更は指定された 2 ファイルのみで、docs 編集・commit はなし。

## 総括

captured pytest 出力の親ストリームへの再掲を除去しました。  
架空 nodeid と第 2 summary block の混入を新設テストで固定しました。  
fail-closed 条件と R5 の裏取りは維持しています。  
焦点走は基盤 rc=16 のため未実走で、緑とは申告しません。