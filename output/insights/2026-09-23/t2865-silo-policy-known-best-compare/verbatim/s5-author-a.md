## 実装した内容

[silo_policy_coverage.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/campaign/silo_policy_coverage.py:363) の `_build_variant` に fixed10 用 genome 引数を追加し、[_source](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/campaign/silo_policy_coverage.py:556) に stock 専用の backoff patch 適用と全 marker 確認を追加しました。patch には既存の `applied(...)` を選びました。既存の骨格 patch と同様、処理終了時や例外時に stock 木を復元できるためです。

[silo_policy_recon.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/campaign/silo_policy_recon.py:35) に compare の巡回順、fixed10、trace1・trace0 各 build 直後の owner TU define 検査、独立した [compare 集計](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/campaign/silo_policy_recon.py:366) と CLI を追加しました。検査不成立時は `backoff-fixed-not-effective` で後続の verify または bench を止めます。集計は8 job の順序・本文・flags・実効 define を照合し、欠格した参照を含む最良参照比を null にします。投影は書きません。

指定された9件の変異対象 test と拒否 test を [test_silo_policy_recon.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/tests/test_silo_policy_recon.py:232) に追加し、[test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py:2936) は build sink の行番号 pin だけを追随させました。

## 確認の実測

`python3 -m py_compile` は変更した Python 4 ファイルを含めて **rc=0** でした。`_cases("compare", j, None)` の case_id 実出力は次のとおりです。

```text
0: 0000 1111 abort0 stock B0-L-W0 fixed10
1: 1110 abort0 stock B0-L-W0 fixed10 0001
2: abort0 stock B0-L-W0 fixed10 0010 1101
3: stock B0-L-W0 fixed10 0011 1100 abort0
4: B0-L-W0 fixed10 0100 1011 abort0 stock
5: fixed10 0101 1010 abort0 stock B0-L-W0
6: 0110 1001 abort0 stock B0-L-W0 fixed10
7: 0111 1000 abort0 stock B0-L-W0 fixed10
```

合成8 job の純関数集計は適格16点、null 0件、超過0点でした。参照中央値を stock=80、B0-L-W0=100、fixed10=110、IR=120 にした入力では `best_ref_ratio=1.0909090909090908`、参照別比は `1.5 / 1.2 / 1.0909090909090908` でした。同じ入力で fixed10 の verify を非 certified にすると最良参照比は null、理由は `reference-ineligible` となり、他の2本との比は残りました。境界入力の 1.02 は非超過、1.04 は超過でした。

configure は掛けていないため、実 build の owner TU define 出力はありません。test は**実装済み・未実走**です：`test_compare_fixed10_genome_and_build_args`、`test_source_backoff_fixed_patch_materializes_markers`、`test_compare_fixed10_define_check_rejects_missing_define`、`test_compare_aggregate_uses_best_reference`、`test_compare_aggregate_null_when_reference_ineligible`、`test_compare_aggregate_rejects_wrong_order`、`test_compare_aggregate_rejects_fixed10_flag_mismatch`、`test_compare_cases_rotate_by_job`、`test_compare_aggregate_floor_boundary`、`test_build_variant_backoff_fixed_rejects_non_stock`。

## 現行の受理・拒否挙動と波及

従来の `stock_backoff ∈ {0,1}` と非 stock では `stock_backoff=1` という制約は維持しました。新引数を省略した `_source` は従来どおり stock を無 patch で扱い、`_build_variant` は従来と同じ genome と configure argv を組み立てます。`initial`・`remeasure` の列、既存 `aggregate`、検証・bench の回数と workload は変更していません。

所有外では `test_silo_policy_smoke_entry.py` が coverage を使用し、`materializer_admission.py` が build materializer を登録しています。`test_p3_build_authority_cli.py` はその build sink を監査します。これらと共有 fixture は編集していません。subprocess site の閉集合 test は行番号 pin のみ更新しました。

## 未了と疑問

親が行う計算ノードでの test、実 patch 適用・configure による define 実測、および変異 test の kill 確認は未了です。今回の制約に従い pytest・build・計測は起動していません。

## 総括

compare と fixed10 の実装、集計、指定 test を作成しました。構文確認と合成入力での集計確認は通過しています。実 build と test の受入判定は未実走です。