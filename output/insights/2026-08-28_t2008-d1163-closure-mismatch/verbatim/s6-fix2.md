FR-01 を修正しました。

- 状態: `closed` 1件 / `partial` 0件 / `regressed` 0件
- 変更: [test_plot_backoff_ci.py:375](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2008-d1163-author/orchestrator/tests/test_plot_backoff_ci.py:375) の `is None` → `== 0`
- unstaged 差分: 1 path、`+1/-1`
- 実走 nodeid: `test_production_provenance_records_current_generator_source_sha`
- rc: `16`（`qstat -Q` preflight failure、`child_started=false`）
- 未実走: 上記 node は子プロセス未起動のため未実走
- 波及: production code、既存テスト契約、accepted/rejected、skip、fixture hash、historical SHA、docs/output/frozen bytesは変更なし
- stage/commit 操作なし。既存14 pathの staged 差分を保持し、fix2だけが unstaged
- 生成された dispatch receipt・補助ファイルは除去済み
- `git diff --check`: rc=0

## 総括

FR-01 の誤植のみを production の成功戻り値契約 `0` に合わせました。修正は closed ですが、Pegasus infrastructure failure のため対象 node の実走結果は未取得です。
