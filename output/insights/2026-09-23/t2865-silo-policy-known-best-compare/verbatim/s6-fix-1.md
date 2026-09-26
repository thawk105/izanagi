## 直した内容

- **R1:** `compare` の巡回を `job % 6` に修正し、8 job の期待列を独立した literal で列挙しました。[実装](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/campaign/silo_policy_recon.py:43)・[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/tests/test_silo_policy_recon.py:233)
- **R2:** `BACK_OFF` と `BACKOFF_FIXED` の define 列がそれぞれ指定値 1 個だけの場合に受理するよう修正し、`BACK_OFF` 重複の負例を追加しました。[実装](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/campaign/silo_policy_recon.py:82)・[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/tests/test_silo_policy_recon.py:393)
- **R3:** `_build_variant` を実際に呼び、configure に渡る argv の fixed10 引数を検査する test を追加しました。新引数を省いた呼び出しも確認します。[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/tests/test_silo_policy_coverage.py:578)
- **R4:** 各 file の `case_order` を予定列と照合し、不一致の負例を追加しました。[実装](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/campaign/silo_policy_recon.py:392)・[fixture と test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/tests/test_silo_policy_recon.py:220)

## 確認の実測

`python3 -m py_compile` は **rc=0**、`git diff --check` も **rc=0** でした。純関数への合成入力で得た case_id 列は次のとおりです。

```text
0 0000 1111 abort0 stock B0-L-W0 fixed10
1 1110 abort0 stock B0-L-W0 fixed10 0001
2 abort0 stock B0-L-W0 fixed10 0010 1101
3 stock B0-L-W0 fixed10 0011 1100 abort0
4 B0-L-W0 fixed10 0100 1011 abort0 stock
5 fixed10 0101 1010 abort0 stock B0-L-W0
6 0110 1001 abort0 stock B0-L-W0 fixed10
7 1000 abort0 stock B0-L-W0 fixed10 0111
```

`_backoff_fixed_defines_effective` の実出力は、正例 `True`、欠落 `False`、値違い `False`、`BACK_OFF` 重複 `False` でした。

test は**実装済み・未実走**です。対象 node は `test_compare_cases_rotate_by_job`、`test_compare_fixed10_define_check_rejects_duplicate_back_off`、`test_build_variant_passes_backoff_fixed_to_configure`、`test_compare_aggregate_rejects_case_order_mismatch`、および共通 fixture を使う `test_compare_aggregate_uses_best_reference`、`test_compare_aggregate_null_when_reference_ineligible`、`test_compare_aggregate_rejects_wrong_order`、`test_compare_aggregate_rejects_fixed10_flag_mismatch`、`test_compare_aggregate_floor_boundary` です。

## 波及

所有外では、既存の比較結果を読む `compare-aggregate` が `case_order` 欠落・不一致を拒否するようになります。現行の `run --phase compare` は同フィールドを出力しています。`materializer_admission.py` の build 登録、`test_silo_policy_smoke_entry.py` の coverage 利用、`test_p3_build_authority_cli.py` と `test_ccbench_spawn_sites.py` の build site 監査に関係しますが、これらのファイルは変更していません。変更ファイルは許可された 3 ファイルだけです。

## 総括

R1〜R4 を修正し、構文と指定された純関数の実出力を確認しました。pytest・build・計測は実行していません。