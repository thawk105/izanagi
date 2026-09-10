U1〜U6 を順に実装し、commit・stage は行っていません。

主な変更:

- [policy v2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.v2.json)へ更新し、workload campaign の論理積規則を protocol preimage に追加。指定された 7 schema を bump。
- [certification driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py)を exact 2-job group、nested raw manifest v3、campaign claim↔reservation 束縛へ更新。
- [compute job body](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh)を `IZANAGI_A2_WORKLOAD` 指定の 1 workload/job に変更。`finalize-raw` を除去。
- [login-side submitter](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/submit_paper_story_a2_certification.sh)を新設。批准 precheck、exact 2 qsub、group submission receipt、create-only `finish-group` を実装。
- registry と `test_hooks.py` の class map／全 field／local evidence、および subprocess・executable inventory を追随。
- 歴史 qstat fixture は変更せず、fan-out 用合成 fixture を 2 本追加。
- 新規 nodeid は作らず既存契約テストへ変異検査を統合したため、acceptance duration ledger の node 欠落は 0。

検証結果:

- `python3 tools/check_codex_agents.py`: rc=0。
- `git diff --check`、Python syntax compile、submitterの `bash -n`、JSON parse: rc=0。
- canonical group、finish-group、raw create-only、親非走査、manifest loader、claim/request mutation、片側 nonzero、批准前後 qsub gateを直接 unit call で診断済み。ただしこれは pytest の緑とは数えていません。
- 関連 meta-test の直接診断: hook 3 golden、Pegasus executable inventory、sanctioned projection、CCBench subprocess inventory、campaign caller inventory、official perf inventoryはいずれも通過。

正規 pytest runner は最終対象範囲を含む全 5 回が `qstat -Q preflight rc=1`、`child_started=false`、rc=16 で停止しました。したがって実走済み nodeid は 0 件で、関連テストは「実装済み・未実走」です。

残る赤は `python3 tools/check_docs.py` の 1 件だけです。新 submitterが registry-only で、親未 land の runbook §7.0 投影表に無いという指示どおりの期待赤です。

波及候補は、旧 scalar `request_id` receipt/CLI の外部 caller、policy pathを使う T-1683 probe、親所有の runbook・Pegasus READMEです。旧 schema・共有 root の receipt は現在拒否されます。4 cell、5反復、6時間、reservation v1、失敗時 indeterminate の集合は変更せず、指示された「独立 2 campaign の論理積」以外の受理集合変更は加えていません。

禁止対象の docs、hooks、信頼根、歴史 fixtureには触れていません。既存の未追跡 `output/insights/2026-08-27_t1647-a2-cert-fanout/` も保持したままです。

## 総括

- 完了: U1〜U6 の実装、registry・契約・変異・meta-test追随。
- 残り: 親による docs 投影、正規 pytest 実走、統合・commit。
- 最大リスク: runner infrastructure停止中のため、pytest collection/runtimeを実証できていないこと。