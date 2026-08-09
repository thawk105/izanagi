実装は完了しました。受理・拒否集合と exit code は変更せず、failed report が存在する完走セッションだけに digest を追加します。

変更内容:

- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/conftest.py:328)
  - report を `pytest_runtest_logreport` / `pytest_collectreport` で独立収集。
  - controller の `pytest_unconfigure` post-yield で最大 49,152 bytes を出力。
  - lazy relay 定数 import、ASCII canonical escape、tail excerpt、省略会計・manifest SHA-256を実装。
  - worker・緑走行は完全無出力。通常例外は fail-open、`BaseException` と inner hook 例外は伝播。
  - 既存内容は削除なし（328 insertions / 0 deletions）。
- [test_pytest_failure_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t677-relay-reach/orchestrator/tests/test_pytest_failure_digest.py:210)
  - 裁定 (a)〜(h) を9テストで実装。
  - E2E は実 conftest 自動 discovery、nested xdist、process-group cleanup、独立会計 oracle を使用。
  - mutation consumer の raw／1段／2段 prefix と実 relay 結合を固定。
  - `pytest.main([__file__])` の自走 harness 付き。
  - monkeypatch は未使用。明示的な注入引数と標準 fixture のみ使用。

検査結果:

- Python 2ファイルの構文コンパイル: 成功
- `git diff --check`: 成功
- 静的・純関数 probe: digest 45,076 bytes、selected=10、omitted=14
- report 到着順反転でも digest 一致
- mutation consumer 三形の抽出集合一致
- synthetic stdout を実 `_relay_scheduler_logs` に通し、digest 全体の一致を確認
- top-level `tools` import 不在、plain isolated import、自走 harness を確認

pytest nodeid の実走は0件です。ホストが `pegasus02` で、リポジトリ規律はログインノード上の pytest 直起動を禁止する一方、今回の指示は `tools/run_tests.py` も禁止しているため、許可された実行経路がありません。したがって新規9 node、`test_plain_runner_coverage.py` の3 node、親の全走はいずれも未実走で、緑は主張しません。実測された赤はありませんが、未実走部分の結果は未確定です。

波及可能性は、実 conftest を読む `orchestrator/tests` 全体、xdist controller/worker の終了順、conftest を隔離ロードする `test_real_repo_serialization.py`、失敗 stdout を読む task-run／mutation harness、Pegasus relay 表示です。既存 fixture・session sidecar hook は変更していません。

## 総括

- bounded failure digest と裁定 (a)〜(h) の9テストを指定2ファイルだけに実装。
- 現行の pass/fail・収集・exit code の受理集合は不変。
- 構文、差分、独立会計、consumer三形、synthetic relay probe は成功。
- pytest実走 nodeidは0件で、新規9 node・meta-test 3 node・親全走は未実走。
- 残る実測赤は0件だが、未実走のため緑・closedは申告しない。
- conftestを読む全canonical testとstdout consumerへの波及可能性がある。