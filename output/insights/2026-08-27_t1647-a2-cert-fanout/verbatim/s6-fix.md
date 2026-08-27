7 件すべて修正し、nit のコメントも追加しました。commit は作成していません。

### 変更前 → 変更後

- F1: `campaigns/campaigns/<cid>` を生成して全 raw producer が拒否されていた → job root を output base とし、`jobs/<workload>/campaigns/<cid>` に統一。`A2.run_workload()` を直接通す正例も追加。
- F2: claim digest は 64 桁 hex なら受理 → 再構成した `CampaignConfig` から再計算し、producer・finalizer・manifest loader で一致を要求。digest 単独変異を拒否。
- F3: `finish-group` も qsub・quota・queue・clean-tree gate を要求 → 批准・login・qstat・receipt identity のみ共通化し、投入専用 gate を submit 分岐へ移動。
- F4: fan-out fixture は 7 行抜粋 → 歴史 fixture の 94 行全文から request ID と log path だけを置換した 2 本へ更新。負例も full block の一字段変異。
- F5: v2・不完全 report も materialize 可能 → stage 作成前に exact v3 schema、policy 順の相異なる request IDs、必須 field と evidence identity を検証。v2 負例を追加。
- F6: 既存 raw が mkdir 検査を隠していた → existence check 後、mkdir 直前に競合 directory を作る race 負例へ変更。`exist_ok=True` 退化なら通ってテストが落ちる形。
- F7: job-local raw の余分 file を受理 → 各 `jobs/<workload>/raw/` を exact 2 regular files に閉じ、余分 entry・symlink を finalizer と loader で拒否。共有 `jobs/` は走査しない。
- nit: workload 順序・log path 相異は production 前段に含意される冗長検査であり、独立防壁ではない旨をコメント化。

主な変更先は [paper_story_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py) と [submit_paper_story_a2_certification.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/submit_paper_story_a2_certification.sh) です。

### 検証

以下 7 nodeid を指定 runner で実走しようとしましたが、local headroom 不足後の dispatch が `qstat -Q` の `EACCTAUTH Unknown user-id` で失敗し、child は起動されませんでした。したがって全件「実装済み・未実走」で、緑の主張はありません。

- `test_job_body_is_compute_only_sequential_and_never_submits`
- `test_compute_preflight_rejects_each_m7_boundary[stale-raw]`
- `test_submission_visibility_uses_the_full_real_qstat_fixture`
- `test_m11_materializer_stages_marker_before_single_noreplace_rename`
- `test_raw_manifest_binds_campaign_lock_and_wal_and_freezes_raw_bytes`
- `test_official_run_observes_and_passes_current_toolchain_manifest`
- `test_synthetic_pbs_free_preregister_through_analyze_positive`

その後 1 nodeid を再試行しましたが、同じ rc=16・child 未起動でした。pytest の期待赤・通常赤はいずれも未観測です。

静的検査は成功しました。

- Python 3 file の AST parse、submitter の `bash -n`
- 歴史由来 fixture を除く `git diff --check`
- fan-out fixture 2 本が歴史 fixture に指定の置換だけを加えた exact 94 行であること
- 歴史 fixture の SHA-256 が従来値 `55bc7a…830d` のままであること
- test function inventory が 44 件／12 件で HEAD と同一、新設・削除・改名なし
- docs、`hooks/`、別 wave 所有 4 file、歴史 fixtureへの変更なし

### 波及可能性

- A-2 module 内の CLI callerである `run-workload`、`finalize-raw`、`collect/materialize` が直接影響を受けます。正規 CLI producer は新契約へ追随済みです。
- fan-out fixture 2 本の consumer は `test_paper_story_a2_certification.py` のみです。
- submitter の registry entry と `test_hooks.py` の class/evidence/inventory consumerは内容変更不要ですが、未実走です。
- A-2 の `materialize`・raw loader・claim helperに、module 外の直接 callerは静的検索ではありませんでした。
- 新規 nodeid がないため acceptance duration ledger の再生成は不要です。
- 指示外の受理集合変更はありません。拡大は F1 の正規 producer layout と F3 の正当な finish 操作のみで、F2/F5/F7 は指定された不正入力の拒否復元です。

## 総括

- 修正済み: 7/7 件、nit 1/1 件。
- 残件: 実装上は 0 件。
- テスト: runner dispatch 基盤障害により全対象未実走。
- 最大のリスク: pytest child が一度も起動しておらず、動的な回帰確認が残っていること。