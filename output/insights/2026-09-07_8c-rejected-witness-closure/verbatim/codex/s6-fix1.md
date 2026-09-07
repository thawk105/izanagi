## F1

**closed**

[reflux_formal_consumer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/rejected-witness-fix1/orchestrator/campaign/reflux_formal_consumer.py:896) を厳格化しました。

- `length`、edge endpoint を exact int に限定。
- cycle 長を 2 以上に限定。
- `WW` / `WR` / `RW` を production 正本から import。
- `types`、phenomenon、version field の導出関係を検査。
- version を exact int 2 要素に限定。

## F2

**closed**

production と一致する `verify`、`stats`、`integrity`、permutation details の frozenset を追加しました。

- 4 階層の key 集合を exact 検査。
- `clean=True` の必要条件として wire 上の 11 counter を exact int かつ 0 に限定。
- framing detail と permutation count の導出関係を検査。
- 必要条件であって十分条件ではない旨をコードコメントに明記。
- 実際の `verify_trace_dir()` 出力との drift test を追加。

## F3

**closed**

boolean counter 負例を次の単一理由 test に分離しました。

- `total_cycles=True, anomaly_count=1`
- `total_cycles=1, anomaly_count=True`

既存の期待 reason は変更していません。

## 追加した test

F1:

- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_each_malformed_witness_structure[length-float]` — `length` exact int
- `...::test_fc07_rejects_each_malformed_witness_structure[single-node-cycle]` — cycle 長 2 以上
- `...::test_fc07_rejects_each_malformed_witness_structure[edge-from-float]` — `from` exact int
- `...::test_fc07_rejects_each_malformed_witness_structure[edge-to-float]` — `to` exact int
- `...::test_fc07_rejects_each_malformed_witness_structure[reason-type-outside-closed-set]` — reason type 閉集合
- `...::test_fc07_rejects_each_malformed_witness_structure[types-not-derived-from-reasons]` — `types` 導出
- `...::test_fc07_rejects_each_malformed_witness_structure[phenomenon-not-derived-from-types]` — phenomenon 導出
- `...::test_fc07_rejects_each_malformed_witness_structure[reason-version-not-two-elements]` — version 長
- `...::test_fc07_rejects_each_malformed_witness_structure[wr-reason-has-v-ver]` — WR version field
- `...::test_fc07_rejects_each_malformed_witness_structure[ww-reason-missing-u-ver]` — WW version field
- `...::test_fc07_rejects_each_malformed_witness_structure[rw-reason-missing-v-ver]` — RW version field

F2:

- `...::test_real_dense_cycle4_report_schema_matches_consumer_key_sets` — production schema drift positive control
- `...::test_fc07_rejects_verify_without_stats` — verify top-level key 集合
- `...::test_fc07_rejects_stats_with_missing_key` — stats key 集合
- `...::test_fc07_rejects_integrity_with_missing_key` — integrity key 集合
- `...::test_fc07_rejects_permutation_details_with_missing_key` — permutation details key 集合
- `...::test_fc07_rejects_clean_integrity_with_nonzero_wire_counter` — clean counter
- `...::test_fc07_rejects_zero_framing_count_with_nonempty_details` — framing detail
- `...::test_fc07_rejects_permutation_count_sum_mismatch` — permutation count 導出

F3:

- `...::test_fc07_rejects_boolean_total_cycles`
- `...::test_fc07_rejects_boolean_anomaly_count`

## fixture 無変更の確認

fixture builder と baseline は変更していません。共有 fixture を使う consumer 正例は通過しました。

- `test_exact_fixture_contract_reaches_only_p6_unavailable`: PASS
- 実 verifier anomaly positive control: PASS
- baseline 独立再計算: `1 passed`
- pin の変更なし

## 実走

正規 runner は Pegasus dispatch infrastructure error で `rc=16`、child 未起動でした。

許可された自走 harness の結果:

- `orchestrator/tests/test_reflux_formal_consumer.py`: **120 passed**
- fixture baseline 独立再計算 node: **1 passed**
- `git diff --check`: PASS

## 波及可能性

静的に確認した production caller:

- `p3_autonomous_workload_trial.py`
- `reflux_origin_client.py`
- `trial_registry.py`

共有 fixture の直接 consumer は formal consumer、P3、origin artifacts/binding/client/topology、result evidence、source closure、trial registry 各 testです。`test_reflux_originless_compatibility.py` は P3 helper 経由、`test_ccbench_spawn_sites.py` は production file scan 経由です。fixture bytes が不変なので pin 波及はありません。

## 受理集合の差

追加で拒否されるのは次の payload です。

- float/bool の length・endpoint、1-node cycle
- 未知 reason type、reason と `types` の不一致、誤った phenomenon
- 長さ不正または reason type と存在関係が合わない version field
- production schema と key 集合が異なる verify payload
- `clean=True` と非ゼロまたは非 int counter の自己矛盾
- framing count/detail、permutation count/detail の導出不一致

F3 は test 帰属の修正だけで、production の受理集合は変えません。

## 総括

F1 / F2 / F3 はすべて closed です。  
指定された 2 ファイルだけを変更しました。  
fixture 正例と全 consumer test は通過しました。  
commit と `git add` は行っていません。