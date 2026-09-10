# [T-316] 変異本走の結果 (2026-08-02)

事前登録は `s4-ruling.md` §5 と `mutation-spec.json`。実装後に構造が変わったため、
段 4 の M2 (「opt-in 判定を `True` 固定」) は実効 gate へ再照準した (DW-M01 の F28 規定)。
harness は `tools/mutation_harness.py`、runner は `tools/run_tests.py orchestrator/tests/`、
`--runner-mode dispatch` で Pegasus gen_S 計算ノードへ投入した。anchor は統合 commit
`bb84d44` に対して検証済み (DW-M07)。

## 結果

| ID | 変異 | 期待 | 結果 | 赤くなった node 数 |
|---|---|---|---|---|
| M01 | `CODER_DERIVED` の opt-in 必須拒否を除去 | KILLED | **KILLED** | 11 |
| M02 | 非 `CODER_DERIVED` + opt_in の拒否を除去 | KILLED | **KILLED** | 2 |
| M03 | `pipeline.evaluate()` の `admission` を既定値 `None` 許可へ | KILLED | **KILLED** | 1 (完全一致) |
| M04 | sweep の stock/machine class 判定を潰す | KILLED | **KILLED** | 1 (完全一致) |
| M05 (正例) | `STOCK_OR_PINNED` を opt-in 必須側へ倒す | KILLED | **KILLED** | 15 |

全 5 変異が kill された。受理集合または fail-closed 挙動が期待方向へ変わったことを
確認しており、診断文字列だけの赤は数えていない (DW-M03)。

## M01 が殺した 11 node — gate が全層で歯を持つ証拠

```
test_build_admission.py::test_m1_coder_derived_without_opt_in_has_one_rejection_reason
test_buildcache_v2.py::test_materializer_rejects_unadmitted_coder_before_identity_spy[legacy]
test_buildcache_v2.py::test_materializer_rejects_unadmitted_coder_before_identity_spy[v2]
test_campaign.py::test_build_admission_coder_default_rejects_before_pipeline_build_spy
test_campaign.py::test_build_admission_loop_and_screening_revalidate_before_build_entry_spy
test_p3_exploration_namespace.py::test_coder_driver_without_flag_rejects_before_build_spy[kickoff]
test_p3_exploration_namespace.py::test_coder_driver_without_flag_rejects_before_build_spy[loop]
test_p3_exploration_namespace.py::test_coder_driver_without_flag_rejects_before_build_spy[red]
test_p3_exploration_namespace.py::test_coder_driver_without_flag_rejects_before_build_spy[sort]
test_p3_exploration_namespace.py::test_coder_driver_without_flag_rejects_before_build_spy[trigger_gating]
test_t126_qualification_driver.py::test_qualification_policy_rejects_unadmitted_coder_before_build_spy
```

materializer (legacy と v2 の両方)、`pipeline.evaluate()`、`loop` / `screening`、
coder driver 5 本、qualification のすべてが独立に検出した。

## erratum — 事前登録の不足 (DW-M02)

run-1 は M01 / M02 を `MISMATCH` で記録し、そこで harness が停止した。**gate の弱さではなく
親の登録側の不足である** — `expected_nodes` に単一理由 control 1 本しか書かず、実際には
suite 全体が検出したため、記録 node が期待 node の真の上位集合になった。
初回結果は消さず `mutation-ledger-run1-M01-M02.json` として残す。

M03 / M04 / M05 は run-1 の停止で未走だったため、単独 spec (`mutation-spec-M0*.json` 相当) で
順に走らせ直した。M05 も同じ理由で `MISMATCH` だが、正例として登録した過剰拒否が
15 node で検出されたことが結果である。

次回以降の登録では、単一理由 control と「その変異が殺すべき全 node」を分けて登録する必要がある。
