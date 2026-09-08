## 実装内容

指定された 4 ファイルだけを編集しました。

- [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-d/orchestrator/campaign/condition_meaning_gate.py:124): define 登録と供給 domain 数 38 への更新。
- [screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-d/orchestrator/campaign/screening_driver.py:62): 既定値 `0` を追加。
- [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-d/orchestrator/tests/test_condition_meaning_gate.py:2537): route、patch、owner TU、実行体、companion、inert 値を exact 比較。
- [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-d/orchestrator/tests/test_screening_driver.py:563): 既定値と生成 request を exact 比較。

commit、git add、branch 操作、push は行っていません。

## 追加した spec の逐語

```text
macro = "BACKOFF_TRACE_TERMINAL_US"
route = "cmake-cache-option"
owner_tus = ("cc/silo/transaction.cc",)
target = "ycsb_silo.exe"
patch_rel = "patches/cicada-adaptive-counterfactual.patch"
companion_defines = ()
inert_values = ("0",)
```

patch owner は patch C、実行体は `ycsb_silo.exe` です。screening 既定値は整数 `0` です。

## inert 値が `"0"` で正しい理由

patch C は CMake option を既定 `0`、説明も `0=off` としています。[patch 15 行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-d/patches/cicada-adaptive-counterfactual.patch:15)

terminal handler は `kTraceTerminalUs == 0` の場合、event の記録前に `false` を返します。[patch 350 行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-d/patches/cicada-adaptive-counterfactual.patch:350) したがって値 0 では terminal 計装が発火せず、inert 値 `"0"` が実物と一致します。

## 実走結果

標準入口で次の 6 nodeid を指定しましたが、`qstat -Q` preflight に失敗して `rc=16`、`child_started=false` でした。

実装契約の自走 harness で同じ 6 nodeid を実行し、すべて通過しました。

- `test_condition_meaning_gate.py::test_v1_domain_and_claim_boundaries_are_exact`
- `test_condition_meaning_gate.py::test_counterfactual_specs_are_exact`
- `test_condition_meaning_gate.py::test_define_inventory_includes_counterfactual_defaults`
- `test_condition_meaning_gate.py::test_module_claim_names_the_exact_38_define_supply_domain`
- `test_screening_driver.py::test_screening_condition_requests_cover_exact_define_specs`
- `test_ccbench_spawn_sites.py::test_patch_define_inventory_matches_condition_gate_registry`

追加で次の consumer meta-test も自走し、通過しました。

- `test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member`

範囲は targeted 7 nodeid、7 passed です。両 test file の全体走行は実装済み・未実走です。`git diff --check` は通過し、所有 4 ファイルに U+0300 から U+036F はありません。

失敗 dispatch が生成した ignored 一時ディレクトリだけは所有境界を戻すため削除しました。再実行で再生成できます。

## 所有外 caller・consumer への波及可能性

- `orchestrator/tests/test_ccbench_spawn_sites.py`: patch define inventory と build-sink cross product。編集せず、両 meta-test が通過。
- `orchestrator/campaign/backoff_sweep.py`: 独自の閉じた既定表を持つため、新 macro を渡す将来経路では未宣言 default として fail-closed。
- `orchestrator/campaign/s1_direct_comparison.py`: 同様に独自既定表があり、新 macro を直接渡すと fail-closed。
- `tools/pegasus/probes/t2228_driver_gate_liveness_probe.py`: `s1_direct_comparison` の既定表を参照するため、terminal flag を持つ freeze cell では追随が必要になり得る。
- `orchestrator/campaign/silo_ladder_rung1.py`: registry の companion define を参照する。今回の spec は companion なしなので既存 request には影響しない。
- `orchestrator/tests/condition_gate_test_support.py`: `DefineSpec.owner_tus` を利用する fixture helper。今回の単一 Silo owner 形式と互換。
- unit B の probe、PBS、parser test、および `test_dynamic_backoff_transitions.py` の実 parser consumer は raw v3、terminal、CMake 引数の追随対象。

## 所有外なので触らなかった file

- `patches/cicada-adaptive-counterfactual.patch`、`patches/README.md`、`test_dynamic_backoff_transitions.py`: unit A 所有。実物確認だけ実施。
- `test_ccbench_spawn_sites.py`: 必須 meta-test は既存の動的 inventory で通ったため、所有外の期待値を変更せず実走だけ実施。
- unit B の `t2187_adaptive_const_probe.py`、PBS、関連 test: parser と実行引数の追随は unit B の責務。
- `backoff_sweep.py`、`s1_direct_comparison.py`、`t2228_driver_gate_liveness_probe.py`:独自の閉じた受理範囲を無断で広げないため。
- `docs/`、凍結事前登録、cohort 1 解析器:契約上の所有外かつ変更禁止。

## 総括

実装内容: terminal define の exact spec、供給 domain 38、screening 既定値 0、厳密 test を所有 4 ファイルへ追加。  
実走結果: targeted 7 nodeid は 7 passed、必須の patch 実物 inventory meta-test も緑。  
残っている赤: 今回の実走範囲にはなし。unit A 報告済みの実 parser consumer は unit B 未統合のため、今回未実走の既知赤。