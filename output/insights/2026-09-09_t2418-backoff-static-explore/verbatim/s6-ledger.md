## 実行した producer の argv と rc

cwd は指定 worktree であることを確認しました。`--help` は rc=0、既定 `--repo` も同 worktree を指していました。

```text
python3 tools/update_acceptance_duration_ledger.py \
  /work/1/SFC/tanab/.izanagi-acceptance-shards/c51ea293d249db759623f952cdc7a8f2/shard-0/junit.xml \
  /work/1/SFC/tanab/.izanagi-acceptance-shards/c51ea293d249db759623f952cdc7a8f2/shard-1/junit.xml \
  /work/1/SFC/tanab/.izanagi-acceptance-shards/c51ea293d249db759623f952cdc7a8f2/shard-2/junit.xml \
  --add-only
```

rc=0。producer の結果:

```text
excluded_failure_or_error=1
mode=add-only
added=2079
skipped_existing=19935
excluded_frozen_removed=0
excluded_writer_base_key=1
excluded_frozen_suite=139
excluded_total=141
```

## 追加された nodeid

追加は合計 2,079 件です。全件は台帳の連続した追加ブロック（[acceptance_duration_ledger.json の3〜2081行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2418-ledger/orchestrator/tests/acceptance_duration_ledger.json:3)）にあります。

指定された本 wave の8件はすべて含まれ、JUnit shard-1 の実測値と一致しました。

- `test_b10_run_kind_routes_t2418_through_job_submit_and_finalizer`: `0.036`
- `test_t2418_binary_identity_rejects_incomplete_or_malformed_bindings`: `0.001`
- `test_t2418_cli_requires_exact_five_and_both_report_artifacts`: `0.003`
- `test_t2418_exact_grid_identity_order_and_disclosure_are_literal_pinned`: `0.001`
- `test_t2418_frozen_campaign_is_rejected_by_existing_t2266_consumer`: `0.005`
- `test_t2418_frozen_wal_view_flows_through_capture_loader_and_reports`: `0.006`
- `test_t2418_prebuild_requires_five_distinct_trace_disabled_binaries`: `0.001`
- `test_t2418_run_path_uses_exact_five_genomes_and_shared_campaign_call`: `0.002`

全2,079件について、usable JUnit key への存在は 2,079/2,079、producer の量子化結果との値不一致は0件でした。追加値はすべて正値で、`0.0` は0件、範囲は `0.001`〜`98.0` 秒です。

## 既存 entry の非変更の確認

更新前の台帳は clean でした。

- 既存 entry: 20,042件
- 削除された nodeid: 0件
- 既存値の変更: 0件
- 既存 entry 行の生バイト変更: 0件
- `git diff`: `+2080/-1`
- 唯一の削除行: `-  "nodeid_count": 20042,`
- `git diff --check`: rc=0
- 変更ファイル: 台帳1ファイルのみ

## nodeid_count の整合

更新後は以下で一致しています。

```text
nodeid_count = 22121
duration_seconds_by_nodeid の要素数 = 22121
```

`20042 + 2079 = 22121` です。

## 更新後の網羅率の見込み

consumer と同じ key 集合演算を静的に確認しました。

```text
JUnit/consumer 相当の全 key = 22155
台帳との共通 key          = 22014
未収載 key                = 141
見込み網羅率              = 22014 / 22155
                         = 99.363574813812%
```

更新前分子 `19935` に今回の2,079件を加えた `22014` で、90% 閾値を上回る見込みです。未収載141件は producer の failure/error 1件と凍結除外140件に対応します。

## 実走できなかったもの

`test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` は、指定された sandbox 制約に従い未実走です。pytest や `tools/run_tests.py` は起動していません。

台帳更新済み・網羅率ゲート未実走です。走っていないテストを緑とは報告していません。

## 総括

正本 producer により台帳だけを add-only 更新しました。本 wave の8件を含む2,079件が実測値で追加され、既存 entry は byte exact に維持されています。`git add`、`git commit` その他の禁止 git 操作は行っていません。