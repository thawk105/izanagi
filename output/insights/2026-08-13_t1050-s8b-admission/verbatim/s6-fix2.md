## 系統ごとの根本原因

1. pin 不一致

   production は oracle の `run_contract["ccbench_pin"]` を外部権威として照合しており、この取得元が正当でした。一方、fixture の receipt は floor protocol の pin で発行されるのに、oracle manifest fixture が `fixture-pin` を固定していたことが原因です。

   ratified generation が束縛する floor protocol から pin を読み、binding と `run_contract` の両方へ渡すよう修正しました。pin 欠落も必須添字参照で fail-closed にしています。支配的 7 件に加え、先行 refusal で `events` が消えた transient retry も同じ修正対象です。

2. `contract_sha256` の `KeyError`

   2 件とも record／receipt ではなく、contract を持たない既存の direct assembly seam に対する `protocol["contract_sha256"]` の無条件参照が原因でした。`protocol.get()` に修正しました。互換 loader や backfill は追加していません。

   live 経路は、その前段の store／portable projection が `contract.contract_sha256` を必須外部期待値として検査するため、R-A1 は維持されています。

3. manifest golden

   production の `build_cells`、`assemble_manifest`、実 serializer を呼ぶ導出 probe で再計算しました。再導出値は現在の literal と一致しており、golden の変更は不要でした。焦点走の赤は SHA 不一致ではなく、系統 2 の先行 `KeyError` でした。

4. real-repo の cell path 漏出

   段 5 で test-only `_make_real_freeze_prepare()` が base `external/ccbench` を `external/ccbench/<cell>` に変更した回帰でした。production は渡された `PreparedCell.ccbench_dir` を正しく使用しています。fixture を base root に戻し、既存期待値を変更せず修正しました。

## 再導出した golden 値

`4860905ed2c9bf994886564bad0b3185f3d6e512230e85db43e57503f261fbc8`

現在の literal と一致しました。

## 維持確認

- R-A1: current policy、必須 `run_contract` pin、contract の外部照合を維持。
- R-B1: subject、record、external tuple の三者照合を維持。
- R-A2: historical は current policy 非依存、cell 間 policy 一意性を維持。
- R-A3: 全 runtime record の preflight 完了後にのみ store directory と bytes を作成。
- M3: `subject.binary_sha256 == record.binary_sha256` の独立 gate を維持。
- M4: cell／holdout／configuration／entry／binding の完全 tuple gate を維持。
- schema 移行、互換 loader、遡及再取得、受理集合の拡大は実装していません。

## 実装した変更

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:1639): contract 非保持の direct assembly seamで無条件添字参照を廃止。
- [s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_oracle_driver.py:948): oracle pre-run の外部 pin を必須 `run_contract` field に束縛。
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_oracle_driver.py:1678): manifest fixture の pin を引数化。
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_oracle_driver.py:4303): ratified floor protocol の pin を fixture の binding／run contract に使用。
- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_floor_campaign.py:1181): real-repo fixture の `ccbench_dir` を base root に復元。

docs、非接触 production、tracked freeze、V1 trust root は変更していません。commit と `git add` も行っていません。

## 実走結果

以下を `python3 tools/run_tests.py` 経由で個別投入しましたが、全件 pytest collection 前に `qstat -Q preflight rc=1` で停止し、各 `rc=16` でした。

- `test_real_seal_protocol_to_floor_official_core_e2e@real-repo`
- `test_floor_manifest_golden_stable`
- `test_v2_store_hash_mismatch_is_refused`
- `test_v2_store_missing_is_refused`
- `test_v2_floor_disk_swap_after_launch_uses_same_validated_object`
- `test_legacy_resume_manifest_without_perf_preflight_is_not_backfilled`
- `test_v2_gate_happy_path_completes_and_binds_env_store_receipt`
- `test_v2_store_bytes_are_checked_against_admission_subject_independently`
- `test_v2_completed_driver_adapter_campaign_is_accepted_by_report`
- `test_v2_binary_mismatch_abort_maps_to_binary_mismatch_outcome`
- `test_transient_prepare_failure_retries_once`

したがって緑とは申告しません。

静的検査は以下が rc=0 です。

- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`
- AST／compile、NFC、結合文字不在
- `git diff --check`
- docs、非接触対象、tracked freeze の差分不在
- staged 差分不在

`git submodule update --init` は Git 管理領域が read-only のため config lock を作れず失敗しました。submodule 自体は `511c953…` で初期化済みです。

## 期待値を疑った箇所

ありません。既存テストの期待値は変更していません。系統 3 は期待値変更ではなく、再導出値が既存 literal と一致することを確認しました。

## 総括

- 11 件を 4 系統へ分解し、3 箇所の fixture／production 回帰を修正しました。
- pin 不一致は外部権威ではなく、oracle manifest fixture の固定 pin が原因でした。
- production の pin／contract 外部照合は削除も任意化もしていません。
- contract 欠落 seam の無条件参照を除き、backfill や互換 loader は追加していません。
- golden は production serializer から再導出し、既存値との一致を確認しました。
- real-repo の cell path 漏出は test-only materializer を base root へ戻しました。
- R-A1、R-B1、R-A2、R-A3、M3、M4 は維持されています。
- pytest は dispatch 障害で未実走のため、親環境での再測定が必要です。