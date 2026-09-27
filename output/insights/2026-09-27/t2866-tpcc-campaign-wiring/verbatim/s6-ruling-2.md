# 段 6 裁定 2 — 受入 attempt 1 の赤 (2026-09-27 21:59 JST、親)

受入 attempt 1 (tested main `19d3f2bae`、tip `73197863c` = wave `aa8ec171b` + main の取り込み merge): 1 failed / 27,882 passed / 74 skipped。
赤は `orchestrator/tests/test_layer3_report.py::test_run_bench_ast_assignments_exactly_match_declared_payload_keys` の `assert len(conditional) == 4` (実測 5、`workload` が増えた)。
同じ test の `_BENCH_DONE_PAYLOAD_KEYS == _LEGACY_BENCH_PAYLOAD_KEYS | {"reps"}` も `workload` で破れる。

**帰属: 本 wave。** 統合 commit `2bb35c7a4` が `_BENCH_DONE_CONDITIONAL_PAYLOAD_KEYS` に `workload` を足した。焦点走の consumer 集合 (DW-O26) に private symbol `_BENCH_DONE_*_PAYLOAD_KEYS` の consumer である `test_layer3_report.py` を入れていなかった (親の漏れ)。段 6 review A も「固定 key 検査と衝突しない」と判定していた。

**裁定 (R2-1、real must-fix):** bench payload と commit payload への `workload` の追加を取り下げる。
- 理由 1: この pin は bench payload の key が増えたら layer3 レポート (`orchestrator/campaign/layer3_schema.json`) 側も意識して更新させる閉包で、key を足すなら schema・レポートまで広がる。段 4 裁定の A3 は「既存 field で足りるならそれで足りる」としており、bench は既存の `run_cmd` (binary 名 `tpcc_<protocol>.exe` と `-tpcc_num_wh`) で、commit は同じ variant の build 記録で TPC-C と識別できる。
- 理由 2: WAL では `workload` という key が検証記録で既に `{"tag": ...}` の形で使われており (pipeline.py の verify payload)、commit payload に文字列の `workload` を足すと同名で意味の違う key になる (D75 の二義化)。
- 放置時の影響: 受入が赤のまま land できない。layer3 レポートの run schema と bench payload の閉包が崩れる。

fix の内容 (単位 B の木、Codex author):
- `pipeline.py`: `_BENCH_DONE_CONDITIONAL_PAYLOAD_KEYS` から `"workload"` を除く。`_run_bench` の `if workload_name == "tpcc": bench_payload["workload"] = "tpcc"` と `_commit_prepared` の `if prepared.workload == "tpcc": commit_payload["workload"] = "tpcc"` を削る。
- `test_campaign.py` の本 wave 新設 test (`test_tpcc_evaluate_v3_reaches_bench_with_workload`) の `bench_records[0].payload["workload"] == "tpcc"` と commit 側の同種の assert を、bench payload の `run_cmd` に `-tpcc_num_wh=` があり `-ycsb_tuple_num=` が無いこと (と binary 名が `tpcc_` で始まること) の assert に置き換える。bench payload と commit payload に `workload` key が無いことも assert する。**既存 (本 wave 以前) の test の期待値は変えない。**
- `test_layer3_report.py` は変更しない (pin はそのまま通るはず)。

規模上限: production 10 行以内の削除、test 15 行以内。
