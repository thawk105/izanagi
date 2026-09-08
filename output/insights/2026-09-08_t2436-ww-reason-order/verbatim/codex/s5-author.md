## 変更した file と diff

- `orchestrator/verifier/dsg.py:524`
  - WW 共通 key の走査を `sorted(...)` に変更。
- `orchestrator/tests/test_verifier.py:1592`
  - `test_multi_ww_reason_report_is_hash_seed_deterministic` を追加。

```diff
-for k in u_writes.keys() & v_writes.keys():
+for k in sorted(u_writes.keys() & v_writes.keys()):
```

テストでは seed `1` / `777` の report bytes、昇順 WW 理由列、指定された判定値だけを検査しています。`certified` と SHA-256 は assert していません。

`git diff --check` は成功しました。`git add`、`git commit`、docs・fixture・台帳の編集は行っていません。

## 実走した nodeid と結果

実行コマンド:

```text
PYTHONPATH=. python3 orchestrator/tests/test_verifier.py
```

結果:

```text
106 passed, 0 failed, 0 skipped
```

主な nodeid 相当:

- `orchestrator/tests/test_verifier.py::test_multi_ww_reason_report_is_hash_seed_deterministic` — PASS
- `orchestrator/tests/test_verifier.py::test_all_v2_fixture_files_have_clean_framing` — PASS
- `orchestrator/tests/test_verifier.py::test_structured_report_has_edge_detail` — PASS
- `orchestrator/tests/test_verifier.py::test_broken_silo_norw_structured_report_is_exact` — PASS
- `orchestrator/tests/test_verifier.py::test_parallel_edge_replay_uses_global_logical_ordinal` — PASS
- `orchestrator/tests/test_verifier.py::test_serial_parent_optimizations_match_workers_and_pin_witness_order` — PASS

自走 runner の出力に新設テストが現れており、引数なし `test_` 関数として収集されたことも確認済みです。pytest 系は明示された制約に従い未実走です。

## 赤の内訳

赤、ERROR、SKIP はありません。`contract-loader-drift` も今回の自走 harness では発火しませんでした。

`git status` にある未追跡の `output/insights/2026-09-08_t2436-ww-reason-order/` は必読入力として既に存在していたもので、変更していません。

## 波及可能性の静的列挙

- `result_to_dict()` の構造化 report、text renderer、report digest は WW 理由配列の決定的な昇順を受け取ります。
- `_reasons()` を直接参照する既存 consumer test と、report 全体を比較する並列系テストには波及しますが、全件 PASS です。
- 共有 fixture と `_V2_FIXTURE_FILES` は不変です。一時 trace は `_tmp_trace()` だけで生成・削除します。
- wr / rw 理由、隣接辺、SCC、cycle 選択、phenomenon 分類には変更がありません。
- `dsg.py` を含む campaign source closure では、親の commit 前に外部検査が `contract-loader-drift` を出す可能性が残ります。回避変更はしていません。
- 新 node の所要時間台帳登録は、裁定どおり本変更には含めていません。

## 総括

指定された 2 変更だけを実装し、WW 理由の集合を変えず文字列昇順に固定しました。anomaly の検出条件と受理集合には一切変更を加えておらず、指定の自走 harness は全 106 件成功しています。