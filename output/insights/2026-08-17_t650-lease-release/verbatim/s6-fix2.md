## 総括

- R1 はコード上の原因を修正しましたが、pytest 未起動のため判定は `partial` です。
- `_locked_preflight()` の前倒しを撤回し、active plan だけを最小経路で再観測します。
- rc=29、status=`rejected`、reason の発火順序を固定する新規テストを追加しました。
- 指定 3 node は実行要求済みですが、dispatch infrastructure rc=16 のため実装済み・未実走です。
- 構文検査と `git diff --check` は成功しました。
- docs は編集せず、commit も作成していません。

| 所見 | 状態 | 対応 |
|---|---|---|
| R1 | partial | 実装修正・回帰テスト追加済み。pytest 未起動 |
| F5 の目的維持 | partial | active plan 不在なら rc=21 を release-safe、有れば保持する実装を維持。未実走 |
| regressed | なし | 静的検査で検出なし |

修正箇所は [tools/dev_wave_land.py:2861](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2861) です。再取得後は `_control_snapshot()` を比較し、control 変更時だけ `preflight.fold.load_active_plan(repository.main)` を呼びます。その結果だけを rc=21 の `release_safe` 判定に使用します。

head・collision fingerprint は全 preflight より先に再計算し、変化時は従来どおり rc=29 と `"main/wave heads or collision paths changed during the provenance audit"` を返します。その検査を通過した後だけ [tools/dev_wave_land.py:2907](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/tools/dev_wave_land.py:2907) で全 `_locked_preflight()` を実行します。

追加 node:

- `orchestrator/tests/test_dev_wave_land.py::test_post_provenance_head_change_preserves_provenance_rejection_order`  
  [test_dev_wave_land.py:2871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/orchestrator/tests/test_dev_wave_land.py:2871)

この node は全 preflight が初回の1回だけであることに加え、rc=29、status、reason の完全一致を固定します。

実走要求した node:

- `test_provenance_receipt_rejects_tip_that_moves_during_audit`
- `test_post_provenance_head_change_preserves_provenance_rejection_order`
- `test_post_provenance_reacquire_rejects_control_directory_replacement`

結果は dispatch rc=16、pytest 実行数 0 です。receipt は [receipt.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t650-lease-release/output/pegasus-dispatch/45f4409d1eed100cf9bd96ed0ad15f96/receipt.json) にあります。緑とは報告しません。