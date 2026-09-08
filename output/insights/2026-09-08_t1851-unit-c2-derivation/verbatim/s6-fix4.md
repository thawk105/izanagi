## 台帳の構造と行番号 pin の位置

`_DeferredGateMember` は `relative_path`、`owner`、`reason`、`sink_kind`、`sink_scope`、`sink_lineno` を保持します。exact 検査では `reason` を除く 5 要素を比較し、行番号は第 5 要素です。

## 実測した現物の行番号 (親の値との照合)

- `build_cells.invoke_build`: [s8b_floor_campaign.py:4707](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix3/orchestrator/campaign/s8b_floor_campaign.py:4707)。親の値 4707 と一致。
- `main` の `run_campaign`: [s8b_floor_campaign.py:8636](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix3/orchestrator/campaign/s8b_floor_campaign.py:8636)。親の値 8636 と一致。

## 直した entry (file:line と旧値 → 新値)

2 logical entry の本体と exact 期待集合を追随させました。

- [test_ccbench_spawn_sites.py:901](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix3/orchestrator/tests/test_ccbench_spawn_sites.py:901)、鏡像 pin [同ファイル:2676](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix3/orchestrator/tests/test_ccbench_spawn_sites.py:2676): `4715` → `4707`
- [test_ccbench_spawn_sites.py:909](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix3/orchestrator/tests/test_ccbench_spawn_sites.py:909)、鏡像 pin [同ファイル:2680](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-fix3/orchestrator/tests/test_ccbench_spawn_sites.py:2680): `8642` → `8636`

## 変えていないこと (件数・他 file・行番号以外の field)

- 台帳件数は 8 件のままです。
- entry の追加・削除はありません。
- `relative_path`、`owner`、`reason`、`sink_kind`、`sink_scope` は変更していません。
- 他 file、production、`docs/`、`output/` は変更していません。
- 新規 file は作成していません。
- `git` は実行していません。

## 実走した関数と結果

実行:

```text
PYTHONPATH=. python3 orchestrator/tests/test_ccbench_spawn_sites.py
```

最終結果: `44 passed in 108.65s`

対象 3 nodeid はすべて PASS:

- `orchestrator/tests/test_ccbench_spawn_sites.py::test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member`

## 総括

指定された 2 sink の行番号 pin を現物へ追随させ、全 44 件が緑になりました。変更は所有対象のテストファイル内にある行番号 4 箇所だけです。