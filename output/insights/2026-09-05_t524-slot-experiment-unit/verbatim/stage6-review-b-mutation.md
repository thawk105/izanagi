## 所見

- **must-fix** — `orchestrator/campaign/s8c_acceptance_receipt.py:1545`, `orchestrator/tests/test_s8c_acceptance_receipt_v2.py:990`  
  attempt registry 由来の projection と receipt 記載値の exact 再照合に変異 killer がない。1545 行を `if False:` にしても、M3 は projection を変更せず terminal だけを欠落させるため、1592 行の消費検査で従来どおり期待例外となり、全テストが緑のままになる。generation、slot_id、unit_count、units のいずれかだけを改変した receipt の負例が必要である。  
  **放置時:** tracked registry と異なる slot projection を宣言した receipt まで verified となり、受理集合が広がり、成果物に記録された事前登録参照が現物と食い違う。

## 述語ごとの変異耐性

1. v3 reader の root 単一 generation 検査  
   対象: `orchestrator/campaign/attempt_registry_core.py:742`  
   742 行を `if False:` にすると、`orchestrator/tests/test_trial_registry.py::test_m1_v3_reader_accepts_single_generation_and_rejects_mixed_generation` が `DID NOT RAISE TrialRegistryError` で赤くなる。fixture は generation だけを 13 から 14 に変え、chain を再計算している (`orchestrator/tests/test_trial_registry.py:6463`)。series key は generation を含まない (`orchestrator/campaign/trial_registry.py:1958`) ため、別層の先行拒否はない。

2. genesis 作成器の引数と全 slot の exact 一致  
   対象: `orchestrator/campaign/trial_registry.py:2496`  
   2496 行を `if False:` にすると、`orchestrator/tests/test_trial_registry.py::test_m2_genesis_creator_requires_exact_slot_generation` が `DID NOT RAISE TrialRegistryError` で赤くなる。引数 14 は正の整数で、slot 群は単一 generation 13 のままなので、core reader は拒否しない (`orchestrator/tests/test_trial_registry.py:6534`, `orchestrator/tests/test_trial_registry.py:6542`)。

3. verifier の attempt registry 再照合と全 unit 消費  
   対象 gate: `orchestrator/campaign/s8c_acceptance_receipt.py:1796`  
   1796 行を `if False:` にすると、`orchestrator/tests/test_s8c_acceptance_receipt_v2.py::test_m3_v5_rejects_predeclared_unit_without_final_terminal` が `DID NOT RAISE AcceptanceReceiptError` で赤くなる。  
   全 unit 検査の 1592 行を `if False:` にした場合も同 nodeid が赤くなるが、理由は期待した `AcceptanceReceiptError` ではなく、続く `finals[0]` (`orchestrator/campaign/s8c_acceptance_receipt.py:1597`) の `IndexError` になる。  
   一方、projection exact 再照合の 1545 行を `if False:` にしても赤くなるテストはない。したがって述語 3 は、helper 全体と消費側には耐性があるが、再照合側には耐性がない。

## 過剰決定な fixture

なし。M1 は generation 変更後に chain を再計算している (`orchestrator/tests/test_trial_registry.py:6463`)。M3 は完全版 registry を一度も commit せず、terminal 欠落版を最初の tracked state として receipt と同時に commit するため (`orchestrator/tests/test_s8c_acceptance_receipt_v2.py:995`)、append-only 層による先行拒否を避けている。

## テストの弱化

なし。差分内に既存テストの削除、skip、xfail 化、または例外条件の緩和はない。旧 v2 golden vector も維持され、新しい v3 vector と並置されている (`orchestrator/tests/test_trial_registry.py:7043`)。

## 総括

M1 と M2 は対象述語だけを無効化すると明確に赤くなり、段 3 の過剰決定問題は解消されている。  
M3 の全 unit 消費と top-level gate にも実効的な負例がある。  
ただし attempt registry と receipt projection の exact 再照合だけは変異が生き残るため、must-fix が 1 件ある。  
正例は実体の `verify_acceptance_receipt` を通り、producer から verifier までの統合正例も存在する (`orchestrator/tests/test_trial_registry.py:1652`)。  
揮発 prefix hash は明示的に分類され (`orchestrator/tests/test_reflux_originless_compatibility.py:205`)、golden vector の変更理由と v2 不変範囲も記録されている。