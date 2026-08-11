実装は完了しましたが、pytest が開始前停止したため、受入状態は全件 `partial（実装済み・未実走）` です。変更は所有内3ファイルのみで、commit・docs・`output/` は変更していません。

### 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| F-1 | partial | [verify_manifest](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-fix-b/orchestrator/campaign/s8b_oracle_manifest.py:986) で schedule holdout 集合と `freeze["holdouts"]` を先に完全一致検査。期待積も freeze の全holdoutから導出。generic builder受理を維持する欠落holdout負例を追加 |
| F-4 | partial | [独立golden](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-fix-b/orchestrator/tests/test_s8b_oracle_manifest.py:59) に非ASCII・canonical key順・末尾LFなしのraw bytesと独立SHA literalを固定。末尾LF負例もproduction serializer非依存へ変更 |
| F-6 | partial | [spec pin loader](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t750-fix-b/orchestrator/campaign/s8b_oracle_spec.py:156) を単一helperへ集約。完全にvalidな同一入力・同一出力pathで、pinだけを変えてcandidate出力の有無を比較するテストを追加 |
| F-7 | partial | approved writerがfixed candidate rootだけをdirfd・`O_NOFOLLOW`で作成。caller指定subdirectoryは作らず、leafの`O_EXCL`を維持。tmp root正例・負例を追加 |
| regressed | なし | 静的監査で既存テスト期待値の変更・削除、skip/xfail追加は0件 |

`build_manifest`、`write_manifest`、`_atomic_create_json` は変更していません。`verify_manifest` のみ裁定どおり受理集合を縮小しています。

### F-1 の既存node波及

静的な期待赤集合は以下のとおり、すべて空集合です。

- `test_s8b_oracle_manifest.py`: `∅`。既存verify fixtureはfreezeの全holdoutを保持。新規負例 `test_missing_holdout_build_stays_accepted_but_verify_rejects` のみ拒否期待。
- `test_s8b_oracle_driver.py`: `∅`。F-1到達候補52 nodeは共有freezeから全holdout・全6構成を生成。
- `test_s8b_oracle_report.py`: `∅`。到達候補90 node＋official CLI 2 nodeは全積。scheduleを縮退する既存テストはschema-less legacy経路で、verifierを通らない。
- `test_s8b_oracle_judge.py`: `∅`。`verify_manifest`を呼ばない独立observations fixture。
- `test_s8b_ratified_freeze.py`: `∅`。F-1 verifierへの直接到達なし。

親側で上記4 consumer fileを実測する必要があります。

### 検査と赤の内訳

成功した静的検査:

- AST parse、`git diff --check`
- 独立raw bytes 2535 bytesとSHA literalの一致
- 独立spec fixtureをproduction validatorで検証
- HEAD比で既存テストの `assert`／`pytest.raises` 変更0、削除0、新規4 node
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0

pytestは次の10 nodeを一括で試行しましたが、`qstat -Q preflight rc=1` → runner rc=16で開始前停止しました。

- `test_missing_holdout_build_stays_accepted_but_verify_rejects`
- `test_subset_manifest_build_stays_accepted_but_verify_choke_point_rejects`
- `test_reviewed_spec_has_independent_canonical_bytes_and_sha_literal`
- `test_reviewed_spec_none_pin_is_always_no_approved_spec`
- `test_reviewed_spec_pin_mismatch_is_fail_closed`
- `test_approved_writer_safely_creates_only_fixed_candidate_root`
- `test_approved_writer_rejects_symlink_parent`
- `test_approved_writer_is_exclusive_create`
- `test_build_approved_valid_fixture_output_depends_only_on_spec_pin`
- `test_build_approved_uses_one_active_snapshot_and_writes_valid_candidate`

`test_plain_runner_coverage.py` も同じrc=16です。実行nodeidは0件、pytest assertion赤も0件観測ですが、緑とは主張しません。補助smokeは一度検査コード側の誤ったfield参照で`KeyError`となり、修正後に成功しています。

`git submodule update --init` は共有git configがread-onlyで失敗しましたが、事前の`git submodule status`ではccbenchは既に初期化済みでした。

## 総括

- F-1/F-4/F-6/F-7を所有範囲内で実装し、既存期待値は変更していない。
- generic API、旧writer、consumer、docs、output、commitには触れていない。
- 既存consumerの静的期待赤は全fileで空集合。
- pytestは基盤rc=16で0 node実走のため、全所見をpartialとして返す。