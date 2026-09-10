# 変異走の結果 (要約)

完全な台帳は同 directory の `mutation-ledger.json` (schema `izanagi-dev-wave-mutation/v4`)、
事前登録は `mutation-spec.json`。本書はその読み方を示す要約である。

## 走行条件

```
repo_head          ca8b14c61bb6fb0cda9e351f45d021c5af883390
spec_sha256        f8e51777e56dcd3e36397191306ffa374b1d199066ee25c8f7cd071df8891e3a
runner_mode        dispatch (計算ノード)
runner argv        python3 tools/run_tests.py \
                     orchestrator/tests/test_p3_b4_wiring_probe.py -rf --force-dispatch
tool               tools/mutation_harness.py
date               2026-09-03T12:29:29Z 〜 12:35:41Z
```

対象 file 集合は 1 file である。変更した production file
(`orchestrator/campaign/p3_b4_wiring_probe.py`) を参照する consumer test を
`DW-O26` に従い参照関係で引いたところ、`orchestrator/tests/test_p3_b4_wiring_probe.py`
だけだった (名前の推測ではなく `grep -rln` で確認)。

## 結果

```
summary: KILLED=6 SURVIVED=0 MISMATCH=0 TIMEOUT=0 PARSE_ERROR=0
         registered=6 recorded=6 completed=6 matching=6
baseline (走行前): PASSED  63 passed in 9.28s
baseline (走行後): PASSED
```

| ID | 変異 | 結果 | 期待一致 | 実際に赤になった node |
|---|---|---|---|---|
| M-A1 | byte slice を文字 slice にする | KILLED | true | 境界 |
| M-A2 | form feed でも行分割する | KILLED | true | 境界 |
| M-A3 | 複数行の連結で改行を落とす | KILLED | true | 全 module + 境界 |
| M-A4 | helper を使わず旧経路へ戻る | KILLED | true | 配線 + 分割回数 |
| M-A5 | 分割を `if` ごとに行う | KILLED | true | 分割回数 |
| M-A6 | `or ast.unparse(...)` の fallback を落とす | KILLED | true | 配線 |

node 名は次のとおり (すべて `orchestrator/tests/test_p3_b4_wiring_probe.py::`)。

- 全 module = `test_source_segment_helper_matches_stdlib_for_all_static_ifs`
- 境界 = `test_source_segment_helper_matches_stdlib_at_boundaries`
- 配線 = `test_analyze_source_preserves_guard_wiring_and_fallback`
- 分割回数 = `test_analyze_source_splits_each_module_exactly_once`

## 単一理由性の確認 (`DW-M01`)

guard 文字列は `_build_inventory` と `guard.seal` を通らず、`_proof_switchpoint` が選ぶ
edge の証拠 JSON と digest へだけ流れる。段 2 が file:line で追跡し、段 3 のレンズ A が
独立に追認した。したがって各変異の前後・内側に同じ入力を拒否する別の層は無い。

M-A3 は全 module 比較と境界の両方が赤になった。M-A4 は配線と分割回数の両方が赤になった。
いずれも事前登録の `expected_nodes` を完全集合として登録済みで、`DW-M08` の完全一致を満たす。

## この走行が確かめた最重要の性質

**M-A4 と M-A5 は「修正が入っていないのに全テストが緑になる」形である。**

- M-A4 は `_analyze_source` を旧経路 (`ast.get_source_segment` を `if` ごとに呼ぶ) へ戻す。
- M-A5 は分割を `if` ごとに行い、二乗を復活させる。

どちらも guard 文字列は正しいままなので、helper の等価性テストだけでは検出できない。
段 3 のレンズ A がこの穴を指摘し、段 4 が単位 C を 4 本に割ることを must-fix として裁定し、
段 6 のレンズ D が「呼び出し回数だけでは死んだ 1 回呼び出しを残す実装が通る」と追加で指摘して
返り値の同一性 (`lines is split_results[0]`) まで pin させた。

**両方 KILLED であり、二乗の再発は検出される。**

## 実データで殺せない故障型 (合成 fixture が唯一の検出経路)

親が 45 module / `if` 3282 個を走査した結果:

| 故障型 | 実データでの到達 |
|---|---:|
| guard の前に非 ASCII がある行 (M-A1 が要る) | **0 件** |
| form feed 等を含む module (M-A2 が要る) | **0 件** |
| 複数行にまたがる `if.test` (M-A3 が要る) | 353 件 |

45 module 中 36 個が非 ASCII を含むにもかかわらず、`if` の `col_offset` より前に
非 ASCII がある行は 1 つも無い。**実 corpus の網羅性は入力の多様性を意味しない。**
