## G1

**closed**

[consumer](/work/1/SFC/tanab/izanagi/.codex/worktrees/rejected-witness-fix2/orchestrator/campaign/reflux_formal_consumer.py:148) で次を閉じました。

- stats の数値を exact int、非負に限定。
- `abort_reasons` を dict、文字列 key、exact int 非負値に限定。
- framing details と notes の list schema を検査。
- permutation counts の固定 3 key、exact int、非負性、合計を検査。
- sample 2 種を list に限定。
- counts の固定 key は consumer 側 frozenset とし、実 verifier 出力との drift assertion を追加。
- bool 要求は既存の `integrity.clean` 以外に追加していません。

## G2

**closed**

- 未知 reason の version 参照を安全化。閉集合 gate を仮に緩める probe でも、後続が例外や二次拒否を起こさず通ることを確認しました。
- `stats`、`integrity`、`permutation_violation_details` の取得を `.get()` に変更。欠落時は型 gate が FC07 を返し、`KeyError` は発生しません。
- `reason-type-outside-closed-set` と `verify_without_stats` は変更後も FC07 で拒否されました。

## 追加した test

- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_string_stats_count` — stats exact int
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_negative_stats_count` — stats 非負性
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_non_dict_abort_reasons` — abort reasons の dict 型
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_string_abort_reason_count` — abort count の exact int
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_negative_abort_reason_count` — abort count の非負性
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_non_list_framing_violation_details` — framing details の list 型
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_non_string_integrity_note` — notes 要素の str 型
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_non_list_integrity_notes` — notes の list 型
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_permutation_count_key_set_mismatch` — counts の exact key 集合
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_non_dict_permutation_counts` — counts の dict 型
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_float_permutation_count` — count の exact int
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_negative_permutation_count_with_matching_sum` — 合計を維持した負数
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_non_list_permutation_sample` — sample の list 型
- `orchestrator/tests/test_reflux_formal_consumer.py::test_fc07_rejects_non_list_unknown_reason_sample` — unknown sample の list 型

既存の `test_real_dense_cycle4_report_schema_matches_consumer_key_sets` も拡張し、実 callee が生成した counts の key 集合を照合しました。

## 受理集合が変わっていないことの確認

G2 の変更は先行 gate に支配されています。

- 未知 reason は従来どおり閉集合 gate で拒否。既知 reason に対する version key は従来と同じ値です。
- exact-key gate を通る payload では `.get()` と添字参照の結果が同一です。
- key 欠落 payload は従来どおり FC07。後続が `KeyError` から型拒否へ変わっただけです。
- no-secondary-rejection probe と対象 2 node の実走が PASS しました。

したがって G2 による受理 payload の増減はありません。

## fixture 無変更の確認

fixture builder と baseline は変更していません。

- `test_exact_fixture_contract_reaches_only_p6_unavailable`: PASS
- 実 verifier schema drift test: PASS
- `git diff --name-only` は許可された 2 ファイルだけです。

## 実走

正規 runner は queue preflight infrastructure failureで child 未起動、rc=16 でした。

許可された `PYTHONPATH=.` 自走 harness:

- `test_reflux_formal_consumer.py`: **134 passed**
- 追加 14 node、G2 2 node、fixture 正例、drift test の明示走: **18 passed**
- G2 no-secondary-rejection probe: PASS
- `git diff --check`: PASS

## 受理集合の差

G1 により追加で拒否されるのは、stats または abort counts の型・非負性違反、notes schema 違反、permutation counts の key・非負性違反、sample 2 種の非 list 値です。提示された `counts={}`, `sample="bad"`, `unknown_reason_sample={}` も拒否されます。

framing details の非 list 値は既存の空 list 関係でも拒否済みで、今回は schema を明示しました。G2 による差はありません。

## 総括

G1 / G2 はともに closed です。  
fixture 無変更で全 consumer test が通過しました。  
変更は指定された 2 ファイルだけです。  
commit と `git add` は行っていません。