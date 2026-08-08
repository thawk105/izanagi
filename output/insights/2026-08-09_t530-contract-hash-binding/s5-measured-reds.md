# 親が計算ノードで実測した赤 (段 5 実装差分、未 commit の working tree)

走行: `python3 tools/run_tests.py --force-dispatch <identity 関連 16 file> -q -rf`
結果: **7 failed / 1157 passed / 10 skipped** (rc=1)。log = `s5-subset.log`。
段 4 裁定で事前指定した「期待赤」(campaign-id literal pin) は実装子が更新済みで、
下の 7 件はいずれも**事前指定に無い回帰**である。

## 回帰 1 — guided lane が identity 必須検査で落ちる (2 件)

- `test_guided.py::test_cmd_evaluate_repairs_committed_tail_before_four_new_frames`
- `test_guided.py::test_cmd_start_atomic_loser_is_structured_and_touches_no_meta_or_wal`

逐語 (抜粋):

```
orchestrator/tests/test_guided.py:280: in test_...
    ident.ensure_resumable_wal(
        guided._trial_config(meta, trial), layout,
        admission_policy=guided._NO_BUILD_POLICY,
    )
orchestrator/campaign/ident.py:246: in ensure_resumable_wal
    ensure_campaign_identity(
orchestrator/campaign/ident.py:305: in ensure_campaign_identity
    preimage = canonical_preimage(
...
require_environment_contract = True
```

実装子は「guided / legacy lane は環境契約 key の欠落を引き続き受理する」と報告したが、
`ensure_resumable_wal` の既定が `require_environment_contract=True` であり、
guided の呼出し形では exemption が効いていない。

## 回帰 2 — trigger gating の contract 注入 seam を迂回して ambient registry を引く (4 件)

- `test_p3_s4_loop_trigger_gating.py::test_fresh_default_seams_flow_distinct_contract_to_measurement_sink`
- `test_p3_s4_loop_trigger_gating.py::test_fresh_default_seams_flow_distinct_contract_to_reject_sink`
- `test_p3_s4_loop_trigger_gating.py::test_contract_sentinel_flows_to_run_campaign`
- `test_p3_s4_loop_trigger_gating.py::test_empty_numactl_contract_flows_as_empty_list`

逐語 (抜粋):

```
orchestrator/campaign/env_contract.py:665: in lookup
    return REGISTRY[env_tag]
orchestrator/campaign/env_contract.py:575: in __getitem__
    return _authority_snapshot().current[env_tag]
E   KeyError: 'linux-baremetal'
```

テストは synthetic な authority を活性化し、`lookup` を注入 seam として差し替えている。
実装がその seam を通さず ambient registry を引いているため KeyError になる。
段 2 プラン §7 は「ambient current-registry lookup を layout helper 内で行わない」と
明記しており、これに反している可能性が高い。

## 回帰 3 — exploration namespace の run context 照合 (1 件)

- `test_p3_exploration_namespace.py::test_coder_driver_flag_reaches_build_spy_with_exact_run_context[trigger_gating]`
